"""Strict, bounded semantic JSON comparison for schema v3."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

from platydiff._version import __version__
from platydiff.comparators.json._digest import evidence_digest
from platydiff.comparators.json._parser import (
    JsonMapping,
    JsonNode,
    JsonNumber,
    JsonScalar,
    JsonSequence,
    ParseStats,
    parse_json,
)
from platydiff.core._sources import SourceSnapshot
from platydiff.core.models import (
    ChangeCompleteness,
    ChangeSelection,
    ChangeSet,
    ComparisonProvenanceV2,
    Diagnostic,
    DiagnosticSeverity,
    DiffResult,
    DiffSummary,
    Fidelity,
    FiniteValue,
    InputProvenance,
    JsonCompareSpec,
    JsonNumberMode,
    Metric,
    MetricDirection,
    PipelineStage,
    PolicyEvaluation,
    Relation,
    ResourceUsage,
    ScalarFact,
    SourceKind,
    StructuredChange,
    StructuredDetailMode,
    StructuredType,
    SubtreeFact,
    SummaryCount,
    TransformationRecord,
    Verdict,
)
from platydiff.core.pipeline import ComparisonCompletion, StageRunner
from platydiff.core.problems import CompareResourceLimitError, DecodeError
from platydiff.core.serialization import serialized_change_size, spec_to_data

ALGORITHM_ID = "json.semantic.tree.v1"


@dataclass(frozen=True, slots=True)
class _Decoded:
    data: bytes
    node: JsonNode
    stats: ParseStats
    source_kind: SourceKind
    label: str | None


@dataclass(frozen=True, slots=True)
class _Scan:
    changes: tuple[StructuredChange, ...]
    change_payload_bytes: int
    change_limit: int | None
    change_limit_reason: Literal["change_items", "change_payload_bytes"] | None
    compared: int
    equal: int
    changed: int
    work: int


class _Scanner:
    def __init__(self, spec: JsonCompareSpec) -> None:
        self.spec = spec
        self.changes: list[StructuredChange] = []
        self.change_payload_bytes = 0
        self.change_limit: int | None = None
        self.change_limit_reason: (
            Literal["change_items", "change_payload_bytes"] | None
        ) = None
        self.compared = 0
        self.equal = 0
        self.changed = 0
        self.work = 0

    def scan(self, before: JsonNode, after: JsonNode) -> _Scan:
        self._visit(before, after, "")
        return _Scan(
            tuple(self.changes),
            self.change_payload_bytes,
            self.change_limit,
            self.change_limit_reason,
            self.compared,
            self.equal,
            self.changed,
            self.work,
        )

    def _charge(self) -> None:
        if self.work >= self.spec.limits.max_compare_work:
            raise CompareResourceLimitError(
                "JSON comparison exceeded the configured work limit.",
                used=self.work + 1,
                limit=self.spec.limits.max_compare_work,
            )
        self.work += 1

    def _visit(
        self, before: JsonNode | None, after: JsonNode | None, path: str
    ) -> None:
        self._charge()
        if before is None:
            if after is None:
                raise RuntimeError("comparison frontier cannot omit both sides")
            self._changed("add", path, None, after)
            return
        if after is None:
            self._changed("remove", path, before, None)
            return
        if _numbers(before, after) and _numbers_equal(
            before, after, self.spec.number_mode
        ):
            self._observed_equal()
            return
        before_type = _node_type(before)
        after_type = _node_type(after)
        if before_type is not after_type:
            self._changed("replace", path, before, after)
            return
        if isinstance(before, JsonScalar) and isinstance(after, JsonScalar):
            if _scalar_equal(before, after, self.spec.number_mode):
                self._observed_equal()
            else:
                self._changed("replace", path, before, after)
            return
        if isinstance(before, JsonSequence) and isinstance(after, JsonSequence):
            if not before.items and not after.items:
                self._observed_equal()
                return
            for index in range(max(len(before.items), len(after.items))):
                self._visit(
                    before.items[index] if index < len(before.items) else None,
                    after.items[index] if index < len(after.items) else None,
                    f"{path}/{index}",
                )
            return
        if not isinstance(before, JsonMapping) or not isinstance(after, JsonMapping):
            raise RuntimeError("private JSON node types are inconsistent")
        if not before.items and not after.items:
            self._observed_equal()
            return
        before_items = dict(before.items)
        after_items = dict(after.items)
        for key in sorted(before_items.keys() | after_items.keys()):
            self._visit(
                before_items.get(key),
                after_items.get(key),
                f"{path}/{_pointer_token(key)}",
            )

    def _observed_equal(self) -> None:
        self.compared += 1
        self.equal += 1

    def _changed(
        self,
        operation: Literal["add", "remove", "replace"],
        path: str,
        before: JsonNode | None,
        after: JsonNode | None,
    ) -> None:
        self.compared += 1
        self.changed += 1
        if self.change_limit_reason is not None:
            return
        if len(self.changes) >= self.spec.limits.max_change_items:
            self.change_limit = self.spec.limits.max_change_items
            self.change_limit_reason = "change_items"
            return
        detail = self.spec.detail_mode is StructuredDetailMode.VALUES
        change = StructuredChange(
            operation=operation,
            path=path,
            before_type=None if before is None else _node_type(before),
            after_type=None if after is None else _node_type(after),
            before_digest=(
                None
                if before is None
                else evidence_digest(before, self.spec.number_mode)
            ),
            after_digest=(
                None if after is None else evidence_digest(after, self.spec.number_mode)
            ),
            before_fact=None
            if before is None or not detail
            else _fact(before, self.spec),
            after_fact=None if after is None or not detail else _fact(after, self.spec),
        )
        size = serialized_change_size(change)
        if self.change_payload_bytes + size > self.spec.limits.max_change_payload_bytes:
            self.change_limit = self.spec.limits.max_change_payload_bytes
            self.change_limit_reason = "change_payload_bytes"
            return
        self.changes.append(change)
        self.change_payload_bytes += size


def _numbers(before: JsonNode, after: JsonNode) -> bool:
    return (
        isinstance(before, JsonScalar)
        and before.kind in ("integer", "decimal")
        and isinstance(after, JsonScalar)
        and after.kind in ("integer", "decimal")
    )


def _numbers_equal(before: JsonNode, after: JsonNode, mode: JsonNumberMode) -> bool:
    if not _numbers(before, after):
        return False
    if not isinstance(before, JsonScalar) or not isinstance(after, JsonScalar):
        raise RuntimeError("numeric node narrowing failed")
    if not isinstance(before.value, JsonNumber) or not isinstance(
        after.value, JsonNumber
    ):
        raise RuntimeError("numeric node lacks number data")
    if mode is JsonNumberMode.LEXICAL:
        return before.value.lexical == after.value.lexical
    return (
        before.value.negative,
        before.value.coefficient,
        before.value.exponent,
    ) == (
        after.value.negative,
        after.value.coefficient,
        after.value.exponent,
    )


def _scalar_equal(before: JsonScalar, after: JsonScalar, mode: JsonNumberMode) -> bool:
    if before.kind in ("integer", "decimal"):
        return _numbers_equal(before, after, mode)
    return before.value == after.value


def _node_type(node: JsonNode) -> StructuredType:
    if isinstance(node, JsonSequence):
        return StructuredType.SEQUENCE
    if isinstance(node, JsonMapping):
        return StructuredType.MAPPING
    return StructuredType(node.kind)


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _fact(node: JsonNode, spec: JsonCompareSpec) -> ScalarFact | SubtreeFact:
    if isinstance(node, (JsonSequence, JsonMapping)):
        descendants, scalars = _subtree_counts(node)
        return SubtreeFact(
            "sequence" if isinstance(node, JsonSequence) else "mapping",
            descendants,
            scalars,
        )
    if node.kind == "null":
        return ScalarFact("null", None)
    if node.kind == "boolean":
        if not isinstance(node.value, bool):
            raise RuntimeError("invalid private JSON boolean")
        return ScalarFact("boolean", node.value)
    if node.kind == "string":
        if not isinstance(node.value, str):
            raise RuntimeError("invalid private JSON string")
        return ScalarFact("string", node.value)
    if not isinstance(node.value, JsonNumber):
        raise RuntimeError("invalid private JSON number")
    return ScalarFact(
        node.kind,
        node.value.canonical,
        node.value.lexical if spec.number_mode is JsonNumberMode.LEXICAL else None,
    )


def _subtree_counts(node: JsonNode) -> tuple[int, int]:
    descendants = 0
    scalars = 0
    pending: list[JsonNode] = []
    if isinstance(node, JsonSequence):
        pending.extend(node.items)
    elif isinstance(node, JsonMapping):
        pending.extend(value for _, value in node.items)
    while pending:
        current = pending.pop()
        descendants += 1
        if isinstance(current, JsonScalar):
            scalars += 1
        elif isinstance(current, JsonSequence):
            pending.extend(current.items)
        else:
            pending.extend(value for _, value in current.items)
    return descendants, scalars


def _decode(snapshot: SourceSnapshot, spec: JsonCompareSpec) -> _Decoded:
    data = b"".join(snapshot.iter_chunks(64 * 1024, stage=PipelineStage.DECODING))
    text = snapshot.owned_text()
    if text is None:
        try:
            text = data.decode(spec.encoding.value, errors="strict")
        except UnicodeDecodeError as error:
            raise DecodeError(
                f"A source is not valid strict {spec.encoding.value} text."
            ) from error
    node, stats = parse_json(text, spec.limits)
    return _Decoded(data, node, stats, snapshot.source_kind, snapshot.label)


def _input(decoded: _Decoded, role: Literal["before", "after"]) -> InputProvenance:
    return InputProvenance(
        role,
        decoded.source_kind,
        len(decoded.data),
        hashlib.sha256(decoded.data).hexdigest(),
        decoded.label,
    )


def _select_changes(
    scan: _Scan, spec: JsonCompareSpec
) -> tuple[ChangeSet, int, tuple[Diagnostic, ...]]:
    if len(scan.changes) == scan.changed:
        if scan.change_limit is not None or scan.change_limit_reason is not None:
            raise RuntimeError("complete structured changes must not carry a limit")
        return (
            ChangeSet(
                ChangeCompleteness.COMPLETE,
                scan.changes,
                scan.changed,
                len(scan.changes),
                0,
                ChangeSelection.ALL,
                None,
            ),
            scan.change_payload_bytes,
            (),
        )
    if scan.change_limit is None or scan.change_limit_reason is None:
        raise RuntimeError("truncated structured changes require a limit")
    changes = ChangeSet(
        ChangeCompleteness.TRUNCATED,
        scan.changes,
        scan.changed,
        len(scan.changes),
        scan.changed - len(scan.changes),
        ChangeSelection.SOURCE_ORDER_PREFIX,
        scan.change_limit,
        scan.change_limit_reason,
    )
    return (
        changes,
        scan.change_payload_bytes,
        (
            Diagnostic(
                "change_details_truncated",
                DiagnosticSeverity.WARNING,
                PipelineStage.AGGREGATING,
                "Complete change details were truncated by configured output limits.",
                {
                    "total_count": scan.changed,
                    "returned_count": len(scan.changes),
                    "max_change_items": spec.limits.max_change_items,
                    "max_change_payload_bytes": spec.limits.max_change_payload_bytes,
                    "limit_reason": scan.change_limit_reason,
                },
            ),
        ),
    )


def _aggregate(
    before: _Decoded,
    after: _Decoded,
    scan: _Scan,
    spec: JsonCompareSpec,
    snapshots: tuple[SourceSnapshot, SourceSnapshot],
) -> ComparisonCompletion:
    snapshots[0].ensure_unchanged(stage=PipelineStage.AGGREGATING)
    snapshots[1].ensure_unchanged(stage=PipelineStage.AGGREGATING)
    changes, payload_bytes, diagnostics = _select_changes(scan, spec)
    relation = Relation.EQUAL if scan.changed == 0 else Relation.DIFFERENT
    verdict = Verdict.PASS if scan.changed == 0 else Verdict.FAIL
    observed = FiniteValue(scan.changed)
    resources: list[ResourceUsage] = []
    for role, decoded in (("before", before), ("after", after)):
        resources.extend(
            (
                ResourceUsage(
                    f"{role}_input_bytes",
                    spec.limits.max_input_bytes,
                    len(decoded.data),
                ),
                ResourceUsage(
                    f"{role}_scalar_bytes",
                    spec.limits.max_scalar_bytes,
                    decoded.stats.maximum_scalar_bytes,
                ),
                ResourceUsage(
                    f"{role}_depth", spec.limits.max_depth, decoded.stats.maximum_depth
                ),
                ResourceUsage(
                    f"{role}_nodes", spec.limits.max_nodes, decoded.stats.nodes
                ),
                ResourceUsage(
                    f"{role}_number_digits",
                    spec.limits.max_number_digits,
                    decoded.stats.maximum_number_digits,
                ),
                ResourceUsage(
                    f"{role}_abs_exponent",
                    spec.limits.max_abs_exponent,
                    decoded.stats.maximum_abs_exponent,
                ),
            )
        )
    resources.extend(
        (
            ResourceUsage("compare_work", spec.limits.max_compare_work, scan.work),
            ResourceUsage(
                "change_items", spec.limits.max_change_items, changes.returned_count
            ),
            ResourceUsage(
                "change_payload_bytes",
                spec.limits.max_change_payload_bytes,
                payload_bytes,
            ),
        )
    )
    transformations: list[TransformationRecord] = []
    if (
        before.source_kind is not SourceKind.TEXT
        or after.source_kind is not SourceKind.TEXT
    ):
        transformations.append(
            TransformationRecord(
                "decoding", "json.decode.utf8", {"encoding": spec.encoding.value}
            )
        )
    transformations.extend(
        (
            TransformationRecord("normalizing", "json.object_order.ignore", {}),
            TransformationRecord(
                "normalizing", f"json.number.{spec.number_mode.value}", {}
            ),
            TransformationRecord(
                "aligning",
                "json.pointer.position",
                {"pointer": "rfc6901", "sequences": "positional"},
            ),
        )
    )
    result = DiffResult(
        relation,
        verdict,
        Fidelity.FULL,
        DiffSummary(
            scan.changed,
            (
                SummaryCount("compared_values", scan.compared, "values"),
                SummaryCount("equal_values", scan.equal, "values"),
                SummaryCount("changed_values", scan.changed, "values"),
            ),
        ),
        changes,
        (
            Metric(
                "json.compared_values",
                FiniteValue(scan.compared),
                "items",
                MetricDirection.NEUTRAL,
                "count",
            ),
            Metric(
                "json.equal_values",
                FiniteValue(scan.equal),
                "items",
                MetricDirection.NEUTRAL,
                "count",
            ),
            Metric(
                "json.changed_values",
                observed,
                "items",
                MetricDirection.LOWER_IS_BETTER,
                "count",
            ),
        ),
        (
            PolicyEvaluation(
                "json.semantic_equality",
                verdict,
                "json.changed_values",
                "eq",
                FiniteValue(0),
                observed,
            ),
        ),
        (),
        ComparisonProvenanceV2(
            inputs=(_input(before, "before"), _input(after, "after")),
            spec=spec_to_data(spec),
            transformations=tuple(transformations),
            comparator_id="json",
            comparator_version=__version__,
            algorithm_id=ALGORITHM_ID,
            implementation_version=__version__,
            resources=tuple(resources),
        ),
    )
    return ComparisonCompletion(result, diagnostics)


def compare_json_snapshots(
    before: SourceSnapshot,
    after: SourceSnapshot,
    spec: JsonCompareSpec,
    stages: StageRunner,
) -> ComparisonCompletion:
    """Execute the explicit schema-v3 JSON lifecycle over stable snapshots."""
    decoded_before, decoded_after = stages.run(
        PipelineStage.DECODING,
        lambda: (_decode(before, spec), _decode(after, spec)),
    )
    normalized = stages.run(
        PipelineStage.NORMALIZING, lambda: (decoded_before, decoded_after)
    )
    aligned = stages.run(PipelineStage.ALIGNING, lambda: normalized)
    scan = stages.run(
        PipelineStage.COMPARING,
        lambda: _Scanner(spec).scan(aligned[0].node, aligned[1].node),
    )
    return stages.run(
        PipelineStage.AGGREGATING,
        lambda: _aggregate(aligned[0], aligned[1], scan, spec, (before, after)),
    )
