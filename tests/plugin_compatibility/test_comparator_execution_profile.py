"""P3-B comparator lifecycle, budgets, failures, and outcome profile."""

from __future__ import annotations

import gc
import weakref
from dataclasses import FrozenInstanceError, dataclass, replace
from pathlib import Path

import pytest

from platydiff import (
    CompletedOutcomeV2,
    FailedOutcomeV2,
    PathSource,
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
    ResourceUsage,
)
from platydiff.core.serialization import dumps_outcome, loads_outcome
from platydiff.plugin_sdk import (
    CapabilityAvailabilityV1,
    CapabilityKind,
    PluginComparisonV1,
    PluginResourceLimitErrorV1,
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


def test_completed_runs_are_not_retained_by_a_long_lived_host() -> None:
    class TrackingHandle(_ComparatorHandle):
        run_references: list[weakref.ReferenceType[_Run]]

        def __init__(self) -> None:
            super().__init__()
            self.run_references = []

        def create_run(
            self,
            before: SourceServiceV1,
            after: SourceServiceV1,
            spec: TextCompareSpec,
        ) -> _Run:
            del spec
            run = _Run(before, after, _facts(), self.events)
            self.run_references.append(weakref.ref(run))
            return run

    handle = TrackingHandle()
    host, _ = _capability(handle, CapabilityKind.COMPARATOR, backend=True)
    for _ in range(200):
        outcome = host.compare(
            TextSource("same"),
            TextSource("same"),
            TextCompareSpec(),
            comparator_id=handle.capability_id,
        )
        assert isinstance(outcome, CompletedOutcomeV2)
    del outcome
    gc.collect()
    assert all(reference() is None for reference in handle.run_references)
    assert len(host._used_runs) == 1


def test_invalid_run_shape_is_a_safe_resolving_failure() -> None:
    class InvalidRunHandle(_ComparatorHandle):
        def create_run(
            self,
            before: SourceServiceV1,
            after: SourceServiceV1,
            spec: TextCompareSpec,
        ) -> _Run:
            del before, after, spec
            return None  # type: ignore[return-value]

    outcome = _compare(InvalidRunHandle())
    assert isinstance(outcome, FailedOutcomeV2)
    assert outcome.problem.code == "plugin_execution_failure"
    assert outcome.problem.stage.value == "resolving"


def test_non_weak_referenceable_run_is_a_safe_resolving_failure() -> None:
    class SlottedRun:
        __slots__ = ()

        def decode(self) -> None:
            return None

        def normalize(self) -> None:
            return None

        def align(self) -> None:
            return None

        def compare(self) -> None:
            return None

        def aggregate(self) -> PluginComparisonV1:
            return _facts()

    class SlottedRunHandle(_ComparatorHandle):
        def create_run(
            self,
            before: SourceServiceV1,
            after: SourceServiceV1,
            spec: TextCompareSpec,
        ) -> _Run:
            del before, after, spec
            return SlottedRun()  # type: ignore[return-value]

    outcome = _compare(SlottedRunHandle())
    assert isinstance(outcome, FailedOutcomeV2)
    assert outcome.problem.code == "plugin_execution_failure"
    assert outcome.problem.stage.value == "resolving"


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


@pytest.mark.parametrize(
    "resource_name",
    ["host.plugin_before_source_bytes", "host.plugin_after_source_bytes"],
)
def test_host_reserved_resource_name_is_an_aggregating_failure(
    resource_name: str,
) -> None:
    facts = replace(
        _facts(),
        resources=(ResourceUsage(resource_name, 4, 1),),
    )
    outcome = _compare(_ConfiguredHandle(aggregate_facts=facts))
    assert isinstance(outcome, FailedOutcomeV2)
    assert outcome.problem.code == "plugin_execution_failure"
    assert outcome.problem.stage.value == "aggregating"
    assert outcome.execution.stages[-1].stage.value == "aggregating"
    assert outcome.execution.stages[-1].disposition.value == "failed"
    assert outcome.execution.attempts[-1].disposition == "failed"
    assert outcome.execution.attempts[-1].reason_code == "plugin_execution_failure"


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


def test_path_mutation_after_source_read_fails_at_aggregation(
    tmp_path: Path,
) -> None:
    before_path = tmp_path / "before.txt"
    after_path = tmp_path / "after.txt"
    before_path.write_bytes(b"same")
    after_path.write_bytes(b"same")

    class MutatingRun(_Run):
        def normalize(self) -> None:
            super().normalize()
            before_path.write_bytes(b"changed")

    handle = _ConfiguredHandle(run_type=MutatingRun)
    host, _ = _capability(handle, CapabilityKind.COMPARATOR, backend=True)
    outcome = host.compare(
        PathSource(before_path),
        PathSource(after_path),
        TextCompareSpec(),
        comparator_id=handle.capability_id,
    )
    assert isinstance(outcome, FailedOutcomeV2)
    assert outcome.problem.code == "source_changed"
    assert outcome.problem.stage.value == "aggregating"
    assert before_path.read_bytes() == b"changed"


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


def test_comparator_availability_resource_limit_is_auditable() -> None:
    class ResourceLimitedHandle(_ConfiguredHandle):
        def availability(self) -> CapabilityAvailabilityV1:
            raise PluginResourceLimitErrorV1("private budget detail")

    handle = ResourceLimitedHandle()
    outcome = _compare(handle)
    assert isinstance(outcome, FailedOutcomeV2)
    assert handle.cached_run is None
    assert outcome.problem.code == "resource_limit_exceeded"
    assert outcome.problem.stage.value == "resolving"
    assert "private" not in outcome.problem.message
    assert len(outcome.execution.attempts) == 1
    attempt = outcome.execution.attempts[0]
    assert attempt.disposition == "failed"
    assert attempt.reason_code == "resource_limit_exceeded"
    assert attempt.provider is not None


def test_comparator_runtime_backend_must_match_its_declaration() -> None:
    class UndeclaredBackendHandle(_ConfiguredHandle):
        def availability(self) -> CapabilityAvailabilityV1:
            return CapabilityAvailabilityV1(
                True,
                "org.example.scidiff.dynamic_backend",
                "9",
            )

    handle = UndeclaredBackendHandle()
    host, _ = _capability(handle, CapabilityKind.COMPARATOR)
    outcome = host.compare(
        TextSource("same"),
        TextSource("same"),
        TextCompareSpec(),
        comparator_id=handle.capability_id,
    )
    assert isinstance(outcome, FailedOutcomeV2)
    assert handle.cached_run is None
    assert outcome.problem.code == "plugin_execution_failure"
    assert outcome.problem.stage.value == "resolving"
    assert outcome.execution.attempts[-1].disposition == "failed"
    assert loads_outcome(dumps_outcome(outcome)) == outcome


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
