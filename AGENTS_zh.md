# AGENTS.md

[English documentation](AGENTS.md)

## 适用范围与优先级

本文件适用于整个仓库。更深层目录中的 `AGENTS.md` 可补充本文件，`AGENTS.override.md` 可覆盖同一目录树中的规则。发生冲突时，以距离目标文件最近的规则为准。

## 项目概览

Platydiff 是面向科研数据、实验回归和竞赛工作流的可扩展多模态 Diff 引擎。它用统一的检测、解码、规范化、对齐、比较、聚合和渲染流水线处理二进制、文本、源代码、结构化配置、图片、音频、视频、PDF、表格与统计数据。

主要技术方向：

- Python 3.12+；首要交付物是 Python 库和 `platydiff` CLI。
- 标准库承担核心文件、哈希、文本、并发和子进程能力。
- NumPy、SciPy、pandas、xarray 用于可选的数组、统计和科研数据能力。
- Pillow、OpenCV、scikit-image、Tree-sitter、FFmpeg 和 PDF 后端均为可选插件或外部后端。
- 性能热点可在接口稳定后使用 Rust 扩展，但不得让核心 API 依赖具体 FFI。

仓库现已包含已实现的 Phase 1 显式文本、Phase 2 自动/二进制 Python 库和 CLI，以及
Phase 3 P3-A/P3-B/P3-C 公共插件 SDK、discovery、execution host、schema-v2
provenance、有界 renderer、显式 CLI selection 与 compatibility receipt；当前仍未发布。
Phase 4 门禁 P4-A1 另加入 schema-v3 contract 与显式内建 semantic JSON comparison。
YAML、table、array、其他新模态、配置文件、自动安装、任意 artifact、HTML 与 review UI
仍处于计划阶段；不得描述为已实现，且只报告实际运行过的验证命令。

## 仓库结构

当前已有：

- `README.md`：英文权威版，说明项目目标、覆盖范围和设计原则；`README_zh.md` 为中文翻译。
- `docs/architecture.md`：英文权威架构文档；`docs/architecture_zh.md` 为中文翻译。
- `pyproject.toml`：Python 打包元数据与标准开发工具配置。
- `platydiff/`：已实现的 Phase 1/2 库与 CLI、Phase 3 plugin boundary，以及 Phase 4 P4-A1 schema-v3/JSON 路径。
- `tests/`：单元、集成、契约、算法、CLI 与打包回归测试。

目标结构：

- `platydiff/core/`：公共模型、插件注册、流水线、策略和来源记录；保持轻量。
- `platydiff/comparators/`：各模态比较器；重量级依赖只能在需要时加载。
- `platydiff/renderers/`：终端、JSON、HTML、JUnit 等输出；只消费公共结果模型。
- `platydiff/cli/`：参数解析、配置加载、退出码和用户可见错误。
- `platydiff/plugins/`：内置扩展入口和第三方插件适配。
- `tests/unit/`：纯单元测试，不依赖外部程序或网络。
- `tests/integration/`：跨模块、CLI 和可选后端测试。
- `tests/corpus/`：许可明确、体积受控的合成测试数据。
- `docs/`：架构、公共行为、算法来源和合规说明。

核心依赖方向必须保持为：

```text
CLI / renderers / comparators / plugins
                 ↓
               core
```

`core` 不得反向导入具体比较器、渲染器或重量级可选依赖。

## 开发命令

### 仅文档修改

文档修改至少运行：

```bash
git diff --check
```

同时手动确认 Markdown 相对链接存在、命令与仓库当前状态一致。

### Python 基线

`pyproject.toml` 规定以下命令为仓库的标准开发接口；不要另造功能重叠的脚本：

安装开发环境：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

运行 CLI：

```bash
python -m platydiff --help
platydiff --help
```

格式与 lint：

```bash
python -m ruff format --check .
python -m ruff check .
```

类型检查：

```bash
python -m mypy platydiff tests
```

测试：

```bash
python -m pytest
python -m pytest -m "not media and not external"
python -m pytest -m media
python -m pytest -m external
```

构建：

```bash
python -m build
```

`media` 用于需要大型媒体 fixture 的测试，`external` 用于需要 FFmpeg、PDF 渲染器等系统程序的测试。脚手架必须在 `pyproject.toml` 中注册这些 marker，并让缺失可选后端时的跳过原因清晰可见。

## 编码约定

- 模块、函数和变量使用 `snake_case`；类型使用 `PascalCase`；常量使用 `UPPER_SNAKE_CASE`。
- 插件 ID、能力名、指标名和序列化字段使用稳定的小写 ASCII 标识符；公开后不得仅为美观改名。
- 新代码必须有完整类型标注。避免 `Any`；解析不可信数据时先得到 `object`，经验证后再收窄类型。
- 公共模型优先使用标准、可序列化的数据结构。不要让 `DiffResult` 携带无法稳定序列化的第三方对象。
- `CompareSpec` 描述用户意图；算法和后端选择由能力注册表解析。不要把具体后端参数泄漏到无关模态。
- 规范化与对齐必须是可见、可关闭、可记录的阶段。禁止在指标实现中偷偷 resize、裁剪、重采样、排序或丢弃数据。
- 结果必须明确指标名称、数值、单位、方向、阈值和聚合方法。不要混淆严格相等、结构相等、感知相似与统计等价。
- 确定性优先：排序稳定，随机过程显式接收 seed，浮点和时间相关行为有测试。
- 核心代码不直接 `print` 或退出进程。抛出项目定义的异常或返回结构化错误，由 CLI 映射消息和退出码。
- 不捕获裸 `Exception` 后静默继续。降级必须产生可见 warning，并记录所选后端和损失的信息。
- 子进程使用参数数组和 `shell=False`；设置超时，验证退出码，限制临时文件范围，不把不可信输入拼入命令字符串。
- 配置不得使用 `eval`、`exec` 或可执行模板。自定义规则使用受限 DSL 或显式 Python 插件。
- 优先使用标准库和已有依赖。新增依赖前说明用途、可选性、许可证、体积、平台支持和替代方案。
- 重量级或强 Copyleft 依赖不得进入默认核心依赖；通过 extras、插件或外部程序边界接入并记录合规条件。
- 不为顺手清理而扩大修改范围，不覆盖与当前任务无关的本地改动。

## 公共契约

以下内容一旦在首个公开版本中发布，即视为公共 API：

- `CompareSpec` 和 `DiffResult` 的字段及序列化形式。
- 插件协议、能力名称、插件发现入口和错误类型。
- CLI 命令、选项、退出码和 JSON 输出。
- 指标名称、单位、方向和默认聚合规则。
- 配置文件键名及其默认行为。

修改公共契约必须同步更新文档、迁移说明和兼容性测试。除非任务明确要求，不删除字段、改变含义、复用退出码或静默改变默认比较策略。

## 安全与修改边界

可以修改：

- 与当前任务直接相关的源码、测试、文档和配置。
- 为新行为增加的合成 fixture、schema 与兼容性测试。

不要随意修改：

- `tests/corpus/` 中已有 fixture 的字节内容、许可证或期望结果；需要变化时新增版本并说明原因。
- 已发布的公共 API、配置 schema、插件 ID、指标语义和 CLI 退出码。
- 锁文件中与任务无关的依赖；新增或升级依赖必须是有意变更。
- 第三方许可证、NOTICE、SBOM 和算法来源记录。
- 数据迁移或兼容层；不得删除旧迁移或用重写历史代替新迁移。

以下内容属于生成物，不手工编辑、不提交，除非发布流程明确要求：

- `dist/`、`build/`、`*.egg-info/`
- `.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`
- `.coverage`、`htmlcov/`
- 本地解码缓存、临时帧、波形、热图和报告预览

永远不要提交密钥、令牌、`.env`、未公开科研数据、竞赛受限数据、个人信息或许可证不允许再分发的媒体。

## 测试与验证

验证范围与修改风险匹配：

| 修改类型 | 最低要求 |
| --- | --- |
| 仅文档 | `git diff --check`；检查链接、路径和命令真实性 |
| Python 源码 | Ruff format、Ruff lint、mypy、完整 pytest |
| 单个比较器 | 全部 Python 检查；正常、边界、损坏输入、阈值和确定性测试 |
| CLI 或配置 | 全部检查；CLI 集成测试、退出码、错误文本和向后兼容测试 |
| 公共模型/插件协议 | 全部检查；序列化快照、兼容性测试、文档与变更日志 |
| 音视频/PDF 后端 | 全部检查；相应 marker 测试；记录外部程序版本和缺失后端行为 |
| 打包或依赖 | 全部检查；`python -m build`；检查 wheel/sdist 内容和许可证清单 |
| 性能或大文件路径 | 正确性检查；有代表性的基准；确认不会无界加载到内存 |

修复 bug 时先添加能复现问题的测试。比较算法测试至少覆盖：完全相同、完全不同、空输入、单点变化、重复元素、顺序变化、损坏输入和超限输入。数值测试同时覆盖 NaN、Inf、dtype、单位、`atol`/`rtol` 与边界值。

如果环境缺少可选依赖，可以报告针对性测试被跳过，但不得把“未运行”写成“通过”。提交结果时列出实际执行的命令和结果。

## 文档

- 英文是人类和 Agent 默认阅读的权威文档语言。
- 英文文档保留默认路径；中文翻译与英文版放在同一目录并使用 `_zh.md` 后缀，例如 `README.md` 与 `README_zh.md`。
- 行为或规则变化时同步维护翻译，并在中英文版本之间添加互链。
- 行为、配置、CLI、公共 API、默认值或支持格式变化时，同步更新 `README_zh.md` 和 `docs/`。
- 新算法记录论文或规范来源、适用范围、已知失败模式和许可证/专利注意事项。
- 示例必须可执行并使用合成或许可明确的数据。
- 文档中的计划能力要标为计划，不能写成已经支持。

## Git 与评审流程

- 从 `main` 创建短生命周期分支；Agent 创建分支时默认使用 `codex/<short-description>`。
- 使用小而聚焦的提交，推荐 Conventional Commits：`feat:`、`fix:`、`docs:`、`test:`、`refactor:`、`build:`、`chore:`。
- 不改写共享历史，不使用 force-push；不要把无关格式化、依赖升级和功能变更混入同一提交。
- PR 描述必须包含动机、行为变化、比较语义、实际运行的验证命令、可选依赖变化和数据/许可证影响。
- 公共行为变化必须提供变更日志；破坏性变化还需要迁移说明。
- 提交前检查 `git diff` 和 `git status`，确保没有生成物、秘密、受限数据或无关文件。

## 代码评审规则

评审时优先检查以下项目特有风险：

1. **语义**：代码比较的是字节、结构、感知还是统计等价，名称和文档是否一致。
2. **对齐**：行、键、坐标、页面、样本和时间轴如何对应；对齐失败是否被误当成内容差异。
3. **隐藏转换**：颜色空间、方向、Alpha、采样率、帧率、单位、dtype、时区、键排序和 NaN 是否被静默改变。
4. **可复现性**：输入哈希、配置、插件、后端版本、seed 和聚合方法是否进入 provenance。
5. **数值正确性**：容差公式、溢出、精度、归一化、单位和指标方向是否正确；p-value 是否同时报告效应量和样本量。
6. **资源边界**：大文件是否流式处理；压缩炸弹、损坏媒体、无限流、超长行和恶意 PDF 是否有上限。
7. **可选依赖**：未安装媒体、PDF 或 AST 后端时，核心导入和基础 CLI 是否仍可用。
8. **错误行为**：不支持、失败、跳过和降级是否可区分；是否错误地返回成功状态。
9. **结果契约**：JSON 是否稳定、可序列化；渲染器是否只解释结果而不重新计算或修改语义。
10. **合规**：新增代码、模型、fixture、编解码器和外部二进制是否有明确来源、许可证与分发权限。

## 子目录专用规则

当根规则不足时再添加子目录规则，避免复制整份文件：

- `platydiff/comparators/AGENTS.md`：各模态 IR、数值约束和 fixture 规范。
- `platydiff/core/AGENTS.override.md`：公共契约、依赖方向和兼容性要求的更严格规则。
- `tests/corpus/AGENTS.override.md`：数据来源、许可证、大小、脱敏和确定性要求。
- `docs/AGENTS.md`：引用格式、算法来源与文档验证规则。

子目录文件只写差异，并明确它覆盖或补充根规则的哪些部分。

## AgentGit 工作流

本项目强制使用 AgentGit 保存和同步所有 Codex/开发 Agent 对话。项目代码仍由当前 Git 仓库管理；AgentGit 只管理会话上下文、VIEW、事件、共享 memory 和 skills。固定 Agent repo 为公开仓库 `chenapr/platydiff`。

- 每次会话开始先运行 `agit status`。如果当前会话尚未托管，运行 `agit status --check-missing`，并将当前运行中的对话导入 `chenapr/platydiff` 的唯一会话分支；不得仅凭目录名选择其他 Agent repo。
- 已经运行中的 Codex 对话用 `agit import @ --repo chenapr/platydiff -b <unique-session-branch>` 接管；不要用 `agit new` 代替导入当前对话。
- 新会话分支使用简短且唯一的任务名称，不得使用 `main` 或以 `agit-` 开头。`main` 只用于 AgentGit 的共享文件线。
- 一个用户回合通常对应一个 AgentGit commit。阶段完成后运行 `agit commit --milestone "<summary>"`；需要同时提交项目代码并建立交叉链接时才添加 `--code`。
- `agit commit` 只写本地 Agent repo，不会自动上传。提交后显式运行 `agit push chenapr/platydiff -b <session-branch>`；共享文件线发生变化时另行运行 `agit push chenapr/platydiff -b main`。
- 第一次发布和仓库可见性必须为 public；不得把本项目的 Agent repo 改为 private。上传前检查会话中没有密钥、令牌、受限竞赛数据、个人信息或未公开科研数据。
- 结束任务前运行 `agit status`，报告未提交或未上传状态。注意当前仍在执行的回合只有在回合结束后才能被完整结算，因此必要时在下一回合再次 `agit commit` 和 `agit push`。
- 不要混淆项目 Git 与 AgentGit，不要在 `~/.agit/repos` 中手工执行历史改写；禁止对 AgentGit 使用 rebase、amend 或 force-push。

<!-- agit:begin -->
## 会话版本控制（agit）

本项目的 Agent 会话由 agit 管理。规则如下：

- 阶段完成时结算：`agit commit --milestone "<summary>"`（需要同时提交项目代码时添加 `--code`）。
- 会话开始时运行 `agit status`；如果作为合并 Agent 恢复，遵循 `AGIT_MERGE_TX` 协议（参见 agit skill）。
- 不得 rebase 或 force-push；使用 `agit revert @#n.k` 移除上下文。
<!-- agit:end -->
