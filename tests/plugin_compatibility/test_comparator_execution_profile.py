"""P3-B comparator lifecycle, budgets, failures, and outcome profile."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace

import pytest

from platydiff import (
    CompletedOutcomeV2,
    FailedOutcomeV2,
    ResourceLimits,
    TextCompareSpec,
    TextSource,
    UnavailableOutcomeV2,
)
from platydiff.core.models import (
    ChangeCompleteness,
    ChangeSelection,
    ChangeSet,
    Diagnostic,
    DiagnosticSeverity,
    DiffSummary,
    ExtensionChange,
)
from platydiff.plugin_sdk import (
    CapabilityAvailabilityV1,
    CapabilityKind,
    PluginComparisonV1,
    SourceServiceV1,
)
from tests.unit.test_plugin_host_execution import (
    _capability,
    _ComparatorHandle,
    _facts,
    _Run,
)


class _WrongStageRun(_Run):
    def decode(self) -> None:
        self.events.append("decode")

    def normalize(self) -> None:
        self.events.append("normalize")
        self.before.read()


class _OverreadingRun(_Run):
    def decode(self) -> None:
        super().decode()
        self.before.read()


@dataclass
class _ConfiguredHandle(_ComparatorHandle):
    run_type: type[_Run] = _Run
    aggregate_facts: PluginComparisonV1 | None = None
    cached_run: _Run | None = None
    reuse_run: bool = False

    def create_run(
        self,
        before: SourceServiceV1,
        after: SourceServiceV1,
        spec: TextCompareSpec,
    ) -> _Run:
        del spec
        if self.reuse_run and self.cached_run is not None:
            return self.cached_run
        run = self.run_type(
            before, after, self.aggregate_facts or _facts(), self.events
        )
        self.cached_run = run
        return run


def _compare(
    handle: _ComparatorHandle,
    spec: TextCompareSpec | None = None,
) -> CompletedOutcomeV2 | FailedOutcomeV2 | UnavailableOutcomeV2:
    host, _ = _capability(handle, CapabilityKind.COMPARATOR, backend=True)
    return host.compare(
        TextSource("same"),
        TextSource("same"),
        TextCompareSpec() if spec is None else spec,
        comparator_id=handle.capability_id,
    )


def test_comparator_profile_invokes_each_stage_once_and_is_repeatable() -> None:
    handle = _ConfiguredHandle()
    first = _compare(handle)
    second = _compare(handle)
    assert isinstance(first, CompletedOutcomeV2)
    assert isinstance(second, CompletedOutcomeV2)
    assert (
        handle.events
        == [
            "decode",
            "normalize",
            "align",
            "compare",
            "aggregate",
        ]
        * 2
    )
    assert first.result.relation is second.result.relation
    assert first.result.summary == second.result.summary
    assert first.result.metrics == second.result.metrics


def test_source_access_outside_declared_stage_fails_visibly() -> None:
    outcome = _compare(_ConfiguredHandle(run_type=_WrongStageRun))
    assert isinstance(outcome, FailedOutcomeV2)
    assert outcome.problem.code == "plugin_execution_failure"
    assert outcome.problem.stage.value == "normalizing"


def test_cumulative_source_budget_is_host_enforced() -> None:
    outcome = _compare(
        _ConfiguredHandle(run_type=_OverreadingRun),
        TextCompareSpec(limits=ResourceLimits(max_input_bytes=4)),
    )
    assert isinstance(outcome, FailedOutcomeV2)
    assert outcome.problem.code == "resource_limit_exceeded"
    assert outcome.problem.stage.value == "decoding"


def test_reused_run_is_rejected_before_a_second_execution() -> None:
    handle = _ConfiguredHandle(reuse_run=True)
    host, _ = _capability(handle, CapabilityKind.COMPARATOR, backend=True)
    first = host.compare(
        TextSource("same"),
        TextSource("same"),
        TextCompareSpec(),
        comparator_id=handle.capability_id,
    )
    second = host.compare(
        TextSource("same"),
        TextSource("same"),
        TextCompareSpec(),
        comparator_id=handle.capability_id,
    )
    assert isinstance(first, CompletedOutcomeV2)
    assert isinstance(second, FailedOutcomeV2)
    assert second.problem.stage.value == "resolving"
    assert handle.events.count("decode") == 1


def test_foreign_extension_namespace_is_rejected() -> None:
    facts = _facts()
    invalid_change = ExtensionChange("org.other.change", "org.other", 1, {"safe": True})
    facts = replace(
        facts,
        summary=DiffSummary(1, ()),
        changes=ChangeSet(
            ChangeCompleteness.COMPLETE,
            (invalid_change,),
            1,
            1,
            0,
            ChangeSelection.ALL,
            None,
        ),
    )
    outcome = _compare(_ConfiguredHandle(aggregate_facts=facts))
    assert isinstance(outcome, FailedOutcomeV2)
    assert outcome.problem.code == "plugin_execution_failure"
    assert outcome.problem.stage.value == "aggregating"


def test_unsafe_diagnostic_detail_is_rejected_without_disclosure() -> None:
    facts = replace(
        _facts(),
        diagnostics=(
            Diagnostic(
                "plugin_warning",
                DiagnosticSeverity.WARNING,
                None,
                "safe summary",
                {"location": "/private/user/secret"},
            ),
        ),
    )
    outcome = _compare(_ConfiguredHandle(aggregate_facts=facts))
    assert isinstance(outcome, FailedOutcomeV2)
    assert "secret" not in outcome.problem.message


def test_pinned_unavailable_comparator_never_falls_back() -> None:
    class UnavailableHandle(_ConfiguredHandle):
        def availability(self) -> CapabilityAvailabilityV1:
            return CapabilityAvailabilityV1(
                False,
                "org.example.scidiff.stdlib",
                "1",
                "backend_missing",
            )

    handle = UnavailableHandle()
    outcome = _compare(handle)
    assert isinstance(outcome, UnavailableOutcomeV2)
    assert handle.cached_run is None
    assert outcome.execution.attempts[-1].disposition == "unavailable"
    assert outcome.execution.attempts[-1].reason_code == "backend_missing"


def test_unpinned_enabled_comparator_never_preempts_builtin() -> None:
    handle = _ConfiguredHandle()
    host, _ = _capability(handle, CapabilityKind.COMPARATOR, backend=True)
    outcome = host.compare(TextSource("same"), TextSource("same"), TextCompareSpec())
    assert isinstance(outcome, CompletedOutcomeV2)
    assert handle.cached_run is None
    assert outcome.result.provenance.comparator_id == "text"


def test_generic_programming_error_propagates_without_retry() -> None:
    class DefectiveRun(_Run):
        def compare(self) -> None:
            self.events.append("compare")
            raise RuntimeError("programming defect")

    handle = _ConfiguredHandle(run_type=DefectiveRun)
    with pytest.raises(RuntimeError, match="programming defect"):
        _compare(handle)
    assert handle.events.count("compare") == 1


@pytest.mark.parametrize("failure", [KeyboardInterrupt, SystemExit, MemoryError])
def test_comparator_process_control_failures_propagate(
    failure: type[BaseException],
) -> None:
    class InterruptingRun(_Run):
        def compare(self) -> None:
            raise failure()

    with pytest.raises(failure):
        _compare(_ConfiguredHandle(run_type=InterruptingRun))


def test_host_public_configuration_is_frozen() -> None:
    host, _ = _capability(_ConfiguredHandle(), CapabilityKind.COMPARATOR, backend=True)
    with pytest.raises(FrozenInstanceError):
        host.catalog = host.catalog  # type: ignore[misc]
