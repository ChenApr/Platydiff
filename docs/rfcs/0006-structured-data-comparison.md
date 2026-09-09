# RFC 0006: Structured Data Comparison

[Chinese documentation](0006-structured-data-comparison_zh.md)

- Status: Accepted
- Date: 2026-09-10
- Accepted: 2026-09-10
- Review revision: 2026-09-10
- Approved decisions: S1-S13
- Owners: Platydiff maintainers
- Implementation owner: unassigned pending separate implementation authorization

## Summary and authorization boundary

This RFC defines the accepted Phase 4 contracts for JSON, a constrained YAML 1.2 profile,
delimited tables, and dense arrays. It defines schema evolution, equality,
paths, alignment, limits, failures, and delivery gates. It does not authorize
implementation, dependency changes, a new plugin SDK, structured-data automatic
detection, or UI work. Each implementation gate requires a separate dispatch
from updated `main`; later gates do not start automatically.

Human approval on 2026-09-10 accepts decisions S1-S13 and authorizes this RFC
documentation PR only. P4-A1, P4-A2, P4-B1, and P4-B2 remain unimplemented and
independently gated. Acceptance does not authorize starting, delegating, or
implying any Phase 4 implementation.

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

## Approved decisions

| ID | Accepted decision | Alternative that was not selected |
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
| S13 | Default JSON/YAML/table detail to bounded typed values and actual keyed coordinates, while retaining evidence digests; an explicit `digest_only` spec mode omits those facts without changing comparison truth. | Default to digest-only and accept value-blind human review, or let renderers reread sources, which violates the outcome boundary. |

Decisions S1-S13 were approved on 2026-09-10. Their acceptance establishes the
design contract and permits this documentation PR; it does not authorize any
implementation gate.

The 2026-09-10 review revision tightens evidence digests, change invariants,
metrics, provenance vocabulary, privacy claims, and resource accounting. It
does not change any S1-S12 recommendation. It does change the proposed keyed
table coordinate from a deterministic `key_digest` to a canonical
`key_ordinal`, reducing guessable digest exposure in `digest_only` while
preserving deterministic navigation. A later review adds S13 because outcome
content versus permanently
value-blind human review is a product decision, not a renderer detail.

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
| Accepted, unimplemented Phase 4 built-in path | v3 | explicit json/yaml/table/array | none | v3 validates new variants and all inherited invariants. |
| Accepted, unimplemented `PluginHost` behavior with Phase 4 spec | none | unsupported | rejected before execution | Python returns resolving-stage unavailable; CLI plugin flags plus a Phase 4 type are usage exit 2. |
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
    before_fact: ScalarFact | SubtreeFact | None
    after_fact: ScalarFact | SubtreeFact | None
```

Digests use the domain-separated evidence encoding below. Add lacks before
facts, remove lacks after facts, and replace has both. Type changes are
replacements; moves are not inferred. Changes are observations, not patches.
Deterministic depth-first pre-order uses sorted mapping keys and rising sequence
indices. A wholly added/removed subtree produces one change at its highest
pointer. Full count is known before applying item/payload truncation.
Pointers necessarily expose bounded decoded mapping-key names as comparison
coordinates. They never expose scalar values, and renderers must escape them as
untrusted text.

### Evidence digest and privacy contract

Every `*_digest` is lowercase SHA-256 over this framing:

```text
UTF8("platydiff/v3/" + domain) || 0x00 || U64BE(payload_length) || payload
```

Canonical structured-value payload tags are `00` null, `01` false, `02` true,
`03` integer, `04` decimal, `05` string, `06` sequence, and `07` mapping.
Variable fields use U64BE byte lengths. Integers use one sign byte followed by
minimal big-endian unsigned magnitude; zero has positive sign and empty
magnitude. Value-mode decimals use one sign byte, canonical ASCII coefficient
without leading/trailing zeroes, and minimal signed big-endian exponent; zero is
positive coefficient `0` exponent zero. Strings use UTF-8, sequences retain
order, and mappings contain canonical string-key/value pairs in key order.
Container element counts precede children.
The encoder feeds this framing incrementally into SHA-256 and never materializes
a complete container payload; encoded lengths use checked arithmetic. The exact
byte fixtures are a schema-v3 compatibility artifact.

Structured value mode uses domain `structured/value`. In JSON lexical number
mode, a number uses domain `structured/number/lexical` and its payload is the
exact validated UTF-8 number token, including sign, decimal point, exponent
marker/sign, and zeroes. Therefore `1`, `1.0`, and `1e0` yield distinct evidence
digests and a coherent replace change in lexical mode, while value mode produces
no change.

Evidence digests are reproducible integrity fingerprints, not encryption,
redaction, or proof that a value is secret. Low-entropy values can be recovered
by dictionary guessing, and equality of equal domain/payload pairs is visible.
Conversely, equal digests do not alone prove comparison equality: a policy can
declare identical NaN representations unequal. Relation and policy evaluation
remain authoritative.
Changing a digest to a randomized or keyed construction would be a schema
change because it would weaken deterministic cross-run evidence. Callers must
protect an outcome as they protect pseudonymous source-derived metadata; a
renderer labels these fields as evidence digests and does not call them hidden
or anonymous. Compatibility tests include known low-entropy inputs to document
guessability and prevent a false secrecy claim.

## Outcome content and human-review contract

S13 recommends human-usable detail by default because existing text changes
carry bounded line content and renderers are deliberately source-blind. JSON,
YAML, and table specs therefore add this normalized field:

```python
detail_mode: Literal["values", "digest_only"] = "values"
```

`detail_mode` affects only returned change facts and their payload truncation.
It never changes decoding, alignment, relation, verdict, fidelity, summary
totals, metrics, evaluations, evidence digests, or provenance other than the
normalized spec itself. CLI commands expose `--detail values|digest_only` with
the same default. A renderer option cannot retroactively recover facts omitted
by the spec.

Typed facts are JSON-safe and immutable:

```python
class ScalarFact:
    kind: Literal[
        "null", "boolean", "integer", "decimal", "string", "missing",
        "float64", "nan", "positive_infinity", "negative_infinity"
    ]
    value: bool | str | None
    lexical: str | None = None

class SubtreeFact:
    kind: Literal["sequence", "mapping"]
    descendant_count: int
    scalar_count: int

class TableRowFact:
    cells: tuple[tuple[str, ScalarFact], ...]

class ColumnSchemaFact:
    name: str
    dtype: Literal["string", "integer", "float64", "boolean"]
    missing_token_count: int
    numeric: NumericPolicy | None

class ColumnOrderFact:
    names: tuple[str, ...]

type TableFact = ScalarFact | TableRowFact | ColumnSchemaFact | ColumnOrderFact
```

`null`, `missing`, NaN, and infinity facts require `value=None`. Boolean uses a
JSON boolean. Integer uses canonical base-10 text; decimal uses canonical
`[-]coefficientEexponent`; finite float64 uses lowercase C99 hexadecimal form,
including the zero sign. String contains the decoded Unicode scalar value.
`lexical` is present only for a JSON number in lexical mode and contains its
validated token; otherwise it is absent. Kinds not admitted by a modality fail
validation. Strings, lexical tokens, names, rows, and tuples retain the existing
scalar/cell/column/count limits.

`SubtreeFact.descendant_count` counts nodes strictly below its container root;
`scalar_count` counts scalar nodes among those descendants, is never greater
than `descendant_count`, and both are zero for an empty container. A
`TableRowFact` contains exactly one `(column_name, fact)` pair per aligned column,
in aligned column order, with unique names and kinds matching the column schema.
All counts are non-negative exact integers.

In `values` mode, each present scalar side of a `StructuredChange` has the
matching `ScalarFact`. A present sequence/mapping side instead has a
`SubtreeFact`: a wholly added/removed container remains one highest-pointer
change and carries type plus total descendant/scalar counts, not a recursively
inlined subtree. A type replacement may therefore have scalar fact on one side
and subtree fact on the other. In `digest_only`, both fact fields are absent.
The operation's absent side always has neither digest nor fact.

Table changes use `before_fact` and `after_fact` according to the operation
mapping below. In `values` mode, keyed row/cell changes also carry the actual
ordered composite key as `key: tuple[ScalarFact, ...]`; positional changes have
no key. In `digest_only`, `key` and all facts are absent while `key_ordinal`,
column coordinate, operation, and evidence digests remain. Key facts must match
the declared key-column count and string/integer types. These invariants are
validated with the normalized spec, so a detached change cannot silently claim
a different detail mode.

| Table operation | Fact type on each present side |
| --- | --- |
| `column_add` / `column_remove` | `ColumnSchemaFact` |
| `column_reorder` | `ColumnOrderFact` |
| `row_add` / `row_remove` | `TableRowFact`, with cells in aligned column order |
| `cell_replace` | `ScalarFact` matching the declared column dtype/missing state |

Every returned change is atomic. Its operation, coordinates, digests, and all
facts are encoded together when charged to `max_change_payload_bytes`. If the
next complete item would exceed either payload or item limit, that item and all
later source-order items are omitted; no value, row, key, or subtree fact is
partially serialized. Full comparison and `total_count` still complete first.
Consequently `values` and `digest_only` can have different `returned_count` and
truncation points but identical comparison truth and total count.

Values mode can expose secrets, tokens, identifiers, scientific data, and PII
in terminal and schema JSON. It is the recommended default for useful human
review and consistency with text diff, not a confidentiality default. Users
handling sensitive inputs must select `digest_only` before comparison and still
treat paths, column names, ordinals, counts, source hashes, and guessable
evidence digests as pseudonymous metadata. `digest_only` is not called redacted
or anonymous.

Terminal rendering prints returned typed facts with control-safe escaping,
visible string boundaries, and explicit type labels; it never emits raw control
sequences. JSON rendering serializes the exact validated facts. Digest-only
rendering visibly states that values and keyed coordinates were omitted by the
comparison spec. Future RFC 0004 surfaces follow the same rules.

Renderers and UI still may not reread original inputs: doing so would bypass the
snapshot, mutation, byte-limit, provenance, detail-mode, and truncation
contracts; make rendering depend on source availability; and allow presentation
to disclose data the comparison intentionally omitted. Schema-v3 readers require
the detail mode and fact fields described here. Changing the default, field
meaning, atomic truncation, or fact encoding after release requires a schema
migration and compatibility fixtures; v1/v2 remain unaffected.

## JSON contract

```python
class JsonCompareSpec:
    kind: Literal["json"] = "json"
    encoding: Literal["utf-8", "utf-8-sig"] = "utf-8"
    number_mode: Literal["value", "lexical"] = "value"
    detail_mode: Literal["values", "digest_only"] = "values"
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
    detail_mode: Literal["values", "digest_only"] = "values"
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
    detail_mode: Literal["values", "digest_only"] = "values"
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
    key_ordinal: int | None
    key: tuple[ScalarFact, ...] | None
    column: str | None
    before_digest: str | None
    after_digest: str | None
    before_fact: TableFact | None
    after_fact: TableFact | None
```

For positional alignment, `row` is present and `key_ordinal`/`key` are absent on
every row/cell operation. It is the one-based before index for `row_remove`, the
one-based after index for `row_add`, and the shared position for `cell_replace`.
For keyed alignment, `row` is absent and `key_ordinal` is the one-based rank of
the key in the canonical sorted union of before/after keys. `key` follows S13's
detail-mode invariant. Physical keyed-row order is ignored. All three
coordinates are absent on column operations.

`column` is present for column add/remove and cell replace, and absent for
column reorder and row add/remove. Add operations have only after digest/fact;
remove operations have only before digest/fact; reorder and replace operations
have both, subject to fact omission in `digest_only`. The digest domains and
payloads are:

| Operation | Domain | Canonical payload |
| --- | --- | --- |
| `column_add` / `column_remove` | `table/column/schema` | name, dtype, ordered missing tokens, and numeric policy |
| `column_reorder` | `table/columns/order` | complete ordered column-name sequence on that side |
| `row_add` / `row_remove` | `table/row` | complete row in aligned column order, including typed missing markers |
| `cell_replace` | `table/cell` | one typed cell value or missing marker |

`key_ordinal` avoids publishing a deterministic digest of often low-entropy key
values and is the only key coordinate in `digest_only`; it still reveals union
cardinality and relative canonical order. S13 `values` mode deliberately carries
the actual typed key facts instead. Column names remain bounded untrusted
coordinates. Schema changes precede row changes, then cell changes, with
deterministic alignment order inside each group. Strict model validation rejects
every illegal field combination before serialization or after parsing.

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

Shape and dtype are compared independently. No broadcast, squeeze, reshape,
transpose, relabel, cross-dtype cast, or coordinate alignment occurs. A shape
mismatch emits `shape_replace`; a dtype mismatch emits `dtype_replace`; when
both differ, both changes appear in that order. Any schema mismatch suppresses
element comparison and is a completed difference, not alignment failure.

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

`shape_replace` and `dtype_replace` require `index=None`, both digests, and no
error fields. Their domains are `array/shape` over rank plus ordered dimensions,
and `array/dtype` over the exact dtype identifier. `element_replace` requires an
in-bounds full-rank index and both `array/scalar` digests over the declared dtype
plus canonical scalar bits. Its error fields follow the numeric rules below;
non-numeric or non-finite pairs have both errors absent. Element changes use
row-major index order. Strict construction and round-trip parsing reject any
operation/field mismatch. No array CLI exists until a file representation is
separately selected. Ecosystem adapters need dependency, ownership, dtype,
coordinate, missing-value, and license review.

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

For one finite pair, `absolute_error = abs(after-before)`. Relative error is
`absolute_error / abs(before)` when `before != 0`, zero when both values are
zero, and tagged positive infinity when `before == 0` and the absolute error is
non-zero. It is absent for pairs containing NaN or infinity. Maximum error
metrics include all finite numeric pairs, including pairs accepted by tolerance
and positive-infinity relative errors caused by a zero reference. They are
omitted, rather than encoded as zero or NaN, when
`finite_numeric_pairs == 0`.

### Stable metric registry

All count metrics use finite integer-valued `NumericValue`, unit `items`, and
aggregation `count`. They are always present. Maximum metrics use binary64
`NumericValue`, aggregation `maximum`, and are conditionally present as stated.
JSON/YAML admit neither missing nor non-finite values and define no tolerance
error metric, so missing/NaN/infinity counts and maximum errors are inapplicable
and absent for those modalities rather than serialized as invented zeroes.

| Modality | Metric name | Meaning/applicability | Unit | Direction | Empty population |
| --- | --- | --- | --- | --- | --- |
| JSON | `json.compared_values` | visited paired values plus roots of wholly added/removed subtrees | `items` | `neutral` | zero |
| JSON | `json.equal_values` | visited values equal under selected number mode | `items` | `neutral` | zero |
| JSON | `json.changed_values` | emitted add/remove/replace observations before truncation | `items` | `lower_is_better` | zero |
| YAML | `yaml.compared_values` | same counting rule as JSON | `items` | `neutral` | zero |
| YAML | `yaml.equal_values` | values equal under YAML semantic profile | `items` | `neutral` | zero |
| YAML | `yaml.changed_values` | emitted observations before truncation | `items` | `lower_is_better` | zero |
| Table | `table.compared_cells` | aligned cell pairs actually evaluated | `items` | `neutral` | zero |
| Table | `table.equal_cells` | evaluated pairs equal under dtype/missing/numeric policy | `items` | `neutral` | zero |
| Table | `table.changed_cells` | unequal evaluated cell pairs | `items` | `lower_is_better` | zero |
| Table | `table.changed_items` | all column, row, and cell changes before truncation | `items` | `lower_is_better` | zero |
| Table | `table.missing_pairs` | evaluated pairs with at least one missing side | `items` | `neutral` | zero |
| Table | `table.nan_pairs` | evaluated float pairs with at least one NaN | `items` | `neutral` | zero |
| Table | `table.infinity_pairs` | evaluated float pairs with at least one infinity | `items` | `neutral` | zero |
| Table | `table.finite_numeric_pairs` | evaluated pairs with two finite float64 values | `items` | `neutral` | zero |
| Table | `table.maximum_absolute_error` | all finite float64 pairs | `numeric_values` | `lower_is_better` | metric omitted |
| Table | `table.maximum_relative_error` | all finite float64 pairs | `ratio` | `lower_is_better` | metric omitted |
| Array | `array.compared_elements` | positional element pairs evaluated when shape/dtype match | `items` | `neutral` | zero |
| Array | `array.equal_elements` | evaluated pairs equal under numeric policy | `items` | `neutral` | zero |
| Array | `array.changed_elements` | unequal evaluated element pairs | `items` | `lower_is_better` | zero |
| Array | `array.changed_items` | shape, dtype, or element changes before truncation | `items` | `lower_is_better` | zero |
| Array | `array.missing_pairs` | reserved first-gate count, always zero | `items` | `neutral` | zero |
| Array | `array.nan_pairs` | float pairs with at least one NaN | `items` | `neutral` | zero |
| Array | `array.infinity_pairs` | float pairs with at least one infinity | `items` | `neutral` | zero |
| Array | `array.finite_numeric_pairs` | float64 pairs with two finite values | `items` | `neutral` | zero |
| Array | `array.maximum_absolute_error` | all finite float64 pairs | `numeric_values` | `lower_is_better` | metric omitted |
| Array | `array.maximum_relative_error` | all finite float64 pairs | `ratio` | `lower_is_better` | metric omitted |

Metric order is exactly table order filtered to the current modality and
applicability. No mean is defined, avoiding an unspecified accumulation order.
Count identities such as equal plus changed equals compared are validated when
applicable; schema/unmatched-row changes contribute to changed items, not
changed cells.

For JSON/YAML, the counted observation frontier consists of scalar pairs, empty
container pairs, type-mismatch pairs, and the highest roots of wholly
added/removed subtrees. A non-empty paired container that is descended is not a
separate observation. Equal and changed values partition this frontier, and
changed values equals `changes.total_count`. For tables, equal plus changed cells
equals compared cells. For arrays with matching shape/dtype, equal plus changed
elements equals compared elements; on schema replacement all three element
counts are zero and changed items is one or two according to the number of
shape/dtype replacements.

Tolerance is comparison intent and determines cell/element equality and thus
relation. It is not itself a verdict threshold. Exactly one default evaluation
is present: `json.semantic_equality` observes `json.changed_values`,
`yaml.semantic_equality` observes `yaml.changed_values`,
`table.value_equality` observes `table.changed_items`, or
`array.value_equality` observes `array.changed_items`, each with operator `eq`
and threshold zero. Observed zero yields pass; non-zero yields fail. No default
rule yields warn. Renderers display the recorded metric and evaluation and do
not reapply tolerance or derive verdict.

## Normalization, alignment, and provenance vocabulary

The normalized spec records all effective caller intent, including defaults.
`TransformationRecord` records behavior actually executed after validation; it
does not encode a second choice, infer user intent, or claim that a syntactic
feature occurred. Records use this fixed stage/id/order vocabulary:

| Modality | Stage | Transformation ID | When recorded / parameters |
| --- | --- | --- | --- |
| JSON | decoding | `json.decode.utf8` | bytes/path input; effective encoding |
| JSON | normalizing | `json.object_order.ignore` | always; no parameters |
| JSON | normalizing | `json.number.value` or `json.number.lexical` | always; selected mode |
| JSON | aligning | `json.pointer.position` | always; RFC 6901 and positional arrays |
| YAML | decoding | `yaml.decode.utf8` | bytes/path input; encoding and `yaml12_core_safe` profile |
| YAML | normalizing | `yaml.presentation.elide` | always; comments, style, and anchor names |
| YAML | normalizing | `yaml.object_order.ignore` | always; no parameters |
| YAML | aligning | `yaml.pointer.position` | always; RFC 6901 and positional sequences |
| Table | decoding | `table.csv.decode` or `table.tsv.decode` | always; dialect, encoding, header policy |
| Table | normalizing | `table.presentation.elide` | always; quoting and record terminators |
| Table | normalizing | `table.cells.typed` | only with column schema; dtype and missing-token policy digest |
| Table | aligning | `table.columns.exact` or `table.columns.by_name` | always; selected column mode |
| Table | aligning | `table.rows.position` or `table.rows.key` | always; selected row mode and key-column names |
| Array | decoding | `array.float64.convert` | float64 source; conversion=`ieee754_binary64`, roles converted |
| Array | aligning | `array.elements.position` | always; order=`c_row_major` |

For YAML, presentation elision covers comment/style/anchor-name removal, while
alias expansion is structural decoding and is represented by resource usage,
not called normalization. Table parameter values are JSON-safe and bounded;
the missing-token policy is represented by the same evidence-digest threat
model rather than raw tokens. Writers emit records in the order above. Readers
require known built-in IDs for schema-v3 built-in results and test exact round
trips; later IDs require a schema change or a namespaced extension mechanism.

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
    max_expanded_scalar_bytes: int = 16 * 1024 * 1024

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
| YAML aliases / expanded nodes / expanded scalar bytes | 10,000 / 1,000,000 / 16 MiB | n/a | n/a |
| Compare work units | 5,000,000 | 5,000,000 | 5,000,000 |
| Returned changes / payload | 10,000 / 4 MiB | 10,000 / 4 MiB | 10,000 / 4 MiB |

`max_input_bytes` counts original source bytes before decoding. For `TextSource`,
it counts strict UTF-8 encoding exactly as existing source handling does.
`max_scalar_bytes` and `max_cell_bytes` count the decoded Unicode scalar's UTF-8
length after escape removal, YAML scalar resolution, or CSV unquoting; original
token bytes remain bounded by `max_input_bytes`. YAML counts each composed scalar
once against `max_scalar_bytes`, each alias occurrence against `max_aliases`,
every materialized occurrence against `max_expanded_nodes`, and the UTF-8 length
of every materialized scalar occurrence—including aliases—against
`max_expanded_scalar_bytes`.

`max_number_digits` counts every ASCII digit in the validated source token before
normalization, including integer, fractional, and exponent digits. Sign, decimal
point, and exponent marker do not count. `max_abs_exponent` applies to the parsed
base-10 exponent after fractional-place adjustment. Parsing checks digit count
and exponent magnitude incrementally; it never constructs a proportional power
of ten, integer, or decimal first.

Required deterministic work is charged before performing the next logical unit:

- JSON/YAML: one unit per paired node visited and one per wholly added/removed
  subtree root; decoding and canonical-digest bytes are bounded separately;
- table positional: one per compared column-schema item, aligned cell pair, and
  unmatched row; keyed mode additionally charges one per input row indexed and
  one per UTF-8 byte in its canonical composite key; and
- array: one per paired or unmatched shape dimension, one for the dtype
  comparison, and—only when both schema checks match—one per element pair.

Canonical keyed sorting remains bounded by row, cell, key-byte, and computed
work limits; the implementation gate must use a deterministic sort independent
of locale and source order. These formulas are schema-v3 compatibility fixtures,
not implementation notes.

Dimension products and cumulative byte/work additions use checked arithmetic.
Host counters are checked before allocating the next host node, decoded scalar,
expanded alias value, row, cell, key entry, or array buffer. The YAML backend may
allocate bounded parser tokens from the already byte-limited source, but it must
not eagerly construct an unbounded application object graph. No normal result
depends on wall-clock time.

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
truncation, source mutation, CLI aliases/exits, transformation vocabulary, and
randomized tree oracles. Fixtures prove that lexical `1`, `1.0`, and `1e0`
produce distinct coherent change digests while value mode remains equal. Known
low-entropy fixtures document digest guessability rather than claiming secrecy.
Value/digest-only scalar and subtree facts, atomic whole-item truncation, safe
terminal rendering, and proof that both modes preserve comparison truth are
compatibility cases.

### P4-A2: YAML backend

1. `build(yaml): add the reviewed optional YAML backend`
2. `feat(yaml): add the bounded YAML 1.2 safe profile`
3. `feat(cli): add explicit YAML comparison commands`
4. `docs: document YAML semantics and dependency provenance`

Tests cover missing backend, pure safe loading, YAML 1.1 ambiguity tokens, tags,
merges, duplicates, aliases, cycles, multi-doc input, parser recreation, hostile
depth/expansion, value/digest-only scalar and subtree facts, atomic payload
truncation, dependency inventory, and unchanged existing auto fixtures.

### P4-B1: delimited tables

1. `feat(table): add typed delimited-table contracts`
2. `feat(table): add bounded positional and keyed comparison`
3. `feat(cli): add explicit table comparison commands`
4. `docs: document table schemas alignment and numeric policy`

Tests cover malformed quoting, embedded newlines, empty/header-only and ragged
input, duplicate headers/keys, every dtype/missing token, alignments, column
order, tolerance boundaries, NaN/Inf/signed zero, per-operation change
invariants and digest domains, metric/evaluation fixtures, limit/work formulas,
value/digest-only facts and key coordinates, atomic payload truncation,
control-safe rendering, deterministic round trips, and exits.

### P4-B2: dense arrays

1. `feat(array): add immutable dense-array sources and contracts`
2. `feat(array): add deterministic dense-array comparison`
3. `docs: document array dtype shape and numeric semantics`

Tests cover scalar/empty/multidimensional shapes, checked products, copy and
mutation isolation, dtype bounds, row-major indices, schema changes, numeric
special cases/boundaries, shape/dtype/scalar digest domains, operation
invariants, deterministic metric/evaluation fixtures, truncation, and work
limits.

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
