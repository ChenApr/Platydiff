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

在 `origin/main` `7907fbf` 上，已实现的 schema-v3 代码公开了 `JsonCompareSpec` 与
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
| P6C0-7 | 将 `pdf_encrypted` 定义为 structured problem code，并给出明确 status mapping：缺少 password 或 encryption unsupported 时，policy 允许报告 unsupported capability 则为 `unavailable`，已选择 comparison 但 validation 后无法继续则为 `failed`；problem detail 只能包含安全字段。 | 把 encryption 折叠成 generic decode failure。 |
| P6C0-8 | 定义 worker problem detail：timeout、resource exhaustion、crash、protocol violation、invalid output、stderr overflow、temp overflow、decoded-output overflow、RSS overflow 与 spawn-limit overflow；每个都有稳定 status 与安全 detail shape。 | 把 backend-specific string 直接作为 problem detail 返回。 |
| P6C0-9 | 定义 fact presence invariant：每个 selected 且 successful 的 view 都发出其 required fact、metric、summary、resource 与 transformation；每个 unselected view 按规定 absent 或显式 null；failed 或 unavailable view 不伪造空 fact。 | 允许没有 schema-level invariant 的 partial fact。 |
| P6C0-10 | P6-C0 保持 models/serialization only：source/PDF 的 public `compare()` 与 CLI 行为直到 P6-S1 或 P6-P1a 才可用。P6-C0 fixture 可以直接构造 unavailable outcome 用于 reader/writer validation，但不得暴露可运行 source/PDF comparator route。 | 在 P6-C0 添加返回 unavailable 的 source/PDF `compare()` 行为。 |

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
