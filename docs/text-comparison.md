# Text comparison

[Chinese documentation](text-comparison_zh.md)

Phase 1 compares one explicit text source with another. It supports files,
owned bytes, and already-decoded strings without automatic format or encoding
detection.

## Python API

```python
from pathlib import Path

from platydiff import PathSource, TextCompareSpec, compare

outcome = compare(
    PathSource(Path("before.txt")),
    PathSource(Path("after.txt")),
    TextCompareSpec(),
)
```

`compare(before, after, spec)` always requires a `TextCompareSpec`. The outcome
is one of `CompletedOutcome`, `UnavailableOutcome`, or `FailedOutcome`; only a
completed outcome contains `DiffResult`. Use
`platydiff.core.dumps_outcome(outcome)` and
`platydiff.core.loads_outcome(payload)` for strict schema-v1 JSON round trips.

`DiffResult.relation`, `verdict`, `fidelity`, and change completeness are
independent. The strict Phase 1 policy produces `equal/pass` or
`different/fail`. A renderer presents those fields without recalculating them.

## CLI

```text
platydiff compare --type text [OPTIONS] BEFORE AFTER
platydiff text [OPTIONS] BEFORE AFTER
```

Both routes construct the same specification and use the same comparison and
rendering path. Options are:

| Option | Values or meaning | Default |
| --- | --- | ---: |
| `--format` | `terminal` or `json` | `terminal` |
| `--encoding` | `utf-8` or `utf-8-sig` | `utf-8` |
| `--newline` | `preserve` or `normalize_lf` | `preserve` |
| `--context-lines` | non-negative hunk context | `3` |
| `--max-input-bytes` | bytes per input | `16777216` |
| `--max-input-lines` | lines per input | `200000` |
| `--max-encoded-line-bytes` | strict UTF-8 bytes per normalized line | `1048576` |
| `--max-myers-work` | deterministic work units | `5000000` |
| `--max-change-items` | returned complete hunks | `10000` |
| `--max-change-payload-bytes` | serialized returned hunk bytes | `4194304` |

All limits accept zero. Invalid values are usage errors and exit with `2`
without emitting an outcome.

## Text semantics

Byte and path inputs decode strictly. `utf-8` retains a BOM as content;
`utf-8-sig` explicitly removes it. Invalid bytes return `failed/decode_error`.
The pipeline recognizes LF, CRLF, and CR terminators and separately represents
line content and terminator. A missing final terminator remains observable.

`preserve` compares terminators exactly. `normalize_lf` changes each present
terminator to LF but does not add a missing terminator. There is no implicit
Unicode normalization, case folding, whitespace trimming, tab expansion, or
locale-dependent transformation.

The algorithm `text.myers.linear_space.v1` emits a shortest insert/delete edit
script with deletion-first ties. Replacements are always a deletion followed
by an insertion. It uses linear auxiliary space, an explicit task stack, and a
deterministic work budget rather than a wall-clock timeout or semantic
fallback.

Hunks use one-based line numbers and `start_line + line_count` spans. Context
is detail only: changing it cannot change the relation, verdict, metrics, or
total hunk count. Item and payload limits are applied after the complete edit
script and all totals are known. Truncation retains only complete hunks in
source order, adds `change_details_truncated`, and does not change the result's
relation, verdict, or fidelity.

## Failures and provenance

Expected source, decoding, and resource failures return a schema-v1
`FailedOutcome` without a placeholder or partial `DiffResult`. Exhausting the
Myers budget uses `compare_resource_limit` and never falls back to
`SequenceMatcher` or emits a partial result. The CLI maps otherwise unhandled
exceptions to a path-safe `internal_error` and suppresses tracebacks by
default; `KeyboardInterrupt`, `SystemExit`, and `MemoryError` remain
interruptions rather than domain outcomes.

Completed result provenance includes input roles, source kinds, byte sizes,
SHA-256 digests, the fully normalized specification, explicit transformations,
algorithm and implementation versions, configured limits, and deterministic
work counts. Absolute source paths and input contents are not serialized.

## Deferred capabilities

Automatic detection, binary and other modality comparators, public plugin
discovery, stdin and directory input, configuration files, and color, HTML,
JUnit, and patch output remain planned. Their roadmap entries do not imply
implementation.
