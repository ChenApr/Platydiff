# 插件 SDK 与显式发现

[English documentation](plugin-sdk.md)

Phase 3 门禁 P3-A 实现了
[RFC 0005](rfcs/0005-third-party-plugin-discovery-sdk-and-compatibility_zh.md)
中的声明与 discovery 子集，但不执行插件 detector、comparator 或 renderer。
comparison host、schema-v2 provider provenance、CLI 插件参数和兼容性 receipt 仍由
P3-B 与 P3-C 门禁控制。

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
manifest factory，协商 API minor `0` 与 required host feature，并返回 immutable
`PluginCatalogV1`。catalog 暴露安全的 entry-point metadata、已加载 manifest、无冲突
capability declaration 与稳定 issue。distribution version 与 plugin version 始终是
两个独立 identity。

空 allowlist 不加载任何插件。disabled、malformed、duplicate 或 conflicted entry point
永不 import。某个插件的 import、factory、manifest、API 或 feature 失败不会丢弃其他
插件。重复 capability ID 与保留的 `core` capability namespace 会从 capability catalog
移除，并记录 `capability_id_conflict`。metadata 与 issue 顺序不依赖环境枚举顺序；issue
不复制 exception text、traceback 或文件系统路径。

`import platydiff` 与现有三参数 `compare()` 都不会枚举或加载已安装插件。因此安装插件
不会改变内置比较路径。entry point 仍是受信任的进程内 Python code：显式加载不是
sandbox，import 或 factory side effect 可使用当前进程的全部权限。

## 当前边界

P3-A 只对 declaration 建立 catalog。目前没有 public registration method、全局第三方
registry、`PluginHost.compare()`、capability invocation、插件 CLI option、renderer
hook、schema-v2 provider record、v1-to-v2 upgrader 或已发布 compatibility receipt。
Phase 1/2 的私有 request、registry、execution-limit、source-snapshot 与 stage-runner
type 继续保持私有，也不会传给插件。

## 版本基线与后续执行

P3-A 刻意把 SDK API `1.0` 冻结为仅声明的基线。`CapabilityDeclarationV1` 只包含
inventory data，不含 executor、callback、detector、comparator、renderer、source
service 或私有 core handle。因此 minor-0 manifest 可用于显式 discovery 与协商，
但不能运行 comparison。

P3-B 可以通过 additive SDK minor 或 negotiated host feature 增加 executable typed-handle
protocol 与 host composition。它必须把新 handle 与现有 declaration 关联，而不能重新
解释 `CapabilityDeclarationV1` 或向其中加入 callable state；现有 API-1.0 manifest
factory、field、default、validation 与 discovery result 必须继续有效。删除或改变这个
已冻结 declaration 契约的含义需要新的 major entry-point group，不能作为 P3-B minor
update 完成。
