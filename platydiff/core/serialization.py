"""Validated schema-v1 JSON serialization."""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from typing import Literal, cast

from platydiff.core.models import (
    SCHEMA_VERSION,
    ArtifactRef,
    CapabilityAttempt,
    CapabilityProblem,
    Change,
    ChangeCompleteness,
    ChangeSelection,
    ChangeSet,
    CompareOutcome,
    ComparisonProvenance,
    CompletedOutcome,
    Diagnostic,
    DiagnosticSeverity,
    DiffResult,
    DiffSummary,
    ExecutionProblem,
    ExecutionRecord,
    ExtensionChange,
    FailedOutcome,
    Fidelity,
    FiniteValue,
    HunkLine,
    InputProvenance,
    JsonObject,
    JsonValue,
    Metric,
    MetricDirection,
    NaNValue,
    NegativeInfinityValue,
    NewlinePolicy,
    NumericValue,
    PipelineStage,
    PolicyEvaluation,
    PositiveInfinityValue,
    Relation,
    ResourceLimits,
    ResourceUsage,
    SourceKind,
    StageDisposition,
    StageRecord,
    SummaryCount,
    TextCompareSpec,
    TextEncoding,
    TextHunk,
    TransformationRecord,
    UnavailableOutcome,
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


def spec_to_data(spec: TextCompareSpec) -> JsonObject:
    """Serialize a normalized Phase 1 specification."""
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


def spec_from_data(value: JsonValue) -> TextCompareSpec:
    """Validate generic JSON data and construct a specification."""
    data = _object(value, "spec")
    kind = _string(_required(data, "kind"), "spec.kind")
    if kind != "text":
        raise SerializationError(f"unknown spec kind: {kind}")
    limits_data = _object(_required(data, "limits"), "spec.limits")
    try:
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
        return FiniteValue(float(raw))
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


def _execution_to_data(record: ExecutionRecord) -> JsonObject:
    return {
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


def _execution_from_data(value: JsonValue) -> ExecutionRecord:
    data = _object(value, "execution")
    attempts: list[CapabilityAttempt] = []
    for value_item in _array(_required(data, "attempts"), "attempts"):
        item = _object(value_item, "capability attempt")
        disposition = _string(_required(item, "disposition"), "disposition")
        if disposition not in ("selected", "rejected", "fallback"):
            raise SerializationError("unknown capability attempt disposition")
        attempts.append(
            CapabilityAttempt(
                capability_id=_string(
                    _required(item, "capability_id"), "capability_id"
                ),
                backend_id=_optional_string(
                    _required(item, "backend_id"), "backend_id"
                ),
                disposition=cast(
                    Literal["selected", "rejected", "fallback"], disposition
                ),
                reason_code=_optional_string(
                    _required(item, "reason_code"), "reason_code"
                ),
            )
        )
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
    try:
        return ExecutionRecord(
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
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def _problem_to_data(problem: ExecutionProblem | CapabilityProblem) -> JsonObject:
    return {
        "code": problem.code,
        "status_code": problem.status_code,
        "stage": problem.stage.value,
        "message": problem.message,
        "details": problem.details,
        "retryable": problem.retryable,
    }


def _problem_from_data(
    value: JsonValue, *, unavailable: bool
) -> ExecutionProblem | CapabilityProblem:
    data = _object(value, "problem")
    code = _string(_required(data, "code"), "problem code")
    status_code = _integer(_required(data, "status_code"), "status_code")
    stage = _enum_value(PipelineStage, _required(data, "stage"), "stage")
    message = _string(_required(data, "message"), "message")
    details = _object(_required(data, "details"), "problem details")
    retryable = _boolean(_required(data, "retryable"), "retryable")
    try:
        if unavailable:
            return CapabilityProblem(
                code=code,
                status_code=status_code,
                stage=stage,
                message=message,
                details=details,
                retryable=retryable,
            )
        return ExecutionProblem(
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
    return {
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


def _provenance_from_data(value: JsonValue) -> ComparisonProvenance:
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
        return ComparisonProvenance(
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


def _change_from_data(value: JsonValue) -> TextHunk | ExtensionChange:
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


def _result_from_data(value: JsonValue) -> DiffResult:
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
        _change_from_data(item)
        for item in _array(_required(changes_data, "items"), "change items")
    )
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
        )
        return DiffResult(
            relation=_enum_value(Relation, _required(data, "relation"), "relation"),
            verdict=_enum_value(Verdict, _required(data, "verdict"), "verdict"),
            fidelity=_enum_value(Fidelity, _required(data, "fidelity"), "fidelity"),
            summary=summary,
            changes=change_set,
            metrics=tuple(metrics),
            evaluations=tuple(evaluations),
            artifacts=tuple(artifacts),
            provenance=_provenance_from_data(_required(data, "provenance")),
        )
    except ValueError as error:
        raise SerializationError(str(error)) from error


def outcome_to_data(outcome: CompareOutcome) -> JsonObject:
    """Convert an outcome to stable JSON-safe schema-v1 data."""
    common: JsonObject = {
        "schema_version": outcome.schema_version,
        "kind": outcome.kind,
        "execution": _execution_to_data(outcome.execution),
    }
    if isinstance(outcome, CompletedOutcome):
        common["result"] = _result_to_data(outcome.result)
    else:
        common["problem"] = _problem_to_data(outcome.problem)
    return common


def outcome_from_data(value: JsonValue) -> CompareOutcome:
    """Validate generic JSON data and construct a schema-v1 outcome."""
    data = _object(value, "outcome")
    schema_version = _integer(_required(data, "schema_version"), "schema_version")
    if schema_version != SCHEMA_VERSION:
        raise SerializationError(f"unknown schema version: {schema_version}")
    kind = _string(_required(data, "kind"), "outcome kind")
    execution = _execution_from_data(_required(data, "execution"))
    try:
        if kind == "completed":
            return CompletedOutcome(
                execution=execution,
                result=_result_from_data(_required(data, "result")),
            )
        if kind == "unavailable":
            problem = _problem_from_data(_required(data, "problem"), unavailable=True)
            if not isinstance(problem, CapabilityProblem):
                raise SerializationError("unavailable problem has the wrong type")
            return UnavailableOutcome(execution=execution, problem=problem)
        if kind == "failed":
            problem = _problem_from_data(_required(data, "problem"), unavailable=False)
            if not isinstance(problem, ExecutionProblem):
                raise SerializationError("failed problem has the wrong type")
            return FailedOutcome(execution=execution, problem=problem)
    except ValueError as error:
        raise SerializationError(str(error)) from error
    raise SerializationError(f"unknown outcome kind: {kind}")


def dumps_outcome(outcome: CompareOutcome, *, pretty: bool = False) -> str:
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


def loads_outcome(payload: str) -> CompareOutcome:
    """Parse untrusted JSON and construct a validated outcome."""
    try:
        raw: object = json.loads(payload, parse_constant=_reject_constant)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise SerializationError("invalid JSON") from error
    return outcome_from_data(_coerce_json(raw))
