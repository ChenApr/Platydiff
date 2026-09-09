# Plugin SDK and explicit discovery

[Chinese documentation](plugin-sdk_zh.md)

Phase 3 gate P3-A implements the declaration and discovery subset of
[RFC 0005](rfcs/0005-third-party-plugin-discovery-sdk-and-compatibility.md).
It does not execute plugin detectors, comparators, or renderers. Comparison
hosting, schema-v2 provider provenance, CLI plugin flags, and compatibility
receipts remain gated by P3-B and P3-C.

## Declare one SDK-v1 manifest

SDK v1 uses only the `platydiff.plugins.v1` entry-point group. The entry-point
name is the lowercase reverse-domain plugin ID and its target is a no-argument
manifest factory:

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

Manifest, capability, dependency, and component declarations are frozen value
objects. IDs and integer bounds are validated, collections become deterministic
tuples, provider identity strings are bounded and path-free, and capability or
backend IDs must use the plugin ID prefix. Dependency, license, Python-version,
platform, and native/external component fields are inventory declarations; the
host does not resolve dependencies or make legal or platform-support claims
from them.

## Discover an exact allowlist

Discovery is an explicit call:

```python
from platydiff import PluginDiscoveryPolicy, discover_plugins

catalog = discover_plugins(
    PluginDiscoveryPolicy(
        enabled_plugin_ids=("org.example.scidiff",),
    )
)
```

The call snapshots matching distribution metadata, validates the exact
allowlist and conflicts, loads only selected manifest factories, negotiates API
minor `0` and required host features, and returns an immutable `PluginCatalogV1`.
The catalog exposes safe entry-point metadata, loaded manifests, conflict-free
capability declarations, and stable issues. Distribution and plugin versions
remain separate identities.

An empty allowlist loads nothing. Disabled, malformed, duplicate, or conflicted
entry points are never imported. One plugin's import, factory, manifest, API, or
feature failure does not discard another plugin. Duplicate capability IDs and
the reserved `core` capability namespace are omitted from the capability
catalog with `capability_id_conflict`. Metadata and issues use deterministic
ordering independent of environment enumeration order; exception text,
tracebacks, and filesystem paths are never copied into issues.

`import platydiff` and the existing three-argument `compare()` do not enumerate
or load installed plugins. Installing a plugin therefore cannot change the
built-in comparison path. Entry points are still trusted in-process Python code:
explicit loading is not a sandbox and can execute arbitrary import or factory
side effects with the current process authority.

## Current boundary

P3-A catalogs declarations only. There is no public registration method, global
third-party registry, `PluginHost.compare()`, capability invocation, plugin CLI
option, renderer hook, schema-v2 provider record, v1-to-v2 upgrader, or published
compatibility receipt. The private Phase 1/2 request, registry, execution-limit,
source-snapshot, and stage-runner types remain private and are never passed to a
plugin.
