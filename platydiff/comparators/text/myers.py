"""Deterministic linear-space Myers shortest edit scripts."""

from __future__ import annotations

from dataclasses import dataclass

from platydiff.comparators.text.models import EditOperation, MyersResult, TextLine
from platydiff.core.problems import CompareResourceLimitError

ALGORITHM_ID = "text.myers.linear_space.v1"


@dataclass(frozen=True, slots=True)
class _Region:
    before_start: int
    before_end: int
    after_start: int
    after_end: int


@dataclass(frozen=True, slots=True)
class _EqualRange:
    before_start: int
    after_start: int
    length: int


class _Budget:
    def __init__(self, limit: int) -> None:
        if limit < 0:
            raise ValueError("max_work must be non-negative")
        self.limit = limit
        self.used = 0

    def charge(self) -> None:
        if self.used >= self.limit:
            raise CompareResourceLimitError(
                "Myers deterministic work budget was exhausted.",
                used=self.used,
                limit=self.limit,
            )
        self.used += 1

    def equal(self, before: TextLine, after: TextLine) -> bool:
        self.charge()
        return before == after


def _append_equal_range(
    operations: list[EditOperation],
    before: tuple[TextLine, ...],
    before_start: int,
    after_start: int,
    length: int,
) -> None:
    for offset in range(length):
        operations.append(
            EditOperation(
                "equal",
                before[before_start + offset],
                before_start + offset,
                after_start + offset,
            )
        )


def _append_delete_range(
    operations: list[EditOperation],
    before: tuple[TextLine, ...],
    start: int,
    end: int,
) -> None:
    for index in range(start, end):
        operations.append(EditOperation("delete", before[index], index, None))


def _append_insert_range(
    operations: list[EditOperation],
    after: tuple[TextLine, ...],
    start: int,
    end: int,
) -> None:
    for index in range(start, end):
        operations.append(EditOperation("insert", after[index], None, index))


def _solve_thin_region(
    before: tuple[TextLine, ...],
    after: tuple[TextLine, ...],
    region: _Region,
    budget: _Budget,
    operations: list[EditOperation],
) -> None:
    """Solve a one-row or one-column Myers base region."""
    before_length = region.before_end - region.before_start
    if before_length == 1:
        match: int | None = None
        for after_index in range(region.after_start, region.after_end):
            if budget.equal(before[region.before_start], after[after_index]):
                match = after_index
                break
        if match is None:
            _append_delete_range(
                operations, before, region.before_start, region.before_end
            )
            _append_insert_range(
                operations, after, region.after_start, region.after_end
            )
            return
        _append_insert_range(operations, after, region.after_start, match)
        _append_equal_range(operations, before, region.before_start, match, 1)
        _append_insert_range(operations, after, match + 1, region.after_end)
        return

    match = None
    for before_index in range(region.before_start, region.before_end):
        if budget.equal(before[before_index], after[region.after_start]):
            match = before_index
            break
    if match is None:
        _append_delete_range(operations, before, region.before_start, region.before_end)
        _append_insert_range(operations, after, region.after_start, region.after_end)
        return
    _append_delete_range(operations, before, region.before_start, match)
    _append_equal_range(operations, before, match, region.after_start, 1)
    _append_delete_range(operations, before, match + 1, region.before_end)


def _middle_split(
    before: tuple[TextLine, ...],
    after: tuple[TextLine, ...],
    region: _Region,
    budget: _Budget,
) -> tuple[int, int]:
    """Find a divide point where forward and reverse Myers waves overlap."""
    before_length = region.before_end - region.before_start
    after_length = region.after_end - region.after_start
    max_distance = (before_length + after_length + 1) // 2
    offset = max_distance + 1
    size = 2 * max_distance + 3
    forward = [-1] * size
    reverse = [-1] * size
    forward[offset + 1] = 0
    reverse[offset + 1] = 0
    delta = before_length - after_length
    odd_delta = delta % 2 != 0

    for distance in range(max_distance + 1):
        for diagonal in range(-distance, distance + 1, 2):
            budget.charge()
            index = offset + diagonal
            if diagonal == -distance or (
                diagonal != distance and forward[index - 1] < forward[index + 1]
            ):
                x = forward[index + 1]
            else:
                x = forward[index - 1] + 1
            y = x - diagonal
            while x < before_length and y < after_length:
                if not budget.equal(
                    before[region.before_start + x], after[region.after_start + y]
                ):
                    break
                x += 1
                y += 1
            forward[index] = x

            if odd_delta:
                reverse_diagonal = delta - diagonal
                if (
                    -distance + 1 <= reverse_diagonal <= distance - 1
                    and reverse[offset + reverse_diagonal] != -1
                ):
                    reverse_x = before_length - reverse[offset + reverse_diagonal]
                    if x >= reverse_x:
                        return region.before_start + x, region.after_start + y

        for diagonal in range(-distance, distance + 1, 2):
            budget.charge()
            index = offset + diagonal
            if diagonal == -distance or (
                diagonal != distance and reverse[index - 1] < reverse[index + 1]
            ):
                x = reverse[index + 1]
            else:
                x = reverse[index - 1] + 1
            y = x - diagonal
            while x < before_length and y < after_length:
                if not budget.equal(
                    before[region.before_end - x - 1],
                    after[region.after_end - y - 1],
                ):
                    break
                x += 1
                y += 1
            reverse[index] = x

            if not odd_delta:
                forward_diagonal = delta - diagonal
                if (
                    -distance <= forward_diagonal <= distance
                    and forward[offset + forward_diagonal] != -1
                ):
                    forward_x = forward[offset + forward_diagonal]
                    reverse_x = before_length - x
                    if forward_x >= reverse_x:
                        return (
                            region.before_start + forward_x,
                            region.after_start + forward_x - forward_diagonal,
                        )

    raise RuntimeError("Myers waves failed to overlap")


def shortest_edit_script(
    before: tuple[TextLine, ...],
    after: tuple[TextLine, ...],
    *,
    max_work: int,
) -> MyersResult:
    """Return a deterministic shortest insert/delete script in source order."""
    budget = _Budget(max_work)
    operations: list[EditOperation] = []
    tasks: list[_Region | _EqualRange] = [_Region(0, len(before), 0, len(after))]

    while tasks:
        task = tasks.pop()
        if isinstance(task, _EqualRange):
            _append_equal_range(
                operations,
                before,
                task.before_start,
                task.after_start,
                task.length,
            )
            continue

        before_start = task.before_start
        after_start = task.after_start
        before_end = task.before_end
        after_end = task.after_end

        prefix_length = 0
        while (
            before_start + prefix_length < before_end
            and after_start + prefix_length < after_end
        ):
            if not budget.equal(
                before[before_start + prefix_length],
                after[after_start + prefix_length],
            ):
                break
            prefix_length += 1
        _append_equal_range(
            operations, before, before_start, after_start, prefix_length
        )
        before_start += prefix_length
        after_start += prefix_length

        suffix_length = 0
        while (
            before_start < before_end - suffix_length
            and after_start < after_end - suffix_length
        ):
            if not budget.equal(
                before[before_end - suffix_length - 1],
                after[after_end - suffix_length - 1],
            ):
                break
            suffix_length += 1
        central_before_end = before_end - suffix_length
        central_after_end = after_end - suffix_length

        if before_start == central_before_end:
            _append_insert_range(operations, after, after_start, central_after_end)
            _append_equal_range(
                operations,
                before,
                central_before_end,
                central_after_end,
                suffix_length,
            )
            continue
        if after_start == central_after_end:
            _append_delete_range(operations, before, before_start, central_before_end)
            _append_equal_range(
                operations,
                before,
                central_before_end,
                central_after_end,
                suffix_length,
            )
            continue

        central = _Region(
            before_start, central_before_end, after_start, central_after_end
        )
        if (
            central.before_end - central.before_start == 1
            or central.after_end - central.after_start == 1
        ):
            _solve_thin_region(before, after, central, budget, operations)
            _append_equal_range(
                operations,
                before,
                central_before_end,
                central_after_end,
                suffix_length,
            )
            continue

        split_before, split_after = _middle_split(before, after, central, budget)
        if (split_before, split_after) in (
            (central.before_start, central.after_start),
            (central.before_end, central.after_end),
        ):
            raise AssertionError(
                "a non-thin middle split must make progress strictly inside its region"
            )

        if suffix_length:
            tasks.append(
                _EqualRange(central_before_end, central_after_end, suffix_length)
            )
        tasks.append(
            _Region(
                split_before,
                central.before_end,
                split_after,
                central.after_end,
            )
        )
        tasks.append(
            _Region(
                central.before_start,
                split_before,
                central.after_start,
                split_after,
            )
        )

    return MyersResult(tuple(operations), budget.used)
