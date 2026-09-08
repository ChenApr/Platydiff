"""Schema-v1 public models for sources, specifications, and outcomes."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal
from urllib.parse import unquote_to_bytes, urlsplit

type JsonPrimitive = bool | int | float | str | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]

SCHEMA_VERSION: Literal[1] = 1
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PERCENT_ESCAPE = re.compile(r"%[0-9a-fA-F]{2}")
_INVALID_PERCENT_ESCAPE = re.compile(r"%(?![0-9a-fA-F]{2})")
_MAX_EXACT_INTEGER = 2**53
_DETECTION_COUNT_KEYS = (
    "inspected_bytes",
    "nul_count",
    "non_ascii_byte_count",
    "pending_utf8_bytes",
    "disallowed_control_count",
)


def _unicode_scalar(value: str, field_name: str) -> None:
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise ValueError(
            f"{field_name} must contain valid Unicode scalar values"
        ) from error


def _identifier(value: str, *, namespaced: bool | None = None) -> None:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"invalid stable identifier: {value!r}")
    has_namespace = "." in value
    if namespaced is True and not has_namespace:
        raise ValueError("extension identifiers must use a reverse-domain name")
    if namespaced is False and has_namespace:
        raise ValueError("built-in identifiers must not use a domain prefix")


def _bounded_integer(value: object, field_name: str, lower: int, upper: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    if not lower <= value <= upper:
        raise ValueError(f"{field_name} must be in {lower}..{upper}")
    return value


def _json_safe(value: JsonValue) -> None:
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("generic JSON data must not contain non-finite numbers")
        return
    if isinstance(value, str):
        _unicode_scalar(value, "JSON strings")
        return
    if isinstance(value, list):
        for item in value:
            _json_safe(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            _unicode_scalar(key, "JSON object keys")
            _json_safe(item)
        return
    raise ValueError("value is not JSON-safe")


def _utc_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("timestamps must be ISO 8601") from error
    offset = parsed.utcoffset()
    if parsed.tzinfo is None or offset is None:
        raise ValueError("timestamps must include a UTC offset")
    if offset.total_seconds() != 0:
        raise ValueError("timestamps must be UTC")
    return parsed


def _safe_artifact_uri(value: str) -> None:
    _unicode_scalar(value, "artifact URI")
    if not value or _INVALID_PERCENT_ESCAPE.search(value):
        raise ValueError("artifact URI must be a safe relative POSIX path")
    try:
        parsed = urlsplit(value)
    except ValueError as error:
        raise ValueError("artifact URI must be a safe relative POSIX path") from error
    if (
        parsed.scheme
        or parsed.netloc
        or parsed.query
        or parsed.fragment
        or parsed.path != value
        or parsed.path.startswith("/")
        or "\\" in parsed.path
    ):
        raise ValueError("artifact URI must be a safe relative POSIX path")
    raw_segments = parsed.path.split("/")
    for index, raw_segment in enumerate(raw_segments):
        try:
            segment = unquote_to_bytes(raw_segment).decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ValueError(
                "artifact URI must be a safe relative POSIX path"
            ) from error
        if (
            not segment
            or segment in (".", "..")
            or "/" in segment
            or "\\" in segment
            or "?" in segment
            or "#" in segment
            or any(
                ord(character) < 0x20 or 0x7F <= ord(character) <= 0x9F
                for character in segment
            )
            or (index == 0 and ":" in segment)
            or _PERCENT_ESCAPE.search(segment)
        ):
            raise ValueError("artifact URI must be a safe relative POSIX path")


class Relation(StrEnum):
    EQUAL = "equal"
    DIFFERENT = "different"


class Verdict(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class Fidelity(StrEnum):
    FULL = "full"
    DEGRADED = "degraded"


class ChangeCompleteness(StrEnum):
    COMPLETE = "complete"
    TRUNCATED = "truncated"
    PARTIAL = "partial"


class ChangeSelection(StrEnum):
    ALL = "all"
    SOURCE_ORDER_PREFIX = "source_order_prefix"
    ALGORITHM_PARTIAL = "algorithm_partial"


class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"


class PipelineStage(StrEnum):
    VALIDATING = "validating"
    SOURCING = "sourcing"
    DETECTING = "detecting"
    RESOLVING = "resolving"
    DECODING = "decoding"
    NORMALIZING = "normalizing"
    ALIGNING = "aligning"
    COMPARING = "comparing"
    AGGREGATING = "aggregating"


class StageDisposition(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class SourceKind(StrEnum):
    PATH = "path"
    BYTES = "bytes"
    TEXT = "text"


class TextEncoding(StrEnum):
    UTF8 = "utf-8"
    UTF8_SIG = "utf-8-sig"


class NewlinePolicy(StrEnum):
    PRESERVE = "preserve"
    NORMALIZE_LF = "normalize_lf"


class MetricDirection(StrEnum):
    LOWER_IS_BETTER = "lower_is_better"
    HIGHER_IS_BETTER = "higher_is_better"
    NEUTRAL = "neutral"


@dataclass(frozen=True, slots=True)
class PathSource:
    """One filesystem path source."""

    path: Path


@dataclass(frozen=True, slots=True)
class BytesSource:
    """Owned immutable byte source."""

    data: bytes
    label: str | None = None

    def __post_init__(self) -> None:
        if self.label is not None:
            _unicode_scalar(self.label, "source label")


@dataclass(frozen=True, slots=True)
class TextSource:
    """Owned already-decoded text source."""

    text: str
    label: str | None = None

    def __post_init__(self) -> None:
        _unicode_scalar(self.text, "source text")
        if self.label is not None:
            _unicode_scalar(self.label, "source label")


type Source = PathSource | BytesSource | TextSource


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    """Deterministic resource limits for the Phase 1 text slice."""

    max_input_bytes: int = 16 * 1024 * 1024
    max_input_lines: int = 200_000
    max_encoded_line_bytes: int = 1024 * 1024
    max_myers_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True, slots=True)
class TextCompareSpec:
    """Explicit user intent for a strict line-oriented text comparison."""

    kind: Literal["text"] = field(default="text", init=False)
    encoding: TextEncoding = TextEncoding.UTF8
    newline: NewlinePolicy = NewlinePolicy.PRESERVE
    context_lines: int = 3
    limits: ResourceLimits = field(default_factory=ResourceLimits)

    def __post_init__(self) -> None:
        if self.context_lines < 0:
            raise ValueError("context_lines must be non-negative")


@dataclass(frozen=True, slots=True)
class BinaryResourceLimits:
    """Deterministic resource limits for exact binary comparison."""

    max_input_bytes: int = 16 * 1024 * 1024
    chunk_bytes: int = 64 * 1024
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

    def __post_init__(self) -> None:
        _bounded_integer(self.max_input_bytes, "max_input_bytes", 0, _MAX_EXACT_INTEGER)
        _bounded_integer(self.chunk_bytes, "chunk_bytes", 1, 16 * 1024 * 1024)
        _bounded_integer(
            self.max_change_items, "max_change_items", 0, _MAX_EXACT_INTEGER
        )
        _bounded_integer(
            self.max_change_payload_bytes,
            "max_change_payload_bytes",
            0,
            _MAX_EXACT_INTEGER,
        )


@dataclass(frozen=True, slots=True)
class BinaryCompareSpec:
    """Explicit user intent for an exact byte comparison."""

    kind: Literal["binary"] = field(default="binary", init=False)
    limits: BinaryResourceLimits = field(default_factory=BinaryResourceLimits)


@dataclass(frozen=True, slots=True)
class AutoTextOptions:
    """Text intent to use only when automatic detection selects text."""

    encoding: TextEncoding = TextEncoding.UTF8
    newline: NewlinePolicy = NewlinePolicy.PRESERVE
    context_lines: int = 3

    def __post_init__(self) -> None:
        _bounded_integer(self.context_lines, "context_lines", 0, _MAX_EXACT_INTEGER)


@dataclass(frozen=True, slots=True)
class AutoResourceLimits:
    """Single normalized resource-limit source for automatic comparison."""

    max_input_bytes: int = 16 * 1024 * 1024
    max_input_lines: int = 200_000
    max_encoded_line_bytes: int = 1024 * 1024
    max_myers_work: int = 5_000_000
    max_detection_bytes: int = 64 * 1024
    binary_chunk_bytes: int = 64 * 1024
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

    def __post_init__(self) -> None:
        for name in (
            "max_input_bytes",
            "max_input_lines",
            "max_encoded_line_bytes",
            "max_myers_work",
            "max_detection_bytes",
            "max_change_items",
            "max_change_payload_bytes",
        ):
            _bounded_integer(getattr(self, name), name, 0, _MAX_EXACT_INTEGER)
        _bounded_integer(
            self.binary_chunk_bytes,
            "binary_chunk_bytes",
            1,
            16 * 1024 * 1024,
        )


@dataclass(frozen=True, slots=True)
class AutoCompareSpec:
    """Intent for deterministic text-or-binary automatic comparison."""

    kind: Literal["auto"] = field(default="auto", init=False)
    text: AutoTextOptions = field(default_factory=AutoTextOptions)
    minimum_confidence: int = 800
    ambiguity_margin: int = 100
    limits: AutoResourceLimits = field(default_factory=AutoResourceLimits)

    def __post_init__(self) -> None:
        _bounded_integer(self.minimum_confidence, "minimum_confidence", 0, 1000)
        _bounded_integer(self.ambiguity_margin, "ambiguity_margin", 0, 1000)


type CompareSpec = AutoCompareSpec | TextCompareSpec | BinaryCompareSpec


@dataclass(frozen=True, slots=True)
class DetectionCandidate:
    modality_id: Literal["text", "binary"]
    confidence: int
    detector_id: str
    detector_version: str
    priority: int
    evidence_codes: tuple[str, ...]
    evidence_counts: JsonObject

    def __post_init__(self) -> None:
        if self.modality_id not in ("text", "binary"):
            raise ValueError("unknown detection modality")
        _bounded_integer(self.confidence, "confidence", 0, 1000)
        _identifier(self.detector_id)
        _unicode_scalar(self.detector_version, "detector version")
        _bounded_integer(self.priority, "priority", 0, _MAX_EXACT_INTEGER)
        for code in self.evidence_codes:
            _identifier(code)
        if len(self.evidence_codes) != len(set(self.evidence_codes)):
            raise ValueError("detection evidence codes must be unique")
        object.__setattr__(self, "evidence_codes", tuple(sorted(self.evidence_codes)))
        normalized: JsonObject = {}
        for key in _DETECTION_COUNT_KEYS:
            if key not in self.evidence_counts:
                raise ValueError(f"missing detection evidence count: {key}")
            normalized[key] = _bounded_integer(
                self.evidence_counts[key], key, 0, _MAX_EXACT_INTEGER
            )
        pending_utf8_bytes = normalized["pending_utf8_bytes"]
        if not isinstance(pending_utf8_bytes, int) or isinstance(
            pending_utf8_bytes, bool
        ):
            raise RuntimeError("normalized detection count must be an integer")
        if pending_utf8_bytes > 3:
            raise ValueError("pending_utf8_bytes must be in 0..3")
        object.__setattr__(self, "evidence_counts", normalized)


@dataclass(frozen=True, slots=True)
class SourceDetectionRecord:
    role: Literal["before", "after"]
    candidates: tuple[DetectionCandidate, ...]

    def __post_init__(self) -> None:
        if self.role not in ("before", "after"):
            raise ValueError("unknown detection source role")
        modalities = [item.modality_id for item in self.candidates]
        if len(modalities) != len(set(modalities)):
            raise ValueError("source detection modalities must be unique")
        object.__setattr__(
            self,
            "candidates",
            tuple(
                sorted(
                    self.candidates,
                    key=lambda item: (-item.confidence, item.modality_id),
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class PairDetectionCandidate:
    modality_id: Literal["text", "binary"]
    confidence: int
    before_confidence: int
    after_confidence: int
    detector_priority: int
    capability_priority: int
    capability_id: str
    backend_id: str

    def __post_init__(self) -> None:
        if self.modality_id not in ("text", "binary"):
            raise ValueError("unknown detection modality")
        for name in ("confidence", "before_confidence", "after_confidence"):
            _bounded_integer(getattr(self, name), name, 0, 1000)
        if self.confidence != min(self.before_confidence, self.after_confidence):
            raise ValueError("pair confidence must be the minimum source confidence")
        _bounded_integer(
            self.detector_priority, "detector_priority", 0, _MAX_EXACT_INTEGER
        )
        _bounded_integer(
            self.capability_priority, "capability_priority", 0, _MAX_EXACT_INTEGER
        )
        _identifier(self.capability_id)
        _identifier(self.backend_id)


def _pair_detection_sort_key(
    item: PairDetectionCandidate,
) -> tuple[int, int, int, str, str, str]:
    return (
        -item.confidence,
        item.detector_priority,
        item.capability_priority,
        item.modality_id,
        item.capability_id,
        item.backend_id,
    )


@dataclass(frozen=True, slots=True)
class DetectionRecord:
    detector_id: str
    detector_version: str
    maximum_bytes: int
    minimum_confidence: int
    ambiguity_margin: int
    sources: tuple[SourceDetectionRecord, SourceDetectionRecord]
    pair_candidates: tuple[PairDetectionCandidate, ...]
    disposition: Literal["selected", "no_match", "ambiguous"]
    selected_modality: Literal["text", "binary"] | None

    def __post_init__(self) -> None:
        _identifier(self.detector_id)
        _unicode_scalar(self.detector_version, "detector version")
        _bounded_integer(self.maximum_bytes, "maximum_bytes", 0, _MAX_EXACT_INTEGER)
        _bounded_integer(self.minimum_confidence, "minimum_confidence", 0, 1000)
        _bounded_integer(self.ambiguity_margin, "ambiguity_margin", 0, 1000)
        if tuple(item.role for item in self.sources) != ("before", "after"):
            raise ValueError("detection sources must be ordered before, after")
        for source in self.sources:
            for candidate in source.candidates:
                if (
                    candidate.detector_id != self.detector_id
                    or candidate.detector_version != self.detector_version
                ):
                    raise ValueError("source candidate detector must match its record")
        identities = [
            (item.modality_id, item.capability_id, item.backend_id)
            for item in self.pair_candidates
        ]
        if len(identities) != len(set(identities)):
            raise ValueError("pair detection candidates must be unique")
        object.__setattr__(
            self,
            "pair_candidates",
            tuple(sorted(self.pair_candidates, key=_pair_detection_sort_key)),
        )
        if self.disposition == "selected":
            if self.selected_modality is None:
                raise ValueError("selected detection requires a modality")
            if (
                not self.pair_candidates
                or self.pair_candidates[0].modality_id != self.selected_modality
            ):
                raise ValueError("selected modality must match the top pair candidate")
            if self.pair_candidates[0].confidence < self.minimum_confidence:
                raise ValueError("selected detection must reach minimum confidence")
            if (
                len(self.pair_candidates) > 1
                and self.pair_candidates[0].confidence
                - self.pair_candidates[1].confidence
                < self.ambiguity_margin
            ):
                raise ValueError("selected detection must satisfy ambiguity margin")
        elif self.disposition in ("no_match", "ambiguous"):
            if self.selected_modality is not None:
                raise ValueError("unselected detection must not contain a modality")
            if (
                self.disposition == "no_match"
                and self.pair_candidates
                and self.pair_candidates[0].confidence >= self.minimum_confidence
            ):
                raise ValueError("no-match detection must be below its minimum")
            if self.disposition == "ambiguous" and (
                len(self.pair_candidates) < 2
                or self.pair_candidates[0].confidence < self.minimum_confidence
                or self.pair_candidates[0].confidence
                - self.pair_candidates[1].confidence
                >= self.ambiguity_margin
            ):
                raise ValueError("ambiguous detection must contain close candidates")
        else:
            raise ValueError("unknown detection disposition")


@dataclass(frozen=True, slots=True)
class StageRecord:
    stage: PipelineStage
    started_at: str
    finished_at: str
    duration_ns: int
    disposition: StageDisposition

    def __post_init__(self) -> None:
        started = _utc_timestamp(self.started_at)
        finished = _utc_timestamp(self.finished_at)
        if finished < started:
            raise ValueError("a stage must not finish before it starts")
        if self.duration_ns < 0:
            raise ValueError("duration_ns must be non-negative")


@dataclass(frozen=True, slots=True)
class CapabilityAttempt:
    capability_id: str
    backend_id: str | None
    disposition: Literal["selected", "rejected", "fallback"]
    reason_code: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.capability_id)
        if self.backend_id is not None:
            _identifier(self.backend_id)
        if self.reason_code is not None:
            _identifier(self.reason_code)


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    severity: DiagnosticSeverity
    stage: PipelineStage | None
    message: str
    details: JsonObject = field(default_factory=dict)

    def __post_init__(self) -> None:
        _identifier(self.code)
        _unicode_scalar(self.message, "diagnostic message")
        _json_safe(self.details)


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    started_at: str
    finished_at: str
    duration_ns: int
    stages: tuple[StageRecord, ...]
    attempts: tuple[CapabilityAttempt, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    last_completed_stage: PipelineStage | None = None
    detection: DetectionRecord | None = None

    def __post_init__(self) -> None:
        started = _utc_timestamp(self.started_at)
        finished = _utc_timestamp(self.finished_at)
        if finished < started:
            raise ValueError("an execution must not finish before it starts")
        if self.duration_ns < 0:
            raise ValueError("duration_ns must be non-negative")
        lifecycle_with_detection = tuple(PipelineStage)
        lifecycle_without_detection = tuple(
            stage for stage in PipelineStage if stage is not PipelineStage.DETECTING
        )
        actual = tuple(record.stage for record in self.stages)
        if not any(
            actual == lifecycle[: len(actual)]
            for lifecycle in (lifecycle_with_detection, lifecycle_without_detection)
        ):
            raise ValueError("execution stages must form a contiguous lifecycle prefix")
        detection_records = [
            record for record in self.stages if record.stage is PipelineStage.DETECTING
        ]
        if self.detection is not None and not detection_records:
            raise ValueError("detection provenance requires a detection stage")
        if (
            detection_records
            and detection_records[0].disposition is not StageDisposition.FAILED
            and self.detection is None
        ):
            raise ValueError("completed detection requires detection provenance")
        terminal_indexes = [
            index
            for index, record in enumerate(self.stages)
            if record.disposition is not StageDisposition.COMPLETED
        ]
        if len(terminal_indexes) > 1 or (
            terminal_indexes and terminal_indexes[0] != len(self.stages) - 1
        ):
            raise ValueError("an execution may have only one final terminal stage")
        previous_finished = started
        for record in self.stages:
            record_started = _utc_timestamp(record.started_at)
            record_finished = _utc_timestamp(record.finished_at)
            if record_started < previous_finished:
                raise ValueError("execution stage intervals must not overlap")
            previous_finished = record_finished
        if previous_finished > finished:
            raise ValueError("execution stage intervals must be contained by execution")
        if sum(record.duration_ns for record in self.stages) > self.duration_ns:
            raise ValueError("stage durations must fit within execution duration")
        completed = [
            record.stage
            for record in self.stages
            if record.disposition is StageDisposition.COMPLETED
        ]
        expected_last = completed[-1] if completed else None
        if self.last_completed_stage is not expected_last:
            raise ValueError("last_completed_stage must match the stage records")
        object.__setattr__(
            self,
            "diagnostics",
            tuple(sorted(self.diagnostics, key=lambda item: (item.code, item.message))),
        )


_PROBLEM_CODES: dict[str, tuple[int, Literal["failed", "unavailable"]]] = {
    "invalid_spec": (400, "failed"),
    "permission_denied": (403, "failed"),
    "source_not_found": (404, "failed"),
    "source_changed": (409, "failed"),
    "resource_limit_exceeded": (413, "failed"),
    "compare_resource_limit": (413, "failed"),
    "unsupported_encoding": (415, "failed"),
    "source_type_unsupported": (415, "failed"),
    "decode_error": (422, "failed"),
    "internal_error": (500, "failed"),
    "io_error": (500, "failed"),
    "capability_unavailable": (501, "unavailable"),
    "detection_no_match": (415, "unavailable"),
    "detection_ambiguous": (409, "unavailable"),
    "comparator_failure": (502, "failed"),
    "backend_unavailable": (503, "unavailable"),
}


@dataclass(frozen=True, slots=True)
class ExecutionProblem:
    code: str
    status_code: int
    stage: PipelineStage
    message: str
    details: JsonObject = field(default_factory=dict)
    retryable: bool = False

    def __post_init__(self) -> None:
        expected = _PROBLEM_CODES.get(self.code)
        if expected != (self.status_code, "failed"):
            raise ValueError("invalid schema-v1 failed problem mapping")
        _unicode_scalar(self.message, "problem message")
        _json_safe(self.details)


@dataclass(frozen=True, slots=True)
class CapabilityProblem:
    code: str
    status_code: int
    stage: PipelineStage
    message: str
    details: JsonObject = field(default_factory=dict)
    retryable: bool = False

    def __post_init__(self) -> None:
        expected = _PROBLEM_CODES.get(self.code)
        if expected != (self.status_code, "unavailable"):
            raise ValueError("invalid schema-v1 unavailable problem mapping")
        if self.stage not in (PipelineStage.DETECTING, PipelineStage.RESOLVING):
            raise ValueError("unavailable outcomes are legal only while resolving")
        _unicode_scalar(self.message, "problem message")
        _json_safe(self.details)


@dataclass(frozen=True, slots=True)
class InputProvenance:
    role: Literal["before", "after"]
    source_kind: SourceKind
    size_bytes: int
    sha256: str
    label: str | None = None

    def __post_init__(self) -> None:
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")
        if not _SHA256.fullmatch(self.sha256):
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        if self.label is not None:
            _unicode_scalar(self.label, "input label")


@dataclass(frozen=True, slots=True)
class TransformationRecord:
    stage: Literal["decoding", "normalizing", "aligning"]
    transformation_id: str
    parameters: JsonObject = field(default_factory=dict)

    def __post_init__(self) -> None:
        _identifier(self.transformation_id)
        _json_safe(self.parameters)


@dataclass(frozen=True, slots=True)
class ResourceUsage:
    name: str
    limit: int
    used: int

    def __post_init__(self) -> None:
        _identifier(self.name)
        if self.limit < 0 or self.used < 0:
            raise ValueError("resource counts must be non-negative")


@dataclass(frozen=True, slots=True)
class ComparisonProvenance:
    inputs: tuple[InputProvenance, InputProvenance]
    spec: JsonObject
    transformations: tuple[TransformationRecord, ...]
    comparator_id: str
    comparator_version: str
    algorithm_id: str
    implementation_version: str
    seeds: tuple[int, ...] = ()
    resources: tuple[ResourceUsage, ...] = ()

    def __post_init__(self) -> None:
        if tuple(item.role for item in self.inputs) != ("before", "after"):
            raise ValueError("input provenance must be ordered before, after")
        _json_safe(self.spec)
        _identifier(self.comparator_id)
        _identifier(self.algorithm_id)
        _unicode_scalar(self.comparator_version, "comparator version")
        _unicode_scalar(self.implementation_version, "implementation version")
        names = [item.name for item in self.resources]
        if len(names) != len(set(names)):
            raise ValueError("resource usage names must be unique")
        object.__setattr__(
            self, "resources", tuple(sorted(self.resources, key=lambda x: x.name))
        )


@dataclass(frozen=True, slots=True)
class FiniteValue:
    kind: Literal["finite"] = field(default="finite", init=False)
    value: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError("FiniteValue must contain a finite number")
        try:
            normalized = float(self.value)
        except (OverflowError, TypeError, ValueError) as error:
            raise ValueError("FiniteValue must contain a finite number") from error
        if not math.isfinite(normalized):
            raise ValueError("FiniteValue must contain a finite number")
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True, slots=True)
class NaNValue:
    kind: Literal["nan"] = field(default="nan", init=False)


@dataclass(frozen=True, slots=True)
class PositiveInfinityValue:
    kind: Literal["positive_infinity"] = field(default="positive_infinity", init=False)


@dataclass(frozen=True, slots=True)
class NegativeInfinityValue:
    kind: Literal["negative_infinity"] = field(default="negative_infinity", init=False)


type NumericValue = (
    FiniteValue | NaNValue | PositiveInfinityValue | NegativeInfinityValue
)


@dataclass(frozen=True, slots=True)
class Metric:
    name: str
    value: NumericValue
    unit: str
    direction: MetricDirection
    aggregation: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.name)
        _identifier(self.unit)
        if self.aggregation is not None:
            _identifier(self.aggregation)


@dataclass(frozen=True, slots=True)
class PolicyEvaluation:
    rule_id: str
    verdict: Verdict
    metric_name: str | None = None
    operator: Literal["eq", "ne", "lt", "le", "gt", "ge"] | None = None
    threshold: NumericValue | None = None
    observed: NumericValue | None = None

    def __post_init__(self) -> None:
        _identifier(self.rule_id)
        if self.metric_name is not None:
            _identifier(self.metric_name)
        optional = (self.metric_name, self.operator, self.threshold, self.observed)
        if any(value is None for value in optional) and any(
            value is not None for value in optional
        ):
            raise ValueError(
                "metric evaluation fields must be all present or all absent"
            )


@dataclass(frozen=True, slots=True)
class SummaryCount:
    name: str
    value: int
    unit: str

    def __post_init__(self) -> None:
        _identifier(self.name)
        _identifier(self.unit)
        if self.value < 0:
            raise ValueError("summary counts must be non-negative")


@dataclass(frozen=True, slots=True)
class DiffSummary:
    change_count: int | None
    counts: tuple[SummaryCount, ...]

    def __post_init__(self) -> None:
        if self.change_count is not None and self.change_count < 0:
            raise ValueError("change_count must be non-negative")
        names = [item.name for item in self.counts]
        if len(names) != len(set(names)):
            raise ValueError("summary count names must be unique")
        object.__setattr__(
            self, "counts", tuple(sorted(self.counts, key=lambda x: x.name))
        )


@dataclass(frozen=True, slots=True)
class HunkLine:
    kind: Literal["equal", "delete", "insert"]
    content: str
    terminator: Literal["", "\n", "\r\n", "\r"]
    before_line: int | None
    after_line: int | None

    def __post_init__(self) -> None:
        if self.kind not in ("equal", "delete", "insert"):
            raise ValueError("unknown hunk line kind")
        if self.terminator not in ("", "\n", "\r\n", "\r"):
            raise ValueError("unknown line terminator")
        _json_safe(self.content)
        if "\n" in self.content or "\r" in self.content:
            raise ValueError("hunk line content must not contain line terminators")
        if self.kind == "equal" and (
            self.before_line is None or self.after_line is None
        ):
            raise ValueError("equal hunk lines require both line numbers")
        if self.kind == "delete" and (
            self.before_line is None or self.after_line is not None
        ):
            raise ValueError("delete hunk lines require only a before line")
        if self.kind == "insert" and (
            self.before_line is not None or self.after_line is None
        ):
            raise ValueError("insert hunk lines require only an after line")
        if self.before_line is not None and self.before_line < 1:
            raise ValueError("line numbers are one-based")
        if self.after_line is not None and self.after_line < 1:
            raise ValueError("line numbers are one-based")


@dataclass(frozen=True, slots=True)
class TextHunk:
    kind: Literal["text_hunk"] = field(default="text_hunk", init=False)
    before_start_line: int = 1
    before_line_count: int = 0
    after_start_line: int = 1
    after_line_count: int = 0
    lines: tuple[HunkLine, ...] = ()

    def __post_init__(self) -> None:
        if self.before_start_line < 1 or self.after_start_line < 1:
            raise ValueError("hunk start lines are one-based")
        if self.before_line_count < 0 or self.after_line_count < 0:
            raise ValueError("hunk line counts must be non-negative")
        before_count = sum(line.kind != "insert" for line in self.lines)
        after_count = sum(line.kind != "delete" for line in self.lines)
        if (before_count, after_count) != (
            self.before_line_count,
            self.after_line_count,
        ):
            raise ValueError("hunk spans must match their line payload")
        if not any(line.kind != "equal" for line in self.lines):
            raise ValueError("a text hunk must contain at least one changed line")
        expected_before = self.before_start_line
        expected_after = self.after_start_line
        insert_seen = False
        for line in self.lines:
            if line.before_line is not None:
                if line.before_line != expected_before:
                    raise ValueError("before line numbers must be contiguous")
                expected_before += 1
            if line.after_line is not None:
                if line.after_line != expected_after:
                    raise ValueError("after line numbers must be contiguous")
                expected_after += 1
            if line.kind == "equal":
                insert_seen = False
            elif line.kind == "insert":
                insert_seen = True
            elif insert_seen:
                raise ValueError(
                    "delete lines must precede insert lines in a change run"
                )


@dataclass(frozen=True, slots=True)
class ExtensionChange:
    kind: str
    plugin_id: str
    schema_version: int
    payload: JsonObject

    def __post_init__(self) -> None:
        _identifier(self.kind, namespaced=True)
        _identifier(self.plugin_id)
        if self.schema_version < 1:
            raise ValueError("extension schema_version must be positive")
        _json_safe(self.payload)


type Change = TextHunk | ExtensionChange


@dataclass(frozen=True, slots=True)
class ChangeSet:
    completeness: ChangeCompleteness
    items: tuple[Change, ...]
    total_count: int | None
    returned_count: int
    omitted_count: int | None
    selection: ChangeSelection
    limit: int | None
    limit_reason: Literal["change_items", "change_payload_bytes"] | None = None

    def __post_init__(self) -> None:
        if self.returned_count != len(self.items) or self.returned_count < 0:
            raise ValueError("returned_count must equal the item count")
        if self.limit is not None and self.limit < 0:
            raise ValueError("change limit must be non-negative")
        if self.limit_reason not in (
            None,
            "change_items",
            "change_payload_bytes",
        ):
            raise ValueError("unknown change limit reason")
        if self.completeness is ChangeCompleteness.COMPLETE:
            if (
                self.total_count != self.returned_count
                or self.omitted_count != 0
                or self.selection is not ChangeSelection.ALL
                or self.limit is not None
                or self.limit_reason is not None
            ):
                raise ValueError("invalid complete ChangeSet")
        elif self.completeness is ChangeCompleteness.TRUNCATED:
            if (
                self.total_count is None
                or self.omitted_count is None
                or self.omitted_count <= 0
                or self.total_count != self.returned_count + self.omitted_count
                or self.selection is not ChangeSelection.SOURCE_ORDER_PREFIX
                or self.limit is None
            ):
                raise ValueError("invalid truncated ChangeSet")
        elif (
            self.total_count is not None
            or self.omitted_count is not None
            or self.selection is not ChangeSelection.ALGORITHM_PARTIAL
            or self.limit_reason is not None
        ):
            raise ValueError("invalid partial ChangeSet")


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    artifact_id: str
    kind: str
    media_type: str
    uri: str
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        _identifier(self.artifact_id)
        _identifier(self.kind)
        _unicode_scalar(self.media_type, "artifact media type")
        _safe_artifact_uri(self.uri)
        if not _SHA256.fullmatch(self.sha256):
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        if self.size_bytes < 0:
            raise ValueError("artifact size must be non-negative")


@dataclass(frozen=True, slots=True)
class DiffResult:
    relation: Relation
    verdict: Verdict
    fidelity: Fidelity
    summary: DiffSummary
    changes: ChangeSet
    metrics: tuple[Metric, ...]
    evaluations: tuple[PolicyEvaluation, ...]
    artifacts: tuple[ArtifactRef, ...]
    provenance: ComparisonProvenance

    def __post_init__(self) -> None:
        if self.summary.change_count != self.changes.total_count:
            raise ValueError("summary and ChangeSet totals must agree")
        if (
            self.changes.completeness is ChangeCompleteness.PARTIAL
            and self.relation is Relation.EQUAL
        ):
            raise ValueError("a partial result must never claim equality")
        metric_names = [metric.name for metric in self.metrics]
        if len(metric_names) != len(set(metric_names)):
            raise ValueError("metric names must be unique")
        if not self.evaluations:
            raise ValueError("at least one policy evaluation is required")
        severity = {Verdict.PASS: 0, Verdict.WARN: 1, Verdict.FAIL: 2}
        expected = max(
            self.evaluations, key=lambda item: severity[item.verdict]
        ).verdict
        if self.verdict is not expected:
            raise ValueError("verdict must equal the highest policy evaluation")
        object.__setattr__(
            self, "metrics", tuple(sorted(self.metrics, key=lambda x: x.name))
        )
        object.__setattr__(
            self,
            "evaluations",
            tuple(sorted(self.evaluations, key=lambda x: x.rule_id)),
        )
        object.__setattr__(
            self,
            "artifacts",
            tuple(sorted(self.artifacts, key=lambda x: x.artifact_id)),
        )


@dataclass(frozen=True, slots=True)
class CompletedOutcome:
    schema_version: Literal[1] = field(default=SCHEMA_VERSION, init=False)
    kind: Literal["completed"] = field(default="completed", init=False)
    execution: ExecutionRecord = field(kw_only=True)
    result: DiffResult = field(kw_only=True)

    def __post_init__(self) -> None:
        if self.execution.last_completed_stage is not PipelineStage.AGGREGATING:
            raise ValueError("completed outcome must finish aggregation")


@dataclass(frozen=True, slots=True)
class UnavailableOutcome:
    schema_version: Literal[1] = field(default=SCHEMA_VERSION, init=False)
    kind: Literal["unavailable"] = field(default="unavailable", init=False)
    execution: ExecutionRecord = field(kw_only=True)
    problem: CapabilityProblem = field(kw_only=True)

    def __post_init__(self) -> None:
        if (
            not self.execution.stages
            or self.execution.stages[-1].stage is not self.problem.stage
            or self.execution.stages[-1].disposition is not StageDisposition.UNAVAILABLE
        ):
            raise ValueError("unavailable outcome must match its terminal stage")


@dataclass(frozen=True, slots=True)
class FailedOutcome:
    schema_version: Literal[1] = field(default=SCHEMA_VERSION, init=False)
    kind: Literal["failed"] = field(default="failed", init=False)
    execution: ExecutionRecord = field(kw_only=True)
    problem: ExecutionProblem = field(kw_only=True)

    def __post_init__(self) -> None:
        if (
            not self.execution.stages
            or self.execution.stages[-1].stage is not self.problem.stage
            or self.execution.stages[-1].disposition is not StageDisposition.FAILED
        ):
            raise ValueError("failed outcome must match its terminal stage")


type CompareOutcome = CompletedOutcome | UnavailableOutcome | FailedOutcome
