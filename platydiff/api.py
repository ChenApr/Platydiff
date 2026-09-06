"""Public comparison entry point and private built-in composition."""

from __future__ import annotations

from platydiff.comparators.text.comparator import compare_text
from platydiff.core._registry import InternalRegistry
from platydiff.core.models import CompareOutcome, CompareSpec, Source
from platydiff.core.pipeline import run_comparison

_REGISTRY = InternalRegistry()
_REGISTRY.register("text", compare_text)


def compare(before: Source, after: Source, spec: CompareSpec) -> CompareOutcome:
    """Compare two sources using the caller's explicit specification."""
    executor = _REGISTRY.resolve(spec)
    return run_comparison(before, after, spec, executor)
