# 插件 SDK 与显式发现

[English documentation](plugin-sdk.md)

Phase 3 门禁 P3-A 与 P3-B 实现了
[RFC 0005](rfcs/0005-third-party-plugin-discovery-sdk-and-compatibility_zh.md)
中的 declaration、discovery、显式选择的 detector/comparator 执行与 provider
provenance。Renderer 执行、CLI 插件参数和发布的 compatibility receipt 仍由 P3-C
门禁控制。

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
现有三参数 `compare()` 和 CLI 仍返回 schema v1。reader 同时接受两个版本；
`upgrade_outcome_v1_to_v2()` 在不改变 v1 result 含义的前提下添加空 host context。
Schema-v1 model 与 encoder 拒绝嵌套 schema-v2 value；schema-v2 构造与读取会将
provider-backed attempt 与 loaded host snapshot、selected comparator/detector provenance
进行交叉校验，要求 selected comparator version 与 result provenance 一致，并对
distribution/version identity 执行 SDK 同级校验。内建 terminal 与 JSON renderer 同时
接受两个 outcome schema 版本，且不会重算 result 语义。

当前仍没有 public mutable registration method、全局第三方 catalog、renderer hook、插件
CLI option 或发布的 compatibility receipt。私有 request、snapshot、descriptor 与
stage runner 不会传给插件。
