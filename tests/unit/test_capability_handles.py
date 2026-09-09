"""Tests for the typed capability execution boundary."""

from __future__ import annotations

import ast
from pathlib import Path

from platydiff import BinaryCompareSpec, BytesSource, CompletedOutcome, compare
from platydiff.comparators._adapters import BuiltinBinaryComparatorHandle
from platydiff.core._capabilities import ComparatorCapabilityHandle


def test_builtin_adapter_satisfies_typed_handle() -> None:
    handle: ComparatorCapabilityHandle = BuiltinBinaryComparatorHandle()
    assert handle is not None


def test_snapshot_pipeline_does_not_import_concrete_comparators() -> None:
    pipeline_path = Path(__file__).parents[2] / "platydiff" / "core" / "pipeline.py"
    tree = ast.parse(pipeline_path.read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not any(
        module.startswith("platydiff.comparators") for module in imported_modules
    )


def test_default_binary_comparison_remains_operational() -> None:
    outcome = compare(BytesSource(b"a"), BytesSource(b"b"), BinaryCompareSpec())
    assert isinstance(outcome, CompletedOutcome)
