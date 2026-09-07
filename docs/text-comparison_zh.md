# 文本比较

[English documentation](text-comparison.md)

默认分支上的 Phase 1 实现比较两个显式指定的文本来源。它支持文件、自持有字节和
已解码字符串，不进行自动格式或编码探测。本文描述的是已实现但尚未发布的行为。

## Python API

```python
from pathlib import Path

from platydiff import PathSource, TextCompareSpec, compare

outcome = compare(
    PathSource(Path("before.txt")),
    PathSource(Path("after.txt")),
    TextCompareSpec(),
)
```

`compare(before, after, spec)` 始终要求 `TextCompareSpec`。outcome 是
`CompletedOutcome`、`UnavailableOutcome` 或 `FailedOutcome`；只有 completed
outcome 包含 `DiffResult`。使用 `platydiff.core.dumps_outcome(outcome)` 和
`platydiff.core.loads_outcome(payload)` 完成 strict schema-v1 JSON 往返。

`DiffResult.relation`、`verdict`、`fidelity` 和 change completeness 相互独立。
Phase 1 strict 策略产生 `equal/pass` 或 `different/fail`。renderer 只展示这些
字段，不重新计算它们。

## CLI

```text
platydiff compare --type text [OPTIONS] BEFORE AFTER
platydiff text [OPTIONS] BEFORE AFTER
```

两个入口构造相同 specification，并使用同一比较和渲染路径。选项如下：

| 选项 | 取值或含义 | 默认值 |
| --- | --- | ---: |
| `--format` | `terminal` 或 `json` | `terminal` |
| `--encoding` | `utf-8` 或 `utf-8-sig` | `utf-8` |
| `--newline` | `preserve` 或 `normalize_lf` | `preserve` |
| `--context-lines` | 非负 hunk 上下文行数 | `3` |
| `--max-input-bytes` | 每个输入的字节数 | `16777216` |
| `--max-input-lines` | 每个输入的行数 | `200000` |
| `--max-encoded-line-bytes` | 每个规范化行的 strict UTF-8 字节数 | `1048576` |
| `--max-myers-work` | 确定性 work unit | `5000000` |
| `--max-change-items` | 返回的完整 hunk 数 | `10000` |
| `--max-change-payload-bytes` | 返回 hunk 的 schema-v1 规范 JSON 字节数 | `4194304` |

所有限制都接受零。非法值属于用法错误，退出码为 `2`，且不输出 outcome。

## 文本语义

字节和路径输入使用 strict 解码。`utf-8` 将 BOM 保留为内容；`utf-8-sig`
显式移除它。非法字节返回 `failed/decode_error`。流水线识别 LF、CRLF 与 CR，
并分别表示行内容和终止符；末尾缺少终止符仍可观察。

`preserve` 精确比较终止符。`normalize_lf` 把每个已有终止符改为 LF，但不会
补充缺失的终止符。不会隐式执行 Unicode 规范化、大小写折叠、空白裁剪、tab
展开或依赖 locale 的转换。

算法 `text.myers.linear_space.v1` 产生最短 insert/delete 编辑脚本，并在平局时
优先 deletion。replacement 始终表示为 deletion 后接 insertion：流水线会把每一段
变更行连续区重排为先删除后插入，这既不改变脚本长度，也不改变重建结果。实现使用线性
辅助空间、显式任务栈和确定性工作预算，不使用墙钟超时或语义 fallback。

hunk 使用一基行号和 `start_line + line_count` span。context 只属于明细：改变
它不会改变 relation、verdict、metric 或 hunk 总数。相邻 hunk 会确定性地分配共享
context 且不重复行；共享间隔为奇数时，较早的 hunk 多获得一行。item 与 payload 限制只在
完整编辑脚本和总数已知后应用。截断仅按来源顺序保留完整 hunk，添加
`change_details_truncated`，且不改变结果的 relation、verdict 或 fidelity。
`changes.limit_reason` 指明其 `limit` 的单位是 `change_items` 还是
`change_payload_bytes`。

Payload 限制是每个保留的完整 change 独立编码为 schema-v1 规范紧凑 JSON 后的
UTF-8 字节数之和：直接输出 Unicode、拒绝非有限数、对象键排序，且分隔符不含
空白。外围 changes 数组、outcome envelope 和 renderer 专用空白均不计入。

## 失败与 provenance

预期的来源、解码与资源失败返回 schema-v1 `FailedOutcome`，不携带占位或部分
`DiffResult`。Myers 预算耗尽使用 `compare_resource_limit`，绝不 fallback 到
`SequenceMatcher`，也不产生 partial result。CLI 将其他未处理异常安全映射为不含
路径的 `internal_error`，并默认隐藏 traceback；`KeyboardInterrupt`、`SystemExit`
和 `MemoryError` 仍作为中断处理，而不是领域 outcome。

Phase 1 的编码选择是封闭的，因此非法字节产生 `decode_error`；
`unsupported_encoding` 以及 capability/backend 失败保留给后续动态解析阶段。
所有成功渲染的 outcome 都写入 stdout；parser 与 renderer 失败写入 stderr。
Renderer 失败以 `3` 退出，但不会替换此前已经产生的 outcome。

completed result provenance 包含输入角色、来源类型、字节大小、SHA-256、完整
规范化 specification、显式转换、算法与实现版本、配置限制和确定性工作计数。
绝对来源路径和输入内容不会被序列化。

## 延后能力

自动探测、二进制及其他模态比较器、公共插件发现、stdin 与目录输入、配置文件，
以及 color、HTML、JUnit 和 patch 输出仍在计划中。路线图条目不表示已经实现。
