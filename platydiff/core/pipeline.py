"""Lightweight orchestration with observed stage boundaries."""

from __future__ import annotations

import os
import stat
import time
from collections.abc import Callable
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import UTC, datetime

from platydiff._version import __version__
from platydiff.core._capabilities import (
    CapabilityCatalog,
    CapabilityRequest,
    Resolution,
    request_from_spec,
)
from platydiff.core._detection import detect_pair
from platydiff.core._sources import SourceSnapshot, open_source_snapshot
from platydiff.core.models import (
    ArrayCompareSpec,
    AutoCompareSpec,
    BinaryCompareSpec,
    BytesSource,
    CapabilityAttempt,
    CapabilityAttemptV2,
    CapabilityProblem,
    CapabilityProblemV2,
    CompareOutcome,
    CompareOutcomeV3,
    CompareSpec,
    CompletedOutcome,
    CompletedOutcomeV3,
    DetectionRecord,
    Diagnostic,
    DiffResult,
    ExecutionProblem,
    ExecutionProblemV2,
    ExecutionRecord,
    ExecutionRecordV2,
    FailedOutcome,
    FailedOutcomeV3,
    JsonCompareSpec,
    PathSource,
    PipelineStage,
    Source,
    SourceKind,
    StageDisposition,
    StageRecord,
    TableCompareSpec,
    TextCompareSpec,
    TextSource,
    UnavailableOutcome,
    UnavailableOutcomeV3,
    YamlCompareSpec,
)
from platydiff.core.problems import (
    CapabilityUnavailableError,
    DetectionUnavailableError,
    DomainError,
    InputOutputError,
    InvalidSpecError,
    ResourceLimitError,
    SourceNotFoundError,
    SourcePermissionError,
    SourceTypeUnsupportedError,
    UnavailableError,
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

    def __init__(self, clock: Clock, *, detection_enabled: bool = False) -> None:
        self._clock = clock
        self._started_at, self._started_ns = clock()
        self._finished_at = self._started_at
        self._finished_ns = self._started_ns
        self._records: list[StageRecord] = []
        self._attempts: list[CapabilityAttempt | CapabilityAttemptV2] = []
        self._detection_enabled = detection_enabled
        self._detection: DetectionRecord | None = None

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
                StageDisposition.UNAVAILABLE
                if isinstance(error, UnavailableError)
                else StageDisposition.FAILED,
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

    def record_selected_v3_capability(
        self, capability_id: str, capability_version: str
    ) -> None:
        if (
            not self._records
            or self._records[-1].stage is not PipelineStage.RESOLVING
            or self._records[-1].disposition is not StageDisposition.COMPLETED
        ):
            raise RuntimeError("capability selection must follow resolution")
        self._attempts.append(
            CapabilityAttemptV2(
                capability_id,
                "stdlib",
                "selected",
                capability_version=capability_version,
                backend_version=capability_version,
            )
        )

    def record_attempts(self, attempts: tuple[CapabilityAttempt, ...]) -> None:
        self._attempts.extend(attempts)

    def record_detection(self, detection: DetectionRecord) -> None:
        self._detection = detection

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
            detection=self._detection,
        )

    def execution_v3(self, diagnostics: tuple[Diagnostic, ...]) -> ExecutionRecordV2:
        completed = [
            record.stage
            for record in self._records
            if record.disposition is StageDisposition.COMPLETED
        ]
        if any(not isinstance(item, CapabilityAttemptV2) for item in self._attempts):
            raise RuntimeError("schema-v3 execution requires versioned attempts")
        return ExecutionRecordV2(
            started_at=self._started_at,
            finished_at=self._finished_at,
            duration_ns=max(0, self._finished_ns - self._started_ns),
            stages=tuple(self._records),
            attempts=tuple(self._attempts),
            diagnostics=diagnostics,
            last_completed_stage=completed[-1] if completed else None,
            detection=self._detection,
            plugin_host=None,
        )

    def _validate_next_stage(self, stage: PipelineStage) -> None:
        if stage is PipelineStage.DETECTING and not self._detection_enabled:
            raise RuntimeError("explicit text comparison must skip detection")
        if (
            self._records
            and self._records[-1].disposition is not StageDisposition.COMPLETED
        ):
            raise RuntimeError("no stage may run after a terminal disposition")
        lifecycle = tuple(PipelineStage) if self._detection_enabled else _PHASE1_STAGES
        expected_index = len(self._records)
        if expected_index >= len(lifecycle) or lifecycle[expected_index] is not stage:
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


def _validate_request(
    before: Source, after: Source, spec: CompareSpec
) -> TextCompareSpec:
    if not isinstance(spec, TextCompareSpec):
        raise InvalidSpecError("The comparison specification is not supported.")
    source_types = (PathSource, BytesSource, TextSource)
    if not isinstance(before, source_types) or not isinstance(after, source_types):
        raise InvalidSpecError("The source type is not supported.")
    return spec


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
        raise InputOutputError("A source is not a regular file.", retryable=False)

    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(path.path, flags)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise InputOutputError("A source is not a regular file.", retryable=False)
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
        validated_spec = stages.run(
            PipelineStage.VALIDATING, lambda: _validate_request(before, after, spec)
        )
        sourced_before, sourced_after = stages.run(
            PipelineStage.SOURCING,
            lambda: _source_pair(before, after, validated_spec),
        )
        executor = stages.run(PipelineStage.RESOLVING, lambda: resolver(validated_spec))
        stages.record_selected_capability()
        completion = executor(sourced_before, sourced_after, validated_spec, stages)
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


def run_snapshot_comparison(
    before: Source,
    after: Source,
    spec: AutoCompareSpec | BinaryCompareSpec,
    catalog: CapabilityCatalog,
    *,
    clock: Clock = _system_clock,
) -> CompareOutcome:
    """Run an automatic or explicit binary comparison over replayable snapshots."""
    stages = StageRunner(clock, detection_enabled=isinstance(spec, AutoCompareSpec))
    with ExitStack() as stack:
        try:
            stages.run(PipelineStage.VALIDATING, lambda: None)
            snapshots = stages.run(
                PipelineStage.SOURCING,
                lambda: _snapshot_pair(
                    stack, before, after, spec.limits.max_input_bytes
                ),
            )
            request = request_from_spec(
                spec, (snapshots[0].source_kind, snapshots[1].source_kind)
            )
            if isinstance(spec, AutoCompareSpec):
                detection = stages.run(
                    PipelineStage.DETECTING,
                    lambda: _detect_or_raise(stages, snapshots, spec, catalog, request),
                )
                if detection.selected_modality is None:
                    raise RuntimeError("selected detection lacks a modality")
                request = request.with_resolved_modality(detection.selected_modality)
            else:
                request = request.with_resolved_modality("binary")
            resolution = stages.run(
                PipelineStage.RESOLVING,
                lambda: _resolve_or_raise(stages, catalog, request),
            )
            if resolution.selected is None:
                raise RuntimeError("resolution completed without a capability")
            completion = resolution.selected.handle.run(
                snapshots[0], snapshots[1], spec, stages
            )
        except UnavailableError as error:
            return UnavailableOutcome(
                execution=stages.execution(()),
                problem=CapabilityProblem(
                    error.code,
                    error.status_code,
                    error.stage,
                    str(error),
                    error.details,
                    error.retryable,
                ),
            )
        except DomainError as error:
            return FailedOutcome(
                execution=stages.execution(()),
                problem=ExecutionProblem(
                    error.code,
                    error.status_code,
                    error.stage,
                    str(error),
                    error.details,
                    error.retryable,
                ),
            )
    return CompletedOutcome(
        execution=stages.execution(completion.diagnostics), result=completion.result
    )


def run_json_comparison(
    before: Source,
    after: Source,
    spec: JsonCompareSpec,
    executor: Callable[
        [SourceSnapshot, SourceSnapshot, JsonCompareSpec, StageRunner],
        ComparisonCompletion,
    ],
    *,
    clock: Clock = _system_clock,
) -> CompareOutcomeV3:
    """Run one explicit structured comparison with a schema-v3 envelope."""
    stages = StageRunner(clock)
    with ExitStack() as stack:
        try:
            stages.run(PipelineStage.VALIDATING, lambda: None)
            snapshots = stages.run(
                PipelineStage.SOURCING,
                lambda: _snapshot_pair(
                    stack, before, after, spec.limits.max_input_bytes
                ),
            )
            stages.run(PipelineStage.RESOLVING, lambda: None)
            stages.record_selected_v3_capability("json", __version__)
            completion = executor(snapshots[0], snapshots[1], spec, stages)
        except UnavailableError as error:
            return UnavailableOutcomeV3(
                execution=stages.execution_v3(()),
                problem=CapabilityProblemV2(
                    error.code,
                    error.status_code,
                    error.stage,
                    str(error),
                    error.details,
                    error.retryable,
                ),
            )
        except DomainError as error:
            return FailedOutcomeV3(
                execution=stages.execution_v3(()),
                problem=ExecutionProblemV2(
                    error.code,
                    error.status_code,
                    error.stage,
                    str(error),
                    error.details,
                    error.retryable,
                ),
            )
    return CompletedOutcomeV3(
        execution=stages.execution_v3(completion.diagnostics), result=completion.result
    )


def reject_phase4_plugin_comparison(
    before: Source,
    after: Source,
    spec: JsonCompareSpec | YamlCompareSpec | TableCompareSpec | ArrayCompareSpec,
    *,
    clock: Clock = _system_clock,
) -> CompareOutcomeV3:
    """Reject schema-v3 intent at the SDK-v1 plugin boundary before execution."""
    stages = StageRunner(clock)
    with ExitStack() as stack:
        try:
            stages.run(PipelineStage.VALIDATING, lambda: None)
            if isinstance(spec, ArrayCompareSpec):
                stages.run(
                    PipelineStage.SOURCING,
                    lambda: _validate_source_pair_types(before, after),
                )
            else:
                stages.run(
                    PipelineStage.SOURCING,
                    lambda: _snapshot_pair(
                        stack, before, after, spec.limits.max_input_bytes
                    ),
                )
            stages.run(
                PipelineStage.RESOLVING,
                lambda: _raise_capability_unavailable(()),
            )
        except UnavailableError as error:
            return UnavailableOutcomeV3(
                execution=stages.execution_v3(()),
                problem=CapabilityProblemV2(
                    error.code,
                    error.status_code,
                    error.stage,
                    str(error),
                    error.details,
                    error.retryable,
                ),
            )
        except DomainError as error:
            return FailedOutcomeV3(
                execution=stages.execution_v3(()),
                problem=ExecutionProblemV2(
                    error.code,
                    error.status_code,
                    error.stage,
                    str(error),
                    error.details,
                    error.retryable,
                ),
            )
    raise RuntimeError("unsupported Phase 4 plugin comparison unexpectedly ran")


def _validate_source_pair_types(before: Source, after: Source) -> None:
    source_types = (PathSource, BytesSource, TextSource)
    if not isinstance(before, source_types) or not isinstance(after, source_types):
        raise SourceTypeUnsupportedError()


def _snapshot_pair(
    stack: ExitStack, before: Source, after: Source, max_input_bytes: int
) -> tuple[SourceSnapshot, SourceSnapshot]:
    source_types = (PathSource, BytesSource, TextSource)
    if not isinstance(before, source_types) or not isinstance(after, source_types):
        raise SourceTypeUnsupportedError()
    return (
        stack.enter_context(
            open_source_snapshot(before, max_input_bytes=max_input_bytes)
        ),
        stack.enter_context(
            open_source_snapshot(after, max_input_bytes=max_input_bytes)
        ),
    )


def _detect_or_raise(
    stages: StageRunner,
    snapshots: tuple[SourceSnapshot, SourceSnapshot],
    spec: AutoCompareSpec,
    catalog: CapabilityCatalog,
    request: CapabilityRequest,
) -> DetectionRecord:
    detection = detect_pair(
        snapshots[0], snapshots[1], spec, catalog.records_for_detection(request)
    )
    stages.record_detection(detection)
    if detection.disposition != "selected":
        raise DetectionUnavailableError(ambiguous=detection.disposition == "ambiguous")
    return detection


def _raise_capability_unavailable(attempts: tuple[CapabilityAttempt, ...]) -> None:
    raise CapabilityUnavailableError(
        backend_missing=any(item.reason_code == "backend_missing" for item in attempts)
    )


def _resolve_or_raise(
    stages: StageRunner,
    catalog: CapabilityCatalog,
    request: CapabilityRequest,
) -> Resolution:
    resolution = catalog.resolve(request)
    stages.record_attempts(resolution.attempts)
    if resolution.selected is None:
        _raise_capability_unavailable(resolution.attempts)
    return resolution
