# RFC 0010: Schema Predecessor and Phase 6 Contract Amendment

[Chinese documentation](0010-schema-predecessor-and-phase6-contract-amendment_zh.md)

- Status: Accepted
- Date: 2026-09-10
- Accepted: 2026-09-10
- Approved decisions: SP1-SP6; Option A/P4-C1; P6C0-1-P6C0-10
- Approved P4-C1 clarifications: P4C1-1-P4C1-5
- P4-C1 clarification approval date: 2026-09-10
- Accepted P6-C0 closure amendment: RFC 0014; contract-only and no implementation authorization
- Owners: Platydiff maintainers
- Implementation dispatch: P4-C1 has since merged; later schema work still
  requires the stated predecessor gates and explicit human dispatch

## Summary and authorization boundary

This RFC is the accepted cross-RFC amendment for a schema predecessor
contradiction found before Phase 5, Phase 6, or Phase 7 schema implementation
starts. It accepts decisions SP1-SP6, selects Option A/P4-C1, and accepts
P6C0-1 through P6C0-10 as Phase 6 contract decisions. RFC acceptance itself
does not start code. Conditional human authorization has been recorded, and
coordinator dispatch may occur only after the stated merge gates. This
documentation acceptance PR does not authorize dependency changes, public schema
implementation, or implementation of structured data, image, source-code, PDF,
audio, video, SDK v2, backend workers, artifacts, automatic detection, or UI
work.

A P4-C1 pre-implementation read-only check found additional schema-v3 reader and
fixture ambiguities. The clarifications P4C1-1 through P4C1-5 below were
approved on 2026-09-10. They supplement but do not alter SP1-SP6,
Option A/P4-C1, or P6C0-1 through P6C0-10. No code starts from this
clarification approval.

A P6-C0 closure review also found unresolved schema-v5 problem-registry and
closed-union shape gaps. [RFC 0014](0014-phase6-source-pdf-contract-closure-amendment.md)
accepts the contract-only closure amendment. It does not alter P6C0-1 through
P6C0-10 and does not authorize source or PDF implementation.

The accepted decision is to treat the missing YAML, table, and array
schema-v3 contract surface on `main` as a Phase 4 code defect, not as proof that
the accepted RFC 0006 contract was wrong. A correction gate must land before
schema v4 image, schema v5 source/PDF, schema v6 audio, or any later video
successor can use v3 as a stable predecessor. That P4-C1 correction has since
merged to `main` in PR #20. P5-A1 contract closure is accepted in RFC 0013 but
P5-A1 remains unimplemented, and P6-C0, P7-A1, and later video schema work
remain conditional on the actual predecessor merges, compatibility fixtures,
and explicit human dispatch.

## Evidence

At `origin/main` `cf3c526`, the implemented schema-v3 code exposes
`JsonCompareSpec` and `StructuredChange`. It does not expose
`YamlCompareSpec`, `TableCompareSpec`, `ArrayCompareSpec`, `TableChange`, or
`ArrayChange` as implemented schema-v3 public models.

RFC 0006 is Accepted and says the schema-v3 closed unions include:

```text
CompareSpec | JsonCompareSpec | YamlCompareSpec | TableCompareSpec | ArrayCompareSpec
TextHunk | BinarySpan | StructuredChange | TableChange | ArrayChange | ExtensionChange
```

RFC 0006 also says schema-v3 fields and fixtures become public after P4-A1 is
implemented. Its later P4-A2, P4-B1, and P4-B2 gates remain independently
authorized and unimplemented, while their commit plans suggest YAML, table, and
array modality work happens later.

RFC 0007 requires a hard predecessor audit: if the merged P4-A1 schema differs
from RFC 0006, Phase 5 stops and the RFC is amended before image models ship.
RFC 0008 assigns Phase 6 source/PDF to schema v5 and includes the full RFC 0006
v3 closed union as a predecessor. Therefore P6-C0 cannot be implemented
uniquely from current `main`: implementers can follow either the accepted RFC
0006 union or the actually implemented JSON-only surface, and those are not the
same contract.

The repository remains unreleased, which gives maintainers room to correct the
pre-release schema implementation. It does not make closed-union drift harmless:
once a writer, reader, migration fixture, downstream schema, or release treats a
closed union as a predecessor, extending that same schema version creates
ambiguous compatibility evidence.

## Approved decisions

| ID | Accepted decision | Alternative not selected |
| --- | --- | --- |
| SP1 | Recognize the schema-v3 predecessor mismatch as blocking for P5-A1, P6-C0, P7-A1, and later video schema work until P4-C1 or an explicitly accepted successor resolution merges. | Let downstream schemas choose whichever v3 definition is convenient. |
| SP2 | Choose Option A: treat the missing YAML/table/array schema-v3 contracts as a Phase 4 code defect and define correction gate P4-C1 before schema v4. | Treat current JSON-only code as the complete v3 contract without amending accepted RFCs. |
| SP3 | Keep the accepted global allocation: v3 structured data, v4 image, v5 source/PDF, v6 audio, and a later video successor. | Renumber accepted image/source/PDF/audio allocations because P4-A1 shipped an incomplete v3 surface. |
| SP4 | State that a closed union may not be extended after it has shipped as public release evidence or after a successor has depended on it; before release, P4-C1 may correct the incomplete v3 implementation to match accepted RFC 0006. | Allow same-version closed-union additions whenever a later gate wants them. |
| SP5 | Require downstream predecessor fixtures to prove the corrected v3 union before schema-v4, schema-v5, or schema-v6 writer fixtures are accepted. | Use design acceptance alone as predecessor compatibility evidence. |
| SP6 | Require a P6-C0 contract amendment before implementation to close the source lexical, PDF binary, coordinate, digest, identifier, problem, fact, and `compare()` behavior gaps below. | Let P6-C0 implementers infer missing public contract details from private code. |

## Alternatives

### A. Phase 4 correction gate before v4

Option A treats RFC 0006 as the correct accepted contract and current P4-A1
code as incomplete. The correction gate, P4-C1, adds the missing public
schema-v3 model, serializer, reader, migration, and fixture surface for
`YamlCompareSpec`, `TableCompareSpec`, `ArrayCompareSpec`, `TableChange`, and
`ArrayChange`. P4-C1 does not implement YAML, table, or array comparators; it
only makes the v3 closed union match the accepted contract so later gates have
one predecessor.

This accepted option preserves already accepted schema
allocations and keeps RFC 0006's structured-data contract intact. The
compatibility cost is still real: v3 fixtures already on `main` must be
expanded and revalidated before any v4/v5/v6 fixtures depend on them. The
project is unreleased, so this is a pre-release defect correction rather than a
public breaking change.

### B. Redefine v3 as JSON-only

Option B amends RFC 0006 to say schema v3 contains only `JsonCompareSpec` and
`StructuredChange`; YAML, table, and array contracts would move to future
global schema successors. This fits current code but weakens an accepted RFC
after implementation and forces maintainers to decide where those structured
modalities live. They could be assigned after audio/video, or grouped into a
new structured-data successor, but either choice changes the predecessor graph
for RFC 0007, RFC 0008, and RFC 0009.

Because the project is unreleased, option B is technically possible. It is not
selected unless humans later decide the accepted RFC 0006 contract was too broad.
It requires explicit migration notes, updated RFC 0006 status text, amended
Phase 5/6/7 predecessor language, and compatibility tests proving that old
pre-release v3 JSON fixtures remain valid while the removed YAML/table/array
names are not accepted as v3.

### C. Add a secondary schema-extension mechanism

Option C keeps numeric schema v3 as JSON-only but adds a separate structured
contract revision or capability-extension namespace for YAML, table, and array.
This avoids renumbering but creates two version axes. It also weakens the
closed-union discipline used by RFC 0006 through RFC 0009: a reader would need
both `schema_version` and extension membership to know what built-in spec and
change names are legal.

This option is coherent only if the project deliberately moves away from
schema-versioned closed unions. It is not selected for the current
pre-release codebase.

## P4-C1 correction gate

Because Option A is accepted, P4-C1 is the required correction gate before any schema
v4/v5/v6 implementation gate:

1. `fix(core): complete schema-v3 structured contract models`
2. `fix(core): complete schema-v3 reader writer and migration validation`
3. `test(core): add schema-v3 YAML table array contract fixtures`
4. `docs(rfc): record schema-v3 predecessor correction evidence`

Gate: coordinator-dispatched from updated `main` after this RFC merges; no YAML, table, or array
comparator behavior is implemented; no CLI route, detector, plugin SDK,
artifact, or renderer feature is added; `git diff --check`, formatting, lint,
strict type checking, complete tests, schema-v1/v2/v3 compatibility fixtures,
unknown-kind rejection, and public-export checks pass. P5-A1, P6-C0, P7-A1, and
later video schema gates must wait for P4-C1 or for an accepted alternative in
this RFC.

## Accepted P4-C1 pre-implementation clarifications

These P4C1 IDs were approved on 2026-09-10. They clarify P4-C1's schema-v3
reader and fixture contract without starting implementation.

### P4C1-1: table encoding field

Recommended choice: add an explicit `encoding` field to `TableCompareSpec`
immediately after `dialect`:

```python
class TableCompareSpec:
    kind: Literal["table"] = "table"
    dialect: Literal["csv", "tsv"]
    encoding: Literal["utf-8", "utf-8-sig"] = "utf-8"
    header: Literal["first_row", "none"] = "first_row"
```

Wire shape and ordering: canonical schema-v3 JSON writes `encoding` after
`dialect` and before `header`, even when the value is the default `utf-8`.
`utf-8` means strict UTF-8 with no implicit BOM handling. `utf-8-sig` permits
one leading UTF-8 BOM at the start of an input and strips it as a recorded table
decoding transformation; all other bytes still decode with strict UTF-8.

Rejected alternative: keep encoding only in prose, infer it from bytes, accept
locale encodings, or silently strip a BOM while serializing no selected policy.

Compatibility impact: no released schema-v3 table fixtures exist, so this is a
pre-release visible default rather than a migration. P4-C1 canonical fixtures
must include `encoding`. Existing v1/v2/v3 fixture bytes remain stable; new
schema-v3 table specs always write the default `utf-8` policy canonically.

### P4C1-2: table fact discriminators and row-cell wire shape

Recommended choice: add explicit `kind` discriminators to table fact variants
and serialize row cells as ordered pair arrays, not JSON objects:

```python
class TableRowFact:
    kind: Literal["table_row"] = "table_row"
    cells: tuple[tuple[str, ScalarFact], ...]

class ColumnSchemaFact:
    kind: Literal["table_column_schema"] = "table_column_schema"
    name: str
    dtype: Literal["string", "integer", "float64", "boolean"]
    missing_token_count: int
    numeric: NumericPolicy | None

class ColumnOrderFact:
    kind: Literal["table_column_order"] = "table_column_order"
    names: tuple[str, ...]
```

Wire shape and ordering: canonical JSON field order is `kind`, then the payload
fields shown above. `TableRowFact.cells` is serialized as
`[["column_name", {"kind": "string", "value": "..."}], ...]` in aligned column
order. Validation rejects object-map cells, duplicate column names, cells whose
scalar kind violates the declared column schema, and row facts that omit or add
columns relative to the aligned column set.

Rejected alternative: infer table fact type from payload keys or serialize
`cells` as an object keyed by column name.

Compatibility impact: discriminators keep the schema-v3 closed union
unambiguous for detached readers. Pair arrays preserve canonical order and make
duplicate-name rejection explicit before any schema-v4/v5/v6 successor consumes
the fixture corpus.

### P4C1-3: array error number type

Recommended choice: replace the undefined `MetricNumber` reference in
`ArrayChange.absolute_error` and `ArrayChange.relative_error` with the existing
`NumericValue` union used by `Metric.value`, `Metric.threshold`, and
`PolicyEvaluation.observed`.

Wire shape and ordering: the `ArrayChange` field names stay unchanged.
`absolute_error`, when non-null, must be a finite `NumericValue` greater than or
equal to zero. `relative_error`, when non-null, must be either a finite
`NumericValue` greater than or equal to zero or `positive_infinity` for a
non-zero finite difference with a zero reference. NaN, negative infinity, and
positive infinity for `absolute_error` are validation errors. For non-numeric
or non-finite input pairs, both error fields are null. The fields are always
present in canonical JSON, and undefined errors are serialized as JSON null
following the current schema serializer's nullable-field convention. Canonical
field order remains
`kind`, `operation`, `index`, `before_digest`, `after_digest`,
`absolute_error`, `relative_error`.

Rejected alternative: define a second number union only for array changes or
serialize errors as bare JSON numbers.

Compatibility impact: reusing `NumericValue` avoids another public numeric
contract and keeps renderer, policy, metric, and schema-v3 fixture parsing on
one numeric representation.

### P4C1-4: completed contract fixtures without comparator routes

Recommended choice: P4-C1 remains contract-only. Completed canonical
YAML/table/array fixtures are reader/writer fixtures constructed directly as
validated schema-v3 outcomes; they do not imply a runnable `compare()` route,
CLI route, detector, plugin handle, or backend. Their provenance uses the
frozen future built-in comparator IDs rather than fixture-only IDs. This follows
the current built-in convention: comparator IDs are non-namespaced
`text`/`binary`/`json`-style identifiers, while algorithm IDs may use dotted
stable names.

| Modality | `comparator_id` | `algorithm_id` |
| --- | --- | --- |
| YAML | `yaml` | `yaml.structural.tree.v1` |
| Table | `table` | `table.delimited.align.v1` |
| Array | `array` | `array.position.numeric.v1` |

Wire shape and ordering: canonical fixtures contain completed `DiffResult`
records with schema version 3, the matching explicit spec kind, the matching
fact/change variants, `comparator_version="1"`, no detector provenance, and no
plugin provider. Each fixture also contains exactly one selected
`CapabilityAttemptV2` in `ExecutionRecordV2.attempts`; its `capability_id`
matches `provenance.comparator_id`, its `capability_version` matches
`provenance.comparator_version`, and its provider/backend fields are null.
`_validate_v3_result` accepts these reserved built-in ID pairs only when the
result's spec, facts, changes, metric names, resource records, transformations,
problem absence, and selected attempt match the corresponding schema-v3
contract. Capability resolution must still reject these IDs as registered
runtime comparators during P4-C1.

Rejected alternative: reuse `json` provenance, omit comparator/algorithm IDs,
allow arbitrary or `contract_fixture` IDs, or add YAML/table/array comparator
implementations inside P4-C1.

Compatibility impact: this gives canonical byte fixtures real future built-in
provenance without widening runtime behavior. Later P4-B1/P4-B2 comparator work
must use these same built-in IDs when the registry actually exposes executable
YAML/table/array capabilities.

### P4C1-5: detached array-change validation context

Recommended choice: do not add shape or dtype fields to every `ArrayChange`.
A detached `ArrayChange` reader validates the operation/field matrix, digest
syntax, `NumericValue` error shapes, and that every `index` component is a
non-negative integer. Because `ArrayCompareSpec`, `DiffResult`, and provenance
do not carry array shape or dtype today, neither the detached reader nor the
schema-v3 result reader can prove full-rank, in-bounds, row-major order, or
dtype-specific error consistency in P4-C1. Those checks are future
producer/comparator invariants deferred to P4-B2.

Wire shape and ordering: `ArrayChange` keeps the RFC 0006 fields exactly, with
`index` serialized as an ordered JSON array of non-negative integers for
`element_replace`. The schema-v3 canonical writer always includes `index`;
`shape_replace` and `dtype_replace` serialize it as JSON null. Exact-key reader
rejects an omitted `index` key, duplicate keys, and extra shape/dtype context
keys on `ArrayChange`. P4-C1 does not add `before_shape`, `after_shape`,
`dtype`, or any `ArraySource` payload to `ArrayChange`. `ArraySource` remains a
P4-B2 source-acquisition/API concern and does not enter P4-C1's serialized
schema-v3 correction.

Rejected alternative: duplicate `shape` and `dtype` context into every
`ArrayChange` so detached readers can prove full-rank and in-bounds constraints
without the enclosing result.

Compatibility impact: the compact accepted `ArrayChange` shape is preserved,
while validators distinguish detached syntactic validation from contextual
producer validation. P4-C1 fixtures must test non-negative index syntax and the
operation/field matrix; producer tests for full-rank, bounds, row-major order,
and dtype/error consistency are deferred to P4-B2.

## P6-C0 contract amendment

P6-C0 remains conditional on P4-C1 and predecessor compatibility fixtures. The
following public contract details are accepted as Phase 6 contract decisions,
not implementation authority.

| ID | Accepted decision | Alternative not selected |
| --- | --- | --- |
| P6C0-1 | Represent source `lexical_text` differences with a source-specific change kind that embeds RFC 0002 text ranges and also records source coordinate context; do not reuse bare `TextHunk` as a source-code change. | Make lexical source output indistinguishable from plain text output. |
| P6C0-2 | Represent PDF binary differences with a PDF-specific binary-span change discriminator that records PDF document identity plus zero-based half-open byte ranges; do not reuse bare `BinarySpan` without a PDF discriminator. | Let PDF binary view produce generic binary changes that renderers cannot distinguish from ordinary binary comparison. |
| P6C0-3 | Define coordinate bases and grammars normatively: bytes are zero-based half-open offsets; source line/column facts state encoding and whether columns are code-point or byte based; PDF page numbers, object references, stream ranges, and rendered pixel rectangles each have one grammar; rendered pixel rectangles are zero-based half-open in the explicitly declared raster space. | Leave coordinate base and grammar to each backend. |
| P6C0-4 | Define render bounds in the schema contract before any renderer backend: maximum pages, rendered pages, pixels per page, decoded bytes, temp bytes, backend seconds, worker output bytes, peak RSS, concurrent workers, and spawned process count all have finite accounting rules. | Put render limits only in backend documentation. |
| P6C0-5 | Define exact digest framing with domain strings, canonical byte framing, hash algorithm, and normative test vectors for source facts, PDF facts, rendered-page facts, and change payloads. | Reuse informal prose references to RFC 0006 digests without vectors. |
| P6C0-6 | Reserve stable lowercase ASCII IDs for summary keys, resource counters, transformation IDs, comparator IDs, algorithm IDs, metric names, and problem codes before any source/PDF writer ships. | Let implementations mint IDs opportunistically. |
| P6C0-7 | Define encrypted PDF behavior exactly: `views=("binary",)` ignores encryption and compares bytes; any selected nonbinary view on either encrypted input produces a top-level `failed` outcome at `stage="decoding"` with registry ID `schema-v5/pdf_encrypted`, serialized code `pdf_encrypted`, and no `DiffResult`. | Collapse encryption into generic decode failure or make encryption policy-dependent. |
| P6C0-8 | Define worker problem details for timeout, resource exhaustion, crash, protocol violation, invalid output, stderr overflow, temp overflow, decoded-output overflow, RSS overflow, and spawn-limit overflow; each has a stable status and safe detail shape. | Return backend-specific strings as problem details. |
| P6C0-9 | Define fact presence invariants: every selected successful view emits its required facts, metrics, summaries, resources, and transformations; every unselected view is absent or explicitly null as specified; failed or unavailable views do not fabricate empty facts. | Permit partial facts without a schema-level invariant. |
| P6C0-10 | Keep P6-C0 models/serialization only: public `compare()` and CLI behavior for source/PDF remain unavailable until P6-S1 or P6-P1a. P6-C0 fixtures may construct unavailable outcomes directly for reader/writer validation but must not expose a runnable source/PDF comparator route. | Add `compare()` behavior that returns unavailable for source/PDF during P6-C0. |

### Accepted schema-v5 public shapes for future P6-C0

These shapes are accepted for the future P6-C0 implementation review, but they
do not start code by themselves. P6-C0 has recorded conditional authorization,
and the coordinator may dispatch it only after RFC 0010, P4-C1,
P5-A1/schema-v4, and their compatibility fixtures have all merged to `main`.
This does not imply automatic start.

Source lexical changes use the existing schema-v5 closed-union member
`kind="source_code_change"` with lexical discriminator
`change_variant="lexical_text"`. This does not add a new built-in change kind.
The stable field order is:

```text
kind
change_variant
language
relation
coordinate_encoding
column_unit
before_range
after_range
lexical_text
payload_digest
```

`language` is the explicit spec language. `relation` is `lexical_text`.
`coordinate_encoding` is `utf-8`. `column_unit` is exactly `unicode_scalar` or
`utf8_byte`; the default serialized value is `unicode_scalar`. `before_range`
and `after_range` are nullable range objects with `start_byte`, `end_byte`,
`start_line`, `start_column`, `end_line`, `end_column`, and `column_unit`.
Byte offsets are zero-based half-open offsets in the decoded byte sequence.
Lines are one-based. Columns use the range object's `column_unit`.
When both outer `column_unit` and a non-null range `column_unit` are present,
they must be equal; readers reject mismatches. Null ranges have no nested
`column_unit`.
`lexical_text` is either null or an object with `before_lines`, `after_lines`,
and `line_ending`. In `detail_mode="facts"`, these line arrays may contain only
bounded UTF-8 text already permitted by the source fact limit. In
`detail_mode="digest_only"`, `lexical_text` is null and only coordinates,
counts, discriminators, and digests remain.

PDF binary changes use the existing schema-v5 closed-union member
`kind="pdf_change"` with `view="binary"` and
`binary_variant="byte_range"`. The stable field order is:

```text
kind
view
binary_variant
ranges
payload_digest
```

`view` is exactly `binary`. Each range has `side`, `start_byte`, and
`end_byte`; `side` is `before` or `after`. Byte offsets are zero-based
half-open offsets over original PDF bytes before parsing, decryption, repair,
or decompression. This is distinct from generic `BinarySpan` even when the same
byte ranges are reported.

Coordinate grammars are:

| Coordinate | Grammar | Base |
| --- | --- | --- |
| Source bytes | `source-byte-range(start,end)` | zero-based half-open decoded UTF-8 bytes |
| Source text | `source-text-range(line,column,line,column,column_unit)` | one-based lines and columns |
| PDF bytes | `pdf-byte-range(start,end)` | zero-based half-open original bytes |
| PDF object | `pdf-object(obj,generation)` | PDF object and generation numbers as stored |
| PDF page | `pdf-page(number)` | one-based logical page number after document catalog resolution |
| PDF stream | `pdf-stream(obj,generation,start,end)` | object identity plus zero-based half-open decoded stream bytes |
| Rendered pixels | `pdf-raster-rect(page,x,y,width,height,dpi,colorspace)` | zero-based raster pixels in declared rendered page space |

Canonical view ordering is `binary`, `extracted_text`, `objects_metadata`,
`rendered_pages`. Within a view, facts and changes sort by before coordinate,
after coordinate, discriminator, and `payload_digest`; absent coordinates sort
after present coordinates.

### Digest framing and vectors

Schema-v5 preserves RFC 0008's accepted evidence-digest framing. Changing this
frame would require a separate human decision and is not selected here.
The frame is:

```text
SHA256(UTF8("platydiff/v5/" + domain) || 0x00 || U64BE(payload_length) || payload)
```

`payload` is a tagged byte sequence:

```text
U64BE(field_count)
for each field in stable field order:
  U64BE(tag_length) || UTF8(tag) || U64BE(value_length) || value_bytes
```

`value_bytes` for strings are strict UTF-8. `value_bytes` for integers are the
shortest unsigned base-10 ASCII representation. Booleans are `true` or `false`.
Null is a zero-length value with tag suffix `?null`, so null and empty string do
not share an encoding. The normative non-empty vectors are:

| Domain | Tagged fields | Payload hex | SHA-256 |
| --- | --- | --- |
| `source/decoded_text_line` | `language=python`, `line=1`, `terminator=lf`, `text=pass` | `000000000000000400000000000000086c616e67756167650000000000000006707974686f6e00000000000000046c696e65000000000000000131000000000000000a7465726d696e61746f7200000000000000026c66000000000000000474657874000000000000000470617373` | `e700a16bc1f2b8703cbaaae345390c507d031261c13ccf31ece00cbac9e11b6e` |
| `source/change_payload` | `kind=source_code_change`, `range_variant=lexical_text`, `before_start_byte=0`, `before_end_byte=4` | `000000000000000400000000000000046b696e640000000000000012736f757263655f636f64655f6368616e6765000000000000000d72616e67655f76617269616e74000000000000000c6c65786963616c5f7465787400000000000000116265666f72655f73746172745f62797465000000000000000130000000000000000f6265666f72655f656e645f62797465000000000000000134` | `07127b46e29dd63562d20877c7d3d52872b2a943a209ad71436a937f5bfaac3d` |
| `pdf/binary/span` | `kind=pdf_change`, `view=binary`, `span_variant=byte_range`, `side=before`, `start_byte=0`, `end_byte=4` | `000000000000000600000000000000046b696e64000000000000000a7064665f6368616e6765000000000000000476696577000000000000000662696e617279000000000000000c7370616e5f76617269616e74000000000000000a627974655f72616e676500000000000000047369646500000000000000066265666f7265000000000000000a73746172745f627974650000000000000001300000000000000008656e645f62797465000000000000000134` | `a95731a041d328d0d9f350ac4c9a45b49761e96103efa7b2fdf544f3411b91f9` |
| `pdf/render/page` | `page=1`, `width_px=2`, `height_px=2`, `dpi=72`, `colorspace=srgb` | `0000000000000005000000000000000470616765000000000000000131000000000000000877696474685f707800000000000000013200000000000000096865696768745f7078000000000000000132000000000000000364706900000000000000023732000000000000000a636f6c6f727370616365000000000000000473726762` | `b9f9fef8b2493372b76f5ae8abf4166aae2a37e9ec8f3134a6b19c838ff1e81f` |

### Stable IDs, policies, and counters

P6-C0 must preserve these accepted RFC 0008 names exactly:

- source relation IDs: `lexical_text`, `syntax_tree`; `semantic` is reserved
  and unavailable;
- PDF view IDs: `pdf.binary`, `pdf.extracted_text`,
  `pdf.objects_metadata`, `pdf.rendered_pages`;
- source metric IDs: `source.nodes_compared`, `source.nodes_changed`,
  `source.tokens_changed`, `source.moves`, `source.parser_errors`,
  `source.ignored_trivia_items`;
- PDF metric IDs: `pdf.binary.changed_bytes`, `pdf.text.changed_runs`,
  `pdf.text.compared_runs`, `pdf.objects.changed_entries`,
  `pdf.objects.compared_entries`, `pdf.render.changed_pixels`,
  `pdf.render.changed_pages`, `pdf.render.compared_pages`;
- accepted evaluation IDs: `source.syntax_tree_equality`,
  `source.lexical_text_equality`, `pdf.extracted_text_equality`,
  `pdf.rendered_page_equality`;
- digest domains: `source/decoded_text_line`, `source/token`, `source/node`,
  `source/subtree`, `pdf/binary/span`, `pdf/text/run`,
  `pdf/object/entry`, `pdf/metadata/entry`, `pdf/render/page`,
  `pdf/render/region`;
- source resource limit fields: `max_input_bytes`, `max_decoded_chars`,
  `max_fact_text_bytes`, `max_tokens`, `max_nodes`, `max_depth`,
  `max_parser_errors`, `max_compare_work`, `max_change_items`,
  `max_change_payload_bytes`;
- PDF base and worker resource fields: `max_input_bytes`,
  `max_fact_text_bytes`, `max_fact_value_bytes`, `max_compare_work`,
  `max_change_items`, `max_change_payload_bytes`,
  `max_total_backend_seconds`, `max_total_stdout_stderr_bytes`,
  `max_total_temp_bytes`, `max_total_decoded_bytes`,
  `max_total_worker_output_bytes`, `max_peak_worker_rss_bytes`,
  `max_peak_concurrent_worker_processes`,
  `max_total_worker_processes_spawned`;
- PDF per-view resource fields: `max_pages`, `max_stream_bytes`,
  `max_decoded_stream_bytes`, `max_text_runs`,
  `max_render_pixels_per_page`, `max_rendered_pages`,
  `max_view_backend_seconds`, `max_view_stdout_stderr_bytes`,
  `max_view_temp_bytes`, `max_view_decoded_bytes`,
  `max_view_worker_output_bytes`, `max_view_peak_worker_rss_bytes`,
  `max_view_peak_concurrent_worker_processes`,
  `max_view_total_worker_processes_spawned`.

RFC 0010 accepts only these missing stable IDs beyond RFC 0008:

- implementation comparator IDs: `builtin.source.lexical_text.v1`,
  `builtin.source.syntax_tree.v1`, `builtin.pdf.binary.v1`,
  `builtin.pdf.extracted_text.v1`, `builtin.pdf.objects_metadata.v1`,
  `builtin.pdf.rendered_pages.v1`;
- algorithm IDs: `source.lexical_text.myers.v1`,
  `source.syntax_tree.digest_align.v1`, `pdf.binary.byte_scan.v1`,
  `pdf.text.run_lcs.v1`, `pdf.objects.key_path_align.v1`,
  `pdf.render.pixel_exact.v1`, `digest.tagged_payload_sha256.v1`;
- transformation IDs: `source.decode_utf8`, `source.normalize_newlines`,
  `source.lexical_tokenize_lines`, `pdf.read_original_bytes`,
  `pdf.parse_xref`, `pdf.extract_text_runs`, `pdf.enumerate_objects`,
  `pdf.render_page`;
- missing PDF evaluation IDs: `pdf.binary_equality`,
  `pdf.objects_metadata_equality`;
- summary keys: `changed_items`, `added_items`, `removed_items`,
  `modified_items`, `moved_items`, `truncated`, `selected_views`.

### Problem registry

New schema-v5 problem codes are registered under a scoped registry key
`schema-v5/<code>` while the serialized `problem.code` remains the short stable
code. P6-C0 reserves:

| Registry ID | Serialized status/code | Stage | Detail keys |
| --- | --- | --- | --- |
| `schema-v5/pdf_encrypted` | `failed/pdf_encrypted` | `decoding` | `input_side`, `view`, `encryption_detected=true` |
| `schema-v5/pdf_worker_timeout` | `failed/pdf_worker_timeout` | `decoding` | `view`, `limit_seconds`, `elapsed_seconds` |
| `schema-v5/pdf_worker_resource_exhausted` | `failed/pdf_worker_resource_exhausted` | `decoding` | `view`, `resource`, `limit`, `actual` |
| `schema-v5/pdf_worker_crash` | `failed/pdf_worker_crash` | `decoding` | `view`, `exit_status` |
| `schema-v5/pdf_worker_protocol_violation` | `failed/pdf_worker_protocol_violation` | `decoding` | `view`, `message_kind` |
| `schema-v5/pdf_worker_invalid_output` | `failed/pdf_worker_invalid_output` | `decoding` | `view`, `field` |

`pdf_encrypted` is not used for pure binary view. Any selected nonbinary view on
either encrypted input fails the whole all-or-nothing PDF invocation with no
`DiffResult` and no fallback to binary.

Problem detail value types are closed: `input_side` is `before` or `after`;
`view` is one of the canonical PDF view names; `encryption_detected` is boolean
`true`; `limit_seconds`, `elapsed_seconds`, `limit`, and `actual` are
non-negative JSON numbers; `resource`, `message_kind`, and `field` are stable
lowercase ASCII identifiers; `exit_status` is a signed integer or null when the
process was terminated without an exit status. Invalid wire coordinates,
unknown problem registry IDs, and malformed tagged payloads raise
`SerializationError`; they do not fabricate runtime failed outcomes.

[RFC 0014](0014-phase6-source-pdf-contract-closure-amendment.md) is an
Accepted contract-only amendment that closes and supersedes these problem
details without authorizing implementation.

### Fact presence and ordering

Completed source/PDF schema-v5 outcomes must emit all required spec, fact,
metric, summary, resource, transformation, comparator, algorithm, and digest
fields for each selected relation or view. Unselected optional views are
serialized as `null` only where RFC 0008 explicitly defines a nullable option
object; otherwise they are absent. Failed or unavailable outcomes contain no
`DiffResult`, and partial view facts appear only inside execution attempts when
the execution model has such an attempt field.

Reader validation rejects selected view facts in a noncanonical order, duplicate
summary or metric IDs, unknown schema-v5 problem registry IDs, unscoped new
problem codes, missing required counters, digest/domain mismatches, noncanonical
coordinates, and any P6-C0 payload that exposes public source/PDF `compare()` or
CLI behavior.

## Migration and compatibility tests

Any accepted resolution must add tests for:

- exact v1/v2/v3 reader and writer compatibility, including unknown schema and
  unknown built-in kind rejection;
- canonical round trips for every accepted schema-v3 built-in spec and change
  name, even when comparator behavior is still gated;
- migration from v1/v2 to corrected v3 without changing legacy outcome meaning;
- predecessor fixture reuse by v4/v5/v6 gates without rewriting v3 bytes after
  those successor fixtures are accepted;
- P6-C0 source/PDF schema fixtures covering unavailable and failed outcomes,
  selected and unselected views, resource accounting, transformations,
  summaries, metrics, problem details, digest vectors, and coordinate examples;
- proof that P6-C0 does not add public `compare()` or CLI source/PDF behavior.

Options B and C were not selected. If a future RFC supersedes Option A, its
migration tests must also prove that removed or relocated YAML/table/array v3
names are rejected with a stable problem and that successor allocations are
documented before code.

## Accepted resolution and remaining authorization

Human reviewers accepted:

1. RFC 0006 remains the desired schema-v3 contract.
2. P4-C1 must correct current code to match RFC 0006 before schema v4.
3. Pre-release schema-v3 fixtures may be expanded only before any successor
   depends on them and before release; after P4-C1 predecessor fixtures are
   consumed by v4/v5/v6, v3 closed-union membership is frozen.
4. The global allocations v4 image, v5 source/PDF, v6 audio, and later video
   successor remain correct.
5. P6C0-1 through P6C0-10 are accepted contract decisions before P6-C0
   implementation starts.

RFC acceptance itself does not start code. Conditional human authorization has
been recorded; coordinator dispatch may occur only after the stated merge
gates. P4-C1 implementation still requires coordinator dispatch after this RFC
is merged. P5-A1, P6-C0, P7-A1, and later video schema implementation remain
blocked until their actual predecessor merges and compatibility fixtures are
present on `main`.
