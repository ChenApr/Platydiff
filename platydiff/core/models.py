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
SCHEMA_VERSION_V2: Literal[2] = 2
SCHEMA_VERSION_V3: Literal[3] = 3
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_DISTRIBUTION_NAME = re.compile(
    r"^(?:[A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9])\Z"
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_JSON_NUMBER = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$")
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


def _identity_text(value: object, field_name: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    _unicode_scalar(value, field_name)
    if not value or len(value.encode("utf-8")) > 1024:
        raise ValueError(f"{field_name} must be non-empty and bounded")
    if "/" in value or "\\" in value:
        raise ValueError(f"{field_name} must not contain a filesystem path")
    if any(
        ord(character) < 0x20 or 0x7F <= ord(character) <= 0x9F for character in value
    ):
        raise ValueError(f"{field_name} must not contain control characters")


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


class JsonNumberMode(StrEnum):
    VALUE = "value"
    LEXICAL = "lexical"


class StructuredDetailMode(StrEnum):
    VALUES = "values"
    DIGEST_ONLY = "digest_only"


class StructuredType(StrEnum):
    NULL = "null"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    DECIMAL = "decimal"
    STRING = "string"
    SEQUENCE = "sequence"
    MAPPING = "mapping"


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


@dataclass(frozen=True, slots=True)
class StructuredResourceLimits:
    """Deterministic resource limits shared by structured tree comparators."""

    max_input_bytes: int = 16 * 1024 * 1024
    max_scalar_bytes: int = 1024 * 1024
    max_depth: int = 256
    max_nodes: int = 1_000_000
    max_number_digits: int = 10_000
    max_abs_exponent: int = 1_000_000
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            _bounded_integer(getattr(self, name), name, 0, _MAX_EXACT_INTEGER)


@dataclass(frozen=True, slots=True)
class JsonCompareSpec:
    """Explicit intent for strict RFC 8259 semantic comparison."""

    kind: Literal["json"] = field(default="json", init=False)
    encoding: TextEncoding = TextEncoding.UTF8
    number_mode: JsonNumberMode = JsonNumberMode.VALUE
    detail_mode: StructuredDetailMode = StructuredDetailMode.VALUES
    limits: StructuredResourceLimits = field(default_factory=StructuredResourceLimits)

    def __post_init__(self) -> None:
        if not isinstance(self.encoding, TextEncoding):
            raise ValueError("JSON encoding must be a TextEncoding")
        if not isinstance(self.number_mode, JsonNumberMode):
            raise ValueError("number_mode must be a JsonNumberMode")
        if not isinstance(self.detail_mode, StructuredDetailMode):
            raise ValueError("detail_mode must be a StructuredDetailMode")
        if not isinstance(self.limits, StructuredResourceLimits):
            raise ValueError("JSON limits must be StructuredResourceLimits")


@dataclass(frozen=True, slots=True)
class YamlResourceLimits(StructuredResourceLimits):
    """Deterministic resource limits for the restricted YAML profile."""

    max_aliases: int = 10_000
    max_expanded_nodes: int = 1_000_000
    max_expanded_scalar_bytes: int = 16 * 1024 * 1024

    def __post_init__(self) -> None:
        super(YamlResourceLimits, self).__post_init__()
        for name in (
            "max_aliases",
            "max_expanded_nodes",
            "max_expanded_scalar_bytes",
        ):
            _bounded_integer(getattr(self, name), name, 0, _MAX_EXACT_INTEGER)


@dataclass(frozen=True, slots=True)
class YamlCompareSpec:
    """Contract-only intent for the restricted YAML 1.2 Core profile."""

    kind: Literal["yaml"] = field(default="yaml", init=False)
    profile: Literal["yaml12_core_safe"] = "yaml12_core_safe"
    encoding: TextEncoding = TextEncoding.UTF8
    detail_mode: StructuredDetailMode = StructuredDetailMode.VALUES
    limits: YamlResourceLimits = field(default_factory=YamlResourceLimits)

    def __post_init__(self) -> None:
        if self.profile != "yaml12_core_safe":
            raise ValueError("unknown YAML profile")
        if not isinstance(self.encoding, TextEncoding):
            raise ValueError("YAML encoding must be a TextEncoding")
        if not isinstance(self.detail_mode, StructuredDetailMode):
            raise ValueError("detail_mode must be a StructuredDetailMode")
        if not isinstance(self.limits, YamlResourceLimits):
            raise ValueError("YAML limits must be YamlResourceLimits")


@dataclass(frozen=True, slots=True)
class NumericPolicy:
    """Explicit binary64 equality policy for table cells and array elements."""

    atol: float = 0.0
    rtol: float = 0.0
    relative_reference: Literal["before"] = "before"
    nan_equal: bool = False
    signed_zero_equal: bool = True

    def __post_init__(self) -> None:
        for name in ("atol", "rtol"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a finite non-negative number")
            normalized = float(value)
            if not math.isfinite(normalized) or normalized < 0:
                raise ValueError(f"{name} must be a finite non-negative number")
            object.__setattr__(self, name, normalized)
        if self.relative_reference != "before":
            raise ValueError("relative_reference must be before")
        if not isinstance(self.nan_equal, bool):
            raise ValueError("nan_equal must be a boolean")
        if not isinstance(self.signed_zero_equal, bool):
            raise ValueError("signed_zero_equal must be a boolean")


@dataclass(frozen=True, slots=True)
class ColumnSpec:
    """One explicit delimited-table column contract."""

    name: str
    dtype: Literal["string", "integer", "float64", "boolean"]
    missing_tokens: tuple[str, ...] = ()
    numeric: NumericPolicy | None = None

    def __post_init__(self) -> None:
        _unicode_scalar(self.name, "column name")
        if not self.name:
            raise ValueError("column name must be non-empty")
        if self.dtype not in ("string", "integer", "float64", "boolean"):
            raise ValueError("unknown column dtype")
        if not isinstance(self.missing_tokens, tuple):
            raise ValueError("missing_tokens must be a tuple")
        for token in self.missing_tokens:
            if not isinstance(token, str):
                raise ValueError("missing tokens must be strings")
            _unicode_scalar(token, "missing token")
        if len(self.missing_tokens) != len(set(self.missing_tokens)):
            raise ValueError("missing tokens must be unique")
        if self.dtype == "float64":
            if not isinstance(self.numeric, NumericPolicy):
                raise ValueError("float64 columns require a numeric policy")
        elif self.numeric is not None:
            raise ValueError("numeric policy is allowed only for float64 columns")


@dataclass(frozen=True, slots=True)
class TableResourceLimits:
    """Deterministic resource limits for delimited-table comparison."""

    max_input_bytes: int = 16 * 1024 * 1024
    max_cell_bytes: int = 1024 * 1024
    max_rows: int = 200_000
    max_columns: int = 10_000
    max_cells: int = 1_000_000
    max_number_digits: int = 10_000
    max_abs_exponent: int = 1_000_000
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            _bounded_integer(getattr(self, name), name, 0, _MAX_EXACT_INTEGER)


@dataclass(frozen=True, slots=True)
class TableCompareSpec:
    """Contract-only explicit intent for a CSV or TSV table."""

    dialect: Literal["csv", "tsv"]
    kind: Literal["table"] = field(default="table", init=False)
    encoding: TextEncoding = TextEncoding.UTF8
    header: Literal["first_row", "none"] = "first_row"
    alignment: Literal["position", "key"] = "position"
    key_columns: tuple[str, ...] = ()
    column_order: Literal["exact", "by_name"] = "exact"
    columns: tuple[ColumnSpec, ...] = ()
    detail_mode: StructuredDetailMode = StructuredDetailMode.VALUES
    limits: TableResourceLimits = field(default_factory=TableResourceLimits)

    def __post_init__(self) -> None:
        if self.dialect not in ("csv", "tsv"):
            raise ValueError("unknown table dialect")
        if not isinstance(self.encoding, TextEncoding):
            raise ValueError("table encoding must be a TextEncoding")
        if self.header not in ("first_row", "none"):
            raise ValueError("unknown table header policy")
        if self.alignment not in ("position", "key"):
            raise ValueError("unknown table alignment")
        if self.column_order not in ("exact", "by_name"):
            raise ValueError("unknown table column order")
        if not isinstance(self.key_columns, tuple) or not isinstance(
            self.columns, tuple
        ):
            raise ValueError("table column collections must be tuples")
        for name in self.key_columns:
            if not isinstance(name, str):
                raise ValueError("key column names must be strings")
            _unicode_scalar(name, "key column name")
            if not name:
                raise ValueError("key column names must be non-empty")
        if len(self.key_columns) != len(set(self.key_columns)):
            raise ValueError("key column names must be unique")
        if self.alignment == "key":
            if self.header != "first_row" or not self.key_columns:
                raise ValueError("key alignment requires a header and key columns")
        elif self.key_columns:
            raise ValueError("positional alignment forbids key columns")
        if any(not isinstance(column, ColumnSpec) for column in self.columns):
            raise ValueError("columns must contain ColumnSpec values")
        column_names = tuple(column.name for column in self.columns)
        if len(column_names) != len(set(column_names)):
            raise ValueError("column names must be unique")
        if self.key_columns and self.columns:
            columns_by_name = {column.name: column for column in self.columns}
            for name in self.key_columns:
                column = columns_by_name.get(name)
                if (
                    column is None
                    or column.dtype not in ("string", "integer")
                    or column.missing_tokens
                ):
                    raise ValueError(
                        "key columns must be declared string/integer "
                        "non-missing columns"
                    )
        if not isinstance(self.detail_mode, StructuredDetailMode):
            raise ValueError("detail_mode must be a StructuredDetailMode")
        if not isinstance(self.limits, TableResourceLimits):
            raise ValueError("table limits must be TableResourceLimits")


@dataclass(frozen=True, slots=True)
class ArrayResourceLimits:
    """Deterministic resource limits for dense-array comparison."""

    max_rank: int = 32
    max_elements: int = 2_000_000
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            _bounded_integer(getattr(self, name), name, 0, _MAX_EXACT_INTEGER)


@dataclass(frozen=True, slots=True)
class ArrayCompareSpec:
    """Contract-only intent for positional dense-array comparison."""

    kind: Literal["array"] = field(default="array", init=False)
    alignment: Literal["position"] = "position"
    numeric: NumericPolicy = field(default_factory=NumericPolicy)
    limits: ArrayResourceLimits = field(default_factory=ArrayResourceLimits)

    def __post_init__(self) -> None:
        if self.alignment != "position":
            raise ValueError("array alignment must be position")
        if not isinstance(self.numeric, NumericPolicy):
            raise ValueError("array numeric policy must be a NumericPolicy")
        if not isinstance(self.limits, ArrayResourceLimits):
            raise ValueError("array limits must be ArrayResourceLimits")


type CompareSpec = AutoCompareSpec | TextCompareSpec | BinaryCompareSpec
type CompareSpecV3 = (
    CompareSpec
    | JsonCompareSpec
    | YamlCompareSpec
    | TableCompareSpec
    | ArrayCompareSpec
)


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
class ProviderIdentity:
    """Path-free identity for one loaded third-party provider in schema v2."""

    plugin_id: str
    plugin_version: str
    distribution_name: str
    distribution_version: str
    manifest_schema_version: int
    api_major: int
    negotiated_api_minor: int
    negotiated_host_features: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _identifier(self.plugin_id, namespaced=True)
        for name in (
            "plugin_version",
            "distribution_name",
            "distribution_version",
        ):
            _identity_text(getattr(self, name), name)
        if not _DISTRIBUTION_NAME.fullmatch(self.distribution_name):
            raise ValueError(
                "distribution_name must be a valid Python distribution name"
            )
        _bounded_integer(
            self.manifest_schema_version,
            "manifest_schema_version",
            1,
            _MAX_EXACT_INTEGER,
        )
        _bounded_integer(self.api_major, "api_major", 1, _MAX_EXACT_INTEGER)
        _bounded_integer(
            self.negotiated_api_minor,
            "negotiated_api_minor",
            0,
            _MAX_EXACT_INTEGER,
        )
        for feature in self.negotiated_host_features:
            _identifier(feature)
        if self.negotiated_host_features != tuple(
            sorted(set(self.negotiated_host_features))
        ):
            raise ValueError("negotiated host features must be unique and sorted")


@dataclass(frozen=True, slots=True)
class CapabilityAttemptV2:
    """A schema-v2 attempt with complete capability and provider identity."""

    capability_id: str
    backend_id: str | None
    disposition: Literal["selected", "rejected", "fallback", "unavailable", "failed"]
    reason_code: str | None = None
    capability_version: str | None = None
    backend_version: str | None = None
    provider: ProviderIdentity | None = None

    def __post_init__(self) -> None:
        _identifier(self.capability_id)
        if self.backend_id is not None:
            _identifier(self.backend_id)
        if self.reason_code is not None:
            _identifier(self.reason_code)
        if self.disposition not in (
            "selected",
            "rejected",
            "fallback",
            "unavailable",
            "failed",
        ):
            raise ValueError("unknown schema-v2 capability attempt disposition")
        for name in ("capability_version", "backend_version"):
            value = getattr(self, name)
            if value is not None:
                _identity_text(value, name)
        if self.provider is not None:
            if not isinstance(self.provider, ProviderIdentity):
                raise ValueError("attempt provider must be a ProviderIdentity")
            if not self.capability_id.startswith(f"{self.provider.plugin_id}."):
                raise ValueError("provider-backed capability must belong to its plugin")
            if self.capability_version is None:
                raise ValueError(
                    "provider-backed attempt requires a capability version"
                )
            if (self.backend_id is None) != (self.backend_version is None):
                raise ValueError(
                    "provider-backed backend identity must be provided together"
                )
            if self.backend_id is not None and not self.backend_id.startswith(
                f"{self.provider.plugin_id}."
            ):
                raise ValueError("provider-backed backend must belong to its plugin")


@dataclass(frozen=True, slots=True)
class PluginHostExecutionRecord:
    """Exact enabled and loaded provider snapshot used by a schema-v2 run."""

    enabled_plugin_ids: tuple[str, ...]
    loaded_providers: tuple[ProviderIdentity, ...]

    def __post_init__(self) -> None:
        for plugin_id in self.enabled_plugin_ids:
            _identifier(plugin_id, namespaced=True)
        if self.enabled_plugin_ids != tuple(sorted(set(self.enabled_plugin_ids))):
            raise ValueError("enabled plugin IDs must be unique and sorted")
        provider_ids = [provider.plugin_id for provider in self.loaded_providers]
        if provider_ids != sorted(set(provider_ids)):
            raise ValueError("loaded providers must be unique and sorted")
        if not set(provider_ids).issubset(self.enabled_plugin_ids):
            raise ValueError("loaded providers must be enabled")


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    severity: DiagnosticSeverity
    stage: PipelineStage | None
    message: str
    details: JsonObject = field(default_factory=dict)

    def __post_init__(self) -> None:
        _identifier(self.code)
        if not isinstance(self.severity, DiagnosticSeverity):
            raise ValueError("diagnostic severity must be a DiagnosticSeverity")
        if self.stage is not None and not isinstance(self.stage, PipelineStage):
            raise ValueError("diagnostic stage must be a PipelineStage")
        _unicode_scalar(self.message, "diagnostic message")
        _json_safe(self.details)


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    started_at: str
    finished_at: str
    duration_ns: int
    stages: tuple[StageRecord, ...]
    attempts: tuple[CapabilityAttempt | CapabilityAttemptV2, ...] = ()
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
        if type(self) is ExecutionRecord and any(
            isinstance(attempt, CapabilityAttemptV2) for attempt in self.attempts
        ):
            raise ValueError("schema-v1 execution cannot contain schema-v2 attempts")
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
            and detection_records[0].disposition is StageDisposition.COMPLETED
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


@dataclass(frozen=True, slots=True)
class ExecutionRecordV2(ExecutionRecord):
    """Schema-v2 execution with the optional immutable plugin-host snapshot."""

    plugin_host: PluginHostExecutionRecord | None = None

    def __post_init__(self) -> None:
        super(ExecutionRecordV2, self).__post_init__()
        if self.plugin_host is not None and not isinstance(
            self.plugin_host, PluginHostExecutionRecord
        ):
            raise ValueError("plugin_host must be a PluginHostExecutionRecord")
        if not all(
            isinstance(attempt, CapabilityAttemptV2) for attempt in self.attempts
        ):
            raise ValueError("schema-v2 execution requires schema-v2 attempts")
        provider_attempts = tuple(
            attempt.provider
            for attempt in self.attempts
            if isinstance(attempt, CapabilityAttemptV2) and attempt.provider is not None
        )
        if provider_attempts and (
            self.plugin_host is None
            or any(
                provider not in self.plugin_host.loaded_providers
                for provider in provider_attempts
            )
        ):
            raise ValueError("attempt provider must be a loaded provider")


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
class ExecutionProblemV2:
    """Schema-v2 failed problem mapping, including selected-plugin failure."""

    code: str
    status_code: int
    stage: PipelineStage
    message: str
    details: JsonObject = field(default_factory=dict)
    retryable: bool = False

    def __post_init__(self) -> None:
        expected = dict(_PROBLEM_CODES)
        expected["plugin_execution_failure"] = (502, "failed")
        if expected.get(self.code) != (self.status_code, "failed"):
            raise ValueError("invalid schema-v2 failed problem mapping")
        _unicode_scalar(self.message, "problem message")
        _json_safe(self.details)


@dataclass(frozen=True, slots=True)
class CapabilityProblemV2:
    """Schema-v2 unavailable problem mapping."""

    code: str
    status_code: int
    stage: PipelineStage
    message: str
    details: JsonObject = field(default_factory=dict)
    retryable: bool = False

    def __post_init__(self) -> None:
        if _PROBLEM_CODES.get(self.code) != (self.status_code, "unavailable"):
            raise ValueError("invalid schema-v2 unavailable problem mapping")
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
class ComparisonProvenanceV2(ComparisonProvenance):
    """Schema-v2 provenance with selected comparator and detector providers."""

    provider: ProviderIdentity | None = None
    detector_provider: ProviderIdentity | None = None

    def __post_init__(self) -> None:
        super(ComparisonProvenanceV2, self).__post_init__()
        if self.provider is not None and not isinstance(
            self.provider, ProviderIdentity
        ):
            raise ValueError("provider must be a ProviderIdentity")
        if self.detector_provider is not None and not isinstance(
            self.detector_provider, ProviderIdentity
        ):
            raise ValueError("detector_provider must be a ProviderIdentity")


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
        if not isinstance(
            self.value,
            (FiniteValue, NaNValue, PositiveInfinityValue, NegativeInfinityValue),
        ):
            raise ValueError("metric value must be a numeric value")
        if not isinstance(self.direction, MetricDirection):
            raise ValueError("metric direction must be a MetricDirection")
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
        if not isinstance(self.verdict, Verdict):
            raise ValueError("policy verdict must be a Verdict")
        if self.metric_name is not None:
            _identifier(self.metric_name)
        if self.operator not in (None, "eq", "ne", "lt", "le", "gt", "ge"):
            raise ValueError("unknown policy operator")
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
class BinarySpan:
    """One maximal observed mismatch range without embedded byte payload."""

    kind: Literal["binary_span"] = field(default="binary_span", init=False)
    before_offset: int = 0
    before_length: int = 0
    after_offset: int = 0
    after_length: int = 0

    def __post_init__(self) -> None:
        for name in (
            "before_offset",
            "before_length",
            "after_offset",
            "after_length",
        ):
            _bounded_integer(getattr(self, name), name, 0, _MAX_EXACT_INTEGER)
        if self.before_length == self.after_length == 0:
            raise ValueError("a binary span must contain changed bytes")
        if self.before_offset != self.after_offset:
            raise ValueError("binary span offsets must share the aligned position")
        if (
            self.before_length > 0
            and self.after_length > 0
            and self.before_length != self.after_length
        ):
            raise ValueError("replacement spans must have equal positive lengths")


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


@dataclass(frozen=True, slots=True)
class ScalarFact:
    """Bounded typed evidence for one structured scalar."""

    kind: Literal[
        "null",
        "boolean",
        "integer",
        "decimal",
        "string",
        "missing",
        "float64",
        "nan",
        "positive_infinity",
        "negative_infinity",
    ]
    value: bool | str | None
    lexical: str | None = None

    def __post_init__(self) -> None:
        if self.kind in (
            "null",
            "missing",
            "nan",
            "positive_infinity",
            "negative_infinity",
        ):
            if self.value is not None:
                raise ValueError(f"{self.kind} fact requires a null value")
        elif self.kind == "boolean":
            if not isinstance(self.value, bool):
                raise ValueError("boolean fact requires a boolean value")
        elif self.kind in ("integer", "decimal", "string", "float64"):
            if not isinstance(self.value, str):
                raise ValueError(f"{self.kind} fact requires a string value")
            _unicode_scalar(self.value, "scalar fact value")
        else:
            raise ValueError("unknown scalar fact kind")
        if self.kind == "integer" and (
            not isinstance(self.value, str)
            or re.fullmatch(r"0|-?[1-9][0-9]*", self.value) is None
        ):
            raise ValueError("integer fact value must be canonical base-10 text")
        if self.kind == "decimal" and (
            not isinstance(self.value, str)
            or re.fullmatch(
                r"-?(?:0|[1-9](?:[0-9]*[1-9])?)E(?:0|-?[1-9][0-9]*)",
                self.value,
            )
            is None
            or self.value.startswith("-0E")
        ):
            raise ValueError(
                "decimal fact value must be canonical coefficient/exponent text"
            )
        if self.lexical is not None:
            if self.kind not in ("integer", "decimal"):
                raise ValueError("lexical text is allowed only for JSON number facts")
            _unicode_scalar(self.lexical, "scalar fact lexical token")
            if _JSON_NUMBER.fullmatch(self.lexical) is None:
                raise ValueError("lexical fact text must be a valid JSON number")
            lexical_is_decimal = "." in self.lexical or "e" in self.lexical.lower()
            if lexical_is_decimal != (self.kind == "decimal"):
                raise ValueError("lexical number spelling must match the fact kind")


@dataclass(frozen=True, slots=True)
class SubtreeFact:
    """Non-recursive evidence for one structured container."""

    kind: Literal["sequence", "mapping"]
    descendant_count: int
    scalar_count: int

    def __post_init__(self) -> None:
        if self.kind not in ("sequence", "mapping"):
            raise ValueError("unknown subtree fact kind")
        _bounded_integer(
            self.descendant_count, "descendant_count", 0, _MAX_EXACT_INTEGER
        )
        _bounded_integer(self.scalar_count, "scalar_count", 0, _MAX_EXACT_INTEGER)
        if self.scalar_count > self.descendant_count:
            raise ValueError("scalar_count must not exceed descendant_count")


type StructuredFact = ScalarFact | SubtreeFact


@dataclass(frozen=True, slots=True)
class TableRowFact:
    """One complete table row in aligned-column order."""

    kind: Literal["table_row"] = field(default="table_row", init=False)
    cells: tuple[tuple[str, ScalarFact], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.cells, tuple):
            raise ValueError("table row cells must be a tuple")
        names: list[str] = []
        for cell in self.cells:
            if not isinstance(cell, tuple) or len(cell) != 2:
                raise ValueError("table row cells must be name/fact pairs")
            name, fact = cell
            if not isinstance(name, str):
                raise ValueError("table row column names must be strings")
            _unicode_scalar(name, "table row column name")
            if not name:
                raise ValueError("table row column names must be non-empty")
            if not isinstance(fact, ScalarFact):
                raise ValueError("table row cells must carry ScalarFact values")
            names.append(name)
        if len(names) != len(set(names)):
            raise ValueError("table row column names must be unique")


@dataclass(frozen=True, slots=True)
class ColumnSchemaFact:
    """One complete declared table-column schema."""

    name: str
    dtype: Literal["string", "integer", "float64", "boolean"]
    missing_token_count: int
    numeric: NumericPolicy | None
    kind: Literal["table_column_schema"] = field(
        default="table_column_schema", init=False
    )

    def __post_init__(self) -> None:
        _unicode_scalar(self.name, "column schema name")
        if not self.name:
            raise ValueError("column schema name must be non-empty")
        if self.dtype not in ("string", "integer", "float64", "boolean"):
            raise ValueError("unknown column schema dtype")
        _bounded_integer(
            self.missing_token_count,
            "missing_token_count",
            0,
            _MAX_EXACT_INTEGER,
        )
        if self.dtype == "float64":
            if not isinstance(self.numeric, NumericPolicy):
                raise ValueError("float64 column schema requires a numeric policy")
        elif self.numeric is not None:
            raise ValueError("numeric policy is allowed only for float64 columns")


@dataclass(frozen=True, slots=True)
class ColumnOrderFact:
    """One complete ordered table-column name sequence."""

    names: tuple[str, ...]
    kind: Literal["table_column_order"] = field(
        default="table_column_order", init=False
    )

    def __post_init__(self) -> None:
        if not isinstance(self.names, tuple):
            raise ValueError("column-order names must be a tuple")
        for name in self.names:
            if not isinstance(name, str):
                raise ValueError("column-order names must be strings")
            _unicode_scalar(name, "column-order name")
            if not name:
                raise ValueError("column-order names must be non-empty")
        if len(self.names) != len(set(self.names)):
            raise ValueError("column-order names must be unique")


type TableFact = ScalarFact | TableRowFact | ColumnSchemaFact | ColumnOrderFact


def _validate_table_scalar_contract(fact: ScalarFact) -> None:
    """Validate scalar grammar that is specific to table evidence."""

    if fact.lexical is not None:
        raise ValueError("table scalar facts must not carry JSON lexical text")
    if fact.kind != "float64":
        return
    if not isinstance(fact.value, str):
        raise ValueError("table scalar float64 facts require canonical C99 hex")
    try:
        numeric = float.fromhex(fact.value)
    except ValueError as error:
        raise ValueError(
            "table scalar float64 facts require canonical C99 hex"
        ) from error
    if not math.isfinite(numeric) or numeric.hex() != fact.value:
        raise ValueError("table scalar float64 facts require canonical C99 hex")


def _validate_table_fact_scalar_contract(fact: TableFact) -> None:
    if isinstance(fact, ScalarFact):
        _validate_table_scalar_contract(fact)
    elif isinstance(fact, TableRowFact):
        for _, cell in fact.cells:
            _validate_table_scalar_contract(cell)


@dataclass(frozen=True, slots=True)
class StructuredChange:
    """One deterministic JSON-Pointer observation, not a patch operation."""

    kind: Literal["structured_change"] = field(default="structured_change", init=False)
    operation: Literal["add", "remove", "replace"] = "replace"
    path: str = ""
    before_type: StructuredType | None = None
    after_type: StructuredType | None = None
    before_digest: str | None = None
    after_digest: str | None = None
    before_fact: StructuredFact | None = None
    after_fact: StructuredFact | None = None

    def __post_init__(self) -> None:
        if self.operation not in ("add", "remove", "replace"):
            raise ValueError("unknown structured change operation")
        _unicode_scalar(self.path, "structured change path")
        if self.path and not self.path.startswith("/"):
            raise ValueError("structured change path must be an RFC 6901 pointer")
        cursor = 0
        while cursor < len(self.path):
            if self.path[cursor] == "~":
                if cursor + 1 >= len(self.path) or self.path[cursor + 1] not in "01":
                    raise ValueError(
                        "structured change path must be canonical RFC 6901"
                    )
                cursor += 2
            else:
                cursor += 1
        before_present = self.before_type is not None
        after_present = self.after_type is not None
        expected = {
            "add": (False, True),
            "remove": (True, False),
            "replace": (True, True),
        }[self.operation]
        if (before_present, after_present) != expected:
            raise ValueError("structured change sides do not match its operation")
        for side, value_type, digest, fact in (
            ("before", self.before_type, self.before_digest, self.before_fact),
            ("after", self.after_type, self.after_digest, self.after_fact),
        ):
            if value_type is None:
                if digest is not None or fact is not None:
                    raise ValueError(f"absent {side} side must not carry evidence")
                continue
            if not isinstance(value_type, StructuredType):
                raise ValueError(f"{side} type must be a StructuredType")
            if digest is None or not _SHA256.fullmatch(digest):
                raise ValueError(f"present {side} side requires a SHA-256 digest")
            if fact is not None:
                expected_kind = value_type.value
                if fact.kind != expected_kind:
                    raise ValueError(f"{side} fact kind must match its structured type")


@dataclass(frozen=True, slots=True)
class TableChange:
    """One atomic schema, row, or cell observation for a table."""

    operation: Literal[
        "column_add",
        "column_remove",
        "column_reorder",
        "row_add",
        "row_remove",
        "cell_replace",
    ]
    kind: Literal["table_change"] = field(default="table_change", init=False)
    row: int | None = None
    key_ordinal: int | None = None
    key: tuple[ScalarFact, ...] | None = None
    column: str | None = None
    before_digest: str | None = None
    after_digest: str | None = None
    before_fact: TableFact | None = None
    after_fact: TableFact | None = None

    def __post_init__(self) -> None:
        operations = (
            "column_add",
            "column_remove",
            "column_reorder",
            "row_add",
            "row_remove",
            "cell_replace",
        )
        if self.operation not in operations:
            raise ValueError("unknown table change operation")
        if self.row is not None:
            _bounded_integer(self.row, "row", 1, _MAX_EXACT_INTEGER)
        if self.key_ordinal is not None:
            _bounded_integer(self.key_ordinal, "key_ordinal", 1, _MAX_EXACT_INTEGER)
        if self.key is not None:
            if not isinstance(self.key, tuple) or not self.key:
                raise ValueError("table key must be a non-empty tuple")
            if self.key_ordinal is None:
                raise ValueError("table key requires key_ordinal")
            for key_fact in self.key:
                if not isinstance(key_fact, ScalarFact) or key_fact.kind not in (
                    "string",
                    "integer",
                ):
                    raise ValueError("table keys require string/integer scalar facts")
                _validate_table_scalar_contract(key_fact)
        if self.row is not None and self.key_ordinal is not None:
            raise ValueError("table row coordinates cannot mix position and key")
        if self.column is not None:
            _unicode_scalar(self.column, "table change column")
            if not self.column:
                raise ValueError("table change column must be non-empty")

        column_operation = self.operation.startswith("column_")
        row_operation = self.operation in ("row_add", "row_remove")
        if column_operation:
            if (
                self.row is not None
                or self.key_ordinal is not None
                or self.key is not None
            ):
                raise ValueError("column changes must not carry row coordinates")
            if (self.operation == "column_reorder") == (self.column is not None):
                raise ValueError("table column coordinate does not match operation")
        else:
            if (self.row is None) == (self.key_ordinal is None):
                raise ValueError("row and cell changes require exactly one coordinate")
            if row_operation and self.column is not None:
                raise ValueError("row changes must not carry a column")
            if self.operation == "cell_replace" and self.column is None:
                raise ValueError("cell replacement requires a column")

        expected_sides = {
            "column_add": (False, True),
            "column_remove": (True, False),
            "column_reorder": (True, True),
            "row_add": (False, True),
            "row_remove": (True, False),
            "cell_replace": (True, True),
        }[self.operation]
        actual_sides = (
            self.before_digest is not None,
            self.after_digest is not None,
        )
        if actual_sides != expected_sides:
            raise ValueError("table change sides do not match its operation")
        for side, digest, side_fact in (
            ("before", self.before_digest, self.before_fact),
            ("after", self.after_digest, self.after_fact),
        ):
            if digest is None:
                if side_fact is not None:
                    raise ValueError(f"absent {side} side must not carry a fact")
            elif not _SHA256.fullmatch(digest):
                raise ValueError(f"present {side} side requires a SHA-256 digest")
        expected_fact_type: type[object]
        if self.operation in ("column_add", "column_remove"):
            expected_fact_type = ColumnSchemaFact
        elif self.operation == "column_reorder":
            expected_fact_type = ColumnOrderFact
        elif row_operation:
            expected_fact_type = TableRowFact
        else:
            expected_fact_type = ScalarFact
        for operation_fact in (self.before_fact, self.after_fact):
            if operation_fact is not None and not isinstance(
                operation_fact, expected_fact_type
            ):
                raise ValueError("table change fact type does not match its operation")
            if operation_fact is not None:
                _validate_table_fact_scalar_contract(operation_fact)


@dataclass(frozen=True, slots=True)
class ArrayChange:
    """One shape, dtype, or element observation for a dense array."""

    operation: Literal["shape_replace", "dtype_replace", "element_replace"]
    index: tuple[int, ...] | None
    before_digest: str
    after_digest: str
    kind: Literal["array_change"] = field(default="array_change", init=False)
    absolute_error: NumericValue | None = None
    relative_error: NumericValue | None = None

    def __post_init__(self) -> None:
        if self.operation not in (
            "shape_replace",
            "dtype_replace",
            "element_replace",
        ):
            raise ValueError("unknown array change operation")
        if not _SHA256.fullmatch(self.before_digest) or not _SHA256.fullmatch(
            self.after_digest
        ):
            raise ValueError("array changes require SHA-256 digests")
        if self.operation == "element_replace":
            if not isinstance(self.index, tuple):
                raise ValueError("element replacement requires an index tuple")
            for component in self.index:
                _bounded_integer(component, "array index", 0, _MAX_EXACT_INTEGER)
        elif self.index is not None:
            raise ValueError("shape/dtype replacement requires a null index")
        if self.operation != "element_replace" and (
            self.absolute_error is not None or self.relative_error is not None
        ):
            raise ValueError("shape/dtype replacement must not carry errors")
        if self.absolute_error is not None and (
            not isinstance(self.absolute_error, FiniteValue)
            or self.absolute_error.value < 0
        ):
            raise ValueError("absolute_error must be finite and non-negative")
        if self.relative_error is not None:
            if isinstance(self.relative_error, FiniteValue):
                if self.relative_error.value < 0:
                    raise ValueError("relative_error must be non-negative")
            elif not isinstance(self.relative_error, PositiveInfinityValue):
                raise ValueError(
                    "relative_error must be finite non-negative or positive infinity"
                )
        if (self.absolute_error is None) != (self.relative_error is None):
            raise ValueError("array element errors must both be present or both absent")
        if isinstance(self.relative_error, PositiveInfinityValue) and (
            not isinstance(self.absolute_error, FiniteValue)
            or self.absolute_error.value <= 0
        ):
            raise ValueError(
                "infinite relative_error requires a positive absolute_error"
            )


type Change = (
    TextHunk
    | BinarySpan
    | StructuredChange
    | TableChange
    | ArrayChange
    | ExtensionChange
)


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
        if not isinstance(self.completeness, ChangeCompleteness):
            raise ValueError("change completeness must be a ChangeCompleteness")
        if not isinstance(self.selection, ChangeSelection):
            raise ValueError("change selection must be a ChangeSelection")
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
        binary_items = [item for item in self.items if isinstance(item, BinarySpan)]
        if binary_items and len(binary_items) != len(self.items):
            raise ValueError("built-in change kinds must not be mixed")
        if binary_items:
            _validate_binary_spans(tuple(binary_items))
        structured_items = [
            item for item in self.items if isinstance(item, StructuredChange)
        ]
        if structured_items and len(structured_items) != len(self.items):
            raise ValueError("built-in change kinds must not be mixed")
        table_items = [item for item in self.items if isinstance(item, TableChange)]
        if table_items and len(table_items) != len(self.items):
            raise ValueError("built-in change kinds must not be mixed")
        array_items = [item for item in self.items if isinstance(item, ArrayChange)]
        if array_items and len(array_items) != len(self.items):
            raise ValueError("built-in change kinds must not be mixed")


def _validate_binary_spans(spans: tuple[BinarySpan, ...]) -> None:
    trailing_seen = False
    previous_end = -1
    for index, span in enumerate(spans):
        is_trailing = span.before_length == 0 or span.after_length == 0
        if is_trailing:
            if trailing_seen or index != len(spans) - 1:
                raise ValueError("a trailing binary span must be the final item")
            trailing_seen = True
        else:
            if span.before_offset <= previous_end:
                raise ValueError("replacement binary spans must not overlap or touch")
            previous_end = span.before_offset + span.before_length


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
        if not isinstance(self.relation, Relation):
            raise ValueError("relation must be a Relation")
        if not isinstance(self.verdict, Verdict):
            raise ValueError("verdict must be a Verdict")
        if not isinstance(self.fidelity, Fidelity):
            raise ValueError("fidelity must be a Fidelity")
        if not isinstance(self.summary, DiffSummary):
            raise ValueError("summary must be a DiffSummary")
        if not isinstance(self.changes, ChangeSet):
            raise ValueError("changes must be a ChangeSet")
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
        spec_kind = self.provenance.spec.get("kind")
        metric_order = {
            "yaml": (
                "yaml.compared_values",
                "yaml.equal_values",
                "yaml.changed_values",
            ),
            "table": (
                "table.compared_cells",
                "table.equal_cells",
                "table.changed_cells",
                "table.changed_items",
                "table.missing_pairs",
                "table.nan_pairs",
                "table.infinity_pairs",
                "table.finite_numeric_pairs",
                "table.maximum_absolute_error",
                "table.maximum_relative_error",
            ),
            "array": (
                "array.compared_elements",
                "array.equal_elements",
                "array.changed_elements",
                "array.changed_items",
                "array.missing_pairs",
                "array.nan_pairs",
                "array.infinity_pairs",
                "array.finite_numeric_pairs",
                "array.maximum_absolute_error",
                "array.maximum_relative_error",
            ),
        }.get(spec_kind if isinstance(spec_kind, str) else "")
        if metric_order is None:
            normalized_metrics = tuple(sorted(self.metrics, key=lambda x: x.name))
        else:
            positions = {name: index for index, name in enumerate(metric_order)}
            normalized_metrics = tuple(
                sorted(self.metrics, key=lambda item: positions.get(item.name, 10**9))
            )
        object.__setattr__(self, "metrics", normalized_metrics)
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


def _validate_completed_v2_provenance(
    execution: ExecutionRecordV2, provenance: ComparisonProvenanceV2
) -> None:
    loaded = (
        () if execution.plugin_host is None else execution.plugin_host.loaded_providers
    )
    if provenance.provider is not None and provenance.provider not in loaded:
        raise ValueError("comparison provider must be a loaded provider")
    if "." in provenance.comparator_id and provenance.provider is None:
        raise ValueError("external comparator requires provider provenance")
    detection = execution.detection
    comparator_attempts = tuple(
        attempt
        for attempt in execution.attempts
        if isinstance(attempt, CapabilityAttemptV2)
        and attempt.disposition == "selected"
        and (detection is None or attempt.capability_id != detection.detector_id)
    )
    if len(comparator_attempts) != 1:
        raise ValueError("completed outcome requires one selected comparator attempt")
    comparator_attempt = comparator_attempts[0]
    if comparator_attempt.capability_id != provenance.comparator_id:
        raise ValueError("selected comparator capability must match provenance")
    if comparator_attempt.provider != provenance.provider:
        raise ValueError("selected comparator provider must match provenance")
    if (
        comparator_attempt.capability_version is not None
        and comparator_attempt.capability_version != provenance.comparator_version
    ):
        raise ValueError("selected comparator version must match provenance")

    if (
        detection is not None
        and not detection.detector_id.startswith("core.")
        and provenance.detector_provider is None
    ):
        raise ValueError("external detector requires detector provider provenance")
    if provenance.detector_provider is not None:
        if provenance.detector_provider not in loaded:
            raise ValueError("detector provider must be a loaded provider")
        if detection is None:
            raise ValueError("detector provider requires detection provenance")
        detector_attempts = tuple(
            attempt
            for attempt in execution.attempts
            if isinstance(attempt, CapabilityAttemptV2)
            and attempt.disposition == "selected"
            and attempt.capability_id == detection.detector_id
        )
        if len(detector_attempts) != 1:
            raise ValueError("selected detector attempt must match detection")
        detector_attempt = detector_attempts[0]
        if (
            detector_attempt.provider != provenance.detector_provider
            or detector_attempt.capability_version != detection.detector_version
        ):
            raise ValueError("selected detector identity must match detection")
    elif detection is not None and any(
        isinstance(attempt, CapabilityAttemptV2)
        and attempt.disposition == "selected"
        and attempt.capability_id == detection.detector_id
        and attempt.provider is not None
        for attempt in execution.attempts
    ):
        raise ValueError("plugin detection requires detector provider provenance")


@dataclass(frozen=True, slots=True)
class CompletedOutcome:
    schema_version: Literal[1] = field(default=SCHEMA_VERSION, init=False)
    kind: Literal["completed"] = field(default="completed", init=False)
    execution: ExecutionRecord = field(kw_only=True)
    result: DiffResult = field(kw_only=True)

    def __post_init__(self) -> None:
        if type(self.execution) is not ExecutionRecord:
            raise ValueError("schema-v1 outcome requires schema-v1 execution")
        if type(self.result.provenance) is not ComparisonProvenance:
            raise ValueError("schema-v1 outcome requires schema-v1 provenance")
        if self.execution.last_completed_stage is not PipelineStage.AGGREGATING:
            raise ValueError("completed outcome must finish aggregation")


@dataclass(frozen=True, slots=True)
class UnavailableOutcome:
    schema_version: Literal[1] = field(default=SCHEMA_VERSION, init=False)
    kind: Literal["unavailable"] = field(default="unavailable", init=False)
    execution: ExecutionRecord = field(kw_only=True)
    problem: CapabilityProblem = field(kw_only=True)

    def __post_init__(self) -> None:
        if type(self.execution) is not ExecutionRecord:
            raise ValueError("schema-v1 outcome requires schema-v1 execution")
        if type(self.problem) is not CapabilityProblem:
            raise ValueError("schema-v1 outcome requires a schema-v1 problem")
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
        if type(self.execution) is not ExecutionRecord:
            raise ValueError("schema-v1 outcome requires schema-v1 execution")
        if type(self.problem) is not ExecutionProblem:
            raise ValueError("schema-v1 outcome requires a schema-v1 problem")
        if (
            not self.execution.stages
            or self.execution.stages[-1].stage is not self.problem.stage
            or self.execution.stages[-1].disposition is not StageDisposition.FAILED
        ):
            raise ValueError("failed outcome must match its terminal stage")


type CompareOutcome = CompletedOutcome | UnavailableOutcome | FailedOutcome


@dataclass(frozen=True, slots=True)
class CompletedOutcomeV2:
    schema_version: Literal[2] = field(default=SCHEMA_VERSION_V2, init=False)
    kind: Literal["completed"] = field(default="completed", init=False)
    execution: ExecutionRecordV2 = field(kw_only=True)
    result: DiffResult = field(kw_only=True)

    def __post_init__(self) -> None:
        if type(self.execution) is not ExecutionRecordV2:
            raise ValueError("schema-v2 outcome requires schema-v2 execution")
        if self.execution.last_completed_stage is not PipelineStage.AGGREGATING:
            raise ValueError("completed outcome must finish aggregation")
        if not isinstance(self.result.provenance, ComparisonProvenanceV2):
            raise ValueError("schema-v2 results require schema-v2 provenance")
        _validate_completed_v2_provenance(self.execution, self.result.provenance)


@dataclass(frozen=True, slots=True)
class UnavailableOutcomeV2:
    schema_version: Literal[2] = field(default=SCHEMA_VERSION_V2, init=False)
    kind: Literal["unavailable"] = field(default="unavailable", init=False)
    execution: ExecutionRecordV2 = field(kw_only=True)
    problem: CapabilityProblemV2 = field(kw_only=True)

    def __post_init__(self) -> None:
        if type(self.execution) is not ExecutionRecordV2:
            raise ValueError("schema-v2 outcome requires schema-v2 execution")
        if type(self.problem) is not CapabilityProblemV2:
            raise ValueError("schema-v2 outcome requires a schema-v2 problem")
        if (
            not self.execution.stages
            or self.execution.stages[-1].stage is not self.problem.stage
            or self.execution.stages[-1].disposition is not StageDisposition.UNAVAILABLE
        ):
            raise ValueError("unavailable outcome must match its terminal stage")


@dataclass(frozen=True, slots=True)
class FailedOutcomeV2:
    schema_version: Literal[2] = field(default=SCHEMA_VERSION_V2, init=False)
    kind: Literal["failed"] = field(default="failed", init=False)
    execution: ExecutionRecordV2 = field(kw_only=True)
    problem: ExecutionProblemV2 = field(kw_only=True)

    def __post_init__(self) -> None:
        if type(self.execution) is not ExecutionRecordV2:
            raise ValueError("schema-v2 outcome requires schema-v2 execution")
        if type(self.problem) is not ExecutionProblemV2:
            raise ValueError("schema-v2 outcome requires a schema-v2 problem")
        if (
            not self.execution.stages
            or self.execution.stages[-1].stage is not self.problem.stage
            or self.execution.stages[-1].disposition is not StageDisposition.FAILED
        ):
            raise ValueError("failed outcome must match its terminal stage")


type CompareOutcomeV2 = CompletedOutcomeV2 | UnavailableOutcomeV2 | FailedOutcomeV2


@dataclass(frozen=True, slots=True)
class CompletedOutcomeV3:
    schema_version: Literal[3] = field(default=SCHEMA_VERSION_V3, init=False)
    kind: Literal["completed"] = field(default="completed", init=False)
    execution: ExecutionRecordV2 = field(kw_only=True)
    result: DiffResult = field(kw_only=True)

    def __post_init__(self) -> None:
        if type(self.execution) is not ExecutionRecordV2:
            raise ValueError("schema-v3 outcome requires provider-aware execution")
        if self.execution.last_completed_stage is not PipelineStage.AGGREGATING:
            raise ValueError("completed outcome must finish aggregation")
        if type(self.result.provenance) is not ComparisonProvenanceV2:
            raise ValueError("schema-v3 outcome requires provider-aware provenance")
        _validate_completed_v2_provenance(self.execution, self.result.provenance)


@dataclass(frozen=True, slots=True)
class UnavailableOutcomeV3:
    schema_version: Literal[3] = field(default=SCHEMA_VERSION_V3, init=False)
    kind: Literal["unavailable"] = field(default="unavailable", init=False)
    execution: ExecutionRecordV2 = field(kw_only=True)
    problem: CapabilityProblemV2 = field(kw_only=True)

    def __post_init__(self) -> None:
        if type(self.execution) is not ExecutionRecordV2:
            raise ValueError("schema-v3 outcome requires provider-aware execution")
        if type(self.problem) is not CapabilityProblemV2:
            raise ValueError("schema-v3 outcome requires a provider-aware problem")
        if (
            not self.execution.stages
            or self.execution.stages[-1].stage is not self.problem.stage
            or self.execution.stages[-1].disposition is not StageDisposition.UNAVAILABLE
        ):
            raise ValueError("unavailable outcome must match its terminal stage")


@dataclass(frozen=True, slots=True)
class FailedOutcomeV3:
    schema_version: Literal[3] = field(default=SCHEMA_VERSION_V3, init=False)
    kind: Literal["failed"] = field(default="failed", init=False)
    execution: ExecutionRecordV2 = field(kw_only=True)
    problem: ExecutionProblemV2 = field(kw_only=True)

    def __post_init__(self) -> None:
        if type(self.execution) is not ExecutionRecordV2:
            raise ValueError("schema-v3 outcome requires provider-aware execution")
        if type(self.problem) is not ExecutionProblemV2:
            raise ValueError("schema-v3 outcome requires a provider-aware problem")
        if (
            not self.execution.stages
            or self.execution.stages[-1].stage is not self.problem.stage
            or self.execution.stages[-1].disposition is not StageDisposition.FAILED
        ):
            raise ValueError("failed outcome must match its terminal stage")


type CompareOutcomeV3 = CompletedOutcomeV3 | UnavailableOutcomeV3 | FailedOutcomeV3
type AnyCompareOutcome = CompareOutcome | CompareOutcomeV2 | CompareOutcomeV3
