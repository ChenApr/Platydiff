"""Validated schema-v1 and schema-v2 JSON serialization."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable
from typing import Literal, cast

from platydiff.core.models import (
    SCHEMA_VERSION,
    SCHEMA_VERSION_V2,
    SCHEMA_VERSION_V3,
    AnyCompareOutcome,
    ArrayChange,
    ArrayCompareSpec,
    ArrayResourceLimits,
    ArtifactRef,
    AutoCompareSpec,
    AutoResourceLimits,
    AutoTextOptions,
    BinaryCompareSpec,
    BinaryResourceLimits,
    BinarySpan,
    CapabilityAttempt,
    CapabilityAttemptV2,
    CapabilityProblem,
    CapabilityProblemV2,
    Change,
    ChangeCompleteness,
    ChangeSelection,
    ChangeSet,
    ColumnOrderFact,
    ColumnSchemaFact,
    ColumnSpec,
    CompareOutcome,
    CompareOutcomeV2,
    CompareOutcomeV3,
    CompareSpecV3,
    ComparisonProvenance,
    ComparisonProvenanceV2,
    CompletedOutcome,
    CompletedOutcomeV2,
    CompletedOutcomeV3,
    DetectionCandidate,
    DetectionRecord,
    Diagnostic,
    DiagnosticSeverity,
    DiffResult,
    DiffSummary,
    ExecutionProblem,
    ExecutionProblemV2,
    ExecutionRecord,
    ExecutionRecordV2,
    ExtensionChange,
    FailedOutcome,
    FailedOutcomeV2,
    FailedOutcomeV3,
    Fidelity,
    FiniteValue,
    HunkLine,
    InputProvenance,
    JsonCompareSpec,
    JsonNumberMode,
    JsonObject,
    JsonValue,
    Metric,
    MetricDirection,
    NaNValue,
    NegativeInfinityValue,
    NewlinePolicy,
    NumericPolicy,
    NumericValue,
    PairDetectionCandidate,
    PipelineStage,
    PluginHostExecutionRecord,
    PolicyEvaluation,
    PositiveInfinityValue,
    ProviderIdentity,
    Relation,
    ResourceLimits,
    ResourceUsage,
    ScalarFact,
    SourceDetectionRecord,
    SourceKind,
    StageDisposition,
    StageRecord,
    StructuredChange,
    StructuredDetailMode,
    StructuredResourceLimits,
    StructuredType,
    SubtreeFact,
    SummaryCount,
    TableChange,
    TableCompareSpec,
    TableFact,
    TableResourceLimits,
    TableRowFact,
    TextCompareSpec,
    TextEncoding,
    TextHunk,
    TransformationRecord,
    UnavailableOutcome,
    UnavailableOutcomeV2,
    UnavailableOutcomeV3,
    Verdict,
    YamlCompareSpec,
    YamlResourceLimits,
)


class SerializationError(ValueError):
    """Untrusted JSON does not satisfy schema v1."""


class _DuplicateKeyError(SerializationError):
    """A canonical outcome object contained the same member twice."""


def _coerce_json(value: object) -> JsonValue:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, str):
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as error:
            raise SerializationError(
                "JSON strings must contain valid Unicode scalar values"
            ) from error
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SerializationError("bare non-finite JSON numbers are forbidden")
        return value
    if isinstance(value, list):
        return [_coerce_json(item) for item in value]
    if isinstance(value, dict):
        converted: JsonObject = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise SerializationError("JSON object keys must be strings")
            try:
                key.encode("utf-8", errors="strict")
            except UnicodeEncodeError as error:
                raise SerializationError(
                    "JSON object keys must contain valid Unicode scalar values"
                ) from error
            converted[key] = _coerce_json(item)
        return converted
    raise SerializationError("value is not JSON-safe")


def _reject_constant(value: str) -> object:
    raise SerializationError(f"non-standard JSON constant is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _object(value: JsonValue, name: str) -> JsonObject:
    if not isinstance(value, dict):
        raise SerializationError(f"{name} must be an object")
    return value


def _array(value: JsonValue, name: str) -> list[JsonValue]:
    if not isinstance(value, list):
        raise SerializationError(f"{name} must be an array")
    return value


def _required(data: JsonObject, key: str) -> JsonValue:
    if key not in data:
        raise SerializationError(f"missing required field: {key}")
    return data[key]


def _string(value: JsonValue, name: str) -> str:
    if not isinstance(value, str):
        raise SerializationError(f"{name} must be a string")
    return value


def _integer(value: JsonValue, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SerializationError(f"{name} must be an integer")
    return value


def _boolean(value: JsonValue, name: str) -> bool:
    if not isinstance(value, bool):
        raise SerializationError(f"{name} must be a boolean")
    return value


def _finite_float(value: JsonValue, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SerializationError(f"{name} must be a finite number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise SerializationError(f"{name} must be a finite number")
    return normalized


def _exact_keys(data: JsonObject, expected: tuple[str, ...], name: str) -> None:
    extras = set(data) - set(expected)
    if extras:
        raise SerializationError(f"{name} has an unexpected field: {min(extras)}")


def _optional_string(value: JsonValue, name: str) -> str | None:
    return None if value is None else _string(value, name)


def _optional_integer(value: JsonValue, name: str) -> int | None:
    return None if value is None else _integer(value, name)


def _enum_value[T](constructor: Callable[[str], T], value: JsonValue, name: str) -> T:
    raw = _string(value, name)
    try:
        return constructor(raw)
    except ValueError as error:
        raise SerializationError(f"unknown {name}: {raw}") from error


def spec_to_data(spec: CompareSpecV3) -> JsonObject:
    """Serialize a normalized specification."""
    if isinstance(spec, YamlCompareSpec):
        yaml_limits = spec.limits
        return {
            "kind": spec.kind,
            "profile": spec.profile,
            "encoding": spec.encoding.value,
            "detail_mode": spec.detail_mode.value,
            "limits": {
                name: getattr(yaml_limits, name)
                for name in yaml_limits.__dataclass_fields__
            },
        }
    if isinstance(spec, TableCompareSpec):
        table_limits = spec.limits
        return {
            "kind": spec.kind,
            "dialect": spec.dialect,
            "encoding": spec.encoding.value,
            "header": spec.header,
            "alignment": spec.alignment,
            "key_columns": list(spec.key_columns),
            "column_order": spec.column_order,
            "columns": [
                {
                    "name": column.name,
                    "dtype": column.dtype,
                    "missing_tokens": list(column.missing_tokens),
                    "numeric": _numeric_policy_to_data(column.numeric),
                }
                for column in spec.columns
            ],
            "detail_mode": spec.detail_mode.value,
            "limits": {
                name: getattr(table_limits, name)
                for name in table_limits.__dataclass_fields__
            },
        }
    if isinstance(spec, ArrayCompareSpec):
        array_limits = spec.limits
        return {
            "kind": spec.kind,
            "alignment": spec.alignment,
            "numeric": _numeric_policy_to_data(spec.numeric),
            "limits": {
                name: getattr(array_limits, name)
                for name in array_limits.__dataclass_fields__
            },
        }
    if isinstance(spec, JsonCompareSpec):
        json_limits = spec.limits
        return {
            "kind": spec.kind,
            "encoding": spec.encoding.value,
            "number_mode": spec.number_mode.value,
            "detail_mode": spec.detail_mode.value,
            "limits": {
                name: getattr(json_limits, name)
                for name in json_limits.__dataclass_fields__
            },
        }
    if isinstance(spec, BinaryCompareSpec):
        return {
            "kind": spec.kind,
            "limits": {
                "max_input_bytes": spec.limits.max_input_bytes,
                "chunk_bytes": spec.limits.chunk_bytes,
                "max_change_items": spec.limits.max_change_items,
                "max_change_payload_bytes": spec.limits.max_change_payload_bytes,
            },
        }
    if isinstance(spec, AutoCompareSpec):
        return {
            "kind": spec.kind,
            "text": {
                "encoding": spec.text.encoding.value,
                "newline": spec.text.newline.value,
                "context_lines": spec.text.context_lines,
            },
            "minimum_confidence": spec.minimum_confidence,
            "ambiguity_margin": spec.ambiguity_margin,
            "limits": {
                "max_input_bytes": spec.limits.max_input_bytes,
                "max_input_lines": spec.limits.max_input_lines,
                "max_encoded_line_bytes": spec.limits.max_encoded_line_bytes,
                "max_myers_work": spec.limits.max_myers_work,
                "max_detection_bytes": spec.limits.max_detection_bytes,
                "binary_chunk_bytes": spec.limits.binary_chunk_bytes,
                "max_change_items": spec.limits.max_change_items,
                "max_change_payload_bytes": spec.limits.max_change_payload_bytes,
            },
        }
    limits = spec.limits
    return {
        "kind": spec.kind,
        "encoding": spec.encoding.value,
        "newline": spec.newline.value,
        "context_lines": spec.context_lines,
        "limits": {
            "max_input_bytes": limits.max_input_bytes,
            "max_input_lines": limits.max_input_lines,
            "max_encoded_line_bytes": limits.max_encoded_line_bytes,
            "max_myers_work": limits.max_myers_work,
            "max_change_items": limits.max_change_items,
            "max_change_payload_bytes": limits.max_change_payload_bytes,
        },
    }


def spec_from_data(value: JsonValue) -> CompareSpecV3:
    """Validate generic JSON data and construct a specification."""
    data = _object(value, "spec")
    kind = _string(_required(data, "kind"), "spec.kind")
    if kind not in ("text", "binary", "auto", "json", "yaml", "table", "array"):
        raise SerializationError(f"unknown spec kind: {kind}")
    limits_data = _object(_required(data, "limits"), "spec.limits")
    try:
        if kind == "yaml":
            _exact_keys(
                data,
                ("kind", "profile", "encoding", "detail_mode", "limits"),
                "YAML spec",
            )
            _exact_keys(
                limits_data,
                tuple(YamlResourceLimits.__dataclass_fields__),
                "YAML limits",
            )
            profile = _string(_required(data, "profile"), "profile")
            if profile != "yaml12_core_safe":
                raise SerializationError(f"unknown YAML profile: {profile}")
            return YamlCompareSpec(
                profile=cast(Literal["yaml12_core_safe"], profile),
                encoding=_enum_value(
                    TextEncoding, _required(data, "encoding"), "encoding"
                ),
                detail_mode=_enum_value(
                    StructuredDetailMode,
                    _required(data, "detail_mode"),
                    "detail_mode",
                ),
                limits=YamlResourceLimits(
                    **{
                        name: _integer(_required(limits_data, name), name)
                        for name in YamlResourceLimits.__dataclass_fields__
                    }
                ),
            )
        if kind == "table":
            _exact_keys(
                data,
                (
                    "kind",
                    "dialect",
                    "encoding",
                    "header",
                    "alignment",
                    "key_columns",
                    "column_order",
                    "columns",
                    "detail_mode",
                    "limits",
                ),
                "table spec",
            )
            _exact_keys(
                limits_data,
                tuple(TableResourceLimits.__dataclass_fields__),
                "table limits",
            )
            dialect = _string(_required(data, "dialect"), "dialect")
            header = _string(_required(data, "header"), "header")
            alignment = _string(_required(data, "alignment"), "alignment")
            column_order = _string(_required(data, "column_order"), "column_order")
            if dialect not in ("csv", "tsv"):
                raise SerializationError(f"unknown table dialect: {dialect}")
            if header not in ("first_row", "none"):
                raise SerializationError(f"unknown table header policy: {header}")
            if alignment not in ("position", "key"):
                raise SerializationError(f"unknown table alignment: {alignment}")
            if column_order not in ("exact", "by_name"):
                raise SerializationError(f"unknown table column order: {column_order}")
            key_columns = tuple(
                _string(item, "key column")
                for item in _array(_required(data, "key_columns"), "key_columns")
            )
            columns: list[ColumnSpec] = []
            for raw_column in _array(_required(data, "columns"), "columns"):
                column = _object(raw_column, "column spec")
                _exact_keys(
                    column,
                    ("name", "dtype", "missing_tokens", "numeric"),
                    "column spec",
                )
                dtype = _string(_required(column, "dtype"), "column dtype")
                if dtype not in ("string", "integer", "float64", "boolean"):
                    raise SerializationError(f"unknown column dtype: {dtype}")
                columns.append(
                    ColumnSpec(
                        name=_string(_required(column, "name"), "column name"),
                        dtype=cast(
                            Literal["string", "integer", "float64", "boolean"],
                            dtype,
                        ),
                        missing_tokens=tuple(
                            _string(item, "missing token")
                            for item in _array(
                                _required(column, "missing_tokens"),
                                "missing_tokens",
                            )
                        ),
                        numeric=_numeric_policy_from_data(
                            _required(column, "numeric"), optional=True
                        ),
                    )
                )
            return TableCompareSpec(
                dialect=cast(Literal["csv", "tsv"], dialect),
                encoding=_enum_value(
                    TextEncoding, _required(data, "encoding"), "encoding"
                ),
                header=cast(Literal["first_row", "none"], header),
                alignment=cast(Literal["position", "key"], alignment),
                key_columns=key_columns,
                column_order=cast(Literal["exact", "by_name"], column_order),
                columns=tuple(columns),
                detail_mode=_enum_value(
                    StructuredDetailMode,
                    _required(data, "detail_mode"),
                    "detail_mode",
                ),
                limits=TableResourceLimits(
                    **{
                        name: _integer(_required(limits_data, name), name)
                        for name in TableResourceLimits.__dataclass_fields__
                    }
                ),
            )
        if kind == "array":
            _exact_keys(
                data,
                ("kind", "alignment", "numeric", "limits"),
                "array spec",
            )
            _exact_keys(
                limits_data,
                tuple(ArrayResourceLimits.__dataclass_fields__),
                "array limits",
            )
            alignment = _string(_required(data, "alignment"), "alignment")
            if alignment != "position":
                raise SerializationError(f"unknown array alignment: {alignment}")
            numeric = _numeric_policy_from_data(
                _required(data, "numeric"), optional=False
            )
            if numeric is None:
                raise SerializationError("array numeric policy is required")
            return ArrayCompareSpec(
                alignment=cast(Literal["position"], alignment),
                numeric=numeric,
                limits=ArrayResourceLimits(
                    **{
                        name: _integer(_required(limits_data, name), name)
                        for name in ArrayResourceLimits.__dataclass_fields__
                    }
                ),
            )
        if kind == "json":
            return JsonCompareSpec(
                encoding=_enum_value(
                    TextEncoding, _required(data, "encoding"), "encoding"
                ),
                number_mode=_enum_value(
                    JsonNumberMode, _required(data, "number_mode"), "number_mode"
                ),
                detail_mode=_enum_value(
                    StructuredDetailMode,
                    _required(data, "detail_mode"),
                    "detail_mode",
                ),
                limits=StructuredResourceLimits(
                    **{
                        name: _integer(_required(limits_data, name), name)
                        for name in StructuredResourceLimits.__dataclass_fields__
                    }
                ),
            )
        if kind == "binary":
            return BinaryCompareSpec(
                limits=BinaryResourceLimits(
                    max_input_bytes=_integer(
                        _required(limits_data, "max_input_bytes"), "max_input_bytes"
                    ),
                    chunk_bytes=_integer(
                        _required(limits_data, "chunk_bytes"), "chunk_bytes"
                    ),
                    max_change_items=_integer(
                        _required(limits_data, "max_change_items"),
                        "max_change_items",
                    ),
                    max_change_payload_bytes=_integer(
                        _required(limits_data, "max_change_payload_bytes"),
                        "max_change_payload_bytes",
                    ),
                )
            )
        if kind == "auto":
            text_data = _object(_required(data, "text"), "spec.text")
            return AutoCompareSpec(
                text=AutoTextOptions(
                    encoding=_enum_value(
                        TextEncoding, _required(text_data, "encoding"), "encoding"
                    ),
                    newline=_enum_value(
                        NewlinePolicy, _required(text_data, "newline"), "newline"
                    ),
                    context_lines=_integer(
                        _required(text_data, "context_lines"), "context_lines"
                    ),
                ),
                minimum_confidence=_integer(
                    _required(data, "minimum_confidence"), "minimum_confidence"
                ),
                ambiguity_margin=_integer(
                    _required(data, "ambiguity_margin"), "ambiguity_margin"
                ),
                limits=AutoResourceLimits(
                    max_input_bytes=_integer(
                        _required(limits_data, "max_input_bytes"), "max_input_bytes"
                    ),
                    max_input_lines=_integer(
                        _required(limits_data, "max_input_lines"), "max_input_lines"
                    ),
                    max_encoded_line_bytes=_integer(
                        _required(limits_data, "max_encoded_line_bytes"),
                        "max_encoded_line_bytes",
                    ),
                    max_myers_work=_integer(
                        _required(limits_data, "max_myers_work"), "max_myers_work"
                    ),
                    max_detection_bytes=_integer(
                        _required(limits_data, "max_detection_bytes"),
                        "max_detection_bytes",
                    ),
                    binary_chunk_bytes=_integer(
                        _required(limits_data, "binary_chunk_bytes"),
                        "binary_chunk_bytes",
                    ),
                    max_change_items=_integer(
                        _required(limits_data, "max_change_items"),
                        "max_change_items",
                    ),
                    max_change_payload_bytes=_integer(
                        _required(limits_data, "max_change_payload_bytes"),
                        "max_change_payload_bytes",
                    ),
                ),
            )
        limits = ResourceLimits(
            max_input_bytes=_integer(
                _required(limits_data, "max_input_bytes"), "max_input_bytes"
            ),
            max_input_lines=_integer(
                _required(limits_data, "max_input_lines"), "max_input_lines"
            ),
            max_encoded_line_bytes=_integer(
                _required(limits_data, "max_encoded_line_bytes"),
                "max_encoded_line_bytes",
            ),
            max_myers_work=_integer(
                _required(limits_data, "max_myers_work"), "max_myers_work"
            ),
            max_change_items=_integer(
                _required(limits_data, "max_change_items"), "max_change_items"
            ),
            max_change_payload_bytes=_integer(
                _required(limits_data, "max_change_payload_bytes"),
                "max_change_payload_bytes",
            ),
        )
        return TextCompareSpec(
            encoding=_enum_value(TextEncoding, _required(data, "encoding"), "encoding"),
            newline=_enum_value(NewlinePolicy, _required(data, "newline"), "newline"),
            context_lines=_integer(_required(data, "context_lines"), "context_lines"),
            limits=limits,
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _numeric_policy_to_data(policy: NumericPolicy | None) -> JsonValue:
    if policy is None:
        return None
    return {
        "atol": policy.atol,
        "rtol": policy.rtol,
        "relative_reference": policy.relative_reference,
        "nan_equal": policy.nan_equal,
        "signed_zero_equal": policy.signed_zero_equal,
    }


def _numeric_policy_from_data(
    value: JsonValue, *, optional: bool
) -> NumericPolicy | None:
    if value is None:
        if optional:
            return None
        raise SerializationError("numeric policy must be an object")
    data = _object(value, "numeric policy")
    _exact_keys(
        data,
        ("atol", "rtol", "relative_reference", "nan_equal", "signed_zero_equal"),
        "numeric policy",
    )
    reference = _string(_required(data, "relative_reference"), "relative_reference")
    if reference != "before":
        raise SerializationError(f"unknown relative reference: {reference}")
    try:
        return NumericPolicy(
            atol=_finite_float(_required(data, "atol"), "atol"),
            rtol=_finite_float(_required(data, "rtol"), "rtol"),
            relative_reference=cast(Literal["before"], reference),
            nan_equal=_boolean(_required(data, "nan_equal"), "nan_equal"),
            signed_zero_equal=_boolean(
                _required(data, "signed_zero_equal"), "signed_zero_equal"
            ),
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _numeric_to_data(value: NumericValue) -> JsonObject:
    if isinstance(value, FiniteValue):
        return {"kind": value.kind, "value": value.value}
    return {"kind": value.kind}


def _numeric_from_data(value: JsonValue, *, strict: bool = False) -> NumericValue:
    data = _object(value, "numeric value")
    kind = _string(_required(data, "kind"), "numeric kind")
    if kind == "finite":
        if strict:
            _exact_keys(data, ("kind", "value"), "finite numeric value")
        raw = _required(data, "value")
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise SerializationError("finite numeric value must be a number")
        try:
            return FiniteValue(raw)
        except ValueError as error:
            raise SerializationError(str(error)) from error
    if kind == "nan":
        if strict:
            _exact_keys(data, ("kind",), "NaN numeric value")
        return NaNValue()
    if kind == "positive_infinity":
        if strict:
            _exact_keys(data, ("kind",), "positive-infinity numeric value")
        return PositiveInfinityValue()
    if kind == "negative_infinity":
        if strict:
            _exact_keys(data, ("kind",), "negative-infinity numeric value")
        return NegativeInfinityValue()
    raise SerializationError(f"unknown numeric kind: {kind}")


def _stage_to_data(record: StageRecord) -> JsonObject:
    return {
        "stage": record.stage.value,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "duration_ns": record.duration_ns,
        "disposition": record.disposition.value,
    }


def _stage_from_data(value: JsonValue) -> StageRecord:
    data = _object(value, "stage record")
    return StageRecord(
        stage=_enum_value(PipelineStage, _required(data, "stage"), "stage"),
        started_at=_string(_required(data, "started_at"), "started_at"),
        finished_at=_string(_required(data, "finished_at"), "finished_at"),
        duration_ns=_integer(_required(data, "duration_ns"), "duration_ns"),
        disposition=_enum_value(
            StageDisposition, _required(data, "disposition"), "disposition"
        ),
    )


def _detection_candidate_to_data(candidate: DetectionCandidate) -> JsonObject:
    return {
        "modality_id": candidate.modality_id,
        "confidence": candidate.confidence,
        "detector_id": candidate.detector_id,
        "detector_version": candidate.detector_version,
        "priority": candidate.priority,
        "evidence_codes": list(candidate.evidence_codes),
        "evidence_counts": dict(candidate.evidence_counts),
    }


def _detection_candidate_from_data(value: JsonValue) -> DetectionCandidate:
    data = _object(value, "detection candidate")
    modality = _string(_required(data, "modality_id"), "modality_id")
    if modality not in ("text", "binary"):
        raise SerializationError(f"unknown detection modality: {modality}")
    evidence_codes = tuple(
        _string(item, "evidence code")
        for item in _array(_required(data, "evidence_codes"), "evidence_codes")
    )
    if evidence_codes != tuple(sorted(evidence_codes)):
        raise SerializationError("detection evidence codes must be sorted")
    try:
        return DetectionCandidate(
            modality_id=cast(Literal["text", "binary"], modality),
            confidence=_integer(_required(data, "confidence"), "confidence"),
            detector_id=_string(_required(data, "detector_id"), "detector_id"),
            detector_version=_string(
                _required(data, "detector_version"), "detector_version"
            ),
            priority=_integer(_required(data, "priority"), "priority"),
            evidence_codes=evidence_codes,
            evidence_counts=_object(
                _required(data, "evidence_counts"), "evidence_counts"
            ),
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _pair_candidate_to_data(candidate: PairDetectionCandidate) -> JsonObject:
    return {
        "modality_id": candidate.modality_id,
        "confidence": candidate.confidence,
        "before_confidence": candidate.before_confidence,
        "after_confidence": candidate.after_confidence,
        "detector_priority": candidate.detector_priority,
        "capability_priority": candidate.capability_priority,
        "capability_id": candidate.capability_id,
        "backend_id": candidate.backend_id,
    }


def _pair_candidate_from_data(value: JsonValue) -> PairDetectionCandidate:
    data = _object(value, "pair detection candidate")
    modality = _string(_required(data, "modality_id"), "modality_id")
    if modality not in ("text", "binary"):
        raise SerializationError(f"unknown detection modality: {modality}")
    try:
        return PairDetectionCandidate(
            modality_id=cast(Literal["text", "binary"], modality),
            confidence=_integer(_required(data, "confidence"), "confidence"),
            before_confidence=_integer(
                _required(data, "before_confidence"), "before_confidence"
            ),
            after_confidence=_integer(
                _required(data, "after_confidence"), "after_confidence"
            ),
            detector_priority=_integer(
                _required(data, "detector_priority"), "detector_priority"
            ),
            capability_priority=_integer(
                _required(data, "capability_priority"), "capability_priority"
            ),
            capability_id=_string(_required(data, "capability_id"), "capability_id"),
            backend_id=_string(_required(data, "backend_id"), "backend_id"),
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _detection_to_data(record: DetectionRecord) -> JsonObject:
    return {
        "detector_id": record.detector_id,
        "detector_version": record.detector_version,
        "maximum_bytes": record.maximum_bytes,
        "minimum_confidence": record.minimum_confidence,
        "ambiguity_margin": record.ambiguity_margin,
        "sources": [
            {
                "role": source.role,
                "candidates": [
                    _detection_candidate_to_data(candidate)
                    for candidate in source.candidates
                ],
            }
            for source in record.sources
        ],
        "pair_candidates": [
            _pair_candidate_to_data(candidate) for candidate in record.pair_candidates
        ],
        "disposition": record.disposition,
        "selected_modality": record.selected_modality,
    }


def _detection_from_data(value: JsonValue) -> DetectionRecord:
    data = _object(value, "detection")
    sources: list[SourceDetectionRecord] = []
    for raw in _array(_required(data, "sources"), "detection sources"):
        item = _object(raw, "source detection")
        role = _string(_required(item, "role"), "source detection role")
        if role not in ("before", "after"):
            raise SerializationError(f"unknown detection source role: {role}")
        candidates = tuple(
            _detection_candidate_from_data(candidate)
            for candidate in _array(
                _required(item, "candidates"), "source detection candidates"
            )
        )
        expected = tuple(
            sorted(
                candidates,
                key=lambda candidate: (-candidate.confidence, candidate.modality_id),
            )
        )
        if candidates != expected:
            raise SerializationError("source detection candidates must be sorted")
        sources.append(
            SourceDetectionRecord(
                role=cast(Literal["before", "after"], role),
                candidates=candidates,
            )
        )
    if len(sources) != 2:
        raise SerializationError("detection must contain two source records")
    pair_candidates = tuple(
        _pair_candidate_from_data(candidate)
        for candidate in _array(
            _required(data, "pair_candidates"), "pair detection candidates"
        )
    )
    disposition = _string(_required(data, "disposition"), "detection disposition")
    if disposition not in ("selected", "no_match", "ambiguous"):
        raise SerializationError(f"unknown detection disposition: {disposition}")
    selected = _optional_string(
        _required(data, "selected_modality"), "selected_modality"
    )
    if selected not in (None, "text", "binary"):
        raise SerializationError(f"unknown selected modality: {selected}")
    try:
        record = DetectionRecord(
            detector_id=_string(_required(data, "detector_id"), "detector_id"),
            detector_version=_string(
                _required(data, "detector_version"), "detector_version"
            ),
            maximum_bytes=_integer(_required(data, "maximum_bytes"), "maximum_bytes"),
            minimum_confidence=_integer(
                _required(data, "minimum_confidence"), "minimum_confidence"
            ),
            ambiguity_margin=_integer(
                _required(data, "ambiguity_margin"), "ambiguity_margin"
            ),
            sources=(sources[0], sources[1]),
            pair_candidates=pair_candidates,
            disposition=cast(Literal["selected", "no_match", "ambiguous"], disposition),
            selected_modality=cast(Literal["text", "binary"] | None, selected),
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error
    if record.pair_candidates != pair_candidates:
        raise SerializationError("pair detection candidates must be sorted")
    return record


def _provider_to_data(provider: ProviderIdentity) -> JsonObject:
    return {
        "plugin_id": provider.plugin_id,
        "plugin_version": provider.plugin_version,
        "distribution_name": provider.distribution_name,
        "distribution_version": provider.distribution_version,
        "manifest_schema_version": provider.manifest_schema_version,
        "api_major": provider.api_major,
        "negotiated_api_minor": provider.negotiated_api_minor,
        "negotiated_host_features": list(provider.negotiated_host_features),
    }


def _provider_from_data(value: JsonValue) -> ProviderIdentity:
    data = _object(value, "provider identity")
    try:
        return ProviderIdentity(
            plugin_id=_string(_required(data, "plugin_id"), "plugin_id"),
            plugin_version=_string(_required(data, "plugin_version"), "plugin_version"),
            distribution_name=_string(
                _required(data, "distribution_name"), "distribution_name"
            ),
            distribution_version=_string(
                _required(data, "distribution_version"), "distribution_version"
            ),
            manifest_schema_version=_integer(
                _required(data, "manifest_schema_version"), "manifest_schema_version"
            ),
            api_major=_integer(_required(data, "api_major"), "api_major"),
            negotiated_api_minor=_integer(
                _required(data, "negotiated_api_minor"), "negotiated_api_minor"
            ),
            negotiated_host_features=tuple(
                _string(item, "negotiated host feature")
                for item in _array(
                    _required(data, "negotiated_host_features"),
                    "negotiated_host_features",
                )
            ),
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _plugin_host_to_data(record: PluginHostExecutionRecord) -> JsonObject:
    return {
        "enabled_plugin_ids": list(record.enabled_plugin_ids),
        "loaded_providers": [
            _provider_to_data(provider) for provider in record.loaded_providers
        ],
    }


def _plugin_host_from_data(value: JsonValue) -> PluginHostExecutionRecord:
    data = _object(value, "plugin host")
    try:
        return PluginHostExecutionRecord(
            enabled_plugin_ids=tuple(
                _string(item, "enabled plugin ID")
                for item in _array(
                    _required(data, "enabled_plugin_ids"), "enabled_plugin_ids"
                )
            ),
            loaded_providers=tuple(
                _provider_from_data(item)
                for item in _array(
                    _required(data, "loaded_providers"), "loaded_providers"
                )
            ),
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _execution_to_data(record: ExecutionRecord) -> JsonObject:
    data: JsonObject = {
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "duration_ns": record.duration_ns,
        "stages": [_stage_to_data(stage) for stage in record.stages],
        "attempts": [
            {
                "capability_id": attempt.capability_id,
                "backend_id": attempt.backend_id,
                "disposition": attempt.disposition,
                "reason_code": attempt.reason_code,
                **(
                    {
                        "capability_version": attempt.capability_version,
                        "backend_version": attempt.backend_version,
                        "provider": (
                            None
                            if attempt.provider is None
                            else _provider_to_data(attempt.provider)
                        ),
                    }
                    if isinstance(attempt, CapabilityAttemptV2)
                    else {}
                ),
            }
            for attempt in record.attempts
        ],
        "diagnostics": [
            {
                "code": diagnostic.code,
                "severity": diagnostic.severity.value,
                "stage": (None if diagnostic.stage is None else diagnostic.stage.value),
                "message": diagnostic.message,
                "details": diagnostic.details,
            }
            for diagnostic in record.diagnostics
        ],
        "last_completed_stage": (
            None
            if record.last_completed_stage is None
            else record.last_completed_stage.value
        ),
    }
    if record.detection is not None:
        data["detection"] = _detection_to_data(record.detection)
    if isinstance(record, ExecutionRecordV2):
        data["plugin_host"] = (
            None
            if record.plugin_host is None
            else _plugin_host_to_data(record.plugin_host)
        )
    return data


def _execution_from_data(
    value: JsonValue, *, schema_version: Literal[1, 2, 3] = 1
) -> ExecutionRecord:
    data = _object(value, "execution")
    attempts: list[CapabilityAttempt | CapabilityAttemptV2] = []
    for value_item in _array(_required(data, "attempts"), "attempts"):
        item = _object(value_item, "capability attempt")
        disposition = _string(_required(item, "disposition"), "disposition")
        allowed_dispositions = (
            ("selected", "rejected", "fallback", "unavailable", "failed")
            if schema_version in (2, 3)
            else ("selected", "rejected", "fallback")
        )
        if disposition not in allowed_dispositions:
            raise SerializationError("unknown capability attempt disposition")
        capability_id = _string(_required(item, "capability_id"), "capability_id")
        backend_id = _optional_string(_required(item, "backend_id"), "backend_id")
        reason_code = _optional_string(_required(item, "reason_code"), "reason_code")
        try:
            if schema_version in (2, 3):
                raw_provider = _required(item, "provider")
                attempts.append(
                    CapabilityAttemptV2(
                        capability_id=capability_id,
                        backend_id=backend_id,
                        disposition=cast(
                            Literal[
                                "selected",
                                "rejected",
                                "fallback",
                                "unavailable",
                                "failed",
                            ],
                            disposition,
                        ),
                        reason_code=reason_code,
                        capability_version=_optional_string(
                            _required(item, "capability_version"),
                            "capability_version",
                        ),
                        backend_version=_optional_string(
                            _required(item, "backend_version"), "backend_version"
                        ),
                        provider=(
                            None
                            if raw_provider is None
                            else _provider_from_data(raw_provider)
                        ),
                    )
                )
            else:
                attempts.append(
                    CapabilityAttempt(
                        capability_id=capability_id,
                        backend_id=backend_id,
                        disposition=cast(
                            Literal["selected", "rejected", "fallback"],
                            disposition,
                        ),
                        reason_code=reason_code,
                    )
                )
        except ValueError as error:
            raise SerializationError(str(error)) from error
    diagnostics: list[Diagnostic] = []
    for value_item in _array(_required(data, "diagnostics"), "diagnostics"):
        item = _object(value_item, "diagnostic")
        raw_stage = _required(item, "stage")
        stage = (
            None
            if raw_stage is None
            else _enum_value(PipelineStage, raw_stage, "diagnostic stage")
        )
        diagnostics.append(
            Diagnostic(
                code=_string(_required(item, "code"), "diagnostic code"),
                severity=_enum_value(
                    DiagnosticSeverity,
                    _required(item, "severity"),
                    "diagnostic severity",
                ),
                stage=stage,
                message=_string(_required(item, "message"), "diagnostic message"),
                details=_object(_required(item, "details"), "diagnostic details"),
            )
        )
    raw_last = _required(data, "last_completed_stage")
    last = (
        None
        if raw_last is None
        else _enum_value(PipelineStage, raw_last, "last completed stage")
    )
    detection = _detection_from_data(data["detection"]) if "detection" in data else None
    try:
        record_type = ExecutionRecordV2 if schema_version in (2, 3) else ExecutionRecord
        record_kwargs: dict[str, object] = {}
        if schema_version in (2, 3):
            raw_plugin_host = _required(data, "plugin_host")
            record_kwargs["plugin_host"] = (
                None
                if raw_plugin_host is None
                else _plugin_host_from_data(raw_plugin_host)
            )
        return record_type(
            started_at=_string(_required(data, "started_at"), "started_at"),
            finished_at=_string(_required(data, "finished_at"), "finished_at"),
            duration_ns=_integer(_required(data, "duration_ns"), "duration_ns"),
            stages=tuple(
                _stage_from_data(item)
                for item in _array(_required(data, "stages"), "stages")
            ),
            attempts=tuple(attempts),
            diagnostics=tuple(diagnostics),
            last_completed_stage=last,
            detection=detection,
            **record_kwargs,
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _problem_to_data(
    problem: ExecutionProblem
    | CapabilityProblem
    | ExecutionProblemV2
    | CapabilityProblemV2,
) -> JsonObject:
    return {
        "code": problem.code,
        "status_code": problem.status_code,
        "stage": problem.stage.value,
        "message": problem.message,
        "details": problem.details,
        "retryable": problem.retryable,
    }


def _problem_from_data(
    value: JsonValue, *, unavailable: bool, schema_version: Literal[1, 2, 3] = 1
) -> ExecutionProblem | CapabilityProblem | ExecutionProblemV2 | CapabilityProblemV2:
    data = _object(value, "problem")
    code = _string(_required(data, "code"), "problem code")
    status_code = _integer(_required(data, "status_code"), "status_code")
    stage = _enum_value(PipelineStage, _required(data, "stage"), "stage")
    message = _string(_required(data, "message"), "message")
    details = _object(_required(data, "details"), "problem details")
    retryable = _boolean(_required(data, "retryable"), "retryable")
    try:
        if unavailable:
            if schema_version in (2, 3):
                return CapabilityProblemV2(
                    code=code,
                    status_code=status_code,
                    stage=stage,
                    message=message,
                    details=details,
                    retryable=retryable,
                )
            return CapabilityProblem(
                code=code,
                status_code=status_code,
                stage=stage,
                message=message,
                details=details,
                retryable=retryable,
            )
        problem_type = (
            ExecutionProblemV2 if schema_version in (2, 3) else ExecutionProblem
        )
        return problem_type(
            code=code,
            status_code=status_code,
            stage=stage,
            message=message,
            details=details,
            retryable=retryable,
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _provenance_to_data(value: ComparisonProvenance) -> JsonObject:
    data: JsonObject = {
        "inputs": [
            {
                "role": item.role,
                "source_kind": item.source_kind.value,
                "size_bytes": item.size_bytes,
                "sha256": item.sha256,
                "label": item.label,
            }
            for item in value.inputs
        ],
        "spec": value.spec,
        "transformations": [
            {
                "stage": item.stage,
                "transformation_id": item.transformation_id,
                "parameters": item.parameters,
            }
            for item in value.transformations
        ],
        "comparator_id": value.comparator_id,
        "comparator_version": value.comparator_version,
        "algorithm_id": value.algorithm_id,
        "implementation_version": value.implementation_version,
        "seeds": list(value.seeds),
        "resources": [
            {"name": item.name, "limit": item.limit, "used": item.used}
            for item in value.resources
        ],
    }
    if isinstance(value, ComparisonProvenanceV2):
        data["provider"] = (
            None if value.provider is None else _provider_to_data(value.provider)
        )
        data["detector_provider"] = (
            None
            if value.detector_provider is None
            else _provider_to_data(value.detector_provider)
        )
    return data


def _provenance_from_data(
    value: JsonValue, *, schema_version: Literal[1, 2, 3] = 1
) -> ComparisonProvenance:
    data = _object(value, "provenance")
    inputs: list[InputProvenance] = []
    for raw in _array(_required(data, "inputs"), "inputs"):
        item = _object(raw, "input provenance")
        role = _string(_required(item, "role"), "role")
        if role not in ("before", "after"):
            raise SerializationError("unknown input role")
        inputs.append(
            InputProvenance(
                role=cast(Literal["before", "after"], role),
                source_kind=_enum_value(
                    SourceKind, _required(item, "source_kind"), "source kind"
                ),
                size_bytes=_integer(_required(item, "size_bytes"), "size_bytes"),
                sha256=_string(_required(item, "sha256"), "sha256"),
                label=_optional_string(_required(item, "label"), "label"),
            )
        )
    if len(inputs) != 2:
        raise SerializationError("provenance must contain two inputs")
    transformations: list[TransformationRecord] = []
    for raw in _array(_required(data, "transformations"), "transformations"):
        item = _object(raw, "transformation")
        stage = _string(_required(item, "stage"), "transformation stage")
        if stage not in ("decoding", "normalizing", "aligning"):
            raise SerializationError("unknown transformation stage")
        transformations.append(
            TransformationRecord(
                stage=cast(Literal["decoding", "normalizing", "aligning"], stage),
                transformation_id=_string(
                    _required(item, "transformation_id"), "transformation_id"
                ),
                parameters=_object(_required(item, "parameters"), "parameters"),
            )
        )
    resources: list[ResourceUsage] = []
    for raw in _array(_required(data, "resources"), "resources"):
        item = _object(raw, "resource usage")
        resources.append(
            ResourceUsage(
                name=_string(_required(item, "name"), "resource name"),
                limit=_integer(_required(item, "limit"), "resource limit"),
                used=_integer(_required(item, "used"), "resource used"),
            )
        )
    seeds = tuple(
        _integer(item, "seed") for item in _array(_required(data, "seeds"), "seeds")
    )
    try:
        provenance_type = (
            ComparisonProvenanceV2 if schema_version in (2, 3) else ComparisonProvenance
        )
        provenance_kwargs: dict[str, object] = {}
        if schema_version in (2, 3):
            raw_provider = _required(data, "provider")
            raw_detector_provider = _required(data, "detector_provider")
            provenance_kwargs = {
                "provider": (
                    None if raw_provider is None else _provider_from_data(raw_provider)
                ),
                "detector_provider": (
                    None
                    if raw_detector_provider is None
                    else _provider_from_data(raw_detector_provider)
                ),
            }
        return provenance_type(
            inputs=(inputs[0], inputs[1]),
            spec=_object(_required(data, "spec"), "normalized spec"),
            transformations=tuple(transformations),
            comparator_id=_string(_required(data, "comparator_id"), "comparator_id"),
            comparator_version=_string(
                _required(data, "comparator_version"), "comparator_version"
            ),
            algorithm_id=_string(_required(data, "algorithm_id"), "algorithm_id"),
            implementation_version=_string(
                _required(data, "implementation_version"), "implementation_version"
            ),
            seeds=seeds,
            resources=tuple(resources),
            **provenance_kwargs,
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _hunk_to_data(hunk: TextHunk) -> JsonObject:
    return {
        "kind": hunk.kind,
        "before_start_line": hunk.before_start_line,
        "before_line_count": hunk.before_line_count,
        "after_start_line": hunk.after_start_line,
        "after_line_count": hunk.after_line_count,
        "lines": [
            {
                "kind": line.kind,
                "content": line.content,
                "terminator": line.terminator,
                "before_line": line.before_line,
                "after_line": line.after_line,
            }
            for line in hunk.lines
        ],
    }


def _change_to_data(change: Change) -> JsonObject:
    if isinstance(change, TextHunk):
        return _hunk_to_data(change)
    if isinstance(change, BinarySpan):
        return {
            "kind": change.kind,
            "before_offset": change.before_offset,
            "before_length": change.before_length,
            "after_offset": change.after_offset,
            "after_length": change.after_length,
        }
    if isinstance(change, StructuredChange):

        def fact_data(fact: ScalarFact | SubtreeFact | None) -> JsonValue:
            if fact is None:
                return None
            if isinstance(fact, ScalarFact):
                data: JsonObject = {"kind": fact.kind, "value": fact.value}
                if fact.lexical is not None:
                    data["lexical"] = fact.lexical
                return data
            return {
                "kind": fact.kind,
                "descendant_count": fact.descendant_count,
                "scalar_count": fact.scalar_count,
            }

        return {
            "kind": change.kind,
            "operation": change.operation,
            "path": change.path,
            "before_type": (
                None if change.before_type is None else change.before_type.value
            ),
            "after_type": (
                None if change.after_type is None else change.after_type.value
            ),
            "before_digest": change.before_digest,
            "after_digest": change.after_digest,
            "before_fact": fact_data(change.before_fact),
            "after_fact": fact_data(change.after_fact),
        }
    if isinstance(change, TableChange):
        return {
            "kind": change.kind,
            "operation": change.operation,
            "row": change.row,
            "key_ordinal": change.key_ordinal,
            "key": (
                None
                if change.key is None
                else [_scalar_fact_to_data(fact) for fact in change.key]
            ),
            "column": change.column,
            "before_digest": change.before_digest,
            "after_digest": change.after_digest,
            "before_fact": _table_fact_to_data(change.before_fact),
            "after_fact": _table_fact_to_data(change.after_fact),
        }
    if isinstance(change, ArrayChange):
        return {
            "kind": change.kind,
            "operation": change.operation,
            "index": None if change.index is None else list(change.index),
            "before_digest": change.before_digest,
            "after_digest": change.after_digest,
            "absolute_error": (
                None
                if change.absolute_error is None
                else _numeric_to_data(change.absolute_error)
            ),
            "relative_error": (
                None
                if change.relative_error is None
                else _numeric_to_data(change.relative_error)
            ),
        }
    return {
        "kind": change.kind,
        "plugin_id": change.plugin_id,
        "schema_version": change.schema_version,
        "payload": change.payload,
    }


def serialized_change_size(change: Change) -> int:
    """Return canonical compact schema-v1 JSON payload bytes for one change."""
    data = _coerce_json(_change_to_data(change))
    return len(
        json.dumps(
            data,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _structured_fact_from_data(value: JsonValue) -> ScalarFact | SubtreeFact | None:
    if value is None:
        return None
    data = _object(value, "structured fact")
    kind = _string(_required(data, "kind"), "structured fact kind")
    try:
        if kind in ("sequence", "mapping"):
            _exact_keys(
                data,
                ("kind", "descendant_count", "scalar_count"),
                "structured subtree fact",
            )
            return SubtreeFact(
                kind=cast(Literal["sequence", "mapping"], kind),
                descendant_count=_integer(
                    _required(data, "descendant_count"), "descendant_count"
                ),
                scalar_count=_integer(_required(data, "scalar_count"), "scalar_count"),
            )
        allowed = (
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
        )
        if kind not in allowed:
            raise SerializationError(f"unknown structured fact kind: {kind}")
        expected = (
            ("kind", "value", "lexical")
            if "lexical" in data
            else (
                "kind",
                "value",
            )
        )
        _exact_keys(data, expected, "structured scalar fact")
        raw_value = _required(data, "value")
        fact_value: bool | str | None
        if raw_value is None or isinstance(raw_value, (bool, str)):
            fact_value = raw_value
        else:
            raise SerializationError("structured scalar fact value is invalid")
        return ScalarFact(
            kind=cast(
                Literal[
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
                ],
                kind,
            ),
            value=fact_value,
            lexical=_optional_string(data.get("lexical"), "lexical"),
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _scalar_fact_to_data(fact: ScalarFact) -> JsonObject:
    data: JsonObject = {"kind": fact.kind, "value": fact.value}
    if fact.lexical is not None:
        data["lexical"] = fact.lexical
    return data


def _scalar_fact_from_data(value: JsonValue, name: str) -> ScalarFact:
    fact = _structured_fact_from_data(value)
    if not isinstance(fact, ScalarFact):
        raise SerializationError(f"{name} must be a scalar fact")
    return fact


def _table_fact_to_data(fact: TableFact | None) -> JsonValue:
    if fact is None:
        return None
    if isinstance(fact, ScalarFact):
        return _scalar_fact_to_data(fact)
    if isinstance(fact, TableRowFact):
        return {
            "kind": fact.kind,
            "cells": [
                [name, _scalar_fact_to_data(cell_fact)]
                for name, cell_fact in fact.cells
            ],
        }
    if isinstance(fact, ColumnSchemaFact):
        return {
            "kind": fact.kind,
            "name": fact.name,
            "dtype": fact.dtype,
            "missing_token_count": fact.missing_token_count,
            "numeric": _numeric_policy_to_data(fact.numeric),
        }
    if isinstance(fact, ColumnOrderFact):
        return {"kind": fact.kind, "names": list(fact.names)}
    raise SerializationError("unknown table fact type")


def _table_fact_from_data(value: JsonValue, name: str) -> TableFact | None:
    if value is None:
        return None
    data = _object(value, name)
    kind = _string(_required(data, "kind"), f"{name}.kind")
    try:
        if kind == "table_row":
            _exact_keys(data, ("kind", "cells"), name)
            cells: list[tuple[str, ScalarFact]] = []
            for raw_cell in _array(_required(data, "cells"), f"{name}.cells"):
                pair = _array(raw_cell, "table row cell")
                if len(pair) != 2:
                    raise SerializationError("table row cells must be two-item arrays")
                cells.append(
                    (
                        _string(pair[0], "table row column name"),
                        _scalar_fact_from_data(pair[1], "table row cell fact"),
                    )
                )
            return TableRowFact(cells=tuple(cells))
        if kind == "table_column_schema":
            _exact_keys(
                data,
                ("kind", "name", "dtype", "missing_token_count", "numeric"),
                name,
            )
            dtype = _string(_required(data, "dtype"), "column schema dtype")
            if dtype not in ("string", "integer", "float64", "boolean"):
                raise SerializationError(f"unknown column schema dtype: {dtype}")
            return ColumnSchemaFact(
                name=_string(_required(data, "name"), "column schema name"),
                dtype=cast(Literal["string", "integer", "float64", "boolean"], dtype),
                missing_token_count=_integer(
                    _required(data, "missing_token_count"), "missing_token_count"
                ),
                numeric=_numeric_policy_from_data(
                    _required(data, "numeric"), optional=True
                ),
            )
        if kind == "table_column_order":
            _exact_keys(data, ("kind", "names"), name)
            return ColumnOrderFact(
                names=tuple(
                    _string(item, "column-order name")
                    for item in _array(_required(data, "names"), "column-order names")
                )
            )
        return _scalar_fact_from_data(value, name)
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _change_from_data(
    value: JsonValue, *, schema_version: Literal[1, 2, 3] = 1
) -> Change:
    data = _object(value, "change")
    kind = _string(_required(data, "kind"), "change kind")
    if kind == "text_hunk":
        lines: list[HunkLine] = []
        for raw in _array(_required(data, "lines"), "hunk lines"):
            item = _object(raw, "hunk line")
            line_kind = _string(_required(item, "kind"), "hunk line kind")
            if line_kind not in ("equal", "delete", "insert"):
                raise SerializationError("unknown hunk line kind")
            terminator = _string(_required(item, "terminator"), "terminator")
            if terminator not in ("", "\n", "\r\n", "\r"):
                raise SerializationError("unknown line terminator")
            lines.append(
                HunkLine(
                    kind=cast(Literal["equal", "delete", "insert"], line_kind),
                    content=_string(_required(item, "content"), "content"),
                    terminator=cast(Literal["", "\n", "\r\n", "\r"], terminator),
                    before_line=_optional_integer(
                        _required(item, "before_line"), "before_line"
                    ),
                    after_line=_optional_integer(
                        _required(item, "after_line"), "after_line"
                    ),
                )
            )
        return TextHunk(
            before_start_line=_integer(
                _required(data, "before_start_line"), "before_start_line"
            ),
            before_line_count=_integer(
                _required(data, "before_line_count"), "before_line_count"
            ),
            after_start_line=_integer(
                _required(data, "after_start_line"), "after_start_line"
            ),
            after_line_count=_integer(
                _required(data, "after_line_count"), "after_line_count"
            ),
            lines=tuple(lines),
        )
    if kind == "binary_span":
        try:
            return BinarySpan(
                before_offset=_integer(
                    _required(data, "before_offset"), "before_offset"
                ),
                before_length=_integer(
                    _required(data, "before_length"), "before_length"
                ),
                after_offset=_integer(_required(data, "after_offset"), "after_offset"),
                after_length=_integer(_required(data, "after_length"), "after_length"),
            )
        except ValueError as error:
            raise SerializationError(str(error)) from error
    if kind == "structured_change":
        if schema_version != 3:
            raise SerializationError("structured changes require schema version 3")
        operation = _string(_required(data, "operation"), "operation")
        if operation not in ("add", "remove", "replace"):
            raise SerializationError(f"unknown structured operation: {operation}")
        try:
            before_raw = _required(data, "before_type")
            after_raw = _required(data, "after_type")
            return StructuredChange(
                operation=cast(Literal["add", "remove", "replace"], operation),
                path=_string(_required(data, "path"), "path"),
                before_type=(
                    None
                    if before_raw is None
                    else _enum_value(StructuredType, before_raw, "structured type")
                ),
                after_type=(
                    None
                    if after_raw is None
                    else _enum_value(StructuredType, after_raw, "structured type")
                ),
                before_digest=_optional_string(
                    _required(data, "before_digest"), "before_digest"
                ),
                after_digest=_optional_string(
                    _required(data, "after_digest"), "after_digest"
                ),
                before_fact=_structured_fact_from_data(_required(data, "before_fact")),
                after_fact=_structured_fact_from_data(_required(data, "after_fact")),
            )
        except ValueError as error:
            raise SerializationError(str(error)) from error
    if kind == "table_change":
        if schema_version != 3:
            raise SerializationError("table changes require schema version 3")
        table_expected = (
            "kind",
            "operation",
            "row",
            "key_ordinal",
            "key",
            "column",
            "before_digest",
            "after_digest",
            "before_fact",
            "after_fact",
        )
        _exact_keys(data, table_expected, "table change")
        operation = _string(_required(data, "operation"), "table operation")
        allowed_operations = (
            "column_add",
            "column_remove",
            "column_reorder",
            "row_add",
            "row_remove",
            "cell_replace",
        )
        if operation not in allowed_operations:
            raise SerializationError(f"unknown table operation: {operation}")
        raw_key = _required(data, "key")
        key = (
            None
            if raw_key is None
            else tuple(
                _scalar_fact_from_data(item, "table key fact")
                for item in _array(raw_key, "table key")
            )
        )
        try:
            return TableChange(
                operation=cast(
                    Literal[
                        "column_add",
                        "column_remove",
                        "column_reorder",
                        "row_add",
                        "row_remove",
                        "cell_replace",
                    ],
                    operation,
                ),
                row=_optional_integer(_required(data, "row"), "row"),
                key_ordinal=_optional_integer(
                    _required(data, "key_ordinal"), "key_ordinal"
                ),
                key=key,
                column=_optional_string(_required(data, "column"), "column"),
                before_digest=_optional_string(
                    _required(data, "before_digest"), "before_digest"
                ),
                after_digest=_optional_string(
                    _required(data, "after_digest"), "after_digest"
                ),
                before_fact=_table_fact_from_data(
                    _required(data, "before_fact"), "before table fact"
                ),
                after_fact=_table_fact_from_data(
                    _required(data, "after_fact"), "after table fact"
                ),
            )
        except ValueError as error:
            raise SerializationError(str(error)) from error
    if kind == "array_change":
        if schema_version != 3:
            raise SerializationError("array changes require schema version 3")
        array_expected = (
            "kind",
            "operation",
            "index",
            "before_digest",
            "after_digest",
            "absolute_error",
            "relative_error",
        )
        _exact_keys(data, array_expected, "array change")
        operation = _string(_required(data, "operation"), "array operation")
        if operation not in ("shape_replace", "dtype_replace", "element_replace"):
            raise SerializationError(f"unknown array operation: {operation}")
        raw_index = _required(data, "index")
        index = (
            None
            if raw_index is None
            else tuple(
                _integer(item, "array index")
                for item in _array(raw_index, "array index")
            )
        )
        raw_absolute_error = _required(data, "absolute_error")
        raw_relative_error = _required(data, "relative_error")
        try:
            return ArrayChange(
                operation=cast(
                    Literal["shape_replace", "dtype_replace", "element_replace"],
                    operation,
                ),
                index=index,
                before_digest=_string(
                    _required(data, "before_digest"), "before_digest"
                ),
                after_digest=_string(_required(data, "after_digest"), "after_digest"),
                absolute_error=(
                    None
                    if raw_absolute_error is None
                    else _numeric_from_data(raw_absolute_error, strict=True)
                ),
                relative_error=(
                    None
                    if raw_relative_error is None
                    else _numeric_from_data(raw_relative_error, strict=True)
                ),
            )
        except ValueError as error:
            raise SerializationError(str(error)) from error
    if "." in kind:
        return ExtensionChange(
            kind=kind,
            plugin_id=_string(_required(data, "plugin_id"), "plugin_id"),
            schema_version=_integer(
                _required(data, "schema_version"), "schema_version"
            ),
            payload=_object(_required(data, "payload"), "extension payload"),
        )
    raise SerializationError(f"unknown built-in change kind: {kind}")


def _result_to_data(result: DiffResult) -> JsonObject:
    changes: list[JsonValue] = [_change_to_data(item) for item in result.changes.items]
    return {
        "relation": result.relation.value,
        "verdict": result.verdict.value,
        "fidelity": result.fidelity.value,
        "summary": {
            "change_count": result.summary.change_count,
            "counts": [
                {"name": item.name, "value": item.value, "unit": item.unit}
                for item in result.summary.counts
            ],
        },
        "changes": {
            "completeness": result.changes.completeness.value,
            "items": changes,
            "total_count": result.changes.total_count,
            "returned_count": result.changes.returned_count,
            "omitted_count": result.changes.omitted_count,
            "selection": result.changes.selection.value,
            "limit": result.changes.limit,
            "limit_reason": result.changes.limit_reason,
        },
        "metrics": [
            {
                "name": item.name,
                "value": _numeric_to_data(item.value),
                "unit": item.unit,
                "direction": item.direction.value,
                "aggregation": item.aggregation,
            }
            for item in result.metrics
        ],
        "evaluations": [
            {
                "rule_id": item.rule_id,
                "verdict": item.verdict.value,
                "metric_name": item.metric_name,
                "operator": item.operator,
                "threshold": (
                    None if item.threshold is None else _numeric_to_data(item.threshold)
                ),
                "observed": (
                    None if item.observed is None else _numeric_to_data(item.observed)
                ),
            }
            for item in result.evaluations
        ],
        "artifacts": [
            {
                "artifact_id": item.artifact_id,
                "kind": item.kind,
                "media_type": item.media_type,
                "uri": item.uri,
                "sha256": item.sha256,
                "size_bytes": item.size_bytes,
            }
            for item in result.artifacts
        ],
        "provenance": _provenance_to_data(result.provenance),
    }


def _result_from_data(
    value: JsonValue, *, schema_version: Literal[1, 2, 3] = 1
) -> DiffResult:
    data = _object(value, "result")
    strict_numeric = False
    if schema_version == 3:
        raw_provenance = _object(_required(data, "provenance"), "provenance")
        raw_spec = _object(_required(raw_provenance, "spec"), "spec")
        strict_numeric = raw_spec.get("kind") in ("yaml", "table", "array")
    summary_data = _object(_required(data, "summary"), "summary")
    counts: list[SummaryCount] = []
    for raw in _array(_required(summary_data, "counts"), "summary counts"):
        item = _object(raw, "summary count")
        counts.append(
            SummaryCount(
                name=_string(_required(item, "name"), "count name"),
                value=_integer(_required(item, "value"), "count value"),
                unit=_string(_required(item, "unit"), "count unit"),
            )
        )
    changes_data = _object(_required(data, "changes"), "changes")
    changes = tuple(
        _change_from_data(item, schema_version=schema_version)
        for item in _array(_required(changes_data, "items"), "change items")
    )
    raw_limit_reason = changes_data.get("limit_reason")
    limit_reason = _optional_string(raw_limit_reason, "limit_reason")
    if limit_reason not in (None, "change_items", "change_payload_bytes"):
        raise SerializationError(f"unknown change limit reason: {limit_reason}")
    metrics: list[Metric] = []
    for raw in _array(_required(data, "metrics"), "metrics"):
        item = _object(raw, "metric")
        metrics.append(
            Metric(
                name=_string(_required(item, "name"), "metric name"),
                value=_numeric_from_data(
                    _required(item, "value"), strict=strict_numeric
                ),
                unit=_string(_required(item, "unit"), "metric unit"),
                direction=_enum_value(
                    MetricDirection,
                    _required(item, "direction"),
                    "metric direction",
                ),
                aggregation=_optional_string(
                    _required(item, "aggregation"), "aggregation"
                ),
            )
        )
    evaluations: list[PolicyEvaluation] = []
    for raw in _array(_required(data, "evaluations"), "evaluations"):
        item = _object(raw, "evaluation")
        operator_value = _optional_string(
            _required(item, "operator"), "evaluation operator"
        )
        if operator_value not in (None, "eq", "ne", "lt", "le", "gt", "ge"):
            raise SerializationError("unknown evaluation operator")
        threshold_value = _required(item, "threshold")
        observed_value = _required(item, "observed")
        evaluations.append(
            PolicyEvaluation(
                rule_id=_string(_required(item, "rule_id"), "rule_id"),
                verdict=_enum_value(
                    Verdict, _required(item, "verdict"), "evaluation verdict"
                ),
                metric_name=_optional_string(
                    _required(item, "metric_name"), "metric_name"
                ),
                operator=cast(
                    Literal["eq", "ne", "lt", "le", "gt", "ge"] | None,
                    operator_value,
                ),
                threshold=(
                    None
                    if threshold_value is None
                    else _numeric_from_data(threshold_value, strict=strict_numeric)
                ),
                observed=(
                    None
                    if observed_value is None
                    else _numeric_from_data(observed_value, strict=strict_numeric)
                ),
            )
        )
    artifacts: list[ArtifactRef] = []
    for raw in _array(_required(data, "artifacts"), "artifacts"):
        item = _object(raw, "artifact")
        artifacts.append(
            ArtifactRef(
                artifact_id=_string(_required(item, "artifact_id"), "artifact_id"),
                kind=_string(_required(item, "kind"), "artifact kind"),
                media_type=_string(_required(item, "media_type"), "media_type"),
                uri=_string(_required(item, "uri"), "uri"),
                sha256=_string(_required(item, "sha256"), "sha256"),
                size_bytes=_integer(_required(item, "size_bytes"), "size_bytes"),
            )
        )
    try:
        summary = DiffSummary(
            change_count=_optional_integer(
                _required(summary_data, "change_count"), "change_count"
            ),
            counts=tuple(counts),
        )
        change_set = ChangeSet(
            completeness=_enum_value(
                ChangeCompleteness,
                _required(changes_data, "completeness"),
                "change completeness",
            ),
            items=changes,
            total_count=_optional_integer(
                _required(changes_data, "total_count"), "total_count"
            ),
            returned_count=_integer(
                _required(changes_data, "returned_count"), "returned_count"
            ),
            omitted_count=_optional_integer(
                _required(changes_data, "omitted_count"), "omitted_count"
            ),
            selection=_enum_value(
                ChangeSelection,
                _required(changes_data, "selection"),
                "change selection",
            ),
            limit=_optional_integer(_required(changes_data, "limit"), "limit"),
            limit_reason=cast(
                Literal["change_items", "change_payload_bytes"] | None,
                limit_reason,
            ),
        )
        result = DiffResult(
            relation=_enum_value(Relation, _required(data, "relation"), "relation"),
            verdict=_enum_value(Verdict, _required(data, "verdict"), "verdict"),
            fidelity=_enum_value(Fidelity, _required(data, "fidelity"), "fidelity"),
            summary=summary,
            changes=change_set,
            metrics=tuple(metrics),
            evaluations=tuple(evaluations),
            artifacts=tuple(artifacts),
            provenance=_provenance_from_data(
                _required(data, "provenance"), schema_version=schema_version
            ),
        )
        if schema_version == 3:
            if result.provenance.spec.get("kind") in ("yaml", "table", "array") and (
                tuple(item.name for item in metrics)
                != tuple(item.name for item in result.metrics)
            ):
                raise SerializationError(
                    "schema-v3 structured metrics are not in canonical order"
                )
            _validate_v3_result(result)
        return result
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _finite_count(metric: Metric, name: str) -> int:
    if not isinstance(metric.value, FiniteValue) or not metric.value.value.is_integer():
        raise SerializationError(f"{name} must be a finite integer count")
    count = int(metric.value.value)
    if count < 0:
        raise SerializationError(f"{name} must be non-negative")
    return count


def _structured_u64(value: int) -> bytes:
    if not 0 <= value <= 2**64 - 1:
        raise SerializationError("canonical structured length exceeds U64")
    return value.to_bytes(8, "big")


def _structured_signed(value: int) -> bytes:
    if value == 0:
        return b""
    length = max(1, (value.bit_length() + 8) // 8)
    encoded = value.to_bytes(length, "big", signed=True)
    while len(encoded) > 1 and (
        (encoded[0] == 0 and encoded[1] < 0x80)
        or (encoded[0] == 0xFF and encoded[1] >= 0x80)
    ):
        encoded = encoded[1:]
    return encoded


def _structured_magnitude(decimal: str) -> bytes:
    chunks: list[int] = []
    for offset in range(0, len(decimal), 9):
        width = min(9, len(decimal) - offset)
        factor = 10**width
        carry = int(decimal[offset : offset + width])
        for index in range(len(chunks)):
            value = chunks[index] * factor + carry
            chunks[index] = value & 0xFFFFFFFF
            carry = value >> 32
        while carry:
            chunks.append(carry & 0xFFFFFFFF)
            carry >>= 32
    encoded = b"".join(item.to_bytes(4, "big") for item in reversed(chunks))
    return encoded.lstrip(b"\x00")


def _bounded_exponent(digits: str, limit: int) -> int:
    value = 0
    for character in digits:
        digit = ord(character) - ord("0")
        if limit < 0 or value > (limit - digit) // 10:
            raise SerializationError("JSON number fact exceeds its exponent limit")
        value = value * 10 + digit
    return value


def _validate_lexical_number_fact(fact: ScalarFact, spec: JsonCompareSpec) -> None:
    if fact.lexical is None or not isinstance(fact.value, str):
        raise SerializationError("lexical JSON number fact is incomplete")
    lexical = fact.lexical
    digit_count = sum(
        character.isascii() and character.isdigit() for character in lexical
    )
    if digit_count > spec.limits.max_number_digits:
        raise SerializationError("JSON number fact exceeds its digit limit")
    unsigned = lexical[1:] if lexical.startswith("-") else lexical
    mantissa, marker, exponent_text = unsigned.lower().partition("e")
    integer, point, fraction = mantissa.partition(".")
    explicit_exponent = 0
    if marker:
        exponent_negative = exponent_text.startswith("-")
        exponent_digits = exponent_text.lstrip("+-")
        exponent_limit = spec.limits.max_abs_exponent + len(fraction)
        if exponent_negative:
            exponent_limit = spec.limits.max_abs_exponent - len(fraction)
        explicit_exponent = _bounded_exponent(exponent_digits, exponent_limit)
        if exponent_negative:
            explicit_exponent = -explicit_exponent
    exponent = explicit_exponent - len(fraction)
    if abs(exponent) > spec.limits.max_abs_exponent:
        raise SerializationError("JSON number fact exceeds its exponent limit")
    coefficient = (integer + fraction).lstrip("0") or "0"
    negative = lexical.startswith("-")
    if coefficient == "0":
        negative = False
        exponent = 0
    else:
        trailing = len(coefficient) - len(coefficient.rstrip("0"))
        if trailing:
            coefficient = coefficient[:-trailing]
            exponent += trailing
    if point or marker:
        canonical = f"{'-' if negative else ''}{coefficient}E{exponent}"
    else:
        canonical = f"{'-' if negative else ''}{coefficient}{'0' * exponent}"
    if canonical != fact.value:
        raise SerializationError("JSON number fact disagrees with its lexical token")


def _scalar_fact_digest(fact: ScalarFact, spec: JsonCompareSpec) -> str:
    if fact.kind in ("integer", "decimal"):
        if not isinstance(fact.value, str):
            raise SerializationError("JSON number fact lacks canonical text")
        if fact.lexical is not None:
            _validate_lexical_number_fact(fact, spec)
        if spec.number_mode is JsonNumberMode.LEXICAL:
            if fact.lexical is None:
                raise SerializationError("lexical JSON number fact lacks its token")
            domain = "structured/number/lexical"
            payload = fact.lexical.encode("utf-8")
        elif fact.kind == "integer":
            digits = fact.value[1:] if fact.value.startswith("-") else fact.value
            if len(digits) > spec.limits.max_number_digits:
                raise SerializationError("JSON integer fact exceeds its digit limit")
            magnitude = _structured_magnitude(digits)
            payload = (
                b"\x03"
                + (b"\x01" if fact.value.startswith("-") else b"\x00")
                + _structured_u64(len(magnitude))
                + magnitude
            )
            domain = "structured/value"
        else:
            unsigned = fact.value[1:] if fact.value.startswith("-") else fact.value
            coefficient, exponent_text = unsigned.split("E", 1)
            if len(coefficient) > spec.limits.max_number_digits:
                raise SerializationError("JSON decimal fact exceeds its digit limit")
            exponent_negative = exponent_text.startswith("-")
            exponent_limit = spec.limits.max_abs_exponent
            if not exponent_negative:
                exponent_limit += spec.limits.max_number_digits
            exponent_value = _bounded_exponent(
                exponent_text.removeprefix("-"), exponent_limit
            )
            if exponent_negative:
                exponent_value = -exponent_value
            coefficient_bytes = coefficient.encode("ascii")
            exponent_bytes = _structured_signed(exponent_value)
            payload = (
                b"\x04"
                + (b"\x01" if fact.value.startswith("-") else b"\x00")
                + _structured_u64(len(coefficient_bytes))
                + coefficient_bytes
                + _structured_u64(len(exponent_bytes))
                + exponent_bytes
            )
            domain = "structured/value"
    else:
        domain = "structured/value"
        if fact.kind == "null":
            payload = b"\x00"
        elif fact.kind == "boolean":
            payload = b"\x02" if fact.value is True else b"\x01"
        elif fact.kind == "string" and isinstance(fact.value, str):
            encoded = fact.value.encode("utf-8")
            if len(encoded) > spec.limits.max_scalar_bytes:
                raise SerializationError("JSON string fact exceeds its spec limit")
            payload = b"\x05" + _structured_u64(len(encoded)) + encoded
        else:
            raise SerializationError("JSON change contains a non-JSON scalar fact")
    digest = hashlib.sha256()
    digest.update(f"platydiff/v3/{domain}".encode())
    digest.update(b"\x00")
    digest.update(_structured_u64(len(payload)))
    digest.update(payload)
    return digest.hexdigest()


def _validate_contract_identity(
    result: DiffResult,
    *,
    comparator_id: str,
    algorithm_id: str,
) -> None:
    provenance = result.provenance
    if (
        result.fidelity is not Fidelity.FULL
        or result.artifacts
        or not isinstance(provenance, ComparisonProvenanceV2)
        or provenance.comparator_id != comparator_id
        or provenance.comparator_version != "1"
        or provenance.algorithm_id != algorithm_id
        or provenance.provider is not None
        or provenance.detector_provider is not None
        or provenance.seeds
    ):
        raise SerializationError(
            f"schema-v3 {comparator_id} result has incompatible identity"
        )
    if result.changes.completeness is ChangeCompleteness.PARTIAL:
        raise SerializationError(
            f"schema-v3 {comparator_id} changes must not be partial"
        )


def _validate_v3_contract_attempt(
    execution: ExecutionRecordV2,
    result: DiffResult,
) -> None:
    kind = result.provenance.spec.get("kind")
    if kind not in ("yaml", "table", "array"):
        return
    if len(execution.attempts) != 1:
        raise SerializationError(
            f"schema-v3 {kind} contract fixture requires exactly one attempt"
        )
    attempt = execution.attempts[0]
    if not isinstance(attempt, CapabilityAttemptV2) or (
        attempt.capability_id != result.provenance.comparator_id
        or attempt.capability_version != result.provenance.comparator_version
        or attempt.disposition != "selected"
        or attempt.provider is not None
        or attempt.backend_id is not None
        or attempt.backend_version is not None
        or attempt.reason_code is not None
    ):
        raise SerializationError(
            f"schema-v3 {kind} contract fixture attempt is not canonical"
        )


def _validate_contract_transformations(
    result: DiffResult,
    expected: tuple[tuple[str, str, JsonObject], ...],
    *,
    comparator_id: str,
) -> None:
    actual = tuple(
        (item.stage, item.transformation_id, item.parameters)
        for item in result.provenance.transformations
    )
    if actual != expected:
        raise SerializationError(
            f"schema-v3 {comparator_id} transformations are not canonical"
        )


def _validate_contract_counts(
    result: DiffResult,
    *,
    prefix: str,
    required: tuple[tuple[str, MetricDirection], ...],
    summary_unit: str,
    compared_name: str,
    equal_name: str,
    changed_name: str,
    change_count_name: str,
) -> dict[str, int]:
    metrics = {item.name: item for item in result.metrics}
    required_names = {f"{prefix}.{name}" for name, _ in required}
    error_names = {
        f"{prefix}.maximum_absolute_error",
        f"{prefix}.maximum_relative_error",
    }
    allowed_names = required_names | (
        error_names if prefix in ("table", "array") else set()
    )
    if not required_names <= set(metrics) or not set(metrics) <= allowed_names:
        raise SerializationError(f"schema-v3 {prefix} metrics are not canonical")
    directions = dict(required)
    counts: dict[str, int] = {}
    for short_name, direction in directions.items():
        metric = metrics[f"{prefix}.{short_name}"]
        counts[short_name] = _finite_count(metric, short_name)
        if (
            metric.unit != "items"
            or metric.aggregation != "count"
            or metric.direction is not direction
        ):
            raise SerializationError(
                f"schema-v3 {prefix} metric metadata is not canonical"
            )
    finite_pairs = counts.get("finite_numeric_pairs")
    expected_error_names = error_names if finite_pairs not in (None, 0) else set()
    if set(metrics) - required_names != expected_error_names:
        raise SerializationError(
            f"schema-v3 {prefix} error metric applicability is not canonical"
        )
    for name in expected_error_names:
        metric = metrics[name]
        expected_unit = "numeric_values" if name.endswith("absolute_error") else "ratio"
        if (
            metric.unit != expected_unit
            or metric.aggregation != "maximum"
            or metric.direction is not MetricDirection.LOWER_IS_BETTER
        ):
            raise SerializationError(
                f"schema-v3 {prefix} error metric metadata is not canonical"
            )
        if name.endswith("absolute_error"):
            valid_value = (
                isinstance(metric.value, FiniteValue) and metric.value.value >= 0
            )
        else:
            valid_value = (
                isinstance(metric.value, FiniteValue) and metric.value.value >= 0
            ) or isinstance(metric.value, PositiveInfinityValue)
        if not valid_value:
            raise SerializationError(
                f"schema-v3 {prefix} error metric value is not canonical"
            )
    compared = counts[compared_name]
    equal = counts[equal_name]
    changed = counts[changed_name]
    if (
        equal + changed != compared
        or result.changes.total_count != counts[change_count_name]
    ):
        raise SerializationError(f"schema-v3 {prefix} count identities do not hold")
    for category in (
        "missing_pairs",
        "nan_pairs",
        "infinity_pairs",
        "finite_numeric_pairs",
    ):
        if category in counts and counts[category] > compared:
            raise SerializationError(
                f"schema-v3 {prefix} category count exceeds compared count"
            )
    summary = {item.name: item for item in result.summary.counts}
    if set(summary) != set(counts) or any(
        summary[name].value != value or summary[name].unit != summary_unit
        for name, value in counts.items()
    ):
        raise SerializationError(f"schema-v3 {prefix} summary is not canonical")
    if result.summary.change_count != counts[change_count_name]:
        raise SerializationError(f"schema-v3 {prefix} change count is inconsistent")
    expected_relation = (
        Relation.EQUAL if counts[change_count_name] == 0 else Relation.DIFFERENT
    )
    expected_verdict = Verdict.PASS if counts[change_count_name] == 0 else Verdict.FAIL
    if (
        result.relation is not expected_relation
        or result.verdict is not expected_verdict
        or len(result.evaluations) != 1
    ):
        raise SerializationError(f"schema-v3 {prefix} outcome truth is not canonical")
    evaluation = result.evaluations[0]
    if evaluation.rule_id != f"{prefix}.value_equality" and not (
        prefix == "yaml" and evaluation.rule_id == "yaml.semantic_equality"
    ):
        raise SerializationError(f"schema-v3 {prefix} evaluation is not canonical")
    if evaluation.metric_name != f"{prefix}.changed_items" and not (
        prefix == "yaml" and evaluation.metric_name == "yaml.changed_values"
    ):
        raise SerializationError(f"schema-v3 {prefix} evaluation is not canonical")
    if (
        evaluation.operator != "eq"
        or not isinstance(evaluation.threshold, FiniteValue)
        or evaluation.threshold.value != 0
        or not isinstance(evaluation.observed, FiniteValue)
        or evaluation.observed.value != counts[change_count_name]
        or evaluation.verdict is not expected_verdict
    ):
        raise SerializationError(f"schema-v3 {prefix} evaluation is not canonical")
    return counts


def _validate_contract_resources(
    result: DiffResult,
    expected: dict[str, int],
    *,
    comparator_id: str,
) -> None:
    resources = {item.name: item for item in result.provenance.resources}
    if set(resources) != set(expected) or any(
        resources[name].limit != limit or resources[name].used > limit
        for name, limit in expected.items()
    ):
        raise SerializationError(
            f"schema-v3 {comparator_id} resources are not canonical"
        )
    for side, source in zip(("before", "after"), result.provenance.inputs, strict=True):
        input_name = f"{side}_input_bytes"
        if input_name in resources and resources[input_name].used != source.size_bytes:
            raise SerializationError(
                f"schema-v3 {comparator_id} input resource use is inconsistent"
            )
    if resources["change_items"].used != result.changes.returned_count or resources[
        "change_payload_bytes"
    ].used != sum(serialized_change_size(item) for item in result.changes.items):
        raise SerializationError(
            f"schema-v3 {comparator_id} change resources are inconsistent"
        )


def _validate_contract_truncation(
    result: DiffResult,
    *,
    max_change_items: int,
    max_change_payload_bytes: int,
    comparator_id: str,
) -> None:
    if result.changes.completeness is not ChangeCompleteness.TRUNCATED:
        return
    if result.changes.limit_reason == "change_items":
        valid = (
            result.changes.limit == max_change_items
            and result.changes.returned_count == max_change_items
        )
    elif result.changes.limit_reason == "change_payload_bytes":
        valid = (
            result.changes.limit == max_change_payload_bytes
            and result.changes.returned_count < max_change_items
            and sum(serialized_change_size(item) for item in result.changes.items)
            <= max_change_payload_bytes
        )
    else:
        valid = False
    if not valid:
        raise SerializationError(
            f"schema-v3 {comparator_id} truncation evidence is inconsistent"
        )


def _structured_contract_resources(
    limits: StructuredResourceLimits,
    *,
    yaml_limits: YamlResourceLimits | None = None,
) -> dict[str, int]:
    expected: dict[str, int] = {}
    for side in ("before", "after"):
        expected.update(
            {
                f"{side}_input_bytes": limits.max_input_bytes,
                f"{side}_scalar_bytes": limits.max_scalar_bytes,
                f"{side}_depth": limits.max_depth,
                f"{side}_nodes": limits.max_nodes,
                f"{side}_number_digits": limits.max_number_digits,
                f"{side}_abs_exponent": limits.max_abs_exponent,
            }
        )
        if yaml_limits is not None:
            expected.update(
                {
                    f"{side}_aliases": yaml_limits.max_aliases,
                    f"{side}_expanded_nodes": yaml_limits.max_expanded_nodes,
                    f"{side}_expanded_scalar_bytes": (
                        yaml_limits.max_expanded_scalar_bytes
                    ),
                }
            )
    expected.update(
        {
            "compare_work": limits.max_compare_work,
            "change_items": limits.max_change_items,
            "change_payload_bytes": limits.max_change_payload_bytes,
        }
    )
    return expected


def _validate_yaml_result(result: DiffResult, spec: YamlCompareSpec) -> None:
    _validate_contract_identity(
        result,
        comparator_id="yaml",
        algorithm_id="yaml.structural.tree.v1",
    )
    expected_transformations: list[tuple[str, str, JsonObject]] = []
    if any(
        item.source_kind is not SourceKind.TEXT for item in result.provenance.inputs
    ):
        expected_transformations.append(
            (
                "decoding",
                "yaml.decode.utf8",
                {"encoding": spec.encoding.value, "profile": spec.profile},
            )
        )
    expected_transformations.extend(
        (
            ("normalizing", "yaml.presentation.elide", {}),
            ("normalizing", "yaml.object_order.ignore", {}),
            (
                "aligning",
                "yaml.pointer.position",
                {"pointer": "rfc6901", "sequences": "positional"},
            ),
        )
    )
    _validate_contract_transformations(
        result, tuple(expected_transformations), comparator_id="yaml"
    )
    if any(not isinstance(item, StructuredChange) for item in result.changes.items):
        raise SerializationError("schema-v3 YAML changes must be structured changes")
    yaml_paths = tuple(
        item.path for item in result.changes.items if isinstance(item, StructuredChange)
    )
    # A pointer alone cannot reveal whether a numeric token belongs to a mapping
    # (`"10"` before `"2"`) or a sequence (`2` before `10`). The reader can
    # prove uniqueness; full preorder remains a producer invariant.
    if len(yaml_paths) != len(set(yaml_paths)):
        raise SerializationError("schema-v3 YAML change paths must be unique")
    digest_spec = JsonCompareSpec(
        encoding=spec.encoding,
        number_mode=JsonNumberMode.VALUE,
        detail_mode=spec.detail_mode,
        limits=StructuredResourceLimits(
            max_input_bytes=spec.limits.max_input_bytes,
            max_scalar_bytes=spec.limits.max_scalar_bytes,
            max_depth=spec.limits.max_depth,
            max_nodes=spec.limits.max_nodes,
            max_number_digits=spec.limits.max_number_digits,
            max_abs_exponent=spec.limits.max_abs_exponent,
            max_compare_work=spec.limits.max_compare_work,
            max_change_items=spec.limits.max_change_items,
            max_change_payload_bytes=spec.limits.max_change_payload_bytes,
        ),
    )
    resources = {item.name: item for item in result.provenance.resources}
    for item in result.changes.items:
        if not isinstance(item, StructuredChange):
            raise RuntimeError("YAML structured-change narrowing failed")
        for side, digest, fact in (
            ("before", item.before_digest, item.before_fact),
            ("after", item.after_digest, item.after_fact),
        ):
            if spec.detail_mode is StructuredDetailMode.DIGEST_ONLY:
                if fact is not None:
                    raise SerializationError("digest_only YAML changes must omit facts")
            elif fact is None:
                continue
            elif isinstance(fact, ScalarFact) and (
                fact.kind not in ("null", "boolean", "integer", "decimal", "string")
                or fact.lexical is not None
            ):
                raise SerializationError("YAML change contains an invalid scalar fact")
            elif isinstance(fact, ScalarFact):
                if digest is None or _scalar_fact_digest(fact, digest_spec) != digest:
                    raise SerializationError(
                        "YAML scalar fact does not match its evidence digest"
                    )
            elif fact.descendant_count >= spec.limits.max_nodes:
                raise SerializationError("YAML subtree fact exceeds its node limit")
            else:
                materialized_nodes = fact.descendant_count + 1
                for resource_name in ("nodes", "expanded_nodes"):
                    usage = resources.get(f"{side}_{resource_name}")
                    if usage is not None and usage.used < materialized_nodes:
                        raise SerializationError(
                            f"YAML {side} {resource_name} resource does not cover "
                            "subtree evidence"
                        )
        if spec.detail_mode is StructuredDetailMode.VALUES:
            if item.before_type is not None and item.before_fact is None:
                raise SerializationError("values YAML change is missing a before fact")
            if item.after_type is not None and item.after_fact is None:
                raise SerializationError("values YAML change is missing an after fact")
        pointer_tokens = item.path.split("/")[1:]
        pointer_depth = len(pointer_tokens)
        if pointer_depth > spec.limits.max_depth:
            raise SerializationError("YAML change path exceeds its depth limit")
        for side, value_type in (
            ("before", item.before_type),
            ("after", item.after_type),
        ):
            depth_usage = resources.get(f"{side}_depth")
            if (
                value_type is not None
                and depth_usage is not None
                and depth_usage.used < pointer_depth
            ):
                raise SerializationError(
                    f"YAML {side} depth resource does not cover change evidence"
                )
        for token in pointer_tokens:
            decoded_token = token.replace("~1", "/").replace("~0", "~")
            if len(decoded_token.encode("utf-8")) > spec.limits.max_scalar_bytes:
                raise SerializationError("YAML Pointer token exceeds its spec limit")
    required = (
        ("compared_values", MetricDirection.NEUTRAL),
        ("equal_values", MetricDirection.NEUTRAL),
        ("changed_values", MetricDirection.LOWER_IS_BETTER),
    )
    _validate_contract_counts(
        result,
        prefix="yaml",
        required=required,
        summary_unit="values",
        compared_name="compared_values",
        equal_name="equal_values",
        changed_name="changed_values",
        change_count_name="changed_values",
    )
    _validate_contract_resources(
        result,
        _structured_contract_resources(spec.limits, yaml_limits=spec.limits),
        comparator_id="yaml",
    )
    _validate_contract_truncation(
        result,
        max_change_items=spec.limits.max_change_items,
        max_change_payload_bytes=spec.limits.max_change_payload_bytes,
        comparator_id="yaml",
    )


def _validate_table_fact_against_spec(
    fact: TableFact,
    spec: TableCompareSpec,
) -> None:
    if isinstance(fact, ScalarFact):
        _validate_table_scalar_fact(fact, spec)
    if (
        isinstance(fact, ScalarFact)
        and not spec.columns
        and fact.kind
        not in (
            "string",
            "missing",
        )
    ):
        raise SerializationError("untyped table cells must be string or missing facts")
    if isinstance(fact, TableRowFact) and spec.columns:
        expected_names = tuple(column.name for column in spec.columns)
        if spec.column_order == "by_name":
            expected_names = tuple(sorted(expected_names))
        if tuple(name for name, _ in fact.cells) != expected_names:
            raise SerializationError("table row fact columns do not match the spec")
        columns_by_name = {column.name: column for column in spec.columns}
        for name, cell in fact.cells:
            column = columns_by_name[name]
            _validate_table_scalar_fact(cell, spec)
            allowed = {
                "string": ("string", "missing"),
                "integer": ("integer", "missing"),
                "float64": (
                    "float64",
                    "nan",
                    "positive_infinity",
                    "negative_infinity",
                    "missing",
                ),
                "boolean": ("boolean", "missing"),
            }[column.dtype]
            if cell.kind not in allowed:
                raise SerializationError("table row fact cell kind violates the spec")
    elif isinstance(fact, TableRowFact):
        if len(fact.cells) > spec.limits.max_columns:
            raise SerializationError("table row fact exceeds its column limit")
        for name, cell in fact.cells:
            if len(name.encode("utf-8")) > spec.limits.max_cell_bytes:
                raise SerializationError("table row column name exceeds its byte limit")
            _validate_table_scalar_fact(cell, spec)
        if any(cell.kind not in ("string", "missing") for _, cell in fact.cells):
            raise SerializationError(
                "untyped table row cells must be string or missing facts"
            )
    elif isinstance(fact, ColumnSchemaFact):
        if len(fact.name.encode("utf-8")) > spec.limits.max_cell_bytes:
            raise SerializationError("table column fact name exceeds its byte limit")
        matching = next(
            (column for column in spec.columns if column.name == fact.name), None
        )
        if matching is None and spec.columns:
            raise SerializationError("table column fact is not declared by the spec")
        if matching is None and fact.dtype != "string":
            raise SerializationError("untyped table columns must use string facts")
        if matching is not None and (
            fact.dtype != matching.dtype
            or fact.missing_token_count != len(matching.missing_tokens)
            or fact.numeric != matching.numeric
        ):
            raise SerializationError("table column fact violates the spec")
    elif isinstance(fact, ColumnOrderFact):
        if len(fact.names) > spec.limits.max_columns or any(
            len(name.encode("utf-8")) > spec.limits.max_cell_bytes
            for name in fact.names
        ):
            raise SerializationError("table column-order fact exceeds its limits")
        if spec.columns and set(fact.names) != {column.name for column in spec.columns}:
            raise SerializationError("table column-order fact violates the spec")


def _validate_table_scalar_fact(fact: ScalarFact, spec: TableCompareSpec) -> None:
    if fact.lexical is not None:
        raise SerializationError("table scalar facts must not carry lexical text")
    if isinstance(fact.value, str) and (
        len(fact.value.encode("utf-8")) > spec.limits.max_cell_bytes
    ):
        raise SerializationError("table scalar fact exceeds its cell-byte limit")
    if (
        fact.kind == "integer"
        and isinstance(fact.value, str)
        and len(fact.value.removeprefix("-")) > spec.limits.max_number_digits
    ):
        raise SerializationError("table integer fact exceeds its digit limit")
    if fact.kind == "float64" and isinstance(fact.value, str):
        try:
            numeric = float.fromhex(fact.value)
        except ValueError as error:
            raise SerializationError(
                "table float64 fact is not canonical C99 hex"
            ) from error
        if not math.isfinite(numeric) or numeric.hex() != fact.value:
            raise SerializationError("table float64 fact is not canonical C99 hex")


def _table_column_policy_digest(spec: TableCompareSpec) -> str:
    columns = spec_to_data(spec)["columns"]
    payload = json.dumps(
        columns,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(b"platydiff/v3/table/column-policy")
    digest.update(b"\x00")
    digest.update(_structured_u64(len(payload)))
    digest.update(payload)
    return digest.hexdigest()


def _validate_table_keyed_coordinates(changes: tuple[TableChange, ...]) -> None:
    seen: dict[int, tuple[str, tuple[ScalarFact, ...] | None]] = {}
    ordinals_by_key: dict[tuple[ScalarFact, ...], int] = {}
    for item in changes:
        if item.key_ordinal is None:
            continue
        if item.key is not None:
            existing_ordinal = ordinals_by_key.get(item.key)
            if existing_ordinal is not None and existing_ordinal != item.key_ordinal:
                raise SerializationError(
                    "table key facts carry inconsistent key ordinals"
                )
            ordinals_by_key[item.key] = item.key_ordinal
        existing = seen.get(item.key_ordinal)
        if existing is None:
            seen[item.key_ordinal] = (item.operation, item.key)
            continue
        existing_operation, existing_key = existing
        if existing_key != item.key:
            raise SerializationError("table key ordinal carries inconsistent key facts")
        if existing_operation != "cell_replace" or item.operation != "cell_replace":
            raise SerializationError(
                "table key ordinal carries conflicting row/cell operations"
            )


def _validate_table_result(result: DiffResult, spec: TableCompareSpec) -> None:
    _validate_contract_identity(
        result,
        comparator_id="table",
        algorithm_id="table.delimited.align.v1",
    )
    if (
        len(spec.columns) > spec.limits.max_columns
        or len(spec.key_columns) > spec.limits.max_columns
        or any(
            len(name.encode("utf-8")) > spec.limits.max_cell_bytes
            for name in spec.key_columns
        )
        or any(
            len(column.name.encode("utf-8")) > spec.limits.max_cell_bytes
            or any(
                len(token.encode("utf-8")) > spec.limits.max_cell_bytes
                for token in column.missing_tokens
            )
            for column in spec.columns
        )
    ):
        raise SerializationError("schema-v3 table column policy exceeds its limits")
    expected_transformations: list[tuple[str, str, JsonObject]] = [
        (
            "decoding",
            f"table.{spec.dialect}.decode",
            {
                "dialect": spec.dialect,
                "encoding": spec.encoding.value,
                "header": spec.header,
            },
        ),
        (
            "normalizing",
            "table.presentation.elide",
            {"quoting": "double", "record_terminators": "elided"},
        ),
    ]
    if spec.columns:
        expected_transformations.append(
            (
                "normalizing",
                "table.cells.typed",
                {"column_policy_digest": _table_column_policy_digest(spec)},
            )
        )
    expected_transformations.extend(
        (
            (
                "aligning",
                f"table.columns.{spec.column_order}",
                {"mode": spec.column_order},
            ),
            (
                "aligning",
                f"table.rows.{spec.alignment}",
                {"key_columns": list(spec.key_columns), "mode": spec.alignment},
            ),
        )
    )
    _validate_contract_transformations(
        result, tuple(expected_transformations), comparator_id="table"
    )
    if any(not isinstance(item, TableChange) for item in result.changes.items):
        raise SerializationError("schema-v3 table changes must be table changes")
    table_changes = tuple(
        item for item in result.changes.items if isinstance(item, TableChange)
    )
    _validate_table_keyed_coordinates(table_changes)
    row_column_sets = {
        tuple(name for name, _ in fact.cells)
        for item in result.changes.items
        if isinstance(item, TableChange)
        for fact in (item.before_fact, item.after_fact)
        if isinstance(fact, TableRowFact)
    }
    if len(row_column_sets) > 1:
        raise SerializationError("table row facts disagree on aligned columns")
    aligned_columns = (
        tuple(
            sorted(column.name for column in spec.columns)
            if spec.column_order == "by_name"
            else (column.name for column in spec.columns)
        )
        if spec.columns
        else next(iter(row_column_sets), ())
    )
    operation_rank = {
        "column_add": 0,
        "column_remove": 1,
        "column_reorder": 2,
        "row_remove": 3,
        "row_add": 4,
        "cell_replace": 5,
    }
    column_positions = {name: index for index, name in enumerate(aligned_columns)}
    order_keys = tuple(
        (
            operation_rank[item.operation],
            item.key_ordinal if item.key_ordinal is not None else item.row or 0,
            (
                column_positions[item.column]
                if item.operation == "cell_replace" and item.column in column_positions
                else 0
            ),
            (
                item.column or ""
                if item.operation != "cell_replace" or aligned_columns
                else ""
            ),
        )
        for item in result.changes.items
        if isinstance(item, TableChange)
    )
    coordinate_keys = tuple(
        (
            item.operation,
            item.key_ordinal if item.key_ordinal is not None else item.row,
            item.column,
        )
        for item in result.changes.items
        if isinstance(item, TableChange)
    )
    if order_keys != tuple(sorted(order_keys)) or len(coordinate_keys) != len(
        set(coordinate_keys)
    ):
        raise SerializationError("schema-v3 table changes are not in canonical order")
    columns_by_name = {column.name: column for column in spec.columns}
    table_resources = {item.name: item for item in result.provenance.resources}
    for item in result.changes.items:
        if not isinstance(item, TableChange):
            raise RuntimeError("table-change narrowing failed")
        if item.operation == "column_reorder" and spec.column_order != "exact":
            raise SerializationError(
                "by-name table alignment must not emit column reorder changes"
            )
        if spec.alignment == "position":
            if item.key_ordinal is not None or item.key is not None:
                raise SerializationError("positional table change carries key data")
            if item.row is not None:
                if item.row > spec.limits.max_rows:
                    raise SerializationError("table row coordinate exceeds its limit")
                required_sides = {
                    "row_add": ("after",),
                    "row_remove": ("before",),
                    "cell_replace": ("before", "after"),
                }.get(item.operation, ())
                for side in required_sides:
                    usage = table_resources.get(f"{side}_rows")
                    if usage is not None and item.row > usage.used:
                        raise SerializationError(
                            f"table {side} row resource does not cover "
                            "change coordinate"
                        )
        elif item.operation in ("row_add", "row_remove", "cell_replace"):
            if item.row is not None or item.key_ordinal is None:
                raise SerializationError("keyed table change has invalid coordinates")
            if spec.detail_mode is StructuredDetailMode.VALUES:
                if item.key is None or len(item.key) != len(spec.key_columns):
                    raise SerializationError("values table change has an invalid key")
                for name, key_fact in zip(spec.key_columns, item.key, strict=True):
                    _validate_table_scalar_fact(key_fact, spec)
                    column = columns_by_name.get(name)
                    if column is not None and key_fact.kind != column.dtype:
                        raise SerializationError(
                            "table key fact kind violates its declared column"
                        )
            elif item.key is not None:
                raise SerializationError("digest_only table change must omit its key")
            before_rows = table_resources.get("before_rows")
            after_rows = table_resources.get("after_rows")
            if (
                item.key_ordinal is not None
                and before_rows is not None
                and after_rows is not None
                and (
                    item.key_ordinal > before_rows.used + after_rows.used
                    or item.key_ordinal > 2 * spec.limits.max_rows
                )
            ):
                raise SerializationError(
                    "table key ordinal exceeds the row-union resource bound"
                )
        if item.column is not None and (
            len(item.column.encode("utf-8")) > spec.limits.max_cell_bytes
        ):
            raise SerializationError("table column coordinate exceeds its byte limit")
        if (
            item.operation == "cell_replace"
            and aligned_columns
            and item.column not in aligned_columns
        ):
            raise SerializationError("table cell coordinate is not an aligned column")
        if spec.detail_mode is StructuredDetailMode.DIGEST_ONLY:
            if item.before_fact is not None or item.after_fact is not None:
                raise SerializationError("digest_only table change must omit facts")
        else:
            for side, digest, fact in (
                ("before", item.before_digest, item.before_fact),
                ("after", item.after_digest, item.after_fact),
            ):
                if digest is not None and fact is None:
                    raise SerializationError("values table change is missing a fact")
                if fact is not None:
                    _validate_table_fact_against_spec(fact, spec)
                    if isinstance(fact, TableRowFact):
                        cell_usage = table_resources.get(f"{side}_cells")
                        if cell_usage is not None and len(fact.cells) > cell_usage.used:
                            raise SerializationError(
                                f"table {side} cell resource does not cover row fact"
                            )
                    if isinstance(fact, ColumnSchemaFact) and fact.name != item.column:
                        raise SerializationError(
                            "table column fact disagrees with its coordinate"
                        )
                    if (
                        item.operation == "cell_replace"
                        and isinstance(fact, ScalarFact)
                        and item.column in columns_by_name
                    ):
                        column = columns_by_name[item.column]
                        allowed = {
                            "string": ("string", "missing"),
                            "integer": ("integer", "missing"),
                            "float64": (
                                "float64",
                                "nan",
                                "positive_infinity",
                                "negative_infinity",
                                "missing",
                            ),
                            "boolean": ("boolean", "missing"),
                        }[column.dtype]
                        if fact.kind not in allowed:
                            raise SerializationError(
                                "table cell fact kind violates its declared column"
                            )
    required = (
        ("compared_cells", MetricDirection.NEUTRAL),
        ("equal_cells", MetricDirection.NEUTRAL),
        ("changed_cells", MetricDirection.LOWER_IS_BETTER),
        ("changed_items", MetricDirection.LOWER_IS_BETTER),
        ("missing_pairs", MetricDirection.NEUTRAL),
        ("nan_pairs", MetricDirection.NEUTRAL),
        ("infinity_pairs", MetricDirection.NEUTRAL),
        ("finite_numeric_pairs", MetricDirection.NEUTRAL),
    )
    counts = _validate_contract_counts(
        result,
        prefix="table",
        required=required,
        summary_unit="cells",
        compared_name="compared_cells",
        equal_name="equal_cells",
        changed_name="changed_cells",
        change_count_name="changed_items",
    )
    if counts["changed_cells"] > counts["changed_items"]:
        raise SerializationError(
            "schema-v3 table changed-cell count exceeds changed items"
        )
    returned_cell_changes = sum(
        item.operation == "cell_replace"
        for item in result.changes.items
        if isinstance(item, TableChange)
    )
    if (
        result.changes.completeness is ChangeCompleteness.COMPLETE
        and counts["changed_cells"] != returned_cell_changes
    ) or (
        result.changes.completeness is ChangeCompleteness.TRUNCATED
        and returned_cell_changes > counts["changed_cells"]
    ):
        raise SerializationError("schema-v3 table cell-change count is inconsistent")
    expected_resources: dict[str, int] = {}
    for side in ("before", "after"):
        expected_resources.update(
            {
                f"{side}_input_bytes": spec.limits.max_input_bytes,
                f"{side}_cell_bytes": spec.limits.max_cell_bytes,
                f"{side}_rows": spec.limits.max_rows,
                f"{side}_columns": spec.limits.max_columns,
                f"{side}_cells": spec.limits.max_cells,
                f"{side}_number_digits": spec.limits.max_number_digits,
                f"{side}_abs_exponent": spec.limits.max_abs_exponent,
            }
        )
    expected_resources.update(
        {
            "compare_work": spec.limits.max_compare_work,
            "change_items": spec.limits.max_change_items,
            "change_payload_bytes": spec.limits.max_change_payload_bytes,
        }
    )
    _validate_contract_resources(result, expected_resources, comparator_id="table")
    _validate_contract_truncation(
        result,
        max_change_items=spec.limits.max_change_items,
        max_change_payload_bytes=spec.limits.max_change_payload_bytes,
        comparator_id="table",
    )


def _validate_array_result(result: DiffResult, spec: ArrayCompareSpec) -> None:
    _validate_contract_identity(
        result,
        comparator_id="array",
        algorithm_id="array.position.numeric.v1",
    )
    _validate_contract_transformations(
        result,
        (
            (
                "aligning",
                "array.elements.position",
                {"order": "c_row_major"},
            ),
        ),
        comparator_id="array",
    )
    if any(not isinstance(item, ArrayChange) for item in result.changes.items):
        raise SerializationError("schema-v3 array changes must be array changes")
    operations = tuple(
        item.operation for item in result.changes.items if isinstance(item, ArrayChange)
    )
    schema_operations = tuple(
        operation
        for operation in operations
        if operation in ("shape_replace", "dtype_replace")
    )
    if schema_operations and any(
        operation == "element_replace" for operation in operations
    ):
        raise SerializationError(
            "schema-v3 array schema changes suppress element changes"
        )
    if schema_operations not in (
        (),
        ("shape_replace",),
        ("dtype_replace",),
        ("shape_replace", "dtype_replace"),
    ):
        raise SerializationError("schema-v3 array schema changes are not canonical")
    element_indices: tuple[tuple[int, ...], ...] = tuple(
        item.index
        for item in result.changes.items
        if isinstance(item, ArrayChange)
        and item.operation == "element_replace"
        and item.index is not None
    )
    if element_indices != tuple(sorted(element_indices)) or len(element_indices) != len(
        set(element_indices)
    ):
        raise SerializationError("schema-v3 array indices are not in row-major order")
    required = (
        ("compared_elements", MetricDirection.NEUTRAL),
        ("equal_elements", MetricDirection.NEUTRAL),
        ("changed_elements", MetricDirection.LOWER_IS_BETTER),
        ("changed_items", MetricDirection.LOWER_IS_BETTER),
        ("missing_pairs", MetricDirection.NEUTRAL),
        ("nan_pairs", MetricDirection.NEUTRAL),
        ("infinity_pairs", MetricDirection.NEUTRAL),
        ("finite_numeric_pairs", MetricDirection.NEUTRAL),
    )
    counts = _validate_contract_counts(
        result,
        prefix="array",
        required=required,
        summary_unit="elements",
        compared_name="compared_elements",
        equal_name="equal_elements",
        changed_name="changed_elements",
        change_count_name="changed_items",
    )
    if counts["missing_pairs"] != 0:
        raise SerializationError("schema-v3 array missing-pair count must be zero")
    if schema_operations:
        if any(
            counts[name] != 0
            for name in (
                "compared_elements",
                "equal_elements",
                "changed_elements",
                "missing_pairs",
                "nan_pairs",
                "infinity_pairs",
                "finite_numeric_pairs",
            )
        ) or counts["changed_items"] != len(schema_operations):
            raise SerializationError(
                "schema-v3 array schema-replacement counts are inconsistent"
            )
    elif counts["changed_items"] != counts["changed_elements"]:
        raise SerializationError(
            "schema-v3 array element-change counts are inconsistent"
        )
    _validate_contract_resources(
        result,
        {
            "before_rank": spec.limits.max_rank,
            "before_elements": spec.limits.max_elements,
            "after_rank": spec.limits.max_rank,
            "after_elements": spec.limits.max_elements,
            "compare_work": spec.limits.max_compare_work,
            "change_items": spec.limits.max_change_items,
            "change_payload_bytes": spec.limits.max_change_payload_bytes,
        },
        comparator_id="array",
    )
    _validate_contract_truncation(
        result,
        max_change_items=spec.limits.max_change_items,
        max_change_payload_bytes=spec.limits.max_change_payload_bytes,
        comparator_id="array",
    )


def _validate_v3_result(result: DiffResult) -> None:
    kind = result.provenance.spec.get("kind")
    if kind in ("auto", "text", "binary"):
        if any(
            isinstance(item, (StructuredChange, TableChange, ArrayChange))
            for item in result.changes.items
        ):
            raise SerializationError("legacy schema-v3 result has Phase 4 changes")
        return
    if kind in ("yaml", "table", "array"):
        spec = spec_from_data(result.provenance.spec)
        if spec_to_data(spec) != result.provenance.spec:
            raise SerializationError(
                f"schema-v3 {kind} spec must be normalized exactly"
            )
        if isinstance(spec, YamlCompareSpec):
            _validate_yaml_result(result, spec)
        elif isinstance(spec, TableCompareSpec):
            _validate_table_result(result, spec)
        elif isinstance(spec, ArrayCompareSpec):
            _validate_array_result(result, spec)
        else:
            raise SerializationError(f"schema-v3 {kind} spec type is invalid")
        return
    if kind != "json":
        raise SerializationError(f"unknown schema-v3 built-in spec kind: {kind}")
    spec = spec_from_data(result.provenance.spec)
    if (
        not isinstance(spec, JsonCompareSpec)
        or spec_to_data(spec) != result.provenance.spec
    ):
        raise SerializationError("schema-v3 JSON spec must be normalized exactly")
    if (
        result.fidelity is not Fidelity.FULL
        or result.artifacts
        or result.provenance.comparator_id != "json"
        or result.provenance.algorithm_id != "json.semantic.tree.v1"
        or not isinstance(result.provenance, ComparisonProvenanceV2)
        or result.provenance.provider is not None
        or result.provenance.detector_provider is not None
    ):
        raise SerializationError("schema-v3 JSON result has incompatible identity")
    expected_transformations: list[tuple[str, str, JsonObject]] = []
    if any(
        item.source_kind is not SourceKind.TEXT for item in result.provenance.inputs
    ):
        expected_transformations.append(
            ("decoding", "json.decode.utf8", {"encoding": spec.encoding.value})
        )
    expected_transformations.extend(
        (
            ("normalizing", "json.object_order.ignore", {}),
            ("normalizing", f"json.number.{spec.number_mode.value}", {}),
            (
                "aligning",
                "json.pointer.position",
                {"pointer": "rfc6901", "sequences": "positional"},
            ),
        )
    )
    actual_transformations = [
        (item.stage, item.transformation_id, item.parameters)
        for item in result.provenance.transformations
    ]
    if actual_transformations != expected_transformations:
        raise SerializationError("schema-v3 JSON transformations are not canonical")
    if any(not isinstance(item, StructuredChange) for item in result.changes.items):
        raise SerializationError("schema-v3 JSON changes must be structured changes")
    for change in result.changes.items:
        if not isinstance(change, StructuredChange):
            raise RuntimeError("structured change narrowing failed")
        for fact, digest in (
            (change.before_fact, change.before_digest),
            (change.after_fact, change.after_digest),
        ):
            if spec.detail_mode is StructuredDetailMode.DIGEST_ONLY:
                if fact is not None:
                    raise SerializationError("digest_only JSON changes must omit facts")
                continue
            if fact is None:
                continue
            if isinstance(fact, ScalarFact):
                if fact.kind not in ("null", "boolean", "integer", "decimal", "string"):
                    raise SerializationError(
                        "JSON change contains a non-JSON scalar fact"
                    )
                if fact.kind in ("integer", "decimal"):
                    if (spec.number_mode is JsonNumberMode.LEXICAL) != (
                        fact.lexical is not None
                    ):
                        raise SerializationError(
                            "JSON number fact has invalid lexical detail"
                        )
                elif fact.lexical is not None:
                    raise SerializationError("non-number JSON fact has lexical detail")
                if (
                    fact.kind == "string"
                    and isinstance(fact.value, str)
                    and len(fact.value.encode("utf-8")) > spec.limits.max_scalar_bytes
                ):
                    raise SerializationError("JSON string fact exceeds its spec limit")
                if digest is None or _scalar_fact_digest(fact, spec) != digest:
                    raise SerializationError(
                        "JSON scalar fact does not match its evidence digest"
                    )
            elif fact.descendant_count >= spec.limits.max_nodes:
                raise SerializationError("JSON subtree fact exceeds its node limit")
        if spec.detail_mode is StructuredDetailMode.VALUES:
            if change.before_type is not None and change.before_fact is None:
                raise SerializationError("values JSON change is missing a before fact")
            if change.after_type is not None and change.after_fact is None:
                raise SerializationError("values JSON change is missing an after fact")
        for token in change.path.split("/")[1:]:
            decoded_token = token.replace("~1", "/").replace("~0", "~")
            if len(decoded_token.encode("utf-8")) > spec.limits.max_scalar_bytes:
                raise SerializationError("JSON Pointer token exceeds its spec limit")
    metrics = {item.name: item for item in result.metrics}
    if set(metrics) != {
        "json.compared_values",
        "json.equal_values",
        "json.changed_values",
    }:
        raise SerializationError("schema-v3 JSON metrics are not canonical")
    compared = _finite_count(metrics["json.compared_values"], "compared values")
    equal = _finite_count(metrics["json.equal_values"], "equal values")
    changed = _finite_count(metrics["json.changed_values"], "changed values")
    if equal + changed != compared or result.changes.total_count != changed:
        raise SerializationError("schema-v3 JSON count identities do not hold")
    expected_metrics = {
        "json.compared_values": (MetricDirection.NEUTRAL, compared),
        "json.equal_values": (MetricDirection.NEUTRAL, equal),
        "json.changed_values": (MetricDirection.LOWER_IS_BETTER, changed),
    }
    if any(
        metric.unit != "items"
        or metric.aggregation != "count"
        or metric.direction is not expected_metrics[name][0]
        for name, metric in metrics.items()
    ):
        raise SerializationError("schema-v3 JSON metric metadata is not canonical")
    summary = {item.name: item for item in result.summary.counts}
    expected_summary = {
        "compared_values": compared,
        "equal_values": equal,
        "changed_values": changed,
    }
    if set(summary) != set(expected_summary) or any(
        summary[name].value != count or summary[name].unit != "values"
        for name, count in expected_summary.items()
    ):
        raise SerializationError("schema-v3 JSON summary is not canonical")
    if result.changes.completeness is ChangeCompleteness.PARTIAL:
        raise SerializationError("schema-v3 JSON changes must not be partial")
    if result.relation is (Relation.EQUAL if changed == 0 else Relation.DIFFERENT):
        expected_verdict = Verdict.PASS if changed == 0 else Verdict.FAIL
    else:
        raise SerializationError("schema-v3 JSON relation disagrees with its counts")
    if result.verdict is not expected_verdict or len(result.evaluations) != 1:
        raise SerializationError("schema-v3 JSON verdict is not canonical")
    evaluation = result.evaluations[0]
    if (
        evaluation.rule_id != "json.semantic_equality"
        or evaluation.metric_name != "json.changed_values"
        or evaluation.operator != "eq"
        or not isinstance(evaluation.threshold, FiniteValue)
        or evaluation.threshold.value != 0
        or not isinstance(evaluation.observed, FiniteValue)
        or evaluation.observed.value != changed
        or evaluation.verdict is not expected_verdict
    ):
        raise SerializationError("schema-v3 JSON evaluation is not canonical")
    expected_resources = {
        "before_input_bytes": spec.limits.max_input_bytes,
        "before_scalar_bytes": spec.limits.max_scalar_bytes,
        "before_depth": spec.limits.max_depth,
        "before_nodes": spec.limits.max_nodes,
        "before_number_digits": spec.limits.max_number_digits,
        "before_abs_exponent": spec.limits.max_abs_exponent,
        "after_input_bytes": spec.limits.max_input_bytes,
        "after_scalar_bytes": spec.limits.max_scalar_bytes,
        "after_depth": spec.limits.max_depth,
        "after_nodes": spec.limits.max_nodes,
        "after_number_digits": spec.limits.max_number_digits,
        "after_abs_exponent": spec.limits.max_abs_exponent,
        "compare_work": spec.limits.max_compare_work,
        "change_items": spec.limits.max_change_items,
        "change_payload_bytes": spec.limits.max_change_payload_bytes,
    }
    resources = {item.name: item for item in result.provenance.resources}
    if set(resources) != set(expected_resources) or any(
        resources[name].limit != limit or resources[name].used > limit
        for name, limit in expected_resources.items()
    ):
        raise SerializationError("schema-v3 JSON resources are not canonical")
    if (
        resources["before_input_bytes"].used != result.provenance.inputs[0].size_bytes
        or resources["after_input_bytes"].used != result.provenance.inputs[1].size_bytes
        or resources["change_items"].used != result.changes.returned_count
        or resources["change_payload_bytes"].used
        != sum(serialized_change_size(item) for item in result.changes.items)
    ):
        raise SerializationError("schema-v3 JSON resource actuals are inconsistent")
    if result.changes.completeness is ChangeCompleteness.TRUNCATED:
        if result.changes.limit_reason == "change_items":
            valid_truncation = (
                result.changes.limit == spec.limits.max_change_items
                and result.changes.returned_count == spec.limits.max_change_items
            )
        elif result.changes.limit_reason == "change_payload_bytes":
            valid_truncation = (
                result.changes.limit == spec.limits.max_change_payload_bytes
                and result.changes.returned_count < spec.limits.max_change_items
            )
        else:
            valid_truncation = False
        if not valid_truncation:
            raise SerializationError(
                "schema-v3 JSON truncation evidence is inconsistent"
            )


def outcome_to_data(outcome: AnyCompareOutcome) -> JsonObject:
    """Convert an outcome to stable JSON-safe schema-v1, v2, or v3 data."""
    _validate_outcome_schema_for_encoding(outcome)
    common: JsonObject = {
        "schema_version": outcome.schema_version,
        "kind": outcome.kind,
        "execution": _execution_to_data(outcome.execution),
    }
    if isinstance(outcome, (CompletedOutcome, CompletedOutcomeV2, CompletedOutcomeV3)):
        common["result"] = _result_to_data(outcome.result)
    else:
        common["problem"] = _problem_to_data(outcome.problem)
    return common


def _validate_outcome_schema_for_encoding(outcome: AnyCompareOutcome) -> None:
    if type(outcome) is CompletedOutcome:
        if (
            type(outcome.execution) is not ExecutionRecord
            or type(outcome.result.provenance) is not ComparisonProvenance
        ):
            raise SerializationError("schema-v1 outcome contains schema-v2 values")
    elif type(outcome) is UnavailableOutcome:
        if (
            type(outcome.execution) is not ExecutionRecord
            or type(outcome.problem) is not CapabilityProblem
        ):
            raise SerializationError("schema-v1 outcome contains schema-v2 values")
    elif type(outcome) is FailedOutcome:
        if (
            type(outcome.execution) is not ExecutionRecord
            or type(outcome.problem) is not ExecutionProblem
        ):
            raise SerializationError("schema-v1 outcome contains schema-v2 values")
    elif type(outcome) is CompletedOutcomeV2:
        if (
            type(outcome.execution) is not ExecutionRecordV2
            or type(outcome.result.provenance) is not ComparisonProvenanceV2
        ):
            raise SerializationError("schema-v2 outcome contains schema-v1 values")
    elif type(outcome) is UnavailableOutcomeV2:
        if (
            type(outcome.execution) is not ExecutionRecordV2
            or type(outcome.problem) is not CapabilityProblemV2
        ):
            raise SerializationError("schema-v2 outcome contains schema-v1 values")
    elif type(outcome) is FailedOutcomeV2:
        if (
            type(outcome.execution) is not ExecutionRecordV2
            or type(outcome.problem) is not ExecutionProblemV2
        ):
            raise SerializationError("schema-v2 outcome contains schema-v1 values")
    elif type(outcome) is CompletedOutcomeV3:
        if (
            type(outcome.execution) is not ExecutionRecordV2
            or type(outcome.result.provenance) is not ComparisonProvenanceV2
        ):
            raise SerializationError("schema-v3 outcome contains incompatible values")
        _validate_v3_result(outcome.result)
        _validate_v3_contract_attempt(outcome.execution, outcome.result)
    elif type(outcome) is UnavailableOutcomeV3:
        if (
            type(outcome.execution) is not ExecutionRecordV2
            or type(outcome.problem) is not CapabilityProblemV2
        ):
            raise SerializationError("schema-v3 outcome contains incompatible values")
    elif type(outcome) is FailedOutcomeV3:
        if (
            type(outcome.execution) is not ExecutionRecordV2
            or type(outcome.problem) is not ExecutionProblemV2
        ):
            raise SerializationError("schema-v3 outcome contains incompatible values")
    else:
        raise SerializationError("unknown outcome type")


def outcome_from_data(value: JsonValue) -> AnyCompareOutcome:
    """Validate generic JSON data and construct a schema-v1, v2, or v3 outcome."""
    data = _object(value, "outcome")
    schema_version = _integer(_required(data, "schema_version"), "schema_version")
    if schema_version not in (SCHEMA_VERSION, SCHEMA_VERSION_V2, SCHEMA_VERSION_V3):
        raise SerializationError(f"unknown schema version: {schema_version}")
    schema: Literal[1, 2, 3] = schema_version
    kind = _string(_required(data, "kind"), "outcome kind")
    if kind == "completed" and "problem" in data:
        raise SerializationError("completed outcome has an incompatible field: problem")
    if kind in ("failed", "unavailable") and "result" in data:
        raise SerializationError(f"{kind} outcome has an incompatible field: result")
    execution = _execution_from_data(
        _required(data, "execution"), schema_version=schema
    )
    try:
        if kind == "completed":
            if schema == 3:
                if not isinstance(execution, ExecutionRecordV2):
                    raise SerializationError("schema-v3 execution has the wrong type")
                completed_v3 = CompletedOutcomeV3(
                    execution=execution,
                    result=_result_from_data(
                        _required(data, "result"), schema_version=3
                    ),
                )
                _validate_v3_contract_attempt(
                    completed_v3.execution, completed_v3.result
                )
                return completed_v3
            if schema == 2:
                if not isinstance(execution, ExecutionRecordV2):
                    raise SerializationError("schema-v2 execution has the wrong type")
                return CompletedOutcomeV2(
                    execution=execution,
                    result=_result_from_data(
                        _required(data, "result"), schema_version=2
                    ),
                )
            return CompletedOutcome(
                execution=execution,
                result=_result_from_data(_required(data, "result")),
            )
        if kind == "unavailable":
            problem = _problem_from_data(
                _required(data, "problem"),
                unavailable=True,
                schema_version=schema,
            )
            if schema == 3:
                if not isinstance(execution, ExecutionRecordV2) or not isinstance(
                    problem, CapabilityProblemV2
                ):
                    raise SerializationError("schema-v3 unavailable types are invalid")
                return UnavailableOutcomeV3(execution=execution, problem=problem)
            if schema == 2:
                if not isinstance(execution, ExecutionRecordV2) or not isinstance(
                    problem, CapabilityProblemV2
                ):
                    raise SerializationError("schema-v2 unavailable types are invalid")
                return UnavailableOutcomeV2(execution=execution, problem=problem)
            if not isinstance(problem, CapabilityProblem):
                raise SerializationError("unavailable problem has the wrong type")
            return UnavailableOutcome(execution=execution, problem=problem)
        if kind == "failed":
            problem = _problem_from_data(
                _required(data, "problem"),
                unavailable=False,
                schema_version=schema,
            )
            if schema == 3:
                if not isinstance(execution, ExecutionRecordV2) or not isinstance(
                    problem, ExecutionProblemV2
                ):
                    raise SerializationError("schema-v3 failed types are invalid")
                return FailedOutcomeV3(execution=execution, problem=problem)
            if schema == 2:
                if not isinstance(execution, ExecutionRecordV2) or not isinstance(
                    problem, ExecutionProblemV2
                ):
                    raise SerializationError("schema-v2 failed types are invalid")
                return FailedOutcomeV2(execution=execution, problem=problem)
            if not isinstance(problem, ExecutionProblem):
                raise SerializationError("failed problem has the wrong type")
            return FailedOutcome(execution=execution, problem=problem)
    except ValueError as error:
        raise SerializationError(str(error)) from error
    raise SerializationError(f"unknown outcome kind: {kind}")


def dumps_outcome(outcome: AnyCompareOutcome, *, pretty: bool = False) -> str:
    """Serialize one outcome as strict UTF-8-compatible JSON text."""
    data = _coerce_json(outcome_to_data(outcome))
    contract_kind: object = None
    if isinstance(outcome, CompletedOutcomeV3):
        contract_kind = outcome.result.provenance.spec.get("kind")
    if contract_kind in ("yaml", "table", "array"):
        data = _ordered_schema_v3_contract_data(data)
    return json.dumps(
        data,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=contract_kind not in ("yaml", "table", "array"),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    )


def _ordered_schema_v3_contract_data(
    value: JsonValue, path: tuple[str, ...] = ()
) -> JsonValue:
    """Sort legacy objects while preserving RFC-ordered new contract objects."""
    if isinstance(value, list):
        return [_ordered_schema_v3_contract_data(item, (*path, "[]")) for item in value]
    if not isinstance(value, dict):
        return value
    kind = value.get("kind")
    in_contract_spec = path[:3] == ("result", "provenance", "spec")
    in_contract_change = path[:4] == ("result", "changes", "items", "[]")
    preserve_spec = path == ("result", "provenance", "spec") and kind in (
        "yaml",
        "table",
        "array",
    )
    preserve_spec_component = in_contract_spec and (
        path[-1] in ("limits", "numeric") or path[-2:] == ("columns", "[]")
    )
    preserve_change = in_contract_change and (
        path == ("result", "changes", "items", "[]")
        or path[-1]
        in (
            "before_fact",
            "after_fact",
            "absolute_error",
            "relative_error",
        )
        or "cells" in path
        or "key" in path
    )
    keys = (
        tuple(value)
        if preserve_spec or preserve_spec_component or preserve_change
        else tuple(sorted(value))
    )
    return {
        key: _ordered_schema_v3_contract_data(value[key], (*path, key)) for key in keys
    }


def loads_outcome(payload: str) -> AnyCompareOutcome:
    """Parse untrusted JSON and construct a validated outcome."""
    try:
        raw: object = json.loads(
            payload,
            parse_constant=_reject_constant,
            object_pairs_hook=_unique_object,
        )
    except _DuplicateKeyError:
        raise
    except (ValueError, UnicodeError) as error:
        raise SerializationError("invalid JSON") from error
    return outcome_from_data(_coerce_json(raw))


def upgrade_outcome_v1_to_v2(outcome: CompareOutcome) -> CompareOutcomeV2:
    """Preserve schema-v1 meaning while adding an empty schema-v2 host context."""
    attempts: tuple[CapabilityAttemptV2, ...] = tuple(
        CapabilityAttemptV2(
            attempt.capability_id,
            attempt.backend_id,
            attempt.disposition,
            attempt.reason_code,
        )
        for attempt in outcome.execution.attempts
    )

    def execution_with(
        upgraded_attempts: tuple[CapabilityAttemptV2, ...],
    ) -> ExecutionRecordV2:
        return ExecutionRecordV2(
            started_at=outcome.execution.started_at,
            finished_at=outcome.execution.finished_at,
            duration_ns=outcome.execution.duration_ns,
            stages=outcome.execution.stages,
            attempts=upgraded_attempts,
            diagnostics=outcome.execution.diagnostics,
            last_completed_stage=outcome.execution.last_completed_stage,
            detection=outcome.execution.detection,
            plugin_host=PluginHostExecutionRecord((), ()),
        )

    if isinstance(outcome, CompletedOutcome):
        provenance = outcome.result.provenance
        matching = tuple(
            index
            for index, attempt in enumerate(attempts)
            if attempt.disposition == "selected"
            and attempt.capability_id == provenance.comparator_id
        )
        if not matching:
            attempts = (
                *attempts,
                CapabilityAttemptV2(
                    provenance.comparator_id,
                    None,
                    "selected",
                    capability_version=provenance.comparator_version,
                ),
            )
        elif len(matching) == 1:
            index = matching[0]
            existing = attempts[index]
            attempts = (
                *attempts[:index],
                CapabilityAttemptV2(
                    existing.capability_id,
                    existing.backend_id,
                    existing.disposition,
                    existing.reason_code,
                    existing.capability_version or provenance.comparator_version,
                    existing.backend_version,
                    existing.provider,
                ),
                *attempts[index + 1 :],
            )
        execution = execution_with(attempts)
        result = DiffResult(
            relation=outcome.result.relation,
            verdict=outcome.result.verdict,
            fidelity=outcome.result.fidelity,
            summary=outcome.result.summary,
            changes=outcome.result.changes,
            metrics=outcome.result.metrics,
            evaluations=outcome.result.evaluations,
            artifacts=outcome.result.artifacts,
            provenance=ComparisonProvenanceV2(
                inputs=provenance.inputs,
                spec=provenance.spec,
                transformations=provenance.transformations,
                comparator_id=provenance.comparator_id,
                comparator_version=provenance.comparator_version,
                algorithm_id=provenance.algorithm_id,
                implementation_version=provenance.implementation_version,
                seeds=provenance.seeds,
                resources=provenance.resources,
            ),
        )
        return CompletedOutcomeV2(execution=execution, result=result)
    execution = execution_with(attempts)
    if isinstance(outcome, UnavailableOutcome):
        problem = outcome.problem
        return UnavailableOutcomeV2(
            execution=execution,
            problem=CapabilityProblemV2(
                problem.code,
                problem.status_code,
                problem.stage,
                problem.message,
                problem.details,
                problem.retryable,
            ),
        )
    failed_problem = outcome.problem
    return FailedOutcomeV2(
        execution=execution,
        problem=ExecutionProblemV2(
            failed_problem.code,
            failed_problem.status_code,
            failed_problem.stage,
            failed_problem.message,
            failed_problem.details,
            failed_problem.retryable,
        ),
    )


def upgrade_outcome_v2_to_v3(outcome: CompareOutcomeV2) -> CompareOutcomeV3:
    """Wrap a validated schema-v2 outcome in the additive schema-v3 envelope."""
    if isinstance(outcome, CompletedOutcomeV2):
        return CompletedOutcomeV3(execution=outcome.execution, result=outcome.result)
    if isinstance(outcome, UnavailableOutcomeV2):
        return UnavailableOutcomeV3(
            execution=outcome.execution, problem=outcome.problem
        )
    return FailedOutcomeV3(execution=outcome.execution, problem=outcome.problem)


def upgrade_outcome_v1_to_v3(outcome: CompareOutcome) -> CompareOutcomeV3:
    """Preserve schema-v1 meaning while adding neutral v2/v3 fields."""
    return upgrade_outcome_v2_to_v3(upgrade_outcome_v1_to_v2(outcome))


def downgrade_outcome_v3_to_v2(outcome: CompareOutcomeV3) -> CompareOutcomeV2:
    """Losslessly remove only the envelope version from a legacy-only v3 outcome."""
    _validate_outcome_schema_for_encoding(outcome)
    if isinstance(outcome, CompletedOutcomeV3):
        spec_kind = outcome.result.provenance.spec.get("kind")
        if spec_kind not in ("auto", "text", "binary") or any(
            isinstance(change, (StructuredChange, TableChange, ArrayChange))
            for change in outcome.result.changes.items
        ):
            raise SerializationError("schema-v3 outcome is not legacy-only")
        return CompletedOutcomeV2(execution=outcome.execution, result=outcome.result)
    if isinstance(outcome, UnavailableOutcomeV3):
        if outcome.execution.plugin_host is None:
            raise SerializationError("schema-v3 outcome cannot be proven legacy-only")
        return UnavailableOutcomeV2(
            execution=outcome.execution, problem=outcome.problem
        )
    if outcome.execution.plugin_host is None:
        raise SerializationError("schema-v3 outcome cannot be proven legacy-only")
    return FailedOutcomeV2(execution=outcome.execution, problem=outcome.problem)
