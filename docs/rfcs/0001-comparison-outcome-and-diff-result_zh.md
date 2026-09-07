# RFC 0001：比较执行终态与差异结果契约

[English documentation](0001-comparison-outcome-and-diff-result.md)

- 状态：Implemented
- 日期：2026-09-06
- 负责人：Platydiff 维护者

## 摘要

Platydiff 将一次比较尝试的执行终态与已完成比较的语义结果分开。`CompareOutcome` 是带 schema 版本且可序列化的执行信封；只有其 `completed` 变体携带 `DiffResult`。因此，`DiffResult` 始终表示真实的比较事实，不替代能力不可用、流水线失败或未来的调度终态。

Schema v1 发布三种 outcome：`completed`、`unavailable` 和 `failed`。它还定义成功结果模型、两层 provenance、策略评价、模态专属 change、扩展 change、结果明细完整度、稳定 diagnostic 和结构化错误。

## 动机

检测、解码、规范化、对齐或能力解析可能在比较器产生任何差异事实前失败。把这些失败表示成 `DiffResult` 会削弱该类型的核心不变量，并让比较器与编排职责耦合。反过来，如果异常是唯一的失败协议，CLI、批量执行、插件、JSON 消费者和 renderer 将分别发明不兼容的结果信封。

因此，契约使用一个可序列化的外层联合，同时保持成功结果类型边界狭窄：

```python
CompareOutcome = CompletedOutcome | UnavailableOutcome | FailedOutcome
```

这种分层还允许执行记录和已完成的差异结果采用不同的缓存与保留策略。

## 执行生命周期

完整的计划生命周期是：

```text
created
  -> validating
  -> sourcing
  -> detecting?        # 显式指定模态时跳过
  -> resolving
  -> decoding
  -> normalizing
  -> aligning
  -> comparing
  -> aggregating
  -> completed
```

首个实现切片要求显式提供文本比较 spec，因此跳过 `detecting`。

终态转移约束如下：

| 来源 | 执行终态 | 含义 |
| --- | --- | --- |
| `detecting`、`resolving` | `unavailable` | 没有合适的模态、比较器、能力或必要后端能满足请求 |
| `validating`、`sourcing` 或任意执行阶段 | `failed` | 请求已匹配执行路径，但验证或执行无法完成 |
| `aggregating` | `completed` | 已产生 relation 和策略 verdict |

`cancelled` 和 `skipped` 是未来候选项，不是合法的 schema v1 outcome kind。添加它们必须进行兼容性评审，并修订本 RFC 或创建后继 RFC。

渲染发生在 `CompareOutcome` 已经存在之后。renderer 失败不得把已有的 completed outcome 改写为比较失败。如果 CLI 无法输出选定的展示形式，它仍可用失败状态退出；该失败单独写入 stderr，并且不得伪造替代 outcome。

## CompareOutcome

每个 schema v1 outcome 都包含以下公共字段：

```python
class OutcomeBase:
    schema_version: Literal[1]
    kind: str
    execution: ExecutionRecord
```

具体变体是：

```python
class CompletedOutcome(OutcomeBase):
    kind: Literal["completed"]
    result: DiffResult


class UnavailableOutcome(OutcomeBase):
    kind: Literal["unavailable"]
    problem: CapabilityProblem


class FailedOutcome(OutcomeBase):
    kind: Literal["failed"]
    problem: ExecutionProblem
```

Unavailable 或 failed outcome 不得包含空的、部分的或占位用的 `DiffResult`。

已知领域失败由流水线边界转换。库代码不得把 `KeyboardInterrupt`、`SystemExit`、`MemoryError` 或程序缺陷捕获并规范化成普通领域失败。CLI 可以在最外层捕获其他未处理异常，默认隐藏敏感堆栈信息，输出 `internal_error` 并以失败状态退出。

## ExecutionRecord

`ExecutionRecord` 描述一次比较尝试推进到了哪里。它包含：

- UTC `started_at`、`finished_at` 以及整数 `duration_ns`；
- 按顺序排列的阶段记录，包括开始、结束和最终处置；
- 能力与后端尝试，包括被拒绝的候选项和 fallback 决策；
- 稳定的 diagnostics；
- 最后完成的阶段。

运行时间字段不参与语义缓存键。测试注入固定时钟，确保时间戳和耗时序列化在测试中保持确定。

Diagnostic 包含稳定的小写 ASCII `code`、`info` 或 `warning` 严重度、可选流水线阶段、安全的人类消息和 JSON-safe details。Diagnostic warning 不意味着 `verdict=warn`。

## Problem 与结构化状态码

Problem 包含稳定字符串 code、HTTP 风格数字 `status_code`、阶段、安全消息、JSON-safe details，以及在有意义时提供的 `retryable`。数字状态码用于粗粒度分类，但它们不是 HTTP response，也不是进程退出码。

Schema v1 保留以下映射：

| Code | 状态码 | Outcome |
| --- | ---: | --- |
| `invalid_spec` | 400 | `failed` |
| `permission_denied` | 403 | `failed` |
| `source_not_found` | 404 | `failed` |
| `resource_limit_exceeded` | 413 | `failed` |
| `compare_resource_limit` | 413 | `failed` |
| `unsupported_encoding` | 415 | `failed` |
| `decode_error` | 422 | `failed` |
| `internal_error` | 500 | CLI 边界产生的 `failed` |
| `io_error` | 500 | `failed` |
| `capability_unavailable` | 501 | `unavailable` |
| `comparator_failure` | 502 | `failed` |
| `backend_unavailable` | 503 | `unavailable` |

字符串 code 是稳定的机器标识；多个字符串 code 可以共享同一数字状态码。

显式 Phase 1 文本切片可以产生 `invalid_spec`、来源与资源失败、`decode_error`，以及 CLI 边界的 `internal_error`。它的编码选择器是封闭的 CLI/API 枚举，因此非法字节产生 `decode_error`；`unsupported_encoding` 保留给未来动态解析编码的阶段。能力与后端 problem code 同样保留到自动探测和可选后端实现之后。

## 两层 provenance

执行 provenance 和比较 provenance 被有意分开。

`CompareOutcome.execution` 记录编排事实：

- 阶段进度和耗时；
- 能力与后端尝试；
- fallback 和 retry 决策；
- 运行 diagnostics。

`DiffResult.provenance` 记录语义比较事实：

- before/after 角色、来源种类、大小与 SHA-256；
- 规范化后的 `CompareSpec`；
- 显式规范化和对齐转换；
- 比较器、算法和实现版本；
- seed、配置的资源预算与实际确定性工作计数。

这种分层既让失败终态可审计，也使分离或缓存后的 `DiffResult` 保持自描述。默认排除原始输入内容、绝对路径、密钥和堆栈信息。

## DiffResult

`DiffResult` 只在比较与聚合均完成后存在：

```python
class DiffResult:
    relation: Literal["equal", "different"]
    verdict: Literal["pass", "warn", "fail"]
    fidelity: Literal["full", "degraded"]
    summary: DiffSummary
    changes: ChangeSet
    metrics: tuple[Metric, ...]
    evaluations: tuple[PolicyEvaluation, ...]
    artifacts: tuple[ArtifactRef, ...]
    provenance: ComparisonProvenance
```

不变量如下：

- `relation` 表示规范化 spec 下的等价关系；spec 说明其含义是严格、结构、感知还是统计等价。
- 默认严格相等策略把 `equal` 映射为 `pass`，把 `different` 映射为 `fail`。
- `warn` 只能由显式策略评价产生。
- `fidelity` 描述比较执行中的信息损失，例如被允许的低保真 fallback；它不描述结果明细截断。
- Metric 记录测量事实；PolicyEvaluation 解释事实与阈值如何得到 verdict。
- 结果 verdict 等于选定聚合策略下所有策略评价的最高严重度。
- Renderer 消费这些字段，不得重新计算比较或策略语义。

## Summary 与 change 完整度

```python
class DiffSummary:
    change_count: int | None
    counts: tuple[SummaryCount, ...]


class ChangeSet:
    completeness: Literal["complete", "truncated", "partial"]
    items: tuple[Change, ...]
    total_count: int | None
    returned_count: int
    omitted_count: int | None
    selection: Literal["all", "source_order_prefix", "algorithm_partial"]
    limit: int | None
    limit_reason: Literal["change_items", "change_payload_bytes"] | None
```

Summary count 的名称和单位是稳定的小写 ASCII 标识符。名称在单个结果中唯一，并按名称稳定排序后序列化。

各完整度状态具有精确定义：

| 完整度 | 必须满足的不变量 |
| --- | --- |
| `complete` | `total_count == returned_count`、`omitted_count == 0`、`selection == "all"` |
| `truncated` | 比较与总量统计已完成；总数与省略数已知；只按来源顺序保留完整 change |
| `partial` | 算法未形成完整 change 集合；总数、省略数和 `summary.change_count` 为 null；返回项仅是已确认事实 |

当两者均非 null 时，`summary.change_count` 必须等于 `changes.total_count`。

Schema v1 声明 `partial`，以防止它与输出截断混淆。首个实现切片不得产生 partial：Myers 工作预算耗尽时返回 failed outcome。未来 spec 必须显式允许部分结果，比较器才能产生 partial；partial 结果可以证明 `different`，但绝不能声称 `equal`。

截断只能发生在完整 change 边界上。新的 schema-v1 producer 会设置 `limit_reason`，使 `limit` 的单位无歧义；reader 为兼容早期 schema-v1 候选 payload，仍接受缺失或 null 的 reason。截断产生 `change_details_truncated` diagnostic，但不改变 relation、verdict 或 fidelity。

## Change 变体与扩展

内置 change 使用稳定、模态专属的标签变体，例如 `text_hunk`。拒绝使用带可选 location 字段的单一通用对象，因为行区间、表格键、图片坐标和时间区间具有不兼容的不变量。

第三方 change 使用 `ExtensionChange`：

```python
class ExtensionChange:
    kind: str                 # 反向域名标识符
    plugin_id: str
    schema_version: int
    payload: JsonObject
```

规则如下：

- 内置 kind 使用不带域名前缀的稳定小写 ASCII 标识符；
- 扩展 kind 使用反向域名，例如 `org.example.spectrogram_region`；
- 扩展 payload 只包含 JSON-safe 值；
- 未知的命名空间 kind 可以保留为 ExtensionChange；
- 未知且没有命名空间的内置 kind 必须拒绝，不得猜测；
- 通用 renderer 可以显示扩展身份和安全摘要，但不得推断其语义；
- 未来插件协议可以注册插件专属 renderer，但不得引入 core 到 plugin 的依赖。

## Metric、evaluation 与 artifact

数字指标值使用带标签且 JSON-safe 的联合：

```json
{"kind": "finite", "value": 1.25}
{"kind": "nan"}
{"kind": "positive_infinity"}
{"kind": "negative_infinity"}
```

JSON 序列化绝不能输出非标准的裸 `NaN` 或 `Infinity` token。

Metric 记录稳定名称、数值、单位、方向和可选的聚合方法。PolicyEvaluation 记录规则 ID、verdict，以及在适用时记录规则使用的指标、操作符、阈值和观察值。阈值不放在 Metric 内，因为同一观察值可能参与多项策略。

`ArtifactRef` 包含 artifact ID、稳定 kind、媒体类型、相对 URI、SHA-256 和字节大小。URI 必须相对于显式 artifact root，并使用可移植的正斜杠。验证前，每个字面路径段恰好执行一次 percent decode，并按 strict UTF-8 解码。空段、`.` 与 `..` 段、解码后的正斜杠、反斜杠、NUL、C0/C1 控制字符、URI 分隔符、scheme 别名与嵌套 percent-escape 别名均被拒绝；非法转义以及任何 scheme、authority、query 或 fragment 也被拒绝。保存的 URI 保持调用方提供的编码形式。默认不在结果中内嵌 artifact。

## JSON 兼容性

- Schema v1 使用 UTF-8 JSON 和稳定的小写 ASCII 字段及枚举标识符。
- Serializer 拒绝非 JSON-safe 的扩展详情和裸非有限数值。
- 消费者应忽略未知的可选对象字段，但必须拒绝未知 schema version 或未知且非扩展的联合 kind。
- 新增必填字段、改变字段含义、改变既有枚举含义或删除变体，必须发布新 schema version 和迁移说明。
- 即使 schema version 不变，新增 outcome 变体也必须进行兼容性评审。
- Summary count、metric、evaluation、diagnostic 和 artifact 必须稳定排序。

## 被拒绝的替代方案

### 让所有终态都成为 DiffResult

拒绝原因：检测或解码失败没有差异结果，这会削弱所有比较器和 renderer 的不变量。

### 只使用异常表达失败

拒绝原因：CLI、批量任务、插件和 JSON 消费者需要一个携带部分执行 provenance 的统一可序列化终态信封。

### 使用单一 status 枚举

拒绝原因：执行完成情况、relation、verdict、fidelity 和明细完整度是彼此独立的维度。

### 在核心结果中保存人类 summary 字符串

拒绝原因：本地化或修订后的文案会变成机器契约。Renderer 应从结构化 summary count 生成人类文本。

## 影响

结果模型比传统布尔 diff 结果更大，但其不变量明确且可测试。比较器实现可以专注于语义比较；流水线代码负责执行终态转换；renderer 消费同一个可序列化信封而不改变含义。未来 outcome kind 和模态 payload 必须经过明确的兼容性评审，不能静默扩张。
