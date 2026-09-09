"""Immutable plugin host and host-owned SDK-v1 execution lifecycles."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from functools import partial
from typing import Literal, cast

from platydiff.core._sources import SourceSnapshot
from platydiff.core.models import (
    AutoCompareSpec,
    BinaryCompareSpec,
    DetectionCandidate,
    DetectionRecord,
    ExtensionChange,
    PairDetectionCandidate,
    PipelineStage,
    SourceDetectionRecord,
    TextCompareSpec,
)
from platydiff.core.pipeline import StageRunner
from platydiff.core.problems import DomainError, ResourceLimitError, UnavailableError
from platydiff.plugin_sdk import (
    CapabilityAvailabilityV1,
    CapabilityKind,
    ComparatorHandleV1,
    DetectorCandidateV1,
    DetectorHandleV1,
    DetectorInputV1,
    PluginComparisonV1,
    PluginExecutionErrorV1,
    PluginResourceLimitErrorV1,
    PluginUnavailableErrorV1,
)
from platydiff.plugins._discovery import (
    DiscoveredCapabilityV1,
    PluginCatalogV1,
    PluginDiscoveryPolicy,
    discover_plugins,
)

type ResolvedPluginSpec = TextCompareSpec | BinaryCompareSpec


class PluginExecutionFailureError(DomainError):
    """A safely mapped failure raised by a selected executable plugin."""

    def __init__(self, *, stage: PipelineStage) -> None:
        super().__init__(
            "The selected plugin could not complete the comparison.",
            code="plugin_execution_failure",
            status_code=502,
            stage=stage,
        )


class PluginCapabilityUnavailableError(UnavailableError):
    """A pinned plugin capability was unavailable before execution."""

    def __init__(self, *, reason_code: str = "capability_unavailable") -> None:
        super().__init__(
            "The selected plugin capability is unavailable.",
            code="capability_unavailable",
            status_code=501,
            stage=PipelineStage.RESOLVING,
            details={"reason_code": reason_code},
        )


@dataclass(frozen=True, slots=True)
class HostedPluginComparison:
    """Host-validated facts plus deterministic source-service byte accounting."""

    capability: DiscoveredCapabilityV1
    facts: PluginComparisonV1
    source_bytes_used: tuple[int, int]


class _HostedSourceService:
    def __init__(
        self,
        snapshot: SourceSnapshot,
        *,
        allowed_stage: PipelineStage,
        byte_budget: int,
    ) -> None:
        self.source_kind = snapshot.source_kind
        self.label = _safe_label(snapshot.label)
        self.size_bytes = snapshot.size_bytes
        self._snapshot = snapshot
        self._allowed_stage = allowed_stage
        self._active_stage: PipelineStage | None = None
        self._byte_budget = byte_budget
        self._bytes_used = 0

    @property
    def bytes_used(self) -> int:
        return self._bytes_used

    def activate(self, stage: PipelineStage | None) -> None:
        self._active_stage = stage

    def read(self) -> bytes:
        return b"".join(self.iter_chunks(64 * 1024))

    def iter_chunks(self, chunk_bytes: int) -> Iterator[bytes]:
        self._check_access()
        if isinstance(chunk_bytes, bool) or not isinstance(chunk_bytes, int):
            raise ValueError("chunk_bytes must be an integer")
        if not 1 <= chunk_bytes <= 16 * 1024 * 1024:
            raise ValueError("chunk_bytes must be in 1..16777216")
        for chunk in self._snapshot.iter_chunks(chunk_bytes, stage=self._allowed_stage):
            self._check_access()
            if self._bytes_used + len(chunk) > self._byte_budget:
                raise PluginResourceLimitErrorV1(
                    "The host source byte budget was exhausted."
                )
            self._bytes_used += len(chunk)
            yield chunk

    def _check_access(self) -> None:
        if self._active_stage is not self._allowed_stage:
            raise PluginExecutionErrorV1(
                "Source bytes are unavailable during this lifecycle stage."
            )


@dataclass(frozen=True, slots=True)
class PluginHost:
    """One immutable snapshot of an explicitly allowlisted plugin environment."""

    catalog: PluginCatalogV1
    _used_runs: list[object] = field(
        default_factory=list, init=False, repr=False, compare=False
    )
    _run_lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False, compare=False
    )

    @classmethod
    def discover(cls, policy: PluginDiscoveryPolicy) -> PluginHost:
        return cls(discover_plugins(policy))

    def capability(self, capability_id: str) -> DiscoveredCapabilityV1 | None:
        return next(
            (
                capability
                for capability in self.catalog.capabilities
                if capability.declaration.capability_id == capability_id
            ),
            None,
        )

    def _probe(self, capability: DiscoveredCapabilityV1) -> CapabilityAvailabilityV1:
        handle = capability.handle
        if handle is None:
            return CapabilityAvailabilityV1(False, reason_code="executor_missing")
        try:
            availability = handle.availability()
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except PluginUnavailableErrorV1 as error:
            return CapabilityAvailabilityV1(False, reason_code=error.reason_code)
        except PluginExecutionErrorV1 as error:
            raise PluginExecutionFailureError(stage=PipelineStage.RESOLVING) from error
        if not isinstance(availability, CapabilityAvailabilityV1):
            raise PluginExecutionFailureError(stage=PipelineStage.RESOLVING)
        return availability

    def _execute_comparator(
        self,
        capability: DiscoveredCapabilityV1,
        snapshots: tuple[SourceSnapshot, SourceSnapshot],
        spec: ResolvedPluginSpec,
        stages: StageRunner,
    ) -> HostedPluginComparison:
        if capability.declaration.kind is not CapabilityKind.COMPARATOR:
            raise PluginCapabilityUnavailableError(
                reason_code="capability_kind_mismatch"
            )
        if not self._probe(capability).available:
            raise PluginCapabilityUnavailableError(reason_code="backend_missing")
        handle = cast(ComparatorHandleV1, capability.handle)
        if handle.modality != spec.kind:
            raise PluginCapabilityUnavailableError(reason_code="modality_mismatch")
        try:
            source_stage = PipelineStage(handle.source_stage)
        except (TypeError, ValueError) as error:
            raise PluginExecutionFailureError(stage=PipelineStage.RESOLVING) from error
        if source_stage not in (
            PipelineStage.DECODING,
            PipelineStage.NORMALIZING,
            PipelineStage.ALIGNING,
            PipelineStage.COMPARING,
        ):
            raise PluginExecutionFailureError(stage=PipelineStage.RESOLVING)
        maximum = _maximum_input_bytes(spec)
        before = _HostedSourceService(
            snapshots[0], allowed_stage=source_stage, byte_budget=maximum
        )
        after = _HostedSourceService(
            snapshots[1], allowed_stage=source_stage, byte_budget=maximum
        )
        run = _invoke_plugin(
            PipelineStage.RESOLVING,
            lambda: handle.create_run(before, after, spec),
        )
        with self._run_lock:
            if any(previous is run for previous in self._used_runs):
                raise PluginExecutionFailureError(stage=PipelineStage.RESOLVING)
            self._used_runs.append(run)
        methods: tuple[tuple[PipelineStage, Callable[[], object]], ...] = (
            (PipelineStage.DECODING, run.decode),
            (PipelineStage.NORMALIZING, run.normalize),
            (PipelineStage.ALIGNING, run.align),
            (PipelineStage.COMPARING, run.compare),
        )
        for stage, method in methods:
            before.activate(stage)
            after.activate(stage)
            try:
                stages.run(
                    stage,
                    partial(_invoke_plugin, stage, method),
                )
            finally:
                before.activate(None)
                after.activate(None)
        before.activate(PipelineStage.AGGREGATING)
        after.activate(PipelineStage.AGGREGATING)
        try:
            facts = stages.run(
                PipelineStage.AGGREGATING,
                lambda: _aggregate_plugin(run.aggregate, capability),
            )
        finally:
            before.activate(None)
            after.activate(None)
        return HostedPluginComparison(
            capability, facts, (before.bytes_used, after.bytes_used)
        )

    def _detect(
        self,
        capability: DiscoveredCapabilityV1,
        snapshots: tuple[SourceSnapshot, SourceSnapshot],
        spec: AutoCompareSpec,
        comparator_candidates: tuple[
            tuple[Literal["text", "binary"], int, str, str], ...
        ],
    ) -> DetectionRecord:
        if capability.declaration.kind is not CapabilityKind.DETECTOR:
            raise PluginCapabilityUnavailableError(
                reason_code="capability_kind_mismatch"
            )
        if not self._probe(capability).available:
            raise PluginCapabilityUnavailableError(reason_code="backend_missing")
        handle = cast(DetectorHandleV1, capability.handle)
        maximum = min(spec.limits.max_detection_bytes, spec.limits.max_input_bytes)
        roles: tuple[Literal["before", "after"], Literal["before", "after"]] = (
            "before",
            "after",
        )
        records = tuple(
            self._detect_source(handle, snapshot, role, maximum, capability)
            for snapshot, role in zip(snapshots, roles, strict=True)
        )
        before, after = cast(
            tuple[SourceDetectionRecord, SourceDetectionRecord], records
        )
        pairs = _plugin_pair_candidates(before, after, comparator_candidates)
        disposition: Literal["selected", "no_match", "ambiguous"]
        selected: Literal["text", "binary"] | None
        if not pairs or pairs[0].confidence < spec.minimum_confidence:
            disposition, selected = "no_match", None
        elif (
            len(pairs) > 1
            and pairs[0].confidence - pairs[1].confidence < spec.ambiguity_margin
        ):
            disposition, selected = "ambiguous", None
        else:
            disposition, selected = "selected", pairs[0].modality_id
        return DetectionRecord(
            detector_id=capability.declaration.capability_id,
            detector_version=capability.declaration.implementation_version,
            maximum_bytes=maximum,
            minimum_confidence=spec.minimum_confidence,
            ambiguity_margin=spec.ambiguity_margin,
            sources=(before, after),
            pair_candidates=pairs,
            disposition=disposition,
            selected_modality=selected,
        )

    def _detect_source(
        self,
        handle: DetectorHandleV1,
        snapshot: SourceSnapshot,
        role: Literal["before", "after"],
        maximum: int,
        capability: DiscoveredCapabilityV1,
    ) -> SourceDetectionRecord:
        prefix = snapshot.read_prefix(maximum, stage=PipelineStage.DETECTING)
        request = DetectorInputV1(
            snapshot.source_kind,
            prefix,
            snapshot.size_bytes <= len(prefix),
            maximum,
        )
        returned = _invoke_plugin(
            PipelineStage.DETECTING, lambda: handle.detect(request)
        )
        if not isinstance(returned, tuple):
            raise PluginExecutionFailureError(stage=PipelineStage.DETECTING)
        try:
            candidates = tuple(
                _validated_detector_candidate(item, capability) for item in returned
            )
            return SourceDetectionRecord(role, candidates)
        except (TypeError, ValueError) as error:
            raise PluginExecutionFailureError(stage=PipelineStage.DETECTING) from error


def _invoke_plugin[T](stage: PipelineStage, operation: Callable[[], T]) -> T:
    try:
        return operation()
    except (KeyboardInterrupt, SystemExit, MemoryError):
        raise
    except PluginResourceLimitErrorV1 as error:
        raise ResourceLimitError(
            "A plugin exhausted a deterministic resource limit.", stage=stage
        ) from error
    except (PluginExecutionErrorV1, PluginUnavailableErrorV1) as error:
        raise PluginExecutionFailureError(stage=stage) from error


def _aggregate_plugin(
    operation: Callable[[], object], capability: DiscoveredCapabilityV1
) -> PluginComparisonV1:
    returned = _invoke_plugin(PipelineStage.AGGREGATING, operation)
    if not isinstance(returned, PluginComparisonV1):
        raise PluginExecutionFailureError(stage=PipelineStage.AGGREGATING)
    if returned.implementation_version != capability.declaration.implementation_version:
        raise PluginExecutionFailureError(stage=PipelineStage.AGGREGATING)
    plugin_id = capability.plugin.manifest.plugin_id
    for change in returned.changes.items:
        if isinstance(change, ExtensionChange) and (
            change.plugin_id != plugin_id or not change.kind.startswith(f"{plugin_id}.")
        ):
            raise PluginExecutionFailureError(stage=PipelineStage.AGGREGATING)
    for diagnostic in returned.diagnostics:
        if not _safe_diagnostic_text(diagnostic.message):
            raise PluginExecutionFailureError(stage=PipelineStage.AGGREGATING)
    return returned


def _validated_detector_candidate(
    value: object, capability: DiscoveredCapabilityV1
) -> DetectionCandidate:
    if not isinstance(value, DetectorCandidateV1):
        raise TypeError("invalid detector candidate")
    return DetectionCandidate(
        value.modality_id,
        value.confidence,
        capability.declaration.capability_id,
        capability.declaration.implementation_version,
        capability.declaration.priority,
        value.evidence_codes,
        dict(value.evidence_counts),
    )


def _plugin_pair_candidates(
    before: SourceDetectionRecord,
    after: SourceDetectionRecord,
    comparator_candidates: tuple[tuple[Literal["text", "binary"], int, str, str], ...],
) -> tuple[PairDetectionCandidate, ...]:
    before_by_modality = {item.modality_id: item for item in before.candidates}
    after_by_modality = {item.modality_id: item for item in after.candidates}
    pairs = []
    for modality, priority, capability_id, backend_id in comparator_candidates:
        before_candidate = before_by_modality.get(modality)
        after_candidate = after_by_modality.get(modality)
        if before_candidate is None or after_candidate is None:
            continue
        pairs.append(
            PairDetectionCandidate(
                modality,
                min(before_candidate.confidence, after_candidate.confidence),
                before_candidate.confidence,
                after_candidate.confidence,
                min(before_candidate.priority, after_candidate.priority),
                priority,
                capability_id,
                backend_id,
            )
        )
    return tuple(
        sorted(
            pairs,
            key=lambda item: (
                -item.confidence,
                item.detector_priority,
                item.capability_priority,
                item.modality_id,
                item.capability_id,
                item.backend_id,
            ),
        )
    )


def _maximum_input_bytes(spec: ResolvedPluginSpec) -> int:
    return spec.limits.max_input_bytes


def _safe_label(label: str | None) -> str | None:
    if label is None or "/" in label or "\\" in label:
        return None
    try:
        encoded = label.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return None
    if len(encoded) > 1024 or any(ord(character) < 0x20 for character in label):
        return None
    return label


def _safe_diagnostic_text(value: str) -> bool:
    return (
        "/" not in value
        and "\\" not in value
        and len(value.encode("utf-8", errors="strict")) <= 1024
        and not any(ord(character) < 0x20 for character in value)
    )
