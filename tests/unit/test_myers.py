"""Correctness, determinism, budget, and memory tests for Myers."""

from __future__ import annotations

import importlib
import itertools
import tracemalloc
from typing import Protocol

import pytest

from platydiff.comparators.text.models import EditOperation, TextLine
from platydiff.comparators.text.myers import shortest_edit_script
from platydiff.core.problems import CompareResourceLimitError


class RegionLike(Protocol):
    before_start: int
    after_start: int


def text_lines(*values: str) -> tuple[TextLine, ...]:
    return tuple(TextLine(value, "\n") for value in values)


def edit_distance(operations: tuple[EditOperation, ...]) -> int:
    return sum(operation.kind != "equal" for operation in operations)


def reconstruct(
    before: tuple[TextLine, ...], operations: tuple[EditOperation, ...]
) -> tuple[TextLine, ...]:
    before_cursor = 0
    rebuilt: list[TextLine] = []
    for operation in operations:
        if operation.kind == "equal":
            assert operation.before_index == before_cursor
            assert before[before_cursor] == operation.line
            rebuilt.append(operation.line)
            before_cursor += 1
        elif operation.kind == "delete":
            assert operation.before_index == before_cursor
            assert before[before_cursor] == operation.line
            before_cursor += 1
        else:
            rebuilt.append(operation.line)
    assert before_cursor == len(before)
    return tuple(rebuilt)


def lcs_edit_distance(before: tuple[TextLine, ...], after: tuple[TextLine, ...]) -> int:
    previous = [0] * (len(after) + 1)
    for before_line in before:
        current = [0]
        for index, after_line in enumerate(after, 1):
            if before_line == after_line:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return len(before) + len(after) - 2 * previous[-1]


def trace_myers_distance(
    before: tuple[TextLine, ...], after: tuple[TextLine, ...]
) -> int:
    """Simple trace-style Myers reference used only for differential tests."""
    frontier = {1: 0}
    for distance in range(len(before) + len(after) + 1):
        next_frontier: dict[int, int] = {}
        for diagonal in range(-distance, distance + 1, 2):
            if diagonal == -distance or (
                diagonal != distance
                and frontier.get(diagonal - 1, -1) < frontier.get(diagonal + 1, -1)
            ):
                x = frontier.get(diagonal + 1, 0)
            else:
                x = frontier.get(diagonal - 1, -1) + 1
            y = x - diagonal
            while x < len(before) and y < len(after) and before[x] == after[y]:
                x += 1
                y += 1
            next_frontier[diagonal] = x
            if x >= len(before) and y >= len(after):
                return distance
        frontier = next_frontier
    raise AssertionError("reference Myers did not reach the target")


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ((), ()),
        (("a",), ("a",)),
        ((), ("a", "b")),
        (("a", "b"), ()),
        (("a", "b"), ("x", "y")),
        (("a", "b", "c"), ("a", "x", "c")),
        (("a", "b", "a"), ("a", "a", "b")),
        (("a", "b", "c"), ("c", "a", "b")),
    ],
)
def test_reconstructs_target_with_minimum_distance(
    before: tuple[str, ...], after: tuple[str, ...]
) -> None:
    before_lines = text_lines(*before)
    after_lines = text_lines(*after)
    result = shortest_edit_script(before_lines, after_lines, max_work=1_000_000)
    assert reconstruct(before_lines, result.operations) == after_lines
    assert edit_distance(result.operations) == lcs_edit_distance(
        before_lines, after_lines
    )


def test_exhaustive_small_inputs_match_dp_and_trace_myers() -> None:
    alphabet = ("a", "b")
    for before_size in range(5):
        for after_size in range(5):
            for before_values in itertools.product(alphabet, repeat=before_size):
                for after_values in itertools.product(alphabet, repeat=after_size):
                    before = text_lines(*before_values)
                    after = text_lines(*after_values)
                    result = shortest_edit_script(before, after, max_work=1_000_000)
                    distance = edit_distance(result.operations)
                    assert reconstruct(before, result.operations) == after
                    assert distance == lcs_edit_distance(before, after)
                    assert distance == trace_myers_distance(before, after)


def test_deletion_first_tie_break_snapshot() -> None:
    before = text_lines("a", "b")
    after = text_lines("b", "a")
    operations = shortest_edit_script(before, after, max_work=100).operations
    assert [(item.kind, item.line.content) for item in operations] == [
        ("delete", "a"),
        ("equal", "b"),
        ("insert", "a"),
    ]


def test_replacement_is_delete_then_insert() -> None:
    operations = shortest_edit_script(
        text_lines("before"), text_lines("after"), max_work=10
    ).operations
    assert [item.kind for item in operations] == ["delete", "insert"]


def test_repeated_runs_are_identical() -> None:
    before = text_lines("a", "b", "a", "b", "a", "c")
    after = text_lines("b", "a", "b", "x", "a", "c")
    snapshots = {
        shortest_edit_script(before, after, max_work=10_000) for _ in range(20)
    }
    assert len(snapshots) == 1


def test_boundary_middle_split_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("platydiff.comparators.text.myers")

    def boundary_split(
        _before: tuple[TextLine, ...],
        _after: tuple[TextLine, ...],
        region: RegionLike,
        _budget: object,
    ) -> tuple[int, int]:
        return region.before_start, region.after_start

    monkeypatch.setattr(module, "_middle_split", boundary_split)
    with pytest.raises(AssertionError, match="strictly inside"):
        shortest_edit_script(text_lines("a", "b"), text_lines("x", "y"), max_work=100)


def test_budget_boundary_is_exact() -> None:
    before = text_lines("a", "b", "c", "d")
    after = text_lines("a", "x", "c", "y")
    complete = shortest_edit_script(before, after, max_work=10_000)
    assert complete.work_units > 0
    assert shortest_edit_script(before, after, max_work=complete.work_units) == complete
    with pytest.raises(CompareResourceLimitError) as captured:
        shortest_edit_script(before, after, max_work=complete.work_units - 1)
    assert captured.value.details == {
        "used": complete.work_units - 1,
        "limit": complete.work_units - 1,
    }


def test_zero_budget_handles_empty_inputs() -> None:
    assert shortest_edit_script((), (), max_work=0).work_units == 0


def test_explicit_stack_is_not_limited_by_python_recursion() -> None:
    before = text_lines(*(str(index) for index in range(2_000)))
    after_values = [str(index) for index in range(2_000)]
    after_values[1_000] = "changed"
    after = text_lines(*after_values)
    result = shortest_edit_script(before, after, max_work=100_000)
    assert reconstruct(before, result.operations) == after


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (
            tuple(f"before-{index}" for index in range(384)),
            tuple(f"after-{index}" for index in range(384)),
        ),
        (
            tuple("a" if index % 2 else "b" for index in range(768)),
            tuple("b" if index % 2 else "a" for index in range(768)),
        ),
        (
            tuple(str(index % 17) for index in range(512)),
            tuple(str((index + 8) % 17) for index in range(512)),
        ),
    ],
)
def test_representative_peak_memory_is_linear(
    before: tuple[str, ...], after: tuple[str, ...]
) -> None:
    before_lines = text_lines(*before)
    after_lines = text_lines(*after)
    tracemalloc.start()
    result = shortest_edit_script(before_lines, after_lines, max_work=5_000_000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert reconstruct(before_lines, result.operations) == after_lines
    assert peak < 16 * 1024 * 1024
