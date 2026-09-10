# RFC 0010：Schema 前驱与 Phase 6 契约修订

[English documentation](0010-schema-predecessor-and-phase6-contract-amendment.md)

- Status: Accepted
- Date: 2026-09-10
- Accepted: 2026-09-10
- Approved decisions: SP1-SP6; Option A/P4-C1; P6C0-1-P6C0-10
- Approved P4-C1 clarifications：P4C1-1-P4C1-5
- P4-C1 clarification approval date：2026-09-10
- Accepted P6-C0 closure amendment：RFC 0014；contract-only 且不授权实现
- Owners: Platydiff 维护者
- Implementation dispatch：P4-C1 此后已合并；后续 schema work 仍需要指定 predecessor
  gate 与明确 human dispatch

## 摘要与授权边界

本 RFC 是已接受的 cross-RFC amendment，用于处理在 Phase 5、Phase 6 或 Phase 7 schema
实现开始前发现的 schema 前驱矛盾。它接受 SP1-SP6，选择 Option A/P4-C1，并接受
P6C0-1 到 P6C0-10 作为 Phase 6 contract decision。RFC acceptance 本身不启动代码。已记录
条件人工授权，coordinator 只有在指定 merge gate 之后才能派发。本文档接受 PR 不授权依赖
变更、public schema implementation，也不启动 structured data、image、source-code、PDF、audio、
video、SDK v2、backend worker、artifact、automatic detection 或 UI 实现。

一次 P4-C1 pre-implementation 只读检查发现了额外的 schema-v3 reader 与 fixture 歧义。
下方 P4C1-1 到 P4C1-5 已于 2026-09-10 获批。它们补充但不修改 SP1-SP6、
Option A/P4-C1 或 P6C0-1 到 P6C0-10。本 clarification approval 不启动任何代码。

一次 P6-C0 closure review 还发现 schema-v5 problem registry 与 closed-union shape 仍有缺口。
[RFC 0014](0014-phase6-source-pdf-contract-closure-amendment_zh.md) 接受 contract-only closure
amendment。它不修改 P6C0-1 到 P6C0-10，也不授权 source 或 PDF 实现。

已接受决策是：将 `main` 上缺失的 YAML、table、array schema-v3 contract surface 视为
Phase 4 代码缺陷，而不是把它当作 RFC 0006 已接受契约错误的证据。必须先落地一个
correction gate，然后 schema v4 image、schema v5 source/PDF、schema v6 audio 或后续
video successor 才能把 v3 当作稳定前驱。该 P4-C1 correction 此后已通过 PR #20 合并到
`main`。P5-A1 contract closure 已在 RFC 0013 中接受，但 P5-A1 仍未实现；P6-C0、P7-A1
与后续 video schema work 仍取决于实际 predecessor merge、compatibility fixture 与明确
human dispatch。

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

## 已批准决策

| ID | 已接受决策 | 未选择的替代方案 |
| --- | --- | --- |
| SP1 | 承认 schema-v3 前驱不一致会阻塞 P5-A1、P6-C0、P7-A1 与后续 video schema 工作，直到 P4-C1 或显式接受的后继解决方案合并。 | 让下游 schema 选择方便的 v3 定义。 |
| SP2 | 选择 Option A：把缺失的 YAML/table/array schema-v3 contract 当作 Phase 4 代码缺陷，并在 schema v4 前定义 correction gate P4-C1。 | 不修订已接受 RFC，就把当前 JSON-only 代码当作完整 v3 契约。 |
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

该已接受方案保留已经接受的 schema allocation，也保持 RFC 0006 的 structured-data
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
不选择。它需要明确 migration note、更新 RFC 0006 status text、修订 Phase 5/6/7 predecessor
语言，并用兼容性测试证明旧 pre-release v3 JSON fixture 仍有效，而移除的 YAML/table/array
名称不会被 v3 接受。

### C. 增加第二套 schema-extension 机制

方案 C 保持 numeric schema v3 为 JSON-only，但为 YAML、table、array 增加单独的 structured
contract revision 或 capability-extension namespace。它避免重编号，却制造两个 version axis。
它还会削弱 RFC 0006 到 RFC 0009 使用的 closed-union discipline：reader 需要同时查看
`schema_version` 与 extension membership 才能判断哪些 built-in spec 与 change 名称合法。

只有当项目有意离开 schema-versioned closed union 时，方案 C 才是连贯的。对于当前
pre-release codebase，未选择该方案。

## P4-C1 correction gate

因为 Option A 已接受，P4-C1 是任何 schema v4/v5/v6 implementation gate 前必须完成的
correction gate：

1. `fix(core): complete schema-v3 structured contract models`
2. `fix(core): complete schema-v3 reader writer and migration validation`
3. `test(core): add schema-v3 YAML table array contract fixtures`
4. `docs(rfc): record schema-v3 predecessor correction evidence`

Gate：本 RFC 合并后由 coordinator 从更新后的 `main` 派发；不实现 YAML、table 或 array comparator 行为；不新增 CLI
route、detector、plugin SDK、artifact 或 renderer feature；`git diff --check`、formatting、lint、
strict type checking、完整测试、schema-v1/v2/v3 compatibility fixture、unknown-kind rejection
与 public-export check 全部通过。P5-A1、P6-C0、P7-A1 与后续 video schema gate 必须等待
P4-C1，或者等待本 RFC 中另一个方案被接受。

## Accepted P4-C1 pre-implementation clarifications

这些 P4C1 ID 已于 2026-09-10 获批。它们只澄清 P4-C1 的 schema-v3 reader 与 fixture
contract，不启动 implementation。

### P4C1-1：table encoding field

推荐选择：在 `TableCompareSpec` 中新增显式 `encoding` field，位置紧跟 `dialect`：

```python
class TableCompareSpec:
    kind: Literal["table"] = "table"
    dialect: Literal["csv", "tsv"]
    encoding: Literal["utf-8", "utf-8-sig"] = "utf-8"
    header: Literal["first_row", "none"] = "first_row"
```

Wire shape 与 ordering：canonical schema-v3 JSON 在 `dialect` 后、`header` 前写入 `encoding`，
即使其值为默认 `utf-8`。`utf-8` 表示 strict UTF-8，不做隐式 BOM 处理。`utf-8-sig` 允许
input 开头存在一个 UTF-8 BOM，并把 stripping 记录为 table decoding transformation；其他
byte 仍按 strict UTF-8 解码。

拒绝的替代方案：只在 prose 中说明 encoding、从 byte 推断 encoding、接受 locale encoding，
或静默剥离 BOM 但不序列化 selected policy。

兼容性影响：尚无已发布 schema-v3 table fixture，因此这是 release 前可见默认值，不是
migration。P4-C1 canonical fixture 必须包含 `encoding`。既有 v1/v2/v3 fixture byte 保持
stable；新的 schema-v3 table spec 始终 canonical 写入默认 `utf-8` policy。

### P4C1-2：table fact discriminator 与 row-cell wire shape

推荐选择：为 table fact variant 增加显式 `kind` discriminator，并把 row cell 序列化为
有序 pair array，而不是 JSON object：

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

Wire shape 与 ordering：canonical JSON field order 为 `kind` 后跟上方 payload fields。
`TableRowFact.cells` 按 aligned column order 序列化为
`[["column_name", {"kind": "string", "value": "..."}], ...]`。Validation 拒绝 object-map
cells、重复 column name、scalar kind 违反 declared column schema 的 cell，以及相对 aligned
column set 省略或新增 column 的 row fact。

拒绝的替代方案：从 payload key 推断 table fact type，或把 `cells` 序列化为按 column name
索引的 object。

兼容性影响：discriminator 让 schema-v3 closed union 对 detached reader 保持无歧义。
Pair array 保留 canonical order，并在任何 schema-v4/v5/v6 successor 消费 fixture corpus 前
明确 duplicate-name rejection。

### P4C1-3：array error number type

推荐选择：将 `ArrayChange.absolute_error` 与 `ArrayChange.relative_error` 中未定义的
`MetricNumber` 替换为既有 `NumericValue` union；该 union 已用于 `Metric.value`、
`Metric.threshold` 与 `PolicyEvaluation.observed`。

Wire shape 与 ordering：`ArrayChange` field name 保持不变。`absolute_error` 非 null 时必须是
大于等于 zero 的 finite `NumericValue`。`relative_error` 非 null 时必须是大于等于 zero 的
finite `NumericValue`，或在 before reference 为 zero 且 finite difference 非零时使用
`positive_infinity`。NaN、negative infinity，以及用于 `absolute_error` 的 positive infinity
均为 validation error。non-numeric 或 non-finite input pair 的两个 error field 均为 null。
Canonical JSON 中这些 field 始终存在；当 error 未定义时，按照当前 schema serializer 的
nullable-field convention 写为 JSON null。Canonical field order 仍为 `kind`、`operation`、
`index`、`before_digest`、`after_digest`、`absolute_error`、`relative_error`。

拒绝的替代方案：为 array change 定义第二套 number union，或把 error 序列化为裸 JSON number。

兼容性影响：复用 `NumericValue` 避免新增 public numeric contract，并让 renderer、policy、
metric 与 schema-v3 fixture parsing 使用同一 numeric representation。

### P4C1-4：无 comparator route 的 completed contract fixture

推荐选择：P4-C1 保持 contract-only。Completed canonical YAML/table/array fixture 是直接构造的
validated schema-v3 outcome，用于 reader/writer；它们不表示可运行 `compare()` route、CLI route、
detector、plugin handle 或 backend。其 provenance 使用冻结的未来 built-in comparator ID，而不是
fixture-only ID。这遵循当前 built-in convention：comparator ID 使用非 namespaced 的
`text`/`binary`/`json` 风格 identifier，algorithm ID 可以使用 dotted stable name。

| Modality | `comparator_id` | `algorithm_id` |
| --- | --- | --- |
| YAML | `yaml` | `yaml.structural.tree.v1` |
| Table | `table` | `table.delimited.align.v1` |
| Array | `array` | `array.position.numeric.v1` |

Wire shape 与 ordering：canonical fixture 包含 completed `DiffResult` record，schema version 为
3，explicit spec kind、fact/change variant 匹配，`comparator_version="1"`，没有 detector
provenance，也没有 plugin provider。每个 fixture 还在 `ExecutionRecordV2.attempts` 中包含
恰好一个 selected `CapabilityAttemptV2`；其 `capability_id` 匹配 `provenance.comparator_id`，
`capability_version` 匹配 `provenance.comparator_version`，provider/backend field 为 null。
`_validate_v3_result` 只在 result 的 spec、fact、change、metric name、resource record、
transformation、problem absence 与 selected attempt 均匹配对应 schema-v3 contract 时，接受这些
reserved built-in ID pair。P4-C1 期间 capability resolution 仍必须拒绝把这些 ID 当作 registered
runtime comparator。

拒绝的替代方案：复用 `json` provenance、省略 comparator/algorithm ID、允许任意 fixture ID，
或允许 `contract_fixture` ID，或在 P4-C1 中加入 YAML/table/array comparator implementation。

兼容性影响：这为 canonical byte fixture 提供真实的未来 built-in provenance，而不扩大 runtime
behavior。后续 P4-B1/P4-B2 comparator work 在 registry 真正暴露 executable YAML/table/array
capability 时，必须使用这些相同 built-in ID。

### P4C1-5：detached array-change validation context

推荐选择：不要给每个 `ArrayChange` 增加 shape 或 dtype field。Detached `ArrayChange` reader
只验证 operation/field matrix、digest syntax、`NumericValue` error shape，以及每个 `index`
component 都是 non-negative integer。由于当前 `ArrayCompareSpec`、`DiffResult` 与 provenance
都不携带 array shape 或 dtype，P4-C1 中 detached reader 与 schema-v3 result reader 都不能证明
full-rank、in-bounds、row-major order 或 dtype-specific error consistency。这些检查降为未来
producer/comparator invariant，并延后到 P4-B2。

Wire shape 与 ordering：`ArrayChange` 保持 RFC 0006 fields 不变；`element_replace` 的 `index`
序列化为 non-negative integer 的有序 JSON array。schema-v3 canonical writer 始终包含
`index`；`shape_replace` 与 `dtype_replace` 将其序列化为 JSON null。Exact-key reader 拒绝
省略 `index` key、重复 key，以及在 `ArrayChange` 上出现额外 shape/dtype context key。P4-C1
不给 `ArrayChange` 新增 `before_shape`、`after_shape`、`dtype` 或任何 `ArraySource` payload。
`ArraySource` 保留给 P4-B2 的 source-acquisition/API，不进入 P4-C1 serialized schema-v3
correction。

拒绝的替代方案：把 `shape` 与 `dtype` context 复制进每个 `ArrayChange`，使 detached reader
不依赖 enclosing result 也能证明 full-rank 与 in-bounds constraint。

兼容性影响：保留 compact accepted `ArrayChange` shape，同时让 validator 区分 detached
syntactic validation 与 producer validation。P4-C1 fixture 必须测试 non-negative index syntax
和 operation/field matrix；full-rank、bounds、row-major order 与 dtype/error consistency 的
producer test 延后到 P4-B2。

## P6-C0 契约修订

P6-C0 仍取决于 P4-C1 与 predecessor compatibility fixture。下列 public contract 细节已作为
Phase 6 contract decision 接受，但不是实现授权。

| ID | 已接受决策 | 未选择的替代方案 |
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

### 未来 P6-C0 的已接受 schema-v5 public shape

这些 shape 已作为 future P6-C0 implementation review 的契约被接受，但其本身不启动代码。
P6-C0 已记录条件授权；coordinator 只有在 RFC 0010、P4-C1、P5-A1/schema-v4 及其
compatibility fixture 都合并到 `main` 后才能派发。这不表示自动启动。

Source lexical change 使用既有 schema-v5 closed-union member
`kind="source_code_change"`，并使用 lexical discriminator
`change_variant="lexical_text"`。这不会增加新的 built-in change kind。稳定 field order 为：

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

`language` 是显式 spec language。`relation` 是 `lexical_text`。`coordinate_encoding` 是
`utf-8`。`column_unit` 只能是 `unicode_scalar` 或 `utf8_byte`；默认序列化值是
`unicode_scalar`。`before_range` 与 `after_range` 是 nullable range object，字段为
`start_byte`、`end_byte`、`start_line`、`start_column`、`end_line`、`end_column`、
`column_unit`。Byte offset 是 decoded byte sequence 中的 zero-based half-open offset。
Line 是 one-based。Column 使用 range object 的 `column_unit`。当 outer `column_unit` 与
non-null range `column_unit` 都存在时，二者必须相等；reader 拒绝不一致。Null range 不含 nested
`column_unit`。`lexical_text` 要么是 null，要么是包含 `before_lines`、`after_lines`、
`line_ending` 的 object。在
`detail_mode="facts"` 下，这些 line array 只能包含 source fact limit 允许的有界 UTF-8 text。
在 `detail_mode="digest_only"` 下，`lexical_text` 为 null，只保留 coordinate、count、
discriminator 与 digest。

PDF binary change 使用既有 schema-v5 closed-union member `kind="pdf_change"`，并使用
`view="binary"` 与 `binary_variant="byte_range"`。稳定 field order 为：

```text
kind
view
binary_variant
ranges
payload_digest
```

`view` 必须是 `binary`。每个 range 有 `side`、`start_byte`、`end_byte`；`side` 是
`before` 或 `after`。Byte offset 是 original PDF bytes 上的 zero-based half-open offset，
位于 parsing、decryption、repair 或 decompression 之前。即使报告相同 byte range，它也不同于
generic `BinarySpan`。

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

Schema-v5 保留 RFC 0008 已接受的 evidence-digest framing。改变该 frame 需要单独人工决策，
且此处未选择。Frame 为：

```text
SHA256(UTF8("platydiff/v5/" + domain) || 0x00 || U64BE(payload_length) || payload)
```

`payload` 是 tagged byte sequence：

```text
U64BE(field_count)
for each field in stable field order:
  U64BE(tag_length) || UTF8(tag) || U64BE(value_length) || value_bytes
```

String 的 `value_bytes` 是 strict UTF-8。Integer 的 `value_bytes` 是最短 unsigned base-10
ASCII 表示。Boolean 为 `true` 或 `false`。Null 是 tag suffix `?null` 加 zero-length value，
因此 null 与 empty string 不共享编码。Normative non-empty vector 为：

| Domain | Tagged fields | Payload hex | SHA-256 |
| --- | --- | --- |
| `source/decoded_text_line` | `language=python`, `line=1`, `terminator=lf`, `text=pass` | `000000000000000400000000000000086c616e67756167650000000000000006707974686f6e00000000000000046c696e65000000000000000131000000000000000a7465726d696e61746f7200000000000000026c66000000000000000474657874000000000000000470617373` | `e700a16bc1f2b8703cbaaae345390c507d031261c13ccf31ece00cbac9e11b6e` |
| `source/change_payload` | `kind=source_code_change`, `range_variant=lexical_text`, `before_start_byte=0`, `before_end_byte=4` | `000000000000000400000000000000046b696e640000000000000012736f757263655f636f64655f6368616e6765000000000000000d72616e67655f76617269616e74000000000000000c6c65786963616c5f7465787400000000000000116265666f72655f73746172745f62797465000000000000000130000000000000000f6265666f72655f656e645f62797465000000000000000134` | `07127b46e29dd63562d20877c7d3d52872b2a943a209ad71436a937f5bfaac3d` |
| `pdf/binary/span` | `kind=pdf_change`, `view=binary`, `span_variant=byte_range`, `side=before`, `start_byte=0`, `end_byte=4` | `000000000000000600000000000000046b696e64000000000000000a7064665f6368616e6765000000000000000476696577000000000000000662696e617279000000000000000c7370616e5f76617269616e74000000000000000a627974655f72616e676500000000000000047369646500000000000000066265666f7265000000000000000a73746172745f627974650000000000000001300000000000000008656e645f62797465000000000000000134` | `a95731a041d328d0d9f350ac4c9a45b49761e96103efa7b2fdf544f3411b91f9` |
| `pdf/render/page` | `page=1`, `width_px=2`, `height_px=2`, `dpi=72`, `colorspace=srgb` | `0000000000000005000000000000000470616765000000000000000131000000000000000877696474685f707800000000000000013200000000000000096865696768745f7078000000000000000132000000000000000364706900000000000000023732000000000000000a636f6c6f727370616365000000000000000473726762` | `b9f9fef8b2493372b76f5ae8abf4166aae2a37e9ec8f3134a6b19c838ff1e81f` |

### Stable ID、policy 与 counter

P6-C0 必须逐字保留这些已接受 RFC 0008 名称：

- source relation ID：`lexical_text`、`syntax_tree`；`semantic` 已保留且 unavailable；
- PDF view ID：`pdf.binary`、`pdf.extracted_text`、`pdf.objects_metadata`、
  `pdf.rendered_pages`；
- source metric ID：`source.nodes_compared`、`source.nodes_changed`、
  `source.tokens_changed`、`source.moves`、`source.parser_errors`、
  `source.ignored_trivia_items`；
- PDF metric ID：`pdf.binary.changed_bytes`、`pdf.text.changed_runs`、
  `pdf.text.compared_runs`、`pdf.objects.changed_entries`、
  `pdf.objects.compared_entries`、`pdf.render.changed_pixels`、
  `pdf.render.changed_pages`、`pdf.render.compared_pages`；
- 已接受 evaluation ID：`source.syntax_tree_equality`、
  `source.lexical_text_equality`、`pdf.extracted_text_equality`、
  `pdf.rendered_page_equality`；
- digest domain：`source/decoded_text_line`、`source/token`、`source/node`、
  `source/subtree`、`pdf/binary/span`、`pdf/text/run`、`pdf/object/entry`、
  `pdf/metadata/entry`、`pdf/render/page`、`pdf/render/region`；
- source resource limit field：`max_input_bytes`、`max_decoded_chars`、
  `max_fact_text_bytes`、`max_tokens`、`max_nodes`、`max_depth`、
  `max_parser_errors`、`max_compare_work`、`max_change_items`、
  `max_change_payload_bytes`；
- PDF base 与 worker resource field：`max_input_bytes`、`max_fact_text_bytes`、
  `max_fact_value_bytes`、`max_compare_work`、`max_change_items`、
  `max_change_payload_bytes`、`max_total_backend_seconds`、
  `max_total_stdout_stderr_bytes`、`max_total_temp_bytes`、
  `max_total_decoded_bytes`、`max_total_worker_output_bytes`、
  `max_peak_worker_rss_bytes`、`max_peak_concurrent_worker_processes`、
  `max_total_worker_processes_spawned`；
- PDF per-view resource field：`max_pages`、`max_stream_bytes`、
  `max_decoded_stream_bytes`、`max_text_runs`、
  `max_render_pixels_per_page`、`max_rendered_pages`、
  `max_view_backend_seconds`、`max_view_stdout_stderr_bytes`、
  `max_view_temp_bytes`、`max_view_decoded_bytes`、
  `max_view_worker_output_bytes`、`max_view_peak_worker_rss_bytes`、
  `max_view_peak_concurrent_worker_processes`、
  `max_view_total_worker_processes_spawned`。

RFC 0010 只接受下列超出 RFC 0008 的缺失 stable ID：

- implementation comparator ID：`builtin.source.lexical_text.v1`、
  `builtin.source.syntax_tree.v1`、`builtin.pdf.binary.v1`、
  `builtin.pdf.extracted_text.v1`、`builtin.pdf.objects_metadata.v1`、
  `builtin.pdf.rendered_pages.v1`；
- algorithm ID：`source.lexical_text.myers.v1`、
  `source.syntax_tree.digest_align.v1`、`pdf.binary.byte_scan.v1`、
  `pdf.text.run_lcs.v1`、`pdf.objects.key_path_align.v1`、
  `pdf.render.pixel_exact.v1`、`digest.tagged_payload_sha256.v1`；
- transformation ID：`source.decode_utf8`、`source.normalize_newlines`、
  `source.lexical_tokenize_lines`、`pdf.read_original_bytes`、`pdf.parse_xref`、
  `pdf.extract_text_runs`、`pdf.enumerate_objects`、`pdf.render_page`；
- 缺失的 PDF evaluation ID：`pdf.binary_equality`、`pdf.objects_metadata_equality`；
- summary key：`changed_items`、`added_items`、`removed_items`、
  `modified_items`、`moved_items`、`truncated`、`selected_views`。

### Problem registry

新的 schema-v5 problem code 使用 scoped registry key `schema-v5/<code>` 注册，而 serialized
`problem.code` 保持短 stable code。P6-C0 预留：

| Registry ID | Serialized status/code | Stage | Detail keys |
| --- | --- | --- | --- |
| `schema-v5/pdf_encrypted` | `failed/pdf_encrypted` | `decoding` | `input_side`, `view`, `encryption_detected=true` |
| `schema-v5/pdf_worker_timeout` | `failed/pdf_worker_timeout` | `decoding` | `view`, `limit_seconds`, `elapsed_seconds` |
| `schema-v5/pdf_worker_resource_exhausted` | `failed/pdf_worker_resource_exhausted` | `decoding` | `view`, `resource`, `limit`, `actual` |
| `schema-v5/pdf_worker_crash` | `failed/pdf_worker_crash` | `decoding` | `view`, `exit_status` |
| `schema-v5/pdf_worker_protocol_violation` | `failed/pdf_worker_protocol_violation` | `decoding` | `view`, `message_kind` |
| `schema-v5/pdf_worker_invalid_output` | `failed/pdf_worker_invalid_output` | `decoding` | `view`, `field` |

`pdf_encrypted` 不用于 pure binary view。任一 selected nonbinary view 遇到任一 encrypted input
时，整个 all-or-nothing PDF invocation failed，不产生 `DiffResult`，也不 fallback 到 binary。

Problem detail value type 是 closed：`input_side` 是 `before` 或 `after`；`view` 是 canonical PDF
view name 之一；`encryption_detected` 是 boolean `true`；`limit_seconds`、`elapsed_seconds`、
`limit`、`actual` 是 non-negative JSON number；`resource`、`message_kind`、`field` 是 stable
lowercase ASCII identifier；`exit_status` 是 signed integer，或在 process 被终止且无 exit status
时为 null。Invalid wire coordinate、unknown problem registry ID 与 malformed tagged payload
都会 raise `SerializationError`；它们不制造 runtime failed outcome。

[RFC 0014](0014-phase6-source-pdf-contract-closure-amendment_zh.md) 是 Accepted contract-only
amendment，会关闭并 supersede 这些 problem detail，但不授权实现。

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

Option B 与 C 未被选择。如果后续 RFC supersede Option A，其 migration test 还必须证明被移除
或迁移的 YAML/table/array v3 名称会以稳定 problem 被拒绝，并且 successor allocation 在代码前
已写入文档。

## 已接受解决方案与剩余授权

人工 reviewer 已接受：

1. RFC 0006 仍是期望的 schema-v3 contract。
2. P4-C1 必须在 schema v4 前修正当前代码以匹配 RFC 0006。
3. Pre-release schema-v3 fixture 只能在任何 successor 依赖它们前、且 release 前扩展；
   P4-C1 predecessor fixture 被 v4/v5/v6 消费后，v3 closed-union membership 冻结。
4. v4 image、v5 source/PDF、v6 audio 与后续 video successor 的全局 allocation 仍正确。
5. P6C0-1 到 P6C0-10 已作为 P6-C0 implementation 前的 contract decision 接受。

RFC acceptance 本身不启动代码。已记录条件人工授权；coordinator 只有在指定 merge gate 之后
才能派发。P4-C1 implementation 在本 RFC 合并后仍需要由 coordinator 派发。P5-A1、P6-C0、
P7-A1 与后续 video schema implementation 仍被阻塞，直到其实际 predecessor merge 与
compatibility fixture 已存在于 `main`。
