# Platydiff

[English documentation](README.md)

`platydiff` 是一个面向科研数据、实验回归测试与竞赛工作流的可扩展多模态
Diff 引擎。Phase 1 与 Phase 2 已实现显式文本、精确二进制，以及需要显式启用的
文本/二进制自动探测。Phase 3 门禁 P3-B 还加入 immutable plugin host、显式选择的
文本/二进制 detector/comparator 执行与 schema-v2 provider provenance。既有 API 与
CLI 仍只使用内建能力并保持 schema-v1 contract。当前仍未发布。

## 开发环境安装

Platydiff 要求 Python 3.12 或更高版本，并且没有第三方运行时依赖。

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 从 CLI 比较文本

下面两个命令等价：

```bash
platydiff compare --type text before.txt after.txt
platydiff text before.txt after.txt
```

使用 `--format json` 选择精确的 schema-v1 JSON 输出：

```bash
platydiff text --format json before.txt after.txt
```

退出码 `0` 表示 completed 且 verdict 为 `pass` 或 `warn`，`1` 表示 completed
且 verdict 为 `fail`，`2` 表示没有产生 outcome 的命令行用法错误，`3` 表示
`unavailable`、`failed` outcome 或 renderer 失败。成功渲染的 outcome 写入 stdout；
parser 与 renderer 错误写入 stderr。结构化消费者应读取 outcome 和 problem code，
而不是从 shell 退出码猜测具体错误。

## 从 Python 比较文本

specification 是必填项；provenance 会记录全部生效默认值：

```python
from platydiff import TextCompareSpec, TextSource, compare

outcome = compare(
    TextSource("alpha\nbeta\n", label="before"),
    TextSource("alpha\ngamma\n", label="after"),
    TextCompareSpec(),
)

if outcome.kind == "completed":
    print(outcome.result.relation, outcome.result.verdict)
else:
    print(outcome.problem.code)
```

支持 `PathSource`、`BytesSource` 和 `TextSource`。字节和路径来源默认使用 strict
UTF-8；只有显式选择 `utf-8-sig` 才移除 BOM。除非显式选择 `normalize_lf`，
LF、CRLF、CR 和末尾缺少换行会保持不同。Unicode、空白、tab、大小写和 locale
不会被隐式规范化。

全部选项、资源限制、结果语义和失败行为见[文本比较指南](docs/text-comparison_zh.md)。
权威契约见 [RFC 0001](docs/rfcs/0001-comparison-outcome-and-diff-result_zh.md)
和 [RFC 0002](docs/rfcs/0002-development-phases-and-text-slice_zh.md)。

## 比较二进制或自动探测文本/二进制

```bash
platydiff binary before.bin after.bin
platydiff compare --type binary before.bin after.bin
platydiff compare --type auto before.dat after.dat
```

自动探测从不隐式启用；省略 `--type` 是用法错误。探测只读取有界前缀，二进制
比较以有界 chunk 流式读取并比较真实字节。详见[自动探测与二进制比较指南](docs/binary-comparison_zh.md)。

## 已实现与计划能力

Phase 1、Phase 2 与 P3-A/P3-B 插件门禁已实现：

- Python 3.12+ 库与 `platydiff` CLI；
- schema-v1 `CompareOutcome` 和 `DiffResult` JSON 序列化；
- strict 行级文本比较；
- 确定性、线性辅助空间的 Myers insert/delete 编辑脚本；
- 具有有界 change 明细的 terminal 与 JSON renderer；
- 有界、确定性的文本/二进制探测与内部 capability resolution；
- collision-safe 的精确二进制比较和不携带 payload 的 change span；
- immutable SDK-v1 manifest 与 capability/dependency/platform inventory；
- 不执行 capability 的显式 entry-point discovery、精确 allowlist、版本/feature 协商与
  确定性冲突隔离；
- 显式 pin 的 SDK-v1.1 detector/comparator handle、host 管理的有界 source access 与
  lifecycle stage；
- schema-v2 provider、attempt 与 plugin-host provenance，以及 typed v1-to-v2 upgrader；
  `PluginHost.compare()` 始终返回 schema v2。

计划中、尚未实现：

- CLI 插件参数、第三方 renderer invocation 与发布的 compatibility receipt（剩余契约仍由
  [RFC 0005](docs/rfcs/0005-third-party-plugin-discovery-sdk-and-compatibility_zh.md)
  门禁控制）；
- JSON/YAML、表格、数组、图片、源代码、PDF、音频和视频；
- stdin、目录、递归比较和配置文件；
- color、HTML、JUnit 和 patch artifact。

更广泛的设计方向见[架构文档](docs/architecture_zh.md)。
已实现的 P3-A/P3-B 边界见[插件 SDK 指南](docs/plugin-sdk_zh.md)。
算法来源与已知限制记录在[算法来源文档](docs/algorithm-references_zh.md)中。

## 许可证

Platydiff 使用 Apache License 2.0。参见 [LICENSE](LICENSE)。
