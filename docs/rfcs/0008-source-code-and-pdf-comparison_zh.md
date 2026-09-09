# RFC 0008：源代码与 PDF 比较

[English documentation](0008-source-code-and-pdf-comparison.md)

- Status: Proposed
- Date: 2026-09-10
- Review revision: 2026-09-10
- Owners: Platydiff maintainers
- Implementation owner: unassigned pending separate implementation authorization

## 摘要与授权边界

本 RFC 提议 Phase 6 的显式源代码与 PDF 比较契约。本文只进行设计工作，不授权源代码
或 PDF 实现、依赖变更、SDK v2、自动探测、UI 工作、artifact 生成、可选后端安装或
任何代码变更。

源代码与 PDF 同属 Phase 6 路线图，是因为二者都需要重量级解析后端和更丰富的结构化
事实；但它们不是同一个实现门禁。源代码和 PDF 的等价关系、后端、安全边界、artifact
与依赖风险都不同，因此本 RFC 将它们拆分为独立授权的交付门禁。后续人工审批可以接受
其中一个、两个或都不接受。

所有行为都保持显式启用。调用者必须直接选择 source-code 或 PDF spec。既有
`AutoCompareSpec` 在 RFC 0003 的后继 RFC 接受新的探测语义之前，仍只支持 text/binary。

## 证据账本

| `origin/main` `fde2bd4` 上的当前证据 | Phase 6 约束 |
| --- | --- |
| RFC 0001 将 failed/unavailable 执行终态与 completed `DiffResult` 事实分离。 | parser、backend、resource、encryption、sandbox 与 rendering 失败不得变成空或伪造的差异。 |
| RFC 0002 要求每个新模态在实现前定义 spec、change、metric、artifact、等价关系、policy、failure 与 gate。 | 本 RFC 只记录契约与门禁，不启动代码工作。 |
| RFC 0003 保持自动探测有界且只对 text/binary 封闭。 | Source/PDF 不参与 auto detection；filename、MIME、grammar 或 PDF magic probe 不改变既有 auto 行为。 |
| RFC 0003 的 snapshot path 管理有界 replay、hash、mutation check 与安全 label。 | Source/PDF gate 依赖它前必须重新验证 snapshot 实现；并发 Phase 4/5 工作不是证据。 |
| RFC 0004 要求 renderer 与 UI 消费 validated outcome，不重读 source 或重算事实。 | Source/PDF renderer 只能展示 validated fact 与 inert artifact ref；page image 与 heatmap 需要 artifact gate。 |
| RFC 0005 实现的 SDK v1.1 只覆盖 text/binary detector、comparator 与 renderer handle。 | Source/PDF plugin comparator 需要显式 SDK-v2 callback，不能通过 SDK v1.1 添加。 |
| RFC 0006 接受 schema v3 用于 structured-data 内建 spec/change，但其门禁仍未实现。RFC 0007 提议 image schema v4，RFC 0009 提议后续 media schema 工作。 | Phase 6 应使用共享 schema allocation，而不是有条件扩展 v3；任何 Phase 6 schema implementation 开始前都必须满足 predecessor schema merge 与 fixture gate。 |
| 当前运行时依赖为零，PDF/source backend 还只是架构层计划。 | Tree-sitter、PDF parser、renderer、font 与 subprocess tool 需要独立依赖、license、platform 与 security review。 |

该账本只说明设计约束，不证明未来 backend、parser、artifact writer 或 schema migration
能够工作。

## 目标与非目标

Phase 6 目标包括：

- 显式 source-code spec，并让 language、parser、normalization、alignment、relation
  与 resource choice 可见；
- 区分 lexical/text、syntax-tree/structural 与 semantic claim relation；
- 稳定的 source-code node coordinate、change operation、metric、provenance 与确定性
  fixture corpus；
- 显式 PDF spec，并分别命名 binary、extracted-text、object/metadata 与 rendered-page view；
- PDF parser、text extraction、rendering、sandbox、timeout、resource limit 与 hostile
  document feature 的后端边界；
- 与 v1、v2 以及已接受 v3 migration 规则兼容；
- 明确 SDK-v2、artifact、detection 与 UI callback gate。

Phase 6 不包括：

- 自动源代码语言探测或 PDF 探测；
- 源代码或 PDF 解析失败后的 text fallback；
- 需要执行代码、类型检查、宏展开、程序分析、OCR 或 accessibility-tree 推断的语义等价声明；
- 源代码格式化、lint、patch 生成、rename detection、blame、仓库遍历、generated-code
  排除或 build-system 集成；
- PDF 密码交互提示、远程字体获取、JavaScript 执行、action 执行、embedded-file 提取、
  OCR、accessibility tag、reflowed layout 或表单填写；
- 通过 SDK v1.1 执行 source/PDF plugin；
- HTML、TUI、desktop、local-web、page-image、heatmap 或 downloadable artifact 实现。

## 提议决策

下面的稳定 ID 是本提案的人工决策清单。在 reviewer 显式批准前，它们都尚未接受。

| ID | 提议决策 | 未选择的替代方案 |
| --- | --- | --- |
| P6X1 | Source-code 与 PDF 比较保持 explicit-only；既有 auto 仍只支持 text/binary。 | 不定义 ambiguity 与 attribution 就把 source/PDF candidate 加入 RFC 0003 detection。 |
| P6X2 | Phase 6 source-code 与 PDF 内建 spec/change variant 使用 schema v5，并受 P6X10 的全局 allocation 与 predecessor merge/fixture gate 约束。 | 有条件扩展 schema v3，或复用 image/media schema 编号。 |
| P6X3 | SDK v1.1 下拒绝 source/PDF plugin comparator；第三方 source/PDF modality 需要 SDK v2。 | 允许 plugin 安装引入 source/PDF spec 或内建 change kind。 |
| P6X4 | 独立授权 source-code 与 PDF 实现门禁。 | 因为二者都需要 parser 而把 Phase 6 当作一个批次。 |
| P6X5 | 保持 RFC 0004 artifact/UI 工作独立；Phase 6 fact 只有在 artifact writer gate 后才能引用 artifact。 | 让 PDF rendering 隐式创建 page image 或 HTML report。 |
| P6X6 | 每个依赖代码状态的假设都是 revalidation gate，包括 P4-A1 和未来 Phase 5 工作。 | 把并发未合并工作当成设计证据。 |
| P6X7 | 后端/parser 开始后，禁止改变比较 relation 的 fallback。 | 失败时静默 fallback 到 text、binary、另一个 parser、另一个 renderer 或 approximate semantics。 |
| P6X8 | 多 view PDF spec 作为 required all-or-nothing invocation 执行：任一 selected view unavailable 或 failed 都终止顶层 outcome，且不产生 `DiffResult`。 | 返回只包含已完成 view 的 partial PDF `DiffResult`。 |
| P6X9 | artifact gate 之前，`artifact_policy` 只有一个取值：`none`。 | 在安全 artifact writer 存在前预留 `record_refs`。 |
| P6X10 | 提议共享 schema allocation：P4 structured data = v3，Phase 5 image = v4，Phase 6 source/PDF = v5，Phase 7 audio/video = v6；每个 successor 只有在其依赖的所有 predecessor schema 已合并到 `main` 且 reader/writer 与 migration fixture 就绪后才能开始。 | 让每个 RFC 局部选择 schema 编号，或把编号推迟到实现期而造成 closed union 冲突。 |
| SC1 | 增加显式 `SourceCodeCompareSpec`，并要求 `language` 与 `relation` 字段。 | 从 suffix/content 推断语言，或复用 `TextCompareSpec`。 |
| SC2 | 首批 source language 为 `python` 与 `javascript`；`typescript`、`c`、`cpp`、`rust`、`go`、`java`、notebook、template 与 generated-code policy 延后。 | 从后端 package 中可用的所有 grammar 同时开始。 |
| SC3 | 分离 `lexical_text`、`syntax_tree` 与未来 `semantic` relation；Phase 6 首批 gate 不声明运行时语义等价。 | 把所有源代码结果报告为泛化 code equality。 |
| SC4 | Parser error 使用显式 error-recovery policy：默认 `reject`；只有在 fact 标记 degraded 且报告 recovery node 时才允许可选 `recover`。 | 隐藏 recovery node，或把 best-effort tree 当成 full fidelity。 |
| SC5 | Comment 与 formatting 默认都是比较维度，除非命名 normalization 显式省略或分类。 | 默认将 formatting/comment 视为无关。 |
| SC6 | Unicode scalar、byte encoding、newline policy、BOM、tab 与 escape 都可见；不隐式执行 Unicode normalization、case folding 或 locale transform。 | 解析前规范化 source text 且不记录。 |
| SC7 | Macro、preprocessing、import、generated code 与 build configuration 不在首批 gate 范围内，且不得模拟。 | 在 source 比较中调用 compiler、build tool、package manager 或 preprocessor。 |
| SC8 | AST alignment 使用稳定 node path 与确定性 tie-break；insert/delete/update/move 是不同 observation，不是 patch。 | 依赖 backend object identity 或不稳定 traversal order。 |
| SC9 | Tree-sitter 是候选可选后端，但每个 gate 都必须审查 grammar version、wheel/source distribution、native build、platform、license 与 security profile。 | 把 parser dependency 加为默认 runtime dependency。 |
| SC10 | Source-code corpus 必须是 synthetic 或 license 明确，并覆盖 malformed、adversarial、Unicode、formatting、comment、move 与 limit。 | 未说明 provenance 就复制真实项目源码 fixture。 |
| PDF1 | 增加显式 `PdfCompareSpec` view：`binary`、`extracted_text`、`objects_metadata` 与 `rendered_pages`。 | 把 PDF 比较折叠成一个 PDF equality bit。 |
| PDF2 | Binary、extracted-text、object/metadata 与 rendered-page equivalence 是独立 relation，且有各自 metric 与 evaluation。 | 让视觉相等覆盖 object/text 差异，或反过来。 |
| PDF3 | 纯 `binary` PDF view 把 encrypted PDF 当作字节接受；任何 selected nonbinary view 遇到 encrypted input 都以稳定 `failed/pdf_encrypted` 终止。 | 拒绝所有 encrypted PDF，或提示密码。 |
| PDF4 | Embedded file、JavaScript、launch action、network action 与 form action 是 inert fact 或显式 unsupported feature；默认绝不执行或提取。 | 比较时执行或解引用 active document content。 |
| PDF5 | Nonbinary PDF parse、text extraction、object inspection 与 rendering 只在受监督的 bounded worker 中运行，并记录 version provenance 与 failure isolation。 | 在进程内运行 PDF backend，或隐藏哪个 view 失败。 |
| PDF6 | 若选择外部 PDF tool，必须使用 argument array、禁用 shell、有界 temp dir、timeout、output limit 且无网络。 | 让后端专用命令行隐式负责安全。 |
| PDF7 | Page、object 与 text alignment 都是确定性的 view-specific 行为；unavailable/degraded/failure 状态保持可区分。 | 把 alignment failure 合并成内容变化。 |
| PDF8 | Rendered-page artifact、thumbnail 与 heatmap 在写入或链接任何文件前需要兼容 RFC 0004 的 artifact gate。 | 把 page image 作为比较副作用输出。 |
| PDF9 | Font、encoding、transparency、page box、rotation、color、malformed xref、stream 与 decompression bomb 是显式 backend/resource case。 | 接受 backend default 且不记录 transformation 和 limit。 |
| PDF10 | PDF fixture 必须生成或明确可再分发，并包含 hostile/malformed case，且不使用受限文档。 | 使用任意真实世界 PDF 作为 test corpus。 |

## Schema 与兼容性契约

本 RFC 为 Phase 6 source-code 与 PDF 内建能力提议 schema v5。人工决策是 P6X10：
P4 structured data 使用 schema v3，Phase 5 image 使用 schema v4，Phase 6 source/PDF
使用 schema v5，Phase 7 audio/video 使用 schema v6。这是 Proposed allocation，不是
已接受的 schema migration。若后续全局 schema RFC 或人工 review 选择不同 allocation，
必须在任何受影响 gate 开始前同时更新 RFC 0007、RFC 0008 与 RFC 0009。

Phase 6 schema implementation 只有在其依赖的 predecessor schema 已合并到 `main` 且
带 compatibility fixture 后才能开始：

- RFC 0006 的 schema v3 reader/writer 与 migration fixture 已存在并重新验证；
- 如果 Phase 5 已先于 Phase 6 接受，则 schema v4 image reader/writer 与 migration
  fixture 已存在；否则需要人工批准的 schema-allocation review 以 no-op predecessor
  fixture 显式保留 v4；
- schema v5 fixture 证明 reader 按已实现 predecessor 集合接受 v1/v2/v3/v4/v5，
  v1/v2 writer 保持不变，source/PDF outcome 绝不会自动 downgrade。

提议的 v5 closed union 为：

```python
CompareSpecV5 = (
    AutoCompareSpec | TextCompareSpec | BinaryCompareSpec
    | JsonCompareSpec | YamlCompareSpec | TableCompareSpec | ArrayCompareSpec
    | ImageCompareSpec
    | SourceCodeCompareSpec | PdfCompareSpec
)
ChangeV5 = (
    TextHunk | BinarySpan | StructuredChange | TableChange | ArrayChange
    | ImageChange | SourceCodeChange | PdfChange | ExtensionChange
)
```

在该提议 allocation 下：

- 既有内建 text、binary 与 auto 调用保持 schema v1；
- 既有 `PluginHost` text/binary 调用保持 schema v2；
- structured data outcome 只有在 RFC 0006 gate 已实现并重新验证后才使用 schema v3；
- image outcome 只有在已接受的 Phase 5 gate 实现并重新验证 v4 后才使用 schema v4；
- 内建 source-code 与 PDF spec 产生 schema v5，即使在 resolution 前失败也是如此；
- schema v5 reader 根据已实现 predecessor 集合接受 v1/v2/v3/v4/v5；
- 显式 migration helper 保留原始事实，只加入文档化的中性默认值；
- source-code 或 PDF outcome 不存在自动 downgrade；
- unknown built-in spec/change kind 仍然非法；unknown namespaced extension change 保持 RFC 0001 行为。

Schema v5 必须为每个新 spec field、change kind、metric、evaluation rule、transformation
ID、backend identity 与 problem detail 定义稳定 JSON 名称。由于 predecessor RFC 可能已
接受但 code gate 仍未实现，每个 Phase 6 implementation gate 开始时都必须重新验证 schema
假设。

## 设计-契约矩阵

| 区域 | Source-code contract | PDF contract |
| --- | --- | --- |
| Public spec | `SourceCodeCompareSpec(language, relation, parser, normalization, alignment, detail_mode, limits)` | `PdfCompareSpec(views, passwords policy, backend choices, text/render/object options, artifact policy, limits)` |
| 首批 relation | `lexical_text` 与 `syntax_tree`；`semantic` 保留且 unavailable | `pdf.binary`、`pdf.extracted_text`、`pdf.objects_metadata`、`pdf.rendered_pages` |
| Default policy | changed item 为零则 pass，否则 fail | 所有 selected view 都是 required；任一 view unavailable/failed 都终止顶层 outcome，只有全部 view 成功后才聚合零变化 evaluation |
| Change | `SourceCodeChange` 包含 node path、operation、language、node kind、relation 与 digest/fact field | `PdfChange` 按 view 标记，并包含 page/text/object/render coordinate 与 digest/fact field |
| Metric | changed nodes/tokens、parser errors、moved nodes、compared nodes、formatting/comment changes | changed bytes、text runs、object entries、metadata entries、rendered pixels/pages、backend warnings |
| Artifact | 首批 source gate 不产生 artifact | 独立 artifact gate 前只允许 `artifact_policy="none"`；rendered-page fact 可含 digest 但不含文件 |
| Backend | 可选 parser backend，例如 Tree-sitter；审查前不加入默认 dependency | 独立 parser/text/render backend；外部 subprocess 需要 sandbox 规则 |
| Fallback | source parsing 开始后没有 text fallback | PDF view 之间不 fallback，也不 fallback 到 binary，除非显式选择 binary view |
| Plugin path | source-code modality 需要 SDK v2 | PDF modality 需要 SDK v2 |
| Verification | language fixture、parser version、AST path、move tie-break、malformed/adversarial limit | generated PDF、malformed/xref/stream case、encryption、font、rendering determinism、sandbox limit |

## Canonical fact、digest 与 ordering

Source-code 与 PDF fact 在提议 schema-v5 allocation 下使用 RFC 0006 的 evidence-digest
framing，并增加新 domain：

```text
UTF8("platydiff/v5/" + domain) || 0x00 || U64BE(payload_length) || payload
```

Payload 是由 tagged field 构成的 canonical byte encoding。变长字符串使用 strict UTF-8，
并带 U64BE byte length。Count、ordinal、coordinate、byte length、page number 与 work
counter 都是 `0..2**53` 范围内的非 boolean integer，除非更窄的 spec limit 适用。Writer
使用排序后的 object field order 与下文定义的稳定 change ordering；reader 拒绝错误类型、
乱序 built-in collection、缺失 required field、需要唯一时的重复 coordinate、非 canonical
ordinal，以及 unknown non-extension kind。

固定 digest domain 如下：

| Domain | Payload |
| --- | --- |
| `source/decoded_text_line` | lexical source 比较使用的 RFC 0002 `TextLine` content 与 terminator |
| `source/token` | language ID、token kind、normalized token bytes、trivia role 与 source span |
| `source/node` | language ID、node kind、child field name、有序 child digest sequence 与保留 token/trivia digest |
| `source/subtree` | language ID、root node kind、descendant count、token count 与 root node digest |
| `pdf/binary/span` | binary view span 的 byte offset 与 length tuple |
| `pdf/text/run` | page ordinal、run ordinal、Unicode text bytes、extractor flag 与 text span |
| `pdf/object/entry` | object coordinate、canonical key path、primitive type 与 canonical value bytes 或 stream digest |
| `pdf/metadata/entry` | metadata namespace、key、normalized value bytes 与 ignore-policy marker |
| `pdf/render/page` | page ordinal、page box、raster policy、pixel dimension 与 page raster digest |
| `pdf/render/region` | page ordinal、raster policy、pixel rectangle、before digest、after digest 与 changed pixel count |

Evidence digest 是确定性 integrity fingerprint，不是 redaction 或 encryption。低熵 source
token、PDF metadata value、object key 与 text run 可能被猜出。`digest_only` 省略有界 fact
payload，但仍暴露 coordinate、count、kind、hash 与确定性 digest。

Fact field 有界且原子化。每个 returned change 的 operation、coordinate、digest 与 fact
payload 一起计入 `max_change_payload_bytes`。如果下一个完整 item 会超过 item 或 payload
limit，该 item 及其后所有稳定顺序 item 都被省略；fact、coordinate、text run、node、object
entry 或 rendered region 不得部分 serialization。

## 源代码比较契约

### Public intent

提议的首个 public shape 为：

```python
class SourceCodeCompareSpec:
    kind: Literal["source_code"] = "source_code"
    language: Literal["python", "javascript"]
    relation: Literal["lexical_text", "syntax_tree", "semantic"] = "syntax_tree"
    parser: SourceParserOptions = SourceParserOptions()
    normalization: SourceNormalizationOptions = SourceNormalizationOptions()
    alignment: SourceAlignmentOptions = SourceAlignmentOptions()
    detail_mode: Literal["facts", "digest_only"] = "facts"
    limits: SourceCodeResourceLimits = SourceCodeResourceLimits()
```

Option 是封闭集合并完整序列化：

```python
class SourceParserOptions:
    backend: Literal["tree_sitter"] = "tree_sitter"
    error_recovery: Literal["reject", "recover"] = "reject"

class SourceNormalizationOptions:
    encoding: Literal["utf-8", "utf-8-sig"] = "utf-8"
    newline: Literal["preserve", "normalize_lf"] = "preserve"
    comments: Literal["compare", "ignore"] = "compare"
    formatting: Literal["compare", "ignore"] = "compare"
    literal_spelling: Literal["compare", "normalize_language"] = "compare"

class SourceAlignmentOptions:
    detect_moves: bool = True
    move_minimum_subtree_tokens: int = 3
    repeated_anchor_policy: Literal["source_order"] = "source_order"
```

首批 gate 要求显式 `language`。文件 suffix、shebang、modeline、package metadata、content
probe 与 backend parser guess 不用于语言探测。后续 source-detection RFC 可以定义有界
language probing、ambiguity 与 attribution。在此之前，语言不匹配会在实际观察到的阶段
产生 `failed/decode_error` 或 `unavailable/backend_unavailable`；它不会用另一种语言或
`TextCompareSpec` 重试。

P6-S1 的 `lexical_text` 复用 RFC 0002 的 exact decoded-text 与 line 语义：strict UTF-8
或显式 `utf-8-sig`、相同 `TextLine` content/terminator model、相同 newline
normalization option、相同 Myers algorithm 与 work accounting，并且没有 Unicode、
whitespace、tab、case 或 locale normalization。Source language 只作为 intent 与
provenance 记录，不授权 P6-S1 parser fallback 或 syntax claim。P6-S1 不解析或加载 parser
backend；parser option 只为 schema stability 序列化，并且仅对 `syntax_tree` 生效。
`syntax_tree` 比较 parser tree structure 与选定 token/comment fact。`semantic` 保留给未来
契约，用于定义 runtime、type-system、macro、import、environment 与 toolchain 边界；首批
gate 对它返回 `unavailable/capability_unavailable`。

### Parsing、normalization 与 provenance

Normalized spec 记录所有生效默认值。Comparison provenance 必须记录：

- input role、source kind、byte size 与 hash，但不记录绝对路径；
- language ID 与 versioned language profile；
- parser backend ID/version、grammar ID/version、ABI/API version 与 platform；
- grammar source/provenance、license、distribution name/version，以及是否使用 native
  extension 或 generated parser；
- parser error-recovery policy 和观测到的 recovery/error node count；
- encoding、newline policy、comment treatment、formatting treatment、literal
  normalization 与 AST normalization 的显式 transformation；
- configured limit 与确定性的实际 work/resource count。

Comment、whitespace、newline、indentation、semicolon、delimiter 与 formatting trivia 默认是
比较事实，除非命名 transformation 改变其角色。只有 spec 明确要求且输出 transformation
record 时，normalization 才能把 trivia 标记为 ignored。Unicode normalization、case
folding、locale-sensitive classification、tab expansion、newline conversion、BOM removal、
超出语言 grammar 的 escape interpretation 与 generated-code filtering 都不会隐式发生。

Macro、preprocessor、import、package manager、code generator、notebook、templating
language 与 build configuration 不属于首批 gate。Comparator 只在选定 language grammar
下解析提供的 source text。它不执行代码、不 import dependency、不运行 formatter/linter、
不调用 compiler，也不查询 language server。

### AST coordinate、alignment 与 change

Comparator 构造 private immutable tree。Backend node object 不进入结果。每个 node 都有由
normalized tree 派生的稳定 path：

```text
/root
/<escaped-node-kind>#<ordinal-among-siblings-of-same-kind>
```

Wire grammar 为：

```text
path = "/root" *("/" segment)
segment = escaped_kind "#" ordinal
escaped_kind = 1*(unreserved / escape)
unreserved = UTF-8 scalar except "/", "#", "~", NUL, C0, or C1 control
escape = "~0" / "~1" / "~h"
ordinal = "0" / (nonzero_digit *digit)
```

Node-kind identifier 中的 `~`、`/` 与 `#` 分别编码为 `~0`、`~1` 与 `~h`。其他字符是
有界 node-kind validator 允许的 UTF-8 字符串；C0/C1 control、NUL、空 node kind 与
malformed escape 都被拒绝。`ordinal` 是同一 normalized node kind sibling 中的零基序号；
没有 all-sibling ordinal。这让插入无关 sibling kind 时 path 保持稳定。Compatibility
fixture 必须覆盖 escaping、repeated sibling、插入无关 sibling、root-only file 与
malformed path。Byte range 与 line/column span 可以作为 fact 记录，但 node path 是主要
结构坐标。

```python
class SourceCodeChange:
    kind: Literal["source_code_change"]
    relation: Literal["lexical_text", "syntax_tree"]
    language: str
    operation: Literal["insert", "delete", "update", "move"]
    before_path: str | None
    after_path: str | None
    before_node_kind: str | None
    after_node_kind: str | None
    before_digest: str | None
    after_digest: str | None
    before_fact: SourceNodeFact | None
    after_fact: SourceNodeFact | None
```

```python
class SourceNodeFact:
    node_kind: str
    field_name: str | None
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    token_count: int
    descendant_count: int
    parser_error: bool
    trivia_role: Literal["none", "comment", "formatting"]
    text_excerpt: str | None
```

Insert 只有 after coordinate。Delete 只有 before coordinate。Update 在已对齐 node 上有两侧
coordinate，并记录 node kind、token、trivia 或 child-shape fact 变化。Move 有两侧
coordinate，用于报告在 move policy 下 digest 与选定 identity fact 匹配但 path 变化的
node。Move 是 observation，不是 patch operation，而且只有 alignment algorithm 可以确定性
证明时才输出。否则同一变化表示为 delete 加 insert。

`facts` mode 包含有界 `SourceNodeFact`。`digest_only` 省略 `before_fact` 与
`after_fact`，但保留 operation、path、node kind 与 digest。`text_excerpt` 只出现在
lexical token/line fact 中，并受 `max_fact_text_bytes` 约束；syntax subtree fact 使用计数，
不递归内嵌 payload。Model validation 拒绝非法 side combination、反向 span、负 count、
digest/fact 与 `detail_mode` 不匹配、缺少双 path 的 move，以及缺少双侧 aligned side 的
update。

Alignment 是确定性的：

- exact node kind 与 digest match 优先配对；
- unique anchor 优先于 repeated anchor；
- parent-consistent match 优先于 cross-parent match；
- source-order tie-breaking 稳定且有文档；
- 不推断 semantic name binding、import resolution 或 control-flow analysis；
- ambiguity 或 resource exhaustion 导致的 alignment failure 是 failed outcome，不是 approximate result。

稳定 source-code change ordering 为：delete/update/move 先按 before path 排序，然后 insert
按最近 containing parent 的 after path 排序；path lexical order 使用 decoded path segment
与 numeric ordinal order。一个 logical alignment 同时产生 parent update 与 child update
时，parent 排在 child 前。Lexical P6-S1 ordering 完全沿用 RFC 0002 hunk source order。

### Source metric 与 policy

首批 source-code metric registry 提议为：

| Metric name | 含义 | Unit | Direction | Aggregation |
| --- | --- | --- | --- | --- |
| `source.nodes_compared` | visited 的 aligned syntax node | `items` | `neutral` | `count` |
| `source.nodes_changed` | 截断前的 insert/delete/update/move observation | `items` | `lower_is_better` | `count` |
| `source.tokens_changed` | lexical relation 下变化的 lexical token | `items` | `lower_is_better` | `count` |
| `source.moves` | 确定性 move observation | `items` | `lower_is_better` | `count` |
| `source.parser_errors` | 观测到的 parser error 或 recovery node | `items` | `lower_is_better` | `count` |
| `source.ignored_trivia_items` | 被显式 normalization 忽略的 comment/formatting fact | `items` | `neutral` | `count` |

Default evaluation 对 `syntax_tree` 使用 `source.syntax_tree_equality`，对 `lexical_text`
使用 `source.lexical_text_equality`，二者都观察 changed item metric，operator 为 `eq`，
threshold 为零。默认 source policy 不产生 `warn`。Full fidelity 要求没有 parser recovery，
除非已接受的 spec 显式允许 degraded recovery。

### Source resource 与 failure

```python
class SourceCodeResourceLimits:
    max_input_bytes: int = 16 * 1024 * 1024
    max_decoded_chars: int = 16 * 1024 * 1024
    max_fact_text_bytes: int = 4096
    max_tokens: int = 1_000_000
    max_nodes: int = 1_000_000
    max_depth: int = 256
    max_parser_errors: int = 0
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024
```

Limit 在分配下一个 decoded slice、token、node、alignment candidate、work unit 或 returned
change 前检查。Parser resource exhaustion 在 `decoding` 阶段产生
`failed/resource_limit_exceeded`；comparison work exhaustion 产生
`failed/compare_resource_limit`；缺失或不兼容 parser backend 是
`unavailable/backend_unavailable`；不支持的 source kind 是
`failed/source_type_unsupported`；`reject` recovery 下的 malformed source 是
`failed/decode_error`。

Source work accounting 按 relation 固定。`lexical_text` 完全使用 RFC 0002 Myers work unit。
`syntax_tree` 对每个 decoded token、每个接受到 host tree 的 parser node、每个构造的 node
digest、每个 alignment candidate-pair score、每个 visited paired node，以及每个在 detail
truncation 前 emitted 的 insert/delete/move/update change 各计一个 unit。每个 unit 都在动作前
检查。默认值尽量继承 RFC 0002 与 RFC 0006：16 MiB input 与 4 MiB payload 匹配既有
text/structured default；1,000,000 token/node ceiling 匹配 structured node ceiling；
5,000,000 work unit 匹配既有 comparison budget。P6-S1 `lexical_text` 可以依赖 RFC 0002
text limit，因为它不选择或加载 parser backend。P6-S2 在开始前必须有 adversarial evidence，
证明 token/node/work default 能在选定 parser backend 上约束 memory。

Adversarial test 必须包含极端 depth、width、token stream、重复 subtree、病态 move
ambiguity、Unicode identifier/control、混合 newline、巨大 comment、未终止 literal、
parser error 与 over-limit input。

## 源代码后端门禁

Tree-sitter 是候选 parser backend，因为架构文档已经把它列为可选源代码 parser。本 RFC
不选择 package 或 version。Source backend gate 必须记录：

- parser project、grammar project、grammar commit/version、generator version、runtime ABI
  version 与 Python binding version；
- runtime、generated grammar、binary wheel 与 build-time tool 的 SPDX license；
- wheel/source distribution size、native code、platform support 与 Python version support；
- grammar 是 bundled、local generated 还是由独立 package 提供；
- malformed input、recursion、memory allocation、native crash 与 parser error recovery
  的安全状态；
- native crash 或 hang 的 failure isolation，包括 release 前是否需要外部 worker process。

如果 backend 不能在进程内有界执行，实现门禁必须使用已批准协议的外部监督 worker，或在该
platform 返回 `backend_unavailable`。Dependency installation 仍属于用户环境；Platydiff
不会获取 grammar 或 compiler。

## PDF 比较契约

### Public intent 与 view

提议的首个 public shape 为：

```python
class PdfCompareSpec:
    kind: Literal["pdf"] = "pdf"
    views: tuple[
        Literal["binary", "extracted_text", "objects_metadata", "rendered_pages"],
        ...
    ] = ("extracted_text",)
    text: PdfTextOptions = PdfTextOptions()
    objects: PdfObjectOptions = PdfObjectOptions()
    rendering: PdfRenderOptions = PdfRenderOptions()
    artifact_policy: Literal["none"] = "none"
    limits: PdfResourceLimits = PdfResourceLimits()
```

PDF option 是封闭集合并完整序列化：

```python
class PdfTextOptions:
    order: Literal["extractor_logical"] = "extractor_logical"
    whitespace: Literal["preserve"] = "preserve"
    unicode_mapping: Literal["backend_tounicode"] = "backend_tounicode"

class PdfObjectOptions:
    metadata: Literal["compare", "ignore_document_info_dates"] = "compare"
    streams: Literal["metadata_and_digest"] = "metadata_and_digest"
    active_content: Literal["inert_inventory"] = "inert_inventory"

class PdfRenderOptions:
    page_box: Literal["media", "crop"] = "media"
    rotation: Literal["apply_page_rotation"] = "apply_page_rotation"
    resolution_dpi: int = 144
    color: Literal["srgb_8bit"] = "srgb_8bit"
    alpha: Literal["composite_white", "preserve"] = "composite_white"
    antialiasing: Literal["backend_default_recorded"] = "backend_default_recorded"
```

所有 selected PDF view 都是 required，并作为一个 all-or-nothing invocation 执行。只有每个
selected view 都达到 completed view result 时，每个 view 才能产生独立 summary count、
metric、change、transformation 与 evaluation。如果任一 selected view unavailable 或
failed，顶层 outcome 是 `unavailable` 或 `failed`，且没有 `DiffResult`；已完成 view 的工作
只作为有界 execution attempt 和 diagnostic 记录，不作为 partial result fact。组合 completed
PDF result 可以聚合 verdict，但不得在不说明 view 的情况下声称 PDF 文件简单相等。Binary
equality、extracted text equality、object/metadata equality 与 rendered-page equality 是
彼此独立的 relation。

`binary` view 复用精确字节比较语义，但记录它是一个 selected PDF view。`extracted_text`
view 比较 decoded text run、extractor 报告的 logical order、page association、Unicode
mapping 与 whitespace policy。`objects_metadata` view 比较 trailer/catalog、page tree、
object dictionary、stream metadata、embedded-file inventory、font reference、作为 inert
fact 的 action 与 document metadata，并遵循显式 ignore rule。`rendered_pages` view 在
显式 page box、rotation、color、alpha、antialiasing、transparency、resolution 与
background policy 下比较 rasterized page。

### Hostile 与 unsupported PDF feature

纯 `views=("binary",)` PDF 比较接受 encrypted PDF，因为它比较 original bytes，不解析
document。任何 selected nonbinary view 都需要 PDF parsing 或 rendering。如果任一输入已加密，
且不存在 accepted password contract，execution 在第一个观察到 encryption 的 nonbinary
worker stage 以 `failed/pdf_encrypted` 终止。不提示密码、不含 password field、不存储密码、
不绕过 permission，也不会 fallback 到 binary，除非 caller 只选择了 binary view。Permission
flag 只有在无需绕过加密即可读取时，才作为 inert metadata 记录。

Embedded file、JavaScript、launch action、submit action、remote go-to action、multimedia
action、rich media 与 external stream 默认绝不执行、下载、启动或提取。Object comparison
可以报告其有界 inert presence。Rendering backend 必须在可能时禁用或忽略 active content，
并记录 backend policy。

Malformed xref、object stream、compressed stream、incremental update、linearized file、
hybrid xref table、missing font、custom encoding、ToUnicode map、ligature、vertical
writing、transparency group、overprint、optional content group、annotation、form、page
box、rotation、crop/bleed/trim/art box 与 color profile 都是显式 case。Backend default
必须记录为 transformation 或 unavailable/degraded fact，而不是隐藏行为。

### PDF alignment 与 change

```python
class PdfChange:
    kind: Literal["pdf_change"]
    view: Literal["binary", "extracted_text", "objects_metadata", "rendered_pages"]
    operation: Literal["insert", "delete", "update", "move"]
    before_coordinate: PdfCoordinate | None
    after_coordinate: PdfCoordinate | None
    before_digest: str | None
    after_digest: str | None
    before_fact: PdfFact | None
    after_fact: PdfFact | None
```

```python
class PdfTextCoordinate:
    page: int
    run: int
    start_text_offset: int
    text_length: int

class PdfObjectCoordinate:
    object_number: int | None
    generation: int | None
    role_path: str
    key_path: str

class PdfRenderCoordinate:
    page: int
    page_box: Literal["media", "crop"]
    x: int
    y: int
    width: int
    height: int
    raster_policy_id: str

class PdfFact:
    fact_kind: Literal["text_run", "object_entry", "metadata_entry", "render_region"]
    type_name: str
    page: int | None
    text: str | None
    value_summary: str | None
    byte_length: int | None
    changed_pixels: int | None

PdfCoordinate = PdfTextCoordinate | PdfObjectCoordinate | PdfRenderCoordinate | BinarySpan
```

Coordinate 按 view 区分：

- binary 使用 `BinarySpan` 的 byte offset 和 length；
- extracted text 使用 page number、extractor text-run ordinal 与 bounded text span fact；
- objects/metadata 在稳定时使用 object number/generation，并加 canonical dictionary path
  或 metadata key；
- rendered pages 使用一基 page number、选定 page box、pixel rectangle 与 raster policy ID。

Page alignment 默认按一基 page position。Object alignment 在双方暴露相同 object
number/generation 时使用 object identity，否则使用 backend 能确定证明的 canonical object
role。Text alignment 是 page-local 且 source-order deterministic。Rendered alignment 是在
显式 raster normalization 之后的 page-local pixel coordinate alignment。任何 unsupported
alignment requirement 都产生 `failed/alignment_failed` 或
`unavailable/capability_unavailable`，而不是 content change。

Change invariant 按 view 区分。Binary view change 必须满足 `BinarySpan` invariant。
Text-run change 要求 page/run coordinate，以及有界 text fact 或 text-run digest。Object
与 metadata change 要求 canonical object coordinate 或 metadata key，且绝不内嵌 decoded
stream bytes。Render change 要求边界内 pixel rectangle、正 width/height，以及大于零的
changed pixel count。Insert 只有 after coordinate，delete 只有 before coordinate，update
有两侧 coordinate；move 只对 stable digest 匹配但 coordinate 改变的 text/object fact 合法。
稳定顺序先按 normalized spec 中的 view order，再按 page，最后按 run/object/key/rectangle
order。Reader 拒绝违反该顺序的 interleaved view。

### PDF metric 与 policy

首批 PDF metric registry 提议为：

| Metric name | 含义 | Unit | Direction | Aggregation |
| --- | --- | --- | --- | --- |
| `pdf.binary.changed_bytes` | binary view 的 byte difference | `bytes` | `lower_is_better` | `sum` |
| `pdf.text.changed_runs` | 截断前的 extracted text run change | `items` | `lower_is_better` | `count` |
| `pdf.text.compared_runs` | aligned extracted text run | `items` | `neutral` | `count` |
| `pdf.objects.changed_entries` | 截断前的 object/metadata observation | `items` | `lower_is_better` | `count` |
| `pdf.objects.compared_entries` | 已评估 object/metadata entry | `items` | `neutral` | `count` |
| `pdf.render.changed_pixels` | region grouping 前的 rendered pixel difference | `pixels` | `lower_is_better` | `sum` |
| `pdf.render.changed_pages` | 至少有一个 rendered difference 的 page | `pages` | `lower_is_better` | `count` |
| `pdf.render.compared_pages` | 已 render 和比较的 page pair | `pages` | `neutral` | `count` |

每个 selected view 都有一个默认 equality evaluation，例如 `pdf.extracted_text_equality` 或
`pdf.rendered_page_equality`，观察该 view 的 changed metric，operator 为 `eq`，threshold
为零。未来 rendered page tolerance policy 必须先定义 color space、alpha、antialiasing、
subpixel 与 aggregation 语义，才能产生 pass/warn。首批 PDF policy 不产生 `warn`。

### PDF resource 与 failure

```python
class PdfResourceLimits:
    max_input_bytes: int = 64 * 1024 * 1024
    max_fact_text_bytes: int = 4096
    max_fact_value_bytes: int = 4096
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

    # Nonbinary PDF gate 必须用 backend evidence 设置有限默认值。
    max_worker_rss_bytes: int
    max_objects: int
    max_pages: int
    max_stream_bytes: int
    max_decoded_stream_bytes: int
    max_text_runs: int
    max_render_pixels_per_page: int
    max_rendered_pages: int
    max_backend_seconds: int
    max_temp_bytes: int
    max_worker_output_bytes: int
    max_worker_processes: int
```

PDF 同时具有 whole-invocation budget 与 per-view budget。`max_input_bytes`、
`max_worker_rss_bytes`、`max_backend_seconds`、`max_temp_bytes`、
`max_worker_output_bytes`、`max_worker_processes`、`max_compare_work`、
`max_change_items` 与 `max_change_payload_bytes` 对完整 PDF invocation 累计适用。Fact
text/value ceiling 先应用到每个保留的 `PdfFact`，然后完整 change item 才计入 payload
budget。Page、object、stream、text-run 与 pixel limit 按 view 适用，同时也消耗累计 work
budget。Host 在派发每个 worker step 前、以及接受 worker 的每个有界 result chunk 前检查累计
limit。

本 RFC 现在接受的 RFC-wide 默认值仅限于上方带具体数值且对 binary 安全的字段：input
bytes、retained fact text/value bytes、comparison work、returned change count 与 returned
change payload bytes。这些 bound 不依赖 PDF parser 或 renderer，足以支持 P6-P1a。它们不
批准 object-count、page-count、stream、text-run、raster-pixel、worker RSS、timeout、
temporary-storage、worker-output 或 worker-process 的默认值。

P6-P1b、P6-P2 与 P6-P3 各自必须在自己的 evidence gate 中提供 backend-specific numeric
default，之后才能开始实现。Gate evidence 必须命名 backend/version/platform，解释每个默认值
为何可强制执行，包含针对该 limit 的 adversarial fixture，并证明 check-before-allocate 行为。
在该 evidence 存在前，schema 只记录这些字段是 required finite limit，而不是已接受的数值默认。
Decompression bomb 与 recursive object reference 必须在分配下一个 object 或 stream segment
前失败。Completed result 不依赖 wall-clock time；timeout 产生 failed 或 unavailable outcome，
不产生 partial equality claim。

接受/启动边界如下：

- P6-S1 与 P6-S2 是 source-code gate，不受 PDF backend numeric default 阻塞；
- P6-P1a 只使用上方 RFC-wide binary-safe PDF limit，因此可以在没有 nonbinary PDF backend
  numeric default 的情况下接受并启动；
- P6-P1b 在开始前必须为 text extraction 提供并论证默认 page、text-run、worker RSS、
  timeout、temp、output、process 与 stream/decode limit；
- P6-P2 在开始前必须为 object/metadata inspection 提供并论证默认 object、page、
  stream/decode、worker RSS、timeout、temp、output 与 process limit；
- P6-P3 在开始前必须为 rendering 提供并论证默认 page、rendered-page、raster-pixel、
  worker RSS、timeout、temp、output 与 process limit；
- P6-A1 仍受 artifact authority 阻塞，不因 PDF backend default evidence 而获得授权。

PDF work accounting 按 view 固定：

- whole invocation：每个 selected view dispatch 与每个 worker result chunk accepted 各计一个 unit；
- binary：RFC 0003 byte-span accounting，并对每个 retained span 加一个 unit；
- extracted text：每个 visited page、accepted text run、aligned run pair 与 emitted text change 各计一个 unit；
- objects/metadata：每个 visited indirect object、accepted dictionary key/value、accepted stream digest、accepted metadata entry、aligned entry 与 emitted object change 各计一个 unit；
- rendered pages：每个 rendered page、accepted raster tile、compared tile、emitted changed region 与 page-level aggregate 各计一个 unit。

每个 unit 都在动作前检查。Completed outcome 的 provenance 同时记录 per-view counter 与
cumulative counter；failed 或 unavailable multi-view outcome 只在 execution attempt 中记录。

Failure 保持可区分：

- 缺少 parser/text/render backend：`unavailable/backend_unavailable`；
- selected nonbinary view 遇到 encrypted input：`failed/pdf_encrypted`；
- malformed syntax 或 unsupported object graph：`failed/decode_error`；
- decompression 或 size limit：`failed/resource_limit_exceeded`；
- comparison work limit：`failed/compare_resource_limit`；
- unsupported view/backend combination：`unavailable/capability_unavailable`；
- alignment failure：`failed/alignment_failed`；
- external backend timeout/crash：根据 backend 是否已被选择并启动，使用
  `failed/comparator_failure` 或 `unavailable/backend_unavailable`。

Unavailable 表示 requested view 无法提供。Failure 表示 selected execution path 已经开始但
无法完成。除非未来 spec 显式允许并记录 lost information、backend attempt 与 policy impact，
否则禁止 degraded fidelity。

## PDF backend 与 sandbox 门禁

PDF parsing、text extraction 与 rendering 是独立 backend role。一个 gate 可以为多个 role
选择同一 backend，但 provenance 仍必须记录 role-specific availability、version、policy、
limit 与 failure。

每个 nonbinary PDF role 都在受监督的 bounded worker 中运行。首批 gate 的 conforming
implementation 不允许在进程内解析 nonbinary PDF content。Worker protocol 由 host 拥有：

- cancellation：caller 取消或 limit 触发时，host 可以终止 worker；schema 不提供 completed
  partial result；
- timeout：wall-clock timeout 会杀掉 worker process group，并记录 `pdf_worker_timeout`；
- RSS：worker 有强制 resident-memory ceiling；超过时记录 `pdf_worker_rss_exceeded`；
- temp：所有 temp file 位于 host 创建的有界 temp root，并计入 `max_temp_bytes`；
- output：stdout/stderr/protocol payload 受 `max_worker_output_bytes` 限制，raw backend
  stderr 不复制进 outcome；
- process：worker 不能派生超过 `max_worker_processes` 的进程；不支持 process supervision
  时 backend unavailable；
- network：policy 禁用 network access 与 remote resource loading；若 platform 无法对某
  backend 强制执行，该 backend unavailable；
- filesystem：worker 只接收该 view 所需的 opened source descriptor 或 host-owned temp path，
  且不能写入 temp root 或 accepted artifact root 之外。

如果 platform 无法强制 timeout、RSS、temp、output、process 或 network isolation，对应
nonbinary backend 在 document execution 前为 `unavailable/backend_unavailable`。如果受监督
worker 已启动后违反边界，selected view failed，因此 required PDF invocation 整体 failed。

每个 PDF backend review 必须记录：

- project name、distribution version、backend/library version、binary version、build
  configuration 与 platform；
- SPDX license、transitive dependency license、binary redistribution term、NOTICE/SBOM
  影响，以及适用时的 strong-copyleft isolation；
- font handling、bundled font data、substitute font、system-font discovery、CMap/encoding
  data 与 redistribution permission；
- font program、color management、image codec 与 bundled data 的 patent 或 commercial
  licensing 考量；
- malformed-input security history 与当前 advisory；
- deterministic rendering setting 与 platform variance；
- resource 与 timeout enforcement strategy。

外部 subprocess 必须以 argument array 和 `shell=False` 调用。Host 提供有界 temporary
directory、只继承 allowlist 中的环境变量、close-on-exec descriptor、output-byte limit、
timeout、exit-code validation 与 cleanup。Conformance profile 禁止 network access、
remote resource loading、active content execution 以及写入 host temp/artifact root 之外。
如果 platform 无法执行必要边界，该 backend 在该 platform 上为 unavailable。

## Artifact 与 renderer 边界

Source-code 首批 gate 不产生 artifact。PDF 首批 gate 也不产生 page-image 或 heatmap 文件。
Rendered-page 比较可以计算内部 raster，并把 hash、dimension、page box 与 changed pixel
region 记录为 validated fact，但除非单独接受 artifact gate，否则不得写出这些 raster。

后续若存在 artifact gate，每个 artifact 都必须使用 RFC 0001 的 `ArtifactRef` URI 验证、
显式 artifact root、SHA-256 校验、有界 byte size、稳定 media type、确定性文件名与 RFC
0004 的安全展示规则。Renderer 或 UI 不得在比较后重读原始 PDF 来创建 preview，因为这会绕过
snapshot、password、resource、backend、detail-mode 与 mutation contract。

Terminal 与 JSON renderer 只能以 control-safe escaping 展示 validated source/PDF fact。
PDF text extract、object name、metadata value、font name、JavaScript snippet、URL 与 file
name 都是不受信任的比较内容，可能含有 secret 或 control。Renderer 不得执行 link、打开
embedded file、获取 remote asset 或派生新 view。

## 交付门禁、commit 与测试

这些 gate 是提议计划，不是实现授权。

### P6-S1：source-code schema 与 lexical relation

1. `feat(core): add source-code schema contracts`
2. `feat(source): add explicit lexical source-code comparison`
3. `feat(cli): add explicit source-code comparison commands`
4. `docs: document source-code comparison contracts`

Gate：schema-v5 migration test 通过；既有 v1/v2 与已实现 predecessor schema fixture
保持兼容；`language` 是必填；不存在自动语言探测或 text fallback；lexical relation 对 Python
与 JavaScript 有确定性 token/text fixture；limit、Unicode、newline、malformed input 与
renderer escaping 均有测试。

### P6-S2：source-code syntax-tree relation 与 parser backend

1. `build(source): add reviewed optional parser backend`
2. `feat(source): add bounded syntax-tree comparison`
3. `test(source): add parser compatibility and adversarial corpus`
4. `docs: document parser provenance and structural semantics`

Gate：backend dependency/license/platform review 完成；grammar version 在 provenance 中 pin；
parser recovery、comment、formatting、stable node path、alignment、insert/delete/update/move
语义、work limit、native failure behavior 与 deterministic repeated run 通过。该 gate
开始前必须提供 adversarial evidence，证明选定 parser backend 能强制 token、node、work、
input 与 payload default。

### P6-P1a：PDF schema 与 binary view

1. `feat(core): add PDF schema contracts`
2. `feat(pdf): add explicit PDF binary view`
3. `feat(cli): add explicit PDF binary comparison commands`
4. `docs: document PDF binary view semantics`

Gate：重新验证 schema migration；`artifact_policy` 只接受 `none`；纯 binary view 把
encrypted PDF 当作字节接受；binary view 复用 exact binary semantics，同时命名 PDF view；
malformed PDF 不被解析；RFC-wide binary-safe resource default、payload truncation 与无
fallback 均由 generated fixture 覆盖。该 gate 可以在没有 nonbinary PDF backend numeric
default 的情况下接受并启动。

### P6-P1b：PDF extracted-text view

1. `feat(pdf): add supervised PDF text extraction worker`
2. `feat(pdf): add explicit PDF extracted-text view`
3. `feat(cli): add explicit PDF extracted-text comparison commands`
4. `docs: document PDF text extraction semantics`

Gate：schema migration 继续兼容 P6-P1a；任何 encrypted input 返回
`failed/pdf_encrypted`；text extraction 只在受监督 bounded worker 中运行；multi-view
all-or-nothing 行为有测试；text order、font/encoding、Unicode mapping、page alignment、
worker isolation、cumulative resource、backend provenance 与无 fallback 均由 generated
fixture 覆盖。该 gate 开始前必须提供并论证默认 page、text-run、worker RSS、timeout、temp、
output、process 与 stream/decode limit。

### P6-P2：PDF object/metadata view

1. `feat(pdf): add bounded object and metadata comparison`
2. `test(pdf): add hostile object graph and metadata corpus`
3. `docs: document PDF object comparison semantics`

Gate：xref/object stream/incremental update 处理、active-content inventory、embedded-file
inventory、metadata ignore policy、object alignment、stream limit、decompression bomb、
malformed reference 与 deterministic canonical ordering 通过。该 gate 开始前必须提供并论证
默认 object、page、stream/decode、worker RSS、timeout、temp、output 与 process limit。

### P6-P3：无 artifact 的 PDF rendered-page view

1. `build(pdf): add reviewed optional rendering backend`
2. `feat(pdf): add bounded rendered-page comparison`
3. `test(pdf): add rendering determinism and sandbox profile`
4. `docs: document rendered-page backend constraints`

Gate：renderer backend license/security/platform review 完成；page box、rotation、color、
alpha、transparency、antialiasing、font substitution、pixel limit、subprocess timeout、temp
limit、changed-region grouping 与 platform variance 均有测试。该 gate 开始前必须提供并论证
默认 page、rendered-page、raster-pixel、worker RSS、timeout、temp、output 与 process
limit。不写入 page-image 或 heatmap artifact。

### P6-A1：rendered page 的可选 artifact gate

1. `feat(artifacts): add PDF rendered-page artifact writer`
2. `feat(artifacts): add PDF heatmap artifact writer`
3. `docs: document PDF artifact safety and retention`

Gate：RFC 0001 `ArtifactRef` validation、RFC 0004 renderer/UI boundary、safe artifact root、
hash verification、deterministic name、no-clobber output、privacy warning、CI retention
guidance 与无 source reread 通过。该 gate 不由 P6-P3 隐含授权。

每个 implementation gate 都运行 Ruff format/lint、strict mypy、完整 pytest、build、
wheel/sdist inspection、documentation link check、package content inspection、涉及 package
的 dependency/license review，以及 secret/path leak scan。Source/PDF gate 还需要 corpus
provenance record 与精确 backend version capture。可选后端缺失时，相关测试必须以明确原因
skip；skipped test 不是 passing evidence。

## 后续 callback

源代码自动探测必须在 RFC 0003 的后继 RFC 中定义 language 与 modality probe budget、
suffix/content/shebang precedence、parser availability interaction、ambiguity、pair selection
与 attribution。PDF 自动探测必须在同一个或另一个后继 RFC 中定义 magic-byte、version、
binary/PDF ambiguity、encrypted-file probing 与 view selection。

SDK v2 必须先定义 source/PDF request view、source service、lifecycle stage、backend role、
artifact authority、compatibility receipt、version negotiation、必要时的 out-of-process
isolation 与 schema migration，第三方 source/PDF comparator 才能执行。SDK v1.1 仍只支持
text/binary。

语义源代码比较需要单独契约来定义 runtime、type system、macro/preprocessor、import graph、
dependency resolution、platform、compiler/interpreter version、side effect 与 false-equivalence
风险。PDF OCR、tagged-PDF accessibility comparison、form appearance regeneration、redaction
validation、digital signature 与 archival conformance 都是独立契约。

更丰富的展示回到 RFC 0004。UI 可以导航 validated source node、PDF page、object、text run
与 artifact ref，但它自身不能比较、获取、渲染、OCR、提取或执行源文档。

## Lifecycle 与 failure table

| Scenario | Required terminal behavior |
| --- | --- |
| 显式 source `lexical_text`，stable input | RFC 0002 text lifecycle 与 exact decoded-line semantics；predecessor fixture gate 通过后，在提议 schema v5 下产生 completed source-code outcome。 |
| 显式 source `syntax_tree`，缺少 parser backend | `resolving/unavailable/backend_unavailable`；没有 `DiffResult`。 |
| 显式 source `syntax_tree`，`reject` recovery 下 source malformed | `decoding/failed/decode_error`；没有 text fallback，也没有 `DiffResult`。 |
| 显式 source `syntax_tree`，parser/resource bound exceeded | `decoding/failed/resource_limit_exceeded`；没有 partial result。 |
| 显式 source `syntax_tree`，alignment ambiguity 或 work bound exceeded | `aligning/failed/alignment_failed` 或 `comparing/failed/compare_resource_limit`；没有 approximate result。 |
| PDF `views=("binary",)`，encrypted input | 若 byte limit 满足，则对 original bytes 完成 binary-view comparison。 |
| PDF 包含任一 nonbinary view 且 input encrypted | `decoding/failed/pdf_encrypted`；不 fallback 到 binary，且没有 `DiffResult`。 |
| PDF nonbinary backend unavailable，或 platform 无法监督 worker | `resolving/unavailable/backend_unavailable`；不启动 worker。 |
| PDF required multi-view run 中早期 view failed | 顶层 failed/unavailable outcome；已完成的早期 view work 只进入 execution attempt。 |
| PDF worker timeout/RSS/temp/output/process/network bound exceeded | selected view 在观测 stage failed；required all-or-nothing invocation 没有 `DiffResult`。 |
| P6-A1 前请求 PDF artifact | `validating/failed/invalid_spec`；`artifact_policy` 只接受 `none`。 |

## 参考

- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
- [PDF 32000-2:2020](https://www.iso.org/standard/75839.html)
- [PDF Association: PDF 2.0 application notes](https://pdfa.org/resource/pdf-2-0-application-notes/)
