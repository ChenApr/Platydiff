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
