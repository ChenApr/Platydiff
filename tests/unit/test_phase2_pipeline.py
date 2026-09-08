"""Automatic detection and snapshot pipeline integration tests."""

from __future__ import annotations

from platydiff import (
    AutoCompareSpec,
    AutoResourceLimits,
    BinaryCompareSpec,
    BytesSource,
    CompletedOutcome,
    FailedOutcome,
    Relation,
    UnavailableOutcome,
    compare,
)


def test_explicit_binary_bypasses_detection_with_complete_trace() -> None:
    outcome = compare(BytesSource(b"a"), BytesSource(b"b"), BinaryCompareSpec())
    assert isinstance(outcome, CompletedOutcome)
    assert [stage.stage.value for stage in outcome.execution.stages] == [
        "validating",
        "sourcing",
        "resolving",
        "decoding",
        "normalizing",
        "aligning",
        "comparing",
        "aggregating",
    ]
    assert outcome.execution.detection is None
    assert outcome.execution.attempts[-1].capability_id == "binary"


def test_auto_selects_text_and_binary_deterministically() -> None:
    text = compare(BytesSource(b"same"), BytesSource(b"same"), AutoCompareSpec())
    binary = compare(BytesSource(b"\x00"), BytesSource(b"\x00"), AutoCompareSpec())
    assert isinstance(text, CompletedOutcome)
    assert isinstance(binary, CompletedOutcome)
    assert text.execution.detection is not None
    assert binary.execution.detection is not None
    assert text.execution.detection.selected_modality == "text"
    assert binary.execution.detection.selected_modality == "binary"
    assert text.result.relation is Relation.EQUAL
    assert binary.result.relation is Relation.EQUAL


def test_detection_no_match_and_ambiguity_are_unavailable() -> None:
    no_match = compare(BytesSource(b""), BytesSource(b""), AutoCompareSpec())
    ambiguous = compare(
        BytesSource(b"ascii"),
        BytesSource(b"ascii"),
        AutoCompareSpec(minimum_confidence=0, ambiguity_margin=501),
    )
    assert isinstance(no_match, UnavailableOutcome)
    assert isinstance(ambiguous, UnavailableOutcome)
    assert no_match.problem.code == "detection_no_match"
    assert ambiguous.problem.code == "detection_ambiguous"
    assert no_match.execution.stages[-1].disposition.value == "unavailable"


def test_zero_detection_budget_runs_without_content_inspection() -> None:
    outcome = compare(
        BytesSource(b"not empty"),
        BytesSource(b"also not empty"),
        AutoCompareSpec(limits=AutoResourceLimits(max_detection_bytes=0)),
    )
    assert isinstance(outcome, UnavailableOutcome)
    assert outcome.execution.detection is not None
    assert outcome.execution.stages[-1].stage.value == "detecting"
    assert {
        candidate.evidence_codes
        for source in outcome.execution.detection.sources
        for candidate in source.candidates
    } == {("content_not_inspected",)}


def test_late_invalid_utf8_fails_decoding_without_binary_fallback() -> None:
    spec = AutoCompareSpec(limits=AutoResourceLimits(max_detection_bytes=1))
    outcome = compare(BytesSource(b"a\xff"), BytesSource(b"a\xff"), spec)
    assert isinstance(outcome, FailedOutcome)
    assert outcome.problem.code == "decode_error"
    assert outcome.problem.stage.value == "decoding"
    assert outcome.execution.detection is not None
    assert outcome.execution.detection.selected_modality == "text"
    assert [attempt.capability_id for attempt in outcome.execution.attempts] == [
        "binary",
        "text",
    ]


def test_explicit_binary_override_accepts_invalid_utf8() -> None:
    outcome = compare(BytesSource(b"\xff"), BytesSource(b"\xff"), BinaryCompareSpec())
    assert isinstance(outcome, CompletedOutcome)
    assert outcome.result.relation is Relation.EQUAL
