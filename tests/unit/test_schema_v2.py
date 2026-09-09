"""Schema-v2 provider provenance and schema-v1 migration tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import cast

import pytest

from platydiff import (
    AutoCompareSpec,
    BytesSource,
    CompletedOutcome,
    CompletedOutcomeV2,
    FailedOutcome,
    FailedOutcomeV2,
    PluginHost,
    TextCompareSpec,
    TextSource,
    UnavailableOutcome,
    compare,
    upgrade_outcome_v1_to_v2,
)
from platydiff.core.models import (
    CapabilityAttemptV2,
    CapabilityProblem,
    CapabilityProblemV2,
    ComparisonProvenanceV2,
    ExecutionProblem,
    ExecutionProblemV2,
    ExecutionRecord,
    JsonObject,
    PipelineStage,
    StageDisposition,
)
from platydiff.core.serialization import (
    SerializationError,
    dumps_outcome,
    loads_outcome,
    outcome_from_data,
    outcome_to_data,
)
from platydiff.plugin_sdk import (
    CapabilityKind,
    PluginExecutionErrorV1,
    SourceServiceV1,
)
from platydiff.plugins import PluginCatalogV1
from tests.unit.test_contracts import STAMP, completed_outcome, stage
from tests.unit.test_plugin_host_execution import (
    _capability,
    _ComparatorHandle,
    _DetectorHandle,
    _facts,
    _Run,
)


def test_default_compare_remains_schema_v1_while_host_always_returns_v2() -> None:
    direct = compare(TextSource("same"), TextSource("same"), TextCompareSpec())
    host = PluginHost(PluginCatalogV1((), (), (), (), ()))
    hosted = host.compare(TextSource("same"), TextSource("same"), TextCompareSpec())
    assert isinstance(direct, CompletedOutcome)
    assert direct.schema_version == 1
    assert isinstance(hosted, CompletedOutcomeV2)
    assert hosted.schema_version == 2
    assert hosted.execution.plugin_host is not None
    assert hosted.execution.plugin_host.enabled_plugin_ids == ()
    assert isinstance(hosted.result.provenance, ComparisonProvenanceV2)
    assert hosted.result.provenance.provider is None


def test_plugin_host_records_provider_versions_on_attempt_and_provenance() -> None:
    handle = _ComparatorHandle()
    host, _ = _capability(handle, CapabilityKind.COMPARATOR, backend=True)
    outcome = host.compare(
        TextSource("same"),
        TextSource("same"),
        TextCompareSpec(),
        comparator_id=handle.capability_id,
    )
    assert isinstance(outcome, CompletedOutcomeV2)
    assert isinstance(outcome.result.provenance, ComparisonProvenanceV2)
    provider = outcome.result.provenance.provider
    assert provider is not None
    assert provider.plugin_id == "org.example.scidiff"
    assert provider.distribution_name == "example-plugin"
    assert provider.negotiated_api_minor == 1
    selected = outcome.execution.attempts[-1]
    assert isinstance(selected, CapabilityAttemptV2)
    assert selected.capability_version == "1"
    assert selected.backend_version == "1"
    assert selected.provider == provider


def test_builtin_selected_attempt_version_must_match_provenance() -> None:
    host = PluginHost(PluginCatalogV1((), (), (), (), ()))
    outcome = host.compare(TextSource("same"), TextSource("same"), TextCompareSpec())
    assert isinstance(outcome, CompletedOutcomeV2)
    attempts = tuple(
        replace(attempt, capability_version="tampered")
        if isinstance(attempt, CapabilityAttemptV2)
        and attempt.disposition == "selected"
        else attempt
        for attempt in outcome.execution.attempts
    )

    with pytest.raises(ValueError, match="selected comparator version"):
        replace(outcome, execution=replace(outcome.execution, attempts=attempts))


def test_provider_identity_rejects_invalid_distribution_name() -> None:
    handle = _ComparatorHandle()
    host, _ = _capability(handle, CapabilityKind.COMPARATOR, backend=True)
    outcome = host.compare(
        TextSource("same"),
        TextSource("same"),
        TextCompareSpec(),
        comparator_id=handle.capability_id,
    )
    assert isinstance(outcome, CompletedOutcomeV2)
    provider = outcome.result.provenance.provider
    assert provider is not None

    with pytest.raises(ValueError, match="distribution_name"):
        replace(provider, distribution_name="not a dist!")


@pytest.mark.parametrize("field_name", ["capability_version", "backend_version"])
@pytest.mark.parametrize("invalid_version", ["", "bad\nversion", "bad/path", "x" * 1025])
def test_attempt_versions_enforce_sdk_identity_text(
    field_name: str,
    invalid_version: str,
) -> None:
    values = {
        "capability_version": "1",
        "backend_version": "1",
    }
    values[field_name] = invalid_version

    with pytest.raises(ValueError):
        CapabilityAttemptV2(
            "org.example.scidiff.text_exact",
            "org.example.scidiff.stdlib",
            "selected",
            capability_version=values["capability_version"],
            backend_version=values["backend_version"],
        )


@pytest.mark.parametrize(
    ("target", "invalid_value"),
    [
        ("distribution_name", "not a dist!"),
        ("capability_version", "bad\nversion"),
    ],
)
def test_schema_v2_json_rejects_untrusted_provider_identity_text(
    target: str,
    invalid_value: str,
) -> None:
    handle = _ComparatorHandle()
    host, _ = _capability(handle, CapabilityKind.COMPARATOR, backend=True)
    outcome = host.compare(
        TextSource("same"),
        TextSource("same"),
        TextCompareSpec(),
        comparator_id=handle.capability_id,
    )
    assert isinstance(outcome, CompletedOutcomeV2)
    data = deepcopy(outcome_to_data(outcome))
    execution = cast(JsonObject, data["execution"])
    if target == "distribution_name":
        plugin_host = cast(JsonObject, execution["plugin_host"])
        loaded = cast(list[object], plugin_host["loaded_providers"])
        cast(JsonObject, loaded[0])[target] = invalid_value
    else:
        attempts = cast(list[object], execution["attempts"])
        cast(JsonObject, attempts[-1])[target] = invalid_value

    with pytest.raises(SerializationError):
        outcome_from_data(data)


def test_schema_v2_round_trip_is_canonical_and_v1_upgrader_preserves_result() -> None:
    original = compare(BytesSource(b"a"), BytesSource(b"b"), TextCompareSpec())
    upgraded = upgrade_outcome_v1_to_v2(original)
    encoded = dumps_outcome(upgraded)
    decoded = loads_outcome(encoded)
    assert decoded == upgraded
    assert dumps_outcome(decoded) == encoded
    assert outcome_to_data(original)["schema_version"] == 1
    assert outcome_to_data(upgraded)["schema_version"] == 2
    if isinstance(original, CompletedOutcome) and isinstance(
        upgraded, CompletedOutcomeV2
    ):
        assert upgraded.result.relation is original.result.relation
        assert upgraded.result.verdict is original.result.verdict


def _v1_terminal_outcomes() -> tuple[
    CompletedOutcome, UnavailableOutcome, FailedOutcome
]:
    unavailable_execution = ExecutionRecord(
        STAMP,
        STAMP,
        0,
        (
            stage(PipelineStage.VALIDATING),
            stage(PipelineStage.SOURCING),
            stage(PipelineStage.RESOLVING, StageDisposition.UNAVAILABLE),
        ),
        last_completed_stage=PipelineStage.SOURCING,
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
    return (
        completed_outcome(),
        UnavailableOutcome(
            execution=unavailable_execution,
            problem=CapabilityProblem(
                "capability_unavailable",
                501,
                PipelineStage.RESOLVING,
                "No comparator is available.",
            ),
        ),
        FailedOutcome(
            execution=failed_execution,
            problem=ExecutionProblem(
                "source_not_found",
                404,
                PipelineStage.SOURCING,
                "Source was not found.",
            ),
        ),
    )


def test_schema_v1_models_reject_schema_v2_nested_values() -> None:
    completed, unavailable, failed = _v1_terminal_outcomes()
    upgraded_completed = upgrade_outcome_v1_to_v2(completed)
    upgraded_unavailable = upgrade_outcome_v1_to_v2(unavailable)
    assert isinstance(upgraded_completed, CompletedOutcomeV2)
    with pytest.raises(ValueError, match="schema-v1"):
        replace(completed, result=upgraded_completed.result)
    with pytest.raises(ValueError, match="schema-v1"):
        replace(unavailable, execution=upgraded_unavailable.execution)
    with pytest.raises(ValueError, match="schema-v1"):
        replace(
            unavailable,
            problem=cast(
                CapabilityProblem,
                CapabilityProblemV2(
                    "capability_unavailable",
                    501,
                    PipelineStage.RESOLVING,
                    "No comparator is available.",
                ),
            ),
        )
    with pytest.raises(ValueError, match="schema-v1"):
        replace(
            failed,
            problem=cast(
                ExecutionProblem,
                ExecutionProblemV2(
                    "plugin_execution_failure",
                    502,
                    PipelineStage.SOURCING,
                    "A plugin failed.",
                ),
            ),
        )


def test_all_legal_v1_and_upgraded_v2_outcomes_round_trip_exactly() -> None:
    for outcome in _v1_terminal_outcomes():
        upgraded = upgrade_outcome_v1_to_v2(outcome)
        assert loads_outcome(dumps_outcome(outcome)) == outcome
        assert loads_outcome(dumps_outcome(upgraded)) == upgraded


def _plugin_completed_data() -> JsonObject:
    handle = _ComparatorHandle()
    host, _ = _capability(handle, CapabilityKind.COMPARATOR, backend=True)
    outcome = host.compare(
        TextSource("same"),
        TextSource("same"),
        TextCompareSpec(),
        comparator_id=handle.capability_id,
    )
    assert isinstance(outcome, CompletedOutcomeV2)
    return outcome_to_data(outcome)


def test_schema_v2_rejects_provenance_provider_not_loaded_by_host() -> None:
    data = deepcopy(_plugin_completed_data())
    result = cast(JsonObject, data["result"])
    provenance = cast(JsonObject, result["provenance"])
    provider = cast(JsonObject, provenance["provider"])
    provider["plugin_id"] = "org.other.plugin"
    with pytest.raises(SerializationError, match="provider"):
        outcome_from_data(data)


def test_schema_v2_rejects_external_comparator_with_deleted_provider() -> None:
    data = deepcopy(_plugin_completed_data())
    result = cast(JsonObject, data["result"])
    provenance = cast(JsonObject, result["provenance"])
    provenance["provider"] = None
    execution = cast(JsonObject, data["execution"])
    attempts = cast(list[object], execution["attempts"])
    selected = cast(JsonObject, attempts[-1])
    selected["provider"] = None
    with pytest.raises(SerializationError, match="provider"):
        outcome_from_data(data)


def test_schema_v2_rejects_selected_attempt_that_disagrees_with_result() -> None:
    data = deepcopy(_plugin_completed_data())
    execution = cast(JsonObject, data["execution"])
    attempts = cast(list[object], execution["attempts"])
    selected = cast(JsonObject, attempts[-1])
    selected["capability_id"] = "org.example.scidiff.other_comparator"
    with pytest.raises(SerializationError, match="comparator"):
        outcome_from_data(data)


def test_schema_v2_rejects_builtin_result_that_disagrees_with_attempt() -> None:
    host = PluginHost(PluginCatalogV1((), (), (), (), ()))
    outcome = host.compare(TextSource("same"), TextSource("same"), TextCompareSpec())
    assert isinstance(outcome, CompletedOutcomeV2)
    data = deepcopy(outcome_to_data(outcome))
    result = cast(JsonObject, data["result"])
    provenance = cast(JsonObject, result["provenance"])
    provenance["comparator_id"] = "binary"
    with pytest.raises(SerializationError, match="comparator"):
        outcome_from_data(data)


def test_schema_v2_rejects_attempt_provider_not_loaded_by_host() -> None:
    data = deepcopy(_plugin_completed_data())
    execution = cast(JsonObject, data["execution"])
    attempts = cast(list[object], execution["attempts"])
    selected = cast(JsonObject, attempts[-1])
    selected["capability_id"] = "org.other.plugin.comparator"
    selected["backend_id"] = "org.other.plugin.backend"
    provider = cast(JsonObject, selected["provider"])
    provider["plugin_id"] = "org.other.plugin"
    with pytest.raises(SerializationError, match="loaded provider"):
        outcome_from_data(data)


def test_schema_v2_rejects_backend_outside_provider_namespace() -> None:
    data = deepcopy(_plugin_completed_data())
    execution = cast(JsonObject, data["execution"])
    attempts = cast(list[object], execution["attempts"])
    selected = cast(JsonObject, attempts[-1])
    selected["backend_id"] = "org.other.backend"
    with pytest.raises(SerializationError, match="backend"):
        outcome_from_data(data)


def test_schema_v2_rejects_detector_provider_that_disagrees_with_detection() -> None:
    detector = _DetectorHandle()
    host, _ = _capability(detector, CapabilityKind.DETECTOR)
    outcome = host.compare(
        BytesSource(b"ascii"),
        BytesSource(b"ascii"),
        AutoCompareSpec(),
        detector_id=detector.capability_id,
    )
    assert isinstance(outcome, CompletedOutcomeV2)
    data = deepcopy(outcome_to_data(outcome))
    execution = cast(JsonObject, data["execution"])
    detection = cast(JsonObject, execution["detection"])
    detection["detector_id"] = "org.example.scidiff.other_detector"
    with pytest.raises(SerializationError, match="detector"):
        outcome_from_data(data)


def test_schema_v2_rejects_external_detector_with_deleted_provider() -> None:
    detector = _DetectorHandle()
    host, _ = _capability(detector, CapabilityKind.DETECTOR)
    outcome = host.compare(
        BytesSource(b"ascii"),
        BytesSource(b"ascii"),
        AutoCompareSpec(),
        detector_id=detector.capability_id,
    )
    assert isinstance(outcome, CompletedOutcomeV2)
    data = deepcopy(outcome_to_data(outcome))
    result = cast(JsonObject, data["result"])
    provenance = cast(JsonObject, result["provenance"])
    provenance["detector_provider"] = None
    execution = cast(JsonObject, data["execution"])
    attempts = cast(list[object], execution["attempts"])
    detector_attempt = next(
        cast(JsonObject, attempt)
        for attempt in attempts
        if cast(JsonObject, attempt)["capability_id"] == detector.capability_id
    )
    detector_attempt["provider"] = None
    with pytest.raises(SerializationError, match="detector provider"):
        outcome_from_data(data)


def test_known_plugin_exception_becomes_schema_v2_execution_failure() -> None:
    class FailingRun(_Run):
        def compare(self) -> None:
            raise PluginExecutionErrorV1("private plugin detail")

    class FailingHandle(_ComparatorHandle):
        def create_run(
            self,
            before: SourceServiceV1,
            after: SourceServiceV1,
            spec: TextCompareSpec,
        ) -> _Run:
            return FailingRun(before, after, _facts(), self.events)

    handle = FailingHandle()
    host, _ = _capability(handle, CapabilityKind.COMPARATOR, backend=True)
    outcome = host.compare(
        TextSource("same"),
        TextSource("same"),
        TextCompareSpec(),
        comparator_id=handle.capability_id,
    )
    assert isinstance(outcome, FailedOutcomeV2)
    assert outcome.problem.code == "plugin_execution_failure"
    assert outcome.problem.stage.value == "comparing"
    assert "private" not in outcome.problem.message
