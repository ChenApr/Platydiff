# Changelog

All notable changes to Platydiff are documented in this file.

## Unreleased

### Added

- Python 3.12 package and `platydiff` console entry point.
- Schema-v1 comparison outcomes, completed results, validation, and strict JSON
  serialization from RFC 0001.
- Explicit path, bytes, and text sources plus `TextCompareSpec`.
- Deterministic linear-space Myers text comparison with resource accounting.
- Equivalent `compare --type text` and `text` CLI routes with terminal and JSON
  output.
- Non-overlapping deterministic hunk context and explicit change-truncation
  limit reasons. `changes.limit_reason` is an additive optional schema-v1 field:
  older readers ignore it and current readers accept candidate payloads where it
  is absent.
- Safe separation of rendered outcomes on stdout from parser and renderer
  failures on stderr.

Later modalities, automatic detection, and public plugin discovery remain
planned and are not part of this change.
