from __future__ import annotations

import copy

import pytest

from platydiff import (
    BytesSource,
    CompareOutcomeV3,
    CompletedOutcomeV3,
    FailedOutcomeV3,
    JsonCompareSpec,
    ScalarFact,
    StructuredChange,
    StructuredDetailMode,
    StructuredType,
    TextCompareSpec,
    TextSource,
    compare,
    downgrade_outcome_v3_to_v2,
    upgrade_outcome_v1_to_v3,
)
from platydiff.core.serialization import (
    SerializationError,
    dumps_outcome,
    loads_outcome,
    outcome_from_data,
    outcome_to_data,
    spec_from_data,
    spec_to_data,
)


def test_json_spec_round_trip_includes_all_effective_defaults() -> None:
    spec = JsonCompareSpec()

    assert spec_from_data(spec_to_data(spec)) == spec
    assert spec_to_data(spec) == {
        "kind": "json",
        "encoding": "utf-8",
        "number_mode": "value",
        "detail_mode": "values",
        "limits": {
            "max_input_bytes": 16 * 1024 * 1024,
            "max_scalar_bytes": 1024 * 1024,
            "max_depth": 256,
            "max_nodes": 1_000_000,
            "max_number_digits": 10_000,
            "max_abs_exponent": 1_000_000,
            "max_compare_work": 5_000_000,
            "max_change_items": 10_000,
            "max_change_payload_bytes": 4 * 1024 * 1024,
        },
    }


def test_v1_upgrade_and_legacy_only_v3_downgrade_are_lossless() -> None:
    original = compare(TextSource("same"), TextSource("same"), TextCompareSpec())
    upgraded: CompareOutcomeV3 = upgrade_outcome_v1_to_v3(original)

    assert loads_outcome(dumps_outcome(upgraded)) == upgraded
    assert downgrade_outcome_v3_to_v2(upgraded).result == upgraded.result  # type: ignore[union-attr]

    failed = compare(BytesSource(b"\xff"), BytesSource(b"\xff"), TextCompareSpec())
    failed_v3 = upgrade_outcome_v1_to_v3(failed)
    assert downgrade_outcome_v3_to_v2(failed_v3).kind == "failed"


def test_native_json_terminal_outcome_cannot_claim_legacy_downgrade() -> None:
    outcome = compare(TextSource("{"), TextSource("{}"), JsonCompareSpec())
    assert isinstance(outcome, FailedOutcomeV3)

    with pytest.raises(SerializationError, match="proven legacy-only"):
        downgrade_outcome_v3_to_v2(outcome)


def test_structured_change_invariants_and_schema_gate() -> None:
    change = StructuredChange(
        operation="replace",
        path="/a~1b",
        before_type=StructuredType.INTEGER,
        after_type=StructuredType.INTEGER,
        before_digest="0" * 64,
        after_digest="1" * 64,
        before_fact=ScalarFact("integer", "1"),
        after_fact=ScalarFact("integer", "2"),
    )
    assert change.before_fact == ScalarFact("integer", "1")
    outcome = compare(
        TextSource("1"),
        TextSource("2"),
        JsonCompareSpec(detail_mode=StructuredDetailMode.VALUES),
    )
    assert isinstance(outcome, CompletedOutcomeV3)
    with pytest.raises(SerializationError, match="not legacy-only"):
        downgrade_outcome_v3_to_v2(outcome)


def test_structured_change_rejects_mismatched_side_facts() -> None:
    with pytest.raises(ValueError, match="absent before"):
        StructuredChange(
            operation="add",
            after_type=StructuredType.NULL,
            after_digest="0" * 64,
            before_fact=ScalarFact("null", None),
        )
    with pytest.raises(ValueError, match="fact kind"):
        StructuredChange(
            operation="replace",
            before_type=StructuredType.STRING,
            after_type=StructuredType.STRING,
            before_digest="0" * 64,
            after_digest="1" * 64,
            before_fact=ScalarFact("integer", "1"),
            after_fact=ScalarFact("string", "x"),
        )


@pytest.mark.parametrize("value", ["10E0", "1E-0", "-0E0"])
def test_decimal_facts_require_canonical_value_text(value: str) -> None:
    with pytest.raises(ValueError, match="canonical"):
        ScalarFact("decimal", value)


def test_json_spec_requires_public_enum_instances() -> None:
    with pytest.raises(ValueError, match="number_mode"):
        JsonCompareSpec(number_mode="value")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="detail_mode"):
        JsonCompareSpec(detail_mode="values")  # type: ignore[arg-type]


def test_schema_v3_reader_enforces_json_detail_and_transformations() -> None:
    outcome = compare(TextSource("1"), TextSource("2"), JsonCompareSpec())
    assert isinstance(outcome, CompletedOutcomeV3)
    data = copy.deepcopy(outcome_to_data(outcome))
    result = data["result"]
    assert isinstance(result, dict)
    provenance = result["provenance"]
    assert isinstance(provenance, dict)
    spec = provenance["spec"]
    assert isinstance(spec, dict)
    spec["detail_mode"] = "digest_only"

    with pytest.raises(SerializationError, match="digest_only"):
        outcome_from_data(data)

    data = copy.deepcopy(outcome_to_data(outcome))
    result = data["result"]
    assert isinstance(result, dict)
    provenance = result["provenance"]
    assert isinstance(provenance, dict)
    transformations = provenance["transformations"]
    assert isinstance(transformations, list)
    first = transformations[0]
    assert isinstance(first, dict)
    first["transformation_id"] = "json.unknown"

    with pytest.raises(SerializationError, match="transformations"):
        outcome_from_data(data)
