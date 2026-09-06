# RFC 0002：开发阶段与首个文本切片

[English documentation](0002-development-phases-and-text-slice.md)

- 状态：Accepted
- 日期：2026-09-06
- 负责人：Platydiff 维护者

## 摘要

本 RFC 定义 Platydiff 首个可执行纵向切片的交付顺序、commit 边界、公共 API 门禁、文件布局、CLI 行为、文本语义、资源限制和验证要求。该切片是 Python 3.12+ 库和 CLI，用于比较显式指定的文本输入，并返回 [RFC 0001](0001-comparison-outcome-and-diff-result_zh.md) 定义的契约。

本文定义的实现契约正由 `feat/python-text-diff` 分支上的 Phase 1 候选 PR #3 验证；在合并并发布前，该候选尚未交付。

自动格式探测、二进制比较、第三方插件发现和其他模态属于后续阶段。它们出现在路线图中并不表示已授权实现。每个阶段开始开发前都必须回到本 RFC 的契约门禁。

## 目标与非目标

Phase 1 必须交付一条贯穿验证、来源读取、能力解析、解码、规范化、对齐、比较、聚合和渲染的完整路径。它必须建立公共结果契约，但不能提前发布插件 API。

Phase 1 的目标是：

- 带显式文本意图的类型化 Python API；
- 路径、字节和内存文本来源；
- 确定性的逐行文本比较；
- terminal 和 JSON outcome 渲染；
- 稳定的 CLI 退出行为；
- 零第三方运行时依赖；
- 兼容性、正确性、确定性和资源边界测试。

Phase 1 不包含：

- 自动模态或编码探测；
- stdin、目录或递归比较；
- 配置文件或基于环境的配置；
- 二进制、结构化数据、表格、数组、图片、源代码、PDF、音频或视频比较器；
- 公共插件发现、entry point 或插件 SDK；
- 彩色输出、HTML、JUnit 或 patch artifact；
- 基于墙钟时间的算法 fallback。

## Phase 1 交付与 commit 门禁

实现 PR 按顺序使用以下 commit。当前 commit 满足门禁后才能开始下一个 commit。

| Commit | 范围 | 门禁 |
| --- | --- | --- |
| `build: bootstrap Python package and quality tooling` | 平铺包、构建元数据、开发 extras、CI、空模块边界 | 包可构建；两个 CLI help 入口可加载；Ruff、strict mypy、pytest、build 已配置；不声称已有比较行为 |
| `feat(core): add comparison contracts and serialization` | Source、spec、outcome、result、problem、provenance、JSON 编码和验证 | RFC 0001 不变量具有类型化构造器、往返测试、非法状态测试和稳定快照 |
| `feat(text): implement linear-space Myers edit scripts` | 内部文本 IR 与确定性的最短编辑脚本引擎 | Oracle、重建、差分、tie-break、预算、确定性和代表性内存测试通过 |
| `feat(text): add the text comparison pipeline` | 显式文本解析、解码、换行规范化、hunk 构建和策略聚合 | 库 API 覆盖相等、不同、解码失败、来源失败、限制、完整输出和明细截断 |
| `feat(cli): add text commands and outcome renderers` | 两条 CLI 路由、terminal 与 JSON renderer、退出码映射 | 两条路由使用同一流水线；输出、错误安全和退出码具有集成测试 |
| `docs: document the first executable vertical slice` | README、API/CLI 示例、限制和计划能力标签 | 示例在测试中运行；文档明确区分已实现行为与路线图 |

脚手架 commit 可以定义建立依赖方向所需的可导入占位模块，但不得发布推测性的字段或插件协议。契约 commit 必须在 comparator 或 CLI 依赖它们之前冻结 schema v1 名称。

## 计划文件布局

Phase 1 使用平铺包布局：

```text
pyproject.toml
platydiff/
├── __init__.py                 # 仅精选公共导出
├── __main__.py                 # python -m platydiff
├── core/
│   ├── models.py               # Source、CompareSpec、outcome、DiffResult
│   ├── problems.py             # 项目定义的领域失败
│   ├── serialization.py        # schema v1 JSON 转换与验证
│   ├── pipeline.py             # 编排和边界转换
│   └── _registry.py            # 内部能力注册
├── comparators/
│   └── text/
│       ├── models.py           # TextLine、编辑操作、TextHunk
│       ├── myers.py            # 线性空间最短编辑脚本
│       └── comparator.py       # 文本结果构造
├── renderers/
│   ├── terminal.py
│   └── json.py
└── cli/
    ├── parser.py
    └── main.py
tests/
├── unit/
└── integration/
```

依赖方向保持为：

```text
CLI / renderers / comparators
              ↓
             core
```

`core` 不得导入具体 comparator 或 renderer。`_registry.py` 在 Phase 1 中只是内部组装机制，不得重新导出。

## Python 打包基线

脚手架固定选项如下：

- Python 3.12 或更高版本；
- 平铺 `platydiff/` 包；
- Hatchling 构建后端；
- 初始版本 `0.1.0.dev0`；
- Apache-2.0 项目许可证；
- CLI 使用 `argparse`；
- 零第三方运行时依赖；
- 开发工具使用 Ruff、strict mypy、pytest 和 build；
- Linux/Python 3.12 基础 CI job。

包必须为后续测试套件注册 `media` 和 `external` pytest marker。Phase 1 没有需要这些能力的测试；未来测试在可选后端缺失时必须报告明确的 skip 原因。

## 公共 Python API

唯一的比较入口是：

```python
def compare(
    before: Source,
    after: Source,
    spec: CompareSpec,
) -> CompareOutcome: ...
```

公共来源联合是：

```python
Source = PathSource | BytesSource | TextSource
```

`PathSource` 指向一个文件系统文件；`BytesSource` 持有不可变字节和可选的安全显示标签；`TextSource` 持有已解码 Python 字符串和可选的安全显示标签。Source provenance 记录角色和摘要，但不序列化绝对路径或输入内容。

`CompareSpec` 是带标签联合；其首个且唯一的 Phase 1 变体是 `TextCompareSpec`。`spec` 参数必填：API 不从文件名、内容或 Python 类型推断文本。规范化后的 spec 包括所有生效默认值，并记录在 comparison provenance 中。

包根目录精选导出 `compare`、source 类型、spec 类型、outcome 类型、`DiffResult` 和核心公共枚举。它不重新导出 registry、pipeline stage、comparator 实现、renderer 内部结构或 Myers primitive。

序列化属于 schema v1 契约。领域模型构造时验证不变量；解码不可信 JSON 时先获得通用 JSON 值，验证 schema 和联合标签后再构造类型化模型。

## CLI 契约

Phase 1 提供等价路由：

```text
platydiff compare --type text BEFORE AFTER
platydiff text BEFORE AFTER
```

两条 parser 路由构造相同的 `TextCompareSpec`，并调用相同的比较与渲染路径；两者都不执行自动探测。

Phase 1 计划选项包括：

- `--format terminal|json`；
- `--encoding utf-8|utf-8-sig`；
- `--newline preserve|normalize_lf`；
- `--context-lines`；
- 输入字节数、行数、编码后单行大小、Myers 工作量、change item 和 change payload 限制。

Terminal 输出供人类阅读；JSON 输出是精确的 schema v1 `CompareOutcome` 信封。Renderer 可以选择展示方式，但不得重新计算 relation、verdict、fidelity、completeness 或策略评价。

Shell 退出码是：

| 退出码 | 含义 |
| ---: | --- |
| `0` | Completed outcome，verdict 为 `pass` 或 `warn` |
| `1` | Completed outcome，verdict 为 `fail` |
| `2` | CLI 语法、选项或执行前使用错误，且不输出 comparison outcome |
| `3` | `unavailable` 或 `failed` outcome，包括安全映射的 `internal_error` |

机器消费者必须使用 RFC 0001 的稳定 problem 字符串和 HTTP 风格 status code，不得从 shell 退出码推断具体原因。

## 文本解码与规范化

字节和路径输入默认按 strict UTF-8 解码。非法输入按具体情况产生 `failed/unsupported_encoding` 或 `failed/decode_error`，绝不静默替换。UTF-8 BOM 在 `utf-8` 下是数据，只有调用方显式选择 `utf-8-sig` 时才移除。

解码后的输入拆分为不可变 `TextLine`：

```python
class TextLine:
    content: str
    terminator: Literal["", "\n", "\r\n", "\r"]
```

默认 `preserve` 策略同时比较内容和 terminator，因此保留 LF、CRLF、CR 和末尾换行缺失。`normalize_lf` 显式把每个已存在的 terminator 映射为 LF，同时保留空 terminator。不隐式执行 Unicode 规范化、大小写折叠、空白裁剪、tab 展开或 locale 转换。

输入 SHA-256 覆盖原始字节。对于 `TextSource`，摘要覆盖其 strict UTF-8 编码。Provenance 另行记录显式解码与换行转换。

## Edit 与 hunk 语义

内部编辑脚本包含 `equal`、`delete` 和 `insert`。Replace 被规范化为先删除后插入；该顺序也控制 hunk 序列化和 terminal 渲染。

`TextHunk` 是 Phase 1 的内置 change，`kind="text_hunk"`。位置使用一基行号和以 `start_line + line_count` 表示的半开区间。零长度 insert/delete 锚点可以指向最后一行之后的位置。Hunk context 只是在完整编辑脚本已知后选取的展示数据；改变 context 不会改变 relation、verdict、metric 或 change 总数。

默认严格策略在脚本没有 insert/delete 时产生 `equal/pass`，否则产生 `different/fail`。Phase 1 没有产生 `warn` 或 `degraded` fidelity 的策略，但会为了 schema v1 兼容性实现并序列化这些值。

## Myers 算法契约

算法 ID 是：

```text
text.myers.linear_space.v1
```

它使用 Myers middle-snake 分治算法，以最短 insert/delete 编辑脚本为目标，辅助空间为 `O(N + M)`。实现必须：

1. 在求解每个剩余区域前剥离公共前缀和后缀；
2. 使用显式任务栈，避免 Python 递归深度成为输入限制；
3. 在最短路径等价时使用固定的 deletion-first tie-break；
4. 按稳定的来源顺序输出操作；
5. 预算耗尽时不得 fallback 到 `difflib.SequenceMatcher` 或其他会改变语义的算法。

正常结果不依赖墙钟时间。工作量计数具有确定性：每推进一个 frontier state 计一个单位；前缀裁剪、后缀裁剪或 snake 扩展中每执行一次 `TextLine` 相等性检查也计一个单位。实现必须在计入下一个单位前检查上限。配置的上限与实际计数都记录在 comparison provenance 中。

工作预算耗尽返回 code 为 `compare_resource_limit` 的 `FailedOutcome`；它绝不返回 `partial`，也不替换成非最短算法。只有比较完成后裁剪完整的 change 明细，才可以产生 `changes.completeness="truncated"`。

## 固定资源默认值

Phase 1 的默认值是：

| 资源 | 默认值 |
| --- | ---: |
| 每个输入的字节数 | 16 MiB |
| 每个输入的行数 | 200,000 |
| 每个规范化行的 strict UTF-8 字节数 | 1 MiB |
| Myers 确定性工作单元 | 5,000,000 |
| 返回的 change item | 10,000 |
| 序列化 change payload | 4 MiB |
| Hunk context | 3 行 |

读取时检查输入限制，确保 path input 不会无界加载。拆分时检查行数限制。编码后单行限制按所选换行规范化完成后的 strict UTF-8 计算。Change item 和 payload 限制只在完整脚本和总数已知后应用；触及任何一个限制都按确定性来源顺序在完整 item 边界截断。Payload 用量是每个保留的完整 change 独立编码为 schema-v1 规范紧凑 JSON 后的字节数之和：`ensure_ascii=false`、`allow_nan=false`、对象键排序且使用紧凑分隔符。外围数组、outcome envelope 和 pretty-print 空白不计入。

## 验证契约

相应工具引入后，所有 Phase 1 commit 必须持续通过：

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy platydiff tests
python -m pytest
python -m build
```

文本算法测试必须包含：

- 小规模输入使用动态规划 LCS oracle 验证最短编辑距离；
- 每个编辑脚本都能精确重建目标；
- 与仅在测试内实现、保存完整 trace 的简易 Myers 参考实现进行差分；
- 相等、空输入、完全不同、单点变化、重复行、顺序变化和缺失末尾换行；
- 固定 deletion-first tie-break 快照和跨运行确定性；
- 精确工作预算边界测试；
- 完全不同输入、重复行和大编辑距离的代表性峰值内存检查。

契约测试必须覆盖所有 outcome 变体、序列化往返、拒绝未知 schema/kind、带标签的非有限 metric、change 完整度不变量、安全 artifact URI 和稳定排序。CLI 集成测试必须覆盖两条路由、两种 renderer、全部退出码、非法选项、来源/解码失败、输出截断和 traceback 抑制。

## 后续阶段与回调门禁

后续阶段构成已接受的路线图，不自动授权实施：

1. **Phase 2：** 自动探测、capability resolution 和 binary comparator。
2. **Phase 3：** 第三方 entry-point discovery、插件 SDK 和兼容性套件。
3. **Phase 4：** JSON/YAML 和 table/array 比较。
4. **Phase 5：** image 比较。
5. **Phase 6：** source code 和 PDF 比较。
6. **Phase 7：** audio 和 video 比较。

每个阶段开始前：

- 每个新模态必须定义自己的 `CompareSpec`、`Change`、metric、artifact、等价关系、默认策略和失败语义；
- Phase 2 必须确定探测歧义、候选排序、置信度报告和 capability request 模型；
- Phase 3 必须先吸收内部 text/binary registry 的经验，再发布 discovery 或插件契约；
- 可选后端必须定义可用性、降级、版本 provenance、许可证和确定性 fallback 行为；
- schema、枚举、默认算法或序列化字段变化需要兼容性测试和迁移说明；
- 当前阶段必须定义自己的 commit/API 门禁，并取得明确的实现授权。

## 影响

首个可执行版本有意保持狭窄，但会贯穿后续模态同样需要的 outcome、provenance、序列化、策略、渲染和资源控制边界。延后 detection 和公共 plugin 能让相关契约等待两个内部能力提供证据后再定稿。线性空间 Myers 与确定性预算让资源行为可观察，同时避免静默改变比较语义。
