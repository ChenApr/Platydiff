"""Compatibility and invariant tests for schema v1."""

from __future__ import annotations

import math
from typing import cast

import pytest

from platydiff.core.models import (
    ArtifactRef,
    CapabilityProblem,
    ChangeCompleteness,
    ChangeSelection,
    ChangeSet,
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
    Metric,
    MetricDirection,
    NaNValue,
    NegativeInfinityValue,
    PipelineStage,
    PolicyEvaluation,
    PositiveInfinityValue,
    Relation,
    ResourceUsage,
    SourceKind,
    StageDisposition,
    StageRecord,
    SummaryCount,
    TextCompareSpec,
    TextHunk,
    UnavailableOutcome,
    Verdict,
)
from platydiff.core.serialization import (
    SerializationError,
    dumps_outcome,
    loads_outcome,
    outcome_from_data,
    outcome_to_data,
    spec_from_data,
    spec_to_data,
)

STAMP = "2026-09-06T00:00:00Z"
ZERO_SHA = "0" * 64


def stage(
    name: PipelineStage, disposition: StageDisposition = StageDisposition.COMPLETED
) -> StageRecord:
    return StageRecord(name, STAMP, STAMP, 0, disposition)


def completed_execution(*, diagnostics: tuple[Diagnostic, ...] = ()) -> ExecutionRecord:
    stages = tuple(
        stage(name) for name in PipelineStage if name is not PipelineStage.DETECTING
    )
    return ExecutionRecord(
        STAMP,
        STAMP,
        0,
        stages,
        diagnostics=diagnostics,
        last_completed_stage=PipelineStage.AGGREGATING,
    )


def provenance() -> ComparisonProvenance:
    return ComparisonProvenance(
        inputs=(
            InputProvenance("before", SourceKind.TEXT, 1, ZERO_SHA, "before"),
            InputProvenance("after", SourceKind.TEXT, 1, ZERO_SHA, "after"),
        ),
        spec=spec_to_data(TextCompareSpec()),
        transformations=(),
        comparator_id="text",
        comparator_version="1",
        algorithm_id="text.myers.linear_space.v1",
        implementation_version="1",
        resources=(ResourceUsage("myers_work", 10, 1),),
    )


def complete_changes() -> ChangeSet:
    hunk = TextHunk(
        before_start_line=1,
        before_line_count=1,
        after_start_line=1,
        after_line_count=1,
        lines=(
            HunkLine("delete", "a", "\n", 1, None),
            HunkLine("insert", "b", "\n", None, 1),
        ),
    )
    return ChangeSet(
        ChangeCompleteness.COMPLETE,
        (hunk,),
        1,
        1,
        0,
        ChangeSelection.ALL,
        None,
    )


def result(
    *,
    verdict: Verdict = Verdict.FAIL,
    fidelity: Fidelity = Fidelity.FULL,
    evaluations: tuple[PolicyEvaluation, ...] | None = None,
) -> DiffResult:
    selected_evaluations = evaluations or (
        PolicyEvaluation("strict_equality", verdict),
    )
    return DiffResult(
        relation=Relation.DIFFERENT,
        verdict=verdict,
        fidelity=fidelity,
        summary=DiffSummary(1, (SummaryCount("changed_hunks", 1, "hunks"),)),
        changes=complete_changes(),
        metrics=(
            Metric(
                "edit_distance",
                FiniteValue(2.0),
                "operations",
                MetricDirection.LOWER_IS_BETTER,
            ),
        ),
        evaluations=selected_evaluations,
        artifacts=(),
        provenance=provenance(),
    )


def completed_outcome(
    *,
    verdict: Verdict = Verdict.FAIL,
    fidelity: Fidelity = Fidelity.FULL,
    diagnostics: tuple[Diagnostic, ...] = (),
) -> CompletedOutcome:
    return CompletedOutcome(
        execution=completed_execution(diagnostics=diagnostics),
        result=result(verdict=verdict, fidelity=fidelity),
    )


def test_all_three_outcomes_round_trip() -> None:
    completed = completed_outcome()
    unavailable_execution = ExecutionRecord(
        STAMP,
        STAMP,
        0,
        (
            stage(PipelineStage.VALIDATING),
            stage(PipelineStage.RESOLVING, StageDisposition.UNAVAILABLE),
        ),
        last_completed_stage=PipelineStage.VALIDATING,
    )
    unavailable = UnavailableOutcome(
        execution=unavailable_execution,
        problem=CapabilityProblem(
            "capability_unavailable",
            501,
            PipelineStage.RESOLVING,
            "No comparator is available.",
        ),
    )
    failed_execution = ExecutionRecord(
        STAMP,
        STAMP,
        0,
        (
            stage(PipelineStage.VALIDATING),
            stage(PipelineStage.SOURCING, StageDisposition.FAILED),
        ),
        last_completed_stage=PipelineStage.VALIDATING,
    )
    failed = FailedOutcome(
        execution=failed_execution,
        problem=ExecutionProblem(
            "source_not_found",
            404,
            PipelineStage.SOURCING,
            "Source was not found.",
        ),
    )
    for outcome in (completed, unavailable, failed):
        assert loads_outcome(dumps_outcome(outcome)) == outcome


def test_spec_round_trip_includes_effective_defaults() -> None:
    spec = TextCompareSpec()
    assert spec_from_data(spec_to_data(spec)) == spec
    assert spec_to_data(spec)["context_lines"] == 3


@pytest.mark.parametrize("schema", [0, 2])
def test_unknown_schema_is_rejected(schema: int) -> None:
    data = outcome_to_data(completed_outcome())
    data["schema_version"] = schema
    with pytest.raises(SerializationError, match="unknown schema version"):
        outcome_from_data(data)


def test_unknown_outcome_kind_is_rejected() -> None:
    data = outcome_to_data(completed_outcome())
    data["kind"] = "cancelled"
    with pytest.raises(SerializationError, match="unknown outcome kind"):
        outcome_from_data(data)


def test_unknown_optional_fields_are_ignored() -> None:
    data = outcome_to_data(completed_outcome())
    data["future_optional"] = {"safe": True}
    assert outcome_from_data(data) == completed_outcome()


def test_extension_change_is_preserved_and_unknown_builtin_is_rejected() -> None:
    extension = ExtensionChange("org.example.region", "example", 1, {"x": 4})
    changes = ChangeSet(
        ChangeCompleteness.COMPLETE,
        (extension,),
        1,
        1,
        0,
        ChangeSelection.ALL,
        None,
    )
    extension_result = DiffResult(
        Relation.DIFFERENT,
        Verdict.FAIL,
        Fidelity.FULL,
        DiffSummary(1, ()),
        changes,
        (),
        (PolicyEvaluation("strict_equality", Verdict.FAIL),),
        (),
        provenance(),
    )
    outcome = CompletedOutcome(execution=completed_execution(), result=extension_result)
    assert loads_outcome(dumps_outcome(outcome)) == outcome

    data = outcome_to_data(outcome)
    result_data = data["result"]
    assert isinstance(result_data, dict)
    change_data = result_data["changes"]
    assert isinstance(change_data, dict)
    items = change_data["items"]
    assert isinstance(items, list)
    item = items[0]
    assert isinstance(item, dict)
    item["kind"] = "future_builtin"
    with pytest.raises(SerializationError, match="unknown built-in change kind"):
        outcome_from_data(data)


@pytest.mark.parametrize(
    "numeric",
    [NaNValue(), PositiveInfinityValue(), NegativeInfinityValue()],
)
def test_non_finite_numeric_values_use_tags(
    numeric: NaNValue | PositiveInfinityValue | NegativeInfinityValue,
) -> None:
    tagged_result = result(
        evaluations=(
            PolicyEvaluation(
                "numeric_rule", Verdict.FAIL, "value", "eq", numeric, numeric
            ),
        )
    )
    outcome = CompletedOutcome(execution=completed_execution(), result=tagged_result)
    payload = dumps_outcome(outcome)
    assert "NaN" not in payload
    assert "Infinity" not in payload
    assert loads_outcome(payload) == outcome


def test_bare_non_finite_json_is_rejected() -> None:
    with pytest.raises(SerializationError, match="non-standard JSON"):
        loads_outcome('{"value": NaN}')
    with pytest.raises(ValueError, match="non-finite"):
        ExtensionChange("org.example.change", "example", 1, {"x": math.inf})


def test_non_json_extension_data_and_surrogates_are_rejected() -> None:
    with pytest.raises(ValueError, match="not JSON-safe"):
        ExtensionChange(
            "org.example.change",
            "example",
            1,
            cast(JsonObject, {"x": object()}),
        )
    with pytest.raises(ValueError, match="Unicode scalar"):
        ExtensionChange("org.example.change", "example", 1, {"x": "\ud800"})
    with pytest.raises(SerializationError, match="Unicode scalar"):
        loads_outcome('{"value":"\\ud800"}')


def test_change_set_invariants() -> None:
    with pytest.raises(ValueError, match="invalid complete"):
        ChangeSet(
            ChangeCompleteness.COMPLETE,
            (),
            1,
            0,
            1,
            ChangeSelection.ALL,
            None,
        )
    truncated = ChangeSet(
        ChangeCompleteness.TRUNCATED,
        (),
        2,
        0,
        2,
        ChangeSelection.SOURCE_ORDER_PREFIX,
        0,
    )
    assert truncated.total_count == 2
    partial = ChangeSet(
        ChangeCompleteness.PARTIAL,
        (),
        None,
        0,
        None,
        ChangeSelection.ALGORITHM_PARTIAL,
        5,
    )
    assert partial.total_count is None


@pytest.mark.parametrize(
    "uri",
    [
        "/absolute/report.txt",
        "../report.txt",
        "a/../../report.txt",
        "a\\b",
        "C:/report.txt",
        "https://example.test/report.txt",
    ],
)
def test_artifact_uri_rejects_unsafe_paths(uri: str) -> None:
    with pytest.raises(ValueError, match="safe relative"):
        ArtifactRef("report", "text_report", "text/plain", uri, ZERO_SHA, 0)


def test_serialization_order_is_stable() -> None:
    unsorted = ComparisonProvenance(
        inputs=provenance().inputs,
        spec=spec_to_data(TextCompareSpec()),
        transformations=(),
        comparator_id="text",
        comparator_version="1",
        algorithm_id="text.myers.linear_space.v1",
        implementation_version="1",
        resources=(ResourceUsage("z_work", 3, 2), ResourceUsage("a_work", 1, 1)),
    )
    ordered_result = DiffResult(
        Relation.DIFFERENT,
        Verdict.FAIL,
        Fidelity.FULL,
        DiffSummary(
            1,
            (
                SummaryCount("z_count", 0, "items"),
                SummaryCount("a_count", 1, "items"),
            ),
        ),
        complete_changes(),
        (
            Metric("z_metric", FiniteValue(), "items", MetricDirection.NEUTRAL),
            Metric("a_metric", FiniteValue(), "items", MetricDirection.NEUTRAL),
        ),
        (
            PolicyEvaluation("z_rule", Verdict.PASS),
            PolicyEvaluation("a_rule", Verdict.FAIL),
        ),
        (),
        unsorted,
    )
    payload = dumps_outcome(
        CompletedOutcome(execution=completed_execution(), result=ordered_result)
    )
    assert payload.index("a_count") < payload.index("z_count")
    assert payload.index("a_metric") < payload.index("z_metric")
    assert payload.index("a_rule") < payload.index("z_rule")
    assert payload.index("a_work") < payload.index("z_work")
    assert payload == dumps_outcome(loads_outcome(payload))


def test_diagnostic_warning_does_not_imply_warn_verdict() -> None:
    diagnostic = Diagnostic(
        "backend_note",
        DiagnosticSeverity.WARNING,
        PipelineStage.COMPARING,
        "A safe warning.",
    )
    outcome = completed_outcome(diagnostics=(diagnostic,))
    assert outcome.result.verdict is Verdict.FAIL


def test_degraded_fidelity_does_not_override_verdict() -> None:
    outcome = completed_outcome(verdict=Verdict.FAIL, fidelity=Fidelity.DEGRADED)
    assert outcome.result.verdict is Verdict.FAIL


def test_invalid_outcome_and_result_states_are_rejected() -> None:
    failed_execution = ExecutionRecord(
        STAMP,
        STAMP,
        0,
        (stage(PipelineStage.VALIDATING, StageDisposition.FAILED),),
    )
    with pytest.raises(ValueError, match="finish aggregation"):
        CompletedOutcome(execution=failed_execution, result=result())
    with pytest.raises(ValueError, match="highest policy"):
        result(
            verdict=Verdict.PASS,
            evaluations=(PolicyEvaluation("strict_equality", Verdict.FAIL),),
        )
