# RFC 0005: Third-Party Plugin Discovery, SDK, and Compatibility

[Chinese documentation](0005-third-party-plugin-discovery-sdk-and-compatibility_zh.md)

- Status: Accepted
- Date: 2026-09-09
- Accepted: 2026-09-09
- Owners: Platydiff maintainers
- Implementation owner: Platydiff maintainers for P3-A; P3-B/P3-C unassigned

## Summary and authorization boundary

This RFC defines the accepted Phase 3 contract: explicit discovery of installed
Python plugins, a versioned plugin SDK, deterministic capability selection, and
a compatibility suite. It is based on the implemented Phase 1 text and Phase 2
automatic/binary paths rather than the earlier single-class plugin sketch.

Acceptance approves P1-P8 as normative design decisions. It is not an
implementation authorization: no entry-point group, SDK symbol, CLI option,
compatibility badge, or third-party execution behavior is implemented merely
because this RFC is `Accepted`. Implementation requires a separately dispatched
session on a new branch from updated `main`.

Implementation note: the separately authorized P3-A gate now provides SDK-v1
declarations and explicit discovery/catalog negotiation without capability
execution. P3-B and P3-C remain unimplemented and separately gated, so this RFC
remains `Accepted` rather than `Implemented`.

Phase 3 does not authorize new modalities or the UI work proposed by
[RFC 0004](0004-human-review-ui-and-renderer-boundary.md). Its first SDK is
deliberately exercised only by the existing `text` and `binary` contracts.

## Evidence and lessons from Phases 1 and 2

The current implementation provides the following evidence. These observations
are constraints for the public protocol, not complaints about the private
implementation.

| Evidence in current code and tests | Phase 3 lesson |
| --- | --- |
| Explicit text uses the small private `_registry.py`; auto/binary uses a separate private `CapabilityCatalog`. | Do not publish either implementation. Define one immutable public catalog and adapt built-ins behind it only after compatibility tests exist. |
| `CapabilityRequest` and `ExecutionLimits` are private, normalized values derived from exactly one public spec. | Preserve the public-intent/private-execution split. Plugins receive an SDK request view, not the internal request object or a second source of limits. |
| `CapabilityRecord.executor` is not the execution boundary for the snapshot path; the pipeline imports concrete comparators after resolution. | Resolution and invocation must be joined by a typed, tested capability handle before third-party code is allowed. |
| `SourceSnapshot` owns bounded replay, one opened path descriptor, mutation checks, and stage-aware failures. | The host must retain snapshot ownership. Plugins receive a narrower read-only source service and never the private snapshot type or an unrestricted path. |
| Explicit text intentionally retains an eager compatibility path while auto/binary use replayable snapshots. | Publishing the current comparator signatures would freeze an accidental split. The SDK needs a host-driven lifecycle that can adapt both paths. |
| Detection is deterministic but its schema is closed to `text`/`binary`, one top-level detector record, and one candidate per modality per source. | SDK v1 can only select one detector provider for the existing modalities. Multi-detector fusion and new modality identifiers require a later schema callback. |
| Registration-order independence, duplicate rejection, stable rejection reasons, explicit bypass, and late-invalid no-fallback behavior are already tested. | Plugin discovery must preserve these properties and must not add filesystem-order, import-order, or wall-clock tie breaking. |
| `ExtensionChange` safely preserves a namespaced kind and JSON-safe payload, while `CompareSpec` and built-in detection/change unions remain closed. | Third-party comparators may emit extension changes for existing specs. A plugin cannot introduce a new public modality or spec merely by installation. |
| `CapabilityAttempt` records capability/backend IDs but not distribution identity or version; comparison provenance lacks an explicit provider/backend record. | Reproducible plugin execution needs an approved additive provenance extension or a new outcome schema before implementation. |
| The built-in renderers consume `CompareOutcome` and do not read original sources. | Renderer plugins must receive only a validated outcome and a bounded host sink. They are downstream of comparison truth and separate from UI-U1. |

The Phase 2 contract tests for ordering, duplicate rejection, rejection reasons,
snapshot replay, mutation, explicit override, late decoding failure, and stable
wire behavior become regression inputs to the Phase 3 compatibility suite.

## Goals and non-goals

Phase 3 goals are:

- no plugin import or execution at `import platydiff` time;
- explicit, allowlisted discovery through Python distribution entry points;
- one versioned manifest that can declare detector, comparator, and renderer
  capabilities;
- deterministic discovery, negotiation, resolution, attempts, and provenance;
- host-owned sources, lifecycle, budgets, outcome construction, and validation;
- isolated failure reporting so an unrelated broken plugin does not break a
  built-in comparison;
- a self-testable compatibility suite with machine-readable receipts;
- dependency, license, platform, and supply-chain inventory for every enabled
  provider.

Phase 3 does not include:

- automatic installation, upgrade, download, or dependency resolution;
- implicit enablement of every installed plugin;
- a mutable global registry or import-time registration decorators;
- new spec kinds, new modalities, multi-detector fusion, or custom configuration
  languages;
- a cross-process or network plugin transport;
- a claim that in-process Python code is sandboxed;
- HTML, TUI, desktop, or local-web UI implementation;
- plugin-generated patches, source mutation, directory traversal, URL sources,
  or unrestricted artifact publication;
- official certification of third-party quality or security.

## Terms and trust model

A **distribution** is an installed Python distribution visible through
`importlib.metadata`. A **plugin** is one versioned manifest exposed by one
distribution entry point. A **capability** is a detector, comparator, or
renderer declaration in that manifest. A **backend** is an implementation
dependency used by a capability and may be the Python implementation itself.

Entry points are executable-code references, not passive data. Enumerating
entry-point metadata need not import a plugin; loading the target does. Phase 3
therefore treats every third-party plugin as trusted in-process code explicitly
enabled by the caller. The host validates all returned values, but cannot stop a
malicious plugin from reading process memory, accessing the filesystem, starting
a process, or using the network. Conformance is a contract, not a sandbox.

The default `compare()` function remains built-in-only. Installing a package
must not alter its results, imports, candidate order, timing path, or JSON.

## Distribution metadata and entry-point contract

### One manifest group

SDK major version 1 uses exactly one entry-point group:

```text
platydiff.plugins.v1
```

The entry-point name is the plugin ID. It must be a lowercase reverse-domain
identifier such as `org.example.scidiff`. The target is a no-argument callable
that returns `PluginManifestV1`:

```toml
[project.entry-points."platydiff.plugins.v1"]
"org.example.scidiff" = "example_scidiff.plugin:manifest"
```

Role-specific groups such as `platydiff.detectors` or import-time registration
modules are not inspected. A future incompatible SDK uses a new major group,
for example `platydiff.plugins.v2`; it does not reinterpret v1 targets.

One distribution may expose multiple plugins, but each plugin has exactly one
entry point and one manifest. Distribution name, distribution version, entry
point name, group, and value are captured before load. Names and versions are
untrusted display data and are escaped by renderers.

### Enumeration, enablement, and loading

Discovery is explicit and has three separate steps:

1. **Enumerate:** snapshot matching installed entry-point metadata without
   importing targets.
2. **Select:** validate metadata, apply the caller's exact plugin-ID allowlist,
   quarantine conflicts, and produce a deterministic load plan.
3. **Load:** import and call only selected factories, validate returned manifests,
   negotiate the SDK, and freeze an immutable catalog.

Enumeration happens when `discover_plugins()` is called, never at package import
and never merely because `compare()` is called. The snapshot is fixed for the
lifetime of its `PluginHost`; changes to the Python environment require a new
discovery call and host.

There is no `enable all installed plugins` default. The accepted Python shape is:

```python
policy = PluginDiscoveryPolicy(
    enabled_plugin_ids=("org.example.scidiff",),
)
host = PluginHost.discover(policy)
outcome = host.compare(before, after, spec)
```

The existing three-argument `platydiff.compare(before, after, spec)` remains
unchanged and built-in-only. A host is immutable and safe to inspect after
construction; there is no public `register()` method and no process-global
third-party catalog.

The corresponding accepted CLI design is explicit under decision P8:

```text
platydiff ... --plugin org.example.scidiff \
  --comparator org.example.scidiff.text_exact
```

`--plugin` is repeatable and only enables loading. Selecting a third-party
detector, comparator, or renderer requires its stable capability ID; enablement
alone never lets a plugin silently outrank a built-in. Environment variables and
configuration files remain out of scope.

### Invalid, disabled, duplicate, and conflicting plugins

- A disabled entry point is never imported. It may appear only in an explicit
  inventory command, not in comparison execution provenance.
- Malformed metadata is quarantined before import.
- Import failure, missing factory, factory exception, invalid manifest, or API
  incompatibility quarantines that plugin and does not discard other plugins.
- If one plugin ID is claimed by multiple entry points or distributions, every
  claimant is quarantined with `plugin_id_conflict`; no version, path, or
  enumeration order wins.
- Duplicate capability IDs within or across enabled manifests are quarantined
  as `capability_id_conflict`; built-in IDs and the `core` namespace are reserved.
- The entry-point name must exactly equal `manifest.plugin_id`. A mismatch is
  invalid rather than an alias.
- A caller that explicitly requires a quarantined or absent plugin receives a
  resolving-stage unavailable outcome. An unrelated invalid plugin cannot alter
  a built-in or another selected plugin's outcome.

Metadata and catalog issues are sorted by plugin ID, normalized distribution
name, distribution version, entry-point value, and stable reason code. Python
environment paths and tracebacks are excluded from safe diagnostics.

## Manifest and SDK version negotiation

The normative shape is conceptually:

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

The entry-point group fixes the API major. The host has one API minor and loads
a plugin only when:

```text
minimum_api_minor <= host_api_minor <= maximum_api_minor
```

Minor releases are additive: they may add optional methods, fields, or feature
IDs with defined defaults. Removing or reinterpreting a field, changing lifecycle
order, or weakening validation requires a new major entry-point group. Manifest
schema version is independent of the outcome schema and SDK API version.

Required host features are unique, sorted stable identifiers. Unsupported
required features make the plugin incompatible before capability resolution.
Optional features are used only when both parties declare them. Runtime duck
typing or `hasattr` without a negotiated feature is forbidden.

`plugin_version` and the installed distribution version are recorded separately.
They need not be equal, but a mismatch is visible. The compatibility suite
recommends equality. Version strings are opaque Unicode values for identity and
provenance; Phase 3 does not add a runtime dependency merely to order versions.

Capability IDs and plugin-defined backend IDs use the plugin's reverse-domain
prefix. Plugin-supplied priority can order capabilities from the same plugin but
cannot cross the host's selection tiers or preempt a built-in.

## Public/private boundary and dependency direction

The dependency direction becomes:

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

`core` does not import an installed plugin, concrete comparator, renderer, or
`importlib.metadata`. Discovery and composition live outside `core`. The public
SDK may import stable core models; core must not import the SDK.

The following remain private and are never passed to a plugin:

- `CapabilityRequest`, `ExecutionLimits`, `CapabilityCatalog`, and
  `InternalRegistry`;
- `SourceSnapshot`, raw path descriptors, `StageRunner`, and comparator-local IR;
- internal clocks, mutable diagnostic lists, and renderer implementation details.

The SDK exposes immutable request views, bounded source/probe services,
capability declarations, plugin result payloads, and project-defined plugin
exceptions. Inputs and returned collections are read-only at the boundary.

## Capability responsibilities

### Detector

A detector receives only host-captured source kind, a bounded prefix, whether
the prefix reached EOF, and the effective detection limit. It must not reopen a
path, read beyond the supplied prefix, inspect filenames, use locale or time, or
perform network/subprocess I/O.

SDK v1 detector output is limited to candidates for the existing `text` and
`binary` modalities. The host validates confidence, identifiers, evidence
counts, and ordering, then constructs `DetectionRecord`. A plugin never returns
an outcome or chooses the final comparator.

Exactly one detector provider is used per auto comparison. The built-in detector
is the default; an external detector must be explicitly pinned. Automatic fusion
of multiple detector outputs is deferred because schema v1 cannot attribute a
pair candidate to multiple detector providers without ambiguity.

### Comparator

Resolution returns a typed capability handle, not an untyped `object`. The host
creates one run object per comparison and invokes its methods in the fixed order:

```python
class ComparatorRunV1(Protocol):
    def decode(self) -> None: ...
    def normalize(self) -> None: ...
    def align(self) -> None: ...
    def compare(self) -> None: ...
    def aggregate(self) -> PluginComparisonV1: ...
```

The run encapsulates plugin-local state. The host owns stage transitions, calls
each method at most once, maps known plugin exceptions at the observed stage,
and rejects an out-of-order or reused run. A no-op stage still has a completed
record. The plugin never receives `StageRunner` and cannot append or rewrite
execution history.

`PluginComparisonV1` carries structured comparison facts—relation, verdict,
fidelity, summary, changes, metrics, evaluations, artifact references,
transformations, algorithm identity, deterministic resource use, and safe
diagnostics—but not the outer outcome or provider provenance. The host validates
all RFC 0001 invariants, binds the selected manifest/capability/backend identity,
constructs `ComparisonProvenance`, and only then constructs `DiffResult` and
`CompletedOutcome`.

SDK v1 comparators accept only existing normalized `TextCompareSpec` or
`BinaryCompareSpec` intent. Auto intent is resolved by the host and remains the
recorded public spec. A plugin may return `ExtensionChange` values whose kind is
within its namespace. It may not introduce a new built-in change kind or spec.

The host-provided source service is replayable and bounded, exposes a safe label
and source kind, and accounts every byte. It does not expose an absolute path.
The host retains descriptors, hashing, mutation checks, close behavior, and
resource-limit enforcement. A capability declares which lifecycle stage may
consume source bytes; access during another stage fails visibly.

### Renderer

A renderer receives a validated typed `CompareOutcome`, presentation options,
and a bounded host sink. It receives no sources, snapshots, artifact root, path,
registry, or comparison callback. It may format or organize existing facts but
must not recompute relation, verdict, fidelity, metrics, evaluations, change
completeness, or problem meaning.

The sink enforces an output-byte limit and captures text or bytes plus a declared
media type. A renderer cannot write an arbitrary path in SDK v1. Renderer failure
happens after comparison and therefore never replaces or mutates its outcome;
the Python renderer API raises a renderer error and the CLI retains exit 3 with
safe stderr behavior.

Third-party renderer output is presentation, not a durable schema and not an
`ArtifactRef`. Self-contained HTML, overwrite rules, CSP, and human-review UI
remain exclusively governed by RFC 0004 and require separate authorization.

## Deterministic resolution, availability, and fallback

Discovery enumeration order and registration order never participate in
selection. The host uses these tiers:

1. an exact capability ID explicitly pinned by the caller;
2. a compatible built-in capability;
3. an enabled compatible third-party capability.

Within tier 3, ordering is ascending host policy priority, plugin ID, capability
ID, backend ID, normalized distribution name, and distribution version as an
opaque final identity field. A plugin cannot gain priority from installation
order or a lexically larger version. An exact pin either selects that identity
or returns unavailable; it never silently substitutes another capability.

Availability probing occurs after load but before source comparison. It is
bounded, deterministic, local, and input-independent. The result contains
available/unavailable, backend ID/version, and one stable reason code. Probes may
inspect already imported Python modules and local executable metadata only when
a later accepted capability profile permits it; SDK v1's conforming baseline
does not spawn a process or use the network.

Fallback rules are:

- a non-pinned unavailable candidate may be skipped before execution, with an
  ordered rejected attempt;
- a pinned unavailable candidate ends in `unavailable`;
- once any selected detector or comparator method begins, failure does not fall
  back to another provider;
- exact text/binary intent never degrades to approximate semantics;
- degradation is legal only for a future spec that explicitly permits it, and
  must set `fidelity=degraded`, record an attempt and diagnostic, and preserve
  the policy verdict independently;
- renderer fallback is a caller presentation policy and cannot alter the
  comparison outcome. The CLI does not silently replace an explicitly selected
  renderer.

Retries are disabled in SDK v1. A later retry policy must define deterministic
attempt bounds, idempotence, and provenance before it can be enabled.

## Outcome, provenance, and schema gate

Plugin execution must make the following facts serializable:

- enabled and loaded plugin IDs;
- distribution names and versions;
- manifest and negotiated SDK versions and features;
- capability, comparator, detector, backend, algorithm, and implementation
  identities and versions as applicable;
- every rejected, selected, unavailable, fallback, and failed attempt;
- configured limits and actual deterministic use;
- safe discovery, load, validation, and execution diagnostics.

Renderer identity belongs to a separate rendering result or compatibility
receipt because rendering happens after the comparison outcome exists.

The current schema cannot represent all comparison facts without overloading
`capability_id`, `implementation_version`, or diagnostic prose. It also cannot
attribute fused detection candidates. Approved decision P6 therefore requires
outcome schema v2 with:

- a typed `ProviderIdentity` containing plugin, distribution, manifest, and
  negotiated SDK identity/version without module paths;
- provider and capability/backend versions on capability attempts;
- an optional selected provider on comparison provenance;
- an optional plugin-host record on execution containing the exact enabled and
  loaded provider set and negotiated features;
- a stable `plugin_execution_failure` problem mapping;
- a v1 reader and documented v1-to-v2 migration tests.

The existing `platydiff.compare()` path and existing CLI routes without plugin
selection continue to produce schema v1 byte-for-byte where behavior is
unchanged. `PluginHost.compare()` and every CLI invocation that enables or pins
a plugin produce schema v2, even when final resolution selects a built-in,
because the enabled provider environment is execution input. Built-in-only v2
outcomes omit selected-provider fields but retain their v2 plugin-host record.

Readers and renderers accept both versions. A documented typed v1-to-v2 upgrader
preserves v1 semantics and adds an empty plugin-host context. Schema v2 is never
silently down-converted; a retained v1 encoder rejects v2/plugin execution that
cannot be represented. Existing v1 payloads remain readable and their golden
fixtures remain unchanged.

This does not amend, supersede, or silently override RFC 0003 decision D3. D3's
single pre-release extension occurred in Phase 2 and continues to freeze the
closed unions and meanings of schema v1. Phase 3 introduces the explicit
successor schema v2 instead of adding plugin fields or problem codes to v1.
The implementation must preserve the v1 reader, document migration into v2,
and prove in compatibility tests that v1 data retains its original meaning.

No provider identity may contain an absolute path, module filesystem location,
username, environment variable, traceback, token, or source content. Distribution
and plugin strings are untrusted data even after manifest validation.

## Failure isolation and stable semantics

The catalog records stable reason codes including:

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

Unrelated quarantined plugins produce inventory issues, not comparison
diagnostics. When a required plugin/capability cannot load or resolve, the
comparison uses the existing `capability_unavailable` or `backend_unavailable`
problem and includes only a bounded safe reason in structured details.

Known exceptions raised by a selected plugin are mapped at the method boundary.
Capability absence remains `unavailable`; resource exhaustion, invalid plugin
output, and execution failure are `failed` and never content differences. A new
stable schema-v2 `plugin_execution_failure` problem code is required by P6.
`KeyboardInterrupt`, `SystemExit`, and `MemoryError` propagate
from the Python API. Programming defects are not silently converted by library
code; the CLI retains its outer safe `internal_error` boundary.

In-process Python cannot be forcibly timed out safely. Normal comparison results
must depend on deterministic work/byte/count budgets, not wall-clock deadlines.
A hung or malicious plugin requires external process supervision, which is out
of scope for SDK v1.

## Security and supply-chain boundaries

- Plugins are never installed, upgraded, or fetched by Platydiff.
- The caller supplies an exact allowlist. The host never loads a disabled,
  conflicted, or merely discovered target.
- Factory import and invocation are separate recorded failure boundaries.
- Import-time side effects are forbidden by conformance, although the host cannot
  enforce that rule against malicious in-process code.
- Manifest strings, diagnostics, extension payloads, and renderer output are
  validated and bounded before entering core models or a terminal.
- Plugin code receives least-authority services, but this reduces accidental
  misuse rather than creating a security sandbox.
- Network, subprocess, dynamic native-library loading, archive expansion, and
  writes outside a host sink are prohibited by the SDK v1 conformance profile.
  A plugin that needs them requires a later capability profile and threat-model
  review.
- There is no automatic trust based on package name, publisher, signature,
  download count, compatibility receipt, or entry-point presence.
- Reproducible deployments should pin distribution versions and hashes in their
  environment tooling. Platydiff records observed identities but is not a package
  resolver or signature verifier.

## Dependency, license, platform, and redistribution contract

Every manifest declares a license expression and each capability declares its
runtime dependencies, optional backend, supported Python versions, platforms,
and native/external components. These declarations are inventory, not legal
verification. Before load, inventory can expose only installed distribution
metadata; manifest declarations become available only for explicitly loaded
plugins. Disabled plugins are never imported to enrich inventory.

The compatibility report records:

- plugin and distribution identity/version;
- negotiated SDK and outcome schema versions;
- declared license and dependency inventory;
- tested Python implementation, OS, architecture, and backend versions;
- suite version, test-profile IDs, result, and deterministic receipt digest.

Third-party plugin dependencies never become Platydiff core dependencies. A
plugin distributed separately owns its license texts, NOTICE obligations, SBOM,
export controls, patent review, and redistribution permission. If the Platydiff
project later bundles or redistributes a plugin/backend, the project must perform
its own dependency and license review and update NOTICE/SBOM artifacts before
merge. A compatibility pass does not grant redistribution permission.

The baseline merge gate is Linux/Python 3.12. A plugin may declare narrower
support, but the host must report that restriction as availability rather than
import failure. Cross-platform claims require the plugin's compatibility receipt
for every claimed platform.

## Compatibility suite and claims

The Phase 3 suite is shipped as development/test tooling and runs against a
plugin factory in an isolated test environment. It has profiles for:

- metadata and manifest validation;
- API negotiation and required-feature rejection;
- discovery without import, explicit loading, conflict quarantine, and stable
  ordering;
- detector bounds, candidate validation, determinism, and explicit pinning;
- comparator lifecycle, source access, outcomes, extension changes, budgets,
  failure mapping, and repeated-run determinism;
- renderer semantic pass-through, output bounds, hostile text/control escaping,
  and proof that source access is unavailable;
- dependency/license/platform inventory and safe redaction.

The suite includes synthetic licensed fixtures for equal, different, empty,
corrupt, over-limit, repeated, conflicting, unavailable-backend, invalid-output,
and exception cases. Comparator profiles reuse the applicable text/binary oracle
and schema round-trip tests. The suite runs with randomized discovery ordering
and verifies identical normalized output.

A machine-readable receipt is self-attestation. It includes the exact suite and
host versions and a digest of normalized results. Permitted wording is
"conforms to Platydiff plugin profile X under suite version Y." A plugin must not
claim "Platydiff certified," security-reviewed, endorsed, or compatible with
untested host versions. The project may later define a governed certification
program in a separate RFC.

Compatibility policy is:

- every supported SDK minor remains in CI while that major is supported;
- golden manifests and provider provenance are retained;
- an additive minor feature has a fallback/default and an old-plugin test;
- a breaking SDK change uses a new entry-point major and migration guide;
- outcome-schema migration tests cover plugin-produced changes and provenance;
- deprecation spans at least one documented release line and never silently
  changes capability selection.

## Implementation and merge gates

Acceptance alone does not start any work below. After separate explicit
implementation authorization, use three independently reviewable merge gates;
do not stack them unless the user approves stacked review.

### P3-A: SDK and discovery, no plugin execution

1. `feat(plugin-sdk): add versioned manifests and capability declarations`
2. `feat(plugins): add explicit entry-point discovery and negotiation`
3. `test(plugins): add manifest and discovery compatibility profiles`

Gate: public names and version rules are frozen; importing Platydiff and calling
the existing `compare()` do not enumerate or load plugins; disabled/invalid/
duplicate/conflicting cases and randomized ordering pass; no comparator,
detector, or renderer is invoked.

### P3-B: comparison host and capability execution

1. `refactor(core): add typed capability handles and built-in adapters`
2. `feat(plugins): add host-driven detector and comparator lifecycles`
3. `feat(core): record plugin attempts and provider provenance`
4. `test(plugins): add detector and comparator conformance profiles`

Gate: decision P6 is implemented with migration tests; all Phase 1/2 payloads
and routes remain compatible where specified; host-owned snapshot, stage,
failure, resource, and no-fallback tests pass; existing `compare()` remains
built-in-only.

### P3-C: renderer boundary, CLI opt-in, and documentation

1. `feat(renderers): add bounded third-party renderer protocol`
2. `feat(cli): add explicit plugin and capability selection`
3. `test(plugins): publish compatibility receipts and full isolation matrix`
4. `docs: document plugin authoring, trust, and compatibility`

Gate: no UI-U1 behavior is introduced; renderer failures preserve outcomes;
CLI defaults and exits remain compatible; package contents and license inventory
are inspected; Ruff, strict mypy, full pytest, build, and default-branch CI pass.

Each merge gate requires independent contract review mapping this RFC to code
and tests, actual verification commands, dependency/license impact, and a scan
showing no source, fixture, secret, local path, or generated artifact leakage.

## Approved decisions

The user approved P1-P8 on 2026-09-09. They are normative parts of this RFC but
do not assign an implementation owner or authorize development.

| ID | Decision | Approved contract | Consequence |
| --- | --- | --- | --- |
| P1 | Default enablement | Keep `compare()` built-in-only; require an exact plugin-ID allowlist | Installed packages cannot silently change behavior |
| P2 | Entry-point layout | Use only `platydiff.plugins.v1` with one manifest factory | Atomic identity and one negotiation boundary; role-specific groups remain reserved |
| P3 | First SDK modality scope | Limit detector/comparator plugins to existing text/binary specs and one pinned detector per run | Prevents plugin installation from bypassing new-modality and detector-fusion RFC gates |
| P4 | Execution isolation | Start with explicitly trusted in-process plugins and state that no sandbox exists | Small implementable SDK; untrusted/out-of-process execution needs a successor RFC |
| P5 | Outcome ownership | Let plugins return validated comparison payloads; host constructs provenance, `DiffResult`, and outcome | Prevents plugins from rewriting execution history or provider identity |
| P6 | Outcome schema evolution | Use schema v2 with v1 reading and migration support; keep RFC 0003 D3 intact and schema v1 frozen | Provider identity and plugin failures become typed and reproducible without changing v1 meanings |
| P7 | Fallback and retry | Permit pre-execution skipping of unpinned unavailable candidates; forbid post-start fallback and all v1 retries | Preserves semantics and makes attempts auditable |
| P8 | Renderer and CLI scope | Add bounded renderer protocol and explicit capability flags, but no arbitrary file writes or HTML/UI behavior | Keeps RFC 0004 independent and prevents hidden plugin activation |

P6 selects a schema successor rather than reopening schema v1. Any future attempt
to add the Phase 3 provider fields to v1 would contradict this accepted contract
and require explicit successor RFC review of both RFC 0003 D3 and this decision.

## Rejected alternatives

### Export the current internal registries and source snapshots

Rejected because their split signatures, mutable registration, direct concrete
imports, and stage ownership are implementation details already shown to differ
between text and binary.

### Load every installed plugin automatically

Rejected because installation would change comparison behavior, imports could
execute unrelated code, and environment enumeration would become hidden input.

### Let plugin priority override built-ins

Rejected because a package could silently capture existing text or binary
requests. Third-party selection is explicit or only fills an unavailable tier.

### Treat entry-point metadata or a compatibility receipt as a sandbox

Rejected because loading a Python entry point executes code with the current
process authority. Validation and self-tests do not establish trust.

### Allow plugins to return complete outcomes

Rejected because they could fabricate stage traces, provider provenance, or
unavailable semantics. The host owns execution and outcome construction.

### Publish a generic new-modality spec in Phase 3

Rejected because each modality must first define comparison intent, change,
metric, artifact, failure, and equivalence semantics through its own callback
RFC. A plugin transport must not bypass those gates.

## Consequences

The accepted SDK contract is intentionally narrower than arbitrary Python extension
hooks. It provides deterministic, auditable third-party implementations for
contracts that Platydiff already understands, while keeping installation,
trust, new modalities, and UI on separate decision paths. The extra manifest,
host, provenance, and conformance machinery is the cost of preventing a plugin
from becoming an invisible second pipeline.
