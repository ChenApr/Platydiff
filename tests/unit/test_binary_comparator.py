"""Exact streaming binary comparator tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from platydiff import (
    BinaryCompareSpec,
    BinaryResourceLimits,
    BinarySpan,
    BytesSource,
    Relation,
    TextSource,
    Verdict,
)
from platydiff.comparators.binary.comparator import compare_binary_snapshots
from platydiff.core._sources import SourceSnapshot, open_source_snapshot
from platydiff.core.models import (
    ChangeCompleteness,
    ChangeSelection,
    ChangeSet,
    PipelineStage,
    SourceKind,
)
from platydiff.core.pipeline import ComparisonCompletion
from platydiff.core.serialization import (
    _change_from_data,
    _change_to_data,
    serialized_change_size,
)


def _compare(
    before: bytes | str,
    after: bytes | str,
    *,
    limits: BinaryResourceLimits | None = None,
) -> ComparisonCompletion:
    before_source = (
        TextSource(before) if isinstance(before, str) else BytesSource(before)
    )
    after_source = TextSource(after) if isinstance(after, str) else BytesSource(after)
    spec = BinaryCompareSpec(limits=limits or BinaryResourceLimits())
    with (
        open_source_snapshot(
            before_source, max_input_bytes=spec.limits.max_input_bytes
        ) as left,
        open_source_snapshot(
            after_source, max_input_bytes=spec.limits.max_input_bytes
        ) as right,
    ):
        return compare_binary_snapshots(left, right, spec)


@pytest.mark.parametrize("payload", [b"", b"same", bytes(range(255))])
def test_identical_binary_inputs_are_exactly_equal(payload: bytes) -> None:
    completion = _compare(payload, payload)
    assert completion.result.relation is Relation.EQUAL
    assert completion.result.verdict is Verdict.PASS
    assert completion.result.changes.items == ()
    assert completion.result.summary.change_count == 0


def test_mismatches_form_maximal_ordered_replacement_spans() -> None:
    completion = _compare(
        b"aXXbYcZZ",
        b"a12b3c45",
        limits=BinaryResourceLimits(chunk_bytes=2),
    )
    assert completion.result.changes.items == (
        BinarySpan(before_offset=1, before_length=2, after_offset=1, after_length=2),
        BinarySpan(before_offset=4, before_length=1, after_offset=4, after_length=1),
        BinarySpan(before_offset=6, before_length=2, after_offset=6, after_length=2),
    )
    counts = {item.name: item.value for item in completion.result.summary.counts}
    assert counts == {
        "deleted_bytes": 0,
        "different_bytes": 5,
        "inserted_bytes": 0,
        "replacement_spans": 3,
    }


@pytest.mark.parametrize(
    ("before", "after", "before_length", "after_length"),
    [(b"abc", b"abcde", 0, 2), (b"abcde", b"abc", 2, 0)],
)
def test_length_difference_is_one_final_trailing_span(
    before: bytes, after: bytes, before_length: int, after_length: int
) -> None:
    completion = _compare(before, after, limits=BinaryResourceLimits(chunk_bytes=1))
    assert completion.result.changes.items[-1] == BinarySpan(
        before_offset=3,
        before_length=before_length,
        after_offset=3,
        after_length=after_length,
    )


def test_change_limits_truncate_details_without_weakening_result() -> None:
    completion = _compare(
        b"aXbYc",
        b"a1b2c",
        limits=BinaryResourceLimits(chunk_bytes=1, max_change_items=1),
    )
    result = completion.result
    assert result.relation is Relation.DIFFERENT
    assert result.verdict is Verdict.FAIL
    assert result.changes.completeness is ChangeCompleteness.TRUNCATED
    assert result.changes.total_count == 2
    assert result.changes.returned_count == 1
    assert result.changes.limit_reason == "change_items"
    assert completion.diagnostics[0].code == "change_details_truncated"


def test_payload_limit_uses_canonical_change_size() -> None:
    span = BinarySpan(before_offset=1, before_length=1, after_offset=1, after_length=1)
    size = serialized_change_size(span)
    complete = _compare(
        b"aX",
        b"a1",
        limits=BinaryResourceLimits(max_change_payload_bytes=size),
    )
    truncated = _compare(
        b"aX",
        b"a1",
        limits=BinaryResourceLimits(max_change_payload_bytes=size - 1),
    )
    assert complete.result.changes.completeness is ChangeCompleteness.COMPLETE
    assert truncated.result.changes.limit_reason == "change_payload_bytes"


def test_text_source_is_incrementally_utf8_encoded_and_recorded() -> None:
    completion = _compare("界", "界")
    assert completion.result.relation is Relation.EQUAL
    assert completion.result.provenance.inputs[0].source_kind is SourceKind.TEXT
    assert completion.result.provenance.transformations[0].transformation_id == (
        "binary.text.encode_utf8"
    )


def test_hash_equality_is_not_trusted_for_relation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SameDigest:
        def update(self, data: bytes) -> None:
            del data

        def hexdigest(self) -> str:
            return "0" * 64

    monkeypatch.setattr(
        "platydiff.comparators.binary.comparator.hashlib.sha256", SameDigest
    )
    completion = _compare(b"a", b"b")
    assert completion.result.provenance.inputs[0].sha256 == "0" * 64
    assert completion.result.provenance.inputs[1].sha256 == "0" * 64
    assert completion.result.relation is Relation.DIFFERENT


@pytest.mark.parametrize(
    "field", ["before_offset", "before_length", "after_offset", "after_length"]
)
def test_binary_span_rejects_boolean_and_inexact_bound(field: str) -> None:
    values = {
        "before_offset": 0,
        "before_length": 1,
        "after_offset": 0,
        "after_length": 1,
    }
    for invalid in (True, 2**53 + 1):
        values[field] = invalid
        with pytest.raises(ValueError):
            BinarySpan(**values)
    values[field] = 2**53
    if field.endswith("offset"):
        values["before_offset"] = values["after_offset"] = 2**53
    else:
        values["before_length"] = values["after_length"] = 2**53
    assert getattr(BinarySpan(**values), field) == 2**53


def test_binary_span_has_canonical_wire_round_trip() -> None:
    span = BinarySpan(
        before_offset=4096,
        before_length=12,
        after_offset=4096,
        after_length=12,
    )
    data = _change_to_data(span)
    assert data == {
        "kind": "binary_span",
        "before_offset": 4096,
        "before_length": 12,
        "after_offset": 4096,
        "after_length": 12,
    }
    assert _change_from_data(data) == span


def test_binary_change_set_rejects_touching_replacement_spans() -> None:
    with pytest.raises(ValueError, match="overlap or touch"):
        ChangeSet(
            ChangeCompleteness.COMPLETE,
            (
                BinarySpan(
                    before_offset=0, before_length=1, after_offset=0, after_length=1
                ),
                BinarySpan(
                    before_offset=1, before_length=1, after_offset=1, after_length=1
                ),
            ),
            2,
            2,
            0,
            ChangeSelection.ALL,
            None,
        )


class _IrregularSnapshot(SourceSnapshot):
    source_kind = SourceKind.BYTES
    label = None
    size_bytes = 6

    def __init__(self, chunks: tuple[bytes, ...]) -> None:
        super().__init__(max_input_bytes=6)
        self._chunks = chunks

    def iter_chunks(self, chunk_bytes: int, *, stage: PipelineStage) -> Iterator[bytes]:
        del chunk_bytes, stage
        yield from self._chunks


def test_comparison_is_independent_of_source_chunk_boundaries() -> None:
    spec = BinaryCompareSpec(limits=BinaryResourceLimits(chunk_bytes=4))
    left = _IrregularSnapshot((b"a", b"bc", b"def"))
    right = _IrregularSnapshot((b"abcd", b"Xf"))
    completion = compare_binary_snapshots(left, right, spec)
    assert completion.result.changes.items == (
        BinarySpan(before_offset=4, before_length=1, after_offset=4, after_length=1),
    )
