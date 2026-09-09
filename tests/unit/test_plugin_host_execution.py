"""Host-owned detector and comparator lifecycle tests."""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass, field
from itertools import count
from typing import cast

import pytest

from platydiff import (
    AutoCompareSpec,
    BytesSource,
    CompletedOutcome,
    TextCompareSpec,
    TextSource,
    compare,
)
from platydiff.core._sources import open_source_snapshot
from platydiff.core.models import JsonObject, PipelineStage
from platydiff.core.pipeline import StageRunner
from platydiff.plugin_sdk import (
    CapabilityAvailabilityV1,
    CapabilityDeclarationV1,
    CapabilityKind,
    DetectorCandidateV1,
    DetectorInputV1,
    PluginComparisonV1,
    PluginExecutionErrorV1,
    PluginManifestV1,
    SourceServiceV1,
)
from platydiff.plugins import (
    DiscoveredCapabilityV1,
    LoadedPluginV1,
    PluginCatalogV1,
    PluginEntryPointV1,
    PluginHost,
)
from platydiff.plugins._host import PluginExecutionFailureError

PLUGIN_ID = "org.example.scidiff"


def _clock() -> tuple[str, int]:
    return "2026-09-09T00:00:00Z", next(_CLOCK_VALUES)


_CLOCK_VALUES = count()


def _facts() -> PluginComparisonV1:
    outcome = compare(TextSource("same"), TextSource("same"), TextCompareSpec())
    assert isinstance(outcome, CompletedOutcome)
    result = outcome.result
    return PluginComparisonV1(
        relation=result.relation,
        verdict=result.verdict,
        fidelity=result.fidelity,
        summary=result.summary,
        changes=result.changes,
        metrics=result.metrics,
        evaluations=result.evaluations,
        artifacts=result.artifacts,
        transformations=result.provenance.transformations,
        algorithm_id=result.provenance.algorithm_id,
        implementation_version="1",
        resources=result.provenance.resources,
    )


@dataclass
class _Run:
    before: SourceServiceV1
    after: SourceServiceV1
    facts: PluginComparisonV1
    events: list[str]

    def decode(self) -> None:
        self.events.append("decode")
        assert self.before.read() == b"same"
        assert self.after.read() == b"same"

    def normalize(self) -> None:
        self.events.append("normalize")

    def align(self) -> None:
        self.events.append("align")

    def compare(self) -> None:
        self.events.append("compare")

    def aggregate(self) -> PluginComparisonV1:
        self.events.append("aggregate")
        return self.facts


@dataclass
class _ComparatorHandle:
    capability_id: str = f"{PLUGIN_ID}.text_exact"
    modality: str = "text"
    source_stage: str = "decoding"
    events: list[str] = field(default_factory=list)

    def availability(self) -> CapabilityAvailabilityV1:
        return CapabilityAvailabilityV1(True, f"{PLUGIN_ID}.stdlib", "1")

    def create_run(
        self,
        before: SourceServiceV1,
        after: SourceServiceV1,
        spec: TextCompareSpec,
    ) -> _Run:
        assert isinstance(spec, TextCompareSpec)
        return _Run(before, after, _facts(), self.events)


@dataclass
class _DetectorHandle:
    capability_id: str = f"{PLUGIN_ID}.text_binary_detector"
    seen: list[DetectorInputV1] = field(default_factory=list)

    def availability(self) -> CapabilityAvailabilityV1:
        return CapabilityAvailabilityV1(True)

    def detect(self, source: DetectorInputV1) -> tuple[DetectorCandidateV1, ...]:
        self.seen.append(source)
        counts: JsonObject = {
            "inspected_bytes": len(source.prefix),
            "nul_count": source.prefix.count(0),
            "non_ascii_byte_count": 0,
            "pending_utf8_bytes": 0,
            "disallowed_control_count": 0,
        }
        return (DetectorCandidateV1("text", 900, ("ascii",), counts),)


def _capability(
    handle: object, kind: CapabilityKind, *, backend: bool = False
) -> tuple[PluginHost, DiscoveredCapabilityV1]:
    capability_id = cast(str, handle.capability_id)  # type: ignore[attr-defined]
    declaration = CapabilityDeclarationV1(
        capability_id,
        kind,
        "1",
        f"{PLUGIN_ID}.stdlib" if backend else None,
        "1" if backend else None,
    )
    manifest = PluginManifestV1(
        1,
        PLUGIN_ID,
        "1",
        1,
        1,
        1,
        ("host.execution.v1",),
        (declaration,),
        "Apache-2.0",
        (handle,),  # type: ignore[arg-type]
    )
    entry_point = PluginEntryPointV1(
        PLUGIN_ID,
        "platydiff.plugins.v1",
        "example_plugin:manifest",
        "example-plugin",
        "1",
    )
    plugin = LoadedPluginV1(entry_point, manifest, 1, ("host.execution.v1",))
    capability = DiscoveredCapabilityV1(
        plugin, declaration, manifest.capability_handles[0]
    )
    catalog = PluginCatalogV1(
        (PLUGIN_ID,), (entry_point,), (plugin,), (capability,), ()
    )
    return PluginHost(catalog), capability


def test_host_invokes_fresh_comparator_run_once_in_fixed_order() -> None:
    handle = _ComparatorHandle()
    host, capability = _capability(handle, CapabilityKind.COMPARATOR, backend=True)
    stages = StageRunner(_clock)
    with ExitStack() as stack:
        stages.run(PipelineStage.VALIDATING, lambda: None)
        snapshots = stages.run(
            PipelineStage.SOURCING,
            lambda: (
                stack.enter_context(
                    open_source_snapshot(TextSource("same"), max_input_bytes=10)
                ),
                stack.enter_context(
                    open_source_snapshot(TextSource("same"), max_input_bytes=10)
                ),
            ),
        )
        stages.run(PipelineStage.RESOLVING, lambda: capability)
        hosted = host._execute_comparator(
            capability,
            snapshots,
            TextCompareSpec(),
            stages,
        )
    assert handle.events == ["decode", "normalize", "align", "compare", "aggregate"]
    assert hosted.source_bytes_used == (4, 4)
    assert [record.stage.value for record in stages.execution(()).stages] == [
        "validating",
        "sourcing",
        "resolving",
        "decoding",
        "normalizing",
        "aligning",
        "comparing",
        "aggregating",
    ]


def test_host_gives_detector_only_the_bounded_prefix() -> None:
    handle = _DetectorHandle()
    host, capability = _capability(handle, CapabilityKind.DETECTOR)
    spec = AutoCompareSpec()
    spec = AutoCompareSpec(
        text=spec.text,
        minimum_confidence=spec.minimum_confidence,
        ambiguity_margin=spec.ambiguity_margin,
        limits=type(spec.limits)(max_input_bytes=10, max_detection_bytes=2),
    )
    with ExitStack() as stack:
        snapshots = (
            stack.enter_context(
                open_source_snapshot(BytesSource(b"abcd"), max_input_bytes=10)
            ),
            stack.enter_context(
                open_source_snapshot(BytesSource(b"efgh"), max_input_bytes=10)
            ),
        )
        detection = host._detect(
            capability,
            snapshots,
            spec,
            (("text", 0, "text", "stdlib"),),
        )
    assert [item.prefix for item in handle.seen] == [b"ab", b"ef"]
    assert [item.reached_eof for item in handle.seen] == [False, False]
    assert detection.detector_id == handle.capability_id
    assert detection.selected_modality == "text"


def test_known_plugin_failure_is_mapped_without_exception_text() -> None:
    class _FailingRun(_Run):
        def compare(self) -> None:
            raise PluginExecutionErrorV1("secret /private/path")

    class _FailingHandle(_ComparatorHandle):
        def create_run(
            self,
            before: SourceServiceV1,
            after: SourceServiceV1,
            spec: TextCompareSpec,
        ) -> _Run:
            return _FailingRun(before, after, _facts(), self.events)

    host, capability = _capability(
        _FailingHandle(), CapabilityKind.COMPARATOR, backend=True
    )
    stages = StageRunner(_clock)
    with ExitStack() as stack:
        stages.run(PipelineStage.VALIDATING, lambda: None)
        snapshots = stages.run(
            PipelineStage.SOURCING,
            lambda: (
                stack.enter_context(
                    open_source_snapshot(TextSource("same"), max_input_bytes=10)
                ),
                stack.enter_context(
                    open_source_snapshot(TextSource("same"), max_input_bytes=10)
                ),
            ),
        )
        stages.run(PipelineStage.RESOLVING, lambda: capability)
        with pytest.raises(PluginExecutionFailureError) as raised:
            host._execute_comparator(
                capability,
                snapshots,
                TextCompareSpec(),
                stages,
            )
    assert raised.value.stage is PipelineStage.COMPARING
    assert "secret" not in str(raised.value)
