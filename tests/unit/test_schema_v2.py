"""Schema-v2 provider provenance and schema-v1 migration tests."""

from __future__ import annotations

from platydiff import (
    BytesSource,
    CompletedOutcome,
    CompletedOutcomeV2,
    FailedOutcomeV2,
    PluginHost,
    TextCompareSpec,
    TextSource,
    compare,
    upgrade_outcome_v1_to_v2,
)
from platydiff.core.models import CapabilityAttemptV2, ComparisonProvenanceV2
from platydiff.core.serialization import dumps_outcome, loads_outcome, outcome_to_data
from platydiff.plugin_sdk import (
    CapabilityKind,
    PluginExecutionErrorV1,
    SourceServiceV1,
)
from platydiff.plugins import PluginCatalogV1
from tests.unit.test_plugin_host_execution import (
    _capability,
    _ComparatorHandle,
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
