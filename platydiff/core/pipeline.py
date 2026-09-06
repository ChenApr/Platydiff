"""Lightweight orchestration with observed stage boundaries."""

from __future__ import annotations

import os
import stat
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from platydiff.core.models import (
    BytesSource,
    CapabilityAttempt,
    CompareOutcome,
    CompareSpec,
    CompletedOutcome,
    Diagnostic,
    DiffResult,
    ExecutionProblem,
    ExecutionRecord,
    FailedOutcome,
    PathSource,
    PipelineStage,
    Source,
    SourceKind,
    StageDisposition,
    StageRecord,
    TextCompareSpec,
    TextSource,
)
from platydiff.core.problems import (
    DomainError,
    InputOutputError,
    InvalidSpecError,
    ResourceLimitError,
    SourceNotFoundError,
    SourcePermissionError,
)

type Clock = Callable[[], tuple[str, int]]
type ComparisonExecutor = Callable[
    [SourcedInput, SourcedInput, CompareSpec, StageRunner], ComparisonCompletion
]
type Resolver = Callable[[CompareSpec], ComparisonExecutor]

_PHASE1_STAGES = tuple(
    stage for stage in PipelineStage if stage is not PipelineStage.DETECTING
)


@dataclass(frozen=True, slots=True)
class ComparisonCompletion:
    result: DiffResult
    diagnostics: tuple[Diagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class SourcedInput:
    """Bounded source data passed from orchestration to a comparator."""

    data: bytes
    source_kind: SourceKind
    label: str | None
    decoded_text: str | None


def _system_clock() -> tuple[str, int]:
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return timestamp, time.monotonic_ns()


class StageRunner:
    """Record actual stage calls, durations, and terminal disposition."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._started_at, self._started_ns = clock()
        self._finished_at = self._started_at
        self._finished_ns = self._started_ns
        self._records: list[StageRecord] = []
        self._attempts: list[CapabilityAttempt] = []

    def run[T](self, stage: PipelineStage, operation: Callable[[], T]) -> T:
        self._validate_next_stage(stage)
        started_at, started_ns = self._clock()
        try:
            result = operation()
        except DomainError as error:
            if error.stage is not stage:
                raise RuntimeError(
                    "domain failure stage does not match its observed boundary"
                ) from error
            finished_at, finished_ns = self._clock()
            self._append_record(
                stage,
                started_at,
                started_ns,
                finished_at,
                finished_ns,
                StageDisposition.FAILED,
            )
            raise
        finished_at, finished_ns = self._clock()
        self._append_record(
            stage,
            started_at,
            started_ns,
            finished_at,
            finished_ns,
            StageDisposition.COMPLETED,
        )
        return result

    def record_selected_capability(self) -> None:
        if (
            not self._records
            or self._records[-1].stage is not PipelineStage.RESOLVING
            or self._records[-1].disposition is not StageDisposition.COMPLETED
        ):
            raise RuntimeError("capability selection must follow resolution")
        self._attempts.append(CapabilityAttempt("text", "stdlib", "selected"))

    def execution(self, diagnostics: tuple[Diagnostic, ...]) -> ExecutionRecord:
        completed = [
            record.stage
            for record in self._records
            if record.disposition is StageDisposition.COMPLETED
        ]
        return ExecutionRecord(
            started_at=self._started_at,
            finished_at=self._finished_at,
            duration_ns=max(0, self._finished_ns - self._started_ns),
            stages=tuple(self._records),
            attempts=tuple(self._attempts),
            diagnostics=diagnostics,
            last_completed_stage=completed[-1] if completed else None,
        )

    def _validate_next_stage(self, stage: PipelineStage) -> None:
        if stage is PipelineStage.DETECTING:
            raise RuntimeError("explicit text comparison must skip detection")
        if (
            self._records
            and self._records[-1].disposition is not StageDisposition.COMPLETED
        ):
            raise RuntimeError("no stage may run after a terminal disposition")
        expected_index = len(self._records)
        if (
            expected_index >= len(_PHASE1_STAGES)
            or _PHASE1_STAGES[expected_index] is not stage
        ):
            raise RuntimeError("comparison stages must run in enabled lifecycle order")

    def _append_record(
        self,
        stage: PipelineStage,
        started_at: str,
        started_ns: int,
        finished_at: str,
        finished_ns: int,
        disposition: StageDisposition,
    ) -> None:
        self._finished_at = finished_at
        self._finished_ns = finished_ns
        self._records.append(
            StageRecord(
                stage=stage,
                started_at=started_at,
                finished_at=finished_at,
                duration_ns=max(0, finished_ns - started_ns),
                disposition=disposition,
            )
        )


def _validate_request(before: Source, after: Source, spec: CompareSpec) -> None:
    if not isinstance(spec, TextCompareSpec):
        raise InvalidSpecError("The comparison specification is not supported.")
    source_types = (PathSource, BytesSource, TextSource)
    if not isinstance(before, source_types) or not isinstance(after, source_types):
        raise InvalidSpecError("The source type is not supported.")


def _read_regular_path(path: PathSource, max_bytes: int) -> bytes:
    try:
        metadata = path.path.stat()
    except FileNotFoundError as error:
        raise SourceNotFoundError("A source file was not found.") from error
    except PermissionError as error:
        raise SourcePermissionError(
            "Permission was denied while reading a source."
        ) from error
    except OSError as error:
        raise InputOutputError("A source could not be inspected.") from error
    if not stat.S_ISREG(metadata.st_mode):
        raise InputOutputError("A source is not a regular file.")

    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(path.path, flags)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise InputOutputError("A source is not a regular file.")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            data = stream.read(max_bytes + 1)
    except FileNotFoundError as error:
        raise SourceNotFoundError("A source file was not found.") from error
    except PermissionError as error:
        raise SourcePermissionError(
            "Permission was denied while reading a source."
        ) from error
    except OSError as error:
        raise InputOutputError("A source could not be read.") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if len(data) > max_bytes:
        raise ResourceLimitError(
            "A source exceeded the configured byte limit.",
            stage=PipelineStage.SOURCING,
        )
    return data


def _source(source: Source, max_bytes: int) -> SourcedInput:
    if isinstance(source, PathSource):
        return SourcedInput(
            _read_regular_path(source, max_bytes),
            SourceKind.PATH,
            source.path.name,
            None,
        )
    if isinstance(source, BytesSource):
        data = source.data
        kind = SourceKind.BYTES
        label = source.label
        decoded_text = None
    else:
        data = source.text.encode("utf-8", errors="strict")
        kind = SourceKind.TEXT
        label = source.label
        decoded_text = source.text
    if len(data) > max_bytes:
        raise ResourceLimitError(
            "A source exceeded the configured byte limit.",
            stage=PipelineStage.SOURCING,
        )
    return SourcedInput(data, kind, label, decoded_text)


def _source_pair(
    before: Source, after: Source, spec: TextCompareSpec
) -> tuple[SourcedInput, SourcedInput]:
    return (
        _source(before, spec.limits.max_input_bytes),
        _source(after, spec.limits.max_input_bytes),
    )


def run_comparison(
    before: Source,
    after: Source,
    spec: CompareSpec,
    resolver: Resolver,
    *,
    clock: Clock = _system_clock,
) -> CompareOutcome:
    """Run one explicit comparison and convert only expected domain failures."""
    stages = StageRunner(clock)
    try:
        stages.run(
            PipelineStage.VALIDATING, lambda: _validate_request(before, after, spec)
        )
        sourced_before, sourced_after = stages.run(
            PipelineStage.SOURCING, lambda: _source_pair(before, after, spec)
        )
        executor = stages.run(PipelineStage.RESOLVING, lambda: resolver(spec))
        stages.record_selected_capability()
        completion = executor(sourced_before, sourced_after, spec, stages)
    except DomainError as error:
        return FailedOutcome(
            execution=stages.execution(()),
            problem=ExecutionProblem(
                code=error.code,
                status_code=error.status_code,
                stage=error.stage,
                message=str(error),
                details=error.details,
                retryable=error.retryable,
            ),
        )
    return CompletedOutcome(
        execution=stages.execution(completion.diagnostics), result=completion.result
    )
