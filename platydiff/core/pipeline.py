"""Lightweight orchestration and expected-domain failure conversion."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from platydiff.core.models import (
    CapabilityAttempt,
    CompareOutcome,
    CompareSpec,
    CompletedOutcome,
    Diagnostic,
    DiffResult,
    ExecutionProblem,
    ExecutionRecord,
    FailedOutcome,
    PipelineStage,
    Source,
    StageDisposition,
    StageRecord,
)
from platydiff.core.problems import DomainError

type Clock = Callable[[], tuple[str, int]]
type Executor = Callable[[Source, Source, CompareSpec], ComparisonCompletion]

_PHASE1_STAGES = tuple(
    stage for stage in PipelineStage if stage is not PipelineStage.DETECTING
)


@dataclass(frozen=True, slots=True)
class ComparisonCompletion:
    result: DiffResult
    diagnostics: tuple[Diagnostic, ...] = ()


def _system_clock() -> tuple[str, int]:
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return timestamp, time.monotonic_ns()


def _execution_record(
    *,
    started_at: str,
    started_ns: int,
    finished_at: str,
    finished_ns: int,
    terminal_stage: PipelineStage,
    terminal_disposition: StageDisposition,
    diagnostics: tuple[Diagnostic, ...],
) -> ExecutionRecord:
    terminal_index = _PHASE1_STAGES.index(terminal_stage)
    records = tuple(
        StageRecord(
            stage=stage,
            started_at=started_at,
            finished_at=finished_at,
            duration_ns=0,
            disposition=(
                terminal_disposition
                if index == terminal_index
                else StageDisposition.COMPLETED
            ),
        )
        for index, stage in enumerate(_PHASE1_STAGES[: terminal_index + 1])
    )
    completed = [
        record.stage
        for record in records
        if record.disposition is StageDisposition.COMPLETED
    ]
    attempts = (
        (CapabilityAttempt("text", "stdlib", "selected"),)
        if terminal_index >= _PHASE1_STAGES.index(PipelineStage.RESOLVING)
        else ()
    )
    return ExecutionRecord(
        started_at=started_at,
        finished_at=finished_at,
        duration_ns=max(0, finished_ns - started_ns),
        stages=records,
        attempts=attempts,
        diagnostics=diagnostics,
        last_completed_stage=completed[-1] if completed else None,
    )


def run_comparison(
    before: Source,
    after: Source,
    spec: CompareSpec,
    executor: Executor,
    *,
    clock: Clock = _system_clock,
) -> CompareOutcome:
    """Run one explicit comparison and convert only expected domain failures."""
    started_at, started_ns = clock()
    try:
        completion = executor(before, after, spec)
    except DomainError as error:
        finished_at, finished_ns = clock()
        execution = _execution_record(
            started_at=started_at,
            started_ns=started_ns,
            finished_at=finished_at,
            finished_ns=finished_ns,
            terminal_stage=error.stage,
            terminal_disposition=StageDisposition.FAILED,
            diagnostics=(),
        )
        return FailedOutcome(
            execution=execution,
            problem=ExecutionProblem(
                code=error.code,
                status_code=error.status_code,
                stage=error.stage,
                message=str(error),
                details=error.details,
                retryable=error.retryable,
            ),
        )
    finished_at, finished_ns = clock()
    execution = _execution_record(
        started_at=started_at,
        started_ns=started_ns,
        finished_at=finished_at,
        finished_ns=finished_ns,
        terminal_stage=PipelineStage.AGGREGATING,
        terminal_disposition=StageDisposition.COMPLETED,
        diagnostics=completion.diagnostics,
    )
    return CompletedOutcome(execution=execution, result=completion.result)
