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
@dataclass(frozen=True, slots=True)
class BinaryResourceLimits:
    max_input_bytes: int = 16 * 1024 * 1024
    chunk_bytes: int = 64 * 1024
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

@dataclass(frozen=True, slots=True)
class BinaryCompareSpec:
    kind: Literal["binary"] = field(default="binary", init=False)
    limits: BinaryResourceLimits = field(default_factory=BinaryResourceLimits)

@dataclass(frozen=True, slots=True)
class AutoTextOptions:
    encoding: TextEncoding = TextEncoding.UTF8
    newline: NewlinePolicy = NewlinePolicy.PRESERVE
    context_lines: int = 3

@dataclass(frozen=True, slots=True)
class AutoResourceLimits:
    max_input_bytes: int = 16 * 1024 * 1024
    max_input_lines: int = 200_000
    max_encoded_line_bytes: int = 1024 * 1024
    max_myers_work: int = 5_000_000
    max_detection_bytes: int = 64 * 1024
    binary_chunk_bytes: int = 64 * 1024
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

@dataclass(frozen=True, slots=True)
class AutoCompareSpec:
    kind: Literal["auto"] = field(default="auto", init=False)
    text: AutoTextOptions = field(default_factory=AutoTextOptions)
    minimum_confidence: int = 800
    ambiguity_margin: int = 100
    limits: AutoResourceLimits = field(default_factory=AutoResourceLimits)

CompareSpec = AutoCompareSpec | TextCompareSpec | BinaryCompareSpec

compare(before: Source, after: Source, spec: CompareSpec) -> CompareOutcome
```

An explicit `TextCompareSpec` or `BinaryCompareSpec` bypasses `detecting`. Only
`AutoCompareSpec` enables it. A Python source type, filename suffix, or MIME
label never silently changes an explicit specification.

All integer limit fields reject booleans. Byte/count/work limits are in the
inclusive range `0..2**63-1`. A zero input limit accepts only an empty encoded
source; zero line or Myers limits retain their RFC 0002 meanings; zero change
item or payload limits still complete comparison but return a truncated empty
detail prefix when a change exists. `chunk_bytes` and `binary_chunk_bytes` are
execution granularities, not budgets, and must be in `1..16*1024*1024`.
`context_lines` is non-negative. Confidence and margin are integers in
`0..1000`; a zero margin permits an exactly tied top candidate to be selected
by the total ordering. `max_detection_bytes=0` disables content inspection but
does not bypass detection.

Constructors fill every default before validation. Serialization always emits
the normalized, fully populated spec. Readers require every field shown below,
ignore unknown optional object fields as RFC 0001 requires, reject unknown spec
kinds or missing/wrongly typed fields, and do not re-emit ignored fields.
Canonical compact JSON uses RFC 0002's UTF-8, sorted-key, compact-separator
rules. Exact examples are:

```json
{"kind":"binary","limits":{"chunk_bytes":65536,"max_change_items":10000,"max_change_payload_bytes":4194304,"max_input_bytes":16777216}}
```

```json
{"ambiguity_margin":100,"kind":"auto","limits":{"binary_chunk_bytes":65536,"max_change_items":10000,"max_change_payload_bytes":4194304,"max_detection_bytes":65536,"max_encoded_line_bytes":1048576,"max_input_bytes":16777216,"max_input_lines":200000,"max_myers_work":5000000},"minimum_confidence":800,"text":{"context_lines":3,"encoding":"utf-8","newline":"preserve"}}
```

`TextCompareSpec` and its public `ResourceLimits` type and JSON remain exactly
as implemented by Phase 1. The two new specs each have one public limits object;
there is no keyword argument or environment/config override that can become a
second source of truth. `AutoTextOptions` defines the exact text intent used if
auto detection selects text; binary selection ignores it but provenance keeps
the complete auto spec.

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
Phase 2 introduces one private superset `ExecutionLimits` value produced from
exactly one spec limits object. For text it translates the unchanged
`ResourceLimits`; for binary it translates `BinaryResourceLimits`; for auto it
translates `AutoResourceLimits` and computes
`effective_detection_bytes=min(max_detection_bytes, max_input_bytes)`. The
public normalized spec records requested values, while execution provenance
records effective limits and actual use. No public `ExecutionLimits` constructor,
wire object, compare parameter, configuration file, or environment override is
introduced. Moving limits out of specs requires a later schema decision.

## Detection contract

### Bounded evidence collection

Detection reads at most `effective_detection_bytes` from the start of each source.
It uses the same opened source snapshot that comparison will consume or a
replayable bounded prefix owned by that snapshot. Detection must not open a
path by name and then compare a separately resolved path. Text sources provide
an explicit text signal; byte and path sources require content evidence.

Phase 2 has exactly one detector policy:

```text
detector_id: core.text_binary_prefix
detector_version: 1
detector_priority: 0
```

It uses only deterministic evidence:

- source kind;
- a bounded byte prefix and its length;
- strict UTF-8 validity in the inspected prefix;
- NUL and control-character evidence;
- decoded Unicode C0/C1 control counts.

Magic signatures, filename suffixes, operating-system MIME databases, and
statistical file-type classifiers are out of scope in Phase 2 and are neither
scored nor recorded. Locale, wall-clock time, filesystem enumeration order, and
network services are forbidden inputs.

### Detection candidates and confidence

Each source produces candidate records using this typed form:

```text
modality_id: text | binary
confidence: integer 0..1000
detector_id: stable identifier
detector_version: implementation version
priority: non-negative integer
evidence_codes: ordered stable identifiers
evidence_counts: stable identifier -> non-negative integer
```

`confidence` is a deterministic evidence score, not a probability or a promise
about correctness. Scores are comparable only for this detector version. The
evidence counts are limited to `inspected_bytes`, `nul_count`,
`disallowed_control_count`, `non_ascii_byte_count`, and `pending_utf8_bytes`.
They never include bytes or decoded content.

The classifier applies the first matching row. `TextSource` is already validated
as Unicode scalar text and never receives a binary candidate. For `PathSource`
and `BytesSource`, allowed text controls are TAB (`U+0009`), LF (`U+000A`), and
CR (`U+000D`); NUL has its own row; every other C0/C1 scalar is disallowed.

| Source/evidence | Text score and code | Binary score and code |
| --- | --- | --- |
| `TextSource`, including empty | 1000, `explicit_text_source` | no candidate |
| Empty byte/path source | 500, `empty_source` | 500, `empty_source` |
| Non-empty source, effective prefix is zero bytes | 500, `content_not_inspected` | 500, `content_not_inspected` |
| Prefix contains NUL | no candidate | 1000, `nul_present` |
| Prefix has a conclusive strict UTF-8 error | no candidate | 1000, `utf8_invalid` |
| Decoded prefix has another disallowed C0/C1 scalar | 400, `disallowed_control_present` | 950, `disallowed_control_present` |
| Valid UTF-8 prefix with a possibly incomplete final scalar | 850, `utf8_prefix_incomplete` | 500, `utf8_prefix_incomplete` |
| Valid complete prefix with any non-ASCII byte | 950, `utf8_valid_non_ascii` | 400, `utf8_valid_non_ascii` |
| Valid complete ASCII prefix | 900, `utf8_valid_ascii` | 400, `utf8_valid_ascii` |

Validation uses a strict incremental UTF-8 decoder. If the prefix stops before
source EOF, one trailing incomplete scalar of one to three bytes is pending,
not invalid, and produces `utf8_prefix_incomplete`; any error before that suffix
is conclusive. If the prefix reaches EOF, a pending scalar is conclusive
`utf8_invalid`. BOM is valid non-ASCII UTF-8 evidence and is not removed during
detection. Detection never infers an encoding other than UTF-8.

A pair candidate exists only when the modality is eligible for both inputs and
a built-in capability can satisfy the request. Its score is the minimum of the
two source scores. Its source scores are retained in before/after order. This
single detector cannot emit duplicates; the generic fold rule remains: retain
the highest score, then the lowest detector priority, and retain evidence codes
in stable lexical order. A text-looking source paired with an invalid UTF-8
source therefore has only the low-scoring binary intersection; it does not
silently treat one input as text and the other as binary.

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
decision ledger. The draft spec defaults are 800 and 100. For any accepted
values, the table, minimum comparison, margin comparison, and total ordering
make selection fully computable. The minimum test happens first; if the top
candidate is below it, the result is `detection_no_match` even if candidates
are tied. With one eligible candidate its lead is treated as unbounded. With
multiple candidates, `top_score - runner_up_score >= ambiguity_margin` is
required. Accepted values remain explicit in the normalized auto spec and
provenance.

Detection classifies only the bounded prefix. If it selects text and strict
full-input decoding later encounters invalid UTF-8, execution ends as
`failed/decode_error` at `decoding`. It must not retry or fall back to binary.
This `late-invalid` behavior is required for reproducibility and makes prefix
confidence distinct from full-input validation.

### Typed detection provenance

Detection has one wire location: an optional `ExecutionRecord.detection` field.
It is omitted, not serialized as null, for explicit text/binary calls, so every
unchanged Phase 1 JSON payload remains byte-for-byte identical. Auto outcomes,
including detection unavailability, include:

```text
DetectionRecord
  detector_id: core.text_binary_prefix
  detector_version: "1"
  maximum_bytes: effective non-negative limit
  minimum_confidence: 0..1000
  ambiguity_margin: 0..1000
  sources: exactly (before, after) SourceDetectionRecord
  pair_candidates: tuple sorted by the normative rank
  disposition: selected | no_match | ambiguous
  selected_modality: text | binary | null

SourceDetectionRecord
  role: before | after
  candidates: tuple[DetectionCandidate, ...]

DetectionCandidate
  modality_id: text | binary
  confidence: 0..1000
  detector_id: core.text_binary_prefix
  detector_version: "1"
  priority: 0
  evidence_codes: tuple[stable identifier, ...]
  evidence_counts: JSON object of the allowed count keys

PairDetectionCandidate
  modality_id: text | binary
  confidence: 0..1000
  before_confidence: 0..1000
  after_confidence: 0..1000
  detector_priority: 0
  capability_priority: non-negative integer
```

Each `SourceDetectionRecord` contains its role and candidates sorted by
descending confidence then modality ID. Each `PairDetectionCandidate` contains
modality, pair confidence, before/after confidence, detector priority, and
capability priority. Evidence codes are sorted lexically and evidence-count
keys use canonical JSON key ordering. `selected_modality` is non-null exactly
for `selected`; `no_match` and `ambiguous` require null. Candidate bytes and
decoded text are never serialized.

An illustrative `ExecutionRecord` field fragment is:

```json
{"detection": {
  "detector_id": "core.text_binary_prefix",
  "detector_version": "1",
  "maximum_bytes": 65536,
  "minimum_confidence": 800,
  "ambiguity_margin": 100,
  "sources": [
    {"role": "before", "candidates": []},
    {"role": "after", "candidates": []}
  ],
  "pair_candidates": [],
  "disposition": "no_match",
  "selected_modality": null
}}
```

This is a schema-v1 additive field under decision D3. The JSON field names are
the names above; tuples serialize as arrays and enums serialize as their shown
lowercase strings. Unknown optional fields inside these records are ignored on
read and not re-emitted; wrong types,
missing required fields, invalid ordering, and unknown dispositions are rejected.

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

### Snapshot and stage ownership

Phase 2 introduces a private replayable source snapshot. Stage ownership is
normative:

- `sourcing` validates source objects, opens each path once, performs the
  baseline `fstat`, rejects non-regular targets, checks known sizes, and performs
  a bounded incremental UTF-8 size preflight for `TextSource`. It does not read
  path content.
- `detecting` reads and owns the bounded prefix for auto mode, then checks
  descriptor metadata against the sourcing baseline. The prefix remains
  replayable and is not counted twice against input limits.
- `resolving` consumes only detection/request metadata and never source bytes.
- `decoding` consumes the replayed prefix plus remaining bytes when text is
  selected, computes that source hash, enforces text byte/line limits, performs
  strict decoding, and makes the final descriptor metadata check for that text
  snapshot. For binary, it only constructs the byte-stream adapters; incremental
  `TextSource` UTF-8 encoding is one such adapter.
- `normalizing` and `aligning` retain their text meaning and are observed no-ops
  for binary.
- `comparing` consumes the replayed prefix plus remaining binary bytes, directly
  compares bytes, computes both hashes and spans, enforces byte/change limits,
  reaches EOF, and performs the final descriptor metadata checks.
- `aggregating` constructs the result from already completed comparison facts.

The same bytes consumed during detection are replayed to decoding/comparing and
therefore participate once in hashes and comparison. `io_error`,
`resource_limit_exceeded`, `source_changed`, and `decode_error` carry the stage
where they are actually discovered; `source_changed` is not fixed to sourcing.
The existing Phase 1 explicit-text eager-source path and its serialized failures
remain unchanged until an independently reviewed refactor can preserve them.

| Scenario | Required terminal trace |
| --- | --- |
| Auto, stable text | `validating✓ sourcing✓ detecting✓ resolving✓ decoding✓ normalizing✓ aligning✓ comparing✓ aggregating✓` |
| Explicit stable binary | `validating✓ sourcing✓ resolving✓ decoding✓ normalizing✓ aligning✓ comparing✓ aggregating✓` |
| Metadata changes after snapshot, before/during prefix read | terminal `detecting/failed/source_changed` |
| Prefix read raises I/O error | terminal `detecting/failed/io_error` |
| Auto selects text; later bytes are invalid UTF-8 | terminal `decoding/failed/decode_error`; no binary fallback |
| Text full read or final metadata check fails | terminal `decoding/failed/io_error` or `source_changed` |
| Binary stream read or final metadata check fails | terminal `comparing/failed/io_error` or `source_changed` |
| Binary exceeds streamed input-byte limit | terminal `comparing/failed/resource_limit_exceeded` |
| Initial known size already exceeds input limit | terminal `sourcing/failed/resource_limit_exceeded` |

When two failures become observable in one operation, the first deterministic
check wins: byte-budget overflow is checked after every chunk before span/hash
finalization; I/O errors are reported when raised; final metadata comparison
runs only after clean EOF.

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
Sourcing first counts encoded bytes with a strict incremental encoder over
bounded character slices and fails with
`sourcing/failed/resource_limit_exceeded` as soon as the byte limit is exceeded.
Comparison repeats the same deterministic incremental encoding through a
bounded `chunk_bytes` adapter; it never constructs the complete encoded copy.
Invalid Unicode scalar input is rejected by `TextSource` construction or at
`validating/failed/invalid_spec`, before a snapshot exists. `BytesSource` is
already an immutable snapshot. Path inputs use one opened file descriptor per
source for detection, comparison, and hashing.

### Source safety and reproducibility

Before reading a path, the implementation opens it with close-on-exec and a
nonblocking safeguard, then uses `fstat` on the descriptor. The final target
must be a regular file. Directories, FIFOs, devices, sockets, and other special
files fail without blocking. Symlinks are allowed only when their opened target
is regular; provenance records that a path source was used, not an absolute or
resolved local path.

Initial and final descriptor metadata include platform-available device,
inode/file ID, byte length, and nanosecond modification time. A detected change
during the observed read window returns `failed/source_changed` at `detecting`,
`decoding`, or `comparing`, whichever check observes it, and no `DiffResult`.
The streamed byte count is checked independently of advertised size. This
detects ordinary mutations but cannot prove that a hostile writer did not
change and restore all observable metadata; the input SHA-256 remains the
identity of the bytes actually read.

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

All values reject booleans and lie in `0..2**63-1`. Both lengths cannot be zero.
A replacement span has equal positive lengths and equal before/after offsets.
An insertion has `before_length=0`, positive `after_length`, and both offsets at
the common EOF. A deletion is symmetric. The built-in comparator emits at most
one insertion/deletion, always as the final span. Replacement spans cover
maximal contiguous unequal runs within the overlapping prefix, are strictly
ordered by both offsets, and neither overlap nor touch; touching replacements
must be coalesced. These collection invariants are validated when constructing
the binary `ChangeSet`.

`BinarySpan` never embeds byte content. Spans are observational mismatch ranges,
not a minimal insertion/deletion script or patch. Its canonical object is:

```json
{
  "kind": "binary_span",
  "before_offset": 4096,
  "before_length": 12,
  "after_offset": 4096,
  "after_length": 12
}
```

The complete algorithm counts all spans and mismatching bytes while retaining
only the bounded source-order prefix. The item and canonical payload budgets use
the exact schema-v1 accounting rule from RFC 0001. Therefore detail limits may
produce a `truncated` `ChangeSet`; they do not change relation, verdict, or
fidelity. Phase 2 defines no binary work budget: `max_input_bytes` bounds the
linear scan and `chunk_bytes` bounds each allocation. Input-byte exhaustion
produces `failed/resource_limit_exceeded`, never `partial` and never an assumed
difference. A zero input limit accepts two empty inputs; a zero item or payload
limit returns `complete` for equal inputs and `truncated` with zero returned
items for different inputs. For each prospective complete span, the item limit
is checked before the payload limit; the first failing check determines
`limit_reason` and `limit`.

The binary result contract is exact:

| Field | Stable value |
| --- | --- |
| `summary.change_count` | total binary span count |
| Summary `different_bytes` | unequal aligned bytes plus absolute length difference; unit `bytes` |
| Summary `replacement_spans` | replacement span count; unit `spans` |
| Summary `inserted_bytes` | trailing after-only bytes; unit `bytes` |
| Summary `deleted_bytes` | trailing before-only bytes; unit `bytes` |
| Metric `different_bytes` | finite same count; unit `bytes`; direction `lower_is_better`; aggregation `sum` |
| Metric `before_bytes` | finite input size; unit `bytes`; direction `neutral`; aggregation `count` |
| Metric `after_bytes` | finite input size; unit `bytes`; direction `neutral`; aggregation `count` |
| Evaluation | rule `binary.strict_equality`, metric `different_bytes`, operator `eq`, finite threshold `0`, observed metric value |

The evaluation verdict is `pass` exactly when observed is zero and `fail`
otherwise. It is the only Phase 2 binary policy evaluation. Equal inputs have
zero changes and all zero difference counts; lengths remain their actual values.
Input hashes are ordered before/after in comparison provenance. Resource
provenance records `max_input_bytes`, actual `before_bytes`/`after_bytes`,
`chunk_bytes`, `max_change_items`, `max_change_payload_bytes`, returned change
count, and retained canonical payload bytes.

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
kinds remain rejected. `ExecutionRecord.detection` is the only new optional
wire field; producers omit it for every explicit comparison and readers treat
absence as no detection stage. New problem codes proposed by this RFC are:

| Code | Status | Outcome | Stage |
| --- | ---: | --- | --- |
| `detection_no_match` | 415 | unavailable | detecting |
| `detection_ambiguous` | 409 | unavailable | detecting |
| `source_type_unsupported` | 415 | failed | sourcing |
| `source_changed` | 409 | failed | detecting, decoding, or comparing |

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
| Detection | every scoring-table row, empty, mixed evidence, incomplete UTF-8 prefix, late-invalid UTF-8, ties, below-threshold, explicit override, deterministic repeated runs |
| Resolution | registration-order independence, duplicate rejection, every reject reason, selected/rejected attempts, missing backend, no capability |
| Binary correctness | equal, different, empty, length mismatch, chunk-boundary mismatch, reconstruction-free span invariants, hash recorded but not trusted for equality |
| Resources | exact input boundary, detection prefix boundary, change-item and payload truncation, bounded peak memory, no partial result on input/work exhaustion |
| Sources | bytes, text encoding, regular path, missing/denied path, directory, FIFO/device/socket where available, symlink target, mutation during read |
| Contracts | Phase 1 golden payloads, new round trips, unknown fields/kinds, stable codes, public exports, schema decision and migration note |
| CLI | old routes unchanged, binary and auto routes, all exits, stdout/stderr, flag separation, label/path/control escaping, renderer failure |
| Provenance | typed detection wire golden/round trip, detector/comparator/backend versions, thresholds, ranking, attempts, transformations, hashes, limits and actual usage; no inspected bytes |
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
