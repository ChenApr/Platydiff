# Platydiff

[Chinese documentation](README_zh.md)

`platydiff` is an extensible multimodal diff engine for scientific data,
experimental regression testing, and competition workflows. Phases 1 and 2
implement explicit text, exact binary, and opt-in automatic text/binary
comparison through a typed Python API or CLI. Results use the schema-v1 outcome
contract. The implementation remains unreleased.

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

## Implemented and planned capabilities

Implemented in Phases 1 and 2:

- Python 3.12+ library and `platydiff` CLI;
- schema-v1 `CompareOutcome` and `DiffResult` JSON serialization;
- strict line-oriented text comparison;
- deterministic linear-space Myers insert/delete edit scripts;
- terminal and JSON renderers with bounded change details.
- bounded deterministic text/binary detection and internal capability resolution;
- collision-safe exact binary comparison with payload-free change spans.

Planned, not implemented:

- public plugin discovery or SDKs;
- JSON/YAML, tables, arrays, images, source code, PDF, audio, and video;
- stdin, directories, recursive comparison, and configuration files;
- color, HTML, JUnit, and patch artifacts.

See [the architecture](docs/architecture.md) for the broader design direction.
Algorithm provenance and known constraints are recorded in
[the algorithm references](docs/algorithm-references.md).

## License

Platydiff is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
