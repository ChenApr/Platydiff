# RFC 0010: Schema Predecessor and Phase 6 Contract Amendment

[Chinese documentation](0010-schema-predecessor-and-phase6-contract-amendment_zh.md)

- Status: Accepted
- Date: 2026-09-10
- Accepted: 2026-09-10
- Approved decisions: SP1-SP6; Option A/P4-C1; P6C0-1-P6C0-10
- Approved P4-C1 clarifications: P4C1-1-P4C1-5
- P4-C1 clarification approval date: 2026-09-10
- Proposed P6-C0 closure amendment: P6C0A-1-P6C0A-2; not accepted
- Owners: Platydiff maintainers
- Implementation dispatch: conditional human authorization recorded; coordinator
  dispatch only after RFC 0010 merges and the stated merge and clarification
  gates pass

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
closed-union shape gaps. The proposed P6C0A-1 and P6C0A-2 amendments below are
not accepted, do not alter P6C0-1 through P6C0-10, and do not authorize source
or PDF implementation.

The accepted decision is to treat the missing YAML, table, and array
schema-v3 contract surface on `main` as a Phase 4 code defect, not as proof that
the accepted RFC 0006 contract was wrong. A correction gate must land before
schema v4 image, schema v5 source/PDF, schema v6 audio, or any later video
successor can use v3 as a stable predecessor. P4-C1 code may start only after
this RFC is merged to `main` and the coordinator dispatches it. P5-A1, P6-C0,
P7-A1, and later video schema work remain conditional on the actual predecessor
merges and compatibility fixtures.

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
code. The accepted baseline reserves `schema-v5/pdf_encrypted` and the PDF
worker problem families required by P6C0-8: timeout, stderr overflow, temp
overflow, decoded-output overflow, RSS overflow, concurrency overflow, spawn
overflow, crash, protocol violation, and invalid output. The exact source/PDF
problem rows, inherited problem mappings, canonical problem field order, safe
message requirement, rendered-pages worker stage, and detail key order remain
Proposed in P6C0A-1 below.

`pdf_encrypted` is not used for pure binary view. Any selected nonbinary view on
either encrypted input fails the whole all-or-nothing PDF invocation with no
`DiffResult` and no fallback to binary. Invalid wire coordinates, unknown
problem registry IDs, and malformed tagged payloads raise `SerializationError`;
they do not fabricate runtime failed outcomes.

### Proposed P6-C0 closure amendment

The following P6C0A decisions are Proposed, not Accepted. They are draft
closure criteria for P6-C0 only. They preserve P6-C0 as contract-only work:
no source/PDF comparator, CLI route, backend worker, dependency, SDK, artifact,
automatic detection, or UI implementation may start from these proposed
decisions. P6-C0 still waits for RFC 0010, P4-C1, P5-A1/schema-v4, and
compatibility fixtures to merge to `main`, followed by explicit coordinator
dispatch.

#### P6C0A-1: problem registry closure

If accepted, schema-v5 source/PDF problems preserve the existing
`ExecutionProblem` and `CapabilityProblem` wire shape and canonical field order:
`code`, `status_code`, `stage`, `message`, `details`, `retryable`. `message`
is a bounded safe human message. The outer `CompareOutcome.kind` and problem
class determine `failed` versus `unavailable`; schema-v5 does not add a nested
problem `outcome` field. New scoped registry keys use `schema-v5/<code>`, while
serialized `code` remains the short stable code.

Canonical JSON emits `details` keys in the order listed below. Readers reject
missing keys, extra keys, wrong types, and noncanonical key order in canonical
fixtures.

| Registry ID | Problem class and outer outcome | Status code | Stage | Retryable | Detail keys |
| --- | --- | ---: | --- | --- | --- |
| inherited `invalid_spec` | `ExecutionProblem` / `failed` | `400` | `validating` | `false` | `spec_field`, `reason_code` |
| inherited `source_type_unsupported` | `ExecutionProblem` / `failed` | `415` | `resolving` | `false` | `source_kind`, `spec_kind`, `reason_code` |
| inherited `capability_unavailable` | `CapabilityProblem` / `unavailable` | `501` | `resolving` | `true` | `capability_id`, `relation_or_view`, `reason_code` |
| inherited `backend_unavailable` | `CapabilityProblem` / `unavailable` | `503` | `resolving` | `true` | `backend_role`, `backend_id`, `relation_or_view`, `reason_code` |
| inherited `resource_limit_exceeded` | `ExecutionProblem` / `failed` | `413` | action stage | `false` | `resource`, `limit`, `actual`, `limit_scope`, `relation_or_view` |
| inherited `compare_resource_limit` | `ExecutionProblem` / `failed` | `413` | `comparing` | `false` | `resource`, `limit`, `actual`, `relation_or_view` |
| `schema-v5/alignment_failed` | `ExecutionProblem` / `failed` | `409` | `aligning` | `false` | `relation_or_view`, `reason_code`, `before_coordinate`, `after_coordinate` |
| inherited `decode_error` | `ExecutionProblem` / `failed` | `422` | `decoding` | `false` | `input_side`, `relation_or_view`, `message_code`, `line`, `column` |
| `schema-v5/source_backend_unavailable` | `CapabilityProblem` / `unavailable` | `503` | `resolving` | `true` | `source_relation`, `language`, `backend_id`, `reason_code` |
| `schema-v5/source_compare_timeout` | `ExecutionProblem` / `failed` | `504` | `comparing` | `false` | `source_relation`, `limit_seconds`, `elapsed_seconds` |
| `schema-v5/pdf_encrypted` | `ExecutionProblem` / `failed` | `422` | `decoding` | `false` | `input_side`, `view`, `encryption_detected` |
| `schema-v5/pdf_backend_unavailable` | `CapabilityProblem` / `unavailable` | `503` | `resolving` | `true` | `view`, `backend_role`, `backend_id`, `reason_code` |
| `schema-v5/pdf_worker_timeout` | `ExecutionProblem` / `failed` | `504` | view worker stage | `false` | `view`, `limit_seconds`, `elapsed_seconds` |
| `schema-v5/pdf_worker_stderr_overflow` | `ExecutionProblem` / `failed` | `502` | view worker stage | `false` | `view`, `stream`, `limit_bytes`, `actual_bytes` |
| `schema-v5/pdf_worker_temp_overflow` | `ExecutionProblem` / `failed` | `507` | view worker stage | `false` | `view`, `limit_bytes`, `actual_bytes` |
| `schema-v5/pdf_worker_decoded_output_overflow` | `ExecutionProblem` / `failed` | `413` | view worker stage | `false` | `view`, `resource`, `limit_bytes`, `actual_bytes` |
| `schema-v5/pdf_worker_rss_overflow` | `ExecutionProblem` / `failed` | `507` | view worker stage | `false` | `view`, `limit_bytes`, `actual_bytes` |
| `schema-v5/pdf_worker_concurrency_overflow` | `CapabilityProblem` / `unavailable` | `503` | `resolving` | `true` | `view`, `limit_processes`, `actual_processes` |
| `schema-v5/pdf_worker_spawn_overflow` | `ExecutionProblem` / `failed` | `507` | view worker stage | `false` | `view`, `limit_processes`, `actual_processes` |
| `schema-v5/pdf_worker_crash` | `ExecutionProblem` / `failed` | `502` | view worker stage | `false` | `view`, `exit_status`, `signal` |
| `schema-v5/pdf_worker_protocol_violation` | `ExecutionProblem` / `failed` | `502` | view worker stage | `false` | `view`, `message_kind` |
| `schema-v5/pdf_worker_invalid_output` | `ExecutionProblem` / `failed` | `502` | view worker stage | `false` | `view`, `field` |

For rows with action stage, `stage` is selected by the exceeded resource:
source or PDF input bytes fail at `sourcing`; decoded source chars, source
fact text bytes, parser node counts, PDF decoded streams, PDF text runs, PDF
object entries, and nonrender worker output fail at `decoding`; rendered page
counts, rendered pixels, rendered-page worker output, rendered-page temp bytes,
and rendered-page RSS fail at `rendering`. For rows with view worker stage,
`stage` is `rendering` when `view="rendered_pages"` and `decoding` for
`extracted_text` and `objects_metadata`; the pure `binary` view has no worker
stage.

Closed detail value types are:

- `source_relation`: `lexical_text` or `syntax_tree`;
- `view`: `binary`, `extracted_text`, `objects_metadata`, or
  `rendered_pages`;
- `relation_or_view`: one source relation or PDF view name;
- `input_side`: `before` or `after`;
- `source_kind`: `path`, `bytes`, or `text`;
- `spec_kind`: the stable spec discriminator;
- `backend_role`: `parser`, `text_extractor`, `object_reader`, or `renderer`;
- `language`, `backend_id`, `capability_id`, `reason_code`, `message_code`,
  `resource`, `stream`, and `message_kind`: stable lowercase ASCII identifiers
  or null only where the table names a nullable field;
- `line`, `column`, `limit`, `actual`, `limit_bytes`, `actual_bytes`,
  `limit_processes`, and `actual_processes`: non-negative JSON integers or
  null only for `line` and `column` when no source coordinate is available;
- `limit_seconds` and `elapsed_seconds`: finite non-negative JSON numbers;
- `limit_scope`: `source`, `view`, or `invocation`;
- `encryption_detected`: boolean `true`;
- `exit_status`: signed integer or null when the process has no exit status;
- `signal`: stable lowercase ASCII signal identifier or null;
- `field`: RFC 6901 JSON Pointer string naming the invalid output field;
- `before_coordinate` and `after_coordinate`: canonical coordinate strings or
  null when the alignment failure has no single side coordinate.

The rejected alternative is a generic resource-exhausted bucket with
backend-specific strings, omitted safe messages, nested problem outcomes, or no
exact detail shape. If this proposed amendment is accepted, old provisional
`pdf_worker_resource_exhausted` rows are replaced by the named stderr, temp,
decoded-output, RSS, concurrency, and spawn problem codes above.

#### P6C0A-2: source/PDF closed-union closure

If accepted, schema-v5 freezes `SourceCodeChange` and `PdfChange` as mutually
exclusive closed discriminated-union members:

```text
ChangeV5 =
  TextHunk
  | BinarySpan
  | StructuredChange
  | TableChange
  | ArrayChange
  | ImageChange
  | SourceCodeChange
  | PdfChange
  | ExtensionChange
```

`SourceCodeChange` has `kind="source_code_change"` and `change_variant` exactly
`lexical_text` or `syntax_tree`. It never has `view`. `PdfChange` has
`kind="pdf_change"` and `view` exactly `binary`, `extracted_text`,
`objects_metadata`, or `rendered_pages`. It never has `change_variant`.
Unknown discriminator combinations raise `SerializationError`. Extension
changes must use namespaced extension kinds and cannot reuse either built-in
kind.

Source lexical changes have stable top-level field order:

```text
kind
change_variant
operation
language
relation
coordinate_encoding
column_unit
before_range
after_range
lexical_text
before_fact
after_fact
payload_digest
```

`operation` is `equal`, `insert`, `delete`, `update`, or `move`. `insert` has null
`before_range` and `before_fact`; `delete` has null `after_range` and
`after_fact`; `update` and `move` have both sides; `equal` has both sides and is allowed
only in canonical fact and migration fixtures, not as a reported difference.
Byte offsets are zero-based half-open offsets in decoded UTF-8 bytes before
newline normalization. Line and column coordinates are over the normalized
logical line sequence. `lexical_text` is null in `digest_only` mode. In facts
mode it has exact field order `before_lines`, `after_lines`,
`before_final_terminator`, `after_final_terminator`, `mixed_newlines`.
`before_lines` and `after_lines` are arrays of objects with `content` and
`terminator` in that order; `terminator` is exactly `""`, `"\n"`, `"\r\n"`, or
`"\r"`, preserving RFC 0002 `TextLine` semantics per line. The final terminator
fields are booleans recording whether the side has any terminal line
terminator, so missing-final-newline and mixed-newline cases remain
distinguishable. `mixed_newlines` is a boolean computed before any explicit
normalization. Readers must not reconstruct byte offsets from normalized lines
when `mixed_newlines` is true.
`before_fact` and `after_fact` are either null or lexical facts with
`language`, `line_count`, `nonempty_line_count`, `terminator_histogram`,
`final_terminator`, and `content_digest` in that order.

Source syntax changes have stable top-level field order:

```text
kind
change_variant
operation
language
relation
parser_id
parser_version
before_path
after_path
before_node
after_node
before_range
after_range
before_fact
after_fact
payload_digest
```

`operation` is `equal`, `insert`, `delete`, `update`, or `move`. `before_path`
and `after_path` use the accepted RFC 0008 source syntax path grammar
`/root` plus `/<escaped-node-kind>#<ordinal-among-siblings-of-same-kind>`,
including `~0`, `~1`, and `~h` escapes. P6C0A-2 does not supersede that
grammar. `insert` has null `before_path` and before-side facts; `delete` has
null `after_path` and after-side facts; `update` has both paths at an aligned
node; `move` has both paths, equal selected identity facts, and changed paths.
`before_node` and `after_node` are either null or node records with
`node_kind`, `named`, `start_byte`, `end_byte`, `start_line`, `start_column`,
`end_line`, `end_column`, `child_count`, and `subtree_digest` in that order.
Syntax facts have `language`, `parser_id`, `parser_version`, `node_count`,
`max_depth`, `parser_error_count`, `recovery_used`, and `root_digest` in that
order. A syntax `equal` operation follows the same fixture-only rule as lexical
`equal`.

PDF binary changes have stable top-level field order:

```text
kind
view
binary_variant
operation
ranges
before_fact
after_fact
payload_digest
```

`operation` is `equal`, `insert`, `delete`, or `update`. `ranges` is a non-empty
array of objects with exact order `side`, `start_byte`, `end_byte`. `side` is
`before` or `after`; offsets are original PDF bytes before parsing, decryption,
repair, or decompression; each range is zero-based, half-open, non-overlapping
within its side, and sorted by `(side, start_byte, end_byte)`. Binary facts are
non-parsing facts with exact order `byte_length`, `header_prefix`,
`content_digest`. `header_prefix` is either null or the bounded ASCII prefix
obtained by byte-sniffing `%PDF-` at offset zero; binary facts do not include
encryption, xref, trailer, object, or page counts.

PDF extracted-text changes have stable top-level field order:

```text
kind
view
operation
page
before_run
after_run
text
before_fact
after_fact
payload_digest
```

`operation` is `equal`, `insert`, `delete`, `update`, or `move`. `before_run`
and `after_run` are null or objects with exact order `page`, `run`,
`start_text_offset`, `text_length`. Coordinates use
`pdf-text-run(page,run,start_offset,end_offset)`, where `page` is one-based,
`run` is zero-based in canonical extraction order, and offsets are zero-based
half-open Unicode scalar offsets within the extracted run text. `text` is null
in `digest_only` mode or an object with `before_text` and `after_text` bounded
by `max_fact_text_bytes`. Extracted-text facts have `page_count`, `run_count`,
`char_count`, `extraction_digest`, and `backend_id`.

PDF objects-metadata changes have stable top-level field order:

```text
kind
view
operation
object_ref
key_path
before_entry
after_entry
before_fact
after_fact
payload_digest
```

`operation` is `equal`, `insert`, `delete`, `update`, or `move`. `object_ref`
is null only for document-level metadata; otherwise it has exact order
`object_number`, `generation` and serializes as `pdf-object(obj,generation)`.
`key_path` is an RFC 6901 JSON Pointer over the canonical metadata object.
`before_entry` and `after_entry` are null or objects with exact order
`entry_kind`, `type_name`, `value`, `value_digest`, `byte_length`. `value` is
bounded JSON or null in `digest_only` mode. Move is legal only when both entries
have equal `value_digest` and different object or key coordinates.
Objects-metadata facts have `object_count`, `metadata_entry_count`,
`stream_count`, `trailer_digest`, and `object_digest`.

PDF rendered-pages changes have stable top-level field order:

```text
kind
view
operation
page
rect
raster_space
before_fact
after_fact
payload_digest
```

`operation` is `equal`, `insert`, `delete`, or `update`. `page` is one-based.
`rect` is null for whole-page insert/delete and otherwise has exact order
`page`, `x`, `y`, `width`, `height`; it serializes as
`pdf-raster-rect(page,x,y,width,height,dpi,colorspace)` using `raster_space`.
`raster_space` has exact order `page_box`, `rotation_degrees`, `dpi`,
`colorspace`, `alpha_mode`, `antialiasing`, `background`. `x`, `y`, `width`,
and `height` are zero-based pixel integers in the declared rendered page
raster; `width` and `height` are positive, and the rectangle must be in bounds.
Rendered-page facts have `page`, `width_px`, `height_px`, `dpi`, `colorspace`,
`alpha_mode`, `render_backend_id`, and `raster_digest`.

For every variant, operation-side rules are closed:

| Operation | Before coordinate/fact | After coordinate/fact | Cardinality |
| --- | --- | --- | --- |
| `equal` | required | required | fixture-only, facts and payload digest equal |
| `insert` | null | required | one after-side coordinate/fact |
| `delete` | required | null | one before-side coordinate/fact |
| `update` | required | required | one aligned before/after pair |
| `move` | required | required | source syntax and PDF text/object only; stable digest equal and coordinates changed |

P6-C0 fixtures may include equal facts to prove ordering, coordinates, and
digests, but completed comparison outputs do not report equal operations as
changed items.

Contract-only provenance is also closed. P6-C0 fixtures may directly construct
completed outcomes and failed or unavailable outcomes for reader/writer
validation. They must record accepted comparator and algorithm IDs in
provenance and compatibility receipts, but no registry route may execute them
through public `compare()` or the CLI until P6-S1 or P6-P1a starts.

Additional proposed canonical vectors are:

| Domain | Tagged fields | Payload hex | SHA-256 |
| --- | --- | --- | --- |
| `source/node` | `kind=source_code_change`, `change_variant=syntax_tree`, `operation=update`, `language=python`, `before_path=/root/module#0`, `after_path=/root/module#0` | `000000000000000600000000000000046b696e640000000000000012736f757263655f636f64655f6368616e6765000000000000000e6368616e67655f76617269616e74000000000000000b73796e7461785f7472656500000000000000096f7065726174696f6e000000000000000675706461746500000000000000086c616e67756167650000000000000006707974686f6e000000000000000b6265666f72655f70617468000000000000000e2f726f6f742f6d6f64756c652330000000000000000a61667465725f70617468000000000000000e2f726f6f742f6d6f64756c652330` | `f3fdad01158fddcac7cc22eb103d0a8f27c91bbe4363209867a5656c9e2e6e9b` |
| `pdf/text/run` | `kind=pdf_change`, `view=extracted_text`, `operation=update`, `page=1`, `run=1` | `000000000000000500000000000000046b696e64000000000000000a7064665f6368616e6765000000000000000476696577000000000000000e6578747261637465645f7465787400000000000000096f7065726174696f6e0000000000000006757064617465000000000000000470616765000000000000000131000000000000000372756e000000000000000131` | `8a0e8e2e5d20577c69a226ee0f29f61b89959cd8f1034e7d138e87888d5780cb` |
| `pdf/object/entry` | `kind=pdf_change`, `view=objects_metadata`, `operation=update`, `object_ref=1 0`, `key_path=/Type` | `000000000000000500000000000000046b696e64000000000000000a7064665f6368616e676500000000000000047669657700000000000000106f626a656374735f6d6574616461746100000000000000096f7065726174696f6e0000000000000006757064617465000000000000000a6f626a6563745f726566000000000000000331203000000000000000086b65795f7061746800000000000000052f54797065` | `bca6551004edcbdbb5daf3fefb02916ffb4b3e89afc2af08c2b3514cbfb56c6b` |
| `pdf/render/region` | `kind=pdf_change`, `view=rendered_pages`, `operation=update`, `page=1`, `x=0`, `y=0`, `width=1`, `height=1` | `000000000000000800000000000000046b696e64000000000000000a7064665f6368616e6765000000000000000476696577000000000000000e72656e64657265645f706167657300000000000000096f7065726174696f6e0000000000000006757064617465000000000000000470616765000000000000000131000000000000000178000000000000000130000000000000000179000000000000000130000000000000000577696474680000000000000001310000000000000006686569676874000000000000000131` | `fc8cb8dce91350fd39803dab87bfa9971e4341df5889a6749e5964907d4727d8` |

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
