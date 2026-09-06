"""Explicit text sourcing, decoding, normalization, comparison, and aggregation."""

from __future__ import annotations

import hashlib
from typing import Literal, cast

from platydiff._version import __version__
from platydiff.comparators.text.models import EditOperation, MyersResult, TextLine
from platydiff.comparators.text.myers import ALGORITHM_ID, shortest_edit_script
from platydiff.core.models import (
    ChangeCompleteness,
    ChangeSelection,
    ChangeSet,
    CompareSpec,
    ComparisonProvenance,
    Diagnostic,
    DiagnosticSeverity,
    DiffResult,
    DiffSummary,
    Fidelity,
    FiniteValue,
    HunkLine,
    InputProvenance,
    Metric,
    MetricDirection,
    NewlinePolicy,
    PipelineStage,
    PolicyEvaluation,
    Relation,
    ResourceUsage,
    SummaryCount,
    TextCompareSpec,
    TextHunk,
    TransformationRecord,
    Verdict,
)
from platydiff.core.pipeline import ComparisonCompletion, SourcedInput, StageRunner
from platydiff.core.problems import (
    DecodeError,
    ResourceLimitError,
)
from platydiff.core.serialization import serialized_change_size, spec_to_data


def _decode(source: SourcedInput, spec: TextCompareSpec) -> str:
    if source.decoded_text is not None:
        return source.decoded_text
    try:
        return source.data.decode(spec.encoding.value, errors="strict")
    except UnicodeDecodeError as error:
        raise DecodeError(
            f"A source is not valid strict {spec.encoding.value} text."
        ) from error


def _split_lines(text: str, max_lines: int) -> tuple[TextLine, ...]:
    lines: list[TextLine] = []
    start = 0
    cursor = 0
    while cursor < len(text):
        character = text[cursor]
        if character not in ("\r", "\n"):
            cursor += 1
            continue
        if character == "\r" and cursor + 1 < len(text) and text[cursor + 1] == "\n":
            terminator: Literal["\n", "\r\n", "\r"] = "\r\n"
            next_cursor = cursor + 2
        else:
            terminator = cast(Literal["\n", "\r\n", "\r"], character)
            next_cursor = cursor + 1
        lines.append(TextLine(text[start:cursor], terminator))
        if len(lines) > max_lines:
            raise ResourceLimitError(
                "A source exceeded the configured line limit.",
                stage=PipelineStage.DECODING,
            )
        start = next_cursor
        cursor = next_cursor
    if start < len(text):
        lines.append(TextLine(text[start:], ""))
        if len(lines) > max_lines:
            raise ResourceLimitError(
                "A source exceeded the configured line limit.",
                stage=PipelineStage.DECODING,
            )
    return tuple(lines)


def _normalize(
    lines: tuple[TextLine, ...], spec: TextCompareSpec
) -> tuple[TextLine, ...]:
    normalized: list[TextLine] = []
    for line in lines:
        terminator = (
            "\n"
            if spec.newline is NewlinePolicy.NORMALIZE_LF and line.terminator
            else line.terminator
        )
        normalized_line = TextLine(
            line.content,
            terminator,
        )
        encoded_size = len(
            (normalized_line.content + normalized_line.terminator).encode(
                "utf-8", errors="strict"
            )
        )
        if encoded_size > spec.limits.max_encoded_line_bytes:
            raise ResourceLimitError(
                "A normalized line exceeded the configured encoded-line limit.",
                stage=PipelineStage.NORMALIZING,
            )
        normalized.append(normalized_line)
    return tuple(normalized)


def _maximum_encoded_line_size(lines: tuple[TextLine, ...]) -> int:
    return max(
        (
            len((line.content + line.terminator).encode("utf-8", errors="strict"))
            for line in lines
        ),
        default=0,
    )


def _operation_cursors(
    operations: tuple[EditOperation, ...],
) -> tuple[tuple[int, int], ...]:
    before_cursor = 0
    after_cursor = 0
    cursors: list[tuple[int, int]] = []
    for operation in operations:
        cursors.append((before_cursor, after_cursor))
        if operation.kind != "insert":
            before_cursor += 1
        if operation.kind != "delete":
            after_cursor += 1
    cursors.append((before_cursor, after_cursor))
    return tuple(cursors)


def _hunk_ranges(
    operations: tuple[EditOperation, ...], context_lines: int
) -> tuple[tuple[int, int], ...]:
    changed_blocks: list[tuple[int, int]] = []
    block_start: int | None = None
    for index, item in enumerate(operations):
        if item.kind != "equal" and block_start is None:
            block_start = index
        elif item.kind == "equal" and block_start is not None:
            changed_blocks.append((block_start, index))
            block_start = None
    if block_start is not None:
        changed_blocks.append((block_start, len(operations)))
    ranges: list[tuple[int, int]] = []
    for start, end in changed_blocks:
        ranges.append(
            (
                max(0, start - context_lines),
                min(len(operations), end + context_lines),
            )
        )
    return tuple(ranges)


def _build_hunk(
    operations: tuple[EditOperation, ...],
    cursors: tuple[tuple[int, int], ...],
    start: int,
    end: int,
) -> TextHunk:
    before_start, after_start = cursors[start]
    lines = tuple(
        HunkLine(
            kind=operation.kind,
            content=operation.line.content,
            terminator=operation.line.terminator,
            before_line=(
                None if operation.before_index is None else operation.before_index + 1
            ),
            after_line=(
                None if operation.after_index is None else operation.after_index + 1
            ),
        )
        for operation in operations[start:end]
    )
    return TextHunk(
        before_start_line=before_start + 1,
        before_line_count=sum(line.kind != "insert" for line in lines),
        after_start_line=after_start + 1,
        after_line_count=sum(line.kind != "delete" for line in lines),
        lines=lines,
    )


def _select_hunks(
    operations: tuple[EditOperation, ...], spec: TextCompareSpec
) -> tuple[ChangeSet, int, tuple[Diagnostic, ...], int]:
    ranges = _hunk_ranges(operations, spec.context_lines)
    total_count = len(ranges)
    retained: list[TextHunk] = []
    payload_bytes = 0
    limiting_value: int | None = None
    cursors: tuple[tuple[int, int], ...] | None = None
    for start, end in ranges:
        if len(retained) >= spec.limits.max_change_items:
            limiting_value = spec.limits.max_change_items
            break
        if spec.limits.max_change_payload_bytes == 0:
            limiting_value = 0
            break
        if cursors is None:
            cursors = _operation_cursors(operations)
        hunk = _build_hunk(operations, cursors, start, end)
        size = serialized_change_size(hunk)
        if payload_bytes + size > spec.limits.max_change_payload_bytes:
            limiting_value = spec.limits.max_change_payload_bytes
            break
        retained.append(hunk)
        payload_bytes += size
    if len(retained) == total_count:
        return (
            ChangeSet(
                ChangeCompleteness.COMPLETE,
                tuple(retained),
                total_count,
                len(retained),
                0,
                ChangeSelection.ALL,
                None,
            ),
            payload_bytes,
            (),
            total_count,
        )
    omitted = total_count - len(retained)
    diagnostic = Diagnostic(
        "change_details_truncated",
        DiagnosticSeverity.WARNING,
        PipelineStage.AGGREGATING,
        "Complete change details were truncated by configured output limits.",
        {
            "total_count": total_count,
            "returned_count": len(retained),
            "max_change_items": spec.limits.max_change_items,
            "max_change_payload_bytes": spec.limits.max_change_payload_bytes,
        },
    )
    return (
        ChangeSet(
            ChangeCompleteness.TRUNCATED,
            tuple(retained),
            total_count,
            len(retained),
            omitted,
            ChangeSelection.SOURCE_ORDER_PREFIX,
            limiting_value,
        ),
        payload_bytes,
        (diagnostic,),
        total_count,
    )


def _input_provenance(
    source: SourcedInput, role: Literal["before", "after"]
) -> InputProvenance:
    return InputProvenance(
        role,
        source.source_kind,
        len(source.data),
        hashlib.sha256(source.data).hexdigest(),
        source.label,
    )


def _transformations(
    before: SourcedInput, after: SourcedInput, spec: TextCompareSpec
) -> tuple[TransformationRecord, ...]:
    records: list[TransformationRecord] = []
    if before.decoded_text is None or after.decoded_text is None:
        records.append(
            TransformationRecord(
                "decoding", "text.decode", {"encoding": spec.encoding.value}
            )
        )
    if spec.newline is NewlinePolicy.NORMALIZE_LF:
        records.append(
            TransformationRecord(
                "normalizing", "text.newline.normalize_lf", {"enabled": True}
            )
        )
    records.append(TransformationRecord("aligning", "text.lines.source_order", {}))
    return tuple(records)


def _aggregate(
    sourced_before: SourcedInput,
    sourced_after: SourcedInput,
    lines_before: tuple[TextLine, ...],
    lines_after: tuple[TextLine, ...],
    myers: MyersResult,
    spec: TextCompareSpec,
) -> ComparisonCompletion:
    change_set, payload_bytes, diagnostics, total_hunks = _select_hunks(
        myers.operations, spec
    )
    deleted = sum(item.kind == "delete" for item in myers.operations)
    inserted = sum(item.kind == "insert" for item in myers.operations)
    distance = deleted + inserted
    relation = Relation.EQUAL if distance == 0 else Relation.DIFFERENT
    verdict = Verdict.PASS if relation is Relation.EQUAL else Verdict.FAIL
    result = DiffResult(
        relation=relation,
        verdict=verdict,
        fidelity=Fidelity.FULL,
        summary=DiffSummary(
            total_hunks,
            (
                SummaryCount("changed_hunks", total_hunks, "hunks"),
                SummaryCount("deleted_lines", deleted, "lines"),
                SummaryCount("inserted_lines", inserted, "lines"),
            ),
        ),
        changes=change_set,
        metrics=(
            Metric(
                "edit_distance",
                FiniteValue(float(distance)),
                "operations",
                MetricDirection.LOWER_IS_BETTER,
            ),
        ),
        evaluations=(
            PolicyEvaluation(
                "strict_equality",
                verdict,
                "edit_distance",
                "eq",
                FiniteValue(0.0),
                FiniteValue(float(distance)),
            ),
        ),
        artifacts=(),
        provenance=ComparisonProvenance(
            inputs=(
                _input_provenance(sourced_before, "before"),
                _input_provenance(sourced_after, "after"),
            ),
            spec=spec_to_data(spec),
            transformations=_transformations(sourced_before, sourced_after, spec),
            comparator_id="text",
            comparator_version=__version__,
            algorithm_id=ALGORITHM_ID,
            implementation_version=__version__,
            resources=(
                ResourceUsage(
                    "before_input_bytes",
                    spec.limits.max_input_bytes,
                    len(sourced_before.data),
                ),
                ResourceUsage(
                    "before_input_lines",
                    spec.limits.max_input_lines,
                    len(lines_before),
                ),
                ResourceUsage(
                    "before_encoded_line_bytes",
                    spec.limits.max_encoded_line_bytes,
                    _maximum_encoded_line_size(lines_before),
                ),
                ResourceUsage(
                    "change_items",
                    spec.limits.max_change_items,
                    change_set.returned_count,
                ),
                ResourceUsage(
                    "change_payload_bytes",
                    spec.limits.max_change_payload_bytes,
                    payload_bytes,
                ),
                ResourceUsage(
                    "after_input_bytes",
                    spec.limits.max_input_bytes,
                    len(sourced_after.data),
                ),
                ResourceUsage(
                    "after_input_lines",
                    spec.limits.max_input_lines,
                    len(lines_after),
                ),
                ResourceUsage(
                    "after_encoded_line_bytes",
                    spec.limits.max_encoded_line_bytes,
                    _maximum_encoded_line_size(lines_after),
                ),
                ResourceUsage(
                    "myers_work", spec.limits.max_myers_work, myers.work_units
                ),
            ),
        ),
    )
    return ComparisonCompletion(result, diagnostics)


def compare_text(
    sourced_before: SourcedInput,
    sourced_after: SourcedInput,
    generic_spec: CompareSpec,
    stages: StageRunner,
) -> ComparisonCompletion:
    """Execute the staged strict Phase 1 text comparison."""
    spec = generic_spec
    lines_before, lines_after = stages.run(
        PipelineStage.DECODING,
        lambda: (
            _split_lines(_decode(sourced_before, spec), spec.limits.max_input_lines),
            _split_lines(_decode(sourced_after, spec), spec.limits.max_input_lines),
        ),
    )
    normalized_before, normalized_after = stages.run(
        PipelineStage.NORMALIZING,
        lambda: (
            _normalize(lines_before, spec),
            _normalize(lines_after, spec),
        ),
    )
    aligned_before, aligned_after = stages.run(
        PipelineStage.ALIGNING, lambda: (normalized_before, normalized_after)
    )
    myers = stages.run(
        PipelineStage.COMPARING,
        lambda: shortest_edit_script(
            aligned_before,
            aligned_after,
            max_work=spec.limits.max_myers_work,
        ),
    )
    return stages.run(
        PipelineStage.AGGREGATING,
        lambda: _aggregate(
            sourced_before,
            sourced_after,
            aligned_before,
            aligned_after,
            myers,
            spec,
        ),
    )
