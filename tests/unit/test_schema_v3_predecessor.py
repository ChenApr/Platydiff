from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
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
    TextCompareSpec,
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
    Diagnostic,
    DiagnosticSeverity,
    DiffSummary,
    FiniteValue,
    JsonObject,
    Metric,
    MetricDirection,
    PolicyEvaluation,
    PositiveInfinityValue,
    Relation,
    ResourceUsage,
    StructuredChange,
    StructuredDetailMode,
    StructuredType,
    SubtreeFact,
    SummaryCount,
    TransformationRecord,
    Verdict,
)
from platydiff.core.serialization import (
    SerializationError,
    _change_from_data,
    _change_to_data,
    _table_column_policy_digest,
    _validate_table_fact_against_spec,
    _validate_table_keyed_coordinates,
    downgrade_outcome_v3_to_v2,
    dumps_outcome,
    loads_outcome,
    outcome_from_data,
    outcome_to_data,
    serialized_change_size,
    spec_from_data,
    spec_to_data,
    upgrade_outcome_v1_to_v3,
)
from platydiff.plugins import PluginCatalogV1, PluginHost


def _contract_outcome(
    spec: YamlCompareSpec | TableCompareSpec | ArrayCompareSpec,
) -> CompletedOutcomeV3:
    yaml_difference = isinstance(spec, YamlCompareSpec)
    base = compare(
        TextSource("0"),
        TextSource("1" if yaml_difference else "0"),
        JsonCompareSpec(),
    )
    assert isinstance(base, CompletedOutcomeV3)
    transformations: tuple[TransformationRecord, ...]
    if isinstance(spec, YamlCompareSpec):
        prefix = "yaml"
        algorithm = "yaml.structural.tree.v1"
        count_values = {
            "compared_values": 1,
            "equal_values": 0,
            "changed_values": 1,
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
            TransformationRecord(
                "aligning",
                "yaml.pointer.position",
                {"pointer": "rfc6901", "sequences": "positional"},
            ),
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
                "change_items": (spec.limits.max_change_items, 1),
                "change_payload_bytes": (
                    spec.limits.max_change_payload_bytes,
                    sum(
                        serialized_change_size(item)
                        for item in base.result.changes.items
                    ),
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
            TransformationRecord(
                "decoding",
                f"table.{spec.dialect}.decode",
                {
                    "dialect": spec.dialect,
                    "encoding": spec.encoding.value,
                    "header": spec.header,
                },
            ),
            TransformationRecord(
                "normalizing",
                "table.presentation.elide",
                {"quoting": "double", "record_terminators": "elided"},
            ),
        ]
        if spec.columns:
            transformations_list.append(
                TransformationRecord(
                    "normalizing",
                    "table.cells.typed",
                    {"column_policy_digest": _table_column_policy_digest(spec)},
                )
            )
        transformations_list.extend(
            (
                TransformationRecord(
                    "aligning",
                    f"table.columns.{spec.column_order}",
                    {"mode": spec.column_order},
                ),
                TransformationRecord(
                    "aligning",
                    f"table.rows.{spec.alignment}",
                    {"key_columns": list(spec.key_columns), "mode": spec.alignment},
                ),
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
        transformations = (
            TransformationRecord(
                "aligning",
                "array.elements.position",
                {"order": "c_row_major"},
            ),
        )
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
        implementation_version="1",
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
        relation=Relation.DIFFERENT if yaml_difference else Relation.EQUAL,
        verdict=Verdict.FAIL if yaml_difference else Verdict.PASS,
        summary=DiffSummary(
            1 if yaml_difference else 0,
            tuple(
                SummaryCount(name, value, summary_unit)
                for name, value in count_values.items()
            ),
        ),
        changes=ChangeSet(
            ChangeCompleteness.COMPLETE,
            base.result.changes.items if yaml_difference else (),
            1 if yaml_difference else 0,
            1 if yaml_difference else 0,
            0,
            ChangeSelection.ALL,
            None,
        ),
        metrics=metrics,
        evaluations=(
            PolicyEvaluation(
                rule_id,
                Verdict.FAIL if yaml_difference else Verdict.PASS,
                metric_name,
                "eq",
                FiniteValue(0),
                FiniteValue(1 if yaml_difference else 0),
            ),
        ),
        provenance=provenance,
    )
    execution = replace(
        base.execution,
        started_at="2026-09-10T00:00:00Z",
        finished_at="2026-09-10T00:00:00Z",
        duration_ns=0,
        stages=tuple(
            replace(
                stage,
                started_at="2026-09-10T00:00:00Z",
                finished_at="2026-09-10T00:00:00Z",
                duration_ns=0,
            )
            for stage in base.execution.stages
        ),
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
    ("spec", "fixture_name", "size", "sha256"),
    [
        (
            YamlCompareSpec(),
            "yaml_completed.json",
            5249,
            "fac9ac799dd9f28291b060da07541df60f09cec7cc315bcb6c3ecf3449223820",
        ),
        (
            TableCompareSpec(dialect="csv"),
            "table_completed.json",
            5730,
            "c0742af855211f1a8f94b98de9a209e010bfc3be85481fef1b0525a146fe65b5",
        ),
        (
            ArrayCompareSpec(),
            "array_completed.json",
            4717,
            "72940c50a759eb6968aac3cf5c169b5817507b3c9b2524b9be2c428da561dd25",
        ),
    ],
)
def test_contract_only_completed_fixtures_round_trip_canonically(
    spec: YamlCompareSpec | TableCompareSpec | ArrayCompareSpec,
    fixture_name: str,
    size: int,
    sha256: str,
) -> None:
    outcome = _contract_outcome(spec)
    encoded = dumps_outcome(outcome)
    fixture = (
        Path(__file__).parents[1] / "fixtures" / "schema_v3" / fixture_name
    ).read_bytes()

    assert fixture == encoded.encode("utf-8") + b"\n"
    assert len(encoded.encode("utf-8")) == size
    assert hashlib.sha256(encoded.encode("utf-8")).hexdigest() == sha256
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


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: TableChange(
            operation="cell_replace",
            row=1,
            column="value",
            before_digest="1" * 64,
            after_digest="2" * 64,
            before_fact=ScalarFact("integer", "1", lexical="1"),
            after_fact=ScalarFact("string", "value"),
        ),
        lambda: TableChange(
            operation="cell_replace",
            row=1,
            column="value",
            before_digest="1" * 64,
            after_digest="2" * 64,
            before_fact=ScalarFact("float64", "banana"),
            after_fact=ScalarFact("float64", "0x1.0000000000000p+0"),
        ),
        lambda: TableChange(
            operation="row_add",
            key_ordinal=1,
            key=(ScalarFact("integer", "1", lexical="1"),),
            after_digest="1" * 64,
            after_fact=TableRowFact((("value", ScalarFact("float64", "0x1p+0")),)),
        ),
    ],
)
def test_detached_table_changes_reject_json_lexical_and_noncanonical_float_facts(
    constructor: object,
) -> None:
    with pytest.raises(ValueError, match="table scalar"):
        constructor()  # type: ignore[operator]


def test_table_change_reader_applies_detached_scalar_fact_grammar() -> None:
    change = TableChange(
        operation="cell_replace",
        row=1,
        column="value",
        before_digest="1" * 64,
        after_digest="2" * 64,
        before_fact=ScalarFact("string", "before"),
        after_fact=ScalarFact("string", "after"),
    )
    data = _change_to_data(change)
    data["before_fact"] = {"kind": "integer", "value": "1", "lexical": "1"}
    with pytest.raises(SerializationError, match="table scalar"):
        _change_from_data(data, schema_version=3)

    data = _change_to_data(change)
    data["after_fact"] = {"kind": "float64", "value": "0x1p+0"}
    with pytest.raises(SerializationError, match="table scalar"):
        _change_from_data(data, schema_version=3)


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
        lambda: ArrayChange(
            operation="element_replace",
            index=(0,),
            before_digest="1" * 64,
            after_digest="2" * 64,
            absolute_error=FiniteValue(1.0),
        ),
        lambda: ArrayChange(
            operation="element_replace",
            index=(0,),
            before_digest="1" * 64,
            after_digest="2" * 64,
            relative_error=FiniteValue(1.0),
        ),
        lambda: ArrayChange(
            operation="element_replace",
            index=(0,),
            before_digest="1" * 64,
            after_digest="2" * 64,
            absolute_error=FiniteValue(0.0),
            relative_error=PositiveInfinityValue(),
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

    element = _change_to_data(
        ArrayChange(
            "element_replace",
            (0,),
            "1" * 64,
            "2" * 64,
            FiniteValue(1),
            FiniteValue(1),
        )
    )
    element["relative_error"] = None
    with pytest.raises(SerializationError, match="both be present"):
        _change_from_data(element, schema_version=3)

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


@pytest.mark.parametrize(
    "spec",
    [YamlCompareSpec(), TableCompareSpec(dialect="csv"), ArrayCompareSpec()],
)
def test_new_spec_readers_reject_extra_fields_recursively(
    spec: YamlCompareSpec | TableCompareSpec | ArrayCompareSpec,
) -> None:
    data = spec_to_data(spec)
    data["future"] = True
    with pytest.raises(SerializationError, match="unexpected field"):
        spec_from_data(data)

    data = spec_to_data(spec)
    cast(JsonObject, data["limits"])["future"] = 1
    with pytest.raises(SerializationError, match="unexpected field"):
        spec_from_data(data)


def test_new_nested_readers_reject_extra_fields() -> None:
    table = spec_to_data(
        TableCompareSpec(
            dialect="csv",
            columns=(ColumnSpec("value", "float64", numeric=NumericPolicy()),),
        )
    )
    column = cast(JsonObject, cast(list[object], table["columns"])[0])
    column["future"] = True
    with pytest.raises(SerializationError, match="unexpected field"):
        spec_from_data(table)

    numeric = spec_to_data(ArrayCompareSpec())
    cast(JsonObject, numeric["numeric"])["future"] = True
    with pytest.raises(SerializationError, match="unexpected field"):
        spec_from_data(numeric)

    tagged: JsonObject = {"kind": "finite", "value": 1, "future": True}
    change = _change_to_data(
        ArrayChange(
            "element_replace",
            (0,),
            "1" * 64,
            "2" * 64,
            FiniteValue(1),
            FiniteValue(1),
        )
    )
    change["absolute_error"] = tagged
    with pytest.raises(SerializationError, match="unexpected field"):
        _change_from_data(change, schema_version=3)

    fact_change = _change_to_data(
        TableChange(
            operation="cell_replace",
            row=1,
            column="x",
            before_digest="1" * 64,
            after_digest="2" * 64,
            before_fact=ScalarFact("string", "a"),
            after_fact=ScalarFact("string", "b"),
        )
    )
    cast(JsonObject, fact_change["before_fact"])["future"] = True
    with pytest.raises(SerializationError, match="unexpected field"):
        _change_from_data(fact_change, schema_version=3)


def _outcome_with_changes(
    outcome: CompletedOutcomeV3,
    changes: tuple[StructuredChange | TableChange | ArrayChange, ...],
) -> CompletedOutcomeV3:
    total = len(changes)
    return replace(
        outcome,
        result=replace(
            outcome.result,
            summary=replace(outcome.result.summary, change_count=total),
            changes=ChangeSet(
                ChangeCompleteness.COMPLETE,
                changes,
                total,
                total,
                0,
                ChangeSelection.ALL,
                None,
            ),
        ),
    )


def test_table_values_validate_declared_dtype_and_aligned_row_order() -> None:
    spec = TableCompareSpec(
        dialect="csv",
        columns=(ColumnSpec("id", "integer"), ColumnSpec("name", "string")),
    )
    outcome = _contract_outcome(spec)
    wrong_dtype = TableChange(
        operation="cell_replace",
        row=1,
        column="id",
        before_digest="1" * 64,
        after_digest="2" * 64,
        before_fact=ScalarFact("boolean", True),
        after_fact=ScalarFact("integer", "1"),
    )
    with pytest.raises(SerializationError, match="declared column"):
        outcome_to_data(_outcome_with_changes(outcome, (wrong_dtype,)))

    wrong_order = TableChange(
        operation="row_add",
        row=1,
        after_digest="2" * 64,
        after_fact=TableRowFact(
            (("name", ScalarFact("string", "n")), ("id", ScalarFact("integer", "1")))
        ),
    )
    with pytest.raises(SerializationError, match="columns do not match"):
        outcome_to_data(_outcome_with_changes(outcome, (wrong_order,)))


def test_array_result_rejects_mixed_or_reversed_schema_changes() -> None:
    outcome = _contract_outcome(ArrayCompareSpec())
    shape = ArrayChange("shape_replace", None, "1" * 64, "2" * 64)
    dtype = ArrayChange("dtype_replace", None, "3" * 64, "4" * 64)
    element = ArrayChange("element_replace", (0,), "5" * 64, "6" * 64)

    with pytest.raises(SerializationError, match="suppress element"):
        outcome_to_data(_outcome_with_changes(outcome, (shape, element)))
    with pytest.raises(SerializationError, match="schema changes are not canonical"):
        outcome_to_data(_outcome_with_changes(outcome, (dtype, shape)))


def test_yaml_result_binds_scalar_fact_digest_and_transformation_parameters() -> None:
    outcome = _contract_outcome(YamlCompareSpec())
    data = outcome_to_data(outcome)
    result = cast(JsonObject, data["result"])
    changes = cast(JsonObject, result["changes"])
    item = cast(JsonObject, cast(list[object], changes["items"])[0])
    item["after_digest"] = "f" * 64
    with pytest.raises(SerializationError, match="does not match"):
        outcome_from_data(data)

    data = outcome_to_data(outcome)
    result = cast(JsonObject, data["result"])
    provenance = cast(JsonObject, result["provenance"])
    transformations = cast(list[object], provenance["transformations"])
    cast(JsonObject, transformations[0])["parameters"] = {"future": True}
    with pytest.raises(SerializationError, match="transformations are not canonical"):
        outcome_from_data(data)


def test_array_schema_replacement_requires_zero_element_counts() -> None:
    outcome = _contract_outcome(ArrayCompareSpec())
    shape = ArrayChange("shape_replace", None, "1" * 64, "2" * 64)
    changed = _outcome_with_changes(outcome, (shape,))
    metrics = tuple(
        replace(metric, value=FiniteValue(1))
        if metric.name in ("array.changed_items", "array.changed_elements")
        else replace(metric, value=FiniteValue(0))
        if metric.name == "array.equal_elements"
        else metric
        for metric in changed.result.metrics
    )
    counts = tuple(
        replace(count, value=1)
        if count.name in ("changed_items", "changed_elements")
        else replace(count, value=0)
        if count.name == "equal_elements"
        else count
        for count in changed.result.summary.counts
    )
    invalid = replace(
        changed,
        result=replace(
            changed.result,
            relation=Relation.DIFFERENT,
            verdict=Verdict.FAIL,
            metrics=metrics,
            summary=replace(changed.result.summary, counts=counts),
            evaluations=(
                replace(
                    changed.result.evaluations[0],
                    verdict=Verdict.FAIL,
                    observed=FiniteValue(1),
                ),
            ),
        ),
    )
    with pytest.raises(SerializationError, match="schema-replacement counts"):
        outcome_to_data(invalid)


def test_array_element_counts_are_covered_by_resources_and_compare_work() -> None:
    outcome = _contract_outcome(ArrayCompareSpec())

    with pytest.raises(SerializationError, match="element resources"):
        outcome_to_data(_with_resource_usage(outcome, before_elements=0))
    with pytest.raises(SerializationError, match="compare-work resource"):
        outcome_to_data(_with_resource_usage(outcome, compare_work=1))


def test_new_contract_wire_order_and_literal_change_bytes_are_frozen() -> None:
    table_encoded = dumps_outcome(_contract_outcome(TableCompareSpec(dialect="csv")))
    assert (
        '"spec":{"kind":"table","dialect":"csv","encoding":"utf-8","header"'
        in table_encoded
    )
    assert table_encoded.index('"table.compared_cells"') < table_encoded.index(
        '"table.equal_cells"'
    )

    row_change = TableChange(
        operation="row_add",
        row=1,
        after_digest="a" * 64,
        after_fact=TableRowFact((("x", ScalarFact("string", "v")),)),
    )
    assert json.dumps(
        _change_to_data(row_change), ensure_ascii=False, separators=(",", ":")
    ) == (
        '{"kind":"table_change","operation":"row_add","row":1,'
        '"key_ordinal":null,"key":null,"column":null,"before_digest":null,'
        '"after_digest":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
        '"before_fact":null,"after_fact":{"kind":"table_row","cells":'
        '[["x",{"kind":"string","value":"v"}]]}}'
    )
    array_change = ArrayChange("shape_replace", None, "1" * 64, "2" * 64)
    assert json.dumps(
        _change_to_data(array_change), ensure_ascii=False, separators=(",", ":")
    ) == (
        '{"kind":"array_change","operation":"shape_replace","index":null,'
        '"before_digest":"1111111111111111111111111111111111111111111111111111111111111111",'
        '"after_digest":"2222222222222222222222222222222222222222222222222222222222222222",'
        '"absolute_error":null,"relative_error":null}'
    )


@pytest.mark.parametrize(
    "spec",
    [YamlCompareSpec(), TableCompareSpec(dialect="csv"), ArrayCompareSpec()],
)
def test_contract_results_reject_unknown_transformation_parameters(
    spec: YamlCompareSpec | TableCompareSpec | ArrayCompareSpec,
) -> None:
    outcome = _contract_outcome(spec)
    first = outcome.result.provenance.transformations[0]
    invalid = replace(
        outcome,
        result=replace(
            outcome.result,
            provenance=replace(
                cast(ComparisonProvenanceV2, outcome.result.provenance),
                transformations=(
                    replace(first, parameters={**first.parameters, "future": True}),
                    *outcome.result.provenance.transformations[1:],
                ),
            ),
        ),
    )
    with pytest.raises(SerializationError, match="transformations are not canonical"):
        outcome_to_data(invalid)


def test_error_metrics_follow_finite_pair_applicability_and_value_rules() -> None:
    table = _contract_outcome(TableCompareSpec(dialect="csv"))
    unexpected = replace(
        table,
        result=replace(
            table.result,
            metrics=(
                *table.result.metrics,
                Metric(
                    "table.maximum_absolute_error",
                    FiniteValue(0),
                    "numeric_values",
                    MetricDirection.LOWER_IS_BETTER,
                    "maximum",
                ),
            ),
        ),
    )
    with pytest.raises(SerializationError, match="applicability"):
        outcome_to_data(unexpected)

    array = _contract_outcome(ArrayCompareSpec())
    metrics = (
        *(
            replace(metric, value=FiniteValue(1))
            if metric.name == "array.finite_numeric_pairs"
            else metric
            for metric in array.result.metrics
        ),
        Metric(
            "array.maximum_absolute_error",
            PositiveInfinityValue(),
            "numeric_values",
            MetricDirection.LOWER_IS_BETTER,
            "maximum",
        ),
        Metric(
            "array.maximum_relative_error",
            PositiveInfinityValue(),
            "ratio",
            MetricDirection.LOWER_IS_BETTER,
            "maximum",
        ),
    )
    summary = tuple(
        replace(count, value=1) if count.name == "finite_numeric_pairs" else count
        for count in array.result.summary.counts
    )
    invalid_value = replace(
        array,
        result=replace(
            array.result,
            metrics=metrics,
            summary=replace(array.result.summary, counts=summary),
        ),
    )
    with pytest.raises(SerializationError, match="error metric value"):
        outcome_to_data(invalid_value)


def test_table_truncation_evidence_uses_declared_limit_and_reason() -> None:
    outcome = _contract_outcome(TableCompareSpec(dialect="csv"))
    metrics = tuple(
        replace(metric, value=FiniteValue(1))
        if metric.name == "table.changed_items"
        else metric
        for metric in outcome.result.metrics
    )
    counts = tuple(
        replace(count, value=1) if count.name == "changed_items" else count
        for count in outcome.result.summary.counts
    )
    invalid = replace(
        outcome,
        result=replace(
            outcome.result,
            relation=Relation.DIFFERENT,
            verdict=Verdict.FAIL,
            summary=DiffSummary(1, counts),
            changes=ChangeSet(
                ChangeCompleteness.TRUNCATED,
                (),
                1,
                0,
                1,
                ChangeSelection.SOURCE_ORDER_PREFIX,
                999,
                None,
            ),
            metrics=metrics,
            evaluations=(
                replace(
                    outcome.result.evaluations[0],
                    verdict=Verdict.FAIL,
                    observed=FiniteValue(1),
                ),
            ),
        ),
    )
    with pytest.raises(SerializationError, match="truncation evidence"):
        outcome_to_data(invalid)


def test_downgrade_validates_before_rejecting_phase4_change_under_legacy_spec() -> None:
    legacy_v1 = compare(TextSource("same"), TextSource("same"), TextCompareSpec())
    legacy = upgrade_outcome_v1_to_v3(legacy_v1)
    assert isinstance(legacy, CompletedOutcomeV3)
    phase4_change = TableChange(
        operation="column_add",
        column="x",
        after_digest="a" * 64,
        after_fact=ColumnSchemaFact("x", "string", 0, None),
    )
    malformed = _outcome_with_changes(legacy, (phase4_change,))
    with pytest.raises(SerializationError, match="legacy schema-v3 result"):
        downgrade_outcome_v3_to_v2(malformed)


def test_contract_encoder_sorts_arbitrary_nested_details_lexicographically() -> None:
    outcome = _contract_outcome(ArrayCompareSpec())

    def with_details(details: JsonObject) -> CompletedOutcomeV3:
        return replace(
            outcome,
            execution=replace(
                outcome.execution,
                diagnostics=(
                    Diagnostic(
                        "contract_note",
                        DiagnosticSeverity.WARNING,
                        None,
                        "note",
                        details,
                    ),
                ),
            ),
        )

    first = dumps_outcome(with_details({"kind": "string", "z": 1, "a": 2}))
    second = dumps_outcome(with_details({"a": 2, "z": 1, "kind": "string"}))

    assert first == second
    assert '"details":{"a":2,"kind":"string","z":1}' in first


def test_table_fact_context_handles_untyped_and_by_name_columns() -> None:
    with pytest.raises(SerializationError, match="untyped table cells"):
        _validate_table_fact_against_spec(
            ScalarFact("integer", "1"), TableCompareSpec(dialect="csv")
        )

    by_name = TableCompareSpec(
        dialect="csv",
        column_order="by_name",
        columns=(ColumnSpec("b", "string"), ColumnSpec("a", "integer")),
    )
    fact = TableRowFact(
        (("a", ScalarFact("integer", "1")), ("b", ScalarFact("string", "v")))
    )
    _validate_table_fact_against_spec(fact, by_name)


def test_untyped_keyed_table_requires_string_key_facts_on_write_and_read() -> None:
    spec = TableCompareSpec(
        dialect="csv",
        alignment="key",
        key_columns=("id",),
    )
    outcome = _contract_outcome(spec)
    valid = TableChange(
        operation="row_add",
        key_ordinal=1,
        key=(ScalarFact("string", "key-1"),),
        after_digest="1" * 64,
        after_fact=TableRowFact((("id", ScalarFact("string", "key-1")),)),
    )
    changes = ChangeSet(
        ChangeCompleteness.COMPLETE,
        (valid,),
        1,
        1,
        0,
        ChangeSelection.ALL,
        None,
    )
    completed = _with_resource_usage(
        _table_outcome_with_counts(
            outcome,
            changes,
            changed_cells=0,
            changed_items=1,
        ),
        change_items=1,
        change_payload_bytes=serialized_change_size(valid),
    )
    data = outcome_to_data(completed)

    invalid = replace(valid, key=(ScalarFact("integer", "1"),))
    invalid_changes = replace(changes, items=(invalid,))
    with pytest.raises(SerializationError, match="untyped table key"):
        outcome_to_data(
            _table_outcome_with_counts(
                completed,
                invalid_changes,
                changed_cells=0,
                changed_items=1,
            )
        )

    result = cast(JsonObject, data["result"])
    change_set = cast(JsonObject, result["changes"])
    item = cast(JsonObject, cast(list[object], change_set["items"])[0])
    key = cast(list[object], item["key"])
    key[0] = {"kind": "integer", "value": "1"}
    with pytest.raises(SerializationError, match="untyped table key"):
        outcome_from_data(data)


def test_untyped_column_reorder_facts_require_one_column_set() -> None:
    outcome = _contract_outcome(TableCompareSpec(dialect="csv"))
    reorder = TableChange(
        operation="column_reorder",
        before_digest="1" * 64,
        after_digest="2" * 64,
        before_fact=ColumnOrderFact(("a", "b")),
        after_fact=ColumnOrderFact(("a", "c")),
    )
    with pytest.raises(SerializationError, match="column reorder facts disagree"):
        outcome_to_data(_outcome_with_changes(outcome, (reorder,)))

    valid = replace(reorder, after_fact=ColumnOrderFact(("b", "a")))
    valid_changes = ChangeSet(
        ChangeCompleteness.COMPLETE,
        (valid,),
        1,
        1,
        0,
        ChangeSelection.ALL,
        None,
    )
    valid_outcome = _with_resource_usage(
        _table_outcome_with_counts(
            outcome,
            valid_changes,
            changed_cells=0,
            changed_items=1,
        ),
        before_columns=2,
        after_columns=2,
        change_items=1,
        change_payload_bytes=serialized_change_size(valid),
    )
    outcome_to_data(valid_outcome)

    typed = _contract_outcome(
        TableCompareSpec(
            dialect="csv",
            columns=(ColumnSpec("a", "string"), ColumnSpec("b", "string")),
        )
    )
    wrong_aligned = replace(
        reorder,
        before_fact=ColumnOrderFact(("a", "c")),
        after_fact=ColumnOrderFact(("c", "a")),
    )
    with pytest.raises(SerializationError, match="disagree with aligned columns"):
        outcome_to_data(_outcome_with_changes(typed, (wrong_aligned,)))


def test_yaml_reader_does_not_guess_unavailable_parent_type_for_path_order() -> None:
    outcome = _contract_outcome(YamlCompareSpec())
    original = cast(StructuredChange, outcome.result.changes.items[0])
    paths = (
        ("/2", "/10"),  # legal sequence preorder
        ("/10", "/2"),  # legal mapping-key Unicode order
        ("/~1", "/~0"),  # decoded mapping keys `/` then `~`
    )
    for first, second in paths:
        changes = (replace(original, path=first), replace(original, path=second))
        invalid_only_after_path_validation = _with_resource_usage(
            _outcome_with_changes(outcome, changes),
            before_depth=1,
            after_depth=1,
        )
        with pytest.raises(SerializationError, match="count identities"):
            outcome_to_data(invalid_only_after_path_validation)


def test_table_result_orders_removed_rows_before_added_rows() -> None:
    spec = TableCompareSpec(
        dialect="csv",
        alignment="key",
        key_columns=("id",),
        columns=(ColumnSpec("id", "integer"),),
        detail_mode=StructuredDetailMode.DIGEST_ONLY,
    )
    outcome = _contract_outcome(spec)
    row_add = TableChange(operation="row_add", key_ordinal=1, after_digest="1" * 64)
    row_remove = TableChange(
        operation="row_remove", key_ordinal=2, before_digest="2" * 64
    )
    with pytest.raises(SerializationError, match="not in canonical order"):
        outcome_to_data(_outcome_with_changes(outcome, (row_add, row_remove)))


def test_table_key_and_float_facts_enforce_nonlexical_canonical_grammar() -> None:
    keyed_spec = TableCompareSpec(
        dialect="csv",
        alignment="key",
        key_columns=("id",),
        columns=(ColumnSpec("id", "integer"),),
    )
    _contract_outcome(keyed_spec)
    with pytest.raises(ValueError, match="must not carry JSON lexical"):
        TableChange(
            operation="row_add",
            key_ordinal=1,
            key=(ScalarFact("integer", "1", lexical="1"),),
            after_digest="1" * 64,
            after_fact=TableRowFact((("id", ScalarFact("integer", "1")),)),
        )

    float_spec = TableCompareSpec(
        dialect="csv",
        columns=(ColumnSpec("value", "float64", numeric=NumericPolicy()),),
    )
    with pytest.raises(SerializationError, match="canonical C99 hex"):
        _validate_table_fact_against_spec(ScalarFact("float64", "banana"), float_spec)
    _validate_table_fact_against_spec(
        ScalarFact("float64", "0x1.0000000000000p+0"), float_spec
    )


def _table_outcome_with_counts(
    outcome: CompletedOutcomeV3,
    changes: ChangeSet,
    *,
    changed_cells: int,
    changed_items: int,
) -> CompletedOutcomeV3:
    metrics = tuple(
        replace(metric, value=FiniteValue(changed_cells))
        if metric.name == "table.changed_cells"
        else replace(metric, value=FiniteValue(changed_items))
        if metric.name == "table.changed_items"
        else metric
        for metric in outcome.result.metrics
    )
    counts = tuple(
        replace(count, value=changed_cells)
        if count.name == "changed_cells"
        else replace(count, value=changed_items)
        if count.name == "changed_items"
        else count
        for count in outcome.result.summary.counts
    )
    return replace(
        outcome,
        result=replace(
            outcome.result,
            relation=Relation.DIFFERENT,
            verdict=Verdict.FAIL,
            summary=DiffSummary(changes.total_count, counts),
            changes=changes,
            metrics=metrics,
            evaluations=(
                replace(
                    outcome.result.evaluations[0],
                    verdict=Verdict.FAIL,
                    observed=FiniteValue(changed_items),
                ),
            ),
        ),
    )


def test_table_changed_cells_matches_complete_and_truncated_cell_evidence() -> None:
    spec = TableCompareSpec(dialect="csv")
    outcome = _contract_outcome(spec)
    cell = TableChange(
        operation="cell_replace",
        row=1,
        column="column_1",
        before_digest="1" * 64,
        after_digest="2" * 64,
        before_fact=ScalarFact("string", "before"),
        after_fact=ScalarFact("string", "after"),
    )
    complete = ChangeSet(
        ChangeCompleteness.COMPLETE,
        (cell,),
        1,
        1,
        0,
        ChangeSelection.ALL,
        None,
    )
    with pytest.raises(SerializationError, match="cell-change count"):
        outcome_to_data(
            _table_outcome_with_counts(
                outcome, complete, changed_cells=0, changed_items=1
            )
        )

    truncated = ChangeSet(
        ChangeCompleteness.TRUNCATED,
        (cell,),
        2,
        1,
        1,
        ChangeSelection.SOURCE_ORDER_PREFIX,
        spec.limits.max_change_items,
        "change_items",
    )
    with pytest.raises(SerializationError, match="cell-change count"):
        outcome_to_data(
            _table_outcome_with_counts(
                outcome, truncated, changed_cells=0, changed_items=2
            )
        )

    impossible_metrics = tuple(
        replace(metric, value=FiniteValue(1))
        if metric.name == "table.changed_cells"
        else replace(metric, value=FiniteValue(0))
        if metric.name == "table.equal_cells"
        else metric
        for metric in outcome.result.metrics
    )
    impossible_counts = tuple(
        replace(count, value=1)
        if count.name == "changed_cells"
        else replace(count, value=0)
        if count.name == "equal_cells"
        else count
        for count in outcome.result.summary.counts
    )
    impossible = replace(
        outcome,
        result=replace(
            outcome.result,
            metrics=impossible_metrics,
            summary=replace(outcome.result.summary, counts=impossible_counts),
        ),
    )
    with pytest.raises(SerializationError, match="exceeds changed items"):
        outcome_to_data(impossible)


def test_table_key_ordinal_binds_one_key_and_one_operation_class() -> None:
    first = TableChange(
        operation="cell_replace",
        key_ordinal=1,
        key=(ScalarFact("integer", "1"),),
        column="a",
        before_digest="1" * 64,
        after_digest="2" * 64,
        before_fact=ScalarFact("string", "x"),
        after_fact=ScalarFact("string", "y"),
    )
    same_key_other_column = replace(first, column="b")
    _validate_table_keyed_coordinates((first, same_key_other_column))

    different_key = replace(same_key_other_column, key=(ScalarFact("integer", "2"),))
    with pytest.raises(SerializationError, match="inconsistent key facts"):
        _validate_table_keyed_coordinates((first, different_key))
    same_key_different_ordinal = replace(same_key_other_column, key_ordinal=2)
    with pytest.raises(SerializationError, match="inconsistent key ordinals"):
        _validate_table_keyed_coordinates((first, same_key_different_ordinal))
    keyed_outcome = _contract_outcome(
        TableCompareSpec(
            dialect="csv",
            alignment="key",
            key_columns=("id",),
            columns=(
                ColumnSpec("id", "integer"),
                ColumnSpec("a", "string"),
                ColumnSpec("b", "string"),
            ),
        )
    )
    with pytest.raises(SerializationError, match="inconsistent key facts"):
        outcome_to_data(_outcome_with_changes(keyed_outcome, (first, different_key)))

    row_remove = TableChange(
        operation="row_remove",
        key_ordinal=1,
        key=(ScalarFact("integer", "1"),),
        before_digest="3" * 64,
        before_fact=TableRowFact((("a", ScalarFact("string", "x")),)),
    )
    with pytest.raises(SerializationError, match="conflicting row/cell"):
        _validate_table_keyed_coordinates((row_remove, first))

    row_add = TableChange(
        operation="row_add",
        key_ordinal=1,
        key=(ScalarFact("integer", "1"),),
        after_digest="4" * 64,
        after_fact=TableRowFact((("a", ScalarFact("string", "y")),)),
    )
    with pytest.raises(SerializationError, match="conflicting row/cell"):
        _validate_table_keyed_coordinates((row_remove, row_add))


def test_table_cell_order_uses_aligned_column_ordinals() -> None:
    spec = TableCompareSpec(
        dialect="csv",
        columns=(ColumnSpec("z", "string"), ColumnSpec("a", "string")),
    )
    outcome = _contract_outcome(spec)
    z_change = TableChange(
        operation="cell_replace",
        row=1,
        column="z",
        before_digest="1" * 64,
        after_digest="2" * 64,
        before_fact=ScalarFact("string", "x"),
        after_fact=ScalarFact("string", "y"),
    )
    a_change = replace(z_change, column="a")

    with pytest.raises(SerializationError, match="count identities"):
        outcome_to_data(_outcome_with_changes(outcome, (z_change, a_change)))
    with pytest.raises(SerializationError, match="not in canonical order"):
        outcome_to_data(_outcome_with_changes(outcome, (a_change, z_change)))


def _with_resource_usage(
    outcome: CompletedOutcomeV3, **used: int
) -> CompletedOutcomeV3:
    provenance = cast(ComparisonProvenanceV2, outcome.result.provenance)
    return replace(
        outcome,
        result=replace(
            outcome.result,
            provenance=replace(
                provenance,
                resources=tuple(
                    replace(resource, used=used.get(resource.name, resource.used))
                    for resource in provenance.resources
                ),
            ),
        ),
    )


def test_yaml_change_depth_matches_spec_and_present_side_resources() -> None:
    shallow_spec = YamlCompareSpec(limits=replace(YamlResourceLimits(), max_depth=1))
    shallow = _contract_outcome(shallow_spec)
    original = cast(StructuredChange, shallow.result.changes.items[0])
    too_deep = _outcome_with_changes(shallow, (replace(original, path="/a/b"),))
    with pytest.raises(SerializationError, match="exceeds its depth limit"):
        outcome_to_data(too_deep)

    roomy = _contract_outcome(
        YamlCompareSpec(limits=replace(YamlResourceLimits(), max_depth=4))
    )
    original = cast(StructuredChange, roomy.result.changes.items[0])
    nested = _outcome_with_changes(roomy, (replace(original, path="/a"),))
    with pytest.raises(SerializationError, match="depth resource"):
        outcome_to_data(nested)

    covered = _with_resource_usage(
        nested,
        before_depth=1,
        after_depth=1,
        change_payload_bytes=serialized_change_size(nested.result.changes.items[0]),
    )
    outcome_to_data(covered)

    added = StructuredChange(
        operation="add",
        path="/a",
        after_type=original.after_type,
        after_digest=original.after_digest,
        after_fact=original.after_fact,
    )
    add_outcome = _with_resource_usage(
        _outcome_with_changes(roomy, (added,)),
        before_depth=0,
        after_depth=1,
        change_payload_bytes=serialized_change_size(added),
    )
    outcome_to_data(add_outcome)

    subtree = StructuredChange(
        operation="add",
        path="",
        after_type=StructuredType.MAPPING,
        after_digest="a" * 64,
        after_fact=SubtreeFact("mapping", 5, 3),
    )
    subtree_outcome = _outcome_with_changes(roomy, (subtree,))
    with pytest.raises(SerializationError, match="subtree evidence"):
        outcome_to_data(subtree_outcome)
    outcome_to_data(
        _with_resource_usage(
            subtree_outcome,
            after_nodes=6,
            after_expanded_nodes=6,
            change_payload_bytes=serialized_change_size(subtree),
        )
    )


def test_table_coordinates_are_covered_by_row_resources() -> None:
    limits = replace(TableResourceLimits(), max_rows=1)
    outcome = _contract_outcome(TableCompareSpec(dialect="csv", limits=limits))
    cell = TableChange(
        operation="cell_replace",
        row=2,
        column="column_1",
        before_digest="1" * 64,
        after_digest="2" * 64,
        before_fact=ScalarFact("string", "x"),
        after_fact=ScalarFact("string", "y"),
    )
    with pytest.raises(SerializationError, match="row coordinate exceeds"):
        outcome_to_data(_outcome_with_changes(outcome, (cell,)))

    keyed = _contract_outcome(
        TableCompareSpec(
            dialect="csv",
            alignment="key",
            key_columns=("id",),
            columns=(ColumnSpec("id", "integer"),),
            detail_mode=StructuredDetailMode.DIGEST_ONLY,
            limits=limits,
        )
    )
    outside_union = TableChange(
        operation="row_remove", key_ordinal=3, before_digest="3" * 64
    )
    with pytest.raises(SerializationError, match="row-union resource bound"):
        outcome_to_data(_outcome_with_changes(keyed, (outside_union,)))

    ordinary = _contract_outcome(TableCompareSpec(dialect="csv"))
    beyond_used = replace(cell, row=2)
    with pytest.raises(SerializationError, match="row resource"):
        outcome_to_data(_outcome_with_changes(ordinary, (beyond_used,)))

    two_cell_row = TableChange(
        operation="row_add",
        row=1,
        after_digest="4" * 64,
        after_fact=TableRowFact(
            (("a", ScalarFact("string", "x")), ("b", ScalarFact("string", "y")))
        ),
    )
    with pytest.raises(SerializationError, match="cell resource"):
        outcome_to_data(_outcome_with_changes(ordinary, (two_cell_row,)))

    byte_limited = _contract_outcome(
        TableCompareSpec(
            dialect="csv", limits=replace(TableResourceLimits(), max_cell_bytes=1)
        )
    )
    wide_column = replace(cell, row=1, column="xx")
    with pytest.raises(SerializationError, match="column coordinate"):
        outcome_to_data(_outcome_with_changes(byte_limited, (wide_column,)))
