"""Public comparison entry point and private built-in composition."""

from __future__ import annotations

from typing import overload

from platydiff.comparators._adapters import (
    BuiltinBinaryComparatorHandle,
    BuiltinTextComparatorHandle,
)
from platydiff.comparators.json.comparator import compare_json_snapshots
from platydiff.comparators.text.comparator import compare_text
from platydiff.core._capabilities import CapabilityCatalog, CapabilityRecord
from platydiff.core._registry import InternalRegistry
from platydiff.core.models import (
    AnyCompareOutcome,
    AutoCompareSpec,
    BinaryCompareSpec,
    CompareOutcome,
    CompareOutcomeV3,
    CompareSpec,
    CompareSpecV3,
    JsonCompareSpec,
    Source,
    SourceKind,
    TextCompareSpec,
)
from platydiff.core.pipeline import (
    run_comparison,
    run_json_comparison,
    run_snapshot_comparison,
)

_REGISTRY = InternalRegistry()
_REGISTRY.register("text", compare_text)
_CATALOG = CapabilityCatalog()
_SOURCE_KINDS = frozenset(SourceKind)
_CATALOG.register(
    CapabilityRecord(
        "text",
        "text",
        "exact",
        "1",
        "stdlib",
        "1",
        0,
        _SOURCE_KINDS,
        frozenset(),
        BuiltinTextComparatorHandle(),
    )
)
_CATALOG.register(
    CapabilityRecord(
        "binary",
        "binary",
        "exact",
        "1",
        "stdlib",
        "1",
        0,
        _SOURCE_KINDS,
        frozenset(),
        BuiltinBinaryComparatorHandle(),
    )
)


@overload
def compare(before: Source, after: Source, spec: CompareSpec) -> CompareOutcome: ...


@overload
def compare(
    before: Source, after: Source, spec: JsonCompareSpec
) -> CompareOutcomeV3: ...


def compare(before: Source, after: Source, spec: CompareSpecV3) -> AnyCompareOutcome:
    """Compare two sources using the caller's explicit specification."""
    if isinstance(spec, TextCompareSpec):
        return run_comparison(before, after, spec, _REGISTRY.resolve)
    if isinstance(spec, (AutoCompareSpec, BinaryCompareSpec)):
        return run_snapshot_comparison(before, after, spec, _CATALOG)
    if isinstance(spec, JsonCompareSpec):
        return run_json_comparison(before, after, spec, compare_json_snapshots)
    raise TypeError("unsupported comparison specification")
