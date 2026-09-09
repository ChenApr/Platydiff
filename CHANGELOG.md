# Changelog

All notable changes to Platydiff are documented in this file.

## Unreleased

### Added

- Implemented the Phase 2 bounded automatic text/binary detector, deterministic
  built-in capability resolution, exact streaming binary comparator, Python
  contracts, and CLI routes.
- Implemented Phase 3 gate P3-A with immutable SDK-v1 plugin manifests,
  capability/dependency/platform inventory, and explicit allowlisted entry-point
  discovery with deterministic validation, negotiation, and conflict quarantine.
- Implemented Phase 3 gate P3-B with SDK-v1.1 detector/comparator handles,
  immutable host-owned execution, schema-v2 provider and attempt provenance,
  dual-version readers, and a typed schema-v1-to-v2 upgrader.
- Recorded the terminal/HTML-first human review UI roadmap without authorizing
  UI implementation or scheduling.
- Python 3.12 package and `platydiff` console entry point.
- Schema-v1 comparison outcomes, completed results, validation, and strict JSON
  serialization from RFC 0001.
- Explicit path, bytes, and text sources plus `TextCompareSpec`.
- Deterministic linear-space Myers text comparison with resource accounting.
- Canonical delete-then-insert ordering for every run of changed lines, so a
  shortest edit script that emits an insertion first still produces valid hunks.
- Equivalent `compare --type text` and `text` CLI routes with terminal and JSON
  output.
- Non-overlapping deterministic hunk context and explicit change-truncation
  limit reasons. `changes.limit_reason` is an additive optional schema-v1 field:
  older readers ignore it and current readers accept candidate payloads where it
  is absent.
- Safe separation of rendered outcomes on stdout from parser and renderer
  failures on stderr.

CLI plugin flags, third-party renderer invocation, compatibility receipts, and
later modalities remain planned.

### Changed

- Aligned plugin and dependency distribution-name validation and normalization
  with the PyPA name specification, including valid separator runs and strict
  full-string anchoring.
- Extended the unreleased schema v1 with `auto` and `binary` specifications,
  `binary_span` changes, and optional detection provenance. Existing explicit
  text payloads remain byte-for-byte compatible; pre-release Phase 1 readers
  had no forward-compatibility guarantee for the new closed-union kinds.
