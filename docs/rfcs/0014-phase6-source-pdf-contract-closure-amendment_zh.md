# RFC 0014：Phase 6 Source/PDF Contract Closure Amendment

[English documentation](0014-phase6-source-pdf-contract-closure-amendment.md)

- Status: Proposed
- Date: 2026-09-10
- Decision IDs: P6C0A-1-P6C0A-2
- Owners: Platydiff 维护者
- RFC allocation：0011 audio preflight；0012 P7 closure；0013 P5 closure；0014 P6 closure
- Related RFCs：[RFC 0008](0008-source-code-and-pdf-comparison_zh.md)、[RFC 0010](0010-schema-predecessor-and-phase6-contract-amendment_zh.md)
- Implementation authorization：无；本文仅是 proposed clarification-only contract text

## 摘要与授权边界

本 RFC 提议 schema-v5 source/PDF contract 的 P6-C0 closure amendment。它是 Proposed，
不是 Accepted。它不改变 RFC 0008 或 RFC 0010 的 accepted status，不把 P6C0A-1 或 P6C0A-2
标记为 accepted，也不授权 source/PDF comparator、CLI、backend、dependency、SDK、artifact、
automatic detection 或 UI 实现。

P6-C0 保持 contract-only，并且仍须等待 RFC 0010、P4-C1、P5-A1/schema-v4 与 compatibility
fixture 合并到 `main`，之后还需要明确 coordinator dispatch。本 RFC 只用于 review RFC 0010 之后
识别出的 closure gap：schema-v5 source/PDF problem registry，以及 `SourceCodeChange`/`PdfChange`
closed-union shape。

## Proposed P6-C0 Closure Amendment

下列 P6C0A decision 是 Proposed，不是 Accepted。它们只是 P6-C0 的 draft closure criteria。
它们保持 P6-C0 contract-only：不得从这些 proposed decision 启动 source/PDF comparator、
CLI route、backend worker、dependency、SDK、artifact、automatic detection 或 UI 实现。
P6-C0 仍须等待 RFC 0010、P4-C1、P5-A1/schema-v4 与 compatibility fixture 合并到 `main`，
之后还需要明确 coordinator dispatch。

### P6C0A-1：problem registry closure

如果被接受，schema-v5 source/PDF problem 保留现有 `ExecutionProblem` 与
`CapabilityProblem` wire shape 及 canonical field order：`code`、`status_code`、`stage`、
`message`、`details`、`retryable`。`message` 是有界 safe human message。外层
`CompareOutcome.kind` 与 problem class 决定 `failed` 还是 `unavailable`；schema-v5 不新增 nested
problem `outcome` field。新的 scoped registry key 使用 `schema-v5/<code>`，serialized `code`
仍是短 stable code。

Canonical JSON 按下表顺序发出 `details` key。Reader 在 canonical fixture 中拒绝 missing key、
extra key、错误 type 与非 canonical key order。

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

对 action stage row，`stage` 由 exceeded resource 决定：source 或 PDF input byte 在 `sourcing`
失败；decoded source char、source fact text byte、parser node count、PDF decoded stream、PDF text
run、PDF object entry 与 nonrender worker output 在 `decoding` 失败；rendered page count、rendered
pixel、rendered-page worker output、rendered-page temp byte 与 rendered-page RSS 在 `rendering`
失败。对 view worker stage row，当 `view="rendered_pages"` 时 `stage` 是 `rendering`，
`extracted_text` 与 `objects_metadata` 使用 `decoding`；pure `binary` view 没有 worker stage。

Closed detail value type 为：

- `source_relation`：`lexical_text` 或 `syntax_tree`；
- `view`：`binary`、`extracted_text`、`objects_metadata` 或 `rendered_pages`；
- `relation_or_view`：一个 source relation 或 PDF view name；
- `input_side`：`before` 或 `after`；
- `source_kind`：`path`、`bytes` 或 `text`；
- `spec_kind`：stable spec discriminator；
- `backend_role`：`parser`、`text_extractor`、`object_reader` 或 `renderer`；
- `language`、`backend_id`、`capability_id`、`reason_code`、`message_code`、
  `resource`、`stream` 与 `message_kind`：stable lowercase ASCII identifier，只有表中允许
  nullable 的字段可以是 null；
- `line`、`column`、`limit`、`actual`、`limit_bytes`、`actual_bytes`、
  `limit_processes` 与 `actual_processes`：non-negative JSON integer；只有没有 source
  coordinate 时 `line` 与 `column` 可以是 null；
- `limit_seconds` 与 `elapsed_seconds`：finite non-negative JSON number；
- `limit_scope`：`source`、`view` 或 `invocation`；
- `encryption_detected`：boolean `true`；
- `exit_status`：signed integer，或在 process 没有 exit status 时为 null；
- `signal`：stable lowercase ASCII signal identifier 或 null；
- `field`：命名 invalid output field 的 RFC 6901 JSON Pointer string；
- `before_coordinate` 与 `after_coordinate`：canonical coordinate string，或 alignment failure
  没有单一 side coordinate 时为 null。

被拒绝的替代方案是 generic resource-exhausted bucket、backend-specific string、遗漏 safe
message、nested problem outcome，或没有精确 detail shape。如果本 proposed amendment 被接受，
旧的 provisional `pdf_worker_resource_exhausted` row 会被上方 named stderr、temp、
decoded-output、RSS、concurrency 与 spawn problem code 替代。

### P6C0A-2：source/PDF closed-union closure

如果被接受，schema-v5 会把 `SourceCodeChange` 与 `PdfChange` 冻结为 mutually exclusive closed
discriminated-union member：

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

`SourceCodeChange` 具有 `kind="source_code_change"`，且 `change_variant` 只能是
`lexical_text` 或 `syntax_tree`。它绝不包含 `view`。`PdfChange` 具有 `kind="pdf_change"`，
且 `view` 只能是 `binary`、`extracted_text`、`objects_metadata` 或 `rendered_pages`。它绝不包含
`change_variant`。未知 discriminator combination 会 raise `SerializationError`。Extension
change 必须使用 namespaced extension kind，且不能复用任一 built-in kind。

Source lexical change 的 stable top-level field order 为：

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

`operation` 是 `equal`、`insert`、`delete`、`update` 或 `move`。`insert` 的 `before_range` 与
`before_fact` 为 null；`delete` 的 `after_range` 与 `after_fact` 为 null；`update` 与 `move` 两侧都有；
`equal` 两侧都有，且只允许出现在 canonical fact 与 migration fixture 中，不作为 reported
difference。Byte offset 是 newline normalization 前 decoded UTF-8 byte 中的 zero-based
half-open offset。Line 与 column coordinate 基于 normalized logical line sequence。
`lexical_text` 在 `digest_only` mode 中为 null。在 facts mode 中，它的精确 field order 是
`before_lines`、`after_lines`、`before_final_terminator`、`after_final_terminator`、
`mixed_newlines`。`before_lines` 与 `after_lines` 是 object array，每个 object 按 `content`、
`terminator` 排序；`terminator` 只能是 `""`、`"\n"`、`"\r\n"` 或 `"\r"`，逐行保留 RFC 0002
`TextLine` 语义。Final terminator field 是 boolean，记录对应 side 是否有 terminal line
terminator，因此 missing-final-newline 与 mixed-newline case 仍可区分。`mixed_newlines` 是在任何
显式 normalization 前计算的 boolean。当 `mixed_newlines` 为 true 时，reader 不得从 normalized line
重建 byte offset。`before_fact` 与 `after_fact` 要么是 null，要么是按 `language`、`line_count`、
`nonempty_line_count`、`terminator_histogram`、`final_terminator`、`content_digest` 排序的 lexical fact。

Source syntax change 的 stable top-level field order 为：

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

`operation` 是 `equal`、`insert`、`delete`、`update` 或 `move`。`before_path` 与 `after_path`
使用已接受 RFC 0008 source syntax path grammar：`/root` 加
`/<escaped-node-kind>#<ordinal-among-siblings-of-same-kind>`，并包含 `~0`、`~1` 与 `~h`
escape。P6C0A-2 不 supersede 该 grammar。`insert` 的 `before_path` 与 before-side fact 为 null；
`delete` 的 `after_path` 与 after-side fact 为 null；`update` 两侧是 aligned node；`move` 两侧都有
path，selected identity fact 相等，且 path 发生变化。`before_node` 与 `after_node` 要么是 null，
要么是 node record，其字段顺序为 `node_kind`、`named`、
`start_byte`、`end_byte`、`start_line`、`start_column`、`end_line`、`end_column`、
`child_count`、`subtree_digest`。Syntax fact 的字段顺序为 `language`、`parser_id`、
`parser_version`、`node_count`、`max_depth`、`parser_error_count`、`recovery_used`、
`root_digest`。Syntax `equal` operation 遵循与 lexical `equal` 相同的 fixture-only rule。

PDF binary change 的 stable top-level field order 为：

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

`operation` 是 `equal`、`insert`、`delete` 或 `update`。`ranges` 是 non-empty object array，
每个 object 精确字段顺序为 `side`、`start_byte`、`end_byte`。`side` 是 `before` 或 `after`；
offset 是 parsing、decryption、repair 或 decompression 前 original PDF byte 上的 zero-based
half-open offset；每个 range 在同一 side 内不重叠，并按 `(side, start_byte, end_byte)` 排序。
Binary fact 是 non-parsing fact，精确字段顺序为 `byte_length`、`header_prefix`、`content_digest`。
`header_prefix` 要么是 null，要么是通过在 offset zero byte-sniff `%PDF-` 得到的 bounded ASCII
prefix；binary fact 不包含 encryption、xref、trailer、object 或 page count。

PDF extracted-text change 的 stable top-level field order 为：

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

`operation` 是 `equal`、`insert`、`delete`、`update` 或 `move`。`before_run` 与 `after_run`
要么是 null，要么是精确字段顺序为 `page`、`run`、`start_text_offset`、`text_length` 的 object。
Text-run coordinate 使用 `pdf-text-run(page,run,start_offset,end_offset)`，其中 `page` 是
one-based，`run` 是 canonical extraction order 中的 zero-based ordinal，offset 是 extracted
run text 中的 zero-based half-open Unicode scalar offset。`text` 在 `digest_only` mode 中为 null，
否则是包含 `before_text` 与 `after_text`、并受 `max_fact_text_bytes` 限制的 object。
Extracted-text fact 有 `page_count`、`run_count`、`char_count`、`extraction_digest` 与 `backend_id`。

PDF objects-metadata change 的 stable top-level field order 为：

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

`operation` 是 `equal`、`insert`、`delete`、`update` 或 `move`。`object_ref` 只有对 document-level
metadata 才是 null；否则精确字段顺序为 `object_number`、`generation`，并序列化为
`pdf-object(obj,generation)`。`key_path` 是 canonical metadata object 上的 RFC 6901 JSON
Pointer。`before_entry` 与 `after_entry` 要么是 null，要么是精确字段顺序为 `entry_kind`、
`type_name`、`value`、`value_digest`、`byte_length` 的 object。`value` 是 bounded JSON，
或在 `digest_only` mode 中为 null。Move 只在两侧 `value_digest` 相等且 object 或 key coordinate
不同时合法。Objects-metadata fact 有 `object_count`、`metadata_entry_count`、`stream_count`、
`trailer_digest` 与 `object_digest`。

PDF rendered-pages change 的 stable top-level field order 为：

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

`operation` 是 `equal`、`insert`、`delete` 或 `update`。`page` 是 one-based。`rect` 在 whole-page
insert/delete 中为 null，否则精确字段顺序为 `page`、`x`、`y`、`width`、`height`；它使用
`raster_space` 序列化为 `pdf-raster-rect(page,x,y,width,height,dpi,colorspace)`。`raster_space`
精确字段顺序为 `page_box`、`rotation_degrees`、`dpi`、`colorspace`、`alpha_mode`、
`antialiasing`、`background`。`x`、`y`、`width` 与 `height` 是 declared rendered page raster 中的
zero-based pixel integer；`width` 与 `height` 为正，且 rectangle 必须在 bounds 内。Rendered-page
fact 有 `page`、`width_px`、`height_px`、`dpi`、`colorspace`、`alpha_mode`、`render_backend_id`
与 `raster_digest`。

每个 variant 的 operation-side rule 都是 closed：

| Operation | Before coordinate/fact | After coordinate/fact | Cardinality |
| --- | --- | --- | --- |
| `equal` | required | required | fixture-only，fact 与 payload digest 相等 |
| `insert` | null | required | 一个 after-side coordinate/fact |
| `delete` | required | null | 一个 before-side coordinate/fact |
| `update` | required | required | 一个 aligned before/after pair |
| `move` | required | required | 仅 source syntax 与 PDF text/object；stable digest 相等且 coordinate 改变 |

P6-C0 fixture 可以包含 equal fact 来证明 ordering、coordinate 与 digest，但 completed comparison
output 不把 equal operation 报告为 changed item。

Contract-only provenance 也被关闭。P6-C0 fixture 可以直接构造 completed outcome 以及 failed 或
unavailable outcome，用于 reader/writer validation。它们必须在 provenance 与 compatibility receipt
中记录已接受的 comparator 与 algorithm ID，但在 P6-S1 或 P6-P1a 开始前，任何 registry route
都不得通过 public `compare()` 或 CLI 执行这些 ID。

额外 proposed canonical vector 为：

| Domain | Tagged fields | Payload hex | SHA-256 |
| --- | --- | --- | --- |
| `source/node` | `kind=source_code_change`, `change_variant=syntax_tree`, `operation=update`, `language=python`, `before_path=/root/module#0`, `after_path=/root/module#0` | `000000000000000600000000000000046b696e640000000000000012736f757263655f636f64655f6368616e6765000000000000000e6368616e67655f76617269616e74000000000000000b73796e7461785f7472656500000000000000096f7065726174696f6e000000000000000675706461746500000000000000086c616e67756167650000000000000006707974686f6e000000000000000b6265666f72655f70617468000000000000000e2f726f6f742f6d6f64756c652330000000000000000a61667465725f70617468000000000000000e2f726f6f742f6d6f64756c652330` | `f3fdad01158fddcac7cc22eb103d0a8f27c91bbe4363209867a5656c9e2e6e9b` |
| `pdf/text/run` | `kind=pdf_change`, `view=extracted_text`, `operation=update`, `page=1`, `run=1` | `000000000000000500000000000000046b696e64000000000000000a7064665f6368616e6765000000000000000476696577000000000000000e6578747261637465645f7465787400000000000000096f7065726174696f6e0000000000000006757064617465000000000000000470616765000000000000000131000000000000000372756e000000000000000131` | `8a0e8e2e5d20577c69a226ee0f29f61b89959cd8f1034e7d138e87888d5780cb` |
| `pdf/object/entry` | `kind=pdf_change`, `view=objects_metadata`, `operation=update`, `object_ref=1 0`, `key_path=/Type` | `000000000000000500000000000000046b696e64000000000000000a7064665f6368616e676500000000000000047669657700000000000000106f626a656374735f6d6574616461746100000000000000096f7065726174696f6e0000000000000006757064617465000000000000000a6f626a6563745f726566000000000000000331203000000000000000086b65795f7061746800000000000000052f54797065` | `bca6551004edcbdbb5daf3fefb02916ffb4b3e89afc2af08c2b3514cbfb56c6b` |
| `pdf/render/region` | `kind=pdf_change`, `view=rendered_pages`, `operation=update`, `page=1`, `x=0`, `y=0`, `width=1`, `height=1` | `000000000000000800000000000000046b696e64000000000000000a7064665f6368616e6765000000000000000476696577000000000000000e72656e64657265645f706167657300000000000000096f7065726174696f6e0000000000000006757064617465000000000000000470616765000000000000000131000000000000000178000000000000000130000000000000000179000000000000000130000000000000000577696474680000000000000001310000000000000006686569676874000000000000000131` | `fc8cb8dce91350fd39803dab87bfa9971e4341df5889a6749e5964907d4727d8` |
