"""Explicit text sourcing, decoding, normalization, comparison, and aggregation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from platydiff._version import __version__
from platydiff.comparators.text.models import EditOperation, TextLine
from platydiff.comparators.text.myers import ALGORITHM_ID, shortest_edit_script
from platydiff.core.models import (
    BytesSource,
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
    PathSource,
    PipelineStage,
    PolicyEvaluation,
    Relation,
    ResourceUsage,
    Source,
    SourceKind,
    SummaryCount,
    TextCompareSpec,
    TextHunk,
    TransformationRecord,
    Verdict,
)
from platydiff.core.pipeline import ComparisonCompletion
from platydiff.core.problems import (
    DecodeError,
    InputOutputError,
    ResourceLimitError,
    SourceNotFoundError,
    SourcePermissionError,
)
from platydiff.core.serialization import spec_to_data


@dataclass(frozen=True, slots=True)
class _SourcedText:
    data: bytes
    source_kind: SourceKind
    label: str | None
    decoded_text: str | None


def _read_path(path: Path, max_bytes: int) -> bytes:
    try:
        with path.open("rb") as stream:
            data = stream.read(max_bytes + 1)
    except FileNotFoundError as error:
        raise SourceNotFoundError("A source file was not found.") from error
    except PermissionError as error:
        raise SourcePermissionError(
            "Permission was denied while reading a source."
        ) from error
    except OSError as error:
        raise InputOutputError("A source could not be read.") from error
    if len(data) > max_bytes:
        raise ResourceLimitError(
            "A source exceeded the configured byte limit.",
            stage=PipelineStage.SOURCING,
        )
    return data


def _source(source: Source, max_bytes: int) -> _SourcedText:
    if isinstance(source, PathSource):
        return _SourcedText(
            _read_path(source.path, max_bytes),
            SourceKind.PATH,
            source.path.name,
            None,
        )
    if isinstance(source, BytesSource):
        if len(source.data) > max_bytes:
            raise ResourceLimitError(
                "A source exceeded the configured byte limit.",
                stage=PipelineStage.SOURCING,
            )
        return _SourcedText(source.data, SourceKind.BYTES, source.label, None)
    try:
        data = source.text.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise DecodeError(
            "An in-memory text source is not strict UTF-8 encodable."
        ) from error
    if len(data) > max_bytes:
        raise ResourceLimitError(
            "A source exceeded the configured byte limit.",
            stage=PipelineStage.SOURCING,
        )
    return _SourcedText(data, SourceKind.TEXT, source.label, source.text)


def _decode(source: _SourcedText, spec: TextCompareSpec) -> str:
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


def _build_hunks(
    operations: tuple[EditOperation, ...], context_lines: int
) -> tuple[TextHunk, ...]:
    cursors = _operation_cursors(operations)
    hunks: list[TextHunk] = []
    for start, end in _hunk_ranges(operations, context_lines):
        before_start, after_start = cursors[start]
        lines: list[HunkLine] = []
        for operation in operations[start:end]:
            lines.append(
                HunkLine(
                    kind=operation.kind,
                    content=operation.line.content,
                    terminator=operation.line.terminator,
                    before_line=(
                        None
                        if operation.before_index is None
                        else operation.before_index + 1
                    ),
                    after_line=(
                        None
                        if operation.after_index is None
                        else operation.after_index + 1
                    ),
                )
            )
        hunks.append(
            TextHunk(
                before_start_line=before_start + 1,
                before_line_count=sum(line.kind != "insert" for line in lines),
                after_start_line=after_start + 1,
                after_line_count=sum(line.kind != "delete" for line in lines),
                lines=tuple(lines),
            )
        )
    return tuple(hunks)


def _hunk_payload_size(hunk: TextHunk) -> int:
    data = {
        "kind": hunk.kind,
        "before_start_line": hunk.before_start_line,
        "before_line_count": hunk.before_line_count,
        "after_start_line": hunk.after_start_line,
        "after_line_count": hunk.after_line_count,
        "lines": [
            {
                "kind": line.kind,
                "content": line.content,
                "terminator": line.terminator,
                "before_line": line.before_line,
                "after_line": line.after_line,
            }
            for line in hunk.lines
        ],
    }
    return len(
        json.dumps(
            data,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _limit_hunks(
    hunks: tuple[TextHunk, ...], spec: TextCompareSpec
) -> tuple[ChangeSet, int, tuple[Diagnostic, ...]]:
    retained: list[TextHunk] = []
    payload_bytes = 0
    limiting_value: int | None = None
    for hunk in hunks:
        size = _hunk_payload_size(hunk)
        if len(retained) >= spec.limits.max_change_items:
            limiting_value = spec.limits.max_change_items
            break
        if payload_bytes + size > spec.limits.max_change_payload_bytes:
            limiting_value = spec.limits.max_change_payload_bytes
            break
        retained.append(hunk)
        payload_bytes += size
    if len(retained) == len(hunks):
        return (
            ChangeSet(
                ChangeCompleteness.COMPLETE,
                tuple(retained),
                len(hunks),
                len(retained),
                0,
                ChangeSelection.ALL,
                None,
            ),
            payload_bytes,
            (),
        )
    omitted = len(hunks) - len(retained)
    diagnostic = Diagnostic(
        "change_details_truncated",
        DiagnosticSeverity.WARNING,
        PipelineStage.AGGREGATING,
        "Complete change details were truncated by configured output limits.",
        {
            "total_count": len(hunks),
            "returned_count": len(retained),
            "max_change_items": spec.limits.max_change_items,
            "max_change_payload_bytes": spec.limits.max_change_payload_bytes,
        },
    )
    return (
        ChangeSet(
            ChangeCompleteness.TRUNCATED,
            tuple(retained),
            len(hunks),
            len(retained),
            omitted,
            ChangeSelection.SOURCE_ORDER_PREFIX,
            limiting_value,
        ),
        payload_bytes,
        (diagnostic,),
    )


def _input_provenance(
    source: _SourcedText, role: Literal["before", "after"]
) -> InputProvenance:
    return InputProvenance(
        role,
        source.source_kind,
        len(source.data),
        hashlib.sha256(source.data).hexdigest(),
        source.label,
    )


def _transformations(
    before: _SourcedText, after: _SourcedText, spec: TextCompareSpec
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


def compare_text(
    before: Source, after: Source, generic_spec: CompareSpec
) -> ComparisonCompletion:
    """Execute the complete strict Phase 1 text comparison."""
    spec = generic_spec
    sourced_before = _source(before, spec.limits.max_input_bytes)
    sourced_after = _source(after, spec.limits.max_input_bytes)
    decoded_before = _decode(sourced_before, spec)
    decoded_after = _decode(sourced_after, spec)
    lines_before = _normalize(
        _split_lines(decoded_before, spec.limits.max_input_lines), spec
    )
    lines_after = _normalize(
        _split_lines(decoded_after, spec.limits.max_input_lines), spec
    )
    myers = shortest_edit_script(
        lines_before, lines_after, max_work=spec.limits.max_myers_work
    )
    hunks = _build_hunks(myers.operations, spec.context_lines)
    change_set, payload_bytes, diagnostics = _limit_hunks(hunks, spec)
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
            len(hunks),
            (
                SummaryCount("changed_hunks", len(hunks), "hunks"),
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
