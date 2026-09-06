"""Regression tests for real Phase 1 stage timing and failure progress."""

from __future__ import annotations

from pathlib import Path

import pytest

from platydiff import (
    BytesSource,
    CompletedOutcome,
    FailedOutcome,
    PathSource,
    ResourceLimits,
    TextCompareSpec,
    TextSource,
)
from platydiff.api import _REGISTRY
from platydiff.core.models import PipelineStage, StageDisposition
from platydiff.core.pipeline import run_comparison


class IncrementingClock:
    """Return distinct UTC seconds and monotonic ticks on every call."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> tuple[str, int]:
        current = self.calls
        self.calls += 1
        return f"2026-09-07T00:00:{current:02d}Z", current * 10


def run_with_clock(
    before: BytesSource | PathSource | TextSource,
    after: BytesSource | PathSource | TextSource,
    spec: TextCompareSpec,
) -> CompletedOutcome | FailedOutcome:
    outcome = run_comparison(
        before,
        after,
        spec,
        _REGISTRY.resolve,
        clock=IncrementingClock(),
    )
    assert isinstance(outcome, (CompletedOutcome, FailedOutcome))
    return outcome


def assert_real_records(
    outcome: CompletedOutcome | FailedOutcome,
    expected: tuple[tuple[PipelineStage, StageDisposition], ...],
) -> None:
    assert (
        tuple((record.stage, record.disposition) for record in outcome.execution.stages)
        == expected
    )
    assert all(
        record.started_at != record.finished_at for record in outcome.execution.stages
    )
    assert all(record.duration_ns == 10 for record in outcome.execution.stages)
    assert len({record.started_at for record in outcome.execution.stages}) == len(
        expected
    )


def test_completed_outcome_records_each_real_stage_and_skips_detection() -> None:
    outcome = run_with_clock(
        TextSource("same\n"), TextSource("same\n"), TextCompareSpec()
    )
    assert isinstance(outcome, CompletedOutcome)
    expected_stages = tuple(
        (stage, StageDisposition.COMPLETED)
        for stage in PipelineStage
        if stage is not PipelineStage.DETECTING
    )
    assert_real_records(outcome, expected_stages)
    assert outcome.execution.last_completed_stage is PipelineStage.AGGREGATING
    assert outcome.execution.duration_ns == 160
    assert outcome.execution.attempts[0].capability_id == "text"


@pytest.mark.parametrize(
    ("before", "after", "spec", "failed_stage"),
    [
        (
            PathSource(Path("missing-parent-for-stage-test/missing.txt")),
            TextSource(""),
            TextCompareSpec(),
            PipelineStage.SOURCING,
        ),
        (
            BytesSource(b"\xff"),
            BytesSource(b"ok"),
            TextCompareSpec(),
            PipelineStage.DECODING,
        ),
        (
            TextSource("too-long"),
            TextSource("ok"),
            TextCompareSpec(limits=ResourceLimits(max_encoded_line_bytes=2)),
            PipelineStage.NORMALIZING,
        ),
        (
            TextSource("before"),
            TextSource("after"),
            TextCompareSpec(limits=ResourceLimits(max_myers_work=0)),
            PipelineStage.COMPARING,
        ),
    ],
)
def test_failure_records_only_stages_that_actually_ran(
    before: BytesSource | PathSource | TextSource,
    after: BytesSource | PathSource | TextSource,
    spec: TextCompareSpec,
    failed_stage: PipelineStage,
) -> None:
    outcome = run_with_clock(before, after, spec)
    assert isinstance(outcome, FailedOutcome)
    phase1 = tuple(
        stage for stage in PipelineStage if stage is not PipelineStage.DETECTING
    )
    terminal_index = phase1.index(failed_stage)
    expected = tuple(
        (
            stage,
            StageDisposition.FAILED
            if stage is failed_stage
            else StageDisposition.COMPLETED,
        )
        for stage in phase1[: terminal_index + 1]
    )
    assert_real_records(outcome, expected)
    completed = tuple(
        stage
        for stage, disposition in expected
        if disposition is StageDisposition.COMPLETED
    )
    assert outcome.execution.last_completed_stage is (
        completed[-1] if completed else None
    )
    assert all(
        record.stage is not PipelineStage.AGGREGATING
        for record in outcome.execution.stages
    )
