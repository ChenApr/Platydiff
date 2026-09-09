# Platydiff 设计架构

[English documentation](architecture.md)

## 1. 产品定位

`platydiff` 是一个面向科研可视化数据、实验回归和竞赛工作流的多模态差异分析框架。它不是单一算法的封装，也不把每种输入都退化为字节或文本，而是为不同模态提供共同的执行模型、配置协议和结果协议。

项目需要回答四类不同问题：

1. **严格相等**：两个对象的字节、样本或元素是否完全一致。
2. **可变换性**：如何用插入、删除、替换或复制操作从 A 构造 B。
3. **结构变化**：字段、语法节点、页面对象或镜头结构发生了什么变化。
4. **感知或统计差异**：变化是否能被人感知，或是否超过科研任务定义的实际容差。

项目主要交付形态为 Python 库和命令行工具，后续可增加 Notebook 组件、桌面/网页报告和 CI 集成。核心应保持轻量；高成本解析与多媒体处理通过可选插件或外部后端完成。

## 2. 总体流水线

```text
Input A / Input B
        │
        ▼
Format Detection
        │
        ▼
Decode → Typed Intermediate Representation
        │
        ▼
Normalize → Align → Compare → Aggregate
        │
        ▼
Common DiffResult
        │
        ├── Terminal
        ├── JSON
        ├── HTML
        ├── JUnit / CI
        ├── Patch
        └── Heatmap / Waveform / Frames
```

流水线各阶段的职责如下：

| 阶段 | 职责 | 示例 |
| --- | --- | --- |
| Detect | 识别格式与候选插件 | 扩展名、MIME、magic bytes、内容探测 |
| Decode | 转换为模态专用中间表示 | 文本行、AST、RGBA、PCM、视频帧、数据表 |
| Normalize | 消除任务不关心的变化 | 换行、键顺序、元数据、色彩空间、采样率 |
| Align | 建立可比较的对应关系 | 行、字段、主键、坐标、时间戳、帧、页面 |
| Compare | 产生局部差异和指标 | 编辑脚本、字段变化、误差矩阵、质量分数 |
| Aggregate | 汇总并执行规则 | 最大误差、分位数、失败阈值、告警 |
| Render | 表达人或机器需要的结果 | hunk、热图、HTML、JSON、JUnit |

不存在唯一的万能中间表示。框架应定义 `TextIR`、`TreeIR`、`ImageIR`、`AudioIR`、`VideoIR`、`DocumentIR` 和 `TableIR` 等带类型的数据结构，并让它们共享元数据、来源与生命周期约定。

## 3. 模块结构

```text
platydiff/
├── core/
│   ├── models.py          # CompareSpec、DiffResult 和通用类型
│   ├── registry.py        # 插件发现、能力声明和优先级
│   ├── pipeline.py        # 阶段调度、缓存、取消与错误边界
│   ├── policies.py        # 容差、忽略和通过/失败规则
│   └── provenance.py      # 输入哈希、参数、环境和版本记录
├── comparators/
│   ├── binary.py
│   ├── text.py
│   ├── source_code.py
│   ├── structured.py
│   ├── image.py
│   ├── audio.py
│   ├── video.py
│   ├── pdf.py
│   └── tabular.py
├── renderers/
│   ├── terminal.py
│   ├── json.py
│   ├── html.py
│   └── junit.py
├── plugins/               # 内置插件与第三方扩展入口
├── cli/                   # 命令解析、配置加载和退出码
└── tests/corpus/          # 自建和许可明确的测试样例
```

核心层不直接依赖重量级媒体或 PDF 引擎。比较器声明额外能力与依赖，缺少后端时返回结构化的 `capability_unavailable`，而不是静默降级或产生不可复现结果。

## 4. 抽象接口

下面的 Python 伪代码是早期模态流水线草图，不是公共插件协议，也不约束最终类层级：

```python
class DiffPlugin(Protocol):
    id: str
    version: str
    capabilities: set[str]

    def probe(self, source: Source) -> ProbeResult: ...
    def decode(self, source: Source, spec: CompareSpec) -> ArtifactIR: ...
    def normalize(self, artifact: ArtifactIR, spec: CompareSpec) -> ArtifactIR: ...
    def align(
        self, before: ArtifactIR, after: ArtifactIR, spec: CompareSpec
    ) -> Alignment: ...
    def compare(
        self,
        before: ArtifactIR,
        after: ArtifactIR,
        alignment: Alignment,
        spec: CompareSpec,
    ) -> DiffResult: ...
```

以现有实现证据为基础的 Phase 3 契约见
[RFC 0005](rfcs/0005-third-party-plugin-discovery-sdk-and-compatibility_zh.md)。它保持当前
registry 与 source snapshot 私有，要求显式 allowlist discovery，并让 host 拥有 stage、
resource、provenance 与 outcome construction。P3-A 已实现 immutable declaration 与
显式 discovery；P3-B 已实现显式 pin 的 detector/comparator 执行和 schema-v2 provider
provenance；P3-C 已实现有界 renderer invocation、显式 CLI 参数与 compatibility
receipt。新模态与 RFC 0004 review UI 仍在已实现的 Phase 3 边界之外。

### 4.1 CompareSpec

`CompareSpec` 描述需求，而不是绑定某个算法实现：

```yaml
type: table
mode: statistical

align:
  keys: [case_id, timestep]

ignore:
  columns: [generated_at, run_id]

numeric:
  atol: 1.0e-8
  rtol: 1.0e-5
  nan_equal: true

statistics:
  tests: [ks, wasserstein]
  report_effect_size: true

fail_when:
  max_changed_rows: 0
  max_rmse: 1.0e-4

output:
  formats: [terminal, json, html]
```

配置表达式必须使用受限规则语言，不得通过 `eval` 或模板注入执行任意 Python 代码。

### 4.2 DiffResult

执行终态与已完成结果的权威契约见 [RFC 0001](rfcs/0001-comparison-outcome-and-diff-result_zh.md)。下方结构是早期架构草图；如与 RFC 不一致，实现必须以 RFC 为准。

```text
DiffResult
├── equal               # 在当前规则下是否相等
├── status              # pass / warn / fail / error
├── summary             # 跨模态的简要摘要
├── changes[]           # 行、字段、区域、页面或时间区间
├── metrics[]           # 数值、单位、方向和阈值
├── artifacts[]         # patch、热图、波形、帧截图等
├── warnings[]
└── provenance
    ├── input hashes
    ├── normalized parameters
    ├── plugin/backend versions
    ├── environment
    └── timestamps and duration
```

比较器还应声明结果性质：是否对称、是否满足距离度量、是否可生成可逆 patch、是否确定性，以及对齐和规范化是否有损。

## 5. 底层框架与实现路线

### 5.1 技术栈

首个版本采用 Python，原因是科研与数据生态成熟，并能快速接入 Notebook 和比赛脚本：

- 标准库负责文件、哈希、文本和基础并发。
- NumPy/SciPy 负责数组、信号与统计计算。
- pandas/xarray 负责表格、坐标化和多维科研数据。
- Pillow/OpenCV/scikit-image 作为可选图片后端。
- Tree-sitter 作为可选代码解析后端。
- FFmpeg/ffprobe 作为可选外部音视频后端。
- PDF 使用可替换的文本提取与页面渲染后端。

性能热点可以在接口稳定后用 Rust 扩展，包括大文件分块、Myers 编辑路径、二进制块索引和并行指标计算。核心 API 不应提前绑定某个 FFI 实现。

### 5.2 执行与缓存

- 大文件使用流式读取、内存映射或分块计算，避免无界内存占用。
- 中间产物缓存键由输入哈希、规范化参数、插件版本和后端版本共同组成。
- 媒体和 PDF 解析运行在有超时、内存、磁盘和进程限制的工作单元中。
- 任何自动降采样、裁剪、重采样或颜色转换都必须出现在结果来源信息中。
- 比较任务支持取消和阶段级错误，单个渲染器失败不应破坏已有核心结果。
- 所有人类评审界面必须位于已验证 outcome 语义的下游。已备案的 renderer 与 UI
  路线见 [RFC 0004](rfcs/0004-human-review-ui-and-renderer-boundary_zh.md)。路线方向
  已获批准，但该 RFC 保持 Proposed 时仍未授权实施或排期。

## 6. 各模态基本原理

### 6.1 二进制

严格比较包括整体哈希、逐字节扫描和分块摘要。需要生成补丁时，使用滚动哈希、后缀索引或公共字节块搜索，将结果表达为 `COPY`、`ADD` 等指令。二进制比较不理解文件的内容语义；重新压缩后即使感知内容相同，字节差异也可能很大。

### 6.2 文本

文本先统一编码和换行策略，再按行、词或字符切分。核心使用 LCS/Myers 一类序列算法生成插入与删除编辑脚本，并将相邻变化组成 hunk。Patience/Histogram 可作为可选策略，利用唯一或低频行作为锚点，提高代码重排时的可读性。

### 6.3 源代码和配置

源代码解析为语法树后匹配节点，可弱化排版变化并表达节点插入、删除、更新和移动。JSON、YAML、TOML、XML 应解析为带类型的树或映射，再依据字段路径比较；键排序、数字表示和无关元数据属于可配置的规范化阶段。

显式 JSON 与受约束 YAML 1.2 比较契约已在
[RFC 0006](rfcs/0006-structured-data-comparison_zh.md) 中接受，但仍未实现。接受契约不会
扩展既有 text/binary automatic-detection 或 plugin-SDK 契约，也不授权实现门禁。

语法相同不等于运行语义相同。AST 比较需要明确其解析器版本、错误恢复策略和宏/预处理边界。

[RFC 0008](rfcs/0008-source-code-and-pdf-comparison_zh.md) 提议显式源代码比较契约与
独立授权的 Phase 6 门禁。它仍为 Proposed，不授权实现。

### 6.4 图片

严格模式将双方解码到统一尺寸、方向、色彩空间和 Alpha 表示，然后逐像素计算差异。可输出不同像素数、MAE、RMSE、PSNR 和热图。结构或感知模式使用 SSIM、MS-SSIM、LPIPS 或感知哈希。

平移一个像素可能制造大面积差异，因此配准、裁剪和缩放属于独立的对齐阶段，不能隐藏在指标内部。

### 6.5 音频

音频先统一采样率、声道与样本格式，通过时间戳或互相关对齐，再比较 PCM 波形、STFT/Mel 频谱、SNR 或感知质量。毫秒级延迟、增益或重采样都会破坏严格样本比较，因此必须区分“信号相同”和“听感接近”。ViSQOL、PESQ/POLQA 等可作为可选后端，而不是核心依赖。

### 6.6 视频

视频比较需要解封装、解码、时间轴对齐、帧率和分辨率统一、颜色空间规范化，再执行逐帧 PSNR、SSIM、VMAF 等指标并沿时间聚合。检测剪辑、插帧和镜头重排时，需要镜头切分、帧指纹或特征序列匹配，不能只依赖视频质量指标。音轨应作为独立模态比较并与视频时间线关联。

### 6.7 PDF

PDF 同时包含文本、绘制指令、字体、图片和页面布局。应提供三种可组合视角：提取文本比较、PDF 对象/元数据比较、页面渲染后的图片比较。不同生成器可能产生完全不同的内部对象但视觉页面一致，因此不能只做二进制 Diff。

[RFC 0008](rfcs/0008-source-code-and-pdf-comparison_zh.md) 提议 PDF 的显式 view
契约：binary、extracted text、objects/metadata 与 rendered pages。它仍为 Proposed，
不授权实现。

### 6.8 表格、数组和统计数据

比较顺序为 schema、维度、坐标/主键对齐、元素容差、汇总误差和分布差异。必须定义 dtype、单位、缺失值、NaN/Inf、绝对/相对误差和浮点 ULP 策略。

[RFC 0006](rfcs/0006-structured-data-comparison_zh.md) 已接受更窄的首个 table/array
切片契约：使用确定性 alignment 与 numeric semantics 的显式分隔符表格和 immutable dense
array。它仍未实现且分别设置门禁。生态 adapter、coordinate alignment、unit 与 statistical
equivalence 仍是后续契约回调。

统计比较可以包含 KS、Wasserstein、卡方、置信区间和效应量。p-value 不可单独决定是否存在实际差异；结果应同时报告效应量、样本量、多重比较校正和科研任务定义的实际容差。

## 7. 里程碑

分阶段交付计划及实现门禁由 [RFC 0002](rfcs/0002-development-phases-and-text-slice_zh.md) 定义。Phase 2 的有界探测、内部能力解析和精确二进制比较已实现 [RFC 0003](rfcs/0003-automatic-detection-capability-resolution-and-binary-comparison_zh.md)。Phase 3 门禁 P3-A、P3-B 与 P3-C 已实现 [RFC 0005](rfcs/0005-third-party-plugin-discovery-sdk-and-compatibility_zh.md) 的 SDK declaration/discovery、显式选择的 detector/comparator/renderer 执行、schema-v2 provenance、显式 CLI opt-in 与 compatibility receipt。下方版本分组只描述产品方向，不表示后续能力已经实现。

Phase 1 至 Phase 3 包含 Python 包、schema-v1/v2 契约、显式文本、有界文本/二进制
探测、精确二进制比较、CLI、terminal/JSON renderer 与显式 plugin boundary，且仍未
发布。Phase 4 structured-data 契约已在
[RFC 0006](rfcs/0006-structured-data-comparison_zh.md) 中接受，但仍未实现且需要单独门禁授权。
下列其他模态与 renderer 仍是计划能力。

### v0.1：核心闭环

- 插件注册、`CompareSpec`、`DiffResult` 和来源记录。
- 二进制、文本、JSON/YAML、CSV/数组和图片比较。
- Terminal、JSON 和静态 HTML 输出。
- 可复现测试语料与确定性 CI。

### v0.2：结构和文档

- Tree-sitter 代码比较。
- XML/TOML 和复杂表格对齐。
- PDF 文本与页面渲染双视角。
- JUnit 和基准结果管理。

### v0.3：时序媒体

- 音频时间/频谱比较。
- 视频帧、时间线和质量指标。
- 可选 FFmpeg、ViSQOL、VMAF 后端。
- 插件 SDK 和第三方能力清单。

## 8. 合规与安全清单

### 8.1 源码与算法

- 核心实现保持独立编写，不复制其他项目的源码、注释、测试和文档表达。
- 为来自论文、标准或公开资料的算法维护英文权威文档 `docs/algorithm-references.md`，并在需要时同步中文翻译 `docs/algorithm-references_zh.md`。
- 引入代码前确认许可证兼容性，不把“公开可见”误认为“允许使用”。
- 若计划商业化，对目标司法辖区和多媒体算法进行专利风险评估。

### 8.2 开源许可证与依赖

- 项目许可证候选为 Apache-2.0，以获得宽松使用条件和明确的贡献者专利授权；正式发布前完成选择。
- 每个依赖记录 SPDX 标识符、版本、来源、用途和分发方式。
- 提供 `LICENSE`、`NOTICE`、`THIRD_PARTY_NOTICES` 和 SBOM。
- 将 GPL/AGPL、商业双重许可和许可证不明的实现隔离为可选后端，并单独评估组合与分发义务。
- 调用外部 CLI 不代表自动免责；捆绑其二进制时仍需履行对应许可证。

### 8.3 音视频与 PDF

- 默认不捆绑 FFmpeg 或编解码器二进制；优先发现用户安装的外部工具。
- 记录 FFmpeg 构建配置，避免分发启用了 `nonfree` 的组合。
- 将开源许可证合规和 H.264/H.265/AAC 等潜在专利许可分开评估。
- PDF 渲染后端逐一审查许可证，避免无意把强 Copyleft 依赖并入宽松许可核心。

### 8.4 数据和比赛规则

- 测试仓库只包含自行生成、公有领域或明确允许再分发的数据。
- 对受限数据使用下载脚本、哈希或本地 fixture，不上传原始文件。
- 遵守比赛对测试集、隐藏标签、模型输出、派生数据和外部工具的限制。
- 默认不在报告中嵌入完整输入；缩略图、文本摘录和媒体片段由用户显式启用。
- 对个人信息、未公开科研数据和文件元数据提供脱敏与本地处理策略。

### 8.5 项目治理

- 确认代码是否属于学校、实验室、资助项目或雇主的职务成果。
- 外部贡献采用 DCO 或 CLA，并明确贡献的许可证和来源声明。
- 项目名称、Logo 和文档不得暗示与 Git、FFmpeg 或其他项目存在官方关联。
- 发布流程执行许可证扫描、秘密扫描、SBOM 生成和测试数据来源检查。

## 9. 完成标准

一个比较器只有在满足以下条件时才被视为可发布：

1. 定义支持的格式、语义和不支持场景。
2. 规范化与对齐步骤可以被关闭、配置和审计。
3. 指标具有单位、方向、阈值和解释。
4. 对空文件、损坏文件、超大文件和恶意输入有明确行为。
5. 结果可序列化，并在相同环境中确定性复现。
6. 测试数据来源和所有运行时依赖的许可证已经记录。
