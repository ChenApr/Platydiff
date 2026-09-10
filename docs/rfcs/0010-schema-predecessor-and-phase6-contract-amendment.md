# RFC 0010: Schema Predecessor and Phase 6 Contract Amendment

[Chinese documentation](0010-schema-predecessor-and-phase6-contract-amendment_zh.md)

- Status: Proposed
- Date: 2026-09-10
- Owners: Platydiff maintainers
- Implementation owner: unassigned pending human approval

## Summary and authorization boundary

This RFC is a proposed cross-RFC amendment for a schema predecessor
contradiction found before Phase 5, Phase 6, or Phase 7 schema implementation
starts. It proposes decisions only. It does not mark any decision Accepted,
does not authorize code, does not change public schema behavior, and does not
start implementation of structured data, image, source-code, PDF, audio, video,
SDK v2, backend workers, artifacts, automatic detection, or UI work.

The recommended decision is to treat the missing YAML, table, and array
schema-v3 contract surface on `main` as a Phase 4 code defect, not as proof that
the accepted RFC 0006 contract was wrong. A correction gate must land before
schema v4 image, schema v5 source/PDF, schema v6 audio, or any later video
successor can use v3 as a stable predecessor.

## Evidence

At `origin/main` `7907fbf`, the implemented schema-v3 code exposes
`JsonCompareSpec` and `StructuredChange`. It does not expose
`YamlCompareSpec`, `TableCompareSpec`, `ArrayCompareSpec`, `TableChange`, or
`ArrayChange` as implemented schema-v3 public models.

RFC 0006 is Accepted and says the schema-v3 closed unions include:

```text
CompareSpec | JsonCompareSpec | YamlCompareSpec | TableCompareSpec | ArrayCompareSpec
TextHunk | BinarySpan | StructuredChange | TableChange | ArrayChange | ExtensionChange
```

RFC 0006 also says schema-v3 fields and fixtures become public after P4-A1 is
implemented. Its later P4-A2, P4-B1, and P4-B2 gates remain independently
authorized and unimplemented, while their commit plans suggest YAML, table, and
array modality work happens later.

RFC 0007 requires a hard predecessor audit: if the merged P4-A1 schema differs
from RFC 0006, Phase 5 stops and the RFC is amended before image models ship.
RFC 0008 assigns Phase 6 source/PDF to schema v5 and includes the full RFC 0006
v3 closed union as a predecessor. Therefore P6-C0 cannot be implemented
uniquely from current `main`: implementers can follow either the accepted RFC
0006 union or the actually implemented JSON-only surface, and those are not the
same contract.

The repository remains unreleased, which gives maintainers room to correct the
pre-release schema implementation. It does not make closed-union drift harmless:
once a writer, reader, migration fixture, downstream schema, or release treats a
closed union as a predecessor, extending that same schema version creates
ambiguous compatibility evidence.

## Proposed decisions

| ID | Recommended decision | Alternative not selected |
| --- | --- | --- |
| SP1 | Recognize the schema-v3 predecessor mismatch as blocking for P5-A1, P6-C0, P7-A1, and later video schema work until human approval resolves it. | Let downstream schemas choose whichever v3 definition is convenient. |
| SP2 | Choose option A: treat the missing YAML/table/array schema-v3 contracts as a Phase 4 code defect and define correction gate P4-C1 before schema v4. | Treat current JSON-only code as the complete v3 contract without amending accepted RFCs. |
| SP3 | Keep the accepted global allocation: v3 structured data, v4 image, v5 source/PDF, v6 audio, and a later video successor. | Renumber accepted image/source/PDF/audio allocations because P4-A1 shipped an incomplete v3 surface. |
| SP4 | State that a closed union may not be extended after it has shipped as public release evidence or after a successor has depended on it; before release, P4-C1 may correct the incomplete v3 implementation to match accepted RFC 0006. | Allow same-version closed-union additions whenever a later gate wants them. |
| SP5 | Require downstream predecessor fixtures to prove the corrected v3 union before schema-v4, schema-v5, or schema-v6 writer fixtures are accepted. | Use design acceptance alone as predecessor compatibility evidence. |
| SP6 | Require a P6-C0 contract amendment before implementation to close the source lexical, PDF binary, coordinate, digest, identifier, problem, fact, and `compare()` behavior gaps below. | Let P6-C0 implementers infer missing public contract details from private code. |

## Alternatives

### A. Phase 4 correction gate before v4

Option A treats RFC 0006 as the correct accepted contract and current P4-A1
code as incomplete. The correction gate, P4-C1, adds the missing public
schema-v3 model, serializer, reader, migration, and fixture surface for
`YamlCompareSpec`, `TableCompareSpec`, `ArrayCompareSpec`, `TableChange`, and
`ArrayChange`. P4-C1 does not implement YAML, table, or array comparators; it
only makes the v3 closed union match the accepted contract so later gates have
one predecessor.

This is the recommended option because it preserves already accepted schema
allocations and keeps RFC 0006's structured-data contract intact. The
compatibility cost is still real: v3 fixtures already on `main` must be
expanded and revalidated before any v4/v5/v6 fixtures depend on them. The
project is unreleased, so this is a pre-release defect correction rather than a
public breaking change.

### B. Redefine v3 as JSON-only

Option B amends RFC 0006 to say schema v3 contains only `JsonCompareSpec` and
`StructuredChange`; YAML, table, and array contracts would move to future
global schema successors. This fits current code but weakens an accepted RFC
after implementation and forces maintainers to decide where those structured
modalities live. They could be assigned after audio/video, or grouped into a
new structured-data successor, but either choice changes the predecessor graph
for RFC 0007, RFC 0008, and RFC 0009.

Because the project is unreleased, option B is technically possible. It is not
recommended unless humans decide the accepted RFC 0006 contract was too broad.
It requires explicit migration notes, updated RFC 0006 status text, amended
Phase 5/6/7 predecessor language, and compatibility tests proving that old
pre-release v3 JSON fixtures remain valid while the removed YAML/table/array
names are not accepted as v3.

### C. Add a secondary schema-extension mechanism

Option C keeps numeric schema v3 as JSON-only but adds a separate structured
contract revision or capability-extension namespace for YAML, table, and array.
This avoids renumbering but creates two version axes. It also weakens the
closed-union discipline used by RFC 0006 through RFC 0009: a reader would need
both `schema_version` and extension membership to know what built-in spec and
change names are legal.

This option is coherent only if the project deliberately moves away from
schema-versioned closed unions. It is not recommended for the current
pre-release codebase.

## P4-C1 correction gate

If option A is accepted, P4-C1 is the required correction gate before any schema
v4/v5/v6 implementation gate:

1. `fix(core): complete schema-v3 structured contract models`
2. `fix(core): complete schema-v3 reader writer and migration validation`
3. `test(core): add schema-v3 YAML table array contract fixtures`
4. `docs(rfc): record schema-v3 predecessor correction evidence`

Gate: independently authorized from updated `main`; no YAML, table, or array
comparator behavior is implemented; no CLI route, detector, plugin SDK,
artifact, or renderer feature is added; `git diff --check`, formatting, lint,
strict type checking, complete tests, schema-v1/v2/v3 compatibility fixtures,
unknown-kind rejection, and public-export checks pass. P5-A1, P6-C0, P7-A1, and
later video schema gates must wait for P4-C1 or for an accepted alternative in
this RFC.

## P6-C0 contract amendment

P6-C0 remains blocked even after the v3 predecessor decision unless the
following public contract details are accepted. These are proposed decision IDs
for the Phase 6 amendment, not implementation authority.

| ID | Proposed decision | Alternative not selected |
| --- | --- | --- |
| P6C0-1 | Represent source `lexical_text` differences with a source-specific change kind that embeds RFC 0002 text ranges and also records source coordinate context; do not reuse bare `TextHunk` as a source-code change. | Make lexical source output indistinguishable from plain text output. |
| P6C0-2 | Represent PDF binary differences with a PDF-specific binary-span change discriminator that records PDF document identity plus zero-based half-open byte ranges; do not reuse bare `BinarySpan` without a PDF discriminator. | Let PDF binary view produce generic binary changes that renderers cannot distinguish from ordinary binary comparison. |
| P6C0-3 | Define coordinate bases and grammars normatively: bytes are zero-based half-open offsets; source line/column facts state encoding and whether columns are code-point or byte based; PDF page numbers, object references, stream ranges, and rendered pixel rectangles each have one grammar; rendered pixel rectangles are zero-based half-open in the explicitly declared raster space. | Leave coordinate base and grammar to each backend. |
| P6C0-4 | Define render bounds in the schema contract before any renderer backend: maximum pages, rendered pages, pixels per page, decoded bytes, temp bytes, backend seconds, worker output bytes, peak RSS, concurrent workers, and spawned process count all have finite accounting rules. | Put render limits only in backend documentation. |
| P6C0-5 | Define exact digest framing with domain strings, canonical byte framing, hash algorithm, and normative test vectors for source facts, PDF facts, rendered-page facts, and change payloads. | Reuse informal prose references to RFC 0006 digests without vectors. |
| P6C0-6 | Reserve stable lowercase ASCII IDs for summary keys, resource counters, transformation IDs, comparator IDs, algorithm IDs, metric names, and problem codes before any source/PDF writer ships. | Let implementations mint IDs opportunistically. |
| P6C0-7 | Define `pdf_encrypted` as a structured problem code with explicit status mapping: missing password or unsupported encryption is `unavailable` when policy permits unsupported capability reporting, and `failed` when selected comparison cannot proceed after validation; problem details must include only safe fields. | Collapse encryption into generic decode failure. |
| P6C0-8 | Define worker problem details for timeout, resource exhaustion, crash, protocol violation, invalid output, stderr overflow, temp overflow, decoded-output overflow, RSS overflow, and spawn-limit overflow; each has a stable status and safe detail shape. | Return backend-specific strings as problem details. |
| P6C0-9 | Define fact presence invariants: every selected successful view emits its required facts, metrics, summaries, resources, and transformations; every unselected view is absent or explicitly null as specified; failed or unavailable views do not fabricate empty facts. | Permit partial facts without a schema-level invariant. |
| P6C0-10 | Keep P6-C0 models/serialization only: public `compare()` and CLI behavior for source/PDF remain unavailable until P6-S1 or P6-P1a. P6-C0 fixtures may construct unavailable outcomes directly for reader/writer validation but must not expose a runnable source/PDF comparator route. | Add `compare()` behavior that returns unavailable for source/PDF during P6-C0. |

## Migration and compatibility tests

Any accepted resolution must add tests for:

- exact v1/v2/v3 reader and writer compatibility, including unknown schema and
  unknown built-in kind rejection;
- canonical round trips for every accepted schema-v3 built-in spec and change
  name, even when comparator behavior is still gated;
- migration from v1/v2 to corrected v3 without changing legacy outcome meaning;
- predecessor fixture reuse by v4/v5/v6 gates without rewriting v3 bytes after
  those successor fixtures are accepted;
- P6-C0 source/PDF schema fixtures covering unavailable and failed outcomes,
  selected and unselected views, resource accounting, transformations,
  summaries, metrics, problem details, digest vectors, and coordinate examples;
- proof that P6-C0 does not add public `compare()` or CLI source/PDF behavior.

If option B or C is accepted instead of option A, the migration tests must also
prove that the removed or relocated YAML/table/array v3 names are rejected with
a stable problem and that successor allocations are documented before code.

## Required human decisions

Human reviewers must decide:

1. Is accepted RFC 0006 still the desired schema-v3 contract?
2. Should P4-C1 correct current code to match RFC 0006 before schema v4, or
   should RFC 0006 be amended to JSON-only v3?
3. May pre-release schema-v3 fixtures be expanded before any successor depends
   on them, and where is the no-later-extension line drawn?
4. Are the global allocations v4 image, v5 source/PDF, v6 audio, and later
   video successor still correct?
5. Are P6C0-1 through P6C0-10 the right contract decisions before P6-C0
   implementation starts?

Until those decisions are accepted, this RFC is only a proposal and no
downstream schema implementation should treat the current v3 predecessor as
settled.
