"""Private Phase 2 capability request and deterministic built-in catalog."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from platydiff.core.models import (
    AutoCompareSpec,
    BinaryCompareSpec,
    CapabilityAttempt,
    CompareSpec,
    JsonObject,
    ResourceLimits,
    SourceKind,
    TextCompareSpec,
    _bounded_integer,
    _identifier,
    _json_safe,
)

type Modality = Literal["text", "binary"]


@dataclass(frozen=True, slots=True)
class ExecutionLimits:
    """Private normalized superset translated from exactly one public spec."""

    max_input_bytes: int
    max_input_lines: int
    max_encoded_line_bytes: int
    max_myers_work: int
    effective_detection_bytes: int
    binary_chunk_bytes: int
    max_change_items: int
    max_change_payload_bytes: int


@dataclass(frozen=True, slots=True)
class CapabilityRequest:
    """Private exact-comparison request passed to detection and resolution."""

    request_version: Literal[1]
    operation: Literal["compare"]
    requested_modality: Literal["auto", "text", "binary"]
    resolved_modality: Modality | None
    source_kinds: tuple[SourceKind, SourceKind]
    semantic_class: Literal["exact"]
    required_features: tuple[str, ...]
    intent: JsonObject
    limits: ExecutionLimits

    def __post_init__(self) -> None:
        if self.request_version != 1 or self.operation != "compare":
            raise ValueError("unsupported internal capability request")
        if self.requested_modality not in ("auto", "text", "binary"):
            raise ValueError("unknown requested modality")
        if self.requested_modality != "auto" and self.resolved_modality not in (
            None,
            self.requested_modality,
        ):
            raise ValueError("explicit requests cannot resolve to another modality")
        if self.required_features != tuple(sorted(set(self.required_features))):
            raise ValueError("required features must be unique and sorted")
        for feature in self.required_features:
            _identifier(feature)
        _json_safe(self.intent)

    def with_resolved_modality(self, modality: Modality) -> CapabilityRequest:
        return CapabilityRequest(
            request_version=self.request_version,
            operation=self.operation,
            requested_modality=self.requested_modality,
            resolved_modality=modality,
            source_kinds=self.source_kinds,
            semantic_class=self.semantic_class,
            required_features=self.required_features,
            intent=self.intent,
            limits=self.limits,
        )


@dataclass(frozen=True, slots=True)
class CapabilityRecord:
    capability_id: str
    modality: Modality
    semantic_class: str
    implementation_version: str
    backend_id: str
    backend_version: str
    priority: int
    supported_source_kinds: frozenset[SourceKind]
    supported_features: frozenset[str]
    executor: object
    backend_available: bool = True
    backend_version_supported: bool = True

    def __post_init__(self) -> None:
        _identifier(self.capability_id)
        if self.modality not in ("text", "binary"):
            raise ValueError("unknown capability modality")
        _identifier(self.semantic_class)
        _identifier(self.backend_id)
        _bounded_integer(self.priority, "priority", 0, 2**53)
        for feature in self.supported_features:
            _identifier(feature)
        if not isinstance(self.backend_available, bool) or not isinstance(
            self.backend_version_supported, bool
        ):
            raise ValueError("backend availability flags must be booleans")


@dataclass(frozen=True, slots=True)
class Resolution:
    selected: CapabilityRecord | None
    attempts: tuple[CapabilityAttempt, ...]


class CapabilityCatalog:
    """Registration-order-independent catalog for built-in capabilities only."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], CapabilityRecord] = {}

    def register(self, record: CapabilityRecord) -> None:
        key = (record.capability_id, record.backend_id)
        if key in self._records:
            raise RuntimeError("duplicate internal capability and backend")
        self._records[key] = record

    def records_for_detection(
        self, request: CapabilityRequest
    ) -> tuple[CapabilityRecord, ...]:
        records = (
            record
            for record in self._records.values()
            if record.semantic_class == request.semantic_class
            and all(
                kind in record.supported_source_kinds for kind in request.source_kinds
            )
            and set(request.required_features).issubset(record.supported_features)
            and record.backend_available
            and record.backend_version_supported
        )
        return tuple(sorted(records, key=_record_sort_key))

    def resolve(self, request: CapabilityRequest) -> Resolution:
        modality = request.resolved_modality
        if modality is None and request.requested_modality != "auto":
            modality = request.requested_modality
        ranked = tuple(sorted(self._records.values(), key=_record_sort_key))
        selected = next(
            (
                record
                for record in ranked
                if _rejection_reason(record, request, modality) is None
            ),
            None,
        )
        rejected = tuple(
            CapabilityAttempt(
                record.capability_id,
                record.backend_id,
                "rejected",
                _rejection_reason(record, request, modality) or "lower_priority",
            )
            for record in ranked
            if record is not selected
        )
        if selected is None:
            return Resolution(None, rejected)
        return Resolution(
            selected,
            (
                *rejected,
                CapabilityAttempt(
                    selected.capability_id, selected.backend_id, "selected", None
                ),
            ),
        )


def request_from_spec(
    spec: CompareSpec,
    source_kinds: tuple[SourceKind, SourceKind],
) -> CapabilityRequest:
    """Translate one public intent into the private request boundary."""
    if isinstance(spec, TextCompareSpec):
        limits = _text_limits(spec.limits)
        intent: JsonObject = {
            "kind": "text",
            "encoding": spec.encoding.value,
            "newline": spec.newline.value,
            "context_lines": spec.context_lines,
        }
    elif isinstance(spec, BinaryCompareSpec):
        limits = ExecutionLimits(
            max_input_bytes=spec.limits.max_input_bytes,
            max_input_lines=0,
            max_encoded_line_bytes=0,
            max_myers_work=0,
            effective_detection_bytes=0,
            binary_chunk_bytes=spec.limits.chunk_bytes,
            max_change_items=spec.limits.max_change_items,
            max_change_payload_bytes=spec.limits.max_change_payload_bytes,
        )
        intent = {"kind": "binary"}
    elif isinstance(spec, AutoCompareSpec):
        limits = ExecutionLimits(
            max_input_bytes=spec.limits.max_input_bytes,
            max_input_lines=spec.limits.max_input_lines,
            max_encoded_line_bytes=spec.limits.max_encoded_line_bytes,
            max_myers_work=spec.limits.max_myers_work,
            effective_detection_bytes=min(
                spec.limits.max_detection_bytes, spec.limits.max_input_bytes
            ),
            binary_chunk_bytes=spec.limits.binary_chunk_bytes,
            max_change_items=spec.limits.max_change_items,
            max_change_payload_bytes=spec.limits.max_change_payload_bytes,
        )
        intent = {
            "kind": "auto",
            "text": {
                "encoding": spec.text.encoding.value,
                "newline": spec.text.newline.value,
                "context_lines": spec.text.context_lines,
            },
            "minimum_confidence": spec.minimum_confidence,
            "ambiguity_margin": spec.ambiguity_margin,
        }
    else:
        raise TypeError("unsupported comparison specification")
    return CapabilityRequest(
        request_version=1,
        operation="compare",
        requested_modality=spec.kind,
        resolved_modality=None,
        source_kinds=source_kinds,
        semantic_class="exact",
        required_features=(),
        intent=intent,
        limits=limits,
    )


def _text_limits(limits: ResourceLimits) -> ExecutionLimits:
    return ExecutionLimits(
        max_input_bytes=limits.max_input_bytes,
        max_input_lines=limits.max_input_lines,
        max_encoded_line_bytes=limits.max_encoded_line_bytes,
        max_myers_work=limits.max_myers_work,
        effective_detection_bytes=0,
        binary_chunk_bytes=64 * 1024,
        max_change_items=limits.max_change_items,
        max_change_payload_bytes=limits.max_change_payload_bytes,
    )


def _record_sort_key(record: CapabilityRecord) -> tuple[int, str, str]:
    return (record.priority, record.capability_id, record.backend_id)


def _rejection_reason(
    record: CapabilityRecord,
    request: CapabilityRequest,
    modality: Modality | None,
) -> str | None:
    if modality is None or record.modality != modality:
        return "modality_mismatch"
    if record.semantic_class != request.semantic_class:
        return "semantic_class_mismatch"
    if any(kind not in record.supported_source_kinds for kind in request.source_kinds):
        return "source_kind_unsupported"
    if not set(request.required_features).issubset(record.supported_features):
        return "required_feature_missing"
    if not record.backend_available:
        return "backend_missing"
    if not record.backend_version_supported:
        return "backend_version_unsupported"
    return None
