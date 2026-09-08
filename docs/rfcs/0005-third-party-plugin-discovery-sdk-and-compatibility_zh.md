# RFC 0005：第三方插件发现、SDK 与兼容性

[English documentation](0005-third-party-plugin-discovery-sdk-and-compatibility.md)

- 状态：Proposed
- 日期：2026-09-09
- Owners：Platydiff 维护者
- 实现 owner：等待接受并获得显式授权后指派

## 摘要与授权边界

本 RFC 提议 Phase 3：显式发现已安装的 Python 插件、版本化插件 SDK、确定性的
capability 选择，以及兼容性套件。它以已实现的 Phase 1 text 和 Phase 2 auto/binary
路径为证据，而不是沿用早期的单一插件类草图。

本 RFC 不构成实施授权。在状态为 `Proposed` 时，任何 entry-point group、SDK symbol、
CLI option、兼容性标志或第三方执行行为都不是公共契约。接受前必须解决本文末尾的
人类决策。实施还需要另行派发会话，并从更新后的 `main` 新建分支。

Phase 3 不授权新模态，也不授权 [RFC 0004](0004-human-review-ui-and-renderer-boundary_zh.md)
提议的 UI 工作。首版 SDK 刻意只用现有 `text` 与 `binary` 契约验证。

## 来自 Phase 1 与 Phase 2 的证据和经验

当前实现提供了下列证据。这些观察是公共协议的约束，并非对私有实现的否定。

| 当前代码与测试中的证据 | Phase 3 经验 |
| --- | --- |
| 显式 text 使用小型私有 `_registry.py`；auto/binary 使用另一套私有 `CapabilityCatalog`。 | 不公开其中任何一个。定义统一且不可变的公共 catalog；只有兼容性测试存在后才把 built-in 适配到它。 |
| `CapabilityRequest` 和 `ExecutionLimits` 是只从一个公共 spec 规范化得到的私有值。 | 保留“公共意图/私有执行”分层。插件获得 SDK request view，而不是内部 request 或第二套 limit 来源。 |
| `CapabilityRecord.executor` 不是 snapshot path 的调用边界；pipeline 在 resolution 后直接导入具体 comparator。 | 允许第三方代码前，resolution 与 invocation 必须通过类型化且有测试的 capability handle 连接。 |
| `SourceSnapshot` 负责有界 replay、单次打开 path descriptor、mutation check 和带 stage 的 failure。 | host 保持 snapshot ownership。插件只获得更窄的只读 source service，不获得私有 snapshot 或不受限 path。 |
| 显式 text 刻意保留 eager 兼容路径，auto/binary 使用 replayable snapshot。 | 公开当前 comparator signature 会冻结偶然形成的分裂。SDK 需要能适配两条路径的 host-driven lifecycle。 |
| detection 是确定性的，但 schema 限定为 `text`/`binary`、单个顶层 detector record、每来源每模态一个 candidate。 | SDK v1 对现有模态每次只能选择一个 detector provider。多 detector fusion 与新 modality ID 需要后续 schema callback。 |
| 已测试注册顺序无关、重复拒绝、稳定拒绝原因、显式 bypass 和 late-invalid 不 fallback。 | 插件发现必须保持这些属性，不能引入 filesystem/import order 或 wall-clock tie-break。 |
| `ExtensionChange` 可安全保留 namespaced kind 与 JSON-safe payload，而 `CompareSpec` 及 built-in detection/change union 仍封闭。 | 第三方 comparator 可为现有 spec 产生 extension change；安装插件不能直接引入新公共 modality 或 spec。 |
| `CapabilityAttempt` 不含 distribution identity/version；comparison provenance 也没有显式 provider/backend record。 | 可复现插件执行在实施前需要获批的 additive provenance extension 或新 outcome schema。 |
| built-in renderer 消费 `CompareOutcome` 且不读取原始来源。 | renderer plugin 只能获得 validated outcome 与有界 host sink；它位于比较真值下游，并与 UI-U1 分离。 |

Phase 2 关于排序、重复拒绝、拒绝原因、snapshot replay、mutation、显式 override、后期
decode failure 和稳定 wire 的契约测试，将成为 Phase 3 兼容性套件的回归输入。

## 目标与非目标

Phase 3 目标是：

- `import platydiff` 时不发现、不导入、不执行插件；
- 通过 Python distribution entry point 显式、按 allowlist 发现插件；
- 用一个版本化 manifest 声明 detector、comparator 和 renderer capability；
- discovery、negotiation、resolution、attempt 与 provenance 全部确定；
- source、lifecycle、budget、outcome construction 与 validation 由 host 所有；
- 隔离失败，使无关的损坏插件不影响 built-in comparison；
- 提供可自行运行、带机器可读 receipt 的兼容性套件；
- 为每个启用的 provider 记录 dependency、license、platform 与 supply-chain inventory。

Phase 3 不包含：

- 自动安装、升级、下载或依赖解析；
- 隐式启用全部已安装插件；
- mutable global registry 或 import-time registration decorator；
- 新 spec kind、新模态、多 detector fusion 或自定义配置语言；
- 跨进程或网络插件 transport；
- 声称进程内 Python 代码受到 sandbox；
- HTML、TUI、desktop 或 local-web UI 实施；
- 插件生成 patch、修改 source、遍历目录、URL source 或任意发布 artifact；
- 官方认证第三方质量或安全性。

## 术语与信任模型

**Distribution** 是 `importlib.metadata` 可枚举的已安装 Python distribution；
**plugin** 是一个 distribution entry point 暴露的版本化 manifest；**capability** 是
manifest 中的 detector、comparator 或 renderer declaration；**backend** 是 capability
使用的实现依赖，也可以就是 Python 实现本身。

Entry point 是可执行代码引用，不是被动数据。枚举 entry-point metadata 不必导入插件，
但加载 target 会执行代码。因此 Phase 3 把每个第三方插件视为调用方显式启用且受信任的
进程内代码。Host 验证所有返回值，但无法阻止恶意插件读取进程内存、访问文件系统、
启动进程或使用网络。Conformance 是契约，不是 sandbox。

默认 `compare()` 保持 built-in-only。安装 package 不得改变其结果、import、candidate
顺序、时间路径或 JSON。

## Distribution metadata 与 entry-point 契约

### 单一 manifest group

SDK major 1 只使用一个 entry-point group：

```text
platydiff.plugins.v1
```

Entry-point name 就是 plugin ID，必须是 `org.example.scidiff` 形式的小写 reverse-domain
identifier。Target 是返回 `PluginManifestV1` 的无参数 callable：

```toml
[project.entry-points."platydiff.plugins.v1"]
"org.example.scidiff" = "example_scidiff.plugin:manifest"
```

不检查 `platydiff.detectors` 等 role-specific group 或 import-time registration module。
未来不兼容 SDK 使用新 major group，例如 `platydiff.plugins.v2`，不得重新解释 v1 target。

一个 distribution 可以暴露多个 plugin，但每个 plugin 恰有一个 entry point 和一个
manifest。加载前记录 distribution name/version 与 entry point 的 name/group/value。
这些名称与版本属于不可信展示数据，renderer 必须转义。

### 枚举、启用与加载

Discovery 被显式拆成三步：

1. **Enumerate：** 快照化匹配的已安装 entry-point metadata，不导入 target。
2. **Select：** 校验 metadata、应用调用方精确的 plugin-ID allowlist、隔离 conflict，
   并生成确定性的 load plan。
3. **Load：** 只导入并调用被选 factory；校验 manifest、协商 SDK，并冻结 immutable catalog。

只在调用 `discover_plugins()` 时枚举；package import 与单独调用 `compare()` 都不会触发。
环境快照在 `PluginHost` 生命周期内固定；Python 环境改变后必须重新 discovery 和建 host。

不存在“默认启用全部已安装插件”。提议的 Python 形式为：

```python
policy = PluginDiscoveryPolicy(
    enabled_plugin_ids=("org.example.scidiff",),
)
host = PluginHost.discover(policy)
outcome = host.compare(before, after, spec)
```

现有三参数 `platydiff.compare(before, after, spec)` 保持不变且只使用 built-in。Host 构造后
不可变并可安全检查；不提供公共 `register()`，也没有进程全局第三方 catalog。

对应 CLI 设计是显式的，且仍受决策 P8 约束：

```text
platydiff ... --plugin org.example.scidiff \
  --comparator org.example.scidiff.text_exact
```

`--plugin` 可重复，只负责允许加载。选择第三方 detector、comparator 或 renderer 还需要
其稳定 capability ID；仅启用不能让插件静默排在 built-in 前。环境变量与配置文件不在范围。

### 非法、禁用、重复与冲突插件

- disabled entry point 永不导入；它只能出现在显式 inventory command 中，不能进入比较 provenance。
- malformed metadata 在 import 前隔离。
- import failure、factory 缺失/异常、invalid manifest 或 API incompatible 只隔离该插件。
- 多个 entry point/distribution 声明同一 plugin ID 时，全部以 `plugin_id_conflict` 隔离；
  version、path 或枚举顺序均不胜出。
- 启用的 manifest 内部或彼此间 capability ID 重复时，以 `capability_id_conflict` 隔离；
  built-in ID 与 `core` namespace 保留。
- entry-point name 必须与 `manifest.plugin_id` 完全相同；不一致是非法而非 alias。
- 显式要求被隔离或不存在的插件时，返回 resolving-stage unavailable outcome；无关非法插件
  不能改变 built-in 或其他已选插件 outcome。

Metadata 与 catalog issue 按 plugin ID、规范化 distribution name、distribution version、
entry-point value 与稳定 reason code 排序。安全 diagnostic 排除 Python environment path 和 traceback。

## Manifest 与 SDK 版本协商

规范概念结构为：

```python
@dataclass(frozen=True, slots=True)
class PluginManifestV1:
    manifest_schema_version: Literal[1]
    plugin_id: str
    plugin_version: str
    api_major: Literal[1]
    minimum_api_minor: int
    maximum_api_minor: int
    required_host_features: tuple[str, ...]
    capabilities: tuple[CapabilityDeclarationV1, ...]
    license_expression: str
```

Entry-point group 固定 API major。Host 只使用一个 API minor，并仅在下式成立时加载：

```text
minimum_api_minor <= host_api_minor <= maximum_api_minor
```

Minor release 只能 additive：可增加带默认值的 optional method/field/feature ID。删除或重释
field、改变 lifecycle 顺序或弱化 validation 都要求新的 major entry-point group。Manifest
schema version 与 outcome schema、SDK API version 相互独立。

Required host feature 是唯一且排序的稳定 identifier。不支持的 required feature 会在
capability resolution 前令插件 incompatible。Optional feature 只在双方均声明时使用；
禁止绕开协商而用 runtime duck typing 或 `hasattr`。

`plugin_version` 与已安装 distribution version 分别记录；可不同，但差异可见。兼容性套件
建议两者相等。Version string 是用于 identity/provenance 的 opaque Unicode；Phase 3 不为
排序版本而增加 runtime dependency。

Capability ID 与 plugin-defined backend ID 使用 plugin reverse-domain prefix。插件 priority
只能排序同一插件内 capability，不能跨 host selection tier 或抢占 built-in。

## 公共/私有边界与依赖方向

依赖方向变为：

```text
third-party plugin  --->  public plugin_sdk + public core models
                                      |
CLI / PluginHost / discovery ---------+
                 |
                 v
        private pipeline and sources
                 |
                 v
          built-in adapters
```

`core` 不导入 installed plugin、具体 comparator/renderer 或 `importlib.metadata`。Discovery
与 composition 位于 core 之外。公共 SDK 可导入稳定 core model；core 不得导入 SDK。

下列对象保持私有且永不传给插件：

- `CapabilityRequest`、`ExecutionLimits`、`CapabilityCatalog` 与 `InternalRegistry`；
- `SourceSnapshot`、raw path descriptor、`StageRunner` 与 comparator-local IR；
- internal clock、mutable diagnostic list 和 renderer implementation detail。

SDK 暴露 immutable request view、有界 source/probe service、capability declaration、plugin
result payload 与项目定义的 plugin exception。边界两侧的输入和返回 collection 都只读。

## Capability 职责

### Detector

Detector 只获得 host 捕获的 source kind、有界 prefix、prefix 是否到 EOF，以及 effective
detection limit。它不得重新打开 path、越过 prefix、检查 filename、使用 locale/time，
或执行 network/subprocess I/O。

SDK v1 detector output 只允许现有 `text` 与 `binary` modality candidate。Host 校验
confidence、identifier、evidence count 与 ordering，再构造 `DetectionRecord`。插件不能
返回 outcome，也不能选择最终 comparator。

每次 auto comparison 恰好使用一个 detector provider。Built-in detector 为默认；外部
detector 必须显式 pin。自动融合多个 detector 延后，因为 schema v1 无法无歧义地把 pair
candidate 归因给多个 detector provider。

### Comparator

Resolution 返回类型化 capability handle，而非无类型 `object`。Host 每次比较创建一个
run object，并按固定顺序调用：

```python
class ComparatorRunV1(Protocol):
    def decode(self) -> None: ...
    def normalize(self) -> None: ...
    def align(self) -> None: ...
    def compare(self) -> None: ...
    def aggregate(self) -> PluginComparisonV1: ...
```

Run 封装 plugin-local state。Host 拥有 stage transition，每个 method 最多调用一次，在实际
stage 映射已知 plugin exception，并拒绝乱序或复用 run。No-op stage 仍有 completed record。
插件不获得 `StageRunner`，无法追加或改写 execution history。

`PluginComparisonV1` 携带结构化比较事实：relation、verdict、fidelity、summary、changes、
metrics、evaluations、artifact refs、transformations、algorithm identity、确定性 resource
usage 与 safe diagnostics，但不携带 outer outcome 或 provider provenance。Host 校验全部
RFC 0001 invariant，绑定 selected manifest/capability/backend identity，构造
`ComparisonProvenance`，然后才构造 `DiffResult` 与 `CompletedOutcome`。

SDK v1 comparator 只接受现有规范化的 `TextCompareSpec` 或 `BinaryCompareSpec` intent。
Auto intent 由 host resolve，并继续作为记录的公共 spec。插件可返回 kind 位于自身 namespace
的 `ExtensionChange`，不得引入新 built-in change kind 或 spec。

Host source service 可 replay、有界，并暴露 safe label/source kind，同时核算每个 byte；
不暴露 absolute path。Host 保留 descriptor、hashing、mutation check、close behavior 与
resource limit enforcement。Capability 声明可消费 source bytes 的 lifecycle stage；其他
stage 的访问会显式失败。

### Renderer

Renderer 只获得 validated typed `CompareOutcome`、presentation options 与 bounded host sink；
不获得 source、snapshot、artifact root、path、registry 或 comparison callback。它可格式化或
组织既有事实，不得重新计算 relation、verdict、fidelity、metric、evaluation、change
completeness 或 problem meaning。

Sink 强制 output-byte limit，并捕获 text/bytes 与声明的 media type。SDK v1 renderer 不能
写任意 path。Renderer failure 发生在比较后，因此不能替换或修改 outcome；Python renderer
API 抛 renderer error，CLI 保持 exit 3 与安全 stderr 行为。

第三方 renderer output 是展示，不是持久 schema，也不是 `ArtifactRef`。Self-contained HTML、
overwrite rule、CSP 与人类评审 UI 仍完全由 RFC 0004 管理，需要单独授权。

## 确定性 resolution、availability 与 fallback

Discovery enumeration order 与 registration order 永不参与选择。Host 使用下列 tier：

1. 调用方显式 pin 的精确 capability ID；
2. compatible built-in capability；
3. 已启用的 compatible third-party capability。

Tier 3 内按 host policy priority、plugin ID、capability ID、backend ID、规范化 distribution
name 与作为 opaque final identity 的 distribution version 升序。插件不能凭安装顺序或更大
version 获得优先级。Exact pin 要么选中该 identity，要么 unavailable；不能静默替换。

Availability probe 在加载后、source comparison 前发生，且必须有界、确定、本地、与 input
无关。结果包含 available/unavailable、backend ID/version 和一个稳定 reason code。只有后续
获批 capability profile 允许时，probe 才可检查已导入 Python module 与本地 executable
metadata；SDK v1 conformance baseline 不启动进程、不使用网络。

Fallback 规则是：

- 未 pin 且 unavailable 的候选可在执行前跳过，并记录有序 rejected attempt；
- pinned candidate unavailable 时以 `unavailable` 结束；
- selected detector/comparator 的任一 method 开始后，失败不 fallback；
- exact text/binary intent 永不降级为 approximate semantics；
- 只有未来 spec 显式允许时才可 degrade，且必须设置 `fidelity=degraded`，记录 attempt 与
  diagnostic，并让 policy verdict 保持独立；
- renderer fallback 是调用方展示策略，不能改变 comparison outcome；CLI 不静默替换显式
  选择的 renderer。

SDK v1 禁止 retry。未来 retry policy 必须先定义确定性 attempt bound、idempotence 与 provenance。

## Outcome、provenance 与 schema 门禁

插件执行必须可序列化下列事实：

- enabled/loaded plugin ID；
- distribution name/version；
- manifest、协商后的 SDK version 与 feature；
- 适用的 capability、comparator、detector、backend、algorithm、implementation identity/version；
- 每个 rejected、selected、unavailable、fallback 与 failed attempt；
- 配置 limit 与实际确定性用量；
- 安全的 discovery、load、validation 与 execution diagnostic。

Renderer identity 属于独立 rendering result 或 compatibility receipt，因为 rendering 发生在
comparison outcome 已存在之后。

当前 schema 无法在不滥用 `capability_id`、`implementation_version` 或 diagnostic prose 的
情况下表示全部比较事实，也无法归因融合后的 detection candidate。因此 Phase 3 实施被决策
P6 阻塞。推荐使用 outcome schema v2，并包含：

- typed `ProviderIdentity`，记录 plugin、distribution、manifest 与协商后的 SDK identity/version，
  且不含 module path；
- capability attempt 上的 provider 与 capability/backend version；
- comparison provenance 上 optional selected provider；
- execution 上 optional plugin-host record，包含精确 enabled/loaded provider set 与协商 feature；
- 稳定的 `plugin_execution_failure` problem mapping；
- v1 reader 与有文档的 v1-to-v2 migration test。

Built-in-only v2 producer 省略 plugin-only field。既有 v1 payload 保持可读，golden fixture 不变；
若保留 legacy v1 encoder，它不能编码 plugin execution。复用 schema v1 必须显式修订 RFC 0003
决策 D3，是不推荐的替代方案。

Provider identity 不得包含 absolute path、module filesystem location、username、environment
variable、traceback、token 或 source content。Distribution/plugin string 在 manifest validation
后仍是不可信数据。

## Failure isolation 与稳定语义

Catalog 使用包括下列稳定 reason code：

```text
plugin_disabled
plugin_not_found
plugin_metadata_invalid
plugin_id_conflict
plugin_import_failed
plugin_factory_failed
plugin_manifest_invalid
plugin_api_incompatible
plugin_feature_unsupported
capability_id_conflict
capability_unavailable
backend_missing
backend_version_unsupported
```

无关 quarantined plugin 产生 inventory issue，不产生 comparison diagnostic。Required
plugin/capability 无法加载或 resolve 时，比较使用既有 `capability_unavailable` 或
`backend_unavailable` problem，并只在 structured details 放入有界 safe reason。

Selected plugin 抛出的已知异常在 method boundary 映射。Capability absence 仍为
`unavailable`；resource exhaustion、invalid plugin output 与 execution failure 为 `failed`，
且绝不是 content difference。建议新增稳定 `plugin_execution_failure` problem code，但它
需要 schema 决策 P6。Python API 继续传播 `KeyboardInterrupt`、`SystemExit` 与 `MemoryError`。
Library code 不静默转换 programming defect；CLI 保留最外层 safe `internal_error` 边界。

进程内 Python 无法安全地强制 timeout。正常结果必须依赖确定性 work/byte/count budget，
不能依赖 wall-clock deadline。Hung 或 malicious plugin 需要外部 process supervision，超出 SDK v1。

## 安全与 supply-chain 边界

- Platydiff 从不安装、升级或获取插件。
- 调用方提供精确 allowlist；host 不加载 disabled、conflicted 或仅 discovered target。
- Factory import 与 invocation 是分别记录的 failure boundary。
- Conformance 禁止 import-time side effect，但 host 无法对 malicious in-process code 强制执行。
- Manifest string、diagnostic、extension payload 与 renderer output 在进入 core model/terminal 前
  都要 validation 和 bound。
- Plugin code 只获得 least-authority service；这减少意外误用，但不构成 security sandbox。
- SDK v1 conformance profile 禁止 network、subprocess、动态 native-library loading、archive
  expansion 与 host sink 外写入。需要这些能力的插件必须等待后续 capability profile 与 threat-model review。
- 不因 package name、publisher、signature、download count、compatibility receipt 或 entry-point
  presence 自动信任。
- 可复现部署应由环境工具固定 distribution version/hash。Platydiff 记录 observed identity，
  但不是 package resolver 或 signature verifier。

## Dependency、license、platform 与 redistribution 契约

每个 manifest 声明 license expression，每个 capability 声明 runtime dependency、optional backend、
支持的 Python version/platform 与 native/external component。这些 declaration 是 inventory，
不是法律验证。加载前只能展示已安装 distribution metadata；manifest declaration 只对显式
loaded plugin 可用。不得为了丰富 inventory 而导入 disabled plugin。

Compatibility report 记录：

- plugin 与 distribution identity/version；
- 协商后的 SDK 与 outcome schema version；
- 声明的 license/dependency inventory；
- 测试的 Python implementation、OS、architecture 与 backend version；
- suite version、test-profile ID、result 和确定性 receipt digest。

第三方 plugin dependency 永不成为 Platydiff core dependency。独立分发的插件自行负责 license
text、NOTICE、SBOM、export control、patent review 与 redistribution permission。若 Platydiff
未来 bundle/redistribute 某 plugin/backend，项目必须独立完成 dependency/license review，
并在 merge 前更新 NOTICE/SBOM。Compatibility pass 不授予再分发许可。

最低 merge gate 是 Linux/Python 3.12。插件可声明更窄支持，但 host 必须把限制报告为
availability，而不是 import failure。跨平台声明需要每个所声称平台的 compatibility receipt。

## 兼容性套件与声明

Phase 3 套件作为开发/测试工具发布，在隔离测试环境对 plugin factory 运行。Profile 包含：

- metadata 与 manifest validation；
- API negotiation 与 required-feature rejection；
- discovery without import、显式 loading、conflict quarantine 与稳定排序；
- detector bound、candidate validation、determinism 与显式 pin；
- comparator lifecycle、source access、outcome、extension change、budget、failure mapping 与重复运行确定性；
- renderer semantic pass-through、output bound、恶意 text/control escaping，以及无法访问 source 的证明；
- dependency/license/platform inventory 与安全 redaction。

套件包含 synthetic licensed fixture，覆盖 equal、different、empty、corrupt、over-limit、repeated、
conflicting、unavailable-backend、invalid-output 与 exception。Comparator profile 复用适用的
text/binary oracle 与 schema round-trip test。套件随机化 discovery order，并验证 normalized
output 完全相同。

机器可读 receipt 是 self-attestation，包含准确 suite/host version 与 normalized result digest。
允许的表述是“conforms to Platydiff plugin profile X under suite version Y”。插件不得声称
“Platydiff certified”、已安全评审、获得背书，或兼容未测试 host version。官方认证计划
若有需要，另写 RFC。

兼容策略为：

- 支持一个 SDK major 期间，每个受支持 minor 都留在 CI；
- 保留 golden manifest 与 provider provenance；
- additive minor feature 必须有 fallback/default 与 old-plugin test；
- breaking SDK change 使用新 entry-point major 和 migration guide；
- outcome-schema migration test 覆盖 plugin-produced change/provenance；
- deprecation 至少跨一个有文档的 release line，且不能静默改变 capability selection。

## 提议的实施与 merge 门禁

本 RFC 为 `Proposed` 时，下列工作均不得开始。接受并显式授权后，使用三个可独立评审的
merge gate；除非用户批准 stacked review，否则不做 stacked PR。

### P3-A：SDK 与 discovery，不执行插件 capability

1. `feat(plugin-sdk): add versioned manifests and capability declarations`
2. `feat(plugins): add explicit entry-point discovery and negotiation`
3. `test(plugins): add manifest and discovery compatibility profiles`

门禁：公共名称和版本规则冻结；import Platydiff 与调用现有 `compare()` 都不枚举或加载插件；
disabled/invalid/duplicate/conflicting 和随机排序测试通过；不调用 comparator/detector/renderer。

### P3-B：comparison host 与 capability execution

1. `refactor(core): add typed capability handles and built-in adapters`
2. `feat(plugins): add host-driven detector and comparator lifecycles`
3. `feat(core): record plugin attempts and provider provenance`
4. `test(plugins): add detector and comparator conformance profiles`

门禁：决策 P6 已通过 migration test 实现；所有指定保持兼容的 Phase 1/2 payload 与 route 不变；
host-owned snapshot、stage、failure、resource 与 no-fallback test 通过；现有 `compare()` 保持 built-in-only。

### P3-C：renderer boundary、CLI opt-in 与文档

1. `feat(renderers): add bounded third-party renderer protocol`
2. `feat(cli): add explicit plugin and capability selection`
3. `test(plugins): publish compatibility receipts and full isolation matrix`
4. `docs: document plugin authoring, trust, and compatibility`

门禁：不引入 UI-U1 behavior；renderer failure 保留 outcome；CLI default/exit 保持兼容；检查
package content 与 license inventory；Ruff、strict mypy、完整 pytest、build 和默认分支 CI 通过。

每个 merge gate 都要求独立 contract review：把本 RFC 映射到 code/test，列出实际验证命令、
dependency/license impact，并确认无 source、fixture、secret、local path 或 generated artifact 泄漏。

## 接受前需要的人类决策

| ID | 决策 | 推荐默认值 | 后果 |
| --- | --- | --- | --- |
| P1 | 默认启用 | 保持 `compare()` built-in-only；要求精确 plugin-ID allowlist | 已安装 package 不能静默改变行为 |
| P2 | Entry-point layout | 只用 `platydiff.plugins.v1` 的单一 manifest factory | 原子 identity 与单一 negotiation boundary；保留 role-specific group |
| P3 | 首版 SDK modality scope | Detector/comparator 限定现有 text/binary spec，每次只使用一个 pinned detector | 不伪装 schema v1 已支持新模态或 detector fusion |
| P4 | Execution isolation | 从显式受信任的 in-process plugin 开始，并声明不存在 sandbox | SDK 可小步实施；不可信/跨进程执行需要后继 RFC |
| P5 | Outcome ownership | 插件返回 validated comparison payload；host 构造 provenance、`DiffResult` 与 outcome | 插件不能改写 execution history 或 provider identity |
| P6 | Outcome schema evolution | 使用 schema v2 并保留 v1 reading/migration support；只有选择不推荐的 additive-v1 方案时才修订 RFC 0003 D3 | Provider identity 与 plugin failure 类型化且可复现 |
| P7 | Fallback/retry | 允许执行前跳过未 pin 且 unavailable 的候选；禁止开始执行后的 fallback 与全部 v1 retry | 保留语义并让 attempt 可审计 |
| P8 | Renderer/CLI scope | 增加 bounded renderer protocol 与显式 capability flag，但不允许任意 file write 或 HTML/UI behavior | 保持 RFC 0004 独立，并防止隐藏激活插件 |

P1-P8 是推荐项，不是已批准决策。P6 是阻塞性 release 选择，必须与 RFC 0003 决策 D3
显式协调。接受时应在本节记录所选值与日期。

## 被拒绝的替代方案

### 导出当前 internal registry 与 source snapshot

拒绝原因：它们分裂的 signature、mutable registration、直接 concrete import 与 stage ownership
是实现细节，并已在 text/binary 间表现不同。

### 自动加载全部已安装插件

拒绝原因：安装行为会改变比较；import 可执行无关代码；环境枚举会成为隐藏输入。

### 让 plugin priority 覆盖 built-in

拒绝原因：package 可以静默接管现有 text/binary request。第三方选择必须显式，或只填补
unavailable tier。

### 把 entry-point metadata 或 compatibility receipt 当作 sandbox

拒绝原因：加载 Python entry point 会以当前进程权限执行代码；validation/self-test 不建立信任。

### 让插件返回完整 outcome

拒绝原因：插件可伪造 stage trace、provider provenance 或 unavailable semantics。Execution
与 outcome construction 必须由 host 所有。

### 在 Phase 3 发布通用新模态 spec

拒绝原因：每个 modality 都必须先通过自身 callback RFC 定义 comparison intent、change、metric、
artifact、failure 与 equivalence semantics。插件 transport 不能绕过这些门禁。

## 后果

提议的 SDK 刻意窄于任意 Python extension hook。它让第三方实现可确定、可审计地服务于
Platydiff 已理解的契约，同时把 installation、trust、新模态与 UI 保持为独立决策路径。
额外的 manifest、host、provenance 与 conformance 机制，是避免插件变成不可见第二条流水线的成本。
