# RFC 0008: Source Code and PDF Comparison

[Chinese documentation](0008-source-code-and-pdf-comparison_zh.md)

- Status: Accepted
- Date: 2026-09-10
- Accepted: 2026-09-10
- Review revision: 2026-09-10
- Approved decisions: P6X1-P6X11, SC1-SC10, PDF1-PDF10
- Approved contract gate definition: P6-C0
- Owners: Platydiff maintainers
- Implementation owner: unassigned; conditional authorization recorded for
  coordinator dispatch after the actual predecessor merge gates pass
- Predecessor and contract amendment: RFC 0010 accepts Option A/P4-C1 and
  P6C0-1-P6C0-10; P6-C0 has recorded conditional authorization, but
  coordinator dispatch waits for RFC 0010, P4-C1, P5-A1/schema-v4, and
  compatibility fixtures to merge to `main`

## Summary and authorization boundary

This RFC defines the accepted Phase 6 contracts for explicit source-code and
PDF comparison. It is a contract and documentation acceptance only. It does not
authorize source-code or PDF implementation, dependency changes, SDK v2,
automatic detection, UI work, artifact generation, optional backend
installation, or any code changes.

Source code and PDF comparison are grouped as Phase 6 roadmap work because both
need heavyweight parsing backends and richer structural facts, but they are not
one implementation gate. Source code and PDF have different equivalence
relations, backends, security profiles, artifacts, and dependency risks, so this
RFC splits them into independently authorized delivery gates. Human approval on
2026-09-10 accepts decisions P6X1-P6X11, SC1-SC10, PDF1-PDF10, and the P6-C0
contract gate definition. It authorizes this documentation PR only. P6-C0
has recorded conditional authorization, but coordinator dispatch waits for RFC
0010, P4-C1, P5-A1/schema-v4, and compatibility fixtures to merge to `main`.
Every later source/PDF code gate still requires explicit dispatch from updated
`main`.

All behavior remains explicit-only. A caller must choose a source-code or PDF
spec directly. Existing `AutoCompareSpec` remains text/binary-only unless a
successor to RFC 0003 accepts new detection semantics.

## Evidence ledger

| Current evidence at `origin/main` `fde2bd4` | Phase 6 constraint |
| --- | --- |
| RFC 0001 separates failed/unavailable execution outcomes from completed `DiffResult` facts. | Parser, backend, resource, encryption, sandbox, and rendering failures must not become empty or synthetic differences. |
| RFC 0002 requires each new modality to define spec, changes, metrics, artifacts, equivalence relation, policy, failures, and gates before implementation. | This RFC records contracts and gates but does not start code. |
| RFC 0003 keeps automatic detection bounded and closed to text/binary. | Source/PDF do not participate in auto detection; no filename, MIME, grammar, or PDF magic probe changes existing auto behavior. |
| RFC 0003 snapshot paths own bounded replay, hashing, mutation checks, and safe labels. | Source/PDF gates must revalidate the snapshot implementation before relying on it; concurrent Phase 4/5 work is not evidence. |
| RFC 0004 makes renderers and UI consume validated outcomes without rereading sources or recomputing facts. | Source/PDF renderers may present validated facts and inert artifact refs only; page images and heatmaps need an artifact gate. |
| RFC 0005 implements SDK v1.1 for text/binary detector, comparator, and renderer handles only. | Source/PDF plugin comparators require an explicit SDK-v2 callback and cannot be added through SDK v1.1. |
| RFC 0006 accepts schema v3 for structured-data built-in specs and changes, but its gates remain unimplemented. RFC 0007 proposes image schema v4, and RFC 0009 proposes later media schema work. | Phase 6 should use a shared schema allocation instead of conditionally extending v3; predecessor schema merge and fixture gates must be satisfied before any Phase 6 schema implementation starts. |
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

## Approved decisions

The following stable IDs were approved on 2026-09-10. Their acceptance
establishes the Phase 6 contract and P6-C0 gate definition; it does not start
implementation.

| ID | Accepted decision | Alternative not selected |
| --- | --- | --- |
| P6X1 | Keep source-code and PDF comparison explicit-only; existing auto remains text/binary. | Add source/PDF candidates to RFC 0003 detection without defining ambiguity and attribution. |
| P6X2 | Use schema v5 for Phase 6 source-code and PDF built-in spec/change variants, subject to the global allocation in P6X10 and predecessor merge/fixture gates. | Conditionally extend schema v3 or reuse the image/media schema numbers. |
| P6X3 | Reject source/PDF plugin comparators under SDK v1.1; require SDK v2 before third-party source/PDF modalities. | Let plugin installation introduce source/PDF specs or built-in change kinds. |
| P6X4 | Authorize source-code and PDF implementation gates independently. | Treat Phase 6 as one batch because both need parsers. |
| P6X5 | Keep RFC 0004 artifact/UI work separate; Phase 6 facts may reference artifacts only after an artifact writer gate. | Let PDF rendering implicitly create page images or HTML reports. |
| P6X6 | Mark every code-dependent assumption as a revalidation gate, including P4-A1 and future Phase 5 work. | Treat concurrent unmerged work as design evidence. |
| P6X7 | Forbid fallback that changes comparison relation after a parser/backend starts. | On failure, silently fall back to text, binary, another parser, another renderer, or approximate semantics. |
| P6X8 | Execute multi-view PDF specs as required all-or-nothing invocations: any selected view unavailable or failed terminates the top-level outcome without a `DiffResult`. | Return a partial PDF `DiffResult` containing the views that happened to finish. |
| P6X9 | Before the artifact gate, `artifact_policy` has exactly one value, `none`. | Reserve `record_refs` before a safe artifact writer exists. |
| P6X10 | Use the coordinated schema allocation P4 structured data = v3, Phase 5 image = v4, Phase 6 source/PDF = v5, Phase 7 audio = v6, and video schema successor deferred to a separately accepted backend-worker amendment coordinated with RFC 0009; each successor may start only after all predecessor schemas it depends on are merged on `main` with reader/writer and migration fixtures. | Let each RFC pick a schema number locally, or let audio and video share v6 despite later video-worker amendment requirements. |
| P6X11 | Add one independently authorized P6-C0 schema-v5 source/PDF contract gate that freezes both specs and changes before any source/PDF comparator, backend, or CLI gate starts. | Let P6-S1 or P6-P1a merge first and later reopen the schema-v5 closed union for the other modality. |
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
| PDF3 | A pure `binary` PDF view accepts encrypted PDFs as bytes; any selected nonbinary view on encrypted input terminates with stable `failed/pdf_encrypted`. | Reject all encrypted PDFs, or prompt for passwords. |
| PDF4 | Embedded files, JavaScript, launch actions, network actions, and form actions are inert facts or explicit unsupported features; they are never executed or extracted by default. | Execute or dereference active document content during comparison. |
| PDF5 | Nonbinary PDF parse, text extraction, object inspection, and rendering run only in supervised bounded workers with version provenance and failure isolation. | Run PDF backends in-process or hide which view failed. |
| PDF6 | External PDF tools, if selected, run with argument arrays, no shell, bounded temp dirs, timeouts, output limits, and no network. | Let a backend-specific command line manage security implicitly. |
| PDF7 | Page, object, and text alignment are deterministic and view-specific; unavailable/degraded/failure states remain distinguishable. | Merge alignment failures into content changes. |
| PDF8 | Rendered-page artifacts, thumbnails, and heatmaps require an RFC 0004-compatible artifact gate before any file is written or linked. | Emit page images as a side effect of comparison. |
| PDF9 | Fonts, encodings, transparency, page boxes, rotation, color, malformed xrefs, streams, and decompression bombs are explicit backend/resource cases. | Accept backend defaults without recording transformations and limits. |
| PDF10 | PDF fixtures must be generated or explicitly redistributable and include hostile and malformed cases without restricted documents. | Use arbitrary real-world PDFs as test corpus. |

## Schema and compatibility contract

This RFC accepts schema v5 for Phase 6 source-code and PDF built-ins. The
human decision is P6X10: P4 structured data owns schema v3, Phase 5 image owns
schema v4, Phase 6 source/PDF owns schema v5, Phase 7 audio owns schema v6, and
video schema allocation is deferred to a later global successor pending a
separately accepted backend-worker amendment coordinated with RFC 0009. This
coordinated allocation is accepted by RFC 0008 for Phase 6 dependency planning,
but it does not implement a schema migration and does not claim that any RFC
0009 amendment is already accepted on `main`. If a later global schema RFC or
human review chooses a different allocation, it must update RFC 0007, RFC 0008,
and RFC 0009 together before any affected gate starts.

Phase 6 schema implementation belongs only to P6-C0. P6-C0 may start only after
the predecessor schemas it depends on are merged on `main` with compatibility
fixtures:

- schema v3 reader/writer and migration fixtures from RFC 0006 are present and
  revalidated;
- schema v4 image reader/writer and migration fixtures are present if Phase 5
  has been accepted ahead of Phase 6, or a human-approved schema-allocation
  review explicitly reserves v4 with a no-op predecessor fixture;
- schema v5 fixtures cover both source-code and PDF specs/changes in one closed
  union, including relations or views that are initially unavailable;
- schema v5 fixtures prove that readers accept v1/v2/v3/v4/v5 as applicable,
  that v1/v2 writers remain unchanged, and that source/PDF outcomes never
  downgrade automatically.

After P6-C0 merges, P6-S1, P6-P1a, and later Phase 6 gates may re-run schema
compatibility fixtures, but they must not add, remove, rename, or reinterpret
any schema-v5 spec field, change kind, metric name, problem code, canonical
wire key, digest domain, or validation rule. Any missing future relation or
view must already be represented in P6-C0 as an unavailable capability, not
added by reopening the v5 closed union.

The accepted v5 closed unions are:

```python
CompareSpecV5 = (
    AutoCompareSpec | TextCompareSpec | BinaryCompareSpec
    | JsonCompareSpec | YamlCompareSpec | TableCompareSpec | ArrayCompareSpec
    | ImageCompareSpec
    | SourceCodeCompareSpec | PdfCompareSpec
)
ChangeV5 = (
    TextHunk | BinarySpan | StructuredChange | TableChange | ArrayChange
    | ImageChange | SourceCodeChange | PdfChange | ExtensionChange
)
```

Under this allocation:

- existing built-in text, binary, and auto calls keep schema v1;
- existing `PluginHost` text/binary calls keep schema v2;
- structured data outcomes use schema v3 only after the RFC 0006 gate is
  implemented and revalidated;
- image outcomes use schema v4 only after an accepted Phase 5 gate implements
  and revalidates v4;
- built-in source-code and PDF specs produce schema v5, including failure before
  resolution;
- readers for schema v5 accept v1/v2/v3/v4/v5 according to the implemented
  predecessor set;
- explicit migration helpers preserve original facts and add only documented
  neutral defaults;
- no automatic downgrade exists for source-code or PDF outcomes;
- unknown built-in spec/change kinds remain invalid; unknown namespaced
  extension changes retain RFC 0001 behavior.

P6-C0 must define stable JSON names for every new spec field, change kind,
metric, evaluation rule, transformation ID, backend identity, and problem
detail. Later Phase 6 implementation gates validate that the frozen v5 shape is
still present and compatible; they do not choose or change schema shape.

## Design-contract matrix

| Area | Source-code contract | PDF contract |
| --- | --- | --- |
| Public spec | `SourceCodeCompareSpec(language, relation, parser, normalization, alignment, detail_mode, limits)` | `PdfCompareSpec(views, passwords policy, backend choices, text/render/object options, artifact policy, limits)` |
| First relations | `lexical_text` and `syntax_tree`; `semantic` reserved and unavailable | `pdf.binary`, `pdf.extracted_text`, `pdf.objects_metadata`, `pdf.rendered_pages` |
| Default policy | changed items equal zero gives pass; otherwise fail | all selected views are required; any unavailable/failed view terminates the top-level outcome, and completed results aggregate zero-change evaluations only after every view succeeds |
| Changes | `SourceCodeChange` with node path, operation, language, node kind, relation, digest/fact fields | `PdfChange` tagged by view with page/text/object/render coordinates and digest/fact fields |
| Metrics | changed nodes/tokens, parser errors, moved nodes, compared nodes, formatting/comment changes | changed bytes, text runs, object entries, metadata entries, rendered pixels/pages, backend warnings |
| Artifacts | none in first source gates | `artifact_policy="none"` only until a separate artifact gate; rendered-page facts may include digests but no files |
| Backends | optional parser backend such as Tree-sitter; no default dependency until reviewed | separate parser/text/render backends; external subprocesses require sandbox rules |
| Fallback | no text fallback after source parsing starts | no fallback between PDF views or to binary unless binary view was explicitly selected |
| Plugin path | requires SDK v2 for source-code modality | requires SDK v2 for PDF modality |
| Verification | language fixtures, parser versions, AST paths, move tie-breaks, malformed/adversarial limits | generated PDFs, malformed/xref/stream cases, encryption, fonts, rendering determinism, sandbox limits |

## Canonical facts, digests, and ordering

Source-code and PDF facts use the RFC 0006 evidence-digest framing with new
domains under the accepted schema-v5 allocation:

```text
UTF8("platydiff/v5/" + domain) || 0x00 || U64BE(payload_length) || payload
```

Payloads are canonical byte encodings built from tagged fields. Variable-length
strings are strict UTF-8 with U64BE byte lengths. Counts, ordinals, coordinates,
byte lengths, page numbers, and work counters are non-boolean integers in
`0..2**53` unless a narrower spec limit applies. Writers use sorted object
field order and the stable change ordering defined below; readers reject wrong
types, out-of-order built-in collections, missing required fields, duplicate
coordinates where uniqueness is required, noncanonical ordinals, and unknown
non-extension kinds.

Digest domains are fixed:

| Domain | Payload |
| --- | --- |
| `source/decoded_text_line` | RFC 0002 `TextLine` content and terminator for lexical source comparison |
| `source/token` | language ID, token kind, normalized token bytes, trivia role, and source span |
| `source/node` | language ID, node kind, child field names, ordered child digest sequence, and retained token/trivia digests |
| `source/subtree` | language ID, root node kind, descendant count, token count, and root node digest |
| `pdf/binary/span` | byte offset and length tuple for a binary view span |
| `pdf/text/run` | page ordinal, run ordinal, Unicode text bytes, extractor flags, and text span |
| `pdf/object/entry` | object coordinate, canonical key path, primitive type, and canonical value bytes or stream digest |
| `pdf/metadata/entry` | metadata namespace, key, normalized value bytes, and ignore-policy marker |
| `pdf/render/page` | page ordinal, page box, raster policy, pixel dimensions, and page raster digest |
| `pdf/render/region` | page ordinal, raster policy, pixel rectangle, before digest, after digest, and changed pixel count |

Evidence digests are deterministic integrity fingerprints, not redaction or
encryption. Low-entropy source tokens, PDF metadata values, object keys, and
text runs may be guessable. `digest_only` omits bounded fact payloads but still
exposes coordinates, counts, kinds, hashes, and deterministic digests.

Fact fields are bounded and atomic. Each returned change encodes its operation,
coordinates, digests, and fact payload together for
`max_change_payload_bytes`. If the next complete item would exceed the item or
payload limit, that item and every later item in stable order are omitted; no
fact, coordinate, text run, node, object entry, or rendered region is partially
serialized.

## Source-code comparison contract

### Public intent

The accepted first public shape is:

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

The options are closed and fully serialized:

```python
class SourceParserOptions:
    backend: Literal["tree_sitter"] = "tree_sitter"
    error_recovery: Literal["reject", "recover"] = "reject"

class SourceNormalizationOptions:
    encoding: Literal["utf-8", "utf-8-sig"] = "utf-8"
    newline: Literal["preserve", "normalize_lf"] = "preserve"
    comments: Literal["compare", "ignore"] = "compare"
    formatting: Literal["compare", "ignore"] = "compare"
    literal_spelling: Literal["compare", "normalize_language"] = "compare"

class SourceAlignmentOptions:
    detect_moves: bool = True
    move_minimum_subtree_tokens: int = 3
    repeated_anchor_policy: Literal["source_order"] = "source_order"
```

`language` is required in the first gate. File suffix, shebang, modeline,
package metadata, content probe, and backend parser guesses are not used for
language detection. A later source-detection RFC may define bounded language
probing, ambiguity, and attribution. Until then, a mismatched language produces
`failed/decode_error` or `unavailable/backend_unavailable` at the observed
stage; it does not retry with another language or `TextCompareSpec`.

`lexical_text` in P6-S1 reuses RFC 0002 exact decoded-text and line semantics:
strict UTF-8 or explicit `utf-8-sig`, the same `TextLine` content/terminator
model, the same newline normalization options, the same Myers algorithm and
work accounting, and no Unicode, whitespace, tab, case, or locale
normalization. The source language is recorded as intent and provenance but does
not authorize parser fallback or syntax claims in P6-S1. P6-S1 does not resolve
or load a parser backend; parser options are serialized for schema stability and
become effective only for `syntax_tree`. `syntax_tree` compares parser tree
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
/<escaped-node-kind>#<ordinal-among-siblings-of-same-kind>
```

The wire grammar is:

```text
path = "/root" *("/" segment)
segment = escaped_kind "#" ordinal
escaped_kind = 1*(unreserved / escape)
unreserved = UTF-8 scalar except "/", "#", "~", NUL, C0, or C1 control
escape = "~0" / "~1" / "~h"
ordinal = "0" / (nonzero_digit *digit)
```

`~`, `/`, and `#` in node-kind identifiers encode as `~0`, `~1`, and `~h`.
Other characters are UTF-8 strings admitted by the bounded node-kind validator;
C0/C1 controls, NUL, empty node kinds, and malformed escapes are rejected.
`ordinal` is zero-based among siblings with the same normalized node kind only;
there is no all-sibling ordinal. This keeps paths stable when unrelated sibling
kinds are inserted. Compatibility fixtures must cover escaping, repeated
siblings, inserted unrelated siblings, root-only files, and malformed paths.
Byte ranges and line/column spans may be recorded as facts, but node paths are
the primary structural coordinates.

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

```python
class SourceNodeFact:
    node_kind: str
    field_name: str | None
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    token_count: int
    descendant_count: int
    parser_error: bool
    trivia_role: Literal["none", "comment", "formatting"]
    text_excerpt: str | None
```

Insert has only after coordinates. Delete has only before coordinates. Update
has both sides at an aligned node and records changed node kind, token, trivia,
or child-shape facts. Move has both sides and reports a node whose digest and
selected identity facts match under the move policy but whose path changed.
Moves are observations, not patch operations, and are emitted only when the
alignment algorithm can prove them deterministically. Otherwise the same change
is represented as delete plus insert.

`facts` mode includes bounded `SourceNodeFact` values. `digest_only` omits
`before_fact` and `after_fact` while retaining operation, paths, node kinds, and
digests. `text_excerpt` is present only for lexical token/line facts and is
bounded by `max_fact_text_bytes`; syntax subtree facts use counts, not recursive
payloads. Model validation rejects illegal side combinations, reversed spans,
negative counts, digest/fact mismatch with `detail_mode`, move without two
paths, and update without two aligned sides.

Alignment is deterministic:

- exact node kind and digest matches are paired first;
- unique anchors outrank repeated anchors;
- parent-consistent matches outrank cross-parent matches;
- source-order tie-breaking is stable and documented;
- no semantic name binding, import resolution, or control-flow analysis is
  inferred;
- alignment failure caused by ambiguity or resource exhaustion is a failed
  outcome, not an approximate result.

Stable source-code change ordering is delete/update/move by before path, then
insert by after path at the nearest containing parent, with path lexical order
using decoded path segments and numeric ordinal order. When one logical
alignment yields both a parent update and child updates, the parent precedes
children. Lexical P6-S1 ordering is exactly RFC 0002 hunk source order.

### Source metrics and policy

The accepted first source-code metric registry is:

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
    max_fact_text_bytes: int = 4096
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

Source work accounting is fixed per relation. `lexical_text` uses RFC 0002
Myers work units exactly. `syntax_tree` charges one unit per decoded token, one
per parser node accepted into the host tree, one per node digest constructed,
one per candidate-pair score considered during alignment, one per paired node
visited, and one per insert/delete/move/update change emitted before detail
truncation. Each unit is checked before the action. Default values are inherited
from RFC 0002 and RFC 0006 where possible: 16 MiB input and 4 MiB payload match
existing text/structured defaults, 1,000,000 token/node ceilings match the
structured node ceiling, and 5,000,000 work units match the existing comparison
budget. P6-S1 `lexical_text` may rely on the RFC 0002 text limits because it
does not select or load a parser backend. P6-S2 may not start until adversarial
evidence proves the token/node/work defaults bound memory on the selected parser
backend.

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

The accepted first public shape is:

```python
from dataclasses import field

class PdfCompareSpec:
    kind: Literal["pdf"] = "pdf"
    views: tuple[
        Literal["binary", "extracted_text", "objects_metadata", "rendered_pages"],
        ...
    ] = ("binary",)
    text: PdfTextOptions = field(default_factory=PdfTextOptions)
    objects: PdfObjectOptions = field(default_factory=PdfObjectOptions)
    rendering: PdfRenderOptions = field(default_factory=PdfRenderOptions)
    artifact_policy: Literal["none"] = "none"
    limits: PdfResourceLimits = field(default_factory=PdfResourceLimits)
```

`PdfCompareSpec()` is therefore constructable and means explicit PDF binary
comparison. Dataclass implementations must use `default_factory` for nested
model defaults. Nonbinary backend limits are validated only when their view is
selected.

Schema-v5 wire validation is closed:

- top-level writer field order is `kind`, `views`, `text`, `objects`,
  `rendering`, `artifact_policy`, then `limits`;
- `views` is a non-empty JSON array with no duplicate values and no unknown
  values;
- writers normalize `views` into canonical order
  `binary`, `extracted_text`, `objects_metadata`, `rendered_pages`; input order
  is not preserved in the wire form;
- writers always emit `text`, `objects`, and `rendering` as non-null option
  objects, even when the corresponding nonbinary view is not selected;
- `text` has exactly the ordered keys `order`, `whitespace`,
  `unicode_mapping`; the only accepted values in Phase 6 are the defaults
  `extractor_logical`, `preserve`, and `backend_tounicode`;
- `objects` has exactly the ordered keys `metadata`, `streams`,
  `active_content`; `metadata` accepts default `compare` or non-default
  `ignore_document_info_dates`, while `streams` and `active_content` accept only
  their defaults `metadata_and_digest` and `inert_inventory`;
- `rendering` has exactly the ordered keys `page_box`, `rotation`,
  `resolution_dpi`, `color`, `alpha`, and `antialiasing`; `page_box` accepts
  default `media` or non-default `crop`, `alpha` accepts default
  `composite_white` or non-default `preserve`, `resolution_dpi` is a positive
  integer, and the other fields accept only their declared defaults;
- option objects are never `null` and are never omitted; missing option keys,
  unknown option keys, null option values, or values outside the closed set are
  `failed/invalid_spec`;
- writers always emit `limits` with exactly these keys: `base`,
  `worker_invocation`, `extracted_text`, `objects_metadata`, and
  `rendered_pages`;
- `worker_invocation` is `null` when no nonbinary view is selected and is a
  finite object when any nonbinary view is selected;
- every per-view limit key is `null` when that view is not selected and is a
  finite object when that view is selected;
- readers accept only that closed form: missing limit keys, unknown limit keys,
  empty `views`, duplicate `views`, unknown view names, selected nonbinary views
  with `null` limits, or unselected views with non-null limits are
  `failed/invalid_spec` before backend resolution.

The PDF options are closed and fully serialized:

```python
class PdfTextOptions:
    order: Literal["extractor_logical"] = "extractor_logical"
    whitespace: Literal["preserve"] = "preserve"
    unicode_mapping: Literal["backend_tounicode"] = "backend_tounicode"

class PdfObjectOptions:
    metadata: Literal["compare", "ignore_document_info_dates"] = "compare"
    streams: Literal["metadata_and_digest"] = "metadata_and_digest"
    active_content: Literal["inert_inventory"] = "inert_inventory"

class PdfRenderOptions:
    page_box: Literal["media", "crop"] = "media"
    rotation: Literal["apply_page_rotation"] = "apply_page_rotation"
    resolution_dpi: int = 144
    color: Literal["srgb_8bit"] = "srgb_8bit"
    alpha: Literal["composite_white", "preserve"] = "composite_white"
    antialiasing: Literal["backend_default_recorded"] = "backend_default_recorded"
```

All selected PDF views are required and execute as one all-or-nothing
invocation. Each selected view may produce separate summary counts, metrics,
changes, transformations, and evaluations only if every selected view reaches a
completed view result. If any selected view is unavailable or failed, the
top-level outcome is `unavailable` or `failed` with no `DiffResult`; completed
view work is represented only as bounded execution attempts and diagnostics, not
as partial result facts. A combined completed PDF result may aggregate verdicts,
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

A pure `views=("binary",)` PDF comparison accepts encrypted PDFs because it
compares the original bytes and does not parse the document. Any selected
nonbinary view requires PDF parsing or rendering. If either input is encrypted
and no accepted password contract exists, execution terminates with
`failed/pdf_encrypted` at the first nonbinary worker stage that observes
encryption. There is no prompt, no password field, no password storage, no
permission bypass, and no fallback to binary unless the caller selected only the
binary view. Permission flags are recorded only as inert metadata when readable
without bypassing encryption.

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

```python
class PdfTextCoordinate:
    page: int
    run: int
    start_text_offset: int
    text_length: int

class PdfObjectCoordinate:
    object_number: int | None
    generation: int | None
    role_path: str
    key_path: str

class PdfRenderCoordinate:
    page: int
    page_box: Literal["media", "crop"]
    x: int
    y: int
    width: int
    height: int
    raster_policy_id: str

class PdfFact:
    fact_kind: Literal["text_run", "object_entry", "metadata_entry", "render_region"]
    type_name: str
    page: int | None
    text: str | None
    value_summary: str | None
    byte_length: int | None
    changed_pixels: int | None

PdfCoordinate = PdfTextCoordinate | PdfObjectCoordinate | PdfRenderCoordinate | BinarySpan
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

Change invariants are view-specific. Binary view changes must satisfy
`BinarySpan` invariants. Text-run changes require page/run coordinates and
bounded text facts or text-run digests. Object and metadata changes require a
canonical object coordinate or metadata key and never embed decoded stream
bytes. Render changes require an in-bounds pixel rectangle with positive width
and height and changed pixel count greater than zero. Insert has only after
coordinates, delete has only before coordinates, update has both, and move is
legal only for text/object facts whose stable digest matches and whose
coordinate changes. Stable ordering is by view order from the normalized spec,
then page, then run/object/key/rectangle order. Readers reject interleaved views
that violate this order.

### PDF metrics and policy

The accepted first PDF metric registry is:

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
from dataclasses import field

class PdfBaseResourceLimits:
    max_input_bytes: int = 64 * 1024 * 1024
    max_fact_text_bytes: int = 4096
    max_fact_value_bytes: int = 4096
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

class PdfWorkerInvocationLimits:
    max_total_backend_seconds: int
    max_total_stdout_stderr_bytes: int
    max_total_temp_bytes: int
    max_total_decoded_bytes: int
    max_total_worker_output_bytes: int
    max_peak_worker_rss_bytes: int
    max_peak_concurrent_worker_processes: int
    max_total_worker_processes_spawned: int

class PdfTextResourceLimits:
    max_pages: int
    max_stream_bytes: int
    max_decoded_stream_bytes: int
    max_text_runs: int
    max_view_backend_seconds: int
    max_view_stdout_stderr_bytes: int
    max_view_temp_bytes: int
    max_view_decoded_bytes: int
    max_view_worker_output_bytes: int
    max_view_peak_worker_rss_bytes: int
    max_view_peak_concurrent_worker_processes: int
    max_view_total_worker_processes_spawned: int

class PdfObjectResourceLimits:
    max_objects: int
    max_pages: int
    max_stream_bytes: int
    max_decoded_stream_bytes: int
    max_view_backend_seconds: int
    max_view_stdout_stderr_bytes: int
    max_view_temp_bytes: int
    max_view_decoded_bytes: int
    max_view_worker_output_bytes: int
    max_view_peak_worker_rss_bytes: int
    max_view_peak_concurrent_worker_processes: int
    max_view_total_worker_processes_spawned: int

class PdfRenderResourceLimits:
    max_pages: int
    max_render_pixels_per_page: int
    max_rendered_pages: int
    max_view_backend_seconds: int
    max_view_stdout_stderr_bytes: int
    max_view_temp_bytes: int
    max_view_decoded_bytes: int
    max_view_worker_output_bytes: int
    max_view_peak_worker_rss_bytes: int
    max_view_peak_concurrent_worker_processes: int
    max_view_total_worker_processes_spawned: int

class PdfResourceLimits:
    base: PdfBaseResourceLimits = field(default_factory=PdfBaseResourceLimits)
    worker_invocation: PdfWorkerInvocationLimits | None = None
    extracted_text: PdfTextResourceLimits | None = None
    objects_metadata: PdfObjectResourceLimits | None = None
    rendered_pages: PdfRenderResourceLimits | None = None
```

PDF has both whole-invocation and per-view budgets. `base.max_input_bytes`,
`base.max_compare_work`, `base.max_change_items`, and
`base.max_change_payload_bytes` apply cumulatively across the complete PDF
invocation. Fact text/value ceilings apply to each retained `PdfFact` before
the complete change item is charged to the payload budget. `worker_invocation`
is the whole-invocation worker budget and is required when any nonbinary view is
selected. Selected nonbinary views also require their matching per-view limit
object: `limits.extracted_text`, `limits.objects_metadata`, or
`limits.rendered_pages`.

Worker accounting is frozen even though the numeric defaults are gate-supplied:

- `backend_seconds`, `stdout_stderr_bytes`, `temp_bytes`, `decoded_bytes`, and
  `worker_output_bytes` are measured as per-step deltas, summed into per-view
  counters, and summed again into the whole-invocation counters;
- `worker_rss_bytes` is sampled as a current value, recorded as a per-view peak,
  and aggregated as the whole-invocation peak across all workers;
- `concurrent_worker_processes` is sampled as a current value and aggregated as
  per-view and whole-invocation peaks;
- `worker_processes_spawned` is measured as a per-step delta and summed into
  per-view and whole-invocation totals;
- page, object, stream, text-run, and pixel counters apply only to the views
  that define them, while every accepted unit also charges
  `base.max_compare_work`.

The host checks the relevant per-view remaining budget and the
`worker_invocation` remaining budget before dispatching a worker step, before
creating a temp file, before accepting stdout/stderr or protocol output, before
accepting decoded/object/text/raster chunks, before spawning a process, and
after each RSS/process sample. A nullable per-view limit object never creates a
global cap by itself; global worker limits exist only in
`worker_invocation`.

The RFC-wide defaults accepted now are exactly
`PdfBaseResourceLimits()`. These fields are binary-safe: input bytes, retained
fact text/value bytes, comparison work, returned change count, and returned
change payload bytes. They are independent of a PDF parser or renderer and are
sufficient for P6-P1a. They do not approve object-count, page-count, stream,
text-run, raster-pixel, worker RSS, timeout, temporary-storage, worker-output,
or worker-process defaults.

P6-P1b, P6-P2, and P6-P3 each must supply backend-specific numeric defaults in
their own evidence gate before implementation starts. The gate evidence must
name the backend/version/platform, explain why each default is enforceable,
include adversarial fixtures for the limit, and prove check-before-allocate
behavior. Until that evidence exists, `worker_invocation` and omitted nonbinary
limit objects are valid only when no corresponding nonbinary view is selected;
selecting a nonbinary view without `worker_invocation` and its matching finite
per-view limit object is `failed/invalid_spec` before backend resolution.
Decompression bombs and recursive object references fail before
allocating the next object or stream segment. No completed result depends on
wall-clock time; timeouts produce a failed or unavailable outcome, not a partial
equality claim.

Validation examples are part of the contract:

- `PdfCompareSpec()` is valid and normalizes to `views=("binary",)` with
  `PdfResourceLimits(base=PdfBaseResourceLimits(), worker_invocation=None,
  extracted_text=None, objects_metadata=None, rendered_pages=None)`;
- `PdfCompareSpec(views=("binary",), limits=PdfResourceLimits())` is valid and
  requires no nonbinary backend limits;
- `PdfCompareSpec(views=("extracted_text",), limits=PdfResourceLimits())` is
  invalid before backend resolution because `limits.worker_invocation` and
  `limits.extracted_text` are absent;
- a multi-view spec with `views=("binary", "rendered_pages")` is invalid before
  backend resolution unless `limits.worker_invocation` and
  `limits.rendered_pages` are present and finite;
- providing `limits.objects_metadata` while `objects_metadata` is not selected
  is invalid; unselected per-view limit keys serialize as `null`.

Binary-only canonical JSON shape:

```json
{
  "kind": "pdf",
  "views": ["binary"],
  "text": {
    "order": "extractor_logical",
    "whitespace": "preserve",
    "unicode_mapping": "backend_tounicode"
  },
  "objects": {
    "metadata": "compare",
    "streams": "metadata_and_digest",
    "active_content": "inert_inventory"
  },
  "rendering": {
    "page_box": "media",
    "rotation": "apply_page_rotation",
    "resolution_dpi": 144,
    "color": "srgb_8bit",
    "alpha": "composite_white",
    "antialiasing": "backend_default_recorded"
  },
  "artifact_policy": "none",
  "limits": {
    "base": {
      "max_input_bytes": 67108864,
      "max_fact_text_bytes": 4096,
      "max_fact_value_bytes": 4096,
      "max_compare_work": 5000000,
      "max_change_items": 10000,
      "max_change_payload_bytes": 4194304
    },
    "worker_invocation": null,
    "extracted_text": null,
    "objects_metadata": null,
    "rendered_pages": null
  }
}
```

Selected-nonbinary canonical JSON shape. The numeric values below are explicit
gate- or caller-supplied finite values used to show shape only; they are not
RFC-wide defaults:

```json
{
  "kind": "pdf",
  "views": ["extracted_text"],
  "text": {
    "order": "extractor_logical",
    "whitespace": "preserve",
    "unicode_mapping": "backend_tounicode"
  },
  "objects": {
    "metadata": "compare",
    "streams": "metadata_and_digest",
    "active_content": "inert_inventory"
  },
  "rendering": {
    "page_box": "media",
    "rotation": "apply_page_rotation",
    "resolution_dpi": 144,
    "color": "srgb_8bit",
    "alpha": "composite_white",
    "antialiasing": "backend_default_recorded"
  },
  "artifact_policy": "none",
  "limits": {
    "base": {
      "max_input_bytes": 67108864,
      "max_fact_text_bytes": 4096,
      "max_fact_value_bytes": 4096,
      "max_compare_work": 5000000,
      "max_change_items": 10000,
      "max_change_payload_bytes": 4194304
    },
    "worker_invocation": {
      "max_total_backend_seconds": 30,
      "max_total_stdout_stderr_bytes": 1048576,
      "max_total_temp_bytes": 536870912,
      "max_total_decoded_bytes": 268435456,
      "max_total_worker_output_bytes": 67108864,
      "max_peak_worker_rss_bytes": 536870912,
      "max_peak_concurrent_worker_processes": 1,
      "max_total_worker_processes_spawned": 1
    },
    "extracted_text": {
      "max_pages": 1000,
      "max_stream_bytes": 268435456,
      "max_decoded_stream_bytes": 268435456,
      "max_text_runs": 1000000,
      "max_view_backend_seconds": 30,
      "max_view_stdout_stderr_bytes": 1048576,
      "max_view_temp_bytes": 536870912,
      "max_view_decoded_bytes": 268435456,
      "max_view_worker_output_bytes": 67108864,
      "max_view_peak_worker_rss_bytes": 536870912,
      "max_view_peak_concurrent_worker_processes": 1,
      "max_view_total_worker_processes_spawned": 1
    },
    "objects_metadata": null,
    "rendered_pages": null
  }
}
```

The acceptance/start boundary is explicit:

- P6-C0 must merge before any source/PDF comparator, backend, or CLI gate; after
  P6-C0, P6-S1 and P6-P1a may proceed in parallel without reopening schema v5;
- P6-S1 and P6-S2 are source-code gates and are not blocked by PDF backend
  numeric defaults;
- P6-P1a may be accepted and started with `PdfCompareSpec()` and
  `PdfResourceLimits()` because the default view is `binary` and it does not
  parse nonbinary PDF content;
- P6-P1b may not start until text extraction supplies `worker_invocation` and
  `extracted_text` defaults for page, text-run, stream/decode, backend-time,
  stdout/stderr, temp, decoded/output, RSS peak, and process counters with
  evidence;
- P6-P2 may not start until object/metadata inspection supplies default object,
  page, stream/decode, backend-time, stdout/stderr, temp, decoded/output, RSS
  peak, and process counters in `worker_invocation` and `objects_metadata` with
  evidence;
- P6-P3 may not start until rendering supplies default page, rendered-page,
  raster-pixel, backend-time, stdout/stderr, temp, decoded/output, RSS peak, and
  process counters in `worker_invocation` and `rendered_pages` with evidence;
- P6-A1 remains blocked on artifact authority and is not authorized by PDF
  backend default evidence.

PDF work accounting is fixed by view:

- whole invocation: one unit per selected view dispatch and one per worker
  result chunk accepted;
- binary: RFC 0003 byte-span accounting plus one unit per retained span;
- extracted text: one unit per page visited, text run accepted, aligned run
  pair, and text change emitted;
- objects/metadata: one unit per indirect object visited, dictionary key/value
  accepted, stream digest accepted, metadata entry accepted, aligned entry, and
  object change emitted;
- rendered pages: one unit per page rendered, raster tile accepted, compared
  tile, changed region emitted, and page-level aggregate.

Every unit is checked before the action. Per-view counters and cumulative
counters are both recorded in provenance for completed outcomes; for failed or
unavailable multi-view outcomes they are recorded as execution attempts only.

Failures remain distinguishable:

- missing parser/text/render backend: `unavailable/backend_unavailable`;
- encrypted input with selected nonbinary view: `failed/pdf_encrypted`;
- selected nonbinary view without `worker_invocation` or matching finite limits:
  `failed/invalid_spec`;
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

Every nonbinary PDF role runs in a supervised bounded worker. In-process parsing
of nonbinary PDF content is not a conforming first-gate implementation. The
worker protocol is host-owned:

- cancellation: the host can terminate the worker when the caller cancels or a
  limit trips; schema has no completed partial result for cancellation;
- timeout: wall-clock timeout kills the worker process group and charges
  `max_view_backend_seconds` and `max_total_backend_seconds`; exceeding either
  records `pdf_worker_timeout`;
- RSS: the worker has enforced per-view and invocation resident-memory peaks;
  exceeding `max_view_peak_worker_rss_bytes` or
  `max_peak_worker_rss_bytes` records `pdf_worker_rss_exceeded`;
- temp: all temp files live under a host-created bounded temp root and count
  toward `max_view_temp_bytes` and `max_total_temp_bytes`;
- output: stdout/stderr/protocol payloads are bounded by
  `max_view_stdout_stderr_bytes`, `max_total_stdout_stderr_bytes`,
  `max_view_worker_output_bytes`, and `max_total_worker_output_bytes`; raw
  backend stderr is not copied into outcomes;
- process: concurrent and total spawned processes are bounded by the per-view
  and invocation process fields; unsupported process supervision makes the
  backend unavailable;
- network: network access and remote resource loading are disabled by policy;
  if the platform cannot enforce this for a backend, that backend is
  unavailable;
- filesystem: the worker receives only the opened source descriptors or
  host-owned temp paths required for that view and cannot write outside the temp
  root or accepted artifact root.

If the platform cannot enforce timeout, RSS, temp, output, process, or network
isolation, the corresponding nonbinary backend is
`unavailable/backend_unavailable` before document execution. If a supervised
worker starts and then violates a bound, the selected view fails and therefore
the whole required PDF invocation fails.

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

These gates are the accepted Phase 6 plan, not implementation authorization.

### P6-C0: schema-v5 source/PDF contract gate

1. `feat(core): add schema-v5 source/PDF spec and change contracts`
2. `feat(core): add schema-v5 readers, writers, and v1-v4 migrations`
3. `test(core): add canonical source/PDF wire fixtures`
4. `test(core): add source/PDF spec validation and unavailable capability cases`
5. `docs: document schema-v5 source/PDF contract`

Gate: independently authorized from updated `main`; predecessor v1-v4 readers,
writers, and migration fixtures pass; schema v5 freezes `SourceCodeCompareSpec`,
`PdfCompareSpec`, `SourceCodeChange`, and `PdfChange` in one closed union; all
source relations and PDF views are represented even when initially unavailable;
canonical facts, digest domains, option serialization, resource-limit shapes,
problem codes, and spec validation are frozen; no source/PDF comparator,
backend, or CLI behavior is implemented. P6-C0 must merge before P6-S1,
P6-P1a, or any later Phase 6 comparator/backend gate starts.

### P6-S1: source-code lexical relation

1. `feat(source): add dependency-free lexical source-code comparison on schema v5`
2. `feat(cli): add explicit source-code lexical comparison commands`
3. `test(source): add deterministic lexical source fixtures`
4. `docs: document source-code lexical comparison contracts`

Gate: P6-C0 has merged; schema-v5 fixtures are rerun and unchanged; `language`
is required; no automatic language detection or text fallback exists; lexical
relation has deterministic token/text fixtures for Python and JavaScript;
limits, Unicode, newline, malformed input, and renderer escaping are tested.
This gate does not add or change schema-v5 fields, unions, validation rules, or
problem codes. After P6-C0, P6-S1 and P6-P1a may proceed in parallel.

### P6-S2: source-code syntax-tree relation and parser backend

1. `build(source): add reviewed optional parser backend`
2. `feat(source): add bounded syntax-tree comparison`
3. `test(source): add parser compatibility and adversarial corpus`
4. `docs: document parser provenance and structural semantics`

Gate: P6-C0 and P6-S1 have merged; schema-v5 fixtures are rerun and unchanged;
backend dependency/license/platform review is complete; grammar versions are
pinned in provenance; parser recovery, comments, formatting, stable node paths,
alignment, insert/delete/update/move semantics, work limits, native failure
behavior, and deterministic repeated runs pass. This gate must provide
adversarial evidence that the selected parser backend enforces token, node,
work, input, and payload defaults before implementation starts. It must not
reopen the v5 closed union.

### P6-P1a: PDF binary view

1. `feat(pdf): add explicit PDF binary view on schema v5`
2. `feat(cli): add explicit PDF binary comparison commands`
3. `test(pdf): add generated PDF binary fixtures`
4. `docs: document PDF binary view semantics`

Gate: P6-C0 has merged; schema-v5 fixtures are rerun and unchanged;
`artifact_policy` accepts only `none`;
pure binary view accepts encrypted PDFs as bytes; binary view reuses exact
binary semantics while naming the PDF view; malformed PDFs are not parsed;
RFC-wide binary-safe resource defaults, payload truncation, and no fallback are
covered by generated fixtures. This gate may be accepted and started without
nonbinary PDF backend numeric defaults. This gate does not add or change
schema-v5 fields, unions, validation rules, or problem codes. After P6-C0,
P6-S1 and P6-P1a may proceed in parallel.

### P6-P1b: PDF extracted-text view

1. `feat(pdf): add supervised PDF text extraction worker`
2. `feat(pdf): add explicit PDF extracted-text view`
3. `feat(cli): add explicit PDF extracted-text comparison commands`
4. `docs: document PDF text extraction semantics`

Gate: P6-C0 and P6-P1a have merged; schema-v5 fixtures are rerun and unchanged;
any encrypted input returns `failed/pdf_encrypted`; text extraction runs only in
a supervised bounded worker; multi-view all-or-nothing behavior is tested; text
order, fonts/encodings, Unicode mapping, page alignment, worker isolation,
cumulative resources, backend provenance, and no fallback are covered by
generated fixtures. This gate must provide and justify `worker_invocation` and
`extracted_text` defaults for page, text-run, stream/decode, backend-time,
stdout/stderr, temp, decoded/output, RSS peak, and process counters before
implementation starts. It must not reopen the v5 closed union.

### P6-P2: PDF object/metadata view

1. `feat(pdf): add bounded object and metadata comparison`
2. `test(pdf): add hostile object graph and metadata corpus`
3. `docs: document PDF object comparison semantics`

Gate: P6-C0 and P6-P1a have merged; schema-v5 fixtures are rerun and unchanged;
xref/object stream/incremental update handling, active-content inventory,
embedded-file inventory, metadata ignore policy, object alignment, stream
limits, decompression bombs, malformed references, and deterministic canonical
ordering pass. This gate must provide and justify `worker_invocation` and
`objects_metadata` defaults for object, page, stream/decode, backend-time,
stdout/stderr, temp, decoded/output, RSS peak, and process counters before
implementation starts. It must not reopen the v5 closed union.

### P6-P3: PDF rendered-page view without artifacts

1. `build(pdf): add reviewed optional rendering backend`
2. `feat(pdf): add bounded rendered-page comparison`
3. `test(pdf): add rendering determinism and sandbox profile`
4. `docs: document rendered-page backend constraints`

Gate: P6-C0 and P6-P1a have merged; schema-v5 fixtures are rerun and unchanged;
renderer backend license/security/platform review is complete; page box,
rotation, color, alpha, transparency, antialiasing, font substitution, pixel
limits, subprocess timeout, temp limits, changed-region grouping, and platform
variance are tested. This gate must provide and justify `worker_invocation` and
`rendered_pages` defaults for page, rendered-page, raster-pixel, backend-time,
stdout/stderr, temp, decoded/output, RSS peak, and process counters before
implementation starts. No page-image or heatmap artifact is written. It must
not reopen the v5 closed union.

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
scans. P6-C0 additionally runs schema-v5 reader/writer, v1-v4 migration,
canonical fixture, and spec/problem validation checks. Later source/PDF gates
rerun those fixtures as compatibility checks and must prove the frozen v5 shape
is unchanged. Source/PDF comparator or backend gates also require corpus
provenance records and exact backend version capture. Optional-backend tests
must skip with explicit reasons when a backend is absent; skipped tests are not
passing evidence.

## Later callbacks

Source-code automatic detection must define language and modality probe budgets,
suffix/content/shebang precedence, parser availability interaction, ambiguity,
pair selection, and attribution in a successor to RFC 0003. PDF automatic
detection must define magic-byte, version, binary/PDF ambiguity, encrypted-file
probing, and view selection in the same or another successor RFC.

SDK v2 must define source/PDF request views, source services, lifecycle stages,
backend roles, artifact authority, compatibility receipts, version negotiation,
out-of-process isolation if needed, and compatibility with the frozen schema-v5
source/PDF contracts before third-party source/PDF comparators can execute. SDK
v1.1 remains text/binary-only.

Semantic source-code comparison needs a separate contract for runtime, type
system, macro/preprocessor, import graph, dependency resolution, platform,
compiler/interpreter versions, side effects, and false-equivalence risks. PDF
OCR, tagged-PDF accessibility comparison, form appearance regeneration,
redaction validation, digital signatures, and archival conformance are separate
contracts.

Richer presentation returns to RFC 0004. A UI can navigate validated source
nodes, PDF pages, objects, text runs, and artifact refs, but it cannot compare,
fetch, render, OCR, extract, or execute source documents itself.

## Lifecycle and failure table

| Scenario | Required terminal behavior |
| --- | --- |
| Explicit source `lexical_text`, stable inputs | RFC 0002 text lifecycle and exact decoded-line semantics; completed source-code outcome under the P6-C0 frozen schema v5. |
| Explicit source `syntax_tree`, missing parser backend | `resolving/unavailable/backend_unavailable`; no `DiffResult`. |
| Explicit source `syntax_tree`, malformed source with `reject` recovery | `decoding/failed/decode_error`; no text fallback and no `DiffResult`. |
| Explicit source `syntax_tree`, parser/resource bound exceeded | `decoding/failed/resource_limit_exceeded`; no partial result. |
| Explicit source `syntax_tree`, alignment ambiguity or work bound exceeded | `aligning/failed/alignment_failed` or `comparing/failed/compare_resource_limit`; no approximate result. |
| PDF `views=("binary",)`, encrypted input | Completed binary-view comparison of original bytes if byte limits are satisfied. |
| PDF includes any nonbinary view without `worker_invocation` or matching finite limits | `validating/failed/invalid_spec`; no backend resolution and no `DiffResult`. |
| PDF includes any nonbinary view and input is encrypted | `decoding/failed/pdf_encrypted`; no fallback to binary and no `DiffResult`. |
| PDF nonbinary backend unavailable or platform cannot supervise worker | `resolving/unavailable/backend_unavailable`; no worker starts. |
| PDF required multi-view run where an early view fails | Top-level failed/unavailable outcome; completed earlier view work appears only in execution attempts. |
| PDF worker timeout/RSS/temp/output/process/network bound exceeded | Selected view fails at observed stage; required all-or-nothing invocation has no `DiffResult`. |
| PDF artifact requested before P6-A1 | `validating/failed/invalid_spec`; `artifact_policy` only accepts `none`. |

## References

- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
- [PDF 32000-2:2020](https://www.iso.org/standard/75839.html)
- [PDF Association: PDF 2.0 application notes](https://pdfa.org/resource/pdf-2-0-application-notes/)
