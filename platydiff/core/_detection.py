"""Deterministic bounded-prefix text/binary detection."""

from __future__ import annotations

import codecs
from typing import Literal

from platydiff.core._capabilities import CapabilityRecord
from platydiff.core._sources import SourceSnapshot
from platydiff.core.models import (
    AutoCompareSpec,
    DetectionCandidate,
    DetectionRecord,
    JsonObject,
    PairDetectionCandidate,
    PipelineStage,
    SourceDetectionRecord,
    SourceKind,
)

DETECTOR_ID = "core.text_binary_prefix"
DETECTOR_VERSION = "1"
DETECTOR_PRIORITY = 0
_COUNT_KEYS = (
    "inspected_bytes",
    "nul_count",
    "non_ascii_byte_count",
    "pending_utf8_bytes",
    "disallowed_control_count",
)


def detect_pair(
    before: SourceSnapshot,
    after: SourceSnapshot,
    spec: AutoCompareSpec,
    capabilities: tuple[CapabilityRecord, ...],
) -> DetectionRecord:
    """Detect and rank one source pair using only bounded deterministic evidence."""
    maximum_bytes = min(spec.limits.max_detection_bytes, spec.limits.max_input_bytes)
    before_record = _detect_source(before, "before", maximum_bytes)
    after_record = _detect_source(after, "after", maximum_bytes)
    pair_candidates = _pair_candidates(before_record, after_record, capabilities)
    disposition: Literal["selected", "no_match", "ambiguous"]
    selected: Literal["text", "binary"] | None
    if not pair_candidates or pair_candidates[0].confidence < spec.minimum_confidence:
        disposition = "no_match"
        selected = None
    elif (
        len(pair_candidates) > 1
        and pair_candidates[0].confidence - pair_candidates[1].confidence
        < spec.ambiguity_margin
    ):
        disposition = "ambiguous"
        selected = None
    else:
        disposition = "selected"
        selected = pair_candidates[0].modality_id
    return DetectionRecord(
        detector_id=DETECTOR_ID,
        detector_version=DETECTOR_VERSION,
        maximum_bytes=maximum_bytes,
        minimum_confidence=spec.minimum_confidence,
        ambiguity_margin=spec.ambiguity_margin,
        sources=(before_record, after_record),
        pair_candidates=pair_candidates,
        disposition=disposition,
        selected_modality=selected,
    )


def _detect_source(
    snapshot: SourceSnapshot,
    role: Literal["before", "after"],
    maximum_bytes: int,
) -> SourceDetectionRecord:
    if snapshot.source_kind is SourceKind.TEXT:
        return SourceDetectionRecord(
            role,
            (_candidate("text", 1000, "explicit_text_source", _zero_counts()),),
        )
    prefix = snapshot.read_prefix(maximum_bytes, stage=PipelineStage.DETECTING)
    counts = _counts(prefix)
    candidates: tuple[DetectionCandidate, ...]
    if snapshot.size_bytes == 0:
        candidates = (
            _candidate("text", 500, "empty_source", counts),
            _candidate("binary", 500, "empty_source", counts),
        )
    elif not prefix:
        candidates = (
            _candidate("text", 500, "content_not_inspected", counts),
            _candidate("binary", 500, "content_not_inspected", counts),
        )
    else:
        candidates = _classify(prefix, snapshot.size_bytes <= len(prefix), counts)
    return SourceDetectionRecord(role, candidates)


def _counts(prefix: bytes) -> JsonObject:
    return {
        "inspected_bytes": len(prefix),
        "nul_count": prefix.count(0),
        "non_ascii_byte_count": sum(byte >= 0x80 for byte in prefix),
        "pending_utf8_bytes": 0,
        "disallowed_control_count": 0,
    }


def _zero_counts() -> JsonObject:
    return {key: 0 for key in _COUNT_KEYS}


def _classify(
    prefix: bytes, reached_eof: bool, counts: JsonObject
) -> tuple[DetectionCandidate, ...]:
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    invalid = False
    try:
        decoded = decoder.decode(prefix, final=reached_eof)
    except UnicodeDecodeError as error:
        invalid = True
        decoded = prefix[: error.start].decode("utf-8", errors="strict")
    pending = b"" if invalid or reached_eof else decoder.getstate()[0]
    counts["pending_utf8_bytes"] = len(pending)
    counts["disallowed_control_count"] = sum(
        _is_disallowed_control(character) for character in decoded
    )
    if _count(counts, "nul_count") > 0:
        return (_candidate("binary", 1000, "nul_present", counts),)
    if invalid:
        return (_candidate("binary", 1000, "utf8_invalid", counts),)
    if _count(counts, "disallowed_control_count") > 0:
        return (
            _candidate("binary", 950, "disallowed_control_present", counts),
            _candidate("text", 400, "disallowed_control_present", counts),
        )
    if pending:
        return (
            _candidate("text", 850, "utf8_prefix_incomplete", counts),
            _candidate("binary", 500, "utf8_prefix_incomplete", counts),
        )
    if _count(counts, "non_ascii_byte_count") > 0:
        return (
            _candidate("text", 950, "utf8_valid_non_ascii", counts),
            _candidate("binary", 400, "utf8_valid_non_ascii", counts),
        )
    return (
        _candidate("text", 900, "utf8_valid_ascii", counts),
        _candidate("binary", 400, "utf8_valid_ascii", counts),
    )


def _is_disallowed_control(character: str) -> bool:
    value = ord(character)
    return (value < 0x20 or 0x7F <= value <= 0x9F) and value not in (
        0,
        9,
        10,
        13,
    )


def _count(counts: JsonObject, key: str) -> int:
    value = counts[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError("internal detection count is not an integer")
    return value


def _candidate(
    modality: Literal["text", "binary"],
    confidence: int,
    evidence_code: str,
    counts: JsonObject,
) -> DetectionCandidate:
    return DetectionCandidate(
        modality_id=modality,
        confidence=confidence,
        detector_id=DETECTOR_ID,
        detector_version=DETECTOR_VERSION,
        priority=DETECTOR_PRIORITY,
        evidence_codes=(evidence_code,),
        evidence_counts=dict(counts),
    )


def _pair_candidates(
    before: SourceDetectionRecord,
    after: SourceDetectionRecord,
    capabilities: tuple[CapabilityRecord, ...],
) -> tuple[PairDetectionCandidate, ...]:
    before_by_modality = {item.modality_id: item for item in before.candidates}
    after_by_modality = {item.modality_id: item for item in after.candidates}
    candidates: list[PairDetectionCandidate] = []
    for capability in capabilities:
        before_candidate = before_by_modality.get(capability.modality)
        after_candidate = after_by_modality.get(capability.modality)
        if before_candidate is None or after_candidate is None:
            continue
        candidates.append(
            PairDetectionCandidate(
                modality_id=capability.modality,
                confidence=min(before_candidate.confidence, after_candidate.confidence),
                before_confidence=before_candidate.confidence,
                after_confidence=after_candidate.confidence,
                detector_priority=min(
                    before_candidate.priority, after_candidate.priority
                ),
                capability_priority=capability.priority,
                capability_id=capability.capability_id,
                backend_id=capability.backend_id,
            )
        )
    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                -item.confidence,
                item.detector_priority,
                item.capability_priority,
                item.modality_id,
                item.capability_id,
                item.backend_id,
            ),
        )
    )
