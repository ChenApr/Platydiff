# RFC 0006: Structured Data Comparison

[Chinese documentation](0006-structured-data-comparison_zh.md)

- Status: Proposed
- Date: 2026-09-10
- Owners: Platydiff maintainers
- Implementation owner: unassigned pending acceptance and separate authorization

## Summary and authorization boundary

This RFC proposes Phase 4 contracts for JSON, a constrained YAML 1.2 profile,
delimited tables, and dense arrays. It defines schema evolution, equality,
paths, alignment, limits, failures, and delivery gates. It does not authorize
implementation, dependency changes, a new plugin SDK, structured-data automatic
detection, or UI work. Each implementation gate requires a separate dispatch
from updated `main`; later gates do not start automatically.

## Evidence ledger

| Current evidence at `main` `7346d5e` | Phase 4 constraint |
| --- | --- |
| Outcome schema v1 is frozen around text/binary specs and changes. | New public specs and built-in change kinds require a new outcome schema. |
| Schema v2 adds provider facts while retaining the same modality surface. | Schema v3 should be an additive semantic successor to v2. |
| Auto specs, candidates, and detector evidence are closed to text/binary. | Existing auto behavior remains unchanged; Phase 4 is explicit-only. |
| SDK v1.1 comparators and detectors are closed to text/binary. | Phase 4 is built-in-only; new plugin modalities require SDK v2 and a successor RFC. |
| Snapshots already own bounded replay, hashes, mutation checks, and safe labels for path/bytes/text. | JSON, YAML, and tables reuse these source types and host ownership. |
| `ChangeSet` already distinguishes complete, truncated, and partial. | Phase 4 completes comparison before detail truncation and never emits partial. |
| Renderers consume validated outcomes and RFC 0004 keeps UI work separate. | New change shapes need bounded presentation, not renderer-owned semantics or UI authorization. |
| Runtime dependencies are currently empty. | JSON/tables use the standard library; YAML is an optional, lazy, separately reviewed dependency. |

This ledger records implemented constraints, not authorization to modify them.

## Goals and non-goals

Goals are deterministic explicit comparison for JSON/YAML, tables, and dense
arrays; visible normalization and alignment; exact special-value semantics;
bounded work and returned detail; stable schema-v3 changes and provenance; and
tests proving existing text, binary, auto, and plugin behavior remains unchanged.

Phase 4 excludes automatic structured detection; TOML/XML/JSON5; JSON comments;
YAML merge semantics, custom tags, and object constructors; schema languages;
fuzzy or inferred alignment; streaming, sparse, ragged, masked, decimal,
complex, datetime, categorical, or unit-bearing arrays; NumPy, pandas, xarray,
Arrow, Parquet, spreadsheets, compressed containers, URLs, directories, or
stdin; statistical equivalence, ULP policies, patches, artifacts; new plugin
modalities; and HTML, TUI, desktop, or local-web UI implementation.

## Decisions requiring human approval

| ID | Proposed decision | Alternative requiring revision |
| --- | --- | --- |
| S1 | Every Phase 4 outcome uses schema v3; v1/v2 readers and writers remain. | Extend v2 in place, making old v2 readers misinterpret a changed closed union. |
| S2 | Existing auto remains text/binary-only until a successor detection RFC; Phase 4 types are explicit. | First define structured ambiguity, precedence, probing, and attribution. |
| S3 | Phase 4 comparators are built-ins; SDK v1.1 remains text/binary-only. | Accept SDK v2 before Phase 4 implementation. |
| S4 | JSON defaults to semantic value equality: object order and numeric spelling are ignored, array order matters, and duplicate decoded keys fail. | Lexical JSON or order-sensitive objects by default. |
| S5 | YAML uses the constrained `yaml12_core_safe` profile and optional `yaml` extra, with no YAML 1.1 fallback. | Broader YAML semantics or a required core dependency. |
| S6 | Tables require explicit dialect/header policy; cells stay strings without a column schema. | Infer dialect, header, key, missing tokens, or dtypes. |
| S7 | Table alignment is positional by default; keyed alignment is explicit and rejects missing or duplicate keys. | Infer keys or pair duplicates by occurrence. |
| S8 | First-gate arrays are Python-API-only immutable copied sources; ecosystem adapters are later gates. | Add a CLI file format or ecosystem dependency now. |
| S9 | Tolerance is `abs(after-before) <= atol + rtol * abs(before)`; NaN is unequal by default, same-sign infinities and signed zeros are equal. | Symmetric tolerance or different special-value defaults. |
| S10 | Phase 4 never emits partial; pre-completion limits fail and only completed detail can be truncated. | Return a relation from incomplete work. |
| S11 | P4-A1, P4-A2, P4-B1, and P4-B2 are independently authorized. | Deliver Phase 4 as one batch. |
| S12 | Phase 4 emits no artifacts; renderers present only validated bounded facts. | Add patches, previews, downloadable values, or reports now. |

Until accepted decisions are recorded here, this RFC remains `Proposed` and no
implementation gate is authorized.

## Schema-v3 compatibility contract

Schema v3 adds public spec and built-in change variants while retaining RFC
0001 outcomes and RFC 0005 provider fields:

```python
CompareSpecV3 = (
    AutoCompareSpec | TextCompareSpec | BinaryCompareSpec
    | JsonCompareSpec | YamlCompareSpec | TableCompareSpec | ArrayCompareSpec
)
ChangeV3 = (
    TextHunk | BinarySpan | StructuredChange
    | TableChange | ArrayChange | ExtensionChange
)
```

- Existing three-argument text, binary, and auto calls keep schema v1.
- Existing `PluginHost` text/binary calls keep schema v2.
- Every Phase 4 spec produces schema v3, including failure before resolution.
- A v3 reader accepts v1/v2/v3. Old readers continue to reject unknown versions.
- Explicit v1/v2-to-v3 upgraders preserve all facts and add only documented
  neutral defaults. No automatic downgrade exists; an explicit lossless helper
  may downgrade a legacy-only v3 outcome after validation.
- Unknown built-in spec/change kinds remain errors. Unknown namespaced extension
  changes retain RFC 0001 behavior.

Schema-v3 fields and fixtures become public only after a separately authorized
P4-A1 implementation is merged.

### Compatibility matrix

| Producer/path | Schema | Modalities | Plugin participation | Required behavior |
| --- | --- | --- | --- | --- |
| Existing `compare()` and default CLI | v1 | text, binary, auto to either | none | Existing byte-stable fixtures remain valid. |
| Existing explicit `PluginHost` | v2 | text, binary, auto to either | SDK v1.1 | Existing v2 fixtures and receipts remain valid. |
| Proposed Phase 4 built-in path | v3 | explicit json/yaml/table/array | none | v3 validates new variants and all inherited invariants. |
| Proposed `PluginHost` with Phase 4 spec | none | unsupported | rejected before execution | Python returns resolving-stage unavailable; CLI plugin flags plus a Phase 4 type are usage exit 2. |
| Existing auto on structured-looking bytes | v1 | text or binary only | existing rules | Result and detection evidence do not change. |
| Future SDK v2 or structured auto | unspecified | unspecified | unspecified | Requires a successor RFC. |

## Common structured-value contract

JSON and YAML decode into a private immutable tree:

```text
null | boolean | integer | decimal | string | sequence | mapping
```

Parser-specific objects never enter results. Mapping keys must be unique Unicode
scalar strings; other key types fail. Paths are canonical RFC 6901 JSON Pointers:
root is empty, `~` becomes `~0`, `/` becomes `~1`, and array indices are decimal
without leading zeros except `0`.

No Unicode normalization, case folding, string whitespace change, or scalar
coercion occurs. Mapping order is not a comparison dimension; traversal sorts
decoded keys by Unicode code point. Sequences remain positional.

Integers are arbitrary precision within the digit limit. Decimal numbers store
sign, coefficient digits, and base-10 exponent, never binary float. Value mode
removes insignificant zeroes, making `1`, `1.0`, and `1e0` equal and both signed
zeros equal. JSON-only lexical mode compares validated source number tokens and
records that normalization choice.

```python
class StructuredChange:
    kind: Literal["structured_change"]
    operation: Literal["add", "remove", "replace"]
    path: str
    before_type: StructuredType | None
    after_type: StructuredType | None
    before_digest: str | None
    after_digest: str | None
```

Digests are SHA-256 of schema-v3 canonical typed values and reveal no payload.
Add lacks before facts, remove lacks after facts, and replace has both. Type
changes are replacements; moves are not inferred. Changes are observations, not
patches. Deterministic depth-first pre-order uses sorted mapping keys and rising
sequence indices. A wholly added/removed subtree produces one change at its
highest pointer. Full count is known before applying item/payload truncation.
Pointers necessarily expose bounded decoded mapping-key names as comparison
coordinates. They never expose scalar values, and renderers must escape them as
untrusted text.

## JSON contract

```python
class JsonCompareSpec:
    kind: Literal["json"] = "json"
    encoding: Literal["utf-8", "utf-8-sig"] = "utf-8"
    number_mode: Literal["value", "lexical"] = "value"
    limits: StructuredResourceLimits = StructuredResourceLimits()
```

Exactly one RFC 8259 value followed by JSON whitespace is accepted. UTF-8 is
strict; BOM removal needs explicit `utf-8-sig`. Comments, trailing commas, NaN,
infinities, unpaired surrogate escapes, and duplicate object keys after escape
decoding fail. Duplicate detection occurs before host mapping construction.

Object order and string escape spelling are ignored; array order is significant.
Value and lexical number modes follow the common model. Default policy remains
equal/pass and different/fail. Malformed syntax produces failed/decode_error.
Crossing a configured bound produces failed/resource_limit_exceeded.

## YAML contract and dependency gate

```python
class YamlCompareSpec:
    kind: Literal["yaml"] = "yaml"
    profile: Literal["yaml12_core_safe"] = "yaml12_core_safe"
    encoding: Literal["utf-8", "utf-8-sig"] = "utf-8"
    limits: YamlResourceLimits = YamlResourceLimits()
```

The profile is YAML 1.2.2 Core with deliberate restrictions:

- exactly one document; empty and multi-document streams fail;
- keys resolve to unique strings;
- only null, boolean, integer, finite decimal, string, sequence, and mapping
  values enter the private tree;
- tags outside the seven admitted Core value types, object constructors, merge
  keys (`<<`), timestamp
  and binary tags, sets, ordered maps, and pairs fail;
- aliases may express an acyclic graph, while cycles fail and alias, depth,
  composed-node, and expanded-node counts are independently bounded;
- only a compatible `%YAML 1.2` directive is allowed; and
- comments, scalar/collection style, key order, anchor names, and tag spelling
  are not comparison dimensions.

There is no YAML 1.1 resolution fallback: `yes`, `no`, `on`, and `off` are
strings; `true` and `false` are booleans. This safe profile rejects non-finite
YAML floats even though the broader Core schema recognizes them.

The candidate backend is `ruamel.yaml` in an optional `yaml` extra, pinned to a
reviewed range at implementation time. The host uses its pure-Python safe YAML
1.2 event path rather than eager object construction, recreates a parser after
failure, validates tags/events, and builds its own tree while enforcing counters
before allocating the next host node. Import occurs only for explicit YAML.
Missing/incompatible backend returns resolving-stage
unavailable/backend_unavailable, never fallback to text, JSON, or YAML 1.1.

The dependency gate records version, MIT license, Python/platform support,
source/wheel size, transitive dependencies, advisories, and why PyYAML's YAML
1.1 resolver is not equivalent. Acceptance requires hostile alias, tag,
duplicate-key, depth, and multi-doc tests. Installing the extra cannot alter
default or auto behavior.

## Delimited-table contract

```python
class TableCompareSpec:
    kind: Literal["table"] = "table"
    dialect: Literal["csv", "tsv"]
    header: Literal["first_row", "none"] = "first_row"
    alignment: Literal["position", "key"] = "position"
    key_columns: tuple[str, ...] = ()
    column_order: Literal["exact", "by_name"] = "exact"
    columns: tuple[ColumnSpec, ...] = ()
    limits: TableResourceLimits = TableResourceLimits()

class ColumnSpec:
    name: str
    dtype: Literal["string", "integer", "float64", "boolean"]
    missing_tokens: tuple[str, ...] = ()
    numeric: NumericPolicy | None = None
```

CSV uses Python `csv`'s `excel` settings with comma delimiter; TSV substitutes
tab. Both use double quotes, doubled-quote escaping, strict parsing, and embedded
newlines. Sniffing is forbidden. Encoding is strict UTF-8 with explicit
`utf-8-sig` available.

`first_row` requires a non-empty header with unique names. `none` assigns
`column_1`, `column_2`, ... from the first row; zero rows means zero columns.
All rows have the established width. Empty strings are values. Missing exists
only through exact tokens declared by `ColumnSpec`, matched before typed parsing.

Without a complete column schema, all cells are strings. A complete schema lists
each column once as `string`, `integer`, `float64`, or `boolean`, with explicit
missing tokens. Nothing is inferred. Integers are base-10 without separators;
floats accept finite decimal/scientific forms and exact `nan`, `inf`, `-inf`;
booleans are exact `true`/`false`. Typed parse failures are decode errors.
`numeric` is required for `float64` and forbidden for other dtypes. Column names
and missing tokens are unique Unicode scalar strings and remain case-sensitive.
CSV record terminators and quoting are visible recorded decoding transformations,
but are not table-value comparison dimensions.

Positional alignment compares row/column positions. Key alignment requires a
header, at least one string/integer non-missing key column, and unique complete
keys on each side. Missing/duplicate keys fail at aligning and are never paired.
Matched, removed, then added rows each sort by canonical key. Exact column order
treats reorder as schema difference; by-name aligns unique names canonically.

```python
class TableChange:
    kind: Literal["table_change"]
    operation: Literal[
        "column_add", "column_remove", "column_reorder",
        "row_add", "row_remove", "cell_replace"
    ]
    row: int | None
    key_digest: str | None
    column: str | None
    before_digest: str | None
    after_digest: str | None
```

Rows are one-based data rows excluding the header. Key and cell values are
represented only by canonical typed SHA-256 digests. Schema changes precede row
changes, then cell changes, with deterministic alignment order inside each group.

## Dense-array contract

The first array gate is API-only:

```python
class ArraySource:
    shape: tuple[int, ...]
    dtype: Literal["bool", "int64", "uint64", "float64"]
    values: tuple[bool | int | float, ...]
    label: str

class ArrayCompareSpec:
    kind: Literal["array"] = "array"
    alignment: Literal["position"] = "position"
    numeric: NumericPolicy = NumericPolicy()
    limits: ArrayResourceLimits = ArrayResourceLimits()
```

Construction validates and copies values. Row-major C order is normative and
length equals the checked shape product. Zero-length dimensions and rank-zero
scalars are allowed. Boolean is not integer; integers fit their declared dtype;
float values convert once to IEEE 754 binary64. The conversion and source kind
are recorded. Object coercion, post-construction iteration, buffer aliasing, and
mutation are forbidden.

Shape and dtype must match. No broadcast, squeeze, reshape, transpose, relabel,
cross-dtype cast, or coordinate alignment occurs. Shape/dtype mismatch is a
completed difference with one schema-level change, not alignment failure.

```python
class ArrayChange:
    kind: Literal["array_change"]
    operation: Literal["shape_replace", "dtype_replace", "element_replace"]
    index: tuple[int, ...] | None
    before_digest: str
    after_digest: str
    absolute_error: MetricNumber | None
    relative_error: MetricNumber | None
```

Element changes use row-major index order and canonical typed scalar digests.
Errors exist only for finite numeric pairs. No array CLI exists until a file
representation is separately selected. Ecosystem adapters need dependency,
ownership, dtype, coordinate, missing-value, and license review.

## Numeric and missing-value semantics

```python
class NumericPolicy:
    atol: float = 0.0
    rtol: float = 0.0
    relative_reference: Literal["before"] = "before"
    nan_equal: bool = False
    signed_zero_equal: bool = True
```

Finite values are equal exactly when:

```text
abs(after - before) <= atol + rtol * abs(before)
```

Tolerances are finite, non-negative binary64; the boundary is inclusive.
Integer/boolean values ignore tolerance. Same-sign infinities are equal; other
infinite pairs differ. NaN equals NaN only when opted in. Signed zeros are equal
by default; when disabled their sign bits differ before tolerance.

Missing is a separate tagged state: missing equals missing and no present value.
Keys cannot be missing; first-gate arrays have no missing state. Decimal,
complex, datetime, units, ULP, symmetric tolerance, and statistical equivalence
are deferred.

Metrics report compared/equal/changed, missing, NaN, infinity, and finite-numeric
pair counts. Numeric comparisons report maximum absolute and relative error over
finite unequal pairs, or an explicit unavailable metric for an empty population.
No mean is defined, avoiding an unspecified floating-point accumulation order.
Tolerance changes relation because it is explicit intent; renderers cannot
apply or reinterpret it. Strict default policy remains equal/pass and
different/fail.

## Resources and failures

The serialized limit field names are fixed by these conceptual records; YAML
extends rather than reinterprets the common structured limits:

```python
class StructuredResourceLimits:
    max_input_bytes: int = 16 * 1024 * 1024
    max_scalar_bytes: int = 1024 * 1024
    max_depth: int = 256
    max_nodes: int = 1_000_000
    max_number_digits: int = 10_000
    max_abs_exponent: int = 1_000_000
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

class YamlResourceLimits(StructuredResourceLimits):
    max_aliases: int = 10_000
    max_expanded_nodes: int = 1_000_000

class TableResourceLimits:
    max_input_bytes: int = 16 * 1024 * 1024
    max_cell_bytes: int = 1024 * 1024
    max_rows: int = 200_000
    max_columns: int = 10_000
    max_cells: int = 1_000_000
    max_number_digits: int = 10_000
    max_abs_exponent: int = 1_000_000
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

class ArrayResourceLimits:
    max_rank: int = 32
    max_elements: int = 2_000_000
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024
```

| Default limit | JSON/YAML | Table | Array |
| --- | ---: | ---: | ---: |
| Bytes per serialized input | 16 MiB | 16 MiB | n/a |
| UTF-8 bytes per scalar/cell | 1 MiB | 1 MiB | n/a |
| Nesting depth/rank | 256 | n/a | 32 |
| Nodes/elements | 1,000,000 | 1,000,000 cells | 2,000,000 elements |
| Rows/columns | n/a | 200,000 / 10,000 | n/a |
| Number digits / absolute exponent | 10,000 / 1,000,000 | 10,000 / 1,000,000 | fixed dtype |
| YAML aliases / expanded nodes | 10,000 / 1,000,000 | n/a | n/a |
| Compare work units | 5,000,000 | 5,000,000 | 5,000,000 |
| Returned changes / payload | 10,000 / 4 MiB | 10,000 / 4 MiB | 10,000 / 4 MiB |

Dimension products use checked arithmetic before allocation. Decoders increment
counters before constructing a node, row, cell, or expanded alias. Comparator
work units are documented per implementation and never use wall-clock time.

Limit failure uses existing `resource_limit_exceeded` or
`compare_resource_limit` with the observed stage. Syntax/typed-cell failure uses
`decode_error`; missing YAML backend is unavailable; unsupported source is
`source_type_unsupported`. Duplicate or missing table keys use the new stable
`alignment_failed` code, HTTP-style status 422, and the aligning stage. Unknown
exceptions are not swallowed by the library.

No relation is returned before complete semantic comparison and total change
count. Phase 4 therefore emits only complete/truncated change sets; truncation
cannot change relation, verdict, fidelity, metrics, or total. Fidelity is full
because fallback is forbidden. Artifacts are empty. Diagnostics/provenance never
contain raw scalar/cell/key values, tracebacks, absolute/environment paths, or
unbounded backend messages. Structured paths and table column names are bounded
comparison coordinates in changes and are always treated as untrusted text.

## CLI and public API boundary

```text
platydiff json BEFORE AFTER
platydiff compare --type json BEFORE AFTER
platydiff yaml BEFORE AFTER
platydiff compare --type yaml BEFORE AFTER
platydiff table --dialect csv BEFORE AFTER
platydiff compare --type table --dialect csv BEFORE AFTER
```

Aliases share one path. Array is Python-only. Existing renderers accept validated
v3 outcomes after their gate. Exit codes remain 0 equal/pass, 1 completed
non-pass, 2 usage, and 3 unavailable/failed/renderer failure.

Structured commands reject plugin/detector/comparator flags at argparse with
exit 2 before discovery. They accept no stdin, directory, URL, configuration,
inferred type/dialect, or artifact output. Top-level exports add only accepted
specs, sources, policies, outcomes, and enums. Parsers, IRs, canonical encoders,
alignment indexes, counters, and registries remain private. The existing
`compare(before, after, spec)` signature remains.

## Delivery gates, commits, and tests

These are plans, not implementation authorization.

### P4-A1: schema v3 and JSON

1. `feat(core): add schema-v3 structured comparison contracts`
2. `feat(json): add bounded semantic JSON comparison`
3. `feat(cli): add explicit JSON comparison commands`
4. `docs: document schema v3 and JSON comparison`

Tests cover v1/v2 stability and migration, strict v3 round trips, all model
invariants, duplicate keys, number modes, pointers, ordering, every limit,
truncation, source mutation, CLI aliases/exits, and randomized tree oracles.

### P4-A2: YAML backend

1. `build(yaml): add the reviewed optional YAML backend`
2. `feat(yaml): add the bounded YAML 1.2 safe profile`
3. `feat(cli): add explicit YAML comparison commands`
4. `docs: document YAML semantics and dependency provenance`

Tests cover missing backend, pure safe loading, YAML 1.1 ambiguity tokens, tags,
merges, duplicates, aliases, cycles, multi-doc input, parser recreation, hostile
depth/expansion, dependency inventory, and unchanged existing auto fixtures.

### P4-B1: delimited tables

1. `feat(table): add typed delimited-table contracts`
2. `feat(table): add bounded positional and keyed comparison`
3. `feat(cli): add explicit table comparison commands`
4. `docs: document table schemas alignment and numeric policy`

Tests cover malformed quoting, embedded newlines, empty/header-only and ragged
input, duplicate headers/keys, every dtype/missing token, alignments, column
order, tolerance boundaries, NaN/Inf/signed zero, limits, determinism, and exits.

### P4-B2: dense arrays

1. `feat(array): add immutable dense-array sources and contracts`
2. `feat(array): add deterministic dense-array comparison`
3. `docs: document array dtype shape and numeric semantics`

Tests cover scalar/empty/multidimensional shapes, checked products, copy and
mutation isolation, dtype bounds, row-major indices, schema changes, numeric
special cases/boundaries, deterministic metrics, truncation, and work limits.

Every gate runs Ruff format/lint, strict mypy, complete pytest, build,
wheel/sdist inspection, and documentation/link checks. Public models add
serialization/migration fixtures; dependency gates add license/package evidence.

## Later-phase callbacks

Structured auto detection must first define probe budgets, JSON/YAML/text
ambiguity, pair selection, ordering, override, and attribution in a successor to
RFC 0003. New plugin modalities must define SDK v2 ownership, source views,
canonicalization, validation, receipts, and versions in a successor to RFC 0005.

Ecosystem/sparse/unit-aware data must define ownership, dtypes, masks,
coordinates, chunks, endianness, memory mapping, decompression, dependencies,
licenses, and platforms. Statistical work must define hypotheses, correction,
sample size, effect size, confidence, seeds, aggregation, and verdict impact.
Richer presentation returns to RFC 0004; it may display validated facts but
cannot fetch values or compare them.

## References

- [RFC 8259: JSON](https://www.rfc-editor.org/rfc/rfc8259)
- [RFC 6901: JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901)
- [YAML 1.2.2 specification](https://yaml.org/spec/1.2.2/)
- [YAML 1.2.2 changes](https://yaml.org/spec/1.2.2/ext/changes/)
- [Python `csv` documentation](https://docs.python.org/3/library/csv.html)
- [`ruamel.yaml` metadata](https://pypi.org/project/ruamel.yaml/)
- [`ruamel.yaml` safe/pure loader](https://yaml.dev/doc/ruamel.yaml/basicuse/)
