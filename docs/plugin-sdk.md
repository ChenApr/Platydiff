# Plugin SDK and explicit discovery

[Chinese documentation](plugin-sdk_zh.md)

Phase 3 gates P3-A, P3-B, and P3-C implement declaration, discovery, explicitly
selected detector/comparator execution, bounded renderer execution, CLI opt-in,
provider provenance, and compatibility receipts from
[RFC 0005](rfcs/0005-third-party-plugin-discovery-sdk-and-compatibility.md).

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
tracebacks, and filesystem paths are never copied into issues. Ordinary
descriptor/property failures while validating executable handle shape quarantine
only that plugin as `plugin_manifest_invalid`; process-control exceptions and
`MemoryError` continue to propagate.

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

An availability result's backend ID/version pair must exactly match the pair in
its capability declaration, including `None`/`None`; SDK v1.1 does not accept an
undeclared runtime backend. Known availability failures and invalid return
values become structured failures at the detecting or resolving boundary with
one auditable failed attempt. Plugin facts cannot claim the host-reserved
source-byte resource names; conflicts fail within aggregation before outcome
construction.

An exact automatic comparator pin is validated before content detection. A
missing capability, missing executor, wrong capability kind, or unsupported
modality produces `capability_unavailable` with the specific safe reason on the
single pinned attempt; it never falls back or masquerades as a detection
no-match. During aggregation, the host independently reconstructs returned
facts and enforces the resolved text/binary contract. Current specs reject
partial or degraded results, require strict `equal`/`pass` and
`different`/`fail` mapping, reject text/binary built-in change-kind crossover,
and enforce `max_change_items` plus canonical UTF-8 schema payload bytes.
Plugins must truncate within the declared `ChangeSet` contract themselves; the
host rejects excess facts rather than silently changing them. A truncated
plugin result must name `change_items` or `change_payload_bytes` and copy the
corresponding effective spec limit exactly.

Comparator run objects must support Python weak references. This SDK-v1.1 run
requirement lets a long-lived host reject reuse of the same live run without
retaining every completed run. A structurally valid run that cannot be weakly
referenced is rejected safely during resolution before any lifecycle method is
called.

Every host comparison returns schema v2, including built-in selections. Schema
v2 records the enabled/loaded provider snapshot, versioned attempts, and selected
provider provenance. The existing three-argument `compare()` and a CLI command
without plugin/capability flags remain schema v1. A CLI command that enables or
pins a plugin capability uses the host and schema v2. If an unexpected CLI
failure occurs after discovery, the failure outcome preserves the exact loaded
provider snapshot; a discovery failure records the enabled IDs with no loaded
providers. Readers accept both
versions, and `upgrade_outcome_v1_to_v2()` adds an empty host context without
changing v1 result meaning. Schema-v1 models and
encoders reject schema-v2 nested values. Schema-v2 construction and reading
cross-check provider-backed attempts against the loaded host snapshot and the
selected comparator/detector provenance, require selected comparator versions
to match result provenance, and apply SDK-grade distribution/version identity
validation. The built-in terminal and JSON renderers accept both outcome schema
versions without recomputing result semantics.

## Author a bounded renderer

An SDK-v1.1 renderer handle has one declared capability ID, a deterministic
tuple of media types, an availability probe, and a `render()` method. Associate
the handle with a matching `CapabilityDeclarationV1` through the manifest's
`capability_handles` tuple:

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

The renderer receives a validated copy of the outcome, presentation options,
and a host-owned sink only. It receives no source, path, registry, artifact
root, or comparison callback. Use either `write_text()` or `write_bytes()` for
one invocation, never both. The sink enforces the exact UTF-8 byte budget and
declared media type. A `text/*` media type always uses strict UTF-8 text mode,
including bytes supplied through `write_bytes()`; invalid UTF-8 fails rendering,
and valid bytes remain subject to the CLI terminal-safety check. Renderers must escape hostile controls before producing
terminal text; the CLI rejects BOM, bidi controls, and C0/C1 controls other than
newline before writing plugin text to stdout. Renderers must not recompute
relation, verdict, metrics, completeness, or any other comparison fact. SDK v1
does not provide arbitrary file writes, HTML policy, or UI behavior.

Python callers select a renderer only after comparison:

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

`RenderedOutputV1` records exact renderer/provider/backend identity, media type,
bounded bytes, and whether the output is UTF-8 text. Its public constructor
validates namespaces, identity strings, media type, bytes/boolean types, backend
pairing, provider type, and text UTF-8 consistency. A missing, unavailable,
invalid, failing, or over-limit renderer raises a typed renderer error containing
the unchanged outcome. There is no implicit fallback.

## Select plugins and capabilities from the CLI

`--plugin` is repeatable and is an exact allowlist. It enables loading only:

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

`--detector` is valid only for automatic comparison. Capability IDs are exact;
absence or unavailability never chooses a substitute. Duplicate/invalid plugin
IDs, invalid media types and bounds, or renderer-only options without
`--renderer` are usage errors (exit `2`). Comparison unavailability/failure and
renderer failure use exit `3`; renderer failures emit only
`platydiff: rendering failed safely` on stderr and no fallback output.
Environment variables, configuration files, installation, upgrade, download,
and dependency resolution remain out of scope.

## Run the compatibility suite and create a receipt

The source distribution includes `tests/plugin_compatibility`. Run it in an
isolated Python 3.12+ environment containing the exact plugin distribution and
backend versions under test:

```bash
python -m pytest tests/plugin_compatibility
```

The profile covers manifest/API negotiation, explicit discovery, detector and
comparator lifecycles, renderer authority and bounds, terminal-control safety,
dependency/license/platform inventory, deterministic ordering, redaction, and
the discovery-to-CLI failure-isolation matrix. Receipt helpers in
`tests/plugin_compatibility/profiles.py` require one
`CompatibilityProfileResultV1` per actually executed profile. Each result
contains a pass/fail value and a non-empty normalized evidence summary. Canonical
JSON records those results together with the exact suite and host versions,
plugin/distribution identity, negotiated SDK and outcome schema versions, and
backend/platform inventory. The SHA-256 digest covers the normalized per-profile
results. Evidence is recursively snapshotted at result construction and
revalidated when the receipt is emitted; strings containing `/` or `\` are
rejected so embedded local paths cannot enter a receipt. Every nested evidence
key must also be a bounded lowercase ASCII identifier. Overall `conforms` and the permitted
`conforms to Platydiff plugin profile X under suite version Y.` claims appear
only when every included profile passed; a failed or mixed receipt contains no
conformance claim.

A receipt is self-attestation, not certification, endorsement, security review,
or permission to redistribute. Plugin code is trusted in-process Python: least
authority APIs reduce accidental misuse but provide no sandbox. Plugin authors
own dependency pinning, hashes, license texts, NOTICE/SBOM obligations, export
controls, patent review, and redistribution permission. Platydiff never installs
or fetches a plugin, and disabled plugins are never imported for richer
inventory.

There is no public mutable registration method or process-global third-party
catalog. Private requests, snapshots, descriptors, and stage runners are never
passed to a plugin. New modalities, configuration files, arbitrary artifacts,
HTML, TUI, and desktop review remain planned and require their own gates.
