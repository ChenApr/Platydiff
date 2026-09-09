# 插件 SDK 与显式发现

[English documentation](plugin-sdk.md)

Phase 3 门禁 P3-A、P3-B 与 P3-C 实现了
[RFC 0005](rfcs/0005-third-party-plugin-discovery-sdk-and-compatibility_zh.md)
中的 declaration、discovery、显式选择的 detector/comparator 执行、有界 renderer
执行、CLI opt-in、provider provenance 与 compatibility receipt。

## 声明一个 SDK-v1 manifest

SDK v1 只使用 `platydiff.plugins.v1` entry-point group。entry-point name 是小写
reverse-domain 插件 ID，target 是无参数 manifest factory：

```toml
[project.entry-points."platydiff.plugins.v1"]
"org.example.scidiff" = "example_scidiff.plugin:manifest"
```

```python
from platydiff.plugin_sdk import (
    CapabilityDeclarationV1,
    CapabilityKind,
    PluginManifestV1,
)


def manifest() -> PluginManifestV1:
    return PluginManifestV1(
        manifest_schema_version=1,
        plugin_id="org.example.scidiff",
        plugin_version="1.0",
        api_major=1,
        minimum_api_minor=0,
        maximum_api_minor=0,
        required_host_features=(),
        capabilities=(
            CapabilityDeclarationV1(
                capability_id="org.example.scidiff.text_exact",
                kind=CapabilityKind.COMPARATOR,
                implementation_version="1.0",
            ),
        ),
        license_expression="Apache-2.0",
    )
```

manifest、capability、dependency 与 component declaration 都是 frozen value
object。实现会验证 ID 与整数范围，把 collection 规范化为确定性 tuple；所有会进入
catalog 或 compatibility profile 的 manifest string 都有长度边界，且不得包含 control
character 或文件系统路径。capability/backend ID 必须使用 plugin ID 前缀。dependency、
license、Python version、platform 与 native/external component field 只用于 inventory；
host 不负责解析依赖，也不据此作出法律或平台支持判断。

distribution name 遵循
[PyPA 名称与规范化规范](https://packaging.python.org/en/latest/specifications/name-normalization/)：
名称以 ASCII 字母或数字开头和结尾，中间可以包含连续的 `.`、`_`、`-`；identity 比较
时，每段连续分隔符会折叠为一个小写 `-`。原始的无路径拼写仍用于展示和确定性的最终
tie-break。

## 发现精确 allowlist

discovery 只能通过显式调用触发：

```python
from platydiff import PluginDiscoveryPolicy, discover_plugins

catalog = discover_plugins(
    PluginDiscoveryPolicy(
        enabled_plugin_ids=("org.example.scidiff",),
    )
)
```

该调用会快照匹配的 distribution metadata，验证精确 allowlist 与冲突，只加载被选中的
manifest factory，协商 API minor `0` 或 `1` 与 required host feature，并返回 immutable
`PluginCatalogV1`。minor-0 的 declaration-only manifest 仍可加载；executable handle
要求协商 minor 1 与 `host.execution.v1`。catalog 暴露安全的 entry-point metadata、已加载 manifest、无冲突
capability declaration 与稳定 issue。distribution version 与 plugin version 始终是
两个独立 identity。

空 allowlist 不加载任何插件。disabled、malformed、duplicate 或 conflicted entry point
永不 import。某个插件的 import、factory、manifest、API 或 feature 失败不会丢弃其他
插件。重复 capability ID 与保留的 `core` capability namespace 会从 capability catalog
移除，并记录 `capability_id_conflict`。metadata 与 issue 顺序不依赖环境枚举顺序；issue
不复制 exception text、traceback 或文件系统路径。验证 executable handle shape 时，普通
descriptor/property failure 只会将对应插件隔离为 `plugin_manifest_invalid`；
process-control exception 与 `MemoryError` 仍继续传播。

`import platydiff` 与现有三参数 `compare()` 都不会枚举或加载已安装插件。因此安装插件
不会改变内置比较路径。entry point 仍是受信任的进程内 Python code：显式加载不是
sandbox，import 或 factory side effect 可使用当前进程的全部权限。

## 通过 immutable host 执行

SDK API `1.1` 增加可选的 typed detector/comparator handle，并用 capability ID 将其与
保持不变的 declaration object 关联。`PluginHost.discover()` 冻结一份 allowlist catalog
snapshot。`PluginHost.compare()` 默认使用内建能力；第三方能力必须通过 `detector_id=`
或 `comparator_id=` 显式 pin，单纯 enable 不会改变 selection。自动比较也接受精确的
内建 `text` 或 `binary` comparator pin，并将 detection 限定为该 modality，而不会
fallback 到其他 comparator。

host 提供有界 source service，拥有全部 lifecycle transition，并对每次 comparison 创建
fresh comparator run，严格按 `decode`、`normalize`、`align`、`compare`、`aggregate`
顺序各调用一次。插件返回 `PluginComparisonV1` facts 而不是 outcome。已知插件失败在
观测到的 stage 映射；process-control exception 与 programming exception 继续从 Python
API 传播。executable handle 与 run shape 会在 invocation 前验证。host 不会永久保留已
结束的 run，但仍跟踪 live run identity；detector execution 前先记录 selection；在构造
completed outcome 前，还会在 validated aggregation 后重新检查 mutable path snapshot。

availability result 的 backend ID/version pair 必须与 capability declaration 中的 pair
完全一致（包括 `None`/`None`）；SDK v1.1 不接受未声明的 runtime backend。已知的
availability failure 与 invalid return value 会在 detecting 或 resolving 边界形成结构化
failed outcome，并保留唯一、可审计的 failed attempt。插件 facts 不得声明 host 保留的
source-byte resource name；冲突会在 outcome 构造前于 aggregating stage 失败。

自动比较的 exact comparator pin 会在内容检测前验证。capability 缺失、executor 缺失、
capability kind 错误或 modality 不受支持时，会返回 `capability_unavailable`，并在唯一的
pinned attempt 上保留具体且安全的 reason；既不 fallback，也不伪装为 detection
no-match。host 会在 aggregating stage 独立重构返回的 facts，并执行 resolved text/binary
契约。当前 spec 拒绝 partial 或 degraded result，要求严格的 `equal`/`pass` 与
`different`/`fail` 映射，拒绝 text/binary 内建 change kind 交叉，并执行
`max_change_items` 与 canonical UTF-8 schema payload bytes 上限。插件必须依照声明的
`ChangeSet` 契约自行截断；host 会拒绝超限 facts，不会静默修改。插件的 truncated
result 必须声明 `change_items` 或 `change_payload_bytes`，且 `limit` 必须精确复制对应的
有效 spec 上限。

Comparator run object 必须支持 Python weak reference。这个 SDK-v1.1 run 要求使长生命周期
host 能拒绝复用同一个 live run，同时不永久保留所有 completed run。结构完整但无法 weakly
reference 的 run 会在任何 lifecycle method 调用前，于 resolving stage 安全拒绝。

每次 host comparison 都返回 schema v2，包括最终选择内建能力的情况。schema v2 记录
enabled/loaded provider snapshot、带版本的 attempt 与 selected-provider provenance。
现有三参数 `compare()` 和不含 plugin/capability 参数的 CLI 命令仍返回 schema v1；
启用或 pin 插件 capability 的 CLI 命令经 host 返回 schema v2。若 CLI 在 discovery 后出现
非预期失败，failure outcome 会保留精确的 loaded provider snapshot；若 discovery 本身失败，
则只记录 enabled ID，loaded provider 为空。reader 同时接受两个版本；
`upgrade_outcome_v1_to_v2()` 在不改变 v1 result 含义的前提下添加空 host context。
Schema-v1 model 与 encoder 拒绝嵌套 schema-v2 value；schema-v2 构造与读取会将
provider-backed attempt 与 loaded host snapshot、selected comparator/detector provenance
进行交叉校验，要求 selected comparator version 与 result provenance 一致，并对
distribution/version identity 执行 SDK 同级校验。内建 terminal 与 JSON renderer 同时
接受两个 outcome schema 版本，且不会重算 result 语义。

## 编写有界 renderer

SDK-v1.1 renderer handle 包含一个已声明 capability ID、确定性的 media type tuple、
availability probe 与 `render()` method。通过 manifest 的 `capability_handles` tuple 将
handle 与匹配的 `CapabilityDeclarationV1` 关联：

```python
from dataclasses import dataclass

from platydiff.core.models import AnyCompareOutcome
from platydiff.plugin_sdk import (
    CapabilityAvailabilityV1,
    CapabilityDeclarationV1,
    CapabilityKind,
    PluginManifestV1,
    RendererPresentationOptionsV1,
    RendererSinkV1,
)


@dataclass
class SafeTextRenderer:
    capability_id: str = "org.example.scidiff.safe_text"
    media_types: tuple[str, ...] = ("text/plain; charset=utf-8",)

    def availability(self) -> CapabilityAvailabilityV1:
        return CapabilityAvailabilityV1(True)

    def render(
        self,
        outcome: AnyCompareOutcome,
        options: RendererPresentationOptionsV1,
        sink: RendererSinkV1,
    ) -> None:
        del options
        sink.write_text(f"{outcome.kind}:{outcome.schema_version}")


def manifest() -> PluginManifestV1:
    renderer = SafeTextRenderer()
    declaration = CapabilityDeclarationV1(
        capability_id=renderer.capability_id,
        kind=CapabilityKind.RENDERER,
        implementation_version="1.0",
    )
    return PluginManifestV1(
        manifest_schema_version=1,
        plugin_id="org.example.scidiff",
        plugin_version="1.0",
        api_major=1,
        minimum_api_minor=1,
        maximum_api_minor=1,
        required_host_features=("host.execution.v1",),
        capabilities=(declaration,),
        license_expression="Apache-2.0",
        capability_handles=(renderer,),
    )
```

Renderer 只得到 validated outcome 副本、presentation options 与 host-owned sink；不会
得到 source、path、registry、artifact root 或 comparison callback。每次调用只能选择
`write_text()` 或 `write_bytes()` 之一。Sink 强制精确 UTF-8 byte budget 与声明的 media
type。`text/*` media type 始终采用严格 UTF-8 text mode，包括通过 `write_bytes()` 提供的
bytes；无效 UTF-8 会导致 rendering 失败，有效 bytes 仍需通过 CLI terminal safety 检查。
生成 terminal text 的 renderer 必须转义恶意 control character；CLI 会在 plugin
text 写入 stdout 前拒绝 BOM、bidi control 与除 newline 外的 C0/C1 control。Renderer
不得重算 relation、verdict、metric、completeness 或其他 comparison fact。SDK v1 不
提供任意文件写入、HTML policy 或 UI behavior。

Python 调用方只在 comparison 之后选择 renderer：

```python
from platydiff import PluginDiscoveryPolicy, PluginHost
from platydiff.plugin_sdk import RendererPresentationOptionsV1

host = PluginHost.discover(PluginDiscoveryPolicy(("org.example.scidiff",)))
outcome = host.compare(before, after, spec)
rendered = host.render(
    outcome,
    renderer_id="org.example.scidiff.safe_text",
    options=RendererPresentationOptionsV1(max_output_bytes=1_048_576),
)
```

`RenderedOutputV1` 记录精确的 renderer/provider/backend identity、media type、有界
bytes 与是否为 UTF-8 text。其 public constructor 会验证 namespace、identity string、
media type、bytes/boolean 类型、backend pair、provider 类型与 text UTF-8 一致性。
renderer 缺失、不可用、输出无效、执行失败或越界时，会抛出携带原始未变 outcome 的
typed renderer error，且不会隐式 fallback。

## 从 CLI 选择插件与 capability

`--plugin` 可重复使用，是精确 allowlist；它只启用加载：

```bash
platydiff compare --type auto \
  --plugin org.example.scidiff \
  --detector org.example.scidiff.text_binary_detector \
  --comparator org.example.scidiff.text_exact before.dat after.dat

platydiff text \
  --plugin org.example.scidiff \
  --renderer org.example.scidiff.safe_text \
  --renderer-media-type "text/plain; charset=utf-8" \
  --max-render-bytes 1048576 before.txt after.txt
```

`--detector` 仅用于自动比较。Capability ID 精确匹配；缺失或不可用时绝不选择替代项。
重复/无效 plugin ID、无效 media type 或 limit，以及没有 `--renderer` 却提供 renderer
专用参数，都是 exit `2` 的用法错误。Comparison unavailable/failure 与 renderer failure
使用 exit `3`；renderer failure 只向 stderr 输出
`platydiff: rendering failed safely`，且没有 fallback output。环境变量、配置文件、安装、
升级、下载与依赖解析仍不在范围内。

## 运行兼容性套件并创建 receipt

源码发行包包含 `tests/plugin_compatibility`。请在包含待测插件与 backend 精确版本的隔离
Python 3.12+ 环境中运行：

```bash
python -m pytest tests/plugin_compatibility
```

Profile 覆盖 manifest/API negotiation、显式 discovery、detector/comparator lifecycle、
renderer authority 与 bounds、terminal control safety、dependency/license/platform
inventory、确定性顺序、redaction，以及 discovery 到 CLI 的 failure-isolation matrix。
`tests/plugin_compatibility/profiles.py` 中的 receipt helper 要求为每个实际执行的 profile
提供一个 `CompatibilityProfileResultV1`；每项都包含 pass/fail 与非空的 normalized
evidence summary。Canonical JSON 会把这些结果与精确 suite/host version、plugin/
distribution identity、协商后的 SDK 与 outcome schema version，以及 backend/platform
inventory 一起记录；SHA-256 digest 覆盖 normalized per-profile result。Evidence 在 result
构造时会被递归快照，并在 receipt 输出时再次校验；任何包含 `/` 或 `\` 的字符串都会被拒绝，
防止嵌入式本地路径进入 receipt。每一层 evidence key 也必须是有界的 lowercase ASCII
identifier。只有全部 profile
都 passed 时，整体 result 才是 `conforms` 并出现唯一允许的
`conforms to Platydiff plugin profile X under suite version Y.` 声明；failed 或 mixed
receipt 不包含 conformance claim。

Receipt 是 self-attestation，不是认证、背书、安全评审或再分发许可。Plugin code 是受信任
的 in-process Python；least-authority API 只能减少误用，并不提供 sandbox。插件作者负责
dependency pin/hash、license text、NOTICE/SBOM 义务、export control、patent review 与再
分发许可。Platydiff 不安装或获取插件；disabled plugin 不会为了扩充 inventory 而被导入。

当前没有 public mutable registration method 或全局第三方 catalog。私有 request、
snapshot、descriptor 与 stage runner 不会传给插件。新模态、配置文件、任意 artifact、
HTML、TUI 与 desktop review 仍是计划能力，需通过各自门禁。
