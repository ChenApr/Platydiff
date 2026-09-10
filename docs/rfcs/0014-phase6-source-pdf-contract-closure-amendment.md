# RFC 0014: Phase 6 Source/PDF Contract Closure Amendment

[Chinese documentation](0014-phase6-source-pdf-contract-closure-amendment_zh.md)

- Status: Proposed
- Date: 2026-09-10
- Decision IDs: P6C0A-1-P6C0A-2
- Owners: Platydiff maintainers
- RFC allocation: 0011 audio preflight; 0012 P7 closure; 0013 P5 closure; 0014 P6 closure
- Related RFCs: [RFC 0008](0008-source-code-and-pdf-comparison.md), [RFC 0010](0010-schema-predecessor-and-phase6-contract-amendment.md)
- Implementation authorization: none; this is proposed clarification-only contract text

## Summary and Authorization Boundary

This RFC proposes the P6-C0 closure amendment for schema-v5 source/PDF
contracts. It is Proposed, not Accepted. It does not alter the accepted status
of RFC 0008 or RFC 0010, does not mark P6C0A-1 or P6C0A-2 as accepted, and
does not authorize source/PDF comparator, CLI, backend, dependency, SDK,
artifact, automatic detection, or UI implementation.

P6-C0 remains contract-only and still waits for RFC 0010, P4-C1,
P5-A1/schema-v4, and compatibility fixtures to merge to `main`, followed by
explicit coordinator dispatch. This RFC exists only to review the closure gaps
identified after RFC 0010: the schema-v5 source/PDF problem registry and the
`SourceCodeChange`/`PdfChange` closed-union shape.

## Proposed P6-C0 Closure Amendment

The following P6C0A decisions are Proposed, not Accepted. They are draft
closure criteria for P6-C0 only. They preserve P6-C0 as contract-only work:
no source/PDF comparator, CLI route, backend worker, dependency, SDK, artifact,
automatic detection, or UI implementation may start from these proposed
decisions. P6-C0 still waits for RFC 0010, P4-C1, P5-A1/schema-v4, and
compatibility fixtures to merge to `main`, followed by explicit coordinator
dispatch.

### P6C0A-1: problem registry closure

If accepted, schema-v5 source/PDF problems preserve the existing
`ExecutionProblem` and `CapabilityProblem` wire shape and canonical field order:
`code`, `status_code`, `stage`, `message`, `details`, `retryable`. `message`
is a bounded safe human message. The outer `CompareOutcome.kind` and problem
class determine `failed` versus `unavailable`; schema-v5 does not add a nested
problem `outcome` field. New scoped registry keys use `schema-v5/<code>`, while
serialized `code` remains the short stable code.

Canonical JSON emits `details` keys in the order listed below. Readers reject
missing keys, extra keys, wrong types, and noncanonical key order in canonical
fixtures. Detail keys listed as `none` mean the canonical `details` value is an
empty object. Retryability listed as raised value preserves the retryability
flag carried by the originating domain error.

| Registry ID | Problem class and outer outcome | Status code | Stage | Retryable | Detail keys |
| --- | --- | ---: | --- | --- | --- |
| inherited `invalid_spec` | `ExecutionProblem` / `failed` | `400` | `validating` | `false` | `spec_field`, `reason_code` |
| inherited `permission_denied` | `ExecutionProblem` / `failed` | `403` | `sourcing` | `false` | `input_side`, `source_kind`, `source_ref`, `operation`, `reason_code` |
| inherited `source_not_found` | `ExecutionProblem` / `failed` | `404` | `sourcing` | `false` | `input_side`, `source_kind`, `source_ref`, `operation`, `reason_code` |
| inherited `source_changed` | `ExecutionProblem` / `failed` | `409` | observing stage | `false` | `input_side`, `source_kind`, `source_ref`, `observed_stage`, `reason_code` |
| inherited `capability_unavailable` | `CapabilityProblem` / `unavailable` | `501` | `resolving` | `true` | `capability_id`, `relation_or_view`, `reason_code` |
| inherited `backend_unavailable` | `CapabilityProblem` / `unavailable` | `503` | `resolving` | `true` | `backend_role`, `backend_id`, `relation_or_view`, `reason_code` |
| inherited `resource_limit_exceeded` | `ExecutionProblem` / `failed` | `413` | action stage | `false` | `resource`, `limit`, `actual`, `limit_scope`, `relation_or_view` |
| inherited `compare_resource_limit` | `ExecutionProblem` / `failed` | `413` | `comparing` | `false` | `used`, `limit` |
| inherited `unsupported_encoding` | `ExecutionProblem` / `failed` | `415` | `decoding` | `false` | `input_side`, `encoding`, `supported_encodings`, `reason_code` |
| inherited `source_type_unsupported` | `ExecutionProblem` / `failed` | `415` | `sourcing` | `false` | `input_side`, `actual_source_type`, `supported_source_types`, `spec_kind`, `reason_code` |
| `schema-v5/alignment_failed` | `ExecutionProblem` / `failed` | `409` | `aligning` | `false` | `relation_or_view`, `reason_code`, `before_coordinate`, `after_coordinate` |
| inherited `decode_error` | `ExecutionProblem` / `failed` | `422` | `decoding` | `false` | `input_side`, `relation_or_view`, `message_code`, `line`, `column` |
| inherited `internal_error` | `ExecutionProblem` / `failed` | `500` | `validating` | `false` | none |
| inherited `io_error` | `ExecutionProblem` / `failed` | `500` | action stage | raised value | `input_side`, `source_kind`, `operation`, `reason_code` |
| inherited `comparator_failure` | `ExecutionProblem` / `failed` | `502` | `comparing` | `false` | `relation_or_view`, `backend_role`, `backend_id`, `reason_code` |
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

For rows with observing stage, `stage` is where the stable snapshot detects the
change: `detecting`, `decoding`, `comparing`, or `aggregating`. For rows with
action stage, `stage` is selected by the failed action or exceeded resource:
source or PDF input bytes fail at `sourcing`; decoded source chars, source
fact text bytes, parser node counts, PDF decoded streams, PDF text runs, PDF
object entries, and nonrender worker output fail at `decoding`; rendered page
counts, rendered pixels, rendered-page worker output, rendered-page temp bytes,
and rendered-page RSS fail at `decoding`; comparator-local I/O fails at
`comparing`. For rows with view worker stage, `stage` is `decoding` for
`extracted_text`, `objects_metadata`, and `rendered_pages`; the pure `binary`
view has no worker stage.

Closed detail value types are:

- `source_relation`: `lexical_text` or `syntax_tree`;
- `view`: `binary`, `extracted_text`, `objects_metadata`, or
  `rendered_pages`;
- `relation_or_view`: one source relation or PDF view name;
- `input_side`: `before` or `after`;
- `source_kind`: `path`, `bytes`, or `text`;
- `source_ref`: a bounded safe source label or null;
- `actual_source_type`: a stable source type identifier; built-ins are `path`,
  `bytes`, and `text`, and extensions must use namespaced identifiers;
- `supported_source_types`: a non-empty array of stable source type
  identifiers;
- `spec_kind`: the stable spec discriminator;
- `backend_role`: `parser`, `text_extractor`, `object_reader`, or `renderer`;
- `operation`: `stat`, `open`, `read`, `decode`, `snapshot_check`, or
  `compare`;
- `encoding`: a stable encoding label or null when no label is available;
- `supported_encodings`: a non-empty array of stable encoding labels;
- `observed_stage`: `detecting`, `decoding`, `comparing`, or `aggregating`;
- `language`, `backend_id`, `capability_id`, `reason_code`, `message_code`,
  `resource`, `stream`, and `message_kind`: stable lowercase ASCII identifiers
  or null only where the table names a nullable field;
- `line`, `column`, `used`, `limit`, `actual`, `limit_bytes`, `actual_bytes`,
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

### P6C0A-2: source/PDF closed-union closure

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

`operation` is `equal`, `insert`, `delete`, or `update`. `insert` has null
`before_range` and `before_fact`; `delete` has null `after_range` and
`after_fact`; `update` has both sides; `equal` has both sides and is allowed
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
within its side, and sorted by `(side, start_byte, end_byte)`. `insert` ranges
all have side `after`; `delete` ranges all have side `before`; `update` ranges
include at least one `before` range and at least one `after` range; `equal`
fixture ranges contain exactly one `before` range and one `after` range with
equal byte length. Because range objects do not carry per-range content
digests, detached readers validate binary range structure, side membership,
ordering, cardinality, and lengths only; binary byte equality is validated from
named before/after binary facts when they are present. Binary facts are
non-parsing facts with exact order `byte_length`, `header_prefix`,
`content_digest`. `header_prefix` is either null or the bounded ASCII prefix
obtained by byte-sniffing `%PDF-` at offset zero; binary facts do not include
encryption, xref, trailer, object, or page counts.

PDF extracted-text changes have stable top-level field order:

```text
kind
view
operation
before_run
after_run
before_text_digest
after_text_digest
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
by `max_fact_text_bytes`. In facts mode, `before_text` is null exactly when
`before_run` is null, and `after_text` is null exactly when `after_run` is
null. `before_text_digest` is null exactly when `before_run` is null, and
`after_text_digest` is null exactly when `after_run` is null. Non-null text-run
digests are SHA-256 values computed with the accepted `pdf/text/run` frame over
that side's page, run, text bytes, extractor flags, and text span; they remain
present when `text` is null in `digest_only` mode. `insert` has null
`before_run`, `before_text_digest`, and `before_text`; `delete` has null
`after_run`, `after_text_digest`, and `after_text`; `update` has both runs on
the same page at an aligned text coordinate and unequal text-run digests;
`move` has both runs on the same page, equal text-run digests, and changed
`(run, start_text_offset)`. Cross-page text movement is reported as delete plus
insert to preserve RFC 0008 page-local text alignment.
Extracted-text facts have `page_count`, `run_count`, `char_count`,
`extraction_digest`, and `backend_id`.

PDF objects-metadata changes have stable top-level field order:

```text
kind
view
operation
before_object_ref
before_key_path
after_object_ref
after_key_path
before_entry
after_entry
before_fact
after_fact
payload_digest
```

`operation` is `equal`, `insert`, `delete`, `update`, or `move`. Object
reference fields are null only for document-level metadata; otherwise they
have exact order `object_number`, `generation` and serialize as
`pdf-object(obj,generation)`. Key paths are RFC 6901 JSON Pointers over the
canonical metadata object. `before_entry` and `after_entry` are null or objects
with exact order `entry_kind`, `type_name`, `value`, `value_digest`,
`byte_length`. `entry_kind` is `dictionary_entry`, `array_item`,
`stream_dictionary_entry`, or `document_metadata_entry`; `type_name` is
`null`, `boolean`, `integer`, `real`, `name`, `string`, `array`,
`dictionary`, or `stream`. `value` is canonical bounded JSON, with object keys
sorted, arrays ordered as in the PDF fact domain, maximum nesting depth 16, no
non-finite numbers, and no backend-private objects. In `digest_only` mode
`value` is null and `value_digest` is required. When `value` is not null,
`value_digest` must equal the digest of that canonical value and `byte_length`
must equal the original encoded value byte length when one is available.
`insert` has null before object/key/entry fields; `delete` has null after
object/key/entry fields; `update` has both coordinates at an aligned entry and
unequal `value_digest`; `move` has both before and after object/key
coordinates, equal `value_digest`, and changed object or key coordinate.
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
When `rect` is not null, top-level `page`, `rect.page`, and each side's
rendered-page fact `page` are equal. `page_box` is `media` or `crop`;
`rotation_degrees` is `0`, `90`, `180`, or `270`; `dpi` is a positive integer;
`colorspace` is `srgb`, `gray`, or `display_p3`; `alpha_mode` is `opaque` or
`premultiplied`; `antialiasing` is `none`, `grayscale`, or `subpixel`; and
`background` is a six-digit lowercase hex RGB string or null. Rendered-page
facts have `page`, `width_px`, `height_px`, `dpi`, `colorspace`, `alpha_mode`,
`render_backend_id`, and `raster_digest`. Their `dpi`, `colorspace`, and
`alpha_mode` must match `raster_space`, and `raster_digest` must be the digest
of the declared raster-space pixels for that side.

For every variant, operation-side rules are closed. The table's
coordinate/fact references mean the variant's actual before/after fields:
source lexical ranges and facts; source syntax paths, nodes, ranges, and facts;
PDF binary range sides and facts; PDF text runs, text sides, and facts; PDF
object references, key paths, entries, and facts; and PDF raster rects and
rendered-page facts.

| Operation | Before coordinate/fact | After coordinate/fact | Cardinality |
| --- | --- | --- | --- |
| `equal` | required | required | fixture-only; the named before/after facts for that variant are equal, and the single `payload_digest` is the valid digest of the canonical change payload |
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

Additional proposed canonical vectors use the accepted RFC 0008 frame and, if
accepted, supersede the stale RFC 0010 `source/change_payload` vector that uses
`range_variant` and the stale `pdf/binary/span` vector that uses
`span_variant` for P6 source/PDF compatibility fixtures. RFC 0010 remains the
accepted historical baseline until this amendment is accepted. These rows are
not replacement hashes for the old payloads; each row defines one coherent
fact-domain payload matching the accepted domain components.

Generation and check algorithm:

```text
payload =
  U64BE(field_count) ||
  for each listed field in order:
    U64BE(tag_length) || UTF8(tag) || U64BE(value_length) || value_bytes

frame =
  UTF8("platydiff/v5/" + domain) || 0x00 || U64BE(payload_length) || payload

SHA-256 = SHA256(frame)
```

To check a vector, decode the payload hex, rebuild the frame from the domain
and payload length, and compare the SHA-256 column to `SHA256(frame)`.
For change-payload domains, field-path tags flatten nested values in stable
field-order traversal. The change object's `payload_digest` field is excluded
from the hashed payload to avoid recursion; `payload_digest` stores the digest
produced by this algorithm.
Scalar `value_bytes` use the RFC 0010 rules. Sequence fields use nested list
framing, not repeated tags, delimiters, or JSON:

```text
list_value =
  U64BE(element_count) ||
  for each element in order:
    U64BE(element_length) || element_value_bytes
```

`source/node` uses list framing for `child_field_names`,
`ordered_child_digests`, `retained_token_digests`, and
`retained_trivia_digests`. Empty lists encode as `U64BE(0)`. `pdf/text/run`
encodes `extractor_flags` as a closed flagset frame, not as a delimited string:

```text
flagset_value =
  U64BE(entry_count) ||
  for each registry key in canonical order:
    U64BE(key_length) || UTF8(key) || boolean_byte
```

The initial flag registry and canonical order are `backend_tounicode`,
`ligatures_preserved`, then `vertical_writing`. `boolean_byte` is `0x00` for
false and `0x01` for true. Keys are stable lowercase ASCII identifiers; because
each key is length-framed, no escaping or delimiter convention is used.

| Domain | Tagged fields | Payload hex | SHA-256 |
| --- | --- | --- | --- |
| `source/node` | `language=python`, `node_kind=module`, `child_field_names=[]`, `ordered_child_digests=[]`, `retained_token_digests=[]`, `retained_trivia_digests=[]` | `000000000000000600000000000000086c616e67756167650000000000000006707974686f6e00000000000000096e6f64655f6b696e6400000000000000066d6f64756c6500000000000000116368696c645f6669656c645f6e616d65730000000000000008000000000000000000000000000000156f7264657265645f6368696c645f6469676573747300000000000000080000000000000000000000000000001672657461696e65645f746f6b656e5f6469676573747300000000000000080000000000000000000000000000001772657461696e65645f7472697669615f6469676573747300000000000000080000000000000000` | `c4de32de8c4cc95b9808a79cdce30ec5b20304b9ecb83efe719fa271f8f268dd` |
| `source/node` | `language=python`, `node_kind=function_definition`, `child_field_names=[decorator,body]`, `ordered_child_digests=[sha256:1111111111111111111111111111111111111111111111111111111111111111,sha256:2222222222222222222222222222222222222222222222222222222222222222]`, `retained_token_digests=[sha256:3333333333333333333333333333333333333333333333333333333333333333,sha256:4444444444444444444444444444444444444444444444444444444444444444]`, `retained_trivia_digests=[sha256:5555555555555555555555555555555555555555555555555555555555555555,sha256:6666666666666666666666666666666666666666666666666666666666666666]` | `000000000000000600000000000000086c616e67756167650000000000000006707974686f6e00000000000000096e6f64655f6b696e64000000000000001366756e6374696f6e5f646566696e6974696f6e00000000000000116368696c645f6669656c645f6e616d65730000000000000025000000000000000200000000000000096465636f7261746f720000000000000004626f647900000000000000156f7264657265645f6368696c645f6469676573747300000000000000a6000000000000000200000000000000477368613235363a3131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313100000000000000477368613235363a32323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232000000000000001672657461696e65645f746f6b656e5f6469676573747300000000000000a6000000000000000200000000000000477368613235363a3333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333300000000000000477368613235363a34343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434000000000000001772657461696e65645f7472697669615f6469676573747300000000000000a6000000000000000200000000000000477368613235363a3535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353500000000000000477368613235363a36363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636` | `d69b660503f4c010d386e73f15a483b99b5a92e70caa1643502584b3906fe3fc` |
| `pdf/text/run` | `page=1`, `run=0`, `text=Test`, `extractor_flags={backend_tounicode=false,ligatures_preserved=true,vertical_writing=false}`, `start_text_offset=0`, `text_length=4` | `0000000000000006000000000000000470616765000000000000000131000000000000000372756e000000000000000130000000000000000474657874000000000000000454657374000000000000000f657874726163746f725f666c6167730000000000000057000000000000000300000000000000116261636b656e645f746f756e69636f64650000000000000000136c69676174757265735f707265736572766564010000000000000010766572746963616c5f77726974696e6700000000000000001173746172745f746578745f6f6666736574000000000000000130000000000000000b746578745f6c656e677468000000000000000134` | `bd597ba903a5a6ed7c45672420212e141cd31ef0d03d5fa2f73380cbcf833d2f` |
| `pdf/object/entry` | `object_number=1`, `generation=0`, `key_path=/Type`, `type_name=name`, `canonical_value_bytes=/Catalog` | `0000000000000005000000000000000d6f626a6563745f6e756d626572000000000000000131000000000000000a67656e65726174696f6e00000000000000013000000000000000086b65795f7061746800000000000000052f547970650000000000000009747970655f6e616d6500000000000000046e616d65000000000000001563616e6f6e6963616c5f76616c75655f627974657300000000000000082f436174616c6f67` | `3ddea5707609a6d92c3f8febd1b3338a74b5a02484e32a6f639fe34aabec393b` |
| `pdf/render/region` | `page=1`, `page_box=media`, `rotation_degrees=0`, `dpi=72`, `colorspace=srgb`, `alpha_mode=opaque`, `antialiasing=grayscale`, `background=ffffff`, `x=0`, `y=0`, `width=1`, `height=1`, `before_digest=sha256:7777777777777777777777777777777777777777777777777777777777777777`, `after_digest=sha256:8888888888888888888888888888888888888888888888888888888888888888`, `changed_pixel_count=1` | `000000000000000f0000000000000004706167650000000000000001310000000000000008706167655f626f7800000000000000056d656469610000000000000010726f746174696f6e5f64656772656573000000000000000130000000000000000364706900000000000000023732000000000000000a636f6c6f727370616365000000000000000473726762000000000000000a616c7068615f6d6f646500000000000000066f7061717565000000000000000c616e7469616c696173696e670000000000000009677261797363616c65000000000000000a6261636b67726f756e640000000000000006666666666666000000000000000178000000000000000130000000000000000179000000000000000130000000000000000577696474680000000000000001310000000000000006686569676874000000000000000131000000000000000d6265666f72655f64696765737400000000000000477368613235363a37373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737000000000000000c61667465725f64696765737400000000000000477368613235363a3838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383800000000000000136368616e6765645f706978656c5f636f756e74000000000000000131` | `3a974c20b539430366f6ef35367c6354d81ba093db13d3e45caca6bed848d77d` |
| `source/change_payload` | `kind=source_code_change`, `change_variant=lexical_text`, `operation=update`, `language=python`, `relation=lexical_text`, `coordinate_encoding=utf8_byte_offsets`, `column_unit=unicode_scalar`, `before_range.start_byte=0`, `before_range.end_byte=4`, `after_range.start_byte=0`, `after_range.end_byte=5`, `before_fact_digest=sha256:9999999999999999999999999999999999999999999999999999999999999999`, `after_fact_digest=sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | `000000000000000d00000000000000046b696e640000000000000012736f757263655f636f64655f6368616e6765000000000000000e6368616e67655f76617269616e74000000000000000c6c65786963616c5f7465787400000000000000096f7065726174696f6e000000000000000675706461746500000000000000086c616e67756167650000000000000006707974686f6e000000000000000872656c6174696f6e000000000000000c6c65786963616c5f746578740000000000000013636f6f7264696e6174655f656e636f64696e670000000000000011757466385f627974655f6f666673657473000000000000000b636f6c756d6e5f756e6974000000000000000e756e69636f64655f7363616c617200000000000000176265666f72655f72616e67652e73746172745f6279746500000000000000013000000000000000156265666f72655f72616e67652e656e645f62797465000000000000000134000000000000001661667465725f72616e67652e73746172745f62797465000000000000000130000000000000001461667465725f72616e67652e656e645f6279746500000000000000013500000000000000126265666f72655f666163745f64696765737400000000000000477368613235363a39393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939000000000000001161667465725f666163745f64696765737400000000000000477368613235363a61616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161` | `55eba1386fcbda85a62ced49871a9669a16f2b81f7e3ef598c701b7cc8e12930` |
| `pdf/change_payload` | `kind=pdf_change`, `view=binary`, `binary_variant=byte_ranges`, `operation=update`, `ranges.0.side=before`, `ranges.0.start_byte=0`, `ranges.0.end_byte=4`, `ranges.1.side=after`, `ranges.1.start_byte=0`, `ranges.1.end_byte=5`, `before_fact_digest=sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`, `after_fact_digest=sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc` | `000000000000000c00000000000000046b696e64000000000000000a7064665f6368616e6765000000000000000476696577000000000000000662696e617279000000000000000e62696e6172795f76617269616e74000000000000000b627974655f72616e67657300000000000000096f7065726174696f6e0000000000000006757064617465000000000000000d72616e6765732e302e7369646500000000000000066265666f7265000000000000001372616e6765732e302e73746172745f62797465000000000000000130000000000000001172616e6765732e302e656e645f62797465000000000000000134000000000000000d72616e6765732e312e7369646500000000000000056166746572000000000000001372616e6765732e312e73746172745f62797465000000000000000130000000000000001172616e6765732e312e656e645f6279746500000000000000013500000000000000126265666f72655f666163745f64696765737400000000000000477368613235363a62626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262000000000000001161667465725f666163745f64696765737400000000000000477368613235363a63636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363` | `5a85bcf47212f8896206c34a07822d47e64ebdf3480ab751c87814477a1ad9f9` |
