# RFC 0001: Comparison Outcome and Diff Result Contracts

[Chinese documentation](0001-comparison-outcome-and-diff-result_zh.md)

- Status: Implemented
- Date: 2026-09-06
- Owners: Platydiff maintainers

## Summary

Platydiff separates the terminal outcome of a comparison attempt from the semantic result of a completed comparison. `CompareOutcome` is the schema-versioned, serializable execution envelope. Only its `completed` variant carries a `DiffResult`. `DiffResult` therefore always represents an actual comparison fact and never stands in for an unavailable capability, a pipeline failure, or a future scheduling outcome.

Schema v1 publishes three outcome variants: `completed`, `unavailable`, and `failed`. It also defines the successful result model, two-layer provenance, policy evaluation, modality-specific changes, extension changes, result-detail completeness, stable diagnostics, and structured errors.

## Motivation

Detection, decoding, normalization, alignment, or capability resolution can fail before a comparator has produced any difference facts. Treating those failures as `DiffResult` values would weaken the type's central invariant and couple comparators to orchestration concerns. Conversely, using exceptions as the only failure protocol would force the CLI, batch execution, plugins, JSON consumers, and renderers to invent incompatible result envelopes.

The contracts therefore use one serializable outer union while preserving a narrow successful result type:

```python
CompareOutcome = CompletedOutcome | UnavailableOutcome | FailedOutcome
```

This split also permits execution records and completed difference results to use different cache and retention policies.

## Execution lifecycle

The complete planned lifecycle is:

```text
created
  -> validating
  -> sourcing
  -> detecting?        # skipped when the modality is explicit
  -> resolving
  -> decoding
  -> normalizing
  -> aligning
  -> comparing
  -> aggregating
  -> completed
```

The first implementation slice requires an explicit text comparison specification and therefore skips `detecting`.

Terminal transitions are constrained as follows:

| From | Terminal outcome | Meaning |
| --- | --- | --- |
| `detecting`, `resolving` | `unavailable` | No suitable modality, comparator, capability, or required backend can satisfy the request |
| `validating`, `sourcing`, or any execution stage | `failed` | The request matched an execution path, but validation or execution could not finish |
| `aggregating` | `completed` | A relation and policy verdict were produced |

`cancelled` and `skipped` are future candidates. They are not legal schema-v1 outcome kinds. Adding them requires a compatibility review and an RFC amendment or successor.

Rendering occurs after `CompareOutcome` exists. A renderer failure must not rewrite an existing completed outcome as a comparison failure.

## CompareOutcome

Every schema-v1 outcome has these common fields:

```python
class OutcomeBase:
    schema_version: Literal[1]
    kind: str
    execution: ExecutionRecord
```

The variants are:

```python
class CompletedOutcome(OutcomeBase):
    kind: Literal["completed"]
    result: DiffResult


class UnavailableOutcome(OutcomeBase):
    kind: Literal["unavailable"]
    problem: CapabilityProblem


class FailedOutcome(OutcomeBase):
    kind: Literal["failed"]
    problem: ExecutionProblem
```

An unavailable or failed outcome must not contain an empty, partial, or placeholder `DiffResult`.

Known domain failures are converted at the pipeline boundary. Library code must not catch and normalize `KeyboardInterrupt`, `SystemExit`, `MemoryError`, or programming defects into ordinary domain failures. The CLI may catch an otherwise unhandled exception at its outer boundary, hide sensitive traceback data by default, emit `internal_error`, and exit unsuccessfully.

## ExecutionRecord

`ExecutionRecord` describes how far one comparison attempt progressed. It contains:

- UTC `started_at` and `finished_at` timestamps plus integer `duration_ns`;
- ordered stage records with start, finish, and terminal disposition;
- capability and backend attempts, including rejected candidates and fallback decisions;
- stable diagnostics;
- the last completed stage.

Runtime timing fields do not participate in semantic cache keys. Tests use an injected clock so timestamp and duration serialization remain deterministic under test.

A diagnostic has a stable lowercase ASCII `code`, severity `info` or `warning`, an optional pipeline stage, a safe human message, and JSON-safe details. A diagnostic warning does not imply `verdict=warn`.

## Problems and structured status codes

Problems carry a stable string code, an HTTP-style numeric `status_code`, a stage, a safe message, JSON-safe details, and—where meaningful—a `retryable` flag. Numeric status codes provide coarse classification but are not HTTP responses and are not process exit codes.

Schema v1 reserves these mappings:

| Code | Status code | Outcome |
| --- | ---: | --- |
| `invalid_spec` | 400 | `failed` |
| `permission_denied` | 403 | `failed` |
| `source_not_found` | 404 | `failed` |
| `resource_limit_exceeded` | 413 | `failed` |
| `compare_resource_limit` | 413 | `failed` |
| `unsupported_encoding` | 415 | `failed` |
| `decode_error` | 422 | `failed` |
| `internal_error` | 500 | `failed` at the CLI boundary |
| `io_error` | 500 | `failed` |
| `capability_unavailable` | 501 | `unavailable` |
| `comparator_failure` | 502 | `failed` |
| `backend_unavailable` | 503 | `unavailable` |

The string code is the stable machine identifier. Multiple string codes may share a numeric status code.

## Two-layer provenance

Execution and comparison provenance are deliberately separate.

`CompareOutcome.execution` records orchestration facts:

- stage progress and timing;
- capability and backend attempts;
- fallback and retry decisions;
- runtime diagnostics.

`DiffResult.provenance` records semantic comparison facts:

- the before and after roles, source kinds, sizes, and SHA-256 digests;
- the normalized `CompareSpec`;
- explicit normalization and alignment transformations;
- comparator, algorithm, and implementation versions;
- seeds, configured resource budgets, and actual deterministic work counts.

This split keeps failures auditable while allowing a detached or cached `DiffResult` to remain self-describing. Raw input contents, absolute paths, secrets, and tracebacks are excluded by default.

## DiffResult

`DiffResult` exists only after comparison and aggregation have completed:

```python
class DiffResult:
    relation: Literal["equal", "different"]
    verdict: Literal["pass", "warn", "fail"]
    fidelity: Literal["full", "degraded"]
    summary: DiffSummary
    changes: ChangeSet
    metrics: tuple[Metric, ...]
    evaluations: tuple[PolicyEvaluation, ...]
    artifacts: tuple[ArtifactRef, ...]
    provenance: ComparisonProvenance
```

The invariants are:

- `relation` states equivalence under the normalized specification; the specification identifies whether that means exact, structural, perceptual, or statistical equivalence.
- The default strict-equality policy maps `equal` to `pass` and `different` to `fail`.
- `warn` can only be produced by an explicit policy evaluation.
- `fidelity` describes information loss in comparison execution, such as an allowed lower-fidelity fallback. It does not describe result-detail truncation.
- Metrics state measured facts. Policy evaluations explain how facts and thresholds produced the verdict.
- The result verdict equals the highest-severity policy evaluation under the selected aggregation policy.
- Renderers consume these fields and must not recalculate comparison or policy semantics.

## Summary and change completeness

```python
class DiffSummary:
    change_count: int | None
    counts: tuple[SummaryCount, ...]


class ChangeSet:
    completeness: Literal["complete", "truncated", "partial"]
    items: tuple[Change, ...]
    total_count: int | None
    returned_count: int
    omitted_count: int | None
    selection: Literal["all", "source_order_prefix", "algorithm_partial"]
    limit: int | None
```

Summary count names and units are stable lowercase ASCII identifiers. Names are unique within a result and serialized in stable name order.

The completeness states have exact meanings:

| Completeness | Required invariants |
| --- | --- |
| `complete` | `total_count == returned_count`, `omitted_count == 0`, `selection == "all"` |
| `truncated` | The comparison and total statistics completed; total and omitted counts are known; only complete changes are retained in source order |
| `partial` | The algorithm did not form a complete change collection; total and omitted counts and `summary.change_count` are null; returned items are confirmed facts only |

When both are non-null, `summary.change_count` must equal `changes.total_count`.

Schema v1 declares `partial` to prevent it from being conflated with output truncation. The first implementation slice must never produce it: exhausting the Myers work budget returns a failed outcome. A future specification must explicitly allow partial results before a comparator may produce `partial`; a partial result may prove `different` but must never claim `equal`.

Truncation uses complete change boundaries. It produces a `change_details_truncated` diagnostic and does not change relation, verdict, or fidelity.

## Change variants and extensions

Built-in changes use stable, modality-specific tagged variants such as `text_hunk`. A single universal object with optional location fields is rejected because line ranges, table keys, image coordinates, and time intervals have incompatible invariants.

Third-party changes use `ExtensionChange`:

```python
class ExtensionChange:
    kind: str                 # reverse-domain identifier
    plugin_id: str
    schema_version: int
    payload: JsonObject
```

Rules:

- built-in kinds use stable lowercase ASCII identifiers without a domain prefix;
- extension kinds use reverse-domain names such as `org.example.spectrogram_region`;
- extension payloads contain JSON-safe values only;
- an unknown namespaced kind can be preserved as `ExtensionChange`;
- an unknown non-namespaced built-in kind is rejected rather than guessed;
- a generic renderer may show the extension identity and safe summary but must not infer its semantics;
- plugin-specific renderers may be registered in a future plugin protocol, without introducing a core-to-plugin dependency.

## Metrics, evaluations, and artifacts

Numeric metric values use a tagged JSON-safe union:

```json
{"kind": "finite", "value": 1.25}
{"kind": "nan"}
{"kind": "positive_infinity"}
{"kind": "negative_infinity"}
```

JSON serialization must never emit non-standard bare `NaN` or `Infinity` tokens.

A metric records a stable name, value, unit, direction, and optional aggregation method. A policy evaluation records a rule ID, verdict, and, when applicable, the metric, operator, threshold, and observed value used by the rule. Thresholds do not live inside metrics because one observation may participate in multiple policies.

`ArtifactRef` contains an artifact ID, stable kind, media type, relative URI, SHA-256 digest, and byte size. URIs must be relative to an explicit artifact root, use portable forward slashes, and contain no absolute prefix or `..` segment. Artifacts are never embedded in the result by default.

## JSON compatibility

- Schema v1 uses UTF-8 JSON and stable lowercase ASCII field and enum identifiers.
- Serializers reject non-JSON-safe extension details and non-finite bare numbers.
- Consumers should ignore unknown optional object fields but must reject an unknown schema version or unknown non-extension union kind.
- Adding a required field, changing a field's meaning, changing an existing enum meaning, or removing a variant requires a new schema version and migration guidance.
- Adding a new outcome variant requires compatibility review even when the schema version remains unchanged.
- Stable ordering is required for summary counts, metrics, evaluations, diagnostics, and artifacts.

## Rejected alternatives

### Make every terminal state a DiffResult

Rejected because a detection or decoding failure has no difference result and would weaken every comparator and renderer invariant.

### Use exceptions as the only failure protocol

Rejected because CLI, batch, plugin, and JSON consumers need one serializable terminal envelope with partial execution provenance.

### Use one status enum

Rejected because execution completion, relation, verdict, fidelity, and detail completeness are independent dimensions.

### Store human summary text in the core result

Rejected because localized or revised prose would become a machine contract. Renderers produce human text from structured summary counts.

## Consequences

The result model is larger than a traditional boolean diff result, but its invariants are explicit and testable. Comparator implementations remain focused on semantic comparison. Pipeline code owns execution outcome conversion. Renderers consume one serializable envelope without changing meaning. Future outcome kinds and modality payloads require deliberate compatibility review rather than silent expansion.
