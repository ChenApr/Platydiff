# RFC 0010：Schema 前驱与 Phase 6 契约修订

[English documentation](0010-schema-predecessor-and-phase6-contract-amendment.md)

- Status: Proposed
- Date: 2026-09-10
- Owners: Platydiff 维护者
- Implementation owner: 尚未指派，等待人工批准

## 摘要与授权边界

本 RFC 是一个 cross-RFC 修订提案，用于处理在 Phase 5、Phase 6 或 Phase 7 schema
实现开始前发现的 schema 前驱矛盾。它只提出决策，不把任何决策标记为 Accepted，
不授权代码，不改变 public schema 行为，也不启动 structured data、image、source-code、PDF、
audio、video、SDK v2、backend worker、artifact、automatic detection 或 UI 实现。

推荐决策是：将 `main` 上缺失的 YAML、table、array schema-v3 contract surface 视为
Phase 4 代码缺陷，而不是把它当作 RFC 0006 已接受契约错误的证据。必须先落地一个
correction gate，然后 schema v4 image、schema v5 source/PDF、schema v6 audio 或后续
video successor 才能把 v3 当作稳定前驱。

## 证据

在 `origin/main` `cf3c526` 上，已实现的 schema-v3 代码公开了 `JsonCompareSpec` 与
`StructuredChange`。它没有把 `YamlCompareSpec`、`TableCompareSpec`、`ArrayCompareSpec`、
`TableChange` 或 `ArrayChange` 作为已实现的 schema-v3 public model 公开。

RFC 0006 已 Accepted，并说明 schema-v3 closed union 包含：

```text
CompareSpec | JsonCompareSpec | YamlCompareSpec | TableCompareSpec | ArrayCompareSpec
TextHunk | BinarySpan | StructuredChange | TableChange | ArrayChange | ExtensionChange
```

RFC 0006 还说明，schema-v3 field 与 fixture 在 P4-A1 实现后成为 public。它后续的
P4-A2、P4-B1、P4-B2 gate 仍分别授权且尚未实现，而这些 gate 的 commit plan 又暗示
YAML、table、array modality 工作稍后才发生。

RFC 0007 要求硬性前驱审计：如果已合并的 P4-A1 schema 与 RFC 0006 不一致，Phase 5
停止并先修订 RFC，之后才能发布 image model。RFC 0008 将 Phase 6 source/PDF 分配到
schema v5，并把完整 RFC 0006 v3 closed union 作为前驱。因此 P6-C0 无法从当前 `main`
唯一实现：实现者可以遵循已接受 RFC 0006 union，也可以遵循实际 JSON-only surface，
而这两者不是同一个契约。

仓库仍未发布，因此维护者仍有空间修正 pre-release schema implementation。但这不代表
closed-union drift 无害：一旦 writer、reader、migration fixture、下游 schema 或 release
把某个 closed union 当作前驱，再在同一 schema version 中扩展它就会制造含糊的兼容性证据。

## 提议决策

| ID | 推荐决策 | 未选择的替代方案 |
| --- | --- | --- |
| SP1 | 承认 schema-v3 前驱不一致会阻塞 P5-A1、P6-C0、P7-A1 与后续 video schema 工作，直到人工批准解决方案。 | 让下游 schema 选择方便的 v3 定义。 |
| SP2 | 选择方案 A：把缺失的 YAML/table/array schema-v3 contract 当作 Phase 4 代码缺陷，并在 schema v4 前定义 correction gate P4-C1。 | 不修订已接受 RFC，就把当前 JSON-only 代码当作完整 v3 契约。 |
| SP3 | 保持已接受的全局 allocation：v3 structured data、v4 image、v5 source/PDF、v6 audio，以及后续 video successor。 | 因为 P4-A1 合入了不完整 v3 surface 而重新编号已接受的 image/source/PDF/audio allocation。 |
| SP4 | 明确 closed union 在作为 public release 证据发布后，或在 successor 已依赖它后，不得继续扩展；发布前 P4-C1 可以修正不完整 v3 implementation，使其匹配已接受 RFC 0006。 | 允许后续 gate 需要时随意向同一 schema version 增加 closed-union 成员。 |
| SP5 | 要求下游 predecessor fixture 在 schema-v4、schema-v5 或 schema-v6 writer fixture 被接受前证明已修正的 v3 union。 | 只把设计接受当作 predecessor compatibility 证据。 |
| SP6 | 要求 P6-C0 implementation 前先接受 Phase 6 contract amendment，补齐下方 source lexical、PDF binary、coordinate、digest、identifier、problem、fact 与 `compare()` 行为缺口。 | 让 P6-C0 实现者从 private code 推断缺失 public contract 细节。 |

## 替代方案

### A. 在 v4 前设置 Phase 4 correction gate

方案 A 认为 RFC 0006 是正确的已接受契约，而当前 P4-A1 代码不完整。Correction gate
P4-C1 添加缺失的 public schema-v3 model、serializer、reader、migration 与 fixture surface：
`YamlCompareSpec`、`TableCompareSpec`、`ArrayCompareSpec`、`TableChange`、`ArrayChange`。
P4-C1 不实现 YAML、table 或 array comparator；它只让 v3 closed union 匹配已接受契约，
使后续 gate 只有一个前驱。

这是推荐方案，因为它保留已经接受的 schema allocation，也保持 RFC 0006 的 structured-data
契约完整。兼容性成本仍然存在：`main` 上已有的 v3 fixture 必须先扩展并重新验证，之后
v4/v5/v6 fixture 才能依赖它们。项目尚未发布，因此这是 pre-release 缺陷修正，而不是
public breaking change。

### B. 将 v3 重定义为 JSON-only

方案 B 修订 RFC 0006，使 schema v3 只包含 `JsonCompareSpec` 与 `StructuredChange`；
YAML、table、array 契约移动到未来的全局 schema successor。这贴合当前代码，但会在实现后
弱化已接受 RFC，并迫使维护者决定这些 structured modality 放在哪里。它们可以分配到
audio/video 之后，也可以组合进新的 structured-data successor，但任一选择都会改变
RFC 0007、RFC 0008、RFC 0009 的前驱图。

因为项目尚未发布，方案 B 在技术上可行。但除非人工确认 RFC 0006 已接受契约过宽，否则
不推荐。它需要明确 migration note、更新 RFC 0006 status text、修订 Phase 5/6/7 predecessor
语言，并用兼容性测试证明旧 pre-release v3 JSON fixture 仍有效，而移除的 YAML/table/array
名称不会被 v3 接受。

### C. 增加第二套 schema-extension 机制

方案 C 保持 numeric schema v3 为 JSON-only，但为 YAML、table、array 增加单独的 structured
contract revision 或 capability-extension namespace。它避免重编号，却制造两个 version axis。
它还会削弱 RFC 0006 到 RFC 0009 使用的 closed-union discipline：reader 需要同时查看
`schema_version` 与 extension membership 才能判断哪些 built-in spec 与 change 名称合法。

只有当项目有意离开 schema-versioned closed union 时，方案 C 才是连贯的。对于当前
pre-release codebase，不推荐该方案。

## P4-C1 correction gate

如果方案 A 被接受，P4-C1 是任何 schema v4/v5/v6 implementation gate 前必须完成的
correction gate：

1. `fix(core): complete schema-v3 structured contract models`
2. `fix(core): complete schema-v3 reader writer and migration validation`
3. `test(core): add schema-v3 YAML table array contract fixtures`
4. `docs(rfc): record schema-v3 predecessor correction evidence`

Gate：从更新后的 `main` 独立授权；不实现 YAML、table 或 array comparator 行为；不新增 CLI
route、detector、plugin SDK、artifact 或 renderer feature；`git diff --check`、formatting、lint、
strict type checking、完整测试、schema-v1/v2/v3 compatibility fixture、unknown-kind rejection
与 public-export check 全部通过。P5-A1、P6-C0、P7-A1 与后续 video schema gate 必须等待
P4-C1，或者等待本 RFC 中另一个方案被接受。

## P6-C0 契约修订

即使 v3 前驱决策已经解决，P6-C0 仍会被下列 public contract 细节阻塞。这些是 Phase 6
修订的提议决策 ID，不是实现授权。

| ID | 提议决策 | 未选择的替代方案 |
| --- | --- | --- |
| P6C0-1 | 用 source-specific change kind 表示 source `lexical_text` difference；它嵌入 RFC 0002 text range，并记录 source coordinate context；不要把裸 `TextHunk` 直接作为 source-code change。 | 让 lexical source output 与普通 text output 无法区分。 |
| P6C0-2 | 用 PDF-specific binary-span change discriminator 表示 PDF binary difference，记录 PDF document identity 与 zero-based half-open byte range；不要在没有 PDF discriminator 时复用裸 `BinarySpan`。 | 让 PDF binary view 产出 renderer 无法与普通 binary comparison 区分的 generic binary change。 |
| P6C0-3 | 规范定义 coordinate base 与 grammar：byte 是 zero-based half-open offset；source line/column fact 说明 encoding，以及 column 是 code-point 还是 byte based；PDF page number、object reference、stream range 与 rendered pixel rectangle 各有一个 grammar；rendered pixel rectangle 位于显式声明 raster space 中，使用 zero-based half-open。 | 把 coordinate base 与 grammar 留给各 backend。 |
| P6C0-4 | 在任何 renderer backend 前先在 schema contract 中定义 render bound：maximum pages、rendered pages、pixels per page、decoded bytes、temp bytes、backend seconds、worker output bytes、peak RSS、concurrent workers 与 spawned process count 都有有限 accounting rule。 | 只在 backend 文档中描述 render limit。 |
| P6C0-5 | 为 source fact、PDF fact、rendered-page fact 与 change payload 定义精确 digest framing，包括 domain string、canonical byte framing、hash algorithm 与 normative test vector。 | 只用非正式文字引用 RFC 0006 digest，不给 vector。 |
| P6C0-6 | 在任何 source/PDF writer 发布前，为 summary key、resource counter、transformation ID、comparator ID、algorithm ID、metric name 与 problem code 预留 stable lowercase ASCII ID。 | 让 implementation 临时创造 ID。 |
| P6C0-7 | 精确定义 encrypted PDF 行为：`views=("binary",)` 忽略 encryption 并比较字节；任一 selected nonbinary view 遇到任一 encrypted input，都产生顶层 `failed` outcome，`stage="decoding"`，registry ID 为 `schema-v5/pdf_encrypted`，serialized code 为 `pdf_encrypted`，且没有 `DiffResult`。 | 把 encryption 折叠成 generic decode failure，或让 encryption 行为依赖 policy。 |
| P6C0-8 | 定义 worker problem detail：timeout、resource exhaustion、crash、protocol violation、invalid output、stderr overflow、temp overflow、decoded-output overflow、RSS overflow 与 spawn-limit overflow；每个都有稳定 status 与安全 detail shape。 | 把 backend-specific string 直接作为 problem detail 返回。 |
| P6C0-9 | 定义 fact presence invariant：每个 selected 且 successful 的 view 都发出其 required fact、metric、summary、resource 与 transformation；每个 unselected view 按规定 absent 或显式 null；failed 或 unavailable view 不伪造空 fact。 | 允许没有 schema-level invariant 的 partial fact。 |
| P6C0-10 | P6-C0 保持 models/serialization only：source/PDF 的 public `compare()` 与 CLI 行为直到 P6-S1 或 P6-P1a 才可用。P6-C0 fixture 可以直接构造 unavailable outcome 用于 reader/writer validation，但不得暴露可运行 source/PDF comparator route。 | 在 P6-C0 添加返回 unavailable 的 source/PDF `compare()` 行为。 |

### 提议的 schema-v5 public shape

这些 shape 属于 Proposed amendment。它们刻意具体到足以支持后续 P6-C0 implementation review，
但在本 RFC 或后继 RFC 被 Accepted 前仍未授权。

Source lexical change 使用 discriminator `kind="source_lexical_text_hunk"`，稳定 field order 为：

```text
kind
source_id
language
relation
coordinate_encoding
before_range
after_range
text
payload_digest
```

`source_id` 是 snapshot 层提供的安全 source label。`language` 是显式 spec language。
`relation` 是 `lexical_text`。`coordinate_encoding` 是 `utf-8`。`before_range` 与
`after_range` 是 nullable range object，字段为 `start_byte`、`end_byte`、`start_line`、
`start_column`、`end_line`、`end_column`。Byte offset 是 decoded byte sequence 中的
zero-based half-open offset。Line 是 one-based。Column 默认是 one-based Unicode scalar value
column，除非显式出现 `column_unit="utf8_byte"`。`text` 包含 RFC 0002 hunk payload field：
`before_lines`、`after_lines`、`line_ending`，不包含 raw source byte。

PDF binary change 使用 discriminator `kind="pdf_binary_span"`，稳定 field order 为：

```text
kind
view
document_id
ranges
payload_digest
```

`view` 必须是 `binary`。`document_id` 是 `before`、`after`，或当 span 映射到双方时为
`both`。每个 range 有 `side`、`start_byte`、`end_byte`；byte offset 是 original PDF bytes
上的 zero-based half-open offset，位于 parsing、decryption、repair 或 decompression 之前。
即使报告相同 byte range，它也不同于 generic `BinarySpan`。

Coordinate grammar 为：

| Coordinate | Grammar | Base |
| --- | --- | --- |
| Source bytes | `source-byte-range(start,end)` | zero-based half-open decoded UTF-8 bytes |
| Source text | `source-text-range(line,column,line,column,column_unit)` | one-based lines and columns |
| PDF bytes | `pdf-byte-range(start,end)` | zero-based half-open original bytes |
| PDF object | `pdf-object(obj,generation)` | PDF 中存储的 object 与 generation number |
| PDF page | `pdf-page(number)` | document catalog resolution 后的一基 logical page number |
| PDF stream | `pdf-stream(obj,generation,start,end)` | object identity 加 zero-based half-open decoded stream byte |
| Rendered pixels | `pdf-raster-rect(page,x,y,width,height,dpi,colorspace)` | declared rendered page space 中的 zero-based raster pixel |

Canonical view ordering 是 `binary`、`extracted_text`、`objects_metadata`、`rendered_pages`。
每个 view 内，fact 与 change 按 before coordinate、after coordinate、discriminator、
`payload_digest` 排序；absent coordinate 排在 present coordinate 之后。

### Digest framing 与 vector

Schema-v5 digest framing 为：

```text
sha256(
  b"platydiff\0schema-v5\0"
  + ascii_domain
  + b"\0"
  + canonical_json_bytes
)
```

`canonical_json_bytes` 是 UTF-8 JSON bytes，object key 排序、无无意义空白，并使用 checked
integer formatting。Normative empty object vector 为：

| Domain | 使用 `\0` escape 展示的 framed bytes | SHA-256 |
| --- | --- | --- |
| `source.fact` | `platydiff\0schema-v5\0source.fact\0{}` | `1883c8b8971db03c909ca8c27569afe787ccf17a11cf1e1c1e9d22b5c0e57c4a` |
| `source.change_payload` | `platydiff\0schema-v5\0source.change_payload\0{}` | `40b2ec6b43958055c88ef2be025bef108bc8ba233cd2035d42135970dd94ebfa` |
| `pdf.fact` | `platydiff\0schema-v5\0pdf.fact\0{}` | `9089cd53f93ba5548178bfd7cc85cd568392498f1a6ce22bd33353335855134d` |
| `pdf.rendered_page.fact` | `platydiff\0schema-v5\0pdf.rendered_page.fact\0{}` | `ad3d89a46b566d702239423b52d6f8de0bdcb33e8de56e0a79abca17b1c0db79` |
| `pdf.change_payload` | `platydiff\0schema-v5\0pdf.change_payload\0{}` | `07b1d508a7ec6dd7c4f1dde06ae52322d4c9298ffadd9bff8113cc78d0fc9bb9` |

### Stable ID 与 counter

P6-C0 预留以下 stable lowercase ASCII ID：

- comparator ID：`source.lexical_text`、`source.syntax_tree`、
  `source.semantic_unavailable`、`pdf.binary`、`pdf.extracted_text`、
  `pdf.objects_metadata`、`pdf.rendered_pages`；
- transformation ID：`source.decode_utf8`、`source.normalize_newlines`、
  `source.lexical_tokenize_lines`、`pdf.read_original_bytes`、`pdf.parse_xref`、
  `pdf.extract_text_runs`、`pdf.enumerate_objects`、`pdf.render_page`；
- metric ID：`source.changed_hunks`、`source.changed_ranges`、
  `pdf.binary_changed_spans`、`pdf.text_changed_runs`、
  `pdf.object_changed_records`、`pdf.render_changed_pixels`；
- summary key：`changed_items`、`added_items`、`removed_items`、
  `modified_items`、`moved_items`、`truncated`、`selected_views`；
- resource counter：`input_bytes`、`fact_text_bytes`、`fact_value_bytes`、
  `compare_work`、`change_items`、`change_payload_bytes`、
  `pdf_backend_seconds`、`pdf_stdout_stderr_bytes`、`pdf_temp_bytes`、
  `pdf_decoded_bytes`、`pdf_worker_output_bytes`、`pdf_peak_worker_rss_bytes`、
  `pdf_peak_concurrent_worker_processes`、`pdf_worker_processes_spawned`。

### Problem registry

新的 schema-v5 problem code 使用 scoped registry key `schema-v5/<code>` 注册，而 serialized
`problem.code` 保持短 stable code。P6-C0 预留：

| Registry ID | Serialized status/code | Stage | Detail keys |
| --- | --- | --- | --- |
| `schema-v5/pdf_encrypted` | `failed/pdf_encrypted` | `decoding` | `input_side`, `view`, `encryption_detected=true` |
| `schema-v5/pdf_worker_timeout` | `failed/pdf_worker_timeout` | observed worker stage | `view`, `limit`, `elapsed_seconds` |
| `schema-v5/pdf_worker_resource_exhausted` | `failed/pdf_worker_resource_exhausted` | observed worker stage | `view`, `resource`, `limit`, `actual` |
| `schema-v5/pdf_worker_crash` | `failed/pdf_worker_crash` | observed worker stage | `view`, `exit_status` |
| `schema-v5/pdf_worker_protocol_violation` | `failed/pdf_worker_protocol_violation` | `decoding` or `rendering` | `view`, `message_kind` |
| `schema-v5/pdf_worker_invalid_output` | `failed/pdf_worker_invalid_output` | `decoding` or `rendering` | `view`, `field` |
| `schema-v5/source_coordinate_invalid` | `failed/source_coordinate_invalid` | `serializing` | `field`, `reason` |
| `schema-v5/pdf_coordinate_invalid` | `failed/pdf_coordinate_invalid` | `serializing` | `field`, `reason` |

`pdf_encrypted` 不用于 pure binary view。任一 selected nonbinary view 遇到任一 encrypted input
时，整个 all-or-nothing PDF invocation failed，不产生 `DiffResult`，也不 fallback 到 binary。

### Fact presence 与 ordering

Completed source/PDF schema-v5 outcome 必须为每个 selected relation 或 view 发出全部 required
spec、fact、metric、summary、resource、transformation、comparator、algorithm 与 digest field。
Unselected optional view 只有在 RFC 0008 明确定义 nullable option object 时才序列化为 `null`；
其他情况下 absent。Failed 或 unavailable outcome 不包含 `DiffResult`；如果 execution model
存在 attempt field，partial view fact 只能出现在 execution attempt 中。

Reader validation 会拒绝 selected view fact 的非 canonical order、重复 summary 或 metric ID、
unknown schema-v5 problem registry ID、未 scoped 的新 problem code、缺失 required counter、
digest/domain mismatch、非 canonical coordinate，以及任何在 P6-C0 payload 中暴露 public
source/PDF `compare()` 或 CLI 行为的内容。

## Migration 与兼容性测试

任何被接受的解决方案都必须添加以下测试：

- 精确 v1/v2/v3 reader 与 writer compatibility，包括 unknown schema 与 unknown built-in kind
  rejection；
- 每个已接受 schema-v3 built-in spec 与 change 名称都可 canonical round trip，即使 comparator
  行为仍设门禁；
- v1/v2 到已修正 v3 的 migration 不改变 legacy outcome meaning；
- v4/v5/v6 gate 复用 predecessor fixture，且这些 successor fixture 被接受后不得重写 v3 byte；
- P6-C0 source/PDF schema fixture 覆盖 unavailable 与 failed outcome、selected 与 unselected
  view、resource accounting、transformation、summary、metric、problem detail、digest vector
  与 coordinate example；
- 证明 P6-C0 不新增 public `compare()` 或 CLI source/PDF 行为。

如果接受方案 B 或 C 而不是方案 A，migration test 还必须证明被移除或迁移的 YAML/table/array
v3 名称会以稳定 problem 被拒绝，并且 successor allocation 在代码前已写入文档。

## 需要人工决策

人工 reviewer 必须决定：

1. 已接受 RFC 0006 是否仍是期望的 schema-v3 契约？
2. P4-C1 是否应在 schema v4 前修正当前代码以匹配 RFC 0006，或者 RFC 0006 应被修订为
   JSON-only v3？
3. 在任何 successor 依赖它们之前，是否允许扩展 pre-release schema-v3 fixture，以及
   no-later-extension 边界在哪里？
4. v4 image、v5 source/PDF、v6 audio 与后续 video successor 的全局 allocation 是否仍正确？
5. P6-C0 implementation 前，P6C0-1 到 P6C0-10 是否是正确的契约决策？

在这些决策被接受前，本 RFC 只是提案，任何下游 schema implementation 都不应把当前 v3
前驱视为已定。
