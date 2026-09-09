from __future__ import annotations

from dataclasses import replace

import pytest

from platydiff import (
    CompareOutcomeV3,
    CompletedOutcomeV3,
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
from platydiff.core.models import ChangeSet
from platydiff.core.serialization import (
    SerializationError,
    dumps_outcome,
    loads_outcome,
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
    original = compare(TextSource("a"), TextSource("a"), TextCompareSpec())
    upgraded = upgrade_outcome_v1_to_v3(original)
    assert isinstance(upgraded, CompletedOutcomeV3)
    result = replace(
        upgraded.result,
        changes=ChangeSet(
            completeness=upgraded.result.changes.completeness,
            items=(change,),
            total_count=1,
            returned_count=1,
            omitted_count=0,
            selection=upgraded.result.changes.selection,
            limit=None,
        ),
        summary=replace(upgraded.result.summary, change_count=1),
        provenance=replace(
            upgraded.result.provenance,
            spec=spec_to_data(JsonCompareSpec(detail_mode=StructuredDetailMode.VALUES)),
        ),
    )
    outcome = CompletedOutcomeV3(execution=upgraded.execution, result=result)

    assert loads_outcome(dumps_outcome(outcome)) == outcome
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
