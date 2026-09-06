# RFC 0002: Development Phases and the First Text Slice

[Chinese documentation](0002-development-phases-and-text-slice_zh.md)

- Status: Implemented
- Date: 2026-09-06
- Owners: Platydiff maintainers

## Summary

This RFC defines the delivery order, commit boundaries, public API gate, file layout, CLI behavior, text semantics, resource limits, and verification requirements for Platydiff's first executable vertical slice. That slice is a Python 3.12+ library and CLI that compare explicitly selected text inputs and return the contracts in [RFC 0001](0001-comparison-outcome-and-diff-result.md).

This document defined the implementation plan now delivered by the Phase 1 pull request from `feat/python-text-diff`.

Automatic format detection, binary comparison, third-party plugin discovery, and other modalities are later phases. Their appearance in the roadmap does not authorize implementation. Each phase must return to the contract gates in this RFC before development starts.

## Goals and non-goals

Phase 1 must deliver one complete path through validation, sourcing, resolution, decoding, normalization, alignment, comparison, aggregation, and rendering. It must establish the public result contract without prematurely publishing a plugin API.

Phase 1 goals are:

- a typed Python API with explicit text intent;
- path, bytes, and in-memory text sources;
- deterministic line-oriented text comparison;
- terminal and JSON outcome rendering;
- stable CLI exit behavior;
- zero third-party runtime dependencies;
- compatibility, correctness, determinism, and resource-bound tests.

Phase 1 does not include:

- automatic modality or encoding detection;
- stdin, directory, or recursive comparison;
- configuration files or environment-based configuration;
- binary, structured-data, table, array, image, source-code, PDF, audio, or video comparators;
- public plugin discovery, entry points, or a plugin SDK;
- color output, HTML, JUnit, or patch artifacts;
- wall-clock-based algorithm fallbacks.

## Phase 1 delivery and commit gates

The implementation pull request uses these commits in order. A commit must meet its gate before the next one begins.

| Commit | Scope | Gate |
| --- | --- | --- |
| `build: bootstrap Python package and quality tooling` | Flat package, build metadata, development extras, CI, empty module boundaries | Package builds; both CLI help entry points load; Ruff, strict mypy, pytest, and build are configured; no comparison behavior is claimed |
| `feat(core): add comparison contracts and serialization` | Sources, specs, outcomes, results, problems, provenance, JSON encoding and validation | RFC 0001 invariants have typed constructors, round-trip tests, invalid-state tests, and stable snapshots |
| `feat(text): implement linear-space Myers edit scripts` | Internal text IR and deterministic shortest-edit-script engine | Oracle, reconstruction, differential, tie-break, budget, determinism, and representative memory tests pass |
| `feat(text): add the text comparison pipeline` | Explicit text resolution, decoding, newline normalization, hunk construction, policy aggregation | Library API covers equal, different, decoding failure, source failure, limits, complete output, and truncated detail |
| `feat(cli): add text commands and outcome renderers` | Two CLI routes, terminal and JSON renderers, exit mapping | Both routes exercise the same pipeline; output, error safety, and exit codes have integration tests |
| `docs: document the first executable vertical slice` | README, API and CLI examples, limits, planned-capability labels | Examples run in tests; documentation distinguishes implemented behavior from the roadmap |

The bootstrap commit may define importable placeholders needed to establish dependency direction, but it must not publish speculative fields or plugin protocols. The contracts commit freezes schema-v1 names before the comparator or CLI depends on them.

## Planned file layout

Phase 1 uses a flat package layout:

```text
pyproject.toml
platydiff/
├── __init__.py                 # curated public exports only
├── __main__.py                 # python -m platydiff
├── core/
│   ├── models.py               # Source, CompareSpec, outcomes, DiffResult
│   ├── problems.py             # project-defined domain failures
│   ├── serialization.py        # schema-v1 JSON conversion and validation
│   ├── pipeline.py             # orchestration and boundary conversion
│   └── _registry.py            # internal capability registration
├── comparators/
│   └── text/
│       ├── models.py           # TextLine, edit operations, TextHunk
│       ├── myers.py            # linear-space shortest edit script
│       └── comparator.py       # text result construction
├── renderers/
│   ├── terminal.py
│   └── json.py
└── cli/
    ├── parser.py
    └── main.py
tests/
├── unit/
└── integration/
```

The dependency direction remains:

```text
CLI / renderers / comparators
              ↓
             core
```

`core` must not import a concrete comparator or renderer. `_registry.py` is an internal composition mechanism in Phase 1 and is not re-exported.

## Python packaging baseline

The fixed bootstrap choices are:

- Python 3.12 or newer;
- a flat `platydiff/` package;
- Hatchling as the build backend;
- initial version `0.1.0.dev0`;
- Apache-2.0 project license;
- `argparse` for the CLI;
- no third-party runtime dependency;
- Ruff, mypy in strict mode, pytest, and build as development tools;
- a Linux/Python 3.12 baseline CI job.

The package must register `media` and `external` pytest markers for later suites. Phase 1 has no test that requires those capabilities. Future tests must report a specific skip reason when an optional backend is absent.

## Public Python API

The sole comparison entry point is:

```python
def compare(
    before: Source,
    after: Source,
    spec: CompareSpec,
) -> CompareOutcome: ...
```

The public source union is:

```python
Source = PathSource | BytesSource | TextSource
```

`PathSource` refers to one filesystem file. `BytesSource` owns immutable bytes and an optional safe display label. `TextSource` owns an already-decoded Python string and an optional safe display label. Source provenance records roles and digests without serializing absolute paths or input contents.

`CompareSpec` is a tagged union. Its first and only Phase 1 variant is `TextCompareSpec`. The `spec` argument is required: the API does not infer text from filenames, content, or Python types. The normalized specification, including every effective default, is recorded in comparison provenance.

The package root selectively exports `compare`, source types, specification types, outcome types, `DiffResult`, and the core public enums. It does not re-export registries, pipeline stages, comparator implementations, renderer internals, or Myers primitives.

Serialization is part of the schema-v1 contract. Domain model construction validates invariants; decoding untrusted JSON first produces generic JSON values, validates the schema and union tags, and only then constructs typed models.

## CLI contract

Phase 1 provides equivalent routes:

```text
platydiff compare --type text BEFORE AFTER
platydiff text BEFORE AFTER
```

Both parser routes construct the same `TextCompareSpec` and call the same comparison and rendering path. Neither route performs automatic detection.

The planned Phase 1 options cover:

- `--format terminal|json`;
- `--encoding utf-8|utf-8-sig`;
- `--newline preserve|normalize_lf`;
- `--context-lines`;
- input byte, line, encoded-line, Myers-work, change-item, and change-payload limits.

Terminal output is human-readable. JSON output is the exact schema-v1 `CompareOutcome` envelope. Renderers may choose presentation but may not recompute relation, verdict, fidelity, completeness, or policy evaluation.

Shell exit codes are:

| Exit | Meaning |
| ---: | --- |
| `0` | A completed outcome with verdict `pass` or `warn` |
| `1` | A completed outcome with verdict `fail` |
| `2` | CLI syntax, option, or pre-execution usage error for which no comparison outcome is emitted |
| `3` | An `unavailable` or `failed` outcome, including a safely mapped `internal_error` |

Machine consumers must use the stable problem string and HTTP-style status code from RFC 0001 rather than inferring a detailed cause from the shell exit code.

## Text decoding and normalization

Byte and path inputs decode as strict UTF-8 by default. Invalid input produces `failed/unsupported_encoding` or `failed/decode_error` as appropriate; it is never silently replaced. A UTF-8 BOM is data under `utf-8` and is removed only when the caller explicitly selects `utf-8-sig`.

The decoded input is split into immutable `TextLine` values:

```python
class TextLine:
    content: str
    terminator: Literal["", "\n", "\r\n", "\r"]
```

The default `preserve` policy compares content and terminator, thereby preserving LF, CRLF, CR, and the absence of a final newline. `normalize_lf` explicitly maps each present terminator to LF while retaining an absent terminator. No Unicode normalization, case folding, whitespace trimming, tab expansion, or locale transformation occurs implicitly.

Input SHA-256 covers the original bytes. For `TextSource`, the digest covers its strict UTF-8 encoding. Provenance separately records any explicit decoding and newline transformation.

## Edit and hunk semantics

The internal edit script contains `equal`, `delete`, and `insert`. A replacement is represented canonically as deletion followed by insertion. This ordering also governs hunk serialization and terminal rendering.

`TextHunk` is the Phase 1 built-in change with `kind="text_hunk"`. Locations use one-based line numbers and half-open spans expressed as `start_line + line_count`. A zero-length insertion or deletion anchor may point one position after the last line. Hunk context is presentation data selected only after the full edit script is known; changing context does not change relation, verdict, metrics, or total change count.

The strict default policy yields `equal/pass` when the script contains no insertion or deletion and `different/fail` otherwise. Phase 1 has no policy that yields `warn` or `degraded` fidelity, but it implements and serializes those schema-v1 values for compatibility.

## Myers algorithm contract

The algorithm identifier is:

```text
text.myers.linear_space.v1
```

It uses the Myers middle-snake divide-and-conquer algorithm, targets a shortest insertion/deletion edit script, and uses `O(N + M)` auxiliary space. The implementation must:

1. remove common prefixes and suffixes before solving each remaining region;
2. use an explicit task stack so Python recursion depth is not an input limit;
3. apply a fixed deletion-first tie-break whenever shortest paths are otherwise equivalent;
4. emit operations in stable source order;
5. avoid `difflib.SequenceMatcher` or any other semantic fallback when the budget is exhausted.

The normal result is independent of wall-clock time. Work accounting is deterministic: one unit is charged for every frontier state advanced and one unit for every `TextLine` equality check used by prefix trimming, suffix trimming, or snake extension. The implementation checks the limit before charging the next unit. Both the configured limit and actual charged units are recorded in comparison provenance.

Exhausting the work budget returns `FailedOutcome` with code `compare_resource_limit`; it never returns `partial` and never substitutes a non-shortest algorithm. Only trimming fully computed change details after comparison may produce `changes.completeness="truncated"`.

## Fixed resource defaults

Phase 1 defaults are:

| Resource | Default |
| --- | ---: |
| Bytes per input | 16 MiB |
| Lines per input | 200,000 |
| Strict UTF-8 bytes per normalized line | 1 MiB |
| Myers deterministic work units | 5,000,000 |
| Returned change items | 10,000 |
| Serialized change payload | 4 MiB |
| Hunk context | 3 lines |

Input limits are checked while reading so path inputs are not loaded without bounds. Line limits are checked during splitting. The encoded-line limit is measured after the selected newline normalization using strict UTF-8. Change-item and payload limits are applied only after the full script and total counts are known; reaching either produces deterministic source-order truncation with complete item boundaries. Payload usage is the sum of each retained complete change encoded independently as canonical compact schema-v1 JSON: `ensure_ascii=false`, `allow_nan=false`, sorted keys, and compact separators. The surrounding array, outcome envelope, and pretty-printing whitespace are excluded.

## Verification contract

All Phase 1 commits must keep these commands passing once introduced:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy platydiff tests
python -m pytest
python -m build
```

The text algorithm suite must include:

- a dynamic-programming LCS oracle for shortest edit distance on small inputs;
- exact reconstruction of the target from every emitted edit script;
- differential testing against a simple trace-storing Myers reference implemented only in tests;
- equal, empty, wholly different, single-change, repeated-line, reordered, and missing-final-newline cases;
- fixed deletion-first tie-break snapshots and repeated-run determinism;
- exact work-budget boundary tests;
- representative peak-memory checks for wholly different inputs, repeated lines, and large edit distance.

Contract tests must cover every outcome variant, serialization round trips, unknown schema and kind rejection, tagged non-finite metrics, change completeness invariants, safe artifact URIs, and stable ordering. CLI integration tests must cover both routes, both renderers, every exit code, malformed options, source and decoding failures, output truncation, and traceback suppression.

## Later phases and callback gates

Later phases form an accepted roadmap, not automatic authorization to implement them:

1. **Phase 2:** automatic detection, capability resolution, and a binary comparator.
2. **Phase 3:** third-party entry-point discovery, a plugin SDK, and a compatibility suite.
3. **Phase 4:** JSON/YAML and table/array comparison.
4. **Phase 5:** image comparison.
5. **Phase 6:** source-code and PDF comparison.
6. **Phase 7:** audio and video comparison.

Before each phase begins:

- every new modality must define its `CompareSpec`, `Change`, metrics, artifacts, equivalence relation, policy defaults, and failure semantics;
- Phase 2 must settle detection ambiguity, candidate ranking, confidence reporting, and the capability-request model;
- Phase 3 must use lessons from the internal text and binary registries before publishing discovery or plugin contracts;
- optional backends must define availability, degradation, version provenance, licensing, and deterministic fallback behavior;
- schema, enum, default-algorithm, or serialized-field changes require compatibility tests and migration guidance;
- the phase must identify its own commit/API gates and receive explicit implementation approval.

## Consequences

The first executable release remains intentionally narrow but exercises the same outcome, provenance, serialization, policy, rendering, and resource-control boundaries that later modalities need. Deferring detection and public plugins keeps their contracts revisable until two internal capabilities provide evidence. Linear-space Myers and deterministic budgets make resource behavior observable without allowing a silent change of comparison meaning.
