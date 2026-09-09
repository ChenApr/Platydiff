# Plugin SDK and explicit discovery

[Chinese documentation](plugin-sdk_zh.md)

Phase 3 gates P3-A and P3-B implement declaration, discovery, explicitly
selected detector/comparator execution, and provider provenance from
[RFC 0005](rfcs/0005-third-party-plugin-discovery-sdk-and-compatibility.md).
Renderer execution, CLI plugin flags, and published compatibility receipts
remain gated by P3-C.

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
tuples, and every manifest string that can enter a catalog or compatibility
profile is bounded, control-free, and path-free. Capability or backend IDs must
use the plugin ID prefix. Dependency, license, Python-version, platform, and
native/external component fields are inventory declarations; the host does not
resolve dependencies or make legal or platform-support claims from them.

Distribution names follow the
[PyPA name and normalization specification](https://packaging.python.org/en/latest/specifications/name-normalization/):
they start and end with an ASCII letter or digit, may contain runs of `.`, `_`,
and `-` internally, and normalize each such run to one lowercase `-` for
identity comparisons. The original path-free spelling remains available for
display and deterministic final tie-breaking.

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
minor `0` or `1` and required host features, and returns an immutable
`PluginCatalogV1`. Minor-0 declaration-only manifests remain loadable; executable
handles require negotiated minor 1 and `host.execution.v1`.
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

## Execute through an immutable host

SDK API `1.1` adds optional typed detector and comparator handles associated by
capability ID with the unchanged declaration objects. `PluginHost.discover()`
freezes one allowlisted catalog snapshot. `PluginHost.compare()` uses built-ins
unless a third-party capability ID is explicitly pinned with `detector_id=` or
`comparator_id=`; enablement alone never changes selection. Automatic comparison
also accepts an exact `text` or `binary` built-in comparator pin and restricts
detection to that modality instead of falling back to another comparator.

The host supplies bounded source services, owns every lifecycle transition, and
invokes a fresh comparator run exactly once in `decode`, `normalize`, `align`,
`compare`, `aggregate` order. Plugins return `PluginComparisonV1` facts rather
than outcomes. Known plugin failures are mapped at the observed stage; process
control and programming exceptions continue to propagate from the Python API.
Executable handle and run shapes are validated before invocation. The host
tracks live run identity without retaining completed runs, records selection
before detector execution, and rechecks mutable path snapshots after validated
aggregation before constructing a completed outcome.

Comparator run objects must support Python weak references. This SDK-v1.1 run
requirement lets a long-lived host reject reuse of the same live run without
retaining every completed run. A structurally valid run that cannot be weakly
referenced is rejected safely during resolution before any lifecycle method is
called.

Every host comparison returns schema v2, including built-in selections. Schema
v2 records the enabled/loaded provider snapshot, versioned attempts, and selected
provider provenance. The existing three-argument `compare()` and CLI remain
schema v1. Readers accept both versions, and `upgrade_outcome_v1_to_v2()` adds an
empty host context without changing v1 result meaning. Schema-v1 models and
encoders reject schema-v2 nested values. Schema-v2 construction and reading
cross-check provider-backed attempts against the loaded host snapshot and the
selected comparator/detector provenance.

There is still no public mutable registration method, process-global third-party
catalog, renderer hook, plugin CLI option, or published compatibility receipt.
Private requests, snapshots, descriptors, and stage runners are never passed to
a plugin.
