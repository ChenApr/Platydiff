"""P3-B detector bounds, validation, pinning, and determinism profile."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from platydiff import (
    AutoCompareSpec,
    AutoResourceLimits,
    BytesSource,
    CompletedOutcomeV2,
    FailedOutcomeV2,
    PluginHost,
    UnavailableOutcomeV2,
)
from platydiff.core.models import JsonObject
from platydiff.plugin_sdk import (
    CapabilityAvailabilityV1,
    CapabilityKind,
    DetectorCandidateV1,
    DetectorInputV1,
)
from platydiff.plugins import PluginCatalogV1
from tests.unit.test_plugin_host_execution import _capability

_COUNTS: JsonObject = {
    "inspected_bytes": 0,
    "nul_count": 0,
    "non_ascii_byte_count": 0,
    "pending_utf8_bytes": 0,
    "disallowed_control_count": 0,
}


@dataclass
class _Detector:
    capability_id: str = "org.example.scidiff.detector"
    calls: list[DetectorInputV1] = field(default_factory=list)

    def availability(self) -> CapabilityAvailabilityV1:
        return CapabilityAvailabilityV1(True)

    def detect(self, source: DetectorInputV1) -> tuple[DetectorCandidateV1, ...]:
        self.calls.append(source)
        counts: JsonObject = dict(_COUNTS)
        counts["inspected_bytes"] = len(source.prefix)
        return (
            DetectorCandidateV1("binary", 400, ("ascii",), counts),
            DetectorCandidateV1("text", 900, ("ascii",), counts),
        )


def _spec(max_detection_bytes: int = 2) -> AutoCompareSpec:
    return AutoCompareSpec(
        limits=AutoResourceLimits(
            max_input_bytes=16, max_detection_bytes=max_detection_bytes
        )
    )


def test_detector_is_never_invoked_without_an_exact_pin() -> None:
    detector = _Detector()
    host, _ = _capability(detector, CapabilityKind.DETECTOR)
    outcome = host.compare(BytesSource(b"ascii"), BytesSource(b"ascii"), _spec())
    assert isinstance(outcome, CompletedOutcomeV2)
    assert detector.calls == []
    assert outcome.execution.detection is not None
    assert outcome.execution.detection.detector_id == "core.text_binary_prefix"


def test_pinned_detector_receives_only_each_bounded_prefix() -> None:
    detector = _Detector()
    host, _ = _capability(detector, CapabilityKind.DETECTOR)
    outcome = host.compare(
        BytesSource(b"abcdef"),
        BytesSource(b"uvwxyz"),
        _spec(),
        detector_id=detector.capability_id,
    )
    assert isinstance(outcome, CompletedOutcomeV2)
    assert [request.prefix for request in detector.calls] == [b"ab", b"uv"]
    assert [request.effective_limit for request in detector.calls] == [2, 2]
    assert [request.reached_eof for request in detector.calls] == [False, False]
    assert outcome.execution.detection is not None
    assert outcome.execution.detection.detector_id == detector.capability_id


def test_invalid_detector_output_is_a_safe_detecting_stage_failure() -> None:
    class InvalidDetector(_Detector):
        def detect(self, source: DetectorInputV1) -> tuple[DetectorCandidateV1, ...]:
            del source
            return (object(),)  # type: ignore[return-value]

    detector = InvalidDetector()
    host, _ = _capability(detector, CapabilityKind.DETECTOR)
    outcome = host.compare(
        BytesSource(b"ascii"),
        BytesSource(b"ascii"),
        _spec(),
        detector_id=detector.capability_id,
    )
    assert isinstance(outcome, FailedOutcomeV2)
    assert outcome.problem.code == "plugin_execution_failure"
    assert outcome.problem.stage.value == "detecting"


def test_missing_pinned_detector_does_not_fall_back_to_builtin() -> None:
    host = PluginHost(PluginCatalogV1((), (), (), (), ()))
    outcome = host.compare(
        BytesSource(b"ascii"),
        BytesSource(b"ascii"),
        _spec(),
        detector_id="org.example.missing.detector",
    )
    assert isinstance(outcome, UnavailableOutcomeV2)
    assert outcome.problem.code == "capability_unavailable"
    assert outcome.problem.stage.value == "resolving"
    assert outcome.execution.attempts[-1].disposition == "unavailable"


def test_detector_normalized_results_are_repeatable() -> None:
    detector = _Detector()
    host, _ = _capability(detector, CapabilityKind.DETECTOR)
    outcomes = [
        host.compare(
            BytesSource(b"ascii"),
            BytesSource(b"ascii"),
            _spec(),
            detector_id=detector.capability_id,
        )
        for _ in range(3)
    ]
    records = [outcome.execution.detection for outcome in outcomes]
    assert records[0] == records[1] == records[2]


@pytest.mark.parametrize("failure", [KeyboardInterrupt, SystemExit, MemoryError])
def test_detector_process_control_failures_propagate(
    failure: type[BaseException],
) -> None:
    class InterruptingDetector(_Detector):
        def detect(self, source: DetectorInputV1) -> tuple[DetectorCandidateV1, ...]:
            del source
            raise failure()

    detector = InterruptingDetector()
    host, _ = _capability(detector, CapabilityKind.DETECTOR)
    with pytest.raises(failure):
        host.compare(
            BytesSource(b"ascii"),
            BytesSource(b"ascii"),
            _spec(),
            detector_id=detector.capability_id,
        )
