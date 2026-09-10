from __future__ import annotations

import json
from dataclasses import replace
from typing import cast

import pytest

from platydiff import (
    ArrayChange,
    ArrayCompareSpec,
    ArrayResourceLimits,
    BytesSource,
    ColumnOrderFact,
    ColumnSchemaFact,
    ColumnSpec,
    CompletedOutcomeV3,
    JsonCompareSpec,
    NumericPolicy,
    ScalarFact,
    TableChange,
    TableCompareSpec,
    TableResourceLimits,
    TableRowFact,
    TextEncoding,
    TextSource,
    UnavailableOutcomeV3,
    YamlCompareSpec,
    YamlResourceLimits,
    compare,
)
from platydiff.core.models import (
    CapabilityAttemptV2,
    ChangeCompleteness,
    ChangeSelection,
    ChangeSet,
    ComparisonProvenanceV2,
    DiffSummary,
    FiniteValue,
    JsonObject,
    Metric,
    MetricDirection,
    PolicyEvaluation,
    PositiveInfinityValue,
    Relation,
    ResourceUsage,
    SummaryCount,
    TransformationRecord,
    Verdict,
)
from platydiff.core.serialization import (
    SerializationError,
    _change_from_data,
    _change_to_data,
    dumps_outcome,
    loads_outcome,
    outcome_from_data,
    outcome_to_data,
    spec_from_data,
    spec_to_data,
)
from platydiff.plugins import PluginCatalogV1, PluginHost


def _contract_outcome(
    spec: YamlCompareSpec | TableCompareSpec | ArrayCompareSpec,
) -> CompletedOutcomeV3:
    base = compare(TextSource("0"), TextSource("0"), JsonCompareSpec())
    assert isinstance(base, CompletedOutcomeV3)
    transformations: tuple[TransformationRecord, ...]
    if isinstance(spec, YamlCompareSpec):
        prefix = "yaml"
        algorithm = "yaml.structural.tree.v1"
        count_values = {
            "compared_values": 1,
            "equal_values": 1,
            "changed_values": 0,
        }
        directions = {
            "compared_values": MetricDirection.NEUTRAL,
            "equal_values": MetricDirection.NEUTRAL,
            "changed_values": MetricDirection.LOWER_IS_BETTER,
        }
        summary_unit = "values"
        transformations = (
            TransformationRecord("normalizing", "yaml.presentation.elide"),
            TransformationRecord("normalizing", "yaml.object_order.ignore"),
            TransformationRecord("aligning", "yaml.pointer.position"),
        )
        resources: dict[str, tuple[int, int]] = {}
        for side in ("before", "after"):
            resources.update(
                {
                    f"{side}_input_bytes": (spec.limits.max_input_bytes, 1),
                    f"{side}_scalar_bytes": (spec.limits.max_scalar_bytes, 0),
                    f"{side}_depth": (spec.limits.max_depth, 0),
                    f"{side}_nodes": (spec.limits.max_nodes, 1),
                    f"{side}_number_digits": (spec.limits.max_number_digits, 1),
                    f"{side}_abs_exponent": (spec.limits.max_abs_exponent, 0),
                    f"{side}_aliases": (spec.limits.max_aliases, 0),
                    f"{side}_expanded_nodes": (spec.limits.max_expanded_nodes, 1),
                    f"{side}_expanded_scalar_bytes": (
                        spec.limits.max_expanded_scalar_bytes,
                        0,
                    ),
                }
            )
        resources.update(
            {
                "compare_work": (spec.limits.max_compare_work, 1),
                "change_items": (spec.limits.max_change_items, 0),
                "change_payload_bytes": (
                    spec.limits.max_change_payload_bytes,
                    0,
                ),
            }
        )
        rule_id = "yaml.semantic_equality"
        metric_name = "yaml.changed_values"
    elif isinstance(spec, TableCompareSpec):
        prefix = "table"
        algorithm = "table.delimited.align.v1"
        count_values = {
            "compared_cells": 1,
            "equal_cells": 1,
            "changed_cells": 0,
            "changed_items": 0,
            "missing_pairs": 0,
            "nan_pairs": 0,
            "infinity_pairs": 0,
            "finite_numeric_pairs": 0,
        }
        directions = {
            name: (
                MetricDirection.LOWER_IS_BETTER
                if name in ("changed_cells", "changed_items")
                else MetricDirection.NEUTRAL
            )
            for name in count_values
        }
        summary_unit = "cells"
        transformations_list = [
            TransformationRecord("decoding", f"table.{spec.dialect}.decode"),
            TransformationRecord("normalizing", "table.presentation.elide"),
        ]
        if spec.columns:
            transformations_list.append(
                TransformationRecord("normalizing", "table.cells.typed")
            )
        transformations_list.extend(
            (
                TransformationRecord("aligning", f"table.columns.{spec.column_order}"),
                TransformationRecord("aligning", f"table.rows.{spec.alignment}"),
            )
        )
        transformations = tuple(transformations_list)
        resources = {}
        for side in ("before", "after"):
            resources.update(
                {
                    f"{side}_input_bytes": (spec.limits.max_input_bytes, 1),
                    f"{side}_cell_bytes": (spec.limits.max_cell_bytes, 1),
                    f"{side}_rows": (spec.limits.max_rows, 1),
                    f"{side}_columns": (spec.limits.max_columns, 1),
                    f"{side}_cells": (spec.limits.max_cells, 1),
                    f"{side}_number_digits": (spec.limits.max_number_digits, 0),
                    f"{side}_abs_exponent": (spec.limits.max_abs_exponent, 0),
                }
            )
        resources.update(
            {
                "compare_work": (spec.limits.max_compare_work, 1),
                "change_items": (spec.limits.max_change_items, 0),
                "change_payload_bytes": (
                    spec.limits.max_change_payload_bytes,
                    0,
                ),
            }
        )
        rule_id = "table.value_equality"
        metric_name = "table.changed_items"
    else:
        prefix = "array"
        algorithm = "array.position.numeric.v1"
        count_values = {
            "compared_elements": 1,
            "equal_elements": 1,
            "changed_elements": 0,
            "changed_items": 0,
            "missing_pairs": 0,
            "nan_pairs": 0,
            "infinity_pairs": 0,
            "finite_numeric_pairs": 0,
        }
        directions = {
            name: (
                MetricDirection.LOWER_IS_BETTER
                if name in ("changed_elements", "changed_items")
                else MetricDirection.NEUTRAL
            )
            for name in count_values
        }
        summary_unit = "elements"
        transformations = (TransformationRecord("aligning", "array.elements.position"),)
        resources = {
            "before_rank": (spec.limits.max_rank, 1),
            "before_elements": (spec.limits.max_elements, 1),
            "after_rank": (spec.limits.max_rank, 1),
            "after_elements": (spec.limits.max_elements, 1),
            "compare_work": (spec.limits.max_compare_work, 3),
            "change_items": (spec.limits.max_change_items, 0),
            "change_payload_bytes": (spec.limits.max_change_payload_bytes, 0),
        }
        rule_id = "array.value_equality"
        metric_name = "array.changed_items"

    provenance = replace(
        cast(ComparisonProvenanceV2, base.result.provenance),
        spec=spec_to_data(spec),
        transformations=transformations,
        comparator_id=prefix,
        comparator_version="1",
        algorithm_id=algorithm,
        resources=tuple(
            ResourceUsage(name, limit, used)
            for name, (limit, used) in resources.items()
        ),
    )
    metrics = tuple(
        Metric(
            f"{prefix}.{name}",
            FiniteValue(value),
            "items",
            directions[name],
            "count",
        )
        for name, value in count_values.items()
    )
    result = replace(
        base.result,
        relation=Relation.EQUAL,
        verdict=Verdict.PASS,
        summary=DiffSummary(
            0,
            tuple(
                SummaryCount(name, value, summary_unit)
                for name, value in count_values.items()
            ),
        ),
        changes=ChangeSet(
            ChangeCompleteness.COMPLETE,
            (),
            0,
            0,
            0,
            ChangeSelection.ALL,
            None,
        ),
        metrics=metrics,
        evaluations=(
            PolicyEvaluation(
                rule_id,
                Verdict.PASS,
                metric_name,
                "eq",
                FiniteValue(0),
                FiniteValue(0),
            ),
        ),
        provenance=provenance,
    )
    execution = replace(
        base.execution,
        attempts=(
            CapabilityAttemptV2(
                prefix,
                None,
                "selected",
                capability_version="1",
            ),
        ),
    )
    return CompletedOutcomeV3(execution=execution, result=result)


def test_yaml_spec_round_trip_includes_all_effective_defaults() -> None:
    spec = YamlCompareSpec()

    assert spec_from_data(spec_to_data(spec)) == spec
    assert spec_to_data(spec) == {
        "kind": "yaml",
        "profile": "yaml12_core_safe",
        "encoding": "utf-8",
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
            "max_aliases": 10_000,
            "max_expanded_nodes": 1_000_000,
            "max_expanded_scalar_bytes": 16 * 1024 * 1024,
        },
    }


@pytest.mark.parametrize(
    "spec",
    [YamlCompareSpec(), TableCompareSpec(dialect="csv"), ArrayCompareSpec()],
)
def test_contract_only_completed_fixtures_round_trip_canonically(
    spec: YamlCompareSpec | TableCompareSpec | ArrayCompareSpec,
) -> None:
    outcome = _contract_outcome(spec)
    encoded = dumps_outcome(outcome)

    assert loads_outcome(encoded) == outcome
    assert dumps_outcome(loads_outcome(encoded)) == encoded


@pytest.mark.parametrize(
    "spec",
    [YamlCompareSpec(), TableCompareSpec(dialect="csv"), ArrayCompareSpec()],
)
def test_contract_only_fixtures_reject_noncanonical_attempts(
    spec: YamlCompareSpec | TableCompareSpec | ArrayCompareSpec,
) -> None:
    data = outcome_to_data(_contract_outcome(spec))
    execution = cast(JsonObject, data["execution"])
    attempts = cast(list[object], execution["attempts"])
    cast(JsonObject, attempts[0])["backend_id"] = "stdlib"

    with pytest.raises(SerializationError, match="attempt is not canonical"):
        outcome_from_data(data)


@pytest.mark.parametrize(
    "spec",
    [YamlCompareSpec(), TableCompareSpec(dialect="csv"), ArrayCompareSpec()],
)
def test_sdk_v1_host_rejects_contract_only_specs_before_execution(
    spec: YamlCompareSpec | TableCompareSpec | ArrayCompareSpec,
) -> None:
    host = PluginHost(PluginCatalogV1((), (), (), (), ()))

    outcome = host.compare(BytesSource(b"0"), BytesSource(b"0"), spec)

    assert isinstance(outcome, UnavailableOutcomeV3)
    assert outcome.problem.stage.value == "resolving"
    assert outcome.problem.code == "capability_unavailable"
    with pytest.raises(TypeError, match="unsupported comparison specification"):
        compare(BytesSource(b"0"), BytesSource(b"0"), spec)  # type: ignore[call-overload]


def test_table_spec_round_trip_freezes_encoding_and_numeric_policy() -> None:
    spec = TableCompareSpec(
        dialect="csv",
        encoding=TextEncoding.UTF8_SIG,
        columns=(
            ColumnSpec("id", "integer"),
            ColumnSpec(
                "value",
                "float64",
                ("NA",),
                NumericPolicy(atol=0.25, rtol=0.5, nan_equal=True),
            ),
        ),
    )

    assert spec_from_data(spec_to_data(spec)) == spec
    data = spec_to_data(spec)
    assert list(data) == [
        "kind",
        "dialect",
        "encoding",
        "header",
        "alignment",
        "key_columns",
        "column_order",
        "columns",
        "detail_mode",
        "limits",
    ]
    assert data["encoding"] == "utf-8-sig"
    assert data["columns"] == [
        {
            "name": "id",
            "dtype": "integer",
            "missing_tokens": [],
            "numeric": None,
        },
        {
            "name": "value",
            "dtype": "float64",
            "missing_tokens": ["NA"],
            "numeric": {
                "atol": 0.25,
                "rtol": 0.5,
                "relative_reference": "before",
                "nan_equal": True,
                "signed_zero_equal": True,
            },
        },
    ]


def test_table_spec_defaults_and_limits_are_explicit() -> None:
    spec = TableCompareSpec(dialect="tsv")

    assert spec_from_data(spec_to_data(spec)) == spec
    assert spec_to_data(spec) == {
        "kind": "table",
        "dialect": "tsv",
        "encoding": "utf-8",
        "header": "first_row",
        "alignment": "position",
        "key_columns": [],
        "column_order": "exact",
        "columns": [],
        "detail_mode": "values",
        "limits": {
            name: getattr(TableResourceLimits(), name)
            for name in TableResourceLimits.__dataclass_fields__
        },
    }


def test_array_spec_round_trip_includes_all_effective_defaults() -> None:
    spec = ArrayCompareSpec()

    assert spec_from_data(spec_to_data(spec)) == spec
    assert spec_to_data(spec) == {
        "kind": "array",
        "alignment": "position",
        "numeric": {
            "atol": 0.0,
            "rtol": 0.0,
            "relative_reference": "before",
            "nan_equal": False,
            "signed_zero_equal": True,
        },
        "limits": {
            name: getattr(ArrayResourceLimits(), name)
            for name in ArrayResourceLimits.__dataclass_fields__
        },
    }


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: NumericPolicy(atol=float("nan")),
        lambda: NumericPolicy(rtol=float("inf")),
        lambda: NumericPolicy(atol=-1.0),
        lambda: ColumnSpec("x", "float64"),
        lambda: ColumnSpec("x", "string", numeric=NumericPolicy()),
        lambda: TableCompareSpec(dialect="csv", alignment="key"),
        lambda: TableCompareSpec(
            dialect="csv", alignment="position", key_columns=("id",)
        ),
    ],
)
def test_new_spec_models_reject_ambiguous_or_non_finite_policy(
    constructor: object,
) -> None:
    with pytest.raises(ValueError):
        constructor()  # type: ignore[operator]


def test_table_fact_wire_shape_is_discriminated_and_ordered() -> None:
    row = TableRowFact(
        cells=(("b", ScalarFact("string", "2")), ("a", ScalarFact("integer", "1")))
    )
    schema = ColumnSchemaFact("value", "float64", 1, NumericPolicy(atol=0.1))
    order = ColumnOrderFact(("b", "a"))
    change = TableChange(
        operation="row_add",
        row=1,
        after_digest="a" * 64,
        after_fact=row,
    )

    assert _change_from_data(_change_to_data(change), schema_version=3) == change
    assert _change_to_data(change)["after_fact"] == {
        "kind": "table_row",
        "cells": [
            ["b", {"kind": "string", "value": "2"}],
            ["a", {"kind": "integer", "value": "1"}],
        ],
    }
    assert schema.kind == "table_column_schema"
    assert order.kind == "table_column_order"

    with pytest.raises(ValueError, match="unique"):
        TableRowFact(
            cells=(("a", ScalarFact("string", "1")), ("a", ScalarFact("string", "2")))
        )


@pytest.mark.parametrize(
    "change",
    [
        TableChange(
            operation="column_add",
            column="x",
            after_digest="1" * 64,
            after_fact=ColumnSchemaFact("x", "string", 0, None),
        ),
        TableChange(
            operation="column_reorder",
            before_digest="1" * 64,
            after_digest="2" * 64,
            before_fact=ColumnOrderFact(("a", "b")),
            after_fact=ColumnOrderFact(("b", "a")),
        ),
        TableChange(
            operation="cell_replace",
            key_ordinal=1,
            key=(ScalarFact("integer", "7"),),
            column="value",
            before_digest="1" * 64,
            after_digest="2" * 64,
            before_fact=ScalarFact("float64", "0x1.0000000000000p+0"),
            after_fact=ScalarFact("float64", "0x1.0000000000000p+1"),
        ),
    ],
)
def test_table_changes_round_trip(change: TableChange) -> None:
    assert _change_from_data(_change_to_data(change), schema_version=3) == change


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: TableChange(operation="column_add", column="x", before_digest="1" * 64),
        lambda: TableChange(
            operation="column_reorder",
            row=1,
            before_digest="1" * 64,
            after_digest="2" * 64,
        ),
        lambda: TableChange(
            operation="cell_replace",
            row=1,
            key_ordinal=1,
            column="x",
            before_digest="1" * 64,
            after_digest="2" * 64,
        ),
    ],
)
def test_table_changes_reject_illegal_operation_fields(constructor: object) -> None:
    with pytest.raises(ValueError):
        constructor()  # type: ignore[operator]


def test_array_change_round_trip_uses_tagged_numeric_values_and_nulls() -> None:
    change = ArrayChange(
        operation="element_replace",
        index=(0, 2),
        before_digest="1" * 64,
        after_digest="2" * 64,
        absolute_error=FiniteValue(2.0),
        relative_error=PositiveInfinityValue(),
    )

    data = _change_to_data(change)
    assert list(data) == [
        "kind",
        "operation",
        "index",
        "before_digest",
        "after_digest",
        "absolute_error",
        "relative_error",
    ]
    assert data["absolute_error"] == {"kind": "finite", "value": 2.0}
    assert data["relative_error"] == {"kind": "positive_infinity"}
    assert _change_from_data(data, schema_version=3) == change

    shape = ArrayChange(
        operation="shape_replace",
        index=None,
        before_digest="1" * 64,
        after_digest="2" * 64,
    )
    assert _change_to_data(shape)["absolute_error"] is None
    assert _change_to_data(shape)["relative_error"] is None


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: ArrayChange(
            operation="shape_replace",
            index=(0,),
            before_digest="1" * 64,
            after_digest="2" * 64,
        ),
        lambda: ArrayChange(
            operation="element_replace",
            index=(-1,),
            before_digest="1" * 64,
            after_digest="2" * 64,
        ),
        lambda: ArrayChange(
            operation="element_replace",
            index=(0,),
            before_digest="1" * 64,
            after_digest="2" * 64,
            absolute_error=PositiveInfinityValue(),
        ),
        lambda: ArrayChange(
            operation="element_replace",
            index=(0,),
            before_digest="1" * 64,
            after_digest="2" * 64,
            relative_error=FiniteValue(-1.0),
        ),
    ],
)
def test_array_changes_reject_invalid_matrix_and_errors(constructor: object) -> None:
    with pytest.raises(ValueError):
        constructor()  # type: ignore[operator]


def test_array_change_reader_requires_exact_keys_and_rejects_duplicate_json_keys() -> (
    None
):
    data: JsonObject = {
        "kind": "array_change",
        "operation": "shape_replace",
        "index": None,
        "before_digest": "1" * 64,
        "after_digest": "2" * 64,
        "absolute_error": None,
        "relative_error": None,
    }
    assert isinstance(_change_from_data(data, schema_version=3), ArrayChange)

    missing = dict(data)
    del missing["index"]
    with pytest.raises(SerializationError, match="missing required field: index"):
        _change_from_data(missing, schema_version=3)

    extra: JsonObject = {**data, "before_shape": [1]}
    with pytest.raises(SerializationError, match="unexpected field"):
        _change_from_data(extra, schema_version=3)

    duplicate = (
        '{"schema_version":3,"schema_version":3,"kind":"failed",'
        '"execution":{},"problem":{}}'
    )
    with pytest.raises(SerializationError, match="duplicate JSON object key"):
        loads_outcome(duplicate)


def test_new_limit_records_reject_boolean_and_negative_values() -> None:
    with pytest.raises(ValueError):
        YamlResourceLimits(max_aliases=True)
    with pytest.raises(ValueError):
        TableResourceLimits(max_rows=-1)
    with pytest.raises(ValueError):
        ArrayResourceLimits(max_rank=-1)


def test_contract_module_has_no_optional_runtime_dependency() -> None:
    payload = json.dumps(spec_to_data(YamlCompareSpec()))
    assert '"kind": "yaml"' in payload
