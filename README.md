# Platydiff

[Chinese documentation](README_zh.md)

`platydiff` is an extensible multimodal diff engine for scientific data,
experimental regression testing, and competition workflows. PR #3 contains a
Phase 1 implementation candidate that compares explicitly selected text
sources through a typed Python API or CLI and emits terminal output or the
schema-v1 JSON outcome contract. It is not shipped until merged and released.

Other modalities and automatic detection remain planned. Platydiff never
guesses that an input is text from its extension, content, or Python type.

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
`unavailable` or `failed` outcome. Structured consumers should inspect outcome
and problem codes rather than infer details from the shell code.

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

## Candidate and planned capabilities

Included in the Phase 1 candidate in PR #3:

- Python 3.12+ library and `platydiff` CLI;
- schema-v1 `CompareOutcome` and `DiffResult` JSON serialization;
- strict line-oriented text comparison;
- deterministic linear-space Myers insert/delete edit scripts;
- terminal and JSON renderers with bounded change details.

Planned, not implemented:

- automatic format or encoding detection and binary comparison;
- public plugin discovery or SDKs;
- JSON/YAML, tables, arrays, images, source code, PDF, audio, and video;
- stdin, directories, recursive comparison, and configuration files;
- color, HTML, JUnit, and patch artifacts.

See [the architecture](docs/architecture.md) for the broader design direction.
Algorithm provenance and known constraints are recorded in
[the algorithm references](docs/algorithm-references.md).

## License

Platydiff is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
