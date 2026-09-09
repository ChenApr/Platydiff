# RFC 0008：源代码与 PDF 比较

[English documentation](0008-source-code-and-pdf-comparison.md)

- Status: Proposed
- Date: 2026-09-10
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
| RFC 0003 的 snapshot path 管理有界 replay、hash、mutation check 与安全 label。 | Source/PDF gate 依赖它前必须重新验证 snapshot 实现；并发 Phase 4/5 工作只作为设计证据。 |
| RFC 0004 要求 renderer 与 UI 消费 validated outcome，不重读 source 或重算事实。 | Source/PDF renderer 只能展示 validated fact 与 inert artifact ref；page image 与 heatmap 需要 artifact gate。 |
| RFC 0005 实现的 SDK v1.1 只覆盖 text/binary detector、comparator 与 renderer handle。 | Source/PDF plugin comparator 需要显式 SDK-v2 callback，不能通过 SDK v1.1 添加。 |
| RFC 0006 接受 schema v3 用于 structured-data 内建 spec/change，但其门禁仍未实现。 | Phase 6 必须在 public schema implementation 前审计实际 schema-v3 前驱。 |
| RFC 0007 在实际 schema-v3 前驱审计后，为首个 image slice 预留 schema v4。 | Phase 6 source/PDF 使用下一个全局 successor schema v5，且不争用或重开 image v4。 |
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
- 与 v1、v2、实际 P4 schema-v3 前驱和 Phase 5 schema-v4 预留兼容；
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
| P6X2 | 审计实际 v3 前驱与 Phase 5 v4 预留后，Phase 6 内建 source/PDF spec/change variant 使用全局分配的 schema v5 successor。 | 扩展 v1/v2 closed union、重开 v3、复用 image v4，或在实际实现前假设 RFC 0006 的细节。 |
| P6X3 | SDK v1.1 下拒绝 source/PDF plugin comparator；第三方 source/PDF modality 需要 SDK v2。 | 允许 plugin 安装引入 source/PDF spec 或内建 change kind。 |
| P6X4 | 独立授权 source-code 与 PDF 实现门禁。 | 因为二者都需要 parser 而把 Phase 6 当作一个批次。 |
| P6X5 | 保持 RFC 0004 artifact/UI 工作独立；Phase 6 fact 只有在 artifact writer gate 后才能引用 artifact。 | 让 PDF rendering 隐式创建 page image 或 HTML report。 |
| P6X6 | 每个依赖代码状态的假设都是 revalidation gate，包括 P4-A1 和 Phase 5 工作。 | 把并发未合并工作当成实现或合并证据。 |
| P6X7 | 后端/parser 开始后，禁止改变比较 relation 的 fallback。 | 失败时静默 fallback 到 text、binary、另一个 parser、另一个 renderer 或 approximate semantics。 |
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
| PDF3 | 没有 accepted password contract 时，加密 PDF 不受支持；首批 gate 不提示密码也不存储密码。 | 交互式提示、在 spec 中保存密码，或 fallback 到 binary。 |
| PDF4 | Embedded file、JavaScript、launch action、network action 与 form action 是 inert fact 或显式 unsupported feature；默认绝不执行或提取。 | 比较时执行或解引用 active document content。 |
| PDF5 | PDF parser、text extractor 与 page renderer 是分开的有界后端，具有 version provenance 与 failure isolation。 | 使用单体后端并隐藏哪个 view 失败。 |
| PDF6 | 若选择外部 PDF tool，必须使用 argument array、禁用 shell、有界 temp dir、timeout、output limit 且无网络。 | 让后端专用命令行隐式负责安全。 |
| PDF7 | Page、object 与 text alignment 都是确定性的 view-specific 行为；unavailable/degraded/failure 状态保持可区分。 | 把 alignment failure 合并成内容变化。 |
| PDF8 | Rendered-page artifact、thumbnail 与 heatmap 在写入或链接任何文件前需要兼容 RFC 0004 的 artifact gate。 | 把 page image 作为比较副作用输出。 |
| PDF9 | Font、encoding、transparency、page box、rotation、color、malformed xref、stream 与 decompression bomb 是显式 backend/resource case。 | 接受 backend default 且不记录 transformation 和 limit。 |
| PDF10 | PDF fixture 必须生成或明确可再分发，并包含 hostile/malformed case，且不使用受限文档。 | 使用任意真实世界 PDF 作为 test corpus。 |

## Schema 与兼容性契约

Phase 6 使用全局分配的 schema v5 successor。分配顺序是稳定人工决策：P4 structured data
使用 schema v3，P5 image 使用 schema v4，P6 source/PDF 使用 schema v5，P7 audio/video 使用
schema v6。Design、backend、dependency 与 fixture research 可以跨 phase 并发推进，但 public
schema implementation 与 merge 必须遵守此前驱顺序及其兼容性 fixture。

Schema v5 是实际合并 schema-v4 前驱的 additive semantic successor：

```python
CompareSpecV5 = CompareSpecV4 | SourceCodeCompareSpec | PdfCompareSpec
ChangeV5 = ChangeV4 | SourceCodeChange | PdfChange
```

如果 P4-A1 schema v3 没有在 `main` 上实现、实际实现与 RFC 0006 不一致，或 Phase 5 schema
v4 缺失或改变其分配，Phase 6 实现门禁必须停止并先修订本文。Source/PDF schema 工作依赖真实的
v3/v4 reader、writer、upgrader 与 fixture，而不是只依赖已接受的设计文本。无论哪种情况：

- 既有内建 text、binary 与 auto 调用保持 schema v1；
- 既有 `PluginHost` text/binary 调用保持 schema v2；
- 已合并 Phase 4 structured-data 调用保持实际实现的 schema v3；
- 已合并 Phase 5 image 调用保持 schema v4；
- 内建 source-code 与 PDF spec 使用 schema v5，即使 validation、sourcing、resolution、
  parser/backend、rendered-page backend、alignment 或 comparison 阶段失败也是如此；
- v5 reader 接受 v1/v2/v3/v4/v5 payload，并先按显式 schema version 分派，再检查 spec 或
  change kind；
- 显式 v1/v2/v3/v4-to-v5 migration helper 保留原始事实，只加入文档化的中性默认值；
- byte-stable v1/v2 fixture、P4 schema-v3 fixture、P5 schema-v4 fixture 与 P6 v5 round-trip
  fixture 保持在兼容性 corpus 中；
- source-code 或 PDF outcome 不存在自动 downgrade。只有事实能由目标旧 schema 表示时，才允许
  lossless helper downgrade；
- unknown built-in spec/change kind 仍然非法；unknown namespaced extension change 保持 RFC 0001 行为。

选定 schema 必须为每个新 spec field、change kind、metric、evaluation rule、
transformation ID、backend identity 与 problem detail 定义稳定 JSON 名称。每个 Phase 6
implementation gate 开始时与 merge 前都必须重新验证 schema predecessor 假设。

## 设计-契约矩阵

| 区域 | Source-code contract | PDF contract |
| --- | --- | --- |
| Public spec | `SourceCodeCompareSpec(language, relation, parser, normalization, alignment, detail_mode, limits)` | `PdfCompareSpec(views, passwords policy, backend choices, text/render/object options, artifact policy, limits)` |
| 首批 relation | `lexical_text` 与 `syntax_tree`；`semantic` 保留且 unavailable | `pdf.binary`、`pdf.extracted_text`、`pdf.objects_metadata`、`pdf.rendered_pages` |
| Default policy | changed item 为零则 pass，否则 fail | 每个选定 view 都有自己的零变化 evaluation；若任何必需 view fail，聚合 verdict fail |
| Change | `SourceCodeChange` 包含 node path、operation、language、node kind、relation 与 digest/fact field | `PdfChange` 按 view 标记，并包含 page/text/object/render coordinate 与 digest/fact field |
| Metric | changed nodes/tokens、parser errors、moved nodes、compared nodes、formatting/comment changes | changed bytes、text runs、object entries、metadata entries、rendered pixels/pages、backend warnings |
| Artifact | 首批 source gate 不产生 artifact | 独立 artifact gate 前不产生 artifact；rendered-page fact 可含 digest 但不含文件 |
| Backend | 可选 parser backend，例如 Tree-sitter；审查前不加入默认 dependency | 独立 parser/text/render backend；外部 subprocess 需要 sandbox 规则 |
| Fallback | source parsing 开始后没有 text fallback | PDF view 之间不 fallback，也不 fallback 到 binary，除非显式选择 binary view |
| Plugin path | source-code modality 需要 SDK v2 | PDF modality 需要 SDK v2 |
| Verification | language fixture、parser version、AST path、move tie-break、malformed/adversarial limit | generated PDF、malformed/xref/stream case、encryption、font、rendering determinism、sandbox limit |

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

首批 gate 要求显式 `language`。文件 suffix、shebang、modeline、package metadata、content
probe 与 backend parser guess 不用于语言探测。后续 source-detection RFC 可以定义有界
language probing、ambiguity 与 attribution。在此之前，语言不匹配会在实际观察到的阶段
产生 `failed/decode_error` 或 `unavailable/backend_unavailable`；它不会用另一种语言或
`TextCompareSpec` 重试。

`lexical_text` 是 source-specific tokenization 规则下的行/标记文本比较，不得声明语法
等价。`syntax_tree` 比较 parser tree structure 与选定 token/comment fact。`semantic`
保留给未来契约，用于定义 runtime、type-system、macro、import、environment 与 toolchain
边界；首批 gate 对它返回 `unavailable/capability_unavailable`。

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
/<child-kind>#<ordinal-among-siblings-of-kind>@<ordinal-among-all-siblings>
```

具体 wire syntax 必须在实现门禁发布前固定；必需不变量是 path 在重复运行中确定，不依赖
backend object identity，并且在无关 sibling 未变化时保持稳定。Byte range 与 line/column
span 可以作为 fact 记录，但 node path 是主要结构坐标。

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

Insert 只有 after coordinate。Delete 只有 before coordinate。Update 在已对齐 node 上有两侧
coordinate，并记录 node kind、token、trivia 或 child-shape fact 变化。Move 有两侧
coordinate，用于报告在 move policy 下 digest 与选定 identity fact 匹配但 path 变化的
node。Move 是 observation，不是 patch operation，而且只有 alignment algorithm 可以确定性
证明时才输出。否则同一变化表示为 delete 加 insert。

Alignment 是确定性的：

- exact node kind 与 digest match 优先配对；
- unique anchor 优先于 repeated anchor；
- parent-consistent match 优先于 cross-parent match；
- source-order tie-breaking 稳定且有文档；
- 不推断 semantic name binding、import resolution 或 control-flow analysis；
- ambiguity 或 resource exhaustion 导致的 alignment failure 是 failed outcome，不是 approximate result。

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
    artifact_policy: Literal["none", "record_refs"] = "none"
    limits: PdfResourceLimits = PdfResourceLimits()
```

每个 selected view 都产生独立 summary count、metric、change、transformation 与 evaluation。
组合 PDF result 可以聚合 verdict，但不得在不说明 view 的情况下声称 PDF 文件简单相等。
Binary equality、extracted text equality、object/metadata equality 与 rendered-page
equality 是彼此独立的 relation。

`binary` view 复用精确字节比较语义，但记录它是一个 selected PDF view。`extracted_text`
view 比较 decoded text run、extractor 报告的 logical order、page association、Unicode
mapping 与 whitespace policy。`objects_metadata` view 比较 trailer/catalog、page tree、
object dictionary、stream metadata、embedded-file inventory、font reference、作为 inert
fact 的 action 与 document metadata，并遵循显式 ignore rule。`rendered_pages` view 在
显式 page box、rotation、color、alpha、antialiasing、transparency、resolution 与
background policy 下比较 rasterized page。

### Hostile 与 unsupported PDF feature

除非后续决策接受 password API，首批 gate 不支持 encrypted PDF。没有该决策时，加密输入在
检测到加密的阶段返回 failed 或 unavailable outcome，不提示密码、不含 password field，也
不 fallback 到 text 或 rendering。Permission flag 只有在无需绕过加密即可读取时，才作为
inert metadata 记录。

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
    max_objects: int = 1_000_000
    max_pages: int = 10_000
    max_stream_bytes: int = 256 * 1024 * 1024
    max_decoded_stream_bytes: int = 256 * 1024 * 1024
    max_text_runs: int = 1_000_000
    max_render_pixels_per_page: int = 100_000_000
    max_rendered_pages: int = 1_000
    max_backend_seconds: int = 30
    max_temp_bytes: int = 512 * 1024 * 1024
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024
```

具体默认值仍是暂定，接受前必须基于后端行为重新验证。Limit 覆盖 original bytes、parsed
object count、stream decompression、page count、text-run count、raster pixel count、
temporary disk use、subprocess output、deterministic comparison work、returned item 与
payload bytes。Decompression bomb 与 recursive object reference 在分配下一个 object 或
stream segment 前失败。除有界外部 backend supervision 外，正常 result 不依赖 wall-clock
time；timeout 产生 failed 或 unavailable outcome，不产生 partial equality claim。

Failure 保持可区分：

- 缺少 parser/text/render backend：`unavailable/backend_unavailable`；
- encrypted unsupported input：`failed/decode_error` 或实现门禁选择的新稳定 encryption problem；
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

Gate：schema-v5 migration test 基于实际 v3/v4 前驱链通过；既有 v1/v2/v3/v4 fixture 保持兼容；
`language` 是必填；不存在自动语言探测或 text fallback；lexical relation 对 Python 与 JavaScript
有确定性 token/text fixture；limit、Unicode、newline、malformed input 与 renderer escaping 均有测试。

### P6-S2：source-code syntax-tree relation 与 parser backend

1. `build(source): add reviewed optional parser backend`
2. `feat(source): add bounded syntax-tree comparison`
3. `test(source): add parser compatibility and adversarial corpus`
4. `docs: document parser provenance and structural semantics`

Gate：backend dependency/license/platform review 完成；grammar version 在 provenance 中 pin；
parser recovery、comment、formatting、stable node path、alignment、insert/delete/update/move
语义、work limit、native failure behavior 与 deterministic repeated run 通过。

### P6-P1：PDF schema、binary 与 extracted-text view

1. `feat(core): add PDF schema contracts`
2. `feat(pdf): add explicit PDF binary and extracted-text views`
3. `feat(cli): add explicit PDF comparison commands`
4. `docs: document PDF text extraction semantics`

Gate：重新验证 schema migration；encrypted/malformed PDF 安全失败；binary 与 extracted-text
view 保持独立；text order、font/encoding、Unicode mapping、page alignment、resource
limit、backend provenance 与无 fallback 均由 generated fixture 覆盖。

### P6-P2：PDF object/metadata view

1. `feat(pdf): add bounded object and metadata comparison`
2. `test(pdf): add hostile object graph and metadata corpus`
3. `docs: document PDF object comparison semantics`

Gate：xref/object stream/incremental update 处理、active-content inventory、embedded-file
inventory、metadata ignore policy、object alignment、stream limit、decompression bomb、
malformed reference 与 deterministic canonical ordering 通过。

### P6-P3：无 artifact 的 PDF rendered-page view

1. `build(pdf): add reviewed optional rendering backend`
2. `feat(pdf): add bounded rendered-page comparison`
3. `test(pdf): add rendering determinism and sandbox profile`
4. `docs: document rendered-page backend constraints`

Gate：renderer backend license/security/platform review 完成；page box、rotation、color、
alpha、transparency、antialiasing、font substitution、pixel limit、subprocess timeout、temp
limit、changed-region grouping 与 platform variance 均有测试。不写入 page-image 或 heatmap
artifact。

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

## 参考

- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
- [PDF 32000-2:2020](https://www.iso.org/standard/75839.html)
- [PDF Association: PDF 2.0 application notes](https://pdfa.org/resource/pdf-2-0-application-notes/)
