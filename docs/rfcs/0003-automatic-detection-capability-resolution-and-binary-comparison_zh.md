# RFC 0003：自动探测、能力解析与二进制比较

[English documentation](0003-automatic-detection-capability-resolution-and-binary-comparison.md)

- 状态：Proposed
- 日期：2026-09-07
- Owners：Platydiff 维护者
- 实现 owner：等待接受后指派

## 摘要

本 RFC 提议 Phase 2：有界的自动模态探测、确定性能力解析，以及 strict 二进制
比较。它在不发布第三方插件协议的前提下扩展 Phase 1 流水线。本 RFC 处于
`Proposed` 时，其中任何内容都不授权实现。

本提议保持 [RFC 0001](0001-comparison-outcome-and-diff-result_zh.md) 对执行终态和
已完成差异的分离，并遵循 [RFC 0002](0002-development-phases-and-text-slice_zh.md)
对后续阶段的 callback 门禁。显式文本行为继续兼容 Phase 1。

## 范围

Phase 2 将增加：

- 显式的 `AutoCompareSpec` 和 `BinaryCompareSpec`；
- 对路径、字节和文本来源的有界检查；
- 在内置 text 与 binary 能力之间进行确定性选择；
- 采用有界流式读取、且不受哈希碰撞影响的精确字节比较；
- 稳定的探测与解析 provenance；
- `platydiff binary` 与自动探测 CLI 路由；
- 覆盖现有全部 Phase 1 路由与 schema payload 的兼容性测试。

Phase 2 不增加：

- 第三方 entry point discovery、插件 SDK 或公共 registry；
- 除现有显式 UTF-8 选择以外的编码探测；
- 归档展开、目录遍历、stdin、URL、pipe、device、socket 或递归比较；
- 近似二进制相似度、块匹配、patch 生成或内嵌字节 payload；
- HTML、TUI、桌面或本地 Web renderer；
- JSON/YAML、table、array、image、source code、PDF、audio 或 video 语义。

## 公共意图与内部请求

`CompareSpec` 继续作为比较意图的公共描述：

```python
CompareSpec = AutoCompareSpec | TextCompareSpec | BinaryCompareSpec

compare(before: Source, after: Source, spec: CompareSpec) -> CompareOutcome
```

显式 `TextCompareSpec` 或 `BinaryCompareSpec` 跳过 `detecting`。只有
`AutoCompareSpec` 启用探测。Python 来源类型、文件后缀或 MIME 标签不得静默改变
显式 specification。

Phase 2 的 `CapabilityRequest` 是 core/resolver 私有值。它不从 `platydiff` 导出，
不被 `compare` 接受，也没有公共 JSON schema。这样可以先用两个内置能力验证边界，
再由 Phase 3 考虑插件协议。其确定性内部形式为：

```text
request_version: 1
operation: compare
requested_modality: auto | text | binary
resolved_modality: text | binary | null
source_kinds: ordered(before, after)
semantic_class: exact
required_features: ordered stable identifiers
intent: normalized CompareSpec without resource limits
limits: normalized ExecutionLimits
```

不变量是：探测/解析前 `resolved_modality` 为 null，之后必须精确确定。
`semantic_class="exact"` 禁止近似 fallback。request version 是内部实现版本，而非
`schema_version`；debug 表示不持久化，也不作为输入。选定意图和限制通过现有
comparison provenance 与资源使用记录保存。

在 resolver 边界，比较意图与执行限制必须分离。Phase 2 应引入内部
`ExecutionLimits` 规范化模型，并把现有 schema-v1 `TextCompareSpec.limits` 转换到
该模型；Phase 1 公共字段保持不变。未来 schema 是否把 limits 从所有 spec 中移出
另行决定；Phase 2 不得创建两个互相冲突的公共 limits 来源。

## 探测契约

### 有界证据收集

探测对每个来源最多读取开头 `max_detection_bytes`。它使用随后比较会消费的同一
已打开来源快照，或由该快照持有的可重放有界前缀。探测不得按名称打开路径，然后
比较另一次解析得到的路径。TextSource 提供显式文本信号；byte 与 path 来源需要
内容证据。

Phase 2 内置 detector 只能使用确定性证据：

- source kind；
- 有界字节前缀及长度；
- 检查前缀的 strict UTF-8 有效性；
- NUL 与控制字符证据；
- 实现文档明确枚举的稳定内置 magic signature（如有）。

文件后缀与操作系统 MIME 数据库可以作为弱 diagnostic 证据记录，但在 Phase 2
不得决定选中模态。locale、墙钟时间、文件系统枚举顺序和网络服务均禁止作为输入。

### 探测候选与 confidence

每个来源产生零个或多个 candidate record：

```text
modality_id: text | binary
confidence: integer 0..1000
detector_id: stable identifier
detector_version: implementation version
priority: non-negative integer
evidence_codes: ordered stable identifiers
```

`confidence` 是确定性的证据分数，不是概率或正确性承诺。分数只能在同一
detector/version 和 policy 下比较。execution record 必须在 diagnostic details 或
capability attempts 中暴露 detector/version、生效阈值、来源候选、pair 候选及最终
disposition，但不得暴露被检查的输入字节。

只有当模态对两个输入都 eligible，且某内置 capability 可以满足请求时，pair
candidate 才存在；其分数取两个来源分数的最小值。同一模态的重复 candidate
折叠为一个 record：保留最高分，再取最低 detector priority，并按稳定排序保留
所有 evidence code。

### 排序与歧义

eligible pair candidate 使用如下全序：

1. pair confidence 降序；
2. detector priority 升序；
3. capability priority 升序；
4. modality identifier 升序；
5. capability identifier 和 backend identifier 升序。

最后的 identifier 保证输出确定性，但不得用来静默解决语义歧义。只有候选达到
配置的最低 confidence，且领先第二名达到配置的 ambiguity margin，才可选中。
否则探测以 `unavailable` 结束：

- 没有 eligible candidate 达到最低值时为 `detection_no_match`；
- 多个 eligible candidate 差距过小时为 `detection_ambiguous`。

精确的显式类型是 Phase 2 的用户 override，并跳过 confidence、阈值和 tie 处理。
Phase 2 不增加文件名 override 或“best effort”开关。auto 选择 unavailable 时，
消息必须提示用户显式选择 `text` 或 `binary`。

最低值和 ambiguity margin 的数值属于 decision ledger 中的接受决策。它们必须是
normalized auto spec 与 provenance 中的常量，不能是隐藏调参。

## 能力解析

Phase 2 内部 registry 只包含内置 record。record 包含稳定 capability ID、模态、
semantic class、实现版本、backend ID 与版本、priority、支持的 source kind、必需
feature，以及不执行输入比较的 availability probe。

注册顺序不影响结果。解析按 capability ID 与 backend ID 去重，拒绝重复注册，并
按上述排序字段排序；每个被考虑的 entry 都记录为 selected 或 rejected。稳定拒绝
原因包括：

- `modality_mismatch`；
- `semantic_class_mismatch`；
- `source_kind_unsupported`；
- `required_feature_missing`；
- `backend_missing`；
- `backend_version_unsupported`；
- `lower_priority`。

内置标准库 text 与 binary comparator 不需要可选 backend。模型仍区分可选 backend
缺失，以便在 Phase 3 前验证 execution 契约。

没有兼容 capability 或缺失必需 backend，在 `resolving` 产生 `unavailable`；输入
I/O、非法 spec、资源耗尽、读取期间来源变化、comparator failure 和程序缺陷在其
实际边界产生 `failed`。已知 capability 缺失不得转成 `internal_error`，comparator
failure 也不得报告为内容不同。

auto 模式的阶段前缀为：

```text
validating -> sourcing -> detecting -> resolving -> ...
```

显式 text 或 binary 模式保持：

```text
validating -> sourcing -> resolving -> ...
```

选中的 capability 与 backend 在 `ExecutionRecord.attempts` 出现一次。rejection 按
确定性 rank 排在 selection 之前。探测 unavailable 终止于 `detecting`；能力
unavailable 终止于 `resolving`。

## 精确二进制比较

### 语义与算法

提议的内置 comparator 为：

```text
comparator_id: binary
backend_id: stdlib
algorithm_id: binary.exact.stream.v1
relation: 仅当字节长度和每个字节相等时为 equal
policy: equal -> pass; different -> fail
fidelity: full
```

它以有界 chunk 读取两个输入并比较实际字节。SHA-256 用于 provenance 与缓存证据，
但 digest 相等不能单独建立 `relation="equal"`；必须实际字节相等且 EOF 一致。
因此声明的 relation 不受哈希碰撞影响。

空输入合法。binary 显式选择时，`TextSource` 按其 strict UTF-8 字节编码比较，并
记录该 transformation。`BytesSource` 已是不可变快照。path input 对探测、比较和
哈希使用每个来源各自唯一的一次已打开文件描述符。

### 来源安全与可复现性

读取路径前，实现用 close-on-exec 和 nonblocking safeguard 打开它，再对 descriptor
执行 `fstat`。最终目标必须是 regular file。目录、FIFO、device、socket 和其他
special file 必须在不阻塞的情况下失败。只有 symlink 打开的目标为 regular file
时才允许；provenance 记录 path source，但不记录绝对或解析后的本地路径。

descriptor 初始和最终 metadata 包括平台可用的 device、inode/file ID、byte length
和纳秒修改时间。在观察到的读取窗口内检测到变化时，返回
`failed/source_changed`，且不生成 `DiffResult`。streamed byte count 独立于声明
size 检查。这可检测普通 mutation，但不能证明恶意 writer 没有修改后恢复全部可见
metadata；input SHA-256 仍标识实际读到的字节。

Python API 继续传播 `KeyboardInterrupt`、`SystemExit` 和 `MemoryError`。schema v1
没有 cancelled outcome。CLI 可在现有边界抑制未知 traceback，但不得把 interrupt
转为成功 outcome。

### Binary change、metric 与 limits

提议的内置 `BinarySpan` 使用 `kind="binary_span"`，包含：

```text
before_offset: zero-based byte offset
before_length: non-negative byte length
after_offset: zero-based byte offset
after_length: non-negative byte length
```

它不内嵌字节内容。在重叠长度中，极大连续的不等字节 run 变为 before/after 长度
相等的 span；末尾长度差形成一个最终 insertion 或 deletion span。span 按来源顺序、
互不重叠，是观察到的不匹配范围，而不是最小 insert/delete script 或 patch。

完整算法统计全部 span 和不匹配字节，同时只保留有界的来源顺序前缀。因此明细
limit 可以产生 `truncated` `ChangeSet`，但不改变 relation、verdict 或 fidelity。
输入或 work budget 耗尽产生 `failed`，不得产生 `partial` 或假定 difference。

结果至少记录 finite metric：`different_bytes`、`before_bytes` 和 `after_bytes`，unit
均为 `bytes`；同时记录匹配的 summary count 和两个 input hash。`different_bytes`
等于对齐位置的不等字节数加上长度差绝对值。resource provenance 记录 byte limit、
实际读取字节、chunk size、返回 change 数和保留的 canonical change payload bytes。

## CLI 与 Python 兼容性

现有调用保持不变：

```text
platydiff compare --type text BEFORE AFTER
platydiff text BEFORE AFTER
```

Phase 2 提议：

```text
platydiff compare --type binary BEFORE AFTER
platydiff binary BEFORE AFTER
platydiff compare --type auto BEFORE AFTER
```

省略 `--type` 是进入 auto 还是继续作为用法错误，尚未决定。在该决策被接受前，
文档与测试必须使用显式 `--type auto`。text-only flag 必须在 binary 或 auto 路由被
拒绝，除非选定 spec 已定义其含义。现有 shell exit `0/1/2/3` 保持不变；探测或
解析 unavailable 映射为 `3`，parser misuse 映射为不产生 outcome 的 `2`。

JSON 输出仍是 stdout 上的单个 outcome envelope。人类消息与 terminal renderer
必须转义不可信 label 和控制字符，不得包含绝对路径、检查过的字节内容或 traceback。
现有 path、artifact URI、stdout/stderr 和 renderer failure 规则继续生效。

## Schema 与兼容策略

Phase 2 不得声称 schema v1 不具备的前向兼容性。当前 reader 拒绝未知的内置 spec
和 change kind，因此即使源码变更是加法，增加 `AutoCompareSpec`、
`BinaryCompareSpec` 或 `binary_span` 也不能被旧 Phase 1 reader 读取。

实现前，维护者必须选择一个 ledger 选项：

1. 在第一次公开发布前扩展尚未发布的 schema v1；行为未变化时，保持每个 Phase 1
   payload 逐字节不变，并说明预发布 reader 没有前向兼容保证；或
2. 引入 schema v2，并明确 v1/v2 producer 与 reader 行为。

建议 option 1，因为版本仍为 `0.1.0.dev0` 且未发布；但这是 release policy 决策，
不是实现假设。第一次公开发布后，新的 closed-union kind 需要 schema successor。

在选定 schema 内，变更必须为加法：现有 required field、enum 含义、outcome 语义、
problem mapping、exit code 和 Phase 1 golden JSON 保持不变。optional field 必须有
读取默认值。未知 extension change 继续可保留；未知的非命名空间内置 kind 继续拒绝。
本 RFC 提议的新 problem code 为：

| Code | Status | Outcome | Stage |
| --- | ---: | --- | --- |
| `detection_no_match` | 415 | unavailable | detecting |
| `detection_ambiguous` | 409 | unavailable | detecting |
| `source_type_unsupported` | 415 | failed | sourcing |
| `source_changed` | 409 | failed | sourcing |

`capability_unavailable` 与 `backend_unavailable` 保持 RFC 0001 mapping。每个新增 code、
kind、spec 和 public export 都要求 constructor、round-trip、invalid-state、golden JSON
和 CLI compatibility test，以及 migration note。顶层包只应导出已接受的新 spec、
其公共 enum/limits 和 `BinarySpan`；registry 与 request type 继续私有。

## 安全与平台要求

- 探测与比较必须本地、确定、有界且不使用网络；
- Phase 2 禁止解压、归档遍历、可执行探测和 subprocess；
- prefix buffer、change details、diagnostic details 与 renderer 均有界；
- 输入字节不得进入 diagnostic、log、filename、HTML 或 terminal output；
- path opening 与 descriptor validation 要在支持平台测试 symlink swap 和 special file；
- 某 OS 不可用的平台 metadata 必须省略或标为 unavailable，不能伪造；
- 即使 baseline CI 在平台矩阵接受前仍为 Linux/Python 3.12，也必须明确测试 Windows
  与 POSIX 路径行为；
- 恶意字节序列与 terminal control 不得改变 JSON 有效性或 terminal control flow。

## 接受矩阵

| 领域 | 进入 `Implemented` 前的必要证据 |
| --- | --- |
| Detection | empty、合法 UTF-8、非法 UTF-8、NUL/control-heavy、prefix boundary、tie、低于阈值、显式 override、多次运行确定性 |
| Resolution | 注册顺序无关、重复拒绝、每个 reject reason、selected/rejected attempt、backend 缺失、无 capability |
| Binary correctness | equal、different、empty、长度不同、chunk boundary mismatch、无需重建的 span invariant、hash 记录但不用于独立判等 |
| Resources | 精确 input boundary、detection prefix boundary、change-item/payload truncation、有界峰值内存、input/work 耗尽不产生 partial |
| Sources | bytes、text encoding、regular path、missing/denied path、directory、可用平台的 FIFO/device/socket、symlink target、读取中 mutation |
| Contracts | Phase 1 golden payload、新 round trip、unknown field/kind、stable code、public export、schema 决策和 migration note |
| CLI | 旧路由不变、binary/auto 路由、全部 exit、stdout/stderr、flag 分离、label/path/control 转义、renderer failure |
| Provenance | detector/comparator/backend 版本、阈值、排序、attempt、transformation、hash、limits 和实际用量 |
| Packaging | 零新增 runtime dependency、Ruff、strict mypy、完整 pytest、build、wheel/sdist 检查、默认分支 CI 绿色 |

## 提议的实现 commit 与门禁

在 RFC 接受前，实现工作不指派。未来代码会话应按顺序使用以下聚焦 commit：

1. `refactor(core): add bounded replayable source snapshots`
   - 门禁：Phase 1 行为和 golden JSON 不变；regular-file 与 mutation 测试证明单一
     descriptor/snapshot 生命周期。
2. `feat(core): add detection and capability request contracts`
   - 门禁：schema 决策已记录；在没有 binary comparator 时，candidate ranking、
     ambiguity、request normalization 和 registry-order 测试通过。
3. `feat(binary): add exact streaming comparison`
   - 门禁：实际字节判等、span、metric、hash、truncation、资源边界、mutation 和
     代表性 memory 测试通过。
4. `feat(core): integrate automatic detection and resolution`
   - 门禁：execution stage、outcome、attempt、rejection reason、provenance、显式 bypass
     和端到端确定性通过。
5. `feat(cli): add binary and automatic comparison routes`
   - 门禁：已接受的 auto-entry 决策完成；现有 CLI snapshot 与 exit 保持兼容；新路由
     覆盖安全输出和全部 failure。
6. `docs: document automatic and binary comparison`
   - 门禁：中英文行为文档、migration note、example、limit、algorithm provenance 和
     planned 标签与已验证代码一致。

只有独立 contract review 把每个已接受 RFC 条款映射到 code/test、全部要求命令通过、
CI 绿色、dependency/license 影响已记录，且 PR 不包含 Phase 3 plugin API 或 UI 工作
时，实现 PR 才可合并。

## 决策账本

以下决策需要人类明确接受；下列默认只是建议，不是授权：

| ID | 决策 | 建议 | 阻断项 |
| --- | --- | --- | --- |
| D1 | Auto CLI 入口 | Phase 2 要求 `--type auto`；省略 `--type` 继续为 exit-2 用法错误 | CLI 契约 |
| D2 | Confidence policy | 整数 0..1000，最低 800，ambiguity margin 100；接受前用 fixture 校准 | Detector 常量与 snapshot |
| D3 | Schema 演进 | 首次发布前扩展一次未发布 schema v1；发布时冻结 closed union | 公共 model 与 serialization |
| D4 | Binary input 默认值 | Phase 2 保持现有每输入 16 MiB；只有证据和显式 limit 才提高 | limits 与大文件声明 |
| D5 | Auto text 语义 | auto 选中 text 后使用 strict UTF-8、保留 newline，不做其他 normalization | Auto spec normalization |
| D6 | 平台门禁 | 声明跨平台 Phase 2 支持前加入 Windows CI；Linux 仍是最低 merge gate | 支持声明 |

任何已接受答案都必须写回 normative section，并在本 RFC 转为 `Accepted` 前从未决
账本移除。

## 后果

本提议使自动行为可审计且保守：歧义可见、显式意图优先、精确二进制比较从不只
依赖 digest，并让插件发布等待两个内置能力的证据。它也暴露了真实的预发布 schema
决策，要求在代码开始前处理，而不是把它隐藏在实现细节中。
