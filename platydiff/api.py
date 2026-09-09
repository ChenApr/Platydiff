"""Public comparison entry point and private built-in composition."""

from __future__ import annotations

from platydiff.comparators._adapters import (
    BuiltinBinaryComparatorHandle,
    BuiltinTextComparatorHandle,
)
from platydiff.comparators.text.comparator import compare_text
from platydiff.core._capabilities import CapabilityCatalog, CapabilityRecord
from platydiff.core._registry import InternalRegistry
from platydiff.core.models import (
    AutoCompareSpec,
    BinaryCompareSpec,
    CompareOutcome,
    CompareSpec,
    Source,
    SourceKind,
    TextCompareSpec,
)
from platydiff.core.pipeline import run_comparison, run_snapshot_comparison

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


def compare(before: Source, after: Source, spec: CompareSpec) -> CompareOutcome:
    """Compare two sources using the caller's explicit specification."""
    if isinstance(spec, TextCompareSpec):
        return run_comparison(before, after, spec, _REGISTRY.resolve)
    if isinstance(spec, (AutoCompareSpec, BinaryCompareSpec)):
        return run_snapshot_comparison(before, after, spec, _CATALOG)
    raise TypeError("unsupported comparison specification")
