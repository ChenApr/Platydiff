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
extra key、错误 type 与非 canonical key order。Detail key 列为 `none` 表示 canonical `details`
值为空 object。Retryability 列为 raised value 表示保留 originating domain error 携带的 retryability
flag。

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

对 observing stage row，`stage` 是 stable snapshot 检测到变化的阶段：`detecting`、`decoding`、
`comparing` 或 `aggregating`。对 action stage row，`stage` 由 failed action 或 exceeded resource
决定：source 或 PDF input byte 在 `sourcing`
失败；decoded source char、source fact text byte、parser node count、PDF decoded stream、PDF text
run、PDF object entry 与 nonrender worker output 在 `decoding` 失败；rendered page count、rendered
pixel、rendered-page worker output、rendered-page temp byte 与 rendered-page RSS 在 `decoding`
失败；comparator-local I/O 在 `comparing` 失败。对 view worker stage row，`extracted_text`、
`objects_metadata` 与 `rendered_pages` 的 `stage` 都是 `decoding`；pure `binary` view 没有 worker
stage。

Closed detail value type 为：

- `source_relation`：`lexical_text` 或 `syntax_tree`；
- `view`：`binary`、`extracted_text`、`objects_metadata` 或 `rendered_pages`；
- `relation_or_view`：一个 source relation 或 PDF view name；
- `input_side`：`before` 或 `after`；
- `source_kind`：`path`、`bytes` 或 `text`；
- `source_ref`：bounded safe source label 或 null；
- `actual_source_type`：stable source type identifier；built-in 是 `path`、`bytes` 与 `text`，
  extension 必须使用 namespaced identifier；
- `supported_source_types`：stable source type identifier 的 non-empty array；
- `spec_kind`：stable spec discriminator；
- `backend_role`：`parser`、`text_extractor`、`object_reader` 或 `renderer`；
- `operation`：`stat`、`open`、`read`、`decode`、`snapshot_check` 或 `compare`；
- `encoding`：stable encoding label，或没有 label 时为 null；
- `supported_encodings`：stable encoding label 的 non-empty array；
- `observed_stage`：`detecting`、`decoding`、`comparing` 或 `aggregating`；
- `language`、`backend_id`、`capability_id`、`reason_code`、`message_code`、
  `resource`、`stream` 与 `message_kind`：stable lowercase ASCII identifier，只有表中允许
  nullable 的字段可以是 null；
- `line`、`column`、`used`、`limit`、`actual`、`limit_bytes`、`actual_bytes`、
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

`operation` 是 `equal`、`insert`、`delete` 或 `update`。`insert` 的 `before_range` 与
`before_fact` 为 null；`delete` 的 `after_range` 与 `after_fact` 为 null；`update` 两侧都有；
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
`insert` 的 range 全部是 `after` side；`delete` 的 range 全部是 `before` side；`update` 至少包含一个
`before` range 与一个 `after` range；`equal` fixture range 精确包含一个 `before` range 和一个
`after` range，且 byte length 相等。因为 range object 不携带 per-range content digest，detached
reader 只验证 binary range structure、side membership、ordering、cardinality 与 length；当 named
before/after binary fact 存在时，binary byte equality 从这些 fact 验证。Binary fact 是 non-parsing
fact，精确字段顺序为
`byte_length`、`header_prefix`、`content_digest`。
`header_prefix` 要么是 null，要么是通过在 offset zero byte-sniff `%PDF-` 得到的 bounded ASCII
prefix；binary fact 不包含 encryption、xref、trailer、object 或 page count。

PDF extracted-text change 的 stable top-level field order 为：

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

`operation` 是 `equal`、`insert`、`delete`、`update` 或 `move`。`before_run` 与 `after_run`
要么是 null，要么是精确字段顺序为 `page`、`run`、`start_text_offset`、`text_length` 的 object。
Text-run coordinate 使用 `pdf-text-run(page,run,start_offset,end_offset)`，其中 `page` 是
one-based，`run` 是 canonical extraction order 中的 zero-based ordinal，offset 是 extracted
run text 中的 zero-based half-open Unicode scalar offset。`text` 在 `digest_only` mode 中为 null，
否则是包含 `before_text` 与 `after_text`、并受 `max_fact_text_bytes` 限制的 object。
在 facts mode 中，`before_text` 为 null 当且仅当 `before_run` 为 null，`after_text` 为 null 当且仅当
`after_run` 为 null。`before_text_digest` 为 null 当且仅当 `before_run` 为 null；`after_text_digest`
为 null 当且仅当 `after_run` 为 null。非 null text-run digest 使用已接受的 `pdf/text/run` frame，
基于对应 side 的 page、run、text byte、extractor flag 与 text span 计算；当 `digest_only` mode 中
`text` 为 null 时它们仍然存在。`insert` 的 `before_run`、`before_text_digest` 与 `before_text` 为
null；`delete` 的 `after_run`、`after_text_digest` 与 `after_text` 为 null；`update` 两侧在同一 page
上有 aligned text coordinate，且 text-run digest 不相等；`move` 两侧在同一 page 上都有 run，
text-run digest 相等，且 `(run, start_text_offset)` 改变。Cross-page text movement 以 delete plus
insert 表示，以保留 RFC 0008 page-local text alignment。Extracted-text fact 有 `page_count`、`run_count`、
`char_count`、`extraction_digest` 与 `backend_id`。

PDF objects-metadata change 的 stable top-level field order 为：

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

`operation` 是 `equal`、`insert`、`delete`、`update` 或 `move`。Object reference field 只有对
document-level metadata 才是 null；否则精确字段顺序为 `object_number`、
`generation`，并序列化为 `pdf-object(obj,generation)`。Key path 是 canonical metadata object
上的 RFC 6901 JSON Pointer。`before_entry` 与 `after_entry` 要么是 null，要么是精确字段顺序为
`entry_kind`、`type_name`、`value`、`value_digest`、`byte_length` 的 object。`entry_kind` 是
`dictionary_entry`、`array_item`、`stream_dictionary_entry` 或 `document_metadata_entry`；
`type_name` 是 `null`、`boolean`、`integer`、`real`、`name`、`string`、`array`、`dictionary`
或 `stream`。`value` 是 canonical bounded JSON，object key 排序，array 顺序与 PDF fact domain
一致，最大 nesting depth 为 16，不含 non-finite number，也不含 backend-private object。在
`digest_only` mode 中，`value` 为 null 且 `value_digest` 必须存在。当 `value` 非 null 时，
`value_digest` 必须等于该 canonical value 的 digest；可获得原始 encoded value byte length 时，
`byte_length` 必须等于该长度。`insert` 的 before object/key/entry field 为 null；`delete` 的 after
object/key/entry field 为 null；`update` 两侧都有 aligned entry coordinate，且 `value_digest` 不等；
`move` 两侧都有 before 与 after object/key coordinate，`value_digest` 相等，且 object 或 key
coordinate 改变。Objects-metadata fact 有 `object_count`、`metadata_entry_count`、`stream_count`、
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
zero-based pixel integer；`width` 与 `height` 为正，且 rectangle 必须在 bounds 内。当 `rect`
非 null 时，top-level `page`、`rect.page` 与每个 side 的 rendered-page fact `page`
必须相等。`page_box` 是 `media` 或 `crop`；`rotation_degrees` 是 `0`、`90`、`180` 或 `270`；
`dpi` 是 positive integer；`colorspace` 是 `srgb`、`gray` 或 `display_p3`；`alpha_mode` 是
`opaque` 或 `premultiplied`；`antialiasing` 是 `none`、`grayscale` 或 `subpixel`；`background`
是六位 lowercase hex RGB string 或 null。Rendered-page fact 有 `page`、`width_px`、`height_px`、
`dpi`、`colorspace`、`alpha_mode`、`render_backend_id` 与 `raster_digest`。它们的 `dpi`、
`colorspace` 与 `alpha_mode` 必须匹配 `raster_space`，且 `raster_digest` 必须是对应 side 在声明
raster-space 中 pixel 的 digest。

每个 variant 的 operation-side rule 都是 closed。表中的 coordinate/fact 指该 variant 的实际
before/after field：source lexical range 与 fact；source syntax path、node、range 与 fact；PDF
binary range side 与 fact；PDF text run、text side 与 fact；PDF object reference、key path、
entry 与 fact；以及 PDF raster rect 与 rendered-page fact。

| Operation | Before coordinate/fact | After coordinate/fact | Cardinality |
| --- | --- | --- | --- |
| `equal` | required | required | fixture-only；该 variant 的 named before/after fact 相等，且单个 `payload_digest` 是 canonical change payload 的有效 digest |
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

额外 proposed canonical vector 使用已接受的 RFC 0008 frame；如果被接受，会针对 P6 source/PDF
compatibility fixture supersede RFC 0010 中使用 `range_variant` 的过时 `source/change_payload`
vector，以及使用 `span_variant` 的过时 `pdf/binary/span` vector。RFC 0010 在本 amendment 被接受前
仍是 accepted historical baseline。下列表格不是旧 payload 的 replacement hash；每行定义一个与已接受
domain component 匹配的 coherent fact-domain payload。

Generation and check algorithm：

```text
payload =
  U64BE(field_count) ||
  for each listed field in order:
    U64BE(tag_length) || UTF8(tag) || U64BE(value_length) || value_bytes

frame =
  UTF8("platydiff/v5/" + domain) || 0x00 || U64BE(payload_length) || payload

SHA-256 = SHA256(frame)
```

检查 vector 时，decode payload hex，用 domain 与 payload length 重建 frame，并把 SHA-256 column
与 `SHA256(frame)` 比较。
对于 change-payload domain，field-path tag 按 stable field-order traversal 展开 nested value。Change
object 的 `payload_digest` field 不进入被 hash 的 payload，以避免递归；`payload_digest` 存储该算法
产生的 digest。
Scalar `value_bytes` 使用 RFC 0010 rule。Sequence field 使用 nested list framing，而不是 repeated
tag、delimiter 或 JSON：

```text
list_value =
  U64BE(element_count) ||
  for each element in order:
    U64BE(element_length) || element_value_bytes
```

`source/node` 对 `child_field_names`、`ordered_child_digests`、`retained_token_digests` 与
`retained_trivia_digests` 使用 list framing。Empty list 编码为 `U64BE(0)`。`pdf/text/run` 把
`extractor_flags` 编码为 closed flagset frame，而不是 delimited string：

```text
flagset_value =
  U64BE(entry_count) ||
  for each registry key in canonical order:
    U64BE(key_length) || UTF8(key) || boolean_byte
```

Initial flag registry 与 canonical order 是 `backend_tounicode`、`ligatures_preserved`、
`vertical_writing`。`boolean_byte` 用 `0x00` 表示 false，用 `0x01` 表示 true。Key 是 stable
lowercase ASCII identifier；每个 key 都 length-framed，因此不使用 escaping 或 delimiter convention。

| Domain | Tagged fields | Payload hex | SHA-256 |
| --- | --- | --- | --- |
| `source/node` | `language=python`, `node_kind=module`, `child_field_names=[]`, `ordered_child_digests=[]`, `retained_token_digests=[]`, `retained_trivia_digests=[]` | `000000000000000600000000000000086c616e67756167650000000000000006707974686f6e00000000000000096e6f64655f6b696e6400000000000000066d6f64756c6500000000000000116368696c645f6669656c645f6e616d65730000000000000008000000000000000000000000000000156f7264657265645f6368696c645f6469676573747300000000000000080000000000000000000000000000001672657461696e65645f746f6b656e5f6469676573747300000000000000080000000000000000000000000000001772657461696e65645f7472697669615f6469676573747300000000000000080000000000000000` | `c4de32de8c4cc95b9808a79cdce30ec5b20304b9ecb83efe719fa271f8f268dd` |
| `source/node` | `language=python`, `node_kind=function_definition`, `child_field_names=[decorator,body]`, `ordered_child_digests=[sha256:1111111111111111111111111111111111111111111111111111111111111111,sha256:2222222222222222222222222222222222222222222222222222222222222222]`, `retained_token_digests=[sha256:3333333333333333333333333333333333333333333333333333333333333333,sha256:4444444444444444444444444444444444444444444444444444444444444444]`, `retained_trivia_digests=[sha256:5555555555555555555555555555555555555555555555555555555555555555,sha256:6666666666666666666666666666666666666666666666666666666666666666]` | `000000000000000600000000000000086c616e67756167650000000000000006707974686f6e00000000000000096e6f64655f6b696e64000000000000001366756e6374696f6e5f646566696e6974696f6e00000000000000116368696c645f6669656c645f6e616d65730000000000000025000000000000000200000000000000096465636f7261746f720000000000000004626f647900000000000000156f7264657265645f6368696c645f6469676573747300000000000000a6000000000000000200000000000000477368613235363a3131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313100000000000000477368613235363a32323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232000000000000001672657461696e65645f746f6b656e5f6469676573747300000000000000a6000000000000000200000000000000477368613235363a3333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333300000000000000477368613235363a34343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434343434000000000000001772657461696e65645f7472697669615f6469676573747300000000000000a6000000000000000200000000000000477368613235363a3535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353535353500000000000000477368613235363a36363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636` | `d69b660503f4c010d386e73f15a483b99b5a92e70caa1643502584b3906fe3fc` |
| `pdf/text/run` | `page=1`, `run=0`, `text=Test`, `extractor_flags={backend_tounicode=false,ligatures_preserved=true,vertical_writing=false}`, `start_text_offset=0`, `text_length=4` | `0000000000000006000000000000000470616765000000000000000131000000000000000372756e000000000000000130000000000000000474657874000000000000000454657374000000000000000f657874726163746f725f666c6167730000000000000057000000000000000300000000000000116261636b656e645f746f756e69636f64650000000000000000136c69676174757265735f707265736572766564010000000000000010766572746963616c5f77726974696e6700000000000000001173746172745f746578745f6f6666736574000000000000000130000000000000000b746578745f6c656e677468000000000000000134` | `bd597ba903a5a6ed7c45672420212e141cd31ef0d03d5fa2f73380cbcf833d2f` |
| `pdf/object/entry` | `object_number=1`, `generation=0`, `key_path=/Type`, `type_name=name`, `canonical_value_bytes=/Catalog` | `0000000000000005000000000000000d6f626a6563745f6e756d626572000000000000000131000000000000000a67656e65726174696f6e00000000000000013000000000000000086b65795f7061746800000000000000052f547970650000000000000009747970655f6e616d6500000000000000046e616d65000000000000001563616e6f6e6963616c5f76616c75655f627974657300000000000000082f436174616c6f67` | `3ddea5707609a6d92c3f8febd1b3338a74b5a02484e32a6f639fe34aabec393b` |
| `pdf/render/region` | `page=1`, `page_box=media`, `rotation_degrees=0`, `dpi=72`, `colorspace=srgb`, `alpha_mode=opaque`, `antialiasing=grayscale`, `background=ffffff`, `x=0`, `y=0`, `width=1`, `height=1`, `before_digest=sha256:7777777777777777777777777777777777777777777777777777777777777777`, `after_digest=sha256:8888888888888888888888888888888888888888888888888888888888888888`, `changed_pixel_count=1` | `000000000000000f0000000000000004706167650000000000000001310000000000000008706167655f626f7800000000000000056d656469610000000000000010726f746174696f6e5f64656772656573000000000000000130000000000000000364706900000000000000023732000000000000000a636f6c6f727370616365000000000000000473726762000000000000000a616c7068615f6d6f646500000000000000066f7061717565000000000000000c616e7469616c696173696e670000000000000009677261797363616c65000000000000000a6261636b67726f756e640000000000000006666666666666000000000000000178000000000000000130000000000000000179000000000000000130000000000000000577696474680000000000000001310000000000000006686569676874000000000000000131000000000000000d6265666f72655f64696765737400000000000000477368613235363a37373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737373737000000000000000c61667465725f64696765737400000000000000477368613235363a3838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383838383800000000000000136368616e6765645f706978656c5f636f756e74000000000000000131` | `3a974c20b539430366f6ef35367c6354d81ba093db13d3e45caca6bed848d77d` |
| `source/change_payload` | `kind=source_code_change`, `change_variant=lexical_text`, `operation=update`, `language=python`, `relation=lexical_text`, `coordinate_encoding=utf8_byte_offsets`, `column_unit=unicode_scalar`, `before_range.start_byte=0`, `before_range.end_byte=4`, `after_range.start_byte=0`, `after_range.end_byte=5`, `before_fact_digest=sha256:9999999999999999999999999999999999999999999999999999999999999999`, `after_fact_digest=sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | `000000000000000d00000000000000046b696e640000000000000012736f757263655f636f64655f6368616e6765000000000000000e6368616e67655f76617269616e74000000000000000c6c65786963616c5f7465787400000000000000096f7065726174696f6e000000000000000675706461746500000000000000086c616e67756167650000000000000006707974686f6e000000000000000872656c6174696f6e000000000000000c6c65786963616c5f746578740000000000000013636f6f7264696e6174655f656e636f64696e670000000000000011757466385f627974655f6f666673657473000000000000000b636f6c756d6e5f756e6974000000000000000e756e69636f64655f7363616c617200000000000000176265666f72655f72616e67652e73746172745f6279746500000000000000013000000000000000156265666f72655f72616e67652e656e645f62797465000000000000000134000000000000001661667465725f72616e67652e73746172745f62797465000000000000000130000000000000001461667465725f72616e67652e656e645f6279746500000000000000013500000000000000126265666f72655f666163745f64696765737400000000000000477368613235363a39393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939393939000000000000001161667465725f666163745f64696765737400000000000000477368613235363a61616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161616161` | `55eba1386fcbda85a62ced49871a9669a16f2b81f7e3ef598c701b7cc8e12930` |
| `pdf/change_payload` | `kind=pdf_change`, `view=binary`, `binary_variant=byte_ranges`, `operation=update`, `ranges.0.side=before`, `ranges.0.start_byte=0`, `ranges.0.end_byte=4`, `ranges.1.side=after`, `ranges.1.start_byte=0`, `ranges.1.end_byte=5`, `before_fact_digest=sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`, `after_fact_digest=sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc` | `000000000000000c00000000000000046b696e64000000000000000a7064665f6368616e6765000000000000000476696577000000000000000662696e617279000000000000000e62696e6172795f76617269616e74000000000000000b627974655f72616e67657300000000000000096f7065726174696f6e0000000000000006757064617465000000000000000d72616e6765732e302e7369646500000000000000066265666f7265000000000000001372616e6765732e302e73746172745f62797465000000000000000130000000000000001172616e6765732e302e656e645f62797465000000000000000134000000000000000d72616e6765732e312e7369646500000000000000056166746572000000000000001372616e6765732e312e73746172745f62797465000000000000000130000000000000001172616e6765732e312e656e645f6279746500000000000000013500000000000000126265666f72655f666163745f64696765737400000000000000477368613235363a62626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262626262000000000000001161667465725f666163745f64696765737400000000000000477368613235363a63636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363` | `5a85bcf47212f8896206c34a07822d47e64ebdf3480ab751c87814477a1ad9f9` |
