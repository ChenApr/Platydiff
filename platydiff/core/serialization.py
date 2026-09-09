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
    TextCompareSpec,
    TextEncoding,
    TextHunk,
    TransformationRecord,
    UnavailableOutcome,
    UnavailableOutcomeV2,
    UnavailableOutcomeV3,
    Verdict,
)


class SerializationError(ValueError):
    """Untrusted JSON does not satisfy schema v1."""


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
    if kind not in ("text", "binary", "auto", "json"):
        raise SerializationError(f"unknown spec kind: {kind}")
    limits_data = _object(_required(data, "limits"), "spec.limits")
    try:
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


def _numeric_to_data(value: NumericValue) -> JsonObject:
    if isinstance(value, FiniteValue):
        return {"kind": value.kind, "value": value.value}
    return {"kind": value.kind}


def _numeric_from_data(value: JsonValue) -> NumericValue:
    data = _object(value, "numeric value")
    kind = _string(_required(data, "kind"), "numeric kind")
    if kind == "finite":
        raw = _required(data, "value")
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise SerializationError("finite numeric value must be a number")
        try:
            return FiniteValue(raw)
        except ValueError as error:
            raise SerializationError(str(error)) from error
    if kind == "nan":
        return NaNValue()
    if kind == "positive_infinity":
        return PositiveInfinityValue()
    if kind == "negative_infinity":
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


def _change_from_data(
    value: JsonValue, *, schema_version: Literal[1, 2, 3] = 1
) -> TextHunk | BinarySpan | StructuredChange | ExtensionChange:
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
                value=_numeric_from_data(_required(item, "value")),
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
                    else _numeric_from_data(threshold_value)
                ),
                observed=(
                    None
                    if observed_value is None
                    else _numeric_from_data(observed_value)
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
            _validate_v3_result(result)
        return result
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _finite_count(metric: Metric, name: str) -> int:
    if not isinstance(metric.value, FiniteValue) or not metric.value.value.is_integer():
        raise SerializationError(f"{name} must be a finite integer count")
    return int(metric.value.value)


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


def _validate_v3_result(result: DiffResult) -> None:
    kind = result.provenance.spec.get("kind")
    if kind in ("auto", "text", "binary"):
        if any(isinstance(item, StructuredChange) for item in result.changes.items):
            raise SerializationError("legacy schema-v3 result has structured changes")
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
                return CompletedOutcomeV3(
                    execution=execution,
                    result=_result_from_data(
                        _required(data, "result"), schema_version=3
                    ),
                )
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
    return json.dumps(
        data,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    )


def loads_outcome(payload: str) -> AnyCompareOutcome:
    """Parse untrusted JSON and construct a validated outcome."""
    try:
        raw: object = json.loads(payload, parse_constant=_reject_constant)
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
    if isinstance(outcome, CompletedOutcomeV3):
        spec_kind = outcome.result.provenance.spec.get("kind")
        if spec_kind not in ("auto", "text", "binary") or any(
            isinstance(change, StructuredChange)
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
