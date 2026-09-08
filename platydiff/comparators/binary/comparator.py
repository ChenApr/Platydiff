"""Bounded streaming exact binary comparison."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal, Protocol

from platydiff._version import __version__
from platydiff.core._sources import SourceSnapshot
from platydiff.core.models import (
    AutoCompareSpec,
    BinaryCompareSpec,
    BinarySpan,
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
    InputProvenance,
    JsonValue,
    Metric,
    MetricDirection,
    PipelineStage,
    PolicyEvaluation,
    Relation,
    ResourceUsage,
    SourceKind,
    SummaryCount,
    TransformationRecord,
    Verdict,
)
from platydiff.core.pipeline import ComparisonCompletion
from platydiff.core.serialization import serialized_change_size, spec_to_data

ALGORITHM_ID = "binary.exact.stream.v1"


@dataclass(frozen=True, slots=True)
class _Limits:
    max_input_bytes: int
    chunk_bytes: int
    max_change_items: int
    max_change_payload_bytes: int


@dataclass(slots=True)
class _Cursor:
    snapshot: SourceSnapshot
    limit: int
    chunk_bytes: int
    iterator: Iterator[bytes]
    digest: _Digest
    pending: bytes = b""
    eof: bool = False
    total: int = 0

    @classmethod
    def create(cls, snapshot: SourceSnapshot, limits: _Limits) -> _Cursor:
        return cls(
            snapshot,
            limits.max_input_bytes,
            limits.chunk_bytes,
            iter(
                snapshot.iter_chunks(limits.chunk_bytes, stage=PipelineStage.COMPARING)
            ),
            digest=hashlib.sha256(),
        )

    def fill(self) -> None:
        if self.pending or self.eof:
            return
        try:
            chunk = next(self.iterator)
        except StopIteration:
            self.eof = True
            return
        if len(chunk) > self.chunk_bytes:
            raise RuntimeError("source adapter exceeded binary chunk size")
        self.total += len(chunk)
        if self.total > self.limit:
            from platydiff.core.problems import ResourceLimitError

            raise ResourceLimitError(
                "A source exceeded the configured byte limit.",
                stage=PipelineStage.COMPARING,
            )
        self.digest.update(chunk)
        self.pending = chunk


class _Digest(Protocol):
    def update(self, data: bytes) -> None: ...

    def hexdigest(self) -> str: ...


@dataclass(frozen=True, slots=True)
class _Scan:
    spans: tuple[BinarySpan, ...]
    total_spans: int
    replacement_spans: int
    different_bytes: int
    inserted_bytes: int
    deleted_bytes: int
    before_bytes: int
    after_bytes: int
    before_sha256: str
    after_sha256: str
    payload_bytes: int
    limit: int | None
    limit_reason: Literal["change_items", "change_payload_bytes"] | None


def compare_binary_snapshots(
    before: SourceSnapshot,
    after: SourceSnapshot,
    spec: BinaryCompareSpec | AutoCompareSpec,
) -> ComparisonCompletion:
    """Compare two replayable snapshots by actual bytes and aggregate the result."""
    limits = _limits(spec)
    scan = _scan(before, after, limits)
    relation = Relation.EQUAL if scan.different_bytes == 0 else Relation.DIFFERENT
    verdict = Verdict.PASS if relation is Relation.EQUAL else Verdict.FAIL
    if scan.limit_reason is None:
        changes = ChangeSet(
            ChangeCompleteness.COMPLETE,
            scan.spans,
            scan.total_spans,
            len(scan.spans),
            0,
            ChangeSelection.ALL,
            None,
        )
        diagnostics: tuple[Diagnostic, ...] = ()
    else:
        changes = ChangeSet(
            ChangeCompleteness.TRUNCATED,
            scan.spans,
            scan.total_spans,
            len(scan.spans),
            scan.total_spans - len(scan.spans),
            ChangeSelection.SOURCE_ORDER_PREFIX,
            scan.limit,
            scan.limit_reason,
        )
        diagnostics = (
            Diagnostic(
                "change_details_truncated",
                DiagnosticSeverity.WARNING,
                PipelineStage.AGGREGATING,
                "Complete change details were truncated by configured output limits.",
                {
                    "total_count": scan.total_spans,
                    "returned_count": len(scan.spans),
                    "max_change_items": limits.max_change_items,
                    "max_change_payload_bytes": limits.max_change_payload_bytes,
                    "limit_reason": scan.limit_reason,
                },
            ),
        )
    metric = FiniteValue(scan.different_bytes)
    result = DiffResult(
        relation=relation,
        verdict=verdict,
        fidelity=Fidelity.FULL,
        summary=DiffSummary(
            scan.total_spans,
            (
                SummaryCount("different_bytes", scan.different_bytes, "bytes"),
                SummaryCount("replacement_spans", scan.replacement_spans, "spans"),
                SummaryCount("inserted_bytes", scan.inserted_bytes, "bytes"),
                SummaryCount("deleted_bytes", scan.deleted_bytes, "bytes"),
            ),
        ),
        changes=changes,
        metrics=(
            Metric(
                "different_bytes",
                metric,
                "bytes",
                MetricDirection.LOWER_IS_BETTER,
                "sum",
            ),
            Metric(
                "before_bytes",
                FiniteValue(scan.before_bytes),
                "bytes",
                MetricDirection.NEUTRAL,
                "count",
            ),
            Metric(
                "after_bytes",
                FiniteValue(scan.after_bytes),
                "bytes",
                MetricDirection.NEUTRAL,
                "count",
            ),
        ),
        evaluations=(
            PolicyEvaluation(
                "binary.strict_equality",
                verdict,
                "different_bytes",
                "eq",
                FiniteValue(0),
                metric,
            ),
        ),
        artifacts=(),
        provenance=_provenance(before, after, spec, limits, scan),
    )
    return ComparisonCompletion(result, diagnostics)


def _limits(spec: BinaryCompareSpec | AutoCompareSpec) -> _Limits:
    if isinstance(spec, BinaryCompareSpec):
        return _Limits(
            spec.limits.max_input_bytes,
            spec.limits.chunk_bytes,
            spec.limits.max_change_items,
            spec.limits.max_change_payload_bytes,
        )
    return _Limits(
        spec.limits.max_input_bytes,
        spec.limits.binary_chunk_bytes,
        spec.limits.max_change_items,
        spec.limits.max_change_payload_bytes,
    )


def _scan(before: SourceSnapshot, after: SourceSnapshot, limits: _Limits) -> _Scan:
    left = _Cursor.create(before, limits)
    right = _Cursor.create(after, limits)
    retained: list[BinarySpan] = []
    total_spans = replacement_spans = different = 0
    mismatch_start: int | None = None
    offset = 0
    payload_bytes = 0
    limiting_value: int | None = None
    limiting_reason: Literal["change_items", "change_payload_bytes"] | None = None

    def close_replacement() -> None:
        nonlocal mismatch_start, total_spans, replacement_spans, payload_bytes
        nonlocal limiting_value, limiting_reason
        if mismatch_start is None:
            return
        span = BinarySpan(
            before_offset=mismatch_start,
            before_length=offset - mismatch_start,
            after_offset=mismatch_start,
            after_length=offset - mismatch_start,
        )
        total_spans += 1
        replacement_spans += 1
        payload_bytes, limiting_value, limiting_reason = _retain(
            span,
            retained,
            payload_bytes,
            limits,
            limiting_value,
            limiting_reason,
        )
        mismatch_start = None

    while True:
        left.fill()
        right.fill()
        if left.pending and right.pending:
            length = min(len(left.pending), len(right.pending))
            for index in range(length):
                if left.pending[index] != right.pending[index]:
                    different += 1
                    if mismatch_start is None:
                        mismatch_start = offset
                elif mismatch_start is not None:
                    close_replacement()
                offset += 1
            left.pending = left.pending[length:]
            right.pending = right.pending[length:]
            continue
        if (left.eof and not left.pending) or (right.eof and not right.pending):
            close_replacement()
            break

    common_eof = offset
    before_tail = _drain(left)
    after_tail = _drain(right)
    if before_tail or after_tail:
        tail = BinarySpan(
            before_offset=common_eof,
            before_length=before_tail,
            after_offset=common_eof,
            after_length=after_tail,
        )
        total_spans += 1
        different += before_tail + after_tail
        payload_bytes, limiting_value, limiting_reason = _retain(
            tail,
            retained,
            payload_bytes,
            limits,
            limiting_value,
            limiting_reason,
        )
    return _Scan(
        tuple(retained),
        total_spans,
        replacement_spans,
        different,
        after_tail,
        before_tail,
        left.total,
        right.total,
        left.digest.hexdigest(),
        right.digest.hexdigest(),
        payload_bytes,
        limiting_value,
        limiting_reason,
    )


def _drain(cursor: _Cursor) -> int:
    length = len(cursor.pending)
    cursor.pending = b""
    while not cursor.eof:
        cursor.fill()
        length += len(cursor.pending)
        cursor.pending = b""
    return length


def _retain(
    span: BinarySpan,
    retained: list[BinarySpan],
    payload_bytes: int,
    limits: _Limits,
    limiting_value: int | None,
    limiting_reason: Literal["change_items", "change_payload_bytes"] | None,
) -> tuple[int, int | None, Literal["change_items", "change_payload_bytes"] | None]:
    if limiting_reason is not None:
        return payload_bytes, limiting_value, limiting_reason
    if len(retained) >= limits.max_change_items:
        return payload_bytes, limits.max_change_items, "change_items"
    size = serialized_change_size(span)
    if payload_bytes + size > limits.max_change_payload_bytes:
        return payload_bytes, limits.max_change_payload_bytes, "change_payload_bytes"
    retained.append(span)
    return payload_bytes + size, None, None


def _provenance(
    before: SourceSnapshot,
    after: SourceSnapshot,
    spec: CompareSpec,
    limits: _Limits,
    scan: _Scan,
) -> ComparisonProvenance:
    transformations: tuple[TransformationRecord, ...] = ()
    text_roles: list[JsonValue] = [
        role
        for role, snapshot in (("before", before), ("after", after))
        if snapshot.source_kind is SourceKind.TEXT
    ]
    if text_roles:
        transformations = (
            TransformationRecord(
                "decoding", "binary.text.encode_utf8", {"roles": text_roles}
            ),
        )
    return ComparisonProvenance(
        inputs=(
            InputProvenance(
                "before",
                before.source_kind,
                scan.before_bytes,
                scan.before_sha256,
                before.label,
            ),
            InputProvenance(
                "after",
                after.source_kind,
                scan.after_bytes,
                scan.after_sha256,
                after.label,
            ),
        ),
        spec=spec_to_data(spec),
        transformations=transformations,
        comparator_id="binary",
        comparator_version="1",
        algorithm_id=ALGORITHM_ID,
        implementation_version=__version__,
        resources=(
            ResourceUsage("before_bytes", limits.max_input_bytes, scan.before_bytes),
            ResourceUsage("after_bytes", limits.max_input_bytes, scan.after_bytes),
            ResourceUsage("chunk_bytes", limits.chunk_bytes, limits.chunk_bytes),
            ResourceUsage("change_items", limits.max_change_items, len(scan.spans)),
            ResourceUsage(
                "change_payload_bytes",
                limits.max_change_payload_bytes,
                scan.payload_bytes,
            ),
        ),
    )
