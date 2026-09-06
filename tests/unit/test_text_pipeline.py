"""Tests for the complete explicit text comparison pipeline."""

from __future__ import annotations

import os
import time
import tracemalloc
from pathlib import Path

import pytest

from platydiff import (
    BytesSource,
    ChangeCompleteness,
    CompletedOutcome,
    FailedOutcome,
    NewlinePolicy,
    PathSource,
    Relation,
    ResourceLimits,
    TextCompareSpec,
    TextEncoding,
    TextSource,
    Verdict,
    compare,
)
from platydiff.core.models import TextHunk
from platydiff.core.serialization import dumps_outcome, serialized_change_size


def completed(
    before: TextSource | BytesSource | PathSource,
    after: TextSource | BytesSource | PathSource,
    spec: TextCompareSpec | None = None,
) -> CompletedOutcome:
    outcome = compare(before, after, spec or TextCompareSpec())
    assert isinstance(outcome, CompletedOutcome)
    return outcome


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (TextSource("same\n"), TextSource("same\n")),
        (BytesSource(b"same\n"), BytesSource(b"same\n")),
        (TextSource(""), TextSource("")),
    ],
)
def test_equal_sources_complete_with_pass(
    before: TextSource | BytesSource, after: TextSource | BytesSource
) -> None:
    outcome = completed(before, after)
    assert outcome.result.relation is Relation.EQUAL
    assert outcome.result.verdict is Verdict.PASS
    assert outcome.result.summary.change_count == 0
    assert outcome.result.changes.completeness is ChangeCompleteness.COMPLETE
    assert outcome.result.changes.items == ()


def test_path_source_is_bounded_and_records_safe_provenance(tmp_path: Path) -> None:
    before = tmp_path / "before.txt"
    after = tmp_path / "after.txt"
    before.write_bytes(b"same\n")
    after.write_bytes(b"same\n")
    outcome = completed(PathSource(before), PathSource(after))
    assert [item.label for item in outcome.result.provenance.inputs] == [
        "before.txt",
        "after.txt",
    ]
    assert str(tmp_path) not in dumps_outcome(outcome)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO files are unavailable")
def test_fifo_source_is_rejected_without_blocking(tmp_path: Path) -> None:
    fifo = tmp_path / "blocking-input"
    os.mkfifo(fifo)

    started = time.monotonic()
    outcome = compare(PathSource(fifo), TextSource("same\n"), TextCompareSpec())
    elapsed = time.monotonic() - started

    assert elapsed < 1.0
    assert isinstance(outcome, FailedOutcome)
    assert outcome.problem.code == "io_error"
    assert outcome.problem.stage.value == "sourcing"
    assert str(fifo) not in dumps_outcome(outcome)


def test_different_lines_build_one_based_delete_then_insert_hunk() -> None:
    outcome = completed(TextSource("a\nb\n"), TextSource("a\nx\n"))
    assert outcome.result.relation is Relation.DIFFERENT
    assert outcome.result.verdict is Verdict.FAIL
    assert outcome.result.summary.change_count == 1
    hunk = outcome.result.changes.items[0]
    assert isinstance(hunk, TextHunk)
    assert (hunk.before_start_line, hunk.before_line_count) == (1, 2)
    assert (hunk.after_start_line, hunk.after_line_count) == (1, 2)
    assert [line.kind for line in hunk.lines] == ["equal", "delete", "insert"]
    assert [(line.before_line, line.after_line) for line in hunk.lines] == [
        (1, 1),
        (2, None),
        (None, 2),
    ]


@pytest.mark.parametrize("terminator", ["\n", "\r\n", "\r"])
def test_preserve_accepts_each_exact_line_terminator(terminator: str) -> None:
    outcome = completed(TextSource(f"a{terminator}"), TextSource(f"a{terminator}"))
    assert outcome.result.relation is Relation.EQUAL


@pytest.mark.parametrize("left", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("right", ["\n", "\r\n", "\r"])
def test_normalize_lf_explicitly_equates_present_terminators(
    left: str, right: str
) -> None:
    preserve = completed(TextSource(f"a{left}"), TextSource(f"a{right}"))
    normalized = completed(
        TextSource(f"a{left}"),
        TextSource(f"a{right}"),
        TextCompareSpec(newline=NewlinePolicy.NORMALIZE_LF),
    )
    assert preserve.result.relation is (
        Relation.EQUAL if left == right else Relation.DIFFERENT
    )
    assert normalized.result.relation is Relation.EQUAL


def test_missing_final_newline_remains_a_difference() -> None:
    outcome = completed(TextSource("a\n"), TextSource("a"))
    assert outcome.result.relation is Relation.DIFFERENT
    hunk = outcome.result.changes.items[0]
    assert isinstance(hunk, TextHunk)
    assert [line.terminator for line in hunk.lines] == ["\n", ""]


def test_bom_is_data_for_utf8_and_removed_only_for_utf8_sig() -> None:
    before = BytesSource(b"\xef\xbb\xbfa\n")
    after = BytesSource(b"a\n")
    utf8 = completed(before, after)
    utf8_sig = completed(before, after, TextCompareSpec(encoding=TextEncoding.UTF8_SIG))
    assert utf8.result.relation is Relation.DIFFERENT
    assert utf8_sig.result.relation is Relation.EQUAL


def test_invalid_utf8_returns_decode_failure_without_partial_result() -> None:
    outcome = compare(BytesSource(b"\xff"), BytesSource(b"ok"), TextCompareSpec())
    assert isinstance(outcome, FailedOutcome)
    assert outcome.problem.code == "decode_error"
    assert outcome.problem.status_code == 422
    assert not hasattr(outcome, "result")


def test_missing_source_returns_safe_failure(tmp_path: Path) -> None:
    missing = tmp_path / "secret-location" / "missing.txt"
    outcome = compare(PathSource(missing), TextSource(""), TextCompareSpec())
    assert isinstance(outcome, FailedOutcome)
    assert outcome.problem.code == "source_not_found"
    assert str(tmp_path) not in outcome.problem.message


@pytest.mark.parametrize(
    ("before", "limits", "code", "stage"),
    [
        (
            BytesSource(b"ab"),
            ResourceLimits(max_input_bytes=1),
            "resource_limit_exceeded",
            "sourcing",
        ),
        (
            TextSource("a\nb\n"),
            ResourceLimits(max_input_lines=1),
            "resource_limit_exceeded",
            "decoding",
        ),
        (
            TextSource("ab"),
            ResourceLimits(max_encoded_line_bytes=1),
            "resource_limit_exceeded",
            "normalizing",
        ),
        (
            TextSource("a"),
            ResourceLimits(max_myers_work=0),
            "compare_resource_limit",
            "comparing",
        ),
    ],
)
def test_resource_limits_return_failed_outcomes(
    before: TextSource | BytesSource,
    limits: ResourceLimits,
    code: str,
    stage: str,
) -> None:
    outcome = compare(before, TextSource("b"), TextCompareSpec(limits=limits))
    assert isinstance(outcome, FailedOutcome)
    assert outcome.problem.code == code
    assert outcome.problem.stage.value == stage
    assert outcome.problem.status_code == 413
    assert not hasattr(outcome, "result")


def test_item_limit_truncates_complete_hunks_in_source_order() -> None:
    spec = TextCompareSpec(
        context_lines=0,
        limits=ResourceLimits(max_change_items=1),
    )
    outcome = completed(TextSource("a\nsame\nb\n"), TextSource("x\nsame\ny\n"), spec)
    assert outcome.result.summary.change_count == 2
    assert outcome.result.changes.completeness is ChangeCompleteness.TRUNCATED
    assert outcome.result.changes.total_count == 2
    assert outcome.result.changes.returned_count == 1
    assert outcome.result.changes.omitted_count == 1
    assert outcome.result.relation is Relation.DIFFERENT
    assert outcome.result.verdict is Verdict.FAIL
    assert [item.code for item in outcome.execution.diagnostics] == [
        "change_details_truncated"
    ]


def test_payload_limit_never_cuts_a_hunk() -> None:
    spec = TextCompareSpec(
        context_lines=0,
        limits=ResourceLimits(max_change_payload_bytes=1),
    )
    outcome = completed(TextSource("before"), TextSource("after"), spec)
    assert outcome.result.changes.completeness is ChangeCompleteness.TRUNCATED
    assert outcome.result.changes.returned_count == 0
    assert outcome.result.changes.items == ()


def test_payload_limit_uses_exact_canonical_utf8_change_sizes() -> None:
    before = TextSource("before-猫\nsame\nbefore-犬\n")
    after = TextSource("after-猫\nsame\nafter-犬\n")
    unlimited = completed(before, after, TextCompareSpec(context_lines=0))
    sizes = tuple(
        serialized_change_size(item) for item in unlimited.result.changes.items
    )
    assert len(sizes) == 2

    exact_first = completed(
        before,
        after,
        TextCompareSpec(
            context_lines=0,
            limits=ResourceLimits(max_change_payload_bytes=sizes[0]),
        ),
    )
    assert exact_first.result.changes.returned_count == 1
    assert any(
        resource.name == "change_payload_bytes" and resource.used == sizes[0]
        for resource in exact_first.result.provenance.resources
    )

    exact_minus_one = completed(
        before,
        after,
        TextCompareSpec(
            context_lines=0,
            limits=ResourceLimits(max_change_payload_bytes=sizes[0] - 1),
        ),
    )
    assert exact_minus_one.result.changes.returned_count == 0

    exact_both = completed(
        before,
        after,
        TextCompareSpec(
            context_lines=0,
            limits=ResourceLimits(max_change_payload_bytes=sum(sizes)),
        ),
    )
    assert exact_both.result.changes.completeness is ChangeCompleteness.COMPLETE
    assert exact_both.result.changes.returned_count == 2


def test_zero_detail_limits_do_not_materialize_quadratic_context() -> None:
    before_lines = [
        f"same-{index}" if index % 2 == 0 else f"before-{index}"
        for index in range(1_000)
    ]
    after_lines = [
        f"same-{index}" if index % 2 == 0 else f"after-{index}"
        for index in range(1_000)
    ]
    spec = TextCompareSpec(
        context_lines=200_000,
        limits=ResourceLimits(
            max_change_items=0,
            max_change_payload_bytes=0,
        ),
    )
    tracemalloc.start()
    outcome = completed(
        TextSource("\n".join(before_lines)),
        TextSource("\n".join(after_lines)),
        spec,
    )
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert outcome.result.summary.change_count == 500
    assert outcome.result.changes.total_count == 500
    assert outcome.result.changes.returned_count == 0
    assert outcome.result.changes.completeness is ChangeCompleteness.TRUNCATED
    assert peak < 16 * 1024 * 1024


def test_context_changes_details_but_not_semantics_or_total_count() -> None:
    before = TextSource("a\nsame\nb\n")
    after = TextSource("x\nsame\ny\n")
    no_context = completed(before, after, TextCompareSpec(context_lines=0))
    context = completed(before, after, TextCompareSpec(context_lines=3))
    assert no_context.result.relation == context.result.relation
    assert no_context.result.verdict == context.result.verdict
    assert no_context.result.summary == context.result.summary
    assert no_context.result.changes.total_count == context.result.changes.total_count
    assert no_context.result.changes.items != context.result.changes.items


def test_provenance_records_defaults_hashes_transformations_and_work() -> None:
    outcome = completed(
        BytesSource(b"a\r\n", "left"),
        BytesSource(b"a\n", "right"),
        TextCompareSpec(newline=NewlinePolicy.NORMALIZE_LF),
    )
    provenance = outcome.result.provenance
    assert provenance.spec["context_lines"] == 3
    assert [item.role for item in provenance.inputs] == ["before", "after"]
    assert all(len(item.sha256) == 64 for item in provenance.inputs)
    assert [item.transformation_id for item in provenance.transformations] == [
        "text.decode",
        "text.newline.normalize_lf",
        "text.lines.source_order",
    ]
    resources = {item.name: item for item in provenance.resources}
    assert resources["before_encoded_line_bytes"].used == 2
    assert resources["after_encoded_line_bytes"].used == 2
    assert resources["myers_work"].used > 0
    assert resources["myers_work"].limit == 5_000_000


def test_result_is_deterministic_across_runs() -> None:
    before = TextSource("a\nb\na\n")
    after = TextSource("b\na\nb\n")
    results = [completed(before, after).result for _ in range(10)]
    assert all(item == results[0] for item in results)
