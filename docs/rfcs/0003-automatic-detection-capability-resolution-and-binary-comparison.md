# RFC 0003: Automatic Detection, Capability Resolution, and Binary Comparison

[Chinese documentation](0003-automatic-detection-capability-resolution-and-binary-comparison_zh.md)

- Status: Proposed
- Date: 2026-09-07
- Owners: Platydiff maintainers
- Implementation owner: unassigned pending acceptance

## Summary

This RFC proposes Phase 2: bounded automatic modality detection, deterministic
capability resolution, and strict binary comparison. It extends the Phase 1
pipeline without publishing a third-party plugin protocol. Nothing in this RFC
authorizes implementation while its status is `Proposed`.

The proposal preserves the [RFC 0001](0001-comparison-outcome-and-diff-result.md)
separation between execution outcomes and completed differences and the
[RFC 0002](0002-development-phases-and-text-slice.md) callback gate for later
phases. Explicit text behavior remains compatible with Phase 1.

## Scope

Phase 2 would add:

- an explicit `AutoCompareSpec` and an explicit `BinaryCompareSpec`;
- bounded inspection of path, byte, and text sources;
- deterministic selection between built-in text and binary capabilities;
- exact, collision-safe byte comparison with bounded streaming;
- stable detection and resolution provenance;
- `platydiff binary` and an auto-detection CLI route;
- compatibility tests for every existing Phase 1 route and schema payload.

Phase 2 would not add:

- third-party entry-point discovery, a plugin SDK, or a public registry;
- encoding detection beyond the existing explicit UTF-8 choices;
- archive expansion, directory traversal, stdin, URLs, pipes, devices, sockets,
  or recursive comparison;
- approximate binary similarity, block matching, patch generation, or embedded
  byte payloads;
- HTML, TUI, desktop, or local-web rendering;
- JSON/YAML, table, array, image, source-code, PDF, audio, or video semantics.

## Public intent and internal requests

`CompareSpec` remains the public description of comparison intent:

```python
CompareSpec = AutoCompareSpec | TextCompareSpec | BinaryCompareSpec

compare(before: Source, after: Source, spec: CompareSpec) -> CompareOutcome
```

An explicit `TextCompareSpec` or `BinaryCompareSpec` bypasses `detecting`. Only
`AutoCompareSpec` enables it. A Python source type, filename suffix, or MIME
label never silently changes an explicit specification.

`CapabilityRequest` is a private core/resolver value in Phase 2. It is not
exported from `platydiff`, is not accepted by `compare`, and has no public JSON
schema. This lets two built-in capabilities validate the boundary before Phase
3 considers a plugin protocol. Its deterministic internal form is:

```text
request_version: 1
operation: compare
requested_modality: auto | text | binary
resolved_modality: text | binary | null
source_kinds: ordered(before, after)
semantic_class: exact
required_features: ordered stable identifiers
intent: normalized CompareSpec without resource limits
limits: normalized ExecutionLimits
```

The invariant is that `resolved_modality` is null before detection/resolution
and exact afterward. `semantic_class="exact"` forbids an approximate fallback.
The request version is an internal implementation version, not
`schema_version`. Debug representations are not persisted or accepted as
input. The selected intent and limits are instead recorded through existing
comparison provenance and resource-usage records.

Comparison intent and execution limits are distinct at the resolver boundary.
Phase 2 should introduce an internal `ExecutionLimits` normalization model and
translate the existing schema-v1 `TextCompareSpec.limits` into it. The public
Phase 1 field remains unchanged. Whether a later schema moves limits out of
every spec is explicitly deferred; Phase 2 must not create two conflicting
public sources of limits.

## Detection contract

### Bounded evidence collection

Detection reads at most `max_detection_bytes` from the start of each source.
It uses the same opened source snapshot that comparison will consume or a
replayable bounded prefix owned by that snapshot. Detection must not open a
path by name and then compare a separately resolved path. Text sources provide
an explicit text signal; byte and path sources require content evidence.

The Phase 2 built-in detector may use only deterministic evidence:

- source kind;
- a bounded byte prefix and its length;
- strict UTF-8 validity in the inspected prefix;
- NUL and control-character evidence;
- stable built-in magic signatures, if any are explicitly enumerated in the
  implementation documentation.

Filename suffixes and operating-system MIME databases may be recorded as weak
diagnostic evidence but may not determine the selected modality in Phase 2.
Locale, wall-clock time, filesystem enumeration order, and network services are
forbidden inputs.

### Detection candidates and confidence

Each source produces zero or more candidate records:

```text
modality_id: text | binary
confidence: integer 0..1000
detector_id: stable identifier
detector_version: implementation version
priority: non-negative integer
evidence_codes: ordered stable identifiers
```

`confidence` is a deterministic evidence score, not a probability or a promise
about correctness. Scores are comparable only for the same detector/version
and policy. The execution record must expose the detector/version, effective
thresholds, source candidates, pair candidates, and final disposition in
diagnostic details or capability attempts. It must not expose inspected input
bytes.

A pair candidate exists only when the modality is eligible for both inputs and
a built-in capability can satisfy the request. Its score is the minimum of the
two source scores. Duplicate candidates with the same modality are folded into
one record: retain the highest score, then the lowest detector priority, and
retain all evidence codes in stable sorted order.

### Ranking and ambiguity

Eligible pair candidates are ranked by this total order:

1. descending pair confidence;
2. ascending detector priority;
3. ascending capability priority;
4. ascending modality identifier;
5. ascending capability identifier and backend identifier.

The last identifiers make output deterministic; they do not silently resolve
semantic ambiguity. A candidate is selected only when it reaches the configured
minimum confidence and leads the runner-up by the configured ambiguity margin.
Otherwise detection ends as `unavailable`:

- `detection_no_match` when no eligible candidate reaches the minimum;
- `detection_ambiguous` when multiple eligible candidates are too close.

An exact explicit type is the Phase 2 user override and bypasses confidence,
threshold, and tie handling. Phase 2 does not add filename overrides or a
"best effort" switch. If auto selection is unavailable, the message must tell
the user to choose `text` or `binary` explicitly.

The numeric minimum and ambiguity margin are acceptance decisions listed in the
decision ledger. They must be constants in the normalized auto spec and
provenance, not hidden tuning parameters.

## Capability resolution

The internal registry contains only built-in records in Phase 2. A record has a
stable capability ID, modality, semantic class, implementation version,
backend ID and version, priority, supported source kinds, required features,
and an availability probe that performs no input comparison.

Registration order is irrelevant. Resolution deduplicates by capability ID and
backend ID, rejects duplicate registrations, sorts by the ranking fields above,
and records every considered entry as selected or rejected. Stable rejection
reasons include:

- `modality_mismatch`;
- `semantic_class_mismatch`;
- `source_kind_unsupported`;
- `required_feature_missing`;
- `backend_missing`;
- `backend_version_unsupported`;
- `lower_priority`.

The built-in standard-library text and binary comparators require no optional
backend. The model still distinguishes a missing optional backend so the
execution contract can be tested before Phase 3.

No compatible capability, or a missing required backend, produces
`unavailable` during `resolving`; input I/O, invalid specification, resource
exhaustion, a source that changes while read, comparator failures, and program
defects produce `failed` at their observed boundary. A known capability
absence must never be converted to `internal_error`, and a comparator failure
must never be reported as a content difference.

For auto mode the stage prefix is:

```text
validating -> sourcing -> detecting -> resolving -> ...
```

For explicit text or binary mode it remains:

```text
validating -> sourcing -> resolving -> ...
```

The selected capability and backend appear once in `ExecutionRecord.attempts`.
Rejections precede the selection in deterministic rank order. Detection
unavailability terminates at `detecting`; capability unavailability terminates
at `resolving`.

## Exact binary comparison

### Semantics and algorithm

The proposed built-in comparator has:

```text
comparator_id: binary
backend_id: stdlib
algorithm_id: binary.exact.stream.v1
relation: equal only when byte length and every byte are equal
policy: equal -> pass; different -> fail
fidelity: full
```

It reads both inputs in bounded chunks and compares the actual bytes. SHA-256
is computed for provenance and caching evidence, but digest equality alone may
not establish `relation="equal"`; actual byte equality and matching EOF are
required. This makes the result collision-safe with respect to the declared
relation.

An empty input is legal. A `TextSource` is compared as its strict UTF-8 byte
encoding when binary is explicit; this transformation must be recorded.
`BytesSource` is already an immutable snapshot. Path inputs use one opened file
descriptor per source for detection, comparison, and hashing.

### Source safety and reproducibility

Before reading a path, the implementation opens it with close-on-exec and a
nonblocking safeguard, then uses `fstat` on the descriptor. The final target
must be a regular file. Directories, FIFOs, devices, sockets, and other special
files fail without blocking. Symlinks are allowed only when their opened target
is regular; provenance records that a path source was used, not an absolute or
resolved local path.

Initial and final descriptor metadata include platform-available device,
inode/file ID, byte length, and nanosecond modification time. A detected change
during the observed read window returns `failed/source_changed` and no
`DiffResult`. The streamed byte count is checked independently of advertised
size. This detects ordinary mutations but cannot prove that a hostile writer
did not change and restore all observable metadata; the input SHA-256 remains
the identity of the bytes actually read.

`KeyboardInterrupt`, `SystemExit`, and `MemoryError` continue to propagate from
the Python API. Schema v1 has no cancelled outcome. The CLI may suppress an
unknown traceback at its existing boundary but must not turn an interrupt into
a successful outcome.

### Binary changes, metrics, and limits

The proposed built-in `BinarySpan` has `kind="binary_span"` and contains:

```text
before_offset: zero-based byte offset
before_length: non-negative byte length
after_offset: zero-based byte offset
after_length: non-negative byte length
```

It never embeds byte content. Within the overlapping length, maximal contiguous
runs of unequal bytes become spans with equal before/after lengths. A trailing
length difference becomes one final insertion or deletion span. Spans are in
source order, non-overlapping, and are observational mismatch ranges, not a
minimal insertion/deletion script or patch.

The complete algorithm counts all spans and mismatching bytes while retaining
only the bounded source-order prefix. Therefore detail limits may produce a
`truncated` `ChangeSet`; they do not change relation, verdict, or fidelity.
Input or work-budget exhaustion produces `failed`, never `partial` and never an
assumed difference.

At minimum the result records finite metrics for `different_bytes`,
`before_bytes`, and `after_bytes`, all with unit `bytes`; it records matching
summary counts and both input hashes. `different_bytes` is unequal aligned
bytes plus the absolute length difference. Resource provenance records byte
limits, bytes read, chunk size, returned change count, and retained canonical
change payload bytes.

## CLI and Python compatibility

The existing calls remain unchanged:

```text
platydiff compare --type text BEFORE AFTER
platydiff text BEFORE AFTER
```

Phase 2 proposes:

```text
platydiff compare --type binary BEFORE AFTER
platydiff binary BEFORE AFTER
platydiff compare --type auto BEFORE AFTER
```

Whether omitted `--type` means auto or remains a usage error is unresolved.
Until that decision is accepted, documentation and tests must use the explicit
`--type auto` form. Text-only flags must be rejected for binary or auto routes
unless their meaning is defined by the selected spec. Existing shell exits stay
`0/1/2/3`; detection or resolution unavailability maps to `3`, and parser
misuse maps to `2` without an outcome.

JSON output remains one outcome envelope on stdout. Human messages and terminal
rendering must escape untrusted labels and control characters and must not
include absolute paths, inspected byte content, or tracebacks. Existing path,
artifact-URI, stdout/stderr, and renderer-failure rules remain in force.

## Schema and compatibility strategy

Phase 2 must not silently claim forward compatibility that schema v1 does not
provide. The current reader rejects unknown built-in spec and change kinds, so
adding `AutoCompareSpec`, `BinaryCompareSpec`, or `binary_span` is not readable
by an older Phase 1 reader even though the source change is additive.

Before implementation, maintainers must choose one ledger option:

1. extend unreleased schema v1 before the first public release, preserve every
   Phase 1 payload byte-for-byte where behavior is unchanged, and document that
   pre-release readers had no forward-compatibility guarantee; or
2. introduce schema v2 and define explicit v1/v2 producer and reader behavior.

The recommendation is option 1 because version `0.1.0.dev0` remains unreleased,
but it is a release-policy decision, not an implementation assumption. After
the first public release, a new closed-union kind requires a schema successor.

Within the chosen schema, changes must be additive: existing required fields,
enum meanings, outcome semantics, problem mappings, exit codes, and Phase 1
golden JSON remain unchanged. Optional fields require default-on-read behavior.
Unknown extension changes remain preservable; unknown non-namespaced built-in
kinds remain rejected. New problem codes proposed by this RFC are:

| Code | Status | Outcome | Stage |
| --- | ---: | --- | --- |
| `detection_no_match` | 415 | unavailable | detecting |
| `detection_ambiguous` | 409 | unavailable | detecting |
| `source_type_unsupported` | 415 | failed | sourcing |
| `source_changed` | 409 | failed | sourcing |

`capability_unavailable` and `backend_unavailable` retain their RFC 0001
mappings. Every added code, kind, spec, and public export requires constructor,
round-trip, invalid-state, golden JSON, and CLI compatibility tests plus a
migration note. The top-level package should export only the accepted new
specs, their public enums/limits, and `BinarySpan`; registry and request types
remain private.

## Security and platform requirements

- detection and comparison are local, deterministic, bounded, and network-free;
- no decompression, archive traversal, executable probing, or subprocess is
  permitted in Phase 2;
- prefix buffers, change details, diagnostic details, and renderers are bounded;
- input bytes never enter diagnostics, logs, filenames, HTML, or terminal output;
- path opening and descriptor validation are tested for symlink swaps and
  special files on supported platforms;
- platform metadata unavailable on one OS is omitted or marked unavailable,
  never fabricated;
- Windows and POSIX path behavior must have explicit tests even though baseline
  CI may remain Linux/Python 3.12 until the platform matrix is accepted;
- malicious byte sequences and terminal controls cannot alter JSON validity or
  terminal control flow.

## Acceptance matrix

| Area | Required evidence before `Implemented` |
| --- | --- |
| Detection | empty, valid UTF-8, invalid UTF-8, NUL/control-heavy, prefix-boundary, ties, below-threshold, explicit override, deterministic repeated runs |
| Resolution | registration-order independence, duplicate rejection, every reject reason, selected/rejected attempts, missing backend, no capability |
| Binary correctness | equal, different, empty, length mismatch, chunk-boundary mismatch, reconstruction-free span invariants, hash recorded but not trusted for equality |
| Resources | exact input boundary, detection prefix boundary, change-item and payload truncation, bounded peak memory, no partial result on input/work exhaustion |
| Sources | bytes, text encoding, regular path, missing/denied path, directory, FIFO/device/socket where available, symlink target, mutation during read |
| Contracts | Phase 1 golden payloads, new round trips, unknown fields/kinds, stable codes, public exports, schema decision and migration note |
| CLI | old routes unchanged, binary and auto routes, all exits, stdout/stderr, flag separation, label/path/control escaping, renderer failure |
| Provenance | detector/comparator/backend versions, thresholds, ranking, attempts, transformations, hashes, limits and actual usage |
| Packaging | zero new runtime dependencies, Ruff, strict mypy, full pytest, build, wheel/sdist inspection, green default-branch CI |

## Proposed implementation commits and gates

Implementation remains unassigned until this RFC is accepted. A future code
session should use focused commits in this order:

1. `refactor(core): add bounded replayable source snapshots`
   - Gate: Phase 1 behavior and golden JSON unchanged; regular-file and mutation
     tests prove a single descriptor/snapshot lifecycle.
2. `feat(core): add detection and capability request contracts`
   - Gate: schema decision recorded; candidate ranking, ambiguity, request
     normalization, and registry-order tests pass without a binary comparator.
3. `feat(binary): add exact streaming comparison`
   - Gate: direct byte equality, spans, metrics, hashes, truncation, resource
     boundaries, mutation, and representative memory tests pass.
4. `feat(core): integrate automatic detection and resolution`
   - Gate: execution stages, outcomes, attempts, rejection reasons, provenance,
     explicit bypass, and end-to-end determinism pass.
5. `feat(cli): add binary and automatic comparison routes`
   - Gate: accepted auto-entry decision implemented; existing CLI snapshots and
     exits remain compatible; new routes cover safe output and all failures.
6. `docs: document automatic and binary comparison`
   - Gate: English/Chinese behavior docs, migration notes, examples, limits,
     algorithm provenance, and planned-capability labels match verified code.

The implementation PR may merge only after an independent contract review
maps every accepted RFC clause to code/tests, all required commands pass, CI is
green, dependency/license impact is recorded, and no Phase 3 plugin API or UI
work is included.

## Decision ledger

These decisions require explicit human acceptance. Defaults below are
recommendations, not authorization:

| ID | Decision | Recommendation | Blocks |
| --- | --- | --- | --- |
| D1 | Auto CLI entry | Require `--type auto` in Phase 2; keep omitted `--type` as exit-2 usage error | CLI contract |
| D2 | Confidence policy | Integer 0..1000, minimum 800, ambiguity margin 100; fixture-calibrate before acceptance | Detector constants and snapshots |
| D3 | Schema evolution | Extend unreleased schema v1 once before first release; freeze closed unions at release | Public models and serialization |
| D4 | Binary input default | Keep the existing 16 MiB per-input default for Phase 2; raise only with evidence and explicit limits | Limits and large-file claims |
| D5 | Auto text semantics | Auto-selected text uses strict UTF-8, preserved newlines, and no other normalization | Auto spec normalization |
| D6 | Platform gate | Add Windows CI before claiming cross-platform Phase 2 support; Linux remains the minimum merge gate | Support statement |

Any accepted answer must be copied into the normative section and removed from
the unresolved ledger before this RFC changes to `Accepted`.

## Consequences

This proposal makes automatic behavior auditable and conservative: ambiguity
is visible, explicit intent wins, exact binary comparison never relies on a
digest alone, and plugin publication waits for evidence from two built-ins. It
also exposes a real pre-release schema decision that must be resolved before
code begins rather than hidden inside implementation details.
