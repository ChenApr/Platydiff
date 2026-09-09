from __future__ import annotations

import pytest

from platydiff import (
    BytesSource,
    CompletedOutcomeV3,
    FailedOutcomeV3,
    JsonCompareSpec,
    JsonNumberMode,
    StructuredDetailMode,
    StructuredResourceLimits,
    StructuredType,
    SubtreeFact,
    TextEncoding,
    TextSource,
    compare,
)
from platydiff.core.models import (
    ChangeCompleteness,
    StructuredChange,
    UnavailableOutcomeV3,
)
from platydiff.core.serialization import dumps_outcome, loads_outcome
from platydiff.plugins import PluginCatalogV1, PluginHost


def completed(
    before: str, after: str, spec: JsonCompareSpec | None = None
) -> CompletedOutcomeV3:
    outcome = compare(TextSource(before), TextSource(after), spec or JsonCompareSpec())
    assert isinstance(outcome, CompletedOutcomeV3)
    return outcome


def test_identical_and_object_order_are_semantically_equal() -> None:
    outcome = completed('{"b":[1,true],"a":null}', '{"a":null,"b":[1,true]}')

    assert outcome.result.relation.value == "equal"
    assert outcome.result.summary.change_count == 0
    metrics = {item.name: item.value.value for item in outcome.result.metrics}  # type: ignore[union-attr]
    assert metrics == {
        "json.changed_values": 0.0,
        "json.compared_values": 3.0,
        "json.equal_values": 3.0,
    }
    assert [
        item.transformation_id for item in outcome.result.provenance.transformations
    ] == [
        "json.object_order.ignore",
        "json.number.value",
        "json.pointer.position",
    ]


def test_depth_first_changes_use_canonical_pointers_and_subtree_roots() -> None:
    outcome = completed(
        '{"z":[0,{"gone":true}],"a/b":1,"~":[]}',
        '{"z":[0,{"new":[1,2]}],"a/b":2,"~":[]}',
    )
    changes = outcome.result.changes.items

    assert [item.path for item in changes if isinstance(item, StructuredChange)] == [
        "/a~1b",
        "/z/1/gone",
        "/z/1/new",
    ]
    removed = changes[1]
    added = changes[2]
    assert isinstance(removed, StructuredChange)
    assert isinstance(added, StructuredChange)
    assert removed.operation == "remove"
    assert added.operation == "add"
    assert added.after_type is StructuredType.SEQUENCE
    assert isinstance(added.after_fact, SubtreeFact)
    assert added.after_fact.kind == "sequence"
    assert added.after_fact.descendant_count == 2


@pytest.mark.parametrize("before", ["", "{}{}", "[1,]", "NaN", '"\\ud800"'])
def test_strict_json_failures_are_schema_v3_decode_errors(before: str) -> None:
    outcome = compare(TextSource(before), TextSource("null"), JsonCompareSpec())

    assert isinstance(outcome, FailedOutcomeV3)
    assert outcome.problem.code == "decode_error"
    assert outcome.problem.stage.value == "decoding"


def test_duplicate_keys_are_detected_after_escape_decoding() -> None:
    outcome = compare(
        TextSource('{"a":1,"\\u0061":2}'), TextSource("{}"), JsonCompareSpec()
    )

    assert isinstance(outcome, FailedOutcomeV3)
    assert outcome.problem.code == "decode_error"


def test_bom_requires_explicit_utf8_sig() -> None:
    strict = compare(
        BytesSource(b"\xef\xbb\xbfnull"), BytesSource(b"null"), JsonCompareSpec()
    )
    allowed = compare(
        BytesSource(b"\xef\xbb\xbfnull"),
        BytesSource(b"null"),
        JsonCompareSpec(encoding=TextEncoding.UTF8_SIG),
    )

    assert isinstance(strict, FailedOutcomeV3)
    assert strict.problem.code == "decode_error"
    assert isinstance(allowed, CompletedOutcomeV3)
    assert allowed.result.relation.value == "equal"


def test_value_and_lexical_number_modes_have_distinct_truth() -> None:
    value = completed("1", "1.0")
    lexical = completed("1", "1.0", JsonCompareSpec(number_mode=JsonNumberMode.LEXICAL))

    assert value.result.relation.value == "equal"
    assert lexical.result.relation.value == "different"
    change = lexical.result.changes.items[0]
    assert isinstance(change, StructuredChange)
    assert change.before_digest != change.after_digest
    assert change.before_fact is not None
    assert change.before_fact.lexical == "1"  # type: ignore[union-attr]
    assert change.after_fact is not None
    assert change.after_fact.lexical == "1.0"  # type: ignore[union-attr]


def test_evidence_digest_framing_has_a_fixed_low_entropy_fixture() -> None:
    value = completed("1", "2").result.changes.items[0]
    lexical = completed(
        "1", "2", JsonCompareSpec(number_mode=JsonNumberMode.LEXICAL)
    ).result.changes.items[0]
    assert isinstance(value, StructuredChange)
    assert isinstance(lexical, StructuredChange)

    assert value.before_digest == (
        "cb6fe2f774410f38625faceb917d2577927b9df0d316ae6b22e0200bcafb214a"
    )
    assert lexical.before_digest == (
        "7bcae48451a8fb46949ab9cb931d4661bb34c3a497016dc1036a0b23def79b5a"
    )


def test_digest_only_omits_facts_without_changing_truth_or_digests() -> None:
    values = completed('{"secret":"old"}', '{"secret":"new"}')
    digest_only = completed(
        '{"secret":"old"}',
        '{"secret":"new"}',
        JsonCompareSpec(detail_mode=StructuredDetailMode.DIGEST_ONLY),
    )
    values_change = values.result.changes.items[0]
    digest_change = digest_only.result.changes.items[0]
    assert isinstance(values_change, StructuredChange)
    assert isinstance(digest_change, StructuredChange)

    assert digest_only.result.relation == values.result.relation
    assert digest_only.result.summary == values.result.summary
    assert digest_change.before_fact is None
    assert digest_change.after_fact is None
    assert digest_change.before_digest == values_change.before_digest
    assert digest_change.after_digest == values_change.after_digest


@pytest.mark.parametrize(
    ("limits", "source"),
    [
        (StructuredResourceLimits(max_nodes=1), "[0]"),
        (StructuredResourceLimits(max_depth=0), "[0]"),
        (StructuredResourceLimits(max_scalar_bytes=1), '"é"'),
        (StructuredResourceLimits(max_number_digits=1), "10"),
        (StructuredResourceLimits(max_abs_exponent=1), "1e2"),
    ],
)
def test_decode_resource_limits_are_structured(
    limits: StructuredResourceLimits, source: str
) -> None:
    outcome = compare(
        TextSource(source), TextSource(source), JsonCompareSpec(limits=limits)
    )

    assert isinstance(outcome, FailedOutcomeV3)
    assert outcome.problem.code == "resource_limit_exceeded"
    assert outcome.problem.stage.value == "decoding"


def test_compare_work_limit_charges_before_next_node() -> None:
    limits = StructuredResourceLimits(max_compare_work=1)
    outcome = compare(
        TextSource("[1]"), TextSource("[1]"), JsonCompareSpec(limits=limits)
    )

    assert isinstance(outcome, FailedOutcomeV3)
    assert outcome.problem.code == "compare_resource_limit"
    assert outcome.problem.details == {"used": 2, "limit": 1}


def test_sdk_v1_plugin_host_rejects_json_at_resolution() -> None:
    host = PluginHost(PluginCatalogV1((), (), (), (), ()))

    outcome = host.compare(TextSource("null"), TextSource("null"), JsonCompareSpec())

    assert isinstance(outcome, UnavailableOutcomeV3)
    assert outcome.problem.code == "capability_unavailable"
    assert outcome.problem.stage.value == "resolving"


def test_atomic_change_truncation_and_schema_round_trip() -> None:
    truncated = completed(
        '["old",0]',
        '["new",1]',
        JsonCompareSpec(limits=StructuredResourceLimits(max_change_items=1)),
    )

    assert truncated.result.changes.completeness is ChangeCompleteness.TRUNCATED
    assert truncated.result.changes.returned_count == 1
    assert truncated.result.changes.total_count == 2
    assert truncated.result.summary.change_count == 2
    assert loads_outcome(dumps_outcome(truncated)) == truncated
