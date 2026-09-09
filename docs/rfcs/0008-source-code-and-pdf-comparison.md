# RFC 0008: Source Code and PDF Comparison

[Chinese documentation](0008-source-code-and-pdf-comparison_zh.md)

- Status: Proposed
- Date: 2026-09-10
- Owners: Platydiff maintainers
- Implementation owner: unassigned pending separate implementation authorization

## Summary and authorization boundary

This RFC proposes Phase 6 contracts for explicit source-code and PDF
comparison. It is design work only. It does not authorize source-code or PDF
implementation, dependency changes, SDK v2, automatic detection, UI work,
artifact generation, optional backend installation, or any code changes.

Source code and PDF comparison are grouped as Phase 6 roadmap work because both
need heavyweight parsing backends and richer structural facts, but they are not
one implementation gate. Source code and PDF have different equivalence
relations, backends, security profiles, artifacts, and dependency risks, so this
RFC splits them into independently authorized delivery gates. A later human
approval may accept one, both, or neither set of gates.

All behavior remains explicit-only. A caller must choose a source-code or PDF
spec directly. Existing `AutoCompareSpec` remains text/binary-only unless a
successor to RFC 0003 accepts new detection semantics.

## Evidence ledger

| Current evidence at `origin/main` `cbc7e36` | Phase 6 constraint |
| --- | --- |
| RFC 0001 separates failed/unavailable execution outcomes from completed `DiffResult` facts. | Parser, backend, resource, encryption, sandbox, and rendering failures must not become empty or synthetic differences. |
| RFC 0002 requires each new modality to define spec, changes, metrics, artifacts, equivalence relation, policy, failures, and gates before implementation. | This RFC records contracts and gates but does not start code. |
| RFC 0003 keeps automatic detection bounded and closed to text/binary. | Source/PDF do not participate in auto detection; no filename, MIME, grammar, or PDF magic probe changes existing auto behavior. |
| RFC 0003 snapshot paths own bounded replay, hashing, mutation checks, and safe labels. | Source/PDF gates must revalidate the snapshot implementation before relying on it; concurrent Phase 4/5 work is not evidence. |
| RFC 0004 makes renderers and UI consume validated outcomes without rereading sources or recomputing facts. | Source/PDF renderers may present validated facts and inert artifact refs only; page images and heatmaps need an artifact gate. |
| RFC 0005 implements SDK v1.1 for text/binary detector, comparator, and renderer handles only. | Source/PDF plugin comparators require an explicit SDK-v2 callback and cannot be added through SDK v1.1. |
| RFC 0006 accepts schema v3 for structured-data built-in specs and changes, but its gates remain unimplemented. | Phase 6 may extend schema v3 only after revalidating its actual implementation state; if v3 has shipped, a schema successor may be required. |
| Runtime dependencies are currently zero and PDF/source backends are only architecture-level plans. | Tree-sitter, PDF parsers, renderers, fonts, and subprocess tools need separate dependency, license, platform, and security review. |

This ledger is evidence for design constraints, not proof that any future
backend, parser, artifact writer, or schema migration works.

## Goals and non-goals

Phase 6 goals are:

- explicit source-code specs with visible language, parser, normalization,
  alignment, relation, and resource choices;
- distinct lexical/text, syntax-tree/structural, and semantic claim relations;
- stable source-code node coordinates, change operations, metrics, provenance,
  and deterministic fixture corpora;
- explicit PDF specs with separately named binary, extracted-text,
  object/metadata, and rendered-page views;
- PDF backend boundaries for parsing, text extraction, rendering, sandboxing,
  timeouts, resource limits, and hostile document features;
- schema compatibility with v1, v2, and accepted v3 migration rules;
- clear SDK-v2, artifact, detection, and UI callback gates.

Phase 6 does not include:

- automatic source-code language detection or PDF detection;
- text fallback after source-code or PDF parser failure;
- semantic equivalence claims that require executing code, type checking,
  macro expansion, program analysis, OCR, or accessibility-tree inference;
- source-code formatting, linting, patch generation, rename detection, blame,
  repository traversal, generated-code exclusion, or build-system integration;
- PDF password prompting, remote font fetching, JavaScript execution, action
  execution, embedded-file extraction, OCR, accessibility tags, reflowed layout,
  or form filling;
- source/PDF plugin execution through SDK v1.1;
- HTML, TUI, desktop, local-web, page-image, heatmap, or downloadable artifact
  implementation.

## Proposed decisions

The following stable IDs are the human decision list for this proposal. They
are not accepted until a reviewer explicitly approves them.

| ID | Proposed decision | Alternative not selected |
| --- | --- | --- |
| P6X1 | Keep source-code and PDF comparison explicit-only; existing auto remains text/binary. | Add source/PDF candidates to RFC 0003 detection without defining ambiguity and attribution. |
| P6X2 | Use schema v3 for Phase 6 built-in spec/change variants only if v3 is still unreleased and revalidated at implementation start; otherwise require a schema successor. | Extend v1/v2 closed unions or assume RFC 0006 implementation details before they exist. |
| P6X3 | Reject source/PDF plugin comparators under SDK v1.1; require SDK v2 before third-party source/PDF modalities. | Let plugin installation introduce source/PDF specs or built-in change kinds. |
| P6X4 | Authorize source-code and PDF implementation gates independently. | Treat Phase 6 as one batch because both need parsers. |
| P6X5 | Keep RFC 0004 artifact/UI work separate; Phase 6 facts may reference artifacts only after an artifact writer gate. | Let PDF rendering implicitly create page images or HTML reports. |
| P6X6 | Mark every code-dependent assumption as a revalidation gate, including P4-A1 and future Phase 5 work. | Treat concurrent unmerged work as design evidence. |
| P6X7 | Forbid fallback that changes comparison relation after a parser/backend starts. | On failure, silently fall back to text, binary, another parser, another renderer, or approximate semantics. |
| SC1 | Add an explicit `SourceCodeCompareSpec` with required `language` and `relation` fields. | Infer language from suffix/content or reuse `TextCompareSpec`. |
| SC2 | First source languages are `python` and `javascript`; `typescript`, `c`, `cpp`, `rust`, `go`, `java`, notebooks, templates, and generated-code policies are deferred. | Start with every grammar available from a backend package. |
| SC3 | Separate `lexical_text`, `syntax_tree`, and future `semantic` relations; Phase 6 first gates do not claim runtime semantic equivalence. | Report all source-code results as one generic code equality relation. |
| SC4 | Parser errors use explicit error-recovery policy: `reject` by default, optional `recover` only if facts are marked degraded and recovery nodes are reported. | Hide recovery nodes or compare a best-effort tree as full fidelity. |
| SC5 | Comments and formatting are comparison dimensions unless a named normalization explicitly elides or classifies them. | Treat formatting and comments as irrelevant by default. |
| SC6 | Unicode scalars, byte encoding, newline policy, BOM, tabs, and escapes are visible; no Unicode normalization, case folding, or locale transform is implicit. | Normalize source text before parsing without recording it. |
| SC7 | Macros, preprocessing, imports, generated code, and build configuration are outside first gates and must not be simulated. | Invoke compilers, build tools, package managers, or preprocessors inside source comparison. |
| SC8 | AST alignment uses stable node paths and deterministic tie-breaking; insert/delete/update/move are distinct observations, not patches. | Depend on backend object identity or unstable traversal order. |
| SC9 | Tree-sitter is the candidate optional backend, but its grammar versions, wheel/source distribution, native build, platform, license, and security profile must be reviewed per gate. | Add a parser dependency as a default runtime dependency. |
| SC10 | Source-code corpora must be synthetic or explicitly licensed and cover malformed, adversarial, Unicode, formatting, comments, moves, and limits. | Copy real project source fixtures without provenance. |
| PDF1 | Add explicit `PdfCompareSpec` views: `binary`, `extracted_text`, `objects_metadata`, and `rendered_pages`. | Collapse PDF comparison into one PDF equality bit. |
| PDF2 | Binary, extracted-text, object/metadata, and rendered-page equivalence are independent relations with separate metrics and evaluations. | Let a visually equal render override object/text differences or vice versa. |
| PDF3 | Encrypted PDFs without an accepted password contract are unsupported; no prompting or password storage occurs in first gates. | Prompt interactively, store passwords in specs, or fall back to binary. |
| PDF4 | Embedded files, JavaScript, launch actions, network actions, and form actions are inert facts or explicit unsupported features; they are never executed or extracted by default. | Execute or dereference active document content during comparison. |
| PDF5 | PDF parser, text extractor, and page renderer are separate bounded backends with version provenance and failure isolation. | Use one monolithic backend and hide which view failed. |
| PDF6 | External PDF tools, if selected, run with argument arrays, no shell, bounded temp dirs, timeouts, output limits, and no network. | Let a backend-specific command line manage security implicitly. |
| PDF7 | Page, object, and text alignment are deterministic and view-specific; unavailable/degraded/failure states remain distinguishable. | Merge alignment failures into content changes. |
| PDF8 | Rendered-page artifacts, thumbnails, and heatmaps require an RFC 0004-compatible artifact gate before any file is written or linked. | Emit page images as a side effect of comparison. |
| PDF9 | Fonts, encodings, transparency, page boxes, rotation, color, malformed xrefs, streams, and decompression bombs are explicit backend/resource cases. | Accept backend defaults without recording transformations and limits. |
| PDF10 | PDF fixtures must be generated or explicitly redistributable and include hostile and malformed cases without restricted documents. | Use arbitrary real-world PDFs as test corpus. |

## Schema and compatibility contract

If Phase 6 starts while schema v3 remains unreleased and the RFC 0006 v3 base
has been implemented, Phase 6 built-ins extend v3 as follows:

```python
CompareSpecV3 = (
    AutoCompareSpec | TextCompareSpec | BinaryCompareSpec
    | JsonCompareSpec | YamlCompareSpec | TableCompareSpec | ArrayCompareSpec
    | SourceCodeCompareSpec | PdfCompareSpec
)
ChangeV3 = (
    TextHunk | BinarySpan | StructuredChange | TableChange | ArrayChange
    | SourceCodeChange | PdfChange | ExtensionChange
)
```

If schema v3 has already been released with closed unions, Phase 6 must use a
schema successor instead of extending v3 in place. In either case:

- existing built-in text, binary, and auto calls keep schema v1;
- existing `PluginHost` text/binary calls keep schema v2;
- built-in source-code and PDF specs produce the new schema selected by the
  implementation gate, including failure before resolution;
- readers for the selected schema accept v1/v2/that schema;
- explicit v1/v2/v3 migration helpers preserve original facts and add only
  documented neutral defaults;
- no automatic downgrade exists for source-code or PDF outcomes;
- unknown built-in spec/change kinds remain invalid; unknown namespaced
  extension changes retain RFC 0001 behavior.

The selected schema must define stable JSON names for every new spec field,
change kind, metric, evaluation rule, transformation ID, backend identity, and
problem detail. Schema v3 assumptions are revalidated at the beginning of each
Phase 6 implementation gate because RFC 0006 is accepted but unimplemented at
the time of this RFC.

## Design-contract matrix

| Area | Source-code contract | PDF contract |
| --- | --- | --- |
| Public spec | `SourceCodeCompareSpec(language, relation, parser, normalization, alignment, detail_mode, limits)` | `PdfCompareSpec(views, passwords policy, backend choices, text/render/object options, artifact policy, limits)` |
| First relations | `lexical_text` and `syntax_tree`; `semantic` reserved and unavailable | `pdf.binary`, `pdf.extracted_text`, `pdf.objects_metadata`, `pdf.rendered_pages` |
| Default policy | changed items equal zero gives pass; otherwise fail | each selected view has its own zero-change evaluation; aggregate fail if any selected required view fails policy |
| Changes | `SourceCodeChange` with node path, operation, language, node kind, relation, digest/fact fields | `PdfChange` tagged by view with page/text/object/render coordinates and digest/fact fields |
| Metrics | changed nodes/tokens, parser errors, moved nodes, compared nodes, formatting/comment changes | changed bytes, text runs, object entries, metadata entries, rendered pixels/pages, backend warnings |
| Artifacts | none in first source gates | none until a separate artifact gate; rendered-page facts may include digests but no files |
| Backends | optional parser backend such as Tree-sitter; no default dependency until reviewed | separate parser/text/render backends; external subprocesses require sandbox rules |
| Fallback | no text fallback after source parsing starts | no fallback between PDF views or to binary unless binary view was explicitly selected |
| Plugin path | requires SDK v2 for source-code modality | requires SDK v2 for PDF modality |
| Verification | language fixtures, parser versions, AST paths, move tie-breaks, malformed/adversarial limits | generated PDFs, malformed/xref/stream cases, encryption, fonts, rendering determinism, sandbox limits |

## Source-code comparison contract

### Public intent

The proposed first public shape is:

```python
class SourceCodeCompareSpec:
    kind: Literal["source_code"] = "source_code"
    language: Literal["python", "javascript"]
    relation: Literal["lexical_text", "syntax_tree", "semantic"] = "syntax_tree"
    parser: SourceParserOptions = SourceParserOptions()
    normalization: SourceNormalizationOptions = SourceNormalizationOptions()
    alignment: SourceAlignmentOptions = SourceAlignmentOptions()
    detail_mode: Literal["facts", "digest_only"] = "facts"
    limits: SourceCodeResourceLimits = SourceCodeResourceLimits()
```

`language` is required in the first gate. File suffix, shebang, modeline,
package metadata, content probe, and backend parser guesses are not used for
language detection. A later source-detection RFC may define bounded language
probing, ambiguity, and attribution. Until then, a mismatched language produces
`failed/decode_error` or `unavailable/backend_unavailable` at the observed
stage; it does not retry with another language or `TextCompareSpec`.

`lexical_text` is line/token text comparison under source-specific tokenization
rules and must not claim syntax equivalence. `syntax_tree` compares parser tree
structure and selected token/comment facts. `semantic` is reserved for future
contracts that define runtime, type-system, macro, import, environment, and
toolchain boundaries; first gates return `unavailable/capability_unavailable`
for it.

### Parsing, normalization, and provenance

The normalized spec records every effective default. Comparison provenance must
record:

- input roles, source kinds, byte sizes, and hashes without absolute paths;
- language ID and versioned language profile;
- parser backend ID/version, grammar ID/version, ABI/API version, and platform;
- grammar source/provenance, license, distribution name/version, and whether a
  native extension or generated parser is used;
- parser error-recovery policy and observed recovery/error node counts;
- explicit transformations for encoding, newline policy, comment treatment,
  formatting treatment, literal normalization, and AST normalization;
- configured limits and deterministic actual work/resource counts.

Comments, whitespace, newlines, indentation, semicolons, delimiters, and
formatting trivia are comparison facts unless a named transformation changes
their role. A normalization may mark trivia as ignored only when the spec says
so and the transformation record is emitted. Unicode normalization, case
folding, locale-sensitive classification, tab expansion, newline conversion,
BOM removal, escape interpretation beyond the language grammar, and generated
code filtering are never implicit.

Macros, preprocessors, imports, package managers, code generators, notebooks,
templating languages, and build configuration are out of scope for first gates.
The comparator parses exactly the supplied source text under the selected
language grammar. It does not execute code, import dependencies, run formatters,
run linters, invoke compilers, or query a language server.

### AST coordinates, alignment, and changes

The comparator builds a private immutable tree. Backend node objects never enter
results. Each node has a stable path derived from the normalized tree:

```text
/root
/<child-kind>#<ordinal-among-siblings-of-kind>@<ordinal-among-all-siblings>
```

The exact wire syntax must be fixed by the implementation gate before release;
the required invariant is that paths are deterministic across repeated runs,
independent of backend object identity, and stable when unrelated siblings are
unchanged. Byte ranges and line/column spans may be recorded as facts, but node
paths are the primary structural coordinates.

```python
class SourceCodeChange:
    kind: Literal["source_code_change"]
    relation: Literal["lexical_text", "syntax_tree"]
    language: str
    operation: Literal["insert", "delete", "update", "move"]
    before_path: str | None
    after_path: str | None
    before_node_kind: str | None
    after_node_kind: str | None
    before_digest: str | None
    after_digest: str | None
    before_fact: SourceNodeFact | None
    after_fact: SourceNodeFact | None
```

Insert has only after coordinates. Delete has only before coordinates. Update
has both sides at an aligned node and records changed node kind, token, trivia,
or child-shape facts. Move has both sides and reports a node whose digest and
selected identity facts match under the move policy but whose path changed.
Moves are observations, not patch operations, and are emitted only when the
alignment algorithm can prove them deterministically. Otherwise the same change
is represented as delete plus insert.

Alignment is deterministic:

- exact node kind and digest matches are paired first;
- unique anchors outrank repeated anchors;
- parent-consistent matches outrank cross-parent matches;
- source-order tie-breaking is stable and documented;
- no semantic name binding, import resolution, or control-flow analysis is
  inferred;
- alignment failure caused by ambiguity or resource exhaustion is a failed
  outcome, not an approximate result.

### Source metrics and policy

The first source-code metric registry is proposed as:

| Metric name | Meaning | Unit | Direction | Aggregation |
| --- | --- | --- | --- | --- |
| `source.nodes_compared` | aligned syntax nodes visited | `items` | `neutral` | `count` |
| `source.nodes_changed` | insert/delete/update/move observations before truncation | `items` | `lower_is_better` | `count` |
| `source.tokens_changed` | lexical tokens changed under lexical relation | `items` | `lower_is_better` | `count` |
| `source.moves` | deterministic move observations | `items` | `lower_is_better` | `count` |
| `source.parser_errors` | parser errors or recovery nodes observed | `items` | `lower_is_better` | `count` |
| `source.ignored_trivia_items` | comments/formatting facts ignored by explicit normalization | `items` | `neutral` | `count` |

The default evaluation is `source.syntax_tree_equality` for `syntax_tree` and
`source.lexical_text_equality` for `lexical_text`, each observing its changed
item metric with operator `eq` and threshold zero. No default source policy
yields `warn`. Full fidelity requires no parser recovery unless the accepted
spec explicitly permits degraded recovery.

### Source resources and failures

```python
class SourceCodeResourceLimits:
    max_input_bytes: int = 16 * 1024 * 1024
    max_decoded_chars: int = 16 * 1024 * 1024
    max_tokens: int = 1_000_000
    max_nodes: int = 1_000_000
    max_depth: int = 256
    max_parser_errors: int = 0
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024
```

Limits are checked before allocating the next decoded slice, token, node,
alignment candidate, work unit, or returned change. Parser resource exhaustion
is `failed/resource_limit_exceeded` at `decoding`; comparison work
exhaustion is `failed/compare_resource_limit`; missing or incompatible parser
backend is `unavailable/backend_unavailable`; unsupported source kind is
`failed/source_type_unsupported`; malformed source under `reject` recovery is
`failed/decode_error`.

Adversarial tests must include extreme depth, width, token streams, repeated
subtrees, pathological move ambiguity, Unicode identifiers and controls, mixed
newlines, huge comments, unterminated literals, parser errors, and over-limit
inputs.

## Source-code backend gate

Tree-sitter is the candidate parser backend because the architecture already
names it as an optional source-code parser. This RFC does not choose a package
or version. A source backend gate must record:

- parser project, grammar project, grammar commit/version, generator version,
  runtime ABI version, and Python binding version;
- SPDX licenses for runtime, generated grammars, binary wheels, and build-time
  tools;
- wheel/source distribution size, native code, platform support, and Python
  version support;
- whether grammars are bundled, generated locally, or supplied by separate
  packages;
- security posture for malformed input, recursion, memory allocation, native
  crashes, and parser error recovery;
- failure isolation for native crashes or hangs, including whether an external
  worker process is needed before release.

If a backend cannot be bounded in-process, the implementation gate must either
use an externally supervised worker with an approved protocol or return
`backend_unavailable` for that platform. Dependency installation remains a user
environment concern; Platydiff does not fetch grammars or compilers.

## PDF comparison contract

### Public intent and views

The proposed first public shape is:

```python
class PdfCompareSpec:
    kind: Literal["pdf"] = "pdf"
    views: tuple[
        Literal["binary", "extracted_text", "objects_metadata", "rendered_pages"],
        ...
    ] = ("extracted_text",)
    text: PdfTextOptions = PdfTextOptions()
    objects: PdfObjectOptions = PdfObjectOptions()
    rendering: PdfRenderOptions = PdfRenderOptions()
    artifact_policy: Literal["none", "record_refs"] = "none"
    limits: PdfResourceLimits = PdfResourceLimits()
```

Each selected view produces separate summary counts, metrics, changes,
transformations, and evaluations. A combined PDF result may aggregate verdicts,
but it must never say that PDF files are simply equal without naming the views
under which that relation was established. Binary equality, extracted text
equality, object/metadata equality, and rendered-page equality are independent
relations.

The `binary` view reuses exact byte comparison semantics but records that it is
one selected PDF view. The `extracted_text` view compares decoded text runs,
logical order as reported by the extractor, page association, Unicode mapping,
and whitespace policy. The `objects_metadata` view compares trailer/catalog,
page tree, object dictionaries, stream metadata, embedded-file inventory, font
references, actions as inert facts, and document metadata under explicit ignore
rules. The `rendered_pages` view compares rasterized pages under explicit page
box, rotation, color, alpha, antialiasing, transparency, resolution, and
background policies.

### Hostile and unsupported PDF features

Encrypted PDFs are unsupported in the first gate unless a later decision accepts
a password API. Without that decision, encrypted input returns a failed or
unavailable outcome at the stage where encryption is detected, with no prompt,
no password field, and no fallback to text or rendering. Permission flags are
recorded only as inert metadata when readable without bypassing encryption.

Embedded files, JavaScript, launch actions, submit actions, remote go-to actions,
multimedia actions, rich media, and external streams are never executed,
downloaded, launched, or extracted by default. Object comparison may report
their bounded inert presence. Rendering backends must disable or ignore active
content where possible and record the backend policy.

Malformed xrefs, object streams, compressed streams, incremental updates,
linearized files, hybrid xref tables, missing fonts, custom encodings, ToUnicode
maps, ligatures, vertical writing, transparency groups, overprint, optional
content groups, annotations, forms, page boxes, rotation, crop/bleed/trim/art
boxes, and color profiles are explicit cases. Backend defaults must be recorded
as transformations or unavailable/degraded facts rather than hidden.

### PDF alignment and changes

```python
class PdfChange:
    kind: Literal["pdf_change"]
    view: Literal["binary", "extracted_text", "objects_metadata", "rendered_pages"]
    operation: Literal["insert", "delete", "update", "move"]
    before_coordinate: PdfCoordinate | None
    after_coordinate: PdfCoordinate | None
    before_digest: str | None
    after_digest: str | None
    before_fact: PdfFact | None
    after_fact: PdfFact | None
```

Coordinates are view-specific:

- binary uses byte offsets and lengths from `BinarySpan`;
- extracted text uses page number, extractor text-run ordinal, and bounded text
  span facts;
- objects/metadata uses object number/generation where stable, plus canonical
  dictionary path or metadata key;
- rendered pages use one-based page number, selected page box, pixel rectangle,
  and raster policy ID.

Page alignment is by one-based page position by default. Object alignment uses
object identity when both files expose the same object number/generation and
otherwise uses deterministic canonical object roles where the backend can prove
them. Text alignment is page-local and source-order deterministic. Rendered
alignment is page-local pixel coordinate alignment after explicit raster
normalization. Any unsupported alignment requirement produces
`failed/alignment_failed` or `unavailable/capability_unavailable` rather than a
content change.

### PDF metrics and policy

The first PDF metric registry is proposed as:

| Metric name | Meaning | Unit | Direction | Aggregation |
| --- | --- | --- | --- | --- |
| `pdf.binary.changed_bytes` | byte differences for the binary view | `bytes` | `lower_is_better` | `sum` |
| `pdf.text.changed_runs` | extracted text run changes before truncation | `items` | `lower_is_better` | `count` |
| `pdf.text.compared_runs` | aligned extracted text runs | `items` | `neutral` | `count` |
| `pdf.objects.changed_entries` | object/metadata observations before truncation | `items` | `lower_is_better` | `count` |
| `pdf.objects.compared_entries` | object/metadata entries evaluated | `items` | `neutral` | `count` |
| `pdf.render.changed_pixels` | rendered pixel differences before region grouping | `pixels` | `lower_is_better` | `sum` |
| `pdf.render.changed_pages` | pages with at least one rendered difference | `pages` | `lower_is_better` | `count` |
| `pdf.render.compared_pages` | page pairs rendered and compared | `pages` | `neutral` | `count` |

Each selected view has one default equality evaluation, for example
`pdf.extracted_text_equality` or `pdf.rendered_page_equality`, observing that
view's changed metric with operator `eq` and threshold zero. A future tolerance
policy for rendered pages must define color space, alpha, antialiasing,
subpixel, and aggregation semantics before it can produce pass/warn. No first
PDF policy yields `warn`.

### PDF resources and failures

```python
class PdfResourceLimits:
    max_input_bytes: int = 64 * 1024 * 1024
    max_objects: int = 1_000_000
    max_pages: int = 10_000
    max_stream_bytes: int = 256 * 1024 * 1024
    max_decoded_stream_bytes: int = 256 * 1024 * 1024
    max_text_runs: int = 1_000_000
    max_render_pixels_per_page: int = 100_000_000
    max_rendered_pages: int = 1_000
    max_backend_seconds: int = 30
    max_temp_bytes: int = 512 * 1024 * 1024
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024
```

The exact defaults are tentative and must be revalidated against backend
behavior before acceptance. Limits protect original bytes, parsed object count,
stream decompression, page count, text-run count, raster pixel count, temporary
disk use, subprocess output, deterministic comparison work, returned items, and
payload bytes. Decompression bombs and recursive object references fail before
allocating the next object or stream segment. No normal result depends on
wall-clock time except bounded external backend supervision; timeouts produce a
failed or unavailable outcome, not a partial equality claim.

Failures remain distinguishable:

- missing parser/text/render backend: `unavailable/backend_unavailable`;
- encrypted unsupported input: `failed/decode_error` or a new stable encryption
  problem chosen by the implementation gate;
- malformed syntax or unsupported object graph: `failed/decode_error`;
- decompression or size limit: `failed/resource_limit_exceeded`;
- comparison work limit: `failed/compare_resource_limit`;
- unsupported view/backend combination: `unavailable/capability_unavailable`;
- alignment failure: `failed/alignment_failed`;
- external backend timeout/crash: `failed/comparator_failure` or
  `unavailable/backend_unavailable` according to whether the backend was selected
  and started.

Unavailability means the requested view could not be provided. Failure means a
selected execution path began but could not complete. Degraded fidelity is
forbidden unless a future spec explicitly permits it and records lost
information, backend attempt, and policy impact.

## PDF backend and sandbox gate

PDF parsing, text extraction, and rendering are separate backend roles. A gate
may choose one backend for more than one role only if provenance still records
role-specific availability, version, policy, limits, and failures.

Every PDF backend review must record:

- project name, distribution version, backend/library version, binary version,
  build configuration, and platform;
- SPDX license, transitive dependency licenses, binary redistribution terms,
  NOTICE/SBOM impact, and strong-copyleft isolation if applicable;
- font handling, bundled font data, substitute fonts, system-font discovery,
  CMap/encoding data, and redistribution permission;
- patent or commercial licensing considerations for font programs, color
  management, image codecs, and bundled data;
- malformed-input security history and current advisories;
- deterministic rendering settings and platform variance;
- resource and timeout enforcement strategy.

External subprocesses must be invoked with argument arrays and `shell=False`.
The host supplies bounded temporary directories, no inherited untrusted
environment beyond an allowlist, close-on-exec descriptors, output-byte limits,
timeouts, exit-code validation, and cleanup. Network access, remote resource
loading, active content execution, and writes outside the host temp/artifact
root are forbidden by the conformance profile. If the platform cannot enforce a
required bound, the backend is unavailable on that platform.

## Artifact and renderer boundary

Source-code first gates produce no artifacts. PDF first gates also produce no
page-image or heatmap files. Rendered-page comparison may compute internal
rasters and record hashes, dimensions, page boxes, and changed pixel regions as
validated facts, but it must not write those rasters unless a separate artifact
gate is accepted.

When a later artifact gate exists, every artifact must use RFC 0001
`ArtifactRef` URI validation, an explicit artifact root, SHA-256 verification,
bounded byte size, stable media type, deterministic file naming, and RFC 0004
safe presentation rules. A renderer or UI may not reread original PDFs to
create previews after comparison, because that would bypass snapshot, password,
resource, backend, detail-mode, and mutation contracts.

Terminal and JSON renderers may display only validated source/PDF facts with
control-safe escaping. PDF text extracts, object names, metadata values, font
names, JavaScript snippets, URLs, and file names are untrusted comparison
content and may contain secrets or controls. No renderer may execute a link,
open an embedded file, fetch a remote asset, or derive a new view.

## Delivery gates, commits, and tests

These gates are proposed plans, not implementation authorization.

### P6-S1: source-code schema and lexical relation

1. `feat(core): add source-code schema contracts`
2. `feat(source): add explicit lexical source-code comparison`
3. `feat(cli): add explicit source-code comparison commands`
4. `docs: document source-code comparison contracts`

Gate: selected schema migration tests pass; existing v1/v2 and any implemented
v3 fixtures remain compatible; `language` is required; no automatic language
detection or text fallback exists; lexical relation has deterministic token/text
fixtures for Python and JavaScript; limits, Unicode, newline, malformed input,
and renderer escaping are tested.

### P6-S2: source-code syntax-tree relation and parser backend

1. `build(source): add reviewed optional parser backend`
2. `feat(source): add bounded syntax-tree comparison`
3. `test(source): add parser compatibility and adversarial corpus`
4. `docs: document parser provenance and structural semantics`

Gate: backend dependency/license/platform review is complete; grammar versions
are pinned in provenance; parser recovery, comments, formatting, stable node
paths, alignment, insert/delete/update/move semantics, work limits, native
failure behavior, and deterministic repeated runs pass.

### P6-P1: PDF schema, binary, and extracted-text views

1. `feat(core): add PDF schema contracts`
2. `feat(pdf): add explicit PDF binary and extracted-text views`
3. `feat(cli): add explicit PDF comparison commands`
4. `docs: document PDF text extraction semantics`

Gate: schema migration is revalidated; encrypted/malformed PDFs fail safely;
binary and extracted-text views remain distinct; text order, fonts/encodings,
Unicode mapping, page alignment, resource limits, backend provenance, and no
fallback are covered by generated fixtures.

### P6-P2: PDF object/metadata view

1. `feat(pdf): add bounded object and metadata comparison`
2. `test(pdf): add hostile object graph and metadata corpus`
3. `docs: document PDF object comparison semantics`

Gate: xref/object stream/incremental update handling, active-content inventory,
embedded-file inventory, metadata ignore policy, object alignment, stream
limits, decompression bombs, malformed references, and deterministic canonical
ordering pass.

### P6-P3: PDF rendered-page view without artifacts

1. `build(pdf): add reviewed optional rendering backend`
2. `feat(pdf): add bounded rendered-page comparison`
3. `test(pdf): add rendering determinism and sandbox profile`
4. `docs: document rendered-page backend constraints`

Gate: renderer backend license/security/platform review is complete; page box,
rotation, color, alpha, transparency, antialiasing, font substitution, pixel
limits, subprocess timeout, temp limits, changed-region grouping, and platform
variance are tested. No page-image or heatmap artifact is written.

### P6-A1: optional artifact gate for rendered pages

1. `feat(artifacts): add PDF rendered-page artifact writer`
2. `feat(artifacts): add PDF heatmap artifact writer`
3. `docs: document PDF artifact safety and retention`

Gate: RFC 0001 `ArtifactRef` validation, RFC 0004 renderer/UI boundaries,
safe artifact roots, hash verification, deterministic names, no-clobber output,
privacy warnings, CI retention guidance, and no source reread pass. This gate is
not implied by P6-P3.

Every implementation gate runs Ruff format/lint, strict mypy, complete pytest,
build, wheel/sdist inspection, documentation link checks, package content
inspection, dependency/license review for changed packages, and secret/path leak
scans. Source/PDF gates also require corpus provenance records and exact backend
version capture. Optional-backend tests must skip with explicit reasons when a
backend is absent; skipped tests are not passing evidence.

## Later callbacks

Source-code automatic detection must define language and modality probe budgets,
suffix/content/shebang precedence, parser availability interaction, ambiguity,
pair selection, and attribution in a successor to RFC 0003. PDF automatic
detection must define magic-byte, version, binary/PDF ambiguity, encrypted-file
probing, and view selection in the same or another successor RFC.

SDK v2 must define source/PDF request views, source services, lifecycle stages,
backend roles, artifact authority, compatibility receipts, version negotiation,
out-of-process isolation if needed, and schema migration before third-party
source/PDF comparators can execute. SDK v1.1 remains text/binary-only.

Semantic source-code comparison needs a separate contract for runtime, type
system, macro/preprocessor, import graph, dependency resolution, platform,
compiler/interpreter versions, side effects, and false-equivalence risks. PDF
OCR, tagged-PDF accessibility comparison, form appearance regeneration,
redaction validation, digital signatures, and archival conformance are separate
contracts.

Richer presentation returns to RFC 0004. A UI can navigate validated source
nodes, PDF pages, objects, text runs, and artifact refs, but it cannot compare,
fetch, render, OCR, extract, or execute source documents itself.

## References

- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
- [PDF 32000-2:2020](https://www.iso.org/standard/75839.html)
- [PDF Association: PDF 2.0 application notes](https://pdfa.org/resource/pdf-2-0-application-notes/)
