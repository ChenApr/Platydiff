"""Phase 2 specification, detection, and private resolution contracts."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

import platydiff
from platydiff import (
    AutoCompareSpec,
    AutoResourceLimits,
    BinaryCompareSpec,
    BinaryResourceLimits,
    BytesSource,
    TextSource,
)
from platydiff.core._capabilities import (
    CapabilityCatalog,
    CapabilityRecord,
    request_from_spec,
)
from platydiff.core._detection import _detect_source, detect_pair
from platydiff.core._sources import open_source_snapshot
from platydiff.core.models import (
    CapabilityProblem,
    DetectionRecord,
    ExecutionRecord,
    PipelineStage,
    SourceKind,
    StageDisposition,
    StageRecord,
    UnavailableOutcome,
)
from platydiff.core.serialization import (
    SerializationError,
    dumps_outcome,
    outcome_from_data,
    outcome_to_data,
    spec_from_data,
    spec_to_data,
)

STAMP = "2026-09-09T00:00:00Z"
_COUNT_KEYS = {
    "inspected_bytes",
    "nul_count",
    "non_ascii_byte_count",
    "pending_utf8_bytes",
    "disallowed_control_count",
}


def _capability(
    capability_id: str,
    modality: str,
    *,
    priority: int = 0,
    semantic_class: str = "exact",
    source_kinds: frozenset[SourceKind] = frozenset(SourceKind),
    features: frozenset[str] = frozenset(),
    available: bool = True,
    version_supported: bool = True,
) -> CapabilityRecord:
    assert modality in ("text", "binary")
    return CapabilityRecord(
        capability_id=capability_id,
        modality=modality,  # type: ignore[arg-type]
        semantic_class=semantic_class,
        implementation_version="1",
        backend_id=f"{capability_id}_backend",
        backend_version="1",
        priority=priority,
        supported_source_kinds=source_kinds,
        supported_features=features,
        executor=object(),
        backend_available=available,
        backend_version_supported=version_supported,
    )


def _detect(
    source: BytesSource | TextSource, maximum_bytes: int
) -> tuple[tuple[str, int, str], ...]:
    with open_source_snapshot(source, max_input_bytes=100) as snapshot:
        record = _detect_source(snapshot, "before", maximum_bytes)
    for candidate in record.candidates:
        assert set(candidate.evidence_counts) == _COUNT_KEYS
    return tuple(
        (item.modality_id, item.confidence, item.evidence_codes[0])
        for item in record.candidates
    )


def test_new_specs_have_exact_canonical_defaults_and_round_trip() -> None:
    binary = BinaryCompareSpec()
    auto = AutoCompareSpec()
    assert json.dumps(spec_to_data(binary), sort_keys=True, separators=(",", ":")) == (
        '{"kind":"binary","limits":{"chunk_bytes":65536,'
        '"max_change_items":10000,"max_change_payload_bytes":4194304,'
        '"max_input_bytes":16777216}}'
    )
    assert json.dumps(spec_to_data(auto), sort_keys=True, separators=(",", ":")) == (
        '{"ambiguity_margin":100,"kind":"auto","limits":{'
        '"binary_chunk_bytes":65536,"max_change_items":10000,'
        '"max_change_payload_bytes":4194304,"max_detection_bytes":65536,'
        '"max_encoded_line_bytes":1048576,"max_input_bytes":16777216,'
        '"max_input_lines":200000,"max_myers_work":5000000},'
        '"minimum_confidence":800,"text":{"context_lines":3,'
        '"encoding":"utf-8","newline":"preserve"}}'
    )
    assert spec_from_data(spec_to_data(binary)) == binary
    assert spec_from_data(spec_to_data(auto)) == auto


def test_unknown_spec_fields_are_ignored_and_not_reemitted() -> None:
    data = spec_to_data(AutoCompareSpec())
    data["future"] = {"ignored": True}
    text = data["text"]
    limits = data["limits"]
    assert isinstance(text, dict)
    assert isinstance(limits, dict)
    text["future"] = 1
    limits["future"] = 2
    reemitted = spec_to_data(spec_from_data(data))
    assert "future" not in reemitted
    assert "future" not in reemitted["text"]  # type: ignore[operator]
    assert "future" not in reemitted["limits"]  # type: ignore[operator]


@pytest.mark.parametrize("value", [True, -1, 2**53 + 1])
def test_new_budget_limits_reject_non_exact_integers(value: int) -> None:
    with pytest.raises(ValueError):
        BinaryResourceLimits(max_input_bytes=value)
    with pytest.raises(ValueError):
        AutoResourceLimits(max_detection_bytes=value)


@pytest.mark.parametrize("value", [False, 0, 16 * 1024 * 1024 + 1])
def test_binary_chunk_limits_are_strictly_bounded(value: int) -> None:
    with pytest.raises(ValueError):
        BinaryResourceLimits(chunk_bytes=value)
    with pytest.raises(ValueError):
        AutoResourceLimits(binary_chunk_bytes=value)


def test_new_exact_integer_upper_bound_is_inclusive() -> None:
    assert BinaryResourceLimits(max_input_bytes=2**53).max_input_bytes == 2**53
    assert AutoResourceLimits(max_detection_bytes=2**53).max_detection_bytes == 2**53


def test_public_root_exports_specs_but_not_private_resolution_types() -> None:
    assert {
        "AutoCompareSpec",
        "AutoResourceLimits",
        "AutoTextOptions",
        "BinaryCompareSpec",
        "BinaryResourceLimits",
    }.issubset(platydiff.__all__)
    assert "CapabilityRequest" not in platydiff.__all__
    assert "InternalRegistry" not in platydiff.__all__


@pytest.mark.parametrize(
    ("source", "maximum_bytes", "expected"),
    [
        (
            TextSource(""),
            10,
            (("text", 1000, "explicit_text_source"),),
        ),
        (
            BytesSource(b""),
            10,
            (("binary", 500, "empty_source"), ("text", 500, "empty_source")),
        ),
        (
            BytesSource(b"ascii"),
            0,
            (
                ("binary", 500, "content_not_inspected"),
                ("text", 500, "content_not_inspected"),
            ),
        ),
        (BytesSource(b"a\x00b"), 10, (("binary", 1000, "nul_present"),)),
        (BytesSource(b"\xff"), 10, (("binary", 1000, "utf8_invalid"),)),
        (
            BytesSource(b"a\x01"),
            10,
            (
                ("binary", 950, "disallowed_control_present"),
                ("text", 400, "disallowed_control_present"),
            ),
        ),
        (
            BytesSource("界".encode()),
            1,
            (
                ("text", 850, "utf8_prefix_incomplete"),
                ("binary", 500, "utf8_prefix_incomplete"),
            ),
        ),
        (
            BytesSource("界".encode()),
            10,
            (
                ("text", 950, "utf8_valid_non_ascii"),
                ("binary", 400, "utf8_valid_non_ascii"),
            ),
        ),
        (
            BytesSource(b"ascii"),
            10,
            (
                ("text", 900, "utf8_valid_ascii"),
                ("binary", 400, "utf8_valid_ascii"),
            ),
        ),
    ],
)
def test_detection_scoring_table(
    source: BytesSource | TextSource,
    maximum_bytes: int,
    expected: tuple[tuple[str, int, str], ...],
) -> None:
    assert _detect(source, maximum_bytes) == expected


def test_detection_pair_ranking_threshold_and_margin() -> None:
    capabilities = (
        _capability("binary", "binary"),
        _capability("text", "text"),
    )
    with (
        open_source_snapshot(BytesSource(b"abc"), max_input_bytes=10) as before,
        open_source_snapshot(BytesSource(b"xyz"), max_input_bytes=10) as after,
    ):
        selected = detect_pair(before, after, AutoCompareSpec(), capabilities)
        ambiguous = detect_pair(
            before,
            after,
            AutoCompareSpec(minimum_confidence=0, ambiguity_margin=501),
            capabilities,
        )
    assert selected.disposition == "selected"
    assert selected.selected_modality == "text"
    assert [item.modality_id for item in selected.pair_candidates] == [
        "text",
        "binary",
    ]
    assert ambiguous.disposition == "ambiguous"
    assert ambiguous.selected_modality is None


def test_detection_no_match_precedes_ambiguity() -> None:
    capabilities = (
        _capability("binary", "binary"),
        _capability("text", "text"),
    )
    with (
        open_source_snapshot(BytesSource(b""), max_input_bytes=0) as before,
        open_source_snapshot(BytesSource(b""), max_input_bytes=0) as after,
    ):
        record = detect_pair(before, after, AutoCompareSpec(), capabilities)
    assert record.disposition == "no_match"


def test_private_request_normalizes_one_limit_source() -> None:
    spec = AutoCompareSpec(
        limits=AutoResourceLimits(max_input_bytes=10, max_detection_bytes=20)
    )
    request = request_from_spec(spec, (SourceKind.BYTES, SourceKind.PATH))
    assert request.request_version == 1
    assert request.requested_modality == "auto"
    assert request.resolved_modality is None
    assert request.limits.effective_detection_bytes == 10
    assert "limits" not in request.intent
    assert request.with_resolved_modality("binary").resolved_modality == "binary"


def test_capability_catalog_is_order_independent_and_rejects_duplicates() -> None:
    low = _capability("low", "text", priority=10)
    high = _capability("high", "text", priority=0)
    request = request_from_spec(
        AutoCompareSpec(), (SourceKind.BYTES, SourceKind.BYTES)
    ).with_resolved_modality("text")
    selections = []
    for ordered in ((low, high), (high, low)):
        catalog = CapabilityCatalog()
        for item in ordered:
            catalog.register(item)
        resolution = catalog.resolve(request)
        assert resolution.selected is not None
        selections.append(resolution.selected.capability_id)
        reasons = {item.capability_id: item.reason_code for item in resolution.attempts}
        assert reasons == {"low": "lower_priority", "high": None}
    assert selections == ["high", "high"]

    catalog = CapabilityCatalog()
    catalog.register(high)
    with pytest.raises(RuntimeError, match="duplicate"):
        catalog.register(high)


def test_capability_attempts_keep_rejections_in_capability_rank_order() -> None:
    request = request_from_spec(
        AutoCompareSpec(), (SourceKind.BYTES, SourceKind.BYTES)
    ).with_resolved_modality("text")
    catalog = CapabilityCatalog()
    for record in (
        _capability("mismatch", "binary", priority=2),
        _capability("selected", "text", priority=0),
        _capability("lower", "text", priority=1),
    ):
        catalog.register(record)

    resolution = catalog.resolve(request)

    assert tuple(
        (attempt.capability_id, attempt.disposition, attempt.reason_code)
        for attempt in resolution.attempts
    ) == (
        ("lower", "rejected", "lower_priority"),
        ("mismatch", "rejected", "modality_mismatch"),
        ("selected", "selected", None),
    )


def test_capability_catalog_records_every_stable_rejection_reason() -> None:
    request = request_from_spec(
        AutoCompareSpec(), (SourceKind.BYTES, SourceKind.BYTES)
    ).with_resolved_modality("text")
    request = replace(request, required_features=("needed",))
    records = (
        _capability("modality", "binary", features=frozenset({"needed"})),
        _capability(
            "semantic",
            "text",
            semantic_class="approximate",
            features=frozenset({"needed"}),
        ),
        _capability(
            "source",
            "text",
            source_kinds=frozenset({SourceKind.TEXT}),
            features=frozenset({"needed"}),
        ),
        _capability("feature", "text"),
        _capability(
            "missing",
            "text",
            features=frozenset({"needed"}),
            available=False,
        ),
        _capability(
            "version",
            "text",
            features=frozenset({"needed"}),
            version_supported=False,
        ),
        _capability("selected", "text", features=frozenset({"needed"})),
    )
    catalog = CapabilityCatalog()
    for record in reversed(records):
        catalog.register(record)
    resolution = catalog.resolve(request)
    reasons = {item.capability_id: item.reason_code for item in resolution.attempts}
    assert reasons == {
        "feature": "required_feature_missing",
        "missing": "backend_missing",
        "modality": "modality_mismatch",
        "selected": None,
        "semantic": "semantic_class_mismatch",
        "source": "source_kind_unsupported",
        "version": "backend_version_unsupported",
    }


def test_detection_wire_round_trip_and_unknown_count_omission() -> None:
    with (
        open_source_snapshot(BytesSource(b"abc"), max_input_bytes=3) as before,
        open_source_snapshot(BytesSource(b"xyz"), max_input_bytes=3) as after,
    ):
        detection = detect_pair(before, after, AutoCompareSpec(), ())
    execution = ExecutionRecord(
        STAMP,
        STAMP,
        0,
        (
            StageRecord(
                PipelineStage.VALIDATING,
                STAMP,
                STAMP,
                0,
                StageDisposition.COMPLETED,
            ),
            StageRecord(
                PipelineStage.SOURCING,
                STAMP,
                STAMP,
                0,
                StageDisposition.COMPLETED,
            ),
            StageRecord(
                PipelineStage.DETECTING,
                STAMP,
                STAMP,
                0,
                StageDisposition.UNAVAILABLE,
            ),
        ),
        last_completed_stage=PipelineStage.SOURCING,
        detection=detection,
    )
    outcome = UnavailableOutcome(
        execution=execution,
        problem=CapabilityProblem(
            "detection_no_match",
            415,
            PipelineStage.DETECTING,
            "Choose text or binary explicitly.",
        ),
    )
    parsed = json.loads(dumps_outcome(outcome))
    assert isinstance(parsed, dict)
    data = parsed
    detection_data = data["execution"]
    assert isinstance(detection_data, dict)
    wire_detection = detection_data["detection"]
    assert isinstance(wire_detection, dict)
    sources = wire_detection["sources"]
    assert isinstance(sources, list)
    first_source = sources[0]
    assert isinstance(first_source, dict)
    candidates = first_source["candidates"]
    assert isinstance(candidates, list)
    first_candidate = candidates[0]
    assert isinstance(first_candidate, dict)
    counts = first_candidate["evidence_counts"]
    assert isinstance(counts, dict)
    counts["future_count"] = 1
    round_tripped = outcome_from_data(data)
    assert round_tripped == outcome
    assert "future_count" not in dumps_outcome(round_tripped)


def test_detection_wire_requires_all_counts_and_sorted_candidates() -> None:
    with (
        open_source_snapshot(BytesSource(b""), max_input_bytes=0) as before,
        open_source_snapshot(BytesSource(b""), max_input_bytes=0) as after,
    ):
        detection = detect_pair(before, after, AutoCompareSpec(), ())
    assert isinstance(detection, DetectionRecord)
    execution = ExecutionRecord(
        STAMP,
        STAMP,
        0,
        (
            StageRecord(
                PipelineStage.VALIDATING,
                STAMP,
                STAMP,
                0,
                StageDisposition.COMPLETED,
            ),
            StageRecord(
                PipelineStage.SOURCING,
                STAMP,
                STAMP,
                0,
                StageDisposition.COMPLETED,
            ),
            StageRecord(
                PipelineStage.DETECTING,
                STAMP,
                STAMP,
                0,
                StageDisposition.UNAVAILABLE,
            ),
        ),
        last_completed_stage=PipelineStage.SOURCING,
        detection=detection,
    )
    outcome = UnavailableOutcome(
        execution=execution,
        problem=CapabilityProblem(
            "detection_no_match",
            415,
            PipelineStage.DETECTING,
            "Choose text or binary explicitly.",
        ),
    )
    data = outcome_to_data(outcome)
    execution_data = data["execution"]
    assert isinstance(execution_data, dict)
    detection_data = execution_data["detection"]
    assert isinstance(detection_data, dict)
    sources = detection_data["sources"]
    assert isinstance(sources, list)
    source = sources[0]
    assert isinstance(source, dict)
    candidates = source["candidates"]
    assert isinstance(candidates, list)
    candidate = candidates[0]
    assert isinstance(candidate, dict)
    counts = candidate["evidence_counts"]
    assert isinstance(counts, dict)
    del counts["nul_count"]
    with pytest.raises(SerializationError, match="missing detection evidence"):
        outcome_from_data(data)
