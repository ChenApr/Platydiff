"""Built-in comparator adapters for the core capability-handle boundary."""

from __future__ import annotations

from dataclasses import dataclass

from platydiff.comparators.binary.comparator import compare_binary_snapshots
from platydiff.comparators.text.comparator import compare_text_snapshots
from platydiff.core._sources import SourceSnapshot
from platydiff.core.models import AutoCompareSpec, BinaryCompareSpec, PipelineStage
from platydiff.core.pipeline import ComparisonCompletion, StageRunner


@dataclass(frozen=True, slots=True)
class BuiltinBinaryComparatorHandle:
    """Adapt the built-in binary comparator to the complete stage lifecycle."""

    def run(
        self,
        before: SourceSnapshot,
        after: SourceSnapshot,
        spec: AutoCompareSpec | BinaryCompareSpec,
        stages: StageRunner,
    ) -> ComparisonCompletion:
        stages.run(PipelineStage.DECODING, lambda: None)
        stages.run(PipelineStage.NORMALIZING, lambda: None)
        stages.run(PipelineStage.ALIGNING, lambda: None)
        completion = stages.run(
            PipelineStage.COMPARING,
            lambda: compare_binary_snapshots(before, after, spec),
        )
        return stages.run(PipelineStage.AGGREGATING, lambda: completion)


@dataclass(frozen=True, slots=True)
class BuiltinTextComparatorHandle:
    """Adapt the built-in text comparator to the capability-handle boundary."""

    def run(
        self,
        before: SourceSnapshot,
        after: SourceSnapshot,
        spec: AutoCompareSpec | BinaryCompareSpec,
        stages: StageRunner,
    ) -> ComparisonCompletion:
        if not isinstance(spec, AutoCompareSpec):
            raise RuntimeError("binary intent cannot resolve to text")
        return compare_text_snapshots(before, after, spec, stages)
