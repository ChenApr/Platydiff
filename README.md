# Platydiff

[Chinese documentation](README_zh.md)

`platydiff` is an extensible multimodal diff engine for scientific data,
experimental regression testing, and competition workflows. Phases 1 and 2
implement explicit text, exact binary, and opt-in automatic text/binary
comparison through a typed Python API or CLI. Phase 3 adds immutable plugin
hosts, explicitly selected text/binary detector, comparator, and bounded
renderer execution, schema-v2 provider provenance, CLI opt-in flags, and a
compatibility receipt profile. The existing three-argument API and default CLI
remain built-in-only; legacy text/binary/auto calls keep schema v1, while the
explicit Phase 4 P4-A1 JSON path returns schema v3. The implementation remains
unreleased.

## Install for development

Platydiff requires Python 3.12 or newer and has no third-party runtime
dependencies.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Compare text from the CLI

The two commands below are equivalent:

```bash
platydiff compare --type text before.txt after.txt
platydiff text before.txt after.txt
```

Select exact schema-v1 JSON output with `--format json`:

```bash
platydiff text --format json before.txt after.txt
```

Exit code `0` means a completed `pass` or `warn`, `1` means a completed
`fail`, `2` is a command-line usage error with no outcome, and `3` is an
`unavailable` or `failed` outcome or a renderer failure. Successfully rendered
outcomes go to stdout; parser and renderer errors go to stderr. Structured
consumers should inspect outcome and problem codes rather than infer details
from the shell code.

## Compare text from Python

The specification is required and records every effective default in
provenance:

```python
from platydiff import TextCompareSpec, TextSource, compare

outcome = compare(
    TextSource("alpha\nbeta\n", label="before"),
    TextSource("alpha\ngamma\n", label="after"),
    TextCompareSpec(),
)

if outcome.kind == "completed":
    print(outcome.result.relation, outcome.result.verdict)
else:
    print(outcome.problem.code)
```

`PathSource`, `BytesSource`, and `TextSource` are supported. Byte and path
sources use strict UTF-8 by default; choose `utf-8-sig` explicitly to remove a
BOM. LF, CRLF, CR, and a missing final newline remain distinct unless
`normalize_lf` is explicitly selected. Unicode, whitespace, tabs, case, and
locale are never normalized implicitly.

See [the text comparison guide](docs/text-comparison.md) for all options,
resource limits, result semantics, and failure behavior. The authoritative
contracts are [RFC 0001](docs/rfcs/0001-comparison-outcome-and-diff-result.md)
and [RFC 0002](docs/rfcs/0002-development-phases-and-text-slice.md).

## Compare binary data or detect text/binary

```bash
platydiff binary before.bin after.bin
platydiff compare --type binary before.bin after.bin
platydiff compare --type auto before.dat after.dat
```

Automatic detection is never implicit: omitting `--type` is a usage error.
Detection inspects only a bounded prefix; binary comparison streams bounded
chunks and compares actual bytes. See the
[automatic and binary guide](docs/binary-comparison.md).

## Compare JSON explicitly

```bash
platydiff json before.json after.json
platydiff compare --type json --format json before.json after.json
```

JSON comparison is strict RFC 8259 and semantic: object member order and string
escape spelling are ignored, arrays remain positional, and the default
`--number-mode value` makes `1`, `1.0`, and `1e0` equal. Select
`--number-mode lexical` to compare valid number tokens exactly. Returned
schema-v3 changes use canonical JSON Pointers and typed facts. Use
`--detail digest_only` before comparison to omit value facts; paths, input
hashes, counts, and reproducible evidence digests remain pseudonymous metadata,
not confidential redaction.

JSON is explicit-only and built-in-only. It is not selected by `auto`, and JSON
commands reject plugin, detector, comparator, and plugin-renderer flags before
discovery. See [the JSON comparison guide](docs/json-comparison.md) for the full
contract, limits, schema migration, and failure behavior.

## Enable a plugin explicitly

Plugins are never loaded by default. Repeat `--plugin` to allowlist exact
installed plugin IDs, then pin any third-party capability by its complete ID:

```bash
platydiff text --plugin org.example.scidiff \
  --comparator org.example.scidiff.text_exact before.txt after.txt

platydiff text --plugin org.example.scidiff \
  --renderer org.example.scidiff.safe_text \
  --renderer-media-type "text/plain; charset=utf-8" \
  --max-render-bytes 1048576 before.txt after.txt
```

`--detector` applies only to `compare --type auto`. Enabling a plugin without
pinning a capability never lets it outrank a built-in. Any plugin-enabled or
capability-pinned comparison uses schema v2; a command with no plugin flags
retains schema v1. An explicitly selected renderer receives only the validated
outcome, presentation options, and a bounded host sink. Its text or bytes are
written to stdout without fallback; failure leaves stdout empty, reports a safe
message on stderr, and exits `3`.

## Implemented and planned capabilities

Implemented in Phases 1, 2, the P3-A/P3-B/P3-C plugin gates, and P4-A1:

- Python 3.12+ library and `platydiff` CLI;
- schema-v1 `CompareOutcome` and `DiffResult` JSON serialization;
- strict line-oriented text comparison;
- deterministic linear-space Myers insert/delete edit scripts;
- terminal and JSON renderers with bounded change details;
- terminal and JSON renderers for schema-v1, schema-v2, and schema-v3 outcomes;
- bounded deterministic text/binary detection and internal capability resolution;
- collision-safe exact binary comparison with payload-free change spans;
- immutable SDK-v1 manifests and capability/dependency/platform inventory;
- explicit entry-point discovery, exact allowlists, version/feature negotiation,
  and deterministic conflict quarantine;
- explicitly pinned SDK-v1.1 detector/comparator handles with host-owned bounded
  source access and lifecycle stages, including exact built-in comparator pins
  for automatic comparisons, strict declared-backend provenance, and host-side
  output-limit/exact-semantics validation;
- schema-v2 provider, attempt, and plugin-host provenance plus a typed v1-to-v2
  upgrader. Legacy `PluginHost.compare()` calls return schema v2; schema-v3 JSON
  intent is rejected at resolution because SDK v1.1 remains text/binary-only;
- bounded third-party renderer handles, explicit CLI plugin/capability flags,
  deterministic compatibility receipts, and a cross-boundary failure-isolation
  profile.
- schema-v3 outcomes, explicit v1/v2-to-v3 migration, typed structured changes,
  strict bounded JSON decoding, value/lexical number semantics, JSON Pointer
  alignment, deterministic evidence digests, and explicit Python/CLI JSON routes.

Planned, not implemented:

- YAML, tables, arrays, images, source code, PDF, audio, and video;
- stdin, directories, recursive comparison, and configuration files;
- color, HTML, JUnit, and patch artifacts.

See [the architecture](docs/architecture.md) for the broader design direction.
See [the plugin SDK guide](docs/plugin-sdk.md) for the implemented Phase 3 boundary.
Algorithm provenance and known constraints are recorded in
[the algorithm references](docs/algorithm-references.md).

## License

Platydiff is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
