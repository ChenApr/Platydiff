"""Cross-boundary failure isolation matrix for the complete P3 host."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from platydiff import (
    BytesSource,
    FailedOutcomeV2,
    TextCompareSpec,
    TextSource,
    UnavailableOutcomeV2,
    compare,
)
from platydiff.core.models import AnyCompareOutcome
from platydiff.core.serialization import dumps_outcome
from platydiff.plugin_sdk import (
    CapabilityAvailabilityV1,
    CapabilityKind,
    DetectorCandidateV1,
    DetectorInputV1,
    PluginExecutionErrorV1,
    RendererPresentationOptionsV1,
    RendererSinkV1,
)
from platydiff.plugins import (
    PluginDiscoveryPolicy,
    RendererExecutionError,
    discover_plugins,
)
from tests.plugin_compatibility.fakes import FakeEntryPoint
from tests.plugin_compatibility.profiles import FAILURE_ISOLATION_MATRIX
from tests.plugin_compatibility.test_comparator_execution_profile import (
    _compare,
    _ConfiguredHandle,
)
from tests.plugin_compatibility.test_detector_execution_profile import (
    _Detector,
    _spec,
)
from tests.plugin_compatibility.test_discovery_profile import _install, _manifest
from tests.plugin_compatibility.test_renderer_execution_profile import (
    _Renderer,
    _renderer_host,
)
from tests.unit.test_plugin_host_execution import _capability, _Run


def test_isolation_matrix_names_every_p3_execution_boundary() -> None:
    assert FAILURE_ISOLATION_MATRIX == (
        ("discovery", "quarantined", "continue unrelated plugins"),
        (
            "availability",
            "unavailable or failed outcome",
            "no invocation or fallback",
        ),
        ("detector", "failed outcome", "no retry or fallback"),
        ("comparator", "failed outcome", "no retry or content difference"),
        (
            "renderer",
            "typed renderer error",
            "preserve outcome and no fallback",
        ),
        ("cli", "exit 3 with safe stderr", "emit no replacement output"),
    )


def test_discovery_failure_is_quarantined_while_valid_peer_remains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broken = FakeEntryPoint(
        "org.example.broken",
        object(),
        load_error=RuntimeError("private /Users/alice/plugin.py"),
        distribution_name="broken-plugin",
    )
    valid = FakeEntryPoint(
        "org.example.valid",
        lambda: _manifest("org.example.valid"),
        distribution_name="valid-plugin",
    )
    _install(monkeypatch, (broken, valid))

    catalog = discover_plugins(
        PluginDiscoveryPolicy(("org.example.broken", "org.example.valid"))
    )

    assert [item.manifest.plugin_id for item in catalog.plugins] == [
        "org.example.valid"
    ]
    assert [item.reason_code for item in catalog.issues] == ["plugin_import_failed"]
    assert "/Users/alice" not in repr(catalog)


def test_unavailable_capability_is_not_invoked_or_replaced() -> None:
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
    assert outcome.execution.attempts[-1].capability_id == handle.capability_id
    assert outcome.execution.attempts[-1].reason_code == "backend_missing"


def test_detector_failure_is_safe_and_never_falls_back() -> None:
    class FailingDetector(_Detector):
        def detect(self, source: DetectorInputV1) -> tuple[DetectorCandidateV1, ...]:
            del source
            raise PluginExecutionErrorV1("private detector detail")

    detector = FailingDetector()
    host, _ = _capability(detector, CapabilityKind.DETECTOR)
    outcome = host.compare(
        BytesSource(b"same"),
        BytesSource(b"same"),
        _spec(),
        detector_id=detector.capability_id,
    )

    assert isinstance(outcome, FailedOutcomeV2)
    assert outcome.problem.code == "plugin_execution_failure"
    assert outcome.problem.stage.value == "detecting"
    assert [item.capability_id for item in outcome.execution.attempts] == [
        detector.capability_id
    ]


def test_comparator_failure_is_not_retried_or_reported_as_difference() -> None:
    class FailingRun(_Run):
        def compare(self) -> None:
            self.events.append("compare")
            raise PluginExecutionErrorV1("private comparator detail")

    handle = _ConfiguredHandle(run_type=FailingRun)
    outcome = _compare(handle)

    assert isinstance(outcome, FailedOutcomeV2)
    assert outcome.problem.code == "plugin_execution_failure"
    assert outcome.problem.stage.value == "comparing"
    assert handle.events.count("compare") == 1
    assert not hasattr(outcome, "result")


def test_renderer_failure_preserves_completed_outcome_without_fallback() -> None:
    @dataclass
    class FailingRenderer(_Renderer):
        def render(
            self,
            outcome: AnyCompareOutcome,
            options: RendererPresentationOptionsV1,
            sink: RendererSinkV1,
        ) -> None:
            del outcome, options, sink
            raise RuntimeError("private renderer detail")

    renderer = FailingRenderer()
    host = _renderer_host(renderer)
    outcome = compare(TextSource("same"), TextSource("same"), TextCompareSpec())
    before = dumps_outcome(outcome)

    with pytest.raises(RendererExecutionError) as caught:
        host.render(outcome, renderer_id=renderer.capability_id)

    assert caught.value.outcome is outcome
    assert dumps_outcome(outcome) == before
