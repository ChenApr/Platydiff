"""Immutable plugin host and host-owned SDK-v1 execution lifecycles."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from dataclasses import dataclass, field, replace
from functools import partial
from hashlib import sha256
from typing import Literal, cast

from platydiff.api import _CATALOG
from platydiff.api import compare as compare_builtin
from platydiff.core._capabilities import (
    CapabilityRecord,
    ComparatorCapabilityHandle,
    request_from_spec,
)
from platydiff.core._detection import detect_pair
from platydiff.core._sources import SourceSnapshot, open_source_snapshot
from platydiff.core.models import (
    AutoCompareSpec,
    BinaryCompareSpec,
    BytesSource,
    CapabilityAttempt,
    CapabilityAttemptV2,
    CapabilityProblemV2,
    CompareOutcomeV2,
    CompareSpec,
    ComparisonProvenance,
    ComparisonProvenanceV2,
    CompletedOutcomeV2,
    DetectionCandidate,
    DetectionRecord,
    Diagnostic,
    DiffResult,
    ExecutionProblemV2,
    ExecutionRecord,
    ExecutionRecordV2,
    ExtensionChange,
    FailedOutcomeV2,
    InputProvenance,
    PairDetectionCandidate,
    PathSource,
    PipelineStage,
    PluginHostExecutionRecord,
    ProviderIdentity,
    ResourceUsage,
    Source,
    SourceDetectionRecord,
    SourceKind,
    StageDisposition,
    TextCompareSpec,
    TextSource,
    UnavailableOutcomeV2,
)
from platydiff.core.pipeline import StageRunner, _system_clock
from platydiff.core.problems import (
    CapabilityUnavailableError,
    DetectionUnavailableError,
    DomainError,
    ResourceLimitError,
    SourceTypeUnsupportedError,
    UnavailableError,
)
from platydiff.core.serialization import (
    _result_from_data,
    _result_to_data,
    spec_to_data,
    upgrade_outcome_v1_to_v2,
)
from platydiff.plugin_sdk import (
    CapabilityAvailabilityV1,
    CapabilityKind,
    ComparatorHandleV1,
    ComparatorRunV1,
    DetectorCandidateV1,
    DetectorHandleV1,
    DetectorInputV1,
    PluginComparisonV1,
    PluginExecutionErrorV1,
    PluginResourceLimitErrorV1,
    PluginUnavailableErrorV1,
)
from platydiff.plugins._discovery import (
    DiscoveredCapabilityV1,
    PluginCatalogV1,
    PluginDiscoveryPolicy,
    discover_plugins,
)

type ResolvedPluginSpec = TextCompareSpec | BinaryCompareSpec


class PluginExecutionFailureError(DomainError):
    """A safely mapped failure raised by a selected executable plugin."""

    def __init__(self, *, stage: PipelineStage) -> None:
        super().__init__(
            "The selected plugin could not complete the comparison.",
            code="plugin_execution_failure",
            status_code=502,
            stage=stage,
        )


class PluginCapabilityUnavailableError(UnavailableError):
    """A pinned plugin capability was unavailable before execution."""

    def __init__(self, *, reason_code: str = "capability_unavailable") -> None:
        super().__init__(
            "The selected plugin capability is unavailable.",
            code="capability_unavailable",
            status_code=501,
            stage=PipelineStage.RESOLVING,
            details={"reason_code": reason_code},
        )


@dataclass(frozen=True, slots=True)
class HostedPluginComparison:
    """Host-validated facts plus deterministic source-service byte accounting."""

    capability: DiscoveredCapabilityV1
    facts: PluginComparisonV1
    source_bytes_used: tuple[int, int]


@dataclass(frozen=True, slots=True)
class _PreparedComparator:
    capability: DiscoveredCapabilityV1
    run: ComparatorRunV1
    before: _HostedSourceService
    after: _HostedSourceService


class _HostedSourceService:
    def __init__(
        self,
        snapshot: SourceSnapshot,
        *,
        allowed_stage: PipelineStage,
        byte_budget: int,
    ) -> None:
        self.source_kind = snapshot.source_kind
        self.label = _safe_label(snapshot.label)
        self.size_bytes = snapshot.size_bytes
        self._snapshot = snapshot
        self._allowed_stage = allowed_stage
        self._active_stage: PipelineStage | None = None
        self._byte_budget = byte_budget
        self._bytes_used = 0

    @property
    def bytes_used(self) -> int:
        return self._bytes_used

    def activate(self, stage: PipelineStage | None) -> None:
        self._active_stage = stage

    def read(self) -> bytes:
        return b"".join(self.iter_chunks(64 * 1024))

    def iter_chunks(self, chunk_bytes: int) -> Iterator[bytes]:
        self._check_access()
        if isinstance(chunk_bytes, bool) or not isinstance(chunk_bytes, int):
            raise ValueError("chunk_bytes must be an integer")
        if not 1 <= chunk_bytes <= 16 * 1024 * 1024:
            raise ValueError("chunk_bytes must be in 1..16777216")
        for chunk in self._snapshot.iter_chunks(chunk_bytes, stage=self._allowed_stage):
            self._check_access()
            if self._bytes_used + len(chunk) > self._byte_budget:
                raise PluginResourceLimitErrorV1(
                    "The host source byte budget was exhausted."
                )
            self._bytes_used += len(chunk)
            yield chunk

    def _check_access(self) -> None:
        if self._active_stage is not self._allowed_stage:
            raise PluginExecutionErrorV1(
                "Source bytes are unavailable during this lifecycle stage."
            )


@dataclass(frozen=True, slots=True)
class PluginHost:
    """One immutable snapshot of an explicitly allowlisted plugin environment."""

    catalog: PluginCatalogV1
    _used_runs: list[object] = field(
        default_factory=list, init=False, repr=False, compare=False
    )
    _run_lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False, compare=False
    )

    @classmethod
    def discover(cls, policy: PluginDiscoveryPolicy) -> PluginHost:
        return cls(discover_plugins(policy))

    def capability(self, capability_id: str) -> DiscoveredCapabilityV1 | None:
        return next(
            (
                capability
                for capability in self.catalog.capabilities
                if capability.declaration.capability_id == capability_id
            ),
            None,
        )

    def compare(
        self,
        before: Source,
        after: Source,
        spec: CompareSpec,
        *,
        detector_id: str | None = None,
        comparator_id: str | None = None,
    ) -> CompareOutcomeV2:
        """Compare with this fixed provider snapshot and always return schema v2."""
        if detector_id is None and (
            comparator_id is None or comparator_id in {"text", "binary"}
        ):
            if comparator_id is not None and comparator_id != spec.kind:
                raise ValueError(
                    "the pinned built-in comparator does not match the spec"
                )
            upgraded = upgrade_outcome_v1_to_v2(compare_builtin(before, after, spec))
            return _bind_host_context(self, upgraded)
        return self._compare_composed(
            before,
            after,
            spec,
            detector_id=detector_id,
            comparator_id=comparator_id,
        )

    def _compare_composed(
        self,
        before_source: Source,
        after_source: Source,
        spec: CompareSpec,
        *,
        detector_id: str | None,
        comparator_id: str | None,
    ) -> CompareOutcomeV2:
        stages = StageRunner(
            _system_clock, detection_enabled=isinstance(spec, AutoCompareSpec)
        )
        detector_provider: ProviderIdentity | None = None
        with ExitStack() as stack:
            try:
                stages.run(
                    PipelineStage.VALIDATING,
                    lambda: _validate_composed_request(
                        before_source, after_source, spec, detector_id
                    ),
                )
                snapshots, inputs = stages.run(
                    PipelineStage.SOURCING,
                    lambda: _snapshot_inputs(
                        stack,
                        before_source,
                        after_source,
                        spec.limits.max_input_bytes,
                    ),
                )
                request = request_from_spec(
                    spec, (snapshots[0].source_kind, snapshots[1].source_kind)
                )
                detection_capability: DiscoveredCapabilityV1 | None = None
                detector_missing = False
                if isinstance(spec, AutoCompareSpec):
                    detection_capability = (
                        None if detector_id is None else self.capability(detector_id)
                    )
                    detector_missing = (
                        detector_id is not None and detection_capability is None
                    )
                    comparator_candidates = self._detection_comparator_candidates(
                        comparator_id
                    )

                    def run_detection() -> DetectionRecord:
                        nonlocal detector_provider
                        if detector_id is None:
                            detection = detect_pair(
                                snapshots[0],
                                snapshots[1],
                                spec,
                                self._detection_capability_records(comparator_id),
                            )
                        elif detection_capability is None:
                            detection = _missing_detector_record(detector_id, spec)
                        else:
                            detection = self._detect(
                                detection_capability,
                                snapshots,
                                spec,
                                comparator_candidates,
                            )
                            detector_provider = _provider_identity(detection_capability)
                            stages.record_attempts(
                                (_selected_attempt(detection_capability),)
                            )
                        stages.record_detection(detection)
                        if detection.disposition != "selected" and not detector_missing:
                            raise DetectionUnavailableError(
                                ambiguous=detection.disposition == "ambiguous"
                            )
                        return detection

                    detection = stages.run(PipelineStage.DETECTING, run_detection)
                    if detector_missing:
                        pass
                    elif detection.selected_modality is None:
                        raise RuntimeError("selected detection lacks a modality")
                    else:
                        request = request.with_resolved_modality(
                            detection.selected_modality
                        )
                elif isinstance(spec, TextCompareSpec):
                    request = request.with_resolved_modality("text")
                else:
                    request = request.with_resolved_modality("binary")

                selected_plugin: DiscoveredCapabilityV1 | None = None
                selected_builtin: CapabilityRecord | None = None
                prepared: _PreparedComparator | None = None

                def resolve() -> None:
                    nonlocal selected_plugin, selected_builtin, prepared
                    if detector_id is not None and detection_capability is None:
                        stages.record_attempts(
                            (
                                CapabilityAttempt(
                                    detector_id,
                                    None,
                                    "rejected",
                                    "plugin_not_found",
                                ),
                            )
                        )
                        raise CapabilityUnavailableError()
                    if comparator_id is not None and comparator_id not in {
                        "text",
                        "binary",
                    }:
                        selected_plugin = self.capability(comparator_id)
                        if selected_plugin is None:
                            stages.record_attempts(
                                (
                                    CapabilityAttempt(
                                        comparator_id,
                                        None,
                                        "rejected",
                                        "plugin_not_found",
                                    ),
                                )
                            )
                            raise CapabilityUnavailableError()
                        availability = self._probe(selected_plugin)
                        if not availability.available:
                            stages.record_attempts(
                                (
                                    CapabilityAttempt(
                                        comparator_id,
                                        selected_plugin.declaration.backend_id,
                                        "rejected",
                                        availability.reason_code,
                                    ),
                                )
                            )
                            raise PluginCapabilityUnavailableError(
                                reason_code=availability.reason_code
                                or "capability_unavailable"
                            )
                        stages.record_attempts((_selected_attempt(selected_plugin),))
                        resolved_spec = _resolved_plugin_spec(
                            spec, request.resolved_modality
                        )
                        prepared = self._prepare_comparator(
                            selected_plugin,
                            snapshots,
                            resolved_spec,
                            availability,
                        )
                        return
                    resolution = _CATALOG.resolve(request)
                    stages.record_attempts(resolution.attempts)
                    if resolution.selected is None:
                        raise CapabilityUnavailableError(
                            backend_missing=any(
                                item.reason_code == "backend_missing"
                                for item in resolution.attempts
                            )
                        )
                    if (
                        comparator_id is not None
                        and resolution.selected.capability_id != comparator_id
                    ):
                        raise CapabilityUnavailableError()
                    selected_builtin = resolution.selected

                stages.run(PipelineStage.RESOLVING, resolve)
                if selected_plugin is not None:
                    if prepared is None:
                        raise RuntimeError("plugin resolution lacks a prepared run")
                    hosted = self._execute_prepared(prepared, stages)
                    result = _plugin_result(
                        hosted,
                        inputs,
                        spec,
                        detector_provider=detector_provider,
                    )
                    diagnostics = hosted.facts.diagnostics
                else:
                    if selected_builtin is None:
                        raise RuntimeError("built-in resolution lacks a capability")
                    if isinstance(spec, TextCompareSpec):
                        raise RuntimeError(
                            "explicit text built-in execution uses the direct path"
                        )
                    completion = selected_builtin.handle.run(
                        snapshots[0], snapshots[1], spec, stages
                    )
                    result = _builtin_result_v2(
                        completion.result, detector_provider=detector_provider
                    )
                    diagnostics = completion.diagnostics
            except UnavailableError as error:
                return UnavailableOutcomeV2(
                    execution=_execution_v2(
                        self, stages.execution(()), terminal_reason=error.code
                    ),
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
                return FailedOutcomeV2(
                    execution=_execution_v2(
                        self, stages.execution(()), terminal_reason=error.code
                    ),
                    problem=ExecutionProblemV2(
                        error.code,
                        error.status_code,
                        error.stage,
                        str(error),
                        error.details,
                        error.retryable,
                    ),
                )
        return CompletedOutcomeV2(
            execution=_execution_v2(self, stages.execution(diagnostics)), result=result
        )

    def _detection_comparator_candidates(
        self, comparator_id: str | None
    ) -> tuple[tuple[Literal["text", "binary"], int, str, str], ...]:
        if comparator_id is not None and comparator_id not in {"text", "binary"}:
            capability = self.capability(comparator_id)
            if capability is None or capability.handle is None:
                return ()
            handle = cast(ComparatorHandleV1, capability.handle)
            backend = (
                capability.declaration.backend_id
                or capability.declaration.capability_id
            )
            return (
                (
                    handle.modality,
                    capability.declaration.priority,
                    capability.declaration.capability_id,
                    backend,
                ),
            )
        return tuple(
            (record.modality, record.priority, record.capability_id, record.backend_id)
            for record in _builtin_detection_records(comparator_id)
        )

    def _detection_capability_records(
        self, comparator_id: str | None
    ) -> tuple[CapabilityRecord, ...]:
        if comparator_id is not None and comparator_id not in {"text", "binary"}:
            capability = self.capability(comparator_id)
            if capability is None or capability.handle is None:
                return ()
            handle = cast(ComparatorHandleV1, capability.handle)
            if handle.modality not in ("text", "binary"):
                return ()
            declaration = capability.declaration
            return (
                CapabilityRecord(
                    capability_id=declaration.capability_id,
                    modality=handle.modality,
                    semantic_class="exact",
                    implementation_version=declaration.implementation_version,
                    backend_id=declaration.backend_id or declaration.capability_id,
                    backend_version=declaration.backend_version or "1",
                    priority=declaration.priority,
                    supported_source_kinds=frozenset(SourceKind),
                    supported_features=frozenset(),
                    handle=cast(ComparatorCapabilityHandle, handle),
                ),
            )
        return _builtin_detection_records(comparator_id)

    def _probe(self, capability: DiscoveredCapabilityV1) -> CapabilityAvailabilityV1:
        handle = capability.handle
        if handle is None:
            return CapabilityAvailabilityV1(False, reason_code="executor_missing")
        try:
            availability = handle.availability()
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except PluginUnavailableErrorV1 as error:
            return CapabilityAvailabilityV1(False, reason_code=error.reason_code)
        except PluginExecutionErrorV1 as error:
            raise PluginExecutionFailureError(stage=PipelineStage.RESOLVING) from error
        if not isinstance(availability, CapabilityAvailabilityV1):
            raise PluginExecutionFailureError(stage=PipelineStage.RESOLVING)
        declaration = capability.declaration
        if declaration.backend_id is not None and (
            availability.backend_id != declaration.backend_id
            or availability.backend_version != declaration.backend_version
        ):
            raise PluginExecutionFailureError(stage=PipelineStage.RESOLVING)
        return availability

    def _execute_comparator(
        self,
        capability: DiscoveredCapabilityV1,
        snapshots: tuple[SourceSnapshot, SourceSnapshot],
        spec: ResolvedPluginSpec,
        stages: StageRunner,
    ) -> HostedPluginComparison:
        prepared = self._prepare_comparator(capability, snapshots, spec)
        return self._execute_prepared(prepared, stages)

    def _prepare_comparator(
        self,
        capability: DiscoveredCapabilityV1,
        snapshots: tuple[SourceSnapshot, SourceSnapshot],
        spec: ResolvedPluginSpec,
        availability: CapabilityAvailabilityV1 | None = None,
    ) -> _PreparedComparator:
        if capability.declaration.kind is not CapabilityKind.COMPARATOR:
            raise PluginCapabilityUnavailableError(
                reason_code="capability_kind_mismatch"
            )
        if availability is None:
            availability = self._probe(capability)
        if not availability.available:
            raise PluginCapabilityUnavailableError(reason_code="backend_missing")
        handle = cast(ComparatorHandleV1, capability.handle)
        if handle.modality != spec.kind:
            raise PluginCapabilityUnavailableError(reason_code="modality_mismatch")
        try:
            source_stage = PipelineStage(handle.source_stage)
        except (TypeError, ValueError) as error:
            raise PluginExecutionFailureError(stage=PipelineStage.RESOLVING) from error
        if source_stage not in (
            PipelineStage.DECODING,
            PipelineStage.NORMALIZING,
            PipelineStage.ALIGNING,
            PipelineStage.COMPARING,
        ):
            raise PluginExecutionFailureError(stage=PipelineStage.RESOLVING)
        maximum = _maximum_input_bytes(spec)
        before = _HostedSourceService(
            snapshots[0], allowed_stage=source_stage, byte_budget=maximum
        )
        after = _HostedSourceService(
            snapshots[1], allowed_stage=source_stage, byte_budget=maximum
        )
        run = _invoke_plugin(
            PipelineStage.RESOLVING,
            lambda: handle.create_run(before, after, spec),
        )
        with self._run_lock:
            if any(previous is run for previous in self._used_runs):
                raise PluginExecutionFailureError(stage=PipelineStage.RESOLVING)
            self._used_runs.append(run)
        return _PreparedComparator(capability, run, before, after)

    def _execute_prepared(
        self, prepared: _PreparedComparator, stages: StageRunner
    ) -> HostedPluginComparison:
        capability = prepared.capability
        run = prepared.run
        before = prepared.before
        after = prepared.after
        methods: tuple[tuple[PipelineStage, Callable[[], object]], ...] = (
            (PipelineStage.DECODING, run.decode),
            (PipelineStage.NORMALIZING, run.normalize),
            (PipelineStage.ALIGNING, run.align),
            (PipelineStage.COMPARING, run.compare),
        )
        for stage, method in methods:
            before.activate(stage)
            after.activate(stage)
            try:
                stages.run(
                    stage,
                    partial(_invoke_plugin, stage, method),
                )
            finally:
                before.activate(None)
                after.activate(None)
        before.activate(PipelineStage.AGGREGATING)
        after.activate(PipelineStage.AGGREGATING)
        try:
            facts = stages.run(
                PipelineStage.AGGREGATING,
                lambda: _aggregate_plugin(run.aggregate, capability),
            )
        finally:
            before.activate(None)
            after.activate(None)
        return HostedPluginComparison(
            capability, facts, (before.bytes_used, after.bytes_used)
        )

    def _detect(
        self,
        capability: DiscoveredCapabilityV1,
        snapshots: tuple[SourceSnapshot, SourceSnapshot],
        spec: AutoCompareSpec,
        comparator_candidates: tuple[
            tuple[Literal["text", "binary"], int, str, str], ...
        ],
    ) -> DetectionRecord:
        if capability.declaration.kind is not CapabilityKind.DETECTOR:
            raise PluginCapabilityUnavailableError(
                reason_code="capability_kind_mismatch"
            )
        if not self._probe(capability).available:
            raise PluginCapabilityUnavailableError(reason_code="backend_missing")
        handle = cast(DetectorHandleV1, capability.handle)
        maximum = min(spec.limits.max_detection_bytes, spec.limits.max_input_bytes)
        roles: tuple[Literal["before", "after"], Literal["before", "after"]] = (
            "before",
            "after",
        )
        records = tuple(
            self._detect_source(handle, snapshot, role, maximum, capability)
            for snapshot, role in zip(snapshots, roles, strict=True)
        )
        before, after = cast(
            tuple[SourceDetectionRecord, SourceDetectionRecord], records
        )
        pairs = _plugin_pair_candidates(before, after, comparator_candidates)
        disposition: Literal["selected", "no_match", "ambiguous"]
        selected: Literal["text", "binary"] | None
        if not pairs or pairs[0].confidence < spec.minimum_confidence:
            disposition, selected = "no_match", None
        elif (
            len(pairs) > 1
            and pairs[0].confidence - pairs[1].confidence < spec.ambiguity_margin
        ):
            disposition, selected = "ambiguous", None
        else:
            disposition, selected = "selected", pairs[0].modality_id
        return DetectionRecord(
            detector_id=capability.declaration.capability_id,
            detector_version=capability.declaration.implementation_version,
            maximum_bytes=maximum,
            minimum_confidence=spec.minimum_confidence,
            ambiguity_margin=spec.ambiguity_margin,
            sources=(before, after),
            pair_candidates=pairs,
            disposition=disposition,
            selected_modality=selected,
        )

    def _detect_source(
        self,
        handle: DetectorHandleV1,
        snapshot: SourceSnapshot,
        role: Literal["before", "after"],
        maximum: int,
        capability: DiscoveredCapabilityV1,
    ) -> SourceDetectionRecord:
        prefix = snapshot.read_prefix(maximum, stage=PipelineStage.DETECTING)
        request = DetectorInputV1(
            snapshot.source_kind,
            prefix,
            snapshot.size_bytes <= len(prefix),
            maximum,
        )
        returned = _invoke_plugin(
            PipelineStage.DETECTING, lambda: handle.detect(request)
        )
        if not isinstance(returned, tuple):
            raise PluginExecutionFailureError(stage=PipelineStage.DETECTING)
        try:
            candidates = tuple(
                _validated_detector_candidate(item, capability) for item in returned
            )
            return SourceDetectionRecord(role, candidates)
        except (TypeError, ValueError) as error:
            raise PluginExecutionFailureError(stage=PipelineStage.DETECTING) from error


def _invoke_plugin[T](stage: PipelineStage, operation: Callable[[], T]) -> T:
    try:
        return operation()
    except (KeyboardInterrupt, SystemExit, MemoryError):
        raise
    except PluginResourceLimitErrorV1 as error:
        raise ResourceLimitError(
            "A plugin exhausted a deterministic resource limit.", stage=stage
        ) from error
    except (PluginExecutionErrorV1, PluginUnavailableErrorV1) as error:
        raise PluginExecutionFailureError(stage=stage) from error


def _aggregate_plugin(
    operation: Callable[[], object], capability: DiscoveredCapabilityV1
) -> PluginComparisonV1:
    returned = _invoke_plugin(PipelineStage.AGGREGATING, operation)
    if not isinstance(returned, PluginComparisonV1):
        raise PluginExecutionFailureError(stage=PipelineStage.AGGREGATING)
    if returned.implementation_version != capability.declaration.implementation_version:
        raise PluginExecutionFailureError(stage=PipelineStage.AGGREGATING)
    plugin_id = capability.plugin.manifest.plugin_id
    for change in returned.changes.items:
        if isinstance(change, ExtensionChange) and (
            change.plugin_id != plugin_id or not change.kind.startswith(f"{plugin_id}.")
        ):
            raise PluginExecutionFailureError(stage=PipelineStage.AGGREGATING)
    for diagnostic in returned.diagnostics:
        if not _safe_diagnostic_text(diagnostic.message) or not _safe_json_strings(
            diagnostic.details
        ):
            raise PluginExecutionFailureError(stage=PipelineStage.AGGREGATING)
        try:
            Diagnostic(
                diagnostic.code,
                diagnostic.severity,
                diagnostic.stage,
                diagnostic.message,
                dict(diagnostic.details),
            )
        except ValueError as error:
            raise PluginExecutionFailureError(
                stage=PipelineStage.AGGREGATING
            ) from error
    try:
        placeholder_inputs = (
            InputProvenance("before", SourceKind.BYTES, 0, "0" * 64),
            InputProvenance("after", SourceKind.BYTES, 0, "0" * 64),
        )
        candidate = DiffResult(
            returned.relation,
            returned.verdict,
            returned.fidelity,
            returned.summary,
            returned.changes,
            returned.metrics,
            returned.evaluations,
            returned.artifacts,
            ComparisonProvenance(
                placeholder_inputs,
                {},
                returned.transformations,
                capability.declaration.capability_id,
                capability.declaration.implementation_version,
                returned.algorithm_id,
                returned.implementation_version,
                resources=returned.resources,
            ),
        )
        _result_from_data(_result_to_data(candidate))
    except (TypeError, ValueError) as error:
        raise PluginExecutionFailureError(stage=PipelineStage.AGGREGATING) from error
    return returned


def _validated_detector_candidate(
    value: object, capability: DiscoveredCapabilityV1
) -> DetectionCandidate:
    if not isinstance(value, DetectorCandidateV1):
        raise TypeError("invalid detector candidate")
    return DetectionCandidate(
        value.modality_id,
        value.confidence,
        capability.declaration.capability_id,
        capability.declaration.implementation_version,
        capability.declaration.priority,
        value.evidence_codes,
        dict(value.evidence_counts),
    )


def _plugin_pair_candidates(
    before: SourceDetectionRecord,
    after: SourceDetectionRecord,
    comparator_candidates: tuple[tuple[Literal["text", "binary"], int, str, str], ...],
) -> tuple[PairDetectionCandidate, ...]:
    before_by_modality = {item.modality_id: item for item in before.candidates}
    after_by_modality = {item.modality_id: item for item in after.candidates}
    pairs = []
    for modality, priority, capability_id, backend_id in comparator_candidates:
        before_candidate = before_by_modality.get(modality)
        after_candidate = after_by_modality.get(modality)
        if before_candidate is None or after_candidate is None:
            continue
        pairs.append(
            PairDetectionCandidate(
                modality,
                min(before_candidate.confidence, after_candidate.confidence),
                before_candidate.confidence,
                after_candidate.confidence,
                min(before_candidate.priority, after_candidate.priority),
                priority,
                capability_id,
                backend_id,
            )
        )
    return tuple(
        sorted(
            pairs,
            key=lambda item: (
                -item.confidence,
                item.detector_priority,
                item.capability_priority,
                item.modality_id,
                item.capability_id,
                item.backend_id,
            ),
        )
    )


def _maximum_input_bytes(spec: ResolvedPluginSpec) -> int:
    return spec.limits.max_input_bytes


def _safe_label(label: str | None) -> str | None:
    if label is None or "/" in label or "\\" in label:
        return None
    try:
        encoded = label.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return None
    if len(encoded) > 1024 or any(ord(character) < 0x20 for character in label):
        return None
    return label


def _safe_diagnostic_text(value: str) -> bool:
    return (
        "/" not in value
        and "\\" not in value
        and len(value.encode("utf-8", errors="strict")) <= 1024
        and not any(ord(character) < 0x20 for character in value)
    )


def _safe_json_strings(value: object) -> bool:
    if isinstance(value, str):
        return _safe_diagnostic_text(value)
    if isinstance(value, list):
        return all(_safe_json_strings(item) for item in value)
    if isinstance(value, dict):
        return all(
            _safe_diagnostic_text(key) and _safe_json_strings(item)
            for key, item in value.items()
        )
    return value is None or isinstance(value, (bool, int, float))


def _validate_composed_request(
    before: Source,
    after: Source,
    spec: CompareSpec,
    detector_id: str | None,
) -> None:
    if not isinstance(spec, (AutoCompareSpec, TextCompareSpec, BinaryCompareSpec)):
        raise TypeError("unsupported comparison specification")
    if not isinstance(before, (PathSource, BytesSource, TextSource)) or not isinstance(
        after, (PathSource, BytesSource, TextSource)
    ):
        raise SourceTypeUnsupportedError()
    if detector_id is not None and not isinstance(spec, AutoCompareSpec):
        raise ValueError("a detector can be pinned only for an auto comparison")


def _snapshot_inputs(
    stack: ExitStack,
    before: Source,
    after: Source,
    max_input_bytes: int,
) -> tuple[
    tuple[SourceSnapshot, SourceSnapshot],
    tuple[InputProvenance, InputProvenance],
]:
    snapshots = (
        stack.enter_context(
            open_source_snapshot(before, max_input_bytes=max_input_bytes)
        ),
        stack.enter_context(
            open_source_snapshot(after, max_input_bytes=max_input_bytes)
        ),
    )
    roles: tuple[Literal["before", "after"], Literal["before", "after"]] = (
        "before",
        "after",
    )
    inputs = tuple(
        _snapshot_provenance(snapshot, role)
        for snapshot, role in zip(snapshots, roles, strict=True)
    )
    return snapshots, cast(tuple[InputProvenance, InputProvenance], inputs)


def _snapshot_provenance(
    snapshot: SourceSnapshot, role: Literal["before", "after"]
) -> InputProvenance:
    digest = sha256()
    for chunk in snapshot.iter_chunks(64 * 1024, stage=PipelineStage.SOURCING):
        digest.update(chunk)
    return InputProvenance(
        role=role,
        source_kind=snapshot.source_kind,
        size_bytes=snapshot.size_bytes,
        sha256=digest.hexdigest(),
        label=snapshot.label,
    )


def _builtin_detection_records(
    comparator_id: str | None,
) -> tuple[CapabilityRecord, ...]:
    records = tuple(
        record
        for record in _CATALOG.records_for_detection(
            request_from_spec(AutoCompareSpec(), (SourceKind.BYTES, SourceKind.BYTES))
        )
        if comparator_id is None or record.capability_id == comparator_id
    )
    return records


def _missing_detector_record(
    detector_id: str, spec: AutoCompareSpec
) -> DetectionRecord:
    maximum = min(spec.limits.max_detection_bytes, spec.limits.max_input_bytes)
    return DetectionRecord(
        detector_id=detector_id,
        detector_version="unavailable",
        maximum_bytes=maximum,
        minimum_confidence=spec.minimum_confidence,
        ambiguity_margin=spec.ambiguity_margin,
        sources=(
            SourceDetectionRecord("before", ()),
            SourceDetectionRecord("after", ()),
        ),
        pair_candidates=(),
        disposition="no_match",
        selected_modality=None,
    )


def _resolved_plugin_spec(
    spec: CompareSpec, modality: Literal["text", "binary"] | None
) -> ResolvedPluginSpec:
    if isinstance(spec, (TextCompareSpec, BinaryCompareSpec)):
        return spec
    if modality == "text":
        return TextCompareSpec(
            encoding=spec.text.encoding,
            newline=spec.text.newline,
            context_lines=spec.text.context_lines,
            limits=type(TextCompareSpec().limits)(
                max_input_bytes=spec.limits.max_input_bytes,
                max_input_lines=spec.limits.max_input_lines,
                max_encoded_line_bytes=spec.limits.max_encoded_line_bytes,
                max_myers_work=spec.limits.max_myers_work,
                max_change_items=spec.limits.max_change_items,
                max_change_payload_bytes=spec.limits.max_change_payload_bytes,
            ),
        )
    if modality == "binary":
        return BinaryCompareSpec(
            limits=type(BinaryCompareSpec().limits)(
                max_input_bytes=spec.limits.max_input_bytes,
                chunk_bytes=spec.limits.binary_chunk_bytes,
                max_change_items=spec.limits.max_change_items,
                max_change_payload_bytes=spec.limits.max_change_payload_bytes,
            )
        )
    raise RuntimeError("auto comparison has no resolved modality")


def _provider_identity(capability: DiscoveredCapabilityV1) -> ProviderIdentity:
    plugin = capability.plugin
    return ProviderIdentity(
        plugin_id=plugin.manifest.plugin_id,
        plugin_version=plugin.manifest.plugin_version,
        distribution_name=plugin.entry_point.distribution_name,
        distribution_version=plugin.entry_point.distribution_version,
        manifest_schema_version=plugin.manifest.manifest_schema_version,
        api_major=plugin.manifest.api_major,
        negotiated_api_minor=plugin.negotiated_api_minor,
        negotiated_host_features=plugin.negotiated_host_features,
    )


def _host_record(host: PluginHost) -> PluginHostExecutionRecord:
    providers = tuple(
        ProviderIdentity(
            plugin_id=plugin.manifest.plugin_id,
            plugin_version=plugin.manifest.plugin_version,
            distribution_name=plugin.entry_point.distribution_name,
            distribution_version=plugin.entry_point.distribution_version,
            manifest_schema_version=plugin.manifest.manifest_schema_version,
            api_major=plugin.manifest.api_major,
            negotiated_api_minor=plugin.negotiated_api_minor,
            negotiated_host_features=plugin.negotiated_host_features,
        )
        for plugin in host.catalog.plugins
    )
    return PluginHostExecutionRecord(host.catalog.enabled_plugin_ids, providers)


def _selected_attempt(capability: DiscoveredCapabilityV1) -> CapabilityAttempt:
    return CapabilityAttempt(
        capability.declaration.capability_id,
        capability.declaration.backend_id,
        "selected",
    )


def _attempt_v2(
    host: PluginHost, attempt: CapabilityAttempt | CapabilityAttemptV2
) -> CapabilityAttemptV2:
    if isinstance(attempt, CapabilityAttemptV2):
        return attempt
    plugin_capability = host.capability(attempt.capability_id)
    if plugin_capability is not None:
        declaration = plugin_capability.declaration
        return CapabilityAttemptV2(
            attempt.capability_id,
            attempt.backend_id,
            attempt.disposition,
            attempt.reason_code,
            declaration.implementation_version,
            declaration.backend_version,
            _provider_identity(plugin_capability),
        )
    builtin = next(
        (
            record
            for record in _CATALOG.records_for_detection(
                request_from_spec(
                    AutoCompareSpec(), (SourceKind.BYTES, SourceKind.BYTES)
                )
            )
            if record.capability_id == attempt.capability_id
        ),
        None,
    )
    return CapabilityAttemptV2(
        attempt.capability_id,
        attempt.backend_id,
        attempt.disposition,
        attempt.reason_code,
        None if builtin is None else builtin.implementation_version,
        None if builtin is None else builtin.backend_version,
        None,
    )


def _execution_v2(
    host: PluginHost,
    record: ExecutionRecord,
    *,
    terminal_reason: str | None = None,
) -> ExecutionRecordV2:
    attempts = [_attempt_v2(host, attempt) for attempt in record.attempts]
    if terminal_reason is not None and record.stages:
        disposition: Literal["unavailable", "failed"] = (
            "unavailable"
            if record.stages[-1].disposition is StageDisposition.UNAVAILABLE
            else "failed"
        )
        for index in range(len(attempts) - 1, -1, -1):
            if attempts[index].disposition == "selected":
                attempts[index] = replace(
                    attempts[index],
                    disposition=disposition,
                    reason_code=terminal_reason,
                )
                break
            if (
                disposition == "unavailable"
                and attempts[index].disposition == "rejected"
            ):
                attempts[index] = replace(
                    attempts[index],
                    disposition="unavailable",
                    reason_code=attempts[index].reason_code or terminal_reason,
                )
                break
    return ExecutionRecordV2(
        started_at=record.started_at,
        finished_at=record.finished_at,
        duration_ns=record.duration_ns,
        stages=record.stages,
        attempts=tuple(attempts),
        diagnostics=record.diagnostics,
        last_completed_stage=record.last_completed_stage,
        detection=record.detection,
        plugin_host=_host_record(host),
    )


def _plugin_result(
    hosted: HostedPluginComparison,
    inputs: tuple[InputProvenance, InputProvenance],
    spec: CompareSpec,
    *,
    detector_provider: ProviderIdentity | None,
) -> DiffResult:
    facts = hosted.facts
    usage_names = {resource.name for resource in facts.resources}
    host_names = ("host.plugin_before_source_bytes", "host.plugin_after_source_bytes")
    if usage_names.intersection(host_names):
        raise PluginExecutionFailureError(stage=PipelineStage.AGGREGATING)
    resources = (
        *facts.resources,
        ResourceUsage(
            host_names[0], spec.limits.max_input_bytes, hosted.source_bytes_used[0]
        ),
        ResourceUsage(
            host_names[1], spec.limits.max_input_bytes, hosted.source_bytes_used[1]
        ),
    )
    capability = hosted.capability
    provenance = ComparisonProvenanceV2(
        inputs=inputs,
        spec=spec_to_data(spec),
        transformations=facts.transformations,
        comparator_id=capability.declaration.capability_id,
        comparator_version=capability.declaration.implementation_version,
        algorithm_id=facts.algorithm_id,
        implementation_version=facts.implementation_version,
        resources=resources,
        provider=_provider_identity(capability),
        detector_provider=detector_provider,
    )
    return DiffResult(
        relation=facts.relation,
        verdict=facts.verdict,
        fidelity=facts.fidelity,
        summary=facts.summary,
        changes=facts.changes,
        metrics=facts.metrics,
        evaluations=facts.evaluations,
        artifacts=facts.artifacts,
        provenance=provenance,
    )


def _builtin_result_v2(
    result: DiffResult, *, detector_provider: ProviderIdentity | None
) -> DiffResult:
    provenance = result.provenance
    return DiffResult(
        relation=result.relation,
        verdict=result.verdict,
        fidelity=result.fidelity,
        summary=result.summary,
        changes=result.changes,
        metrics=result.metrics,
        evaluations=result.evaluations,
        artifacts=result.artifacts,
        provenance=ComparisonProvenanceV2(
            inputs=provenance.inputs,
            spec=provenance.spec,
            transformations=provenance.transformations,
            comparator_id=provenance.comparator_id,
            comparator_version=provenance.comparator_version,
            algorithm_id=provenance.algorithm_id,
            implementation_version=provenance.implementation_version,
            seeds=provenance.seeds,
            resources=provenance.resources,
            detector_provider=detector_provider,
        ),
    )


def _bind_host_context(host: PluginHost, outcome: CompareOutcomeV2) -> CompareOutcomeV2:
    execution = _execution_v2(host, outcome.execution)
    if isinstance(outcome, CompletedOutcomeV2):
        return CompletedOutcomeV2(execution=execution, result=outcome.result)
    if isinstance(outcome, UnavailableOutcomeV2):
        return UnavailableOutcomeV2(execution=execution, problem=outcome.problem)
    return FailedOutcomeV2(execution=execution, problem=outcome.problem)
