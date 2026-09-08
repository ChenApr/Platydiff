# RFC 0004: Human Review UI and Renderer Boundary

[Chinese documentation](0004-human-review-ui-and-renderer-boundary_zh.md)

- Status: Proposed
- Date: 2026-09-07
- Roadmap decisions recorded: 2026-09-09
- Owners: Platydiff maintainers
- Implementation owner: unassigned pending separate UI authorization

## Summary

This RFC proposes a human-review presentation architecture for Platydiff. The
user approved U1-U7 as roadmap direction on 2026-09-09: the first candidate is
an improved terminal renderer plus a self-contained HTML report, followed only
when justified by an optional TUI and then a local web or desktop application.
This records direction and boundaries only; it does not authorize UI
implementation or scheduling.

Every interface consumes a validated `CompareOutcome`; no renderer or UI may
recompute relation, verdict, fidelity, metrics, policy evaluations, change
completeness, or problem meaning. The UI can organize, filter, and format facts
that already exist, but it cannot become a second comparison engine.

## Boundary and data flow

The required direction is:

```text
CompareOutcome schema JSON
          |
          v
strict schema validation and typed construction
          |
          v
internal read-only UI view model
          |
          +--> terminal renderer
          +--> self-contained HTML renderer
          +--> optional TUI
          `--> future local web or desktop shell
```

In-process Python callers may begin from a typed `CompareOutcome`; serialized
inputs must pass the same strict schema parser before view-model construction.
Raw dictionaries and unvalidated extension payloads do not enter templates.

The internal view model is presentation-only and not a public interchange
schema. At minimum it represents:

- outcome state and stable problem information;
- relation, verdict, and fidelity without reinterpretation;
- summary counts, metrics, and policy evaluations;
- `ChangeSet` completeness, returned/omitted counts, selection, and limits;
- text hunks, binary spans, or explicitly degraded generic extension-change
  summaries;
- diagnostics grouped by stage and severity;
- execution stages, capability attempts, transformations, comparator and
  algorithm versions, input hashes, and resource limits/usage;
- artifact references as inert metadata until a safe artifact-root resolver is
  explicitly provided.

Formatting values, abbreviating hashes with access to the full value, and
indexing existing changes for navigation are allowed. Deriving a new verdict,
similarity, change count, or hidden normalization is forbidden.

## User states and information architecture

Every surface must visibly distinguish:

- `completed/equal/pass`;
- `completed/different/fail`;
- `completed/*/warn` when a future accepted policy emits it;
- full and degraded fidelity;
- complete, truncated, and partial change detail;
- `unavailable` capability/detection outcomes;
- `failed` execution outcomes;
- renderer/view-model validation failure, which is not a comparison outcome.

The top summary shows outcome, verdict, relation, fidelity, source labels,
schema version, and change-detail completeness. Color may reinforce these
states but cannot be the only signal. Unknown extension changes use their
namespaced kind and plugin ID and are shown as unsupported structured details;
the UI must not guess their meaning.

A completed view is organized in this order:

1. decision summary and explicit truncation/degradation banners;
2. change navigation and modality-specific details;
3. metrics and policy evaluations;
4. diagnostics;
5. provenance, execution stages, capability attempts, and resource usage;
6. inert artifact-reference inventory.

Failed and unavailable views lead with the stable code, safe message, stage,
retryability, and non-sensitive details, then show the execution trail. They do
not render an empty or synthetic `DiffResult`.

## Text review experience

Text hunks retain their RFC 0002 one-based line positions and source order.
Each row shows before/after line numbers, operation (`equal`, `delete`, or
`insert`), content, and line-terminator state. The UI must make LF, CRLF, CR,
and missing final newline distinguishable without modifying content.

Optional display aids may reveal spaces, tabs, trailing whitespace, BOM, and
control characters. They are renderer transforms with an explicit legend and
an off state; they never alter the stored line, comparison, relation, metric,
or verdict. Bidirectional controls and other terminal/HTML control characters
must be visibly escaped or isolated so displayed order cannot impersonate the
logical content.

Navigation uses stable view-local anchors such as `change-1`; these are not
persisted change IDs. Previous/next links, a hunk index, and keyboard-focusable
headings are permitted. Search and filtering may hide rows only when the UI
states that a presentation filter is active and preserves access to the full
returned set.

## Binary review experience

Each `BinarySpan` is one navigable change. The UI displays decimal byte offsets
and lengths for before and after, plus a presentation label of replacement,
insertion, or deletion derived only from the validated zero/non-zero length
shape. An optional hexadecimal rendering of the same offsets is formatting,
not a second location value. Binary navigation preserves source order and makes
the final trailing insertion/deletion distinguishable.

U1 never displays, guesses, decodes, previews, or embeds the bytes covered by a
span. It shows no text or hex dump and does not read the original sources.
Summary, metrics, strict-equality evaluation, hashes, truncation, and resource
usage come only from the validated outcome. A malformed span or invalid binary
collection prevents view-model construction rather than producing a partial UI.

## Delivery sequence

### UI-U1: terminal refinement and self-contained HTML

The near-term proposal is:

- preserve the existing safe terminal output and add clearer state banners,
  aligned hunk gutters, terminator/whitespace legends, and compact provenance;
- add a self-contained, JavaScript-free HTML document generated from the same
  view model;
- use semantic HTML landmarks, native details/summary disclosure, fragment
  navigation, print styles, and responsive CSS;
- embed no remote fonts, scripts, analytics, images, or stylesheets;
- add no runtime dependency unless a separate dependency review proves a
  standard-library implementation unsafe or unmaintainable.

The proposed CLI shape is illustrative until accepted:

```text
platydiff ... --format html --output report.html
```

HTML should require an explicit output path, refuse accidental overwrite unless
the user explicitly opts in, and publish a complete file atomically in the
destination directory. The no-overwrite and overwrite algorithms are specified
under local-file security. It remains a renderer output, not a
`DiffResult.artifacts` item. CI can publish the resulting file as a build
artifact; Platydiff itself does not upload it.

### UI-U2: optional TUI after Phase 3 or 4

A TUI is considered only after real text, binary, and at least one structured
or plugin-provided change shape exercise the view model. It would add virtual
scrolling, hunk folding, filtering, side-by-side/narrow layouts, and keyboard
navigation. It must be an optional extra and must not make the core or basic CLI
depend on a terminal framework.

### UI-U3: local web or desktop after multimodal evidence

A local web or desktop shell is deferred until image/PDF/audio/video work shows
which artifact previews, synchronized navigation, and large-result interactions
are actually needed. It must reuse the validated view model and renderer tests.
A browser server, if chosen, binds only to loopback, uses an unguessable session
token, does not accept arbitrary uploads by default, and never opens artifact
paths outside an explicit root. Desktop packaging, code signing, auto-update,
and embedded-browser licenses require separate review.

UI-U2 and UI-U3 are roadmap hypotheses, not automatic successors and not
authorized implementation phases.

## Accessibility and interaction contract

HTML and future interactive surfaces must provide:

- semantic landmarks and heading order;
- real tables or lists for tabular content, with captions and headers;
- WCAG 2.2 AA contrast targets and status text/icons in addition to color;
- full keyboard access, visible focus, skip links, and no keyboard traps;
- no required hover, motion, or pointer-only gesture;
- reduced-motion support and no automatic animation;
- responsive reflow without forcing side-by-side diffs on narrow screens;
- automatic light/dark styling from `prefers-color-scheme` using local CSS
  variables; an in-report theme selector is deferred because U1 has no script;
- copyable logical text distinct from any visible whitespace markers;
- accessible labels for line numbers, insertions, deletions, diagnostics, and
  collapsed sections.

The initial HTML can use browser-native fragment links and disclosure widgets,
which work without JavaScript. U1 provides no custom live search, filtering,
sorting, persisted preferences, or in-report theme switch; users retain browser
Find, fragment navigation, disclosure controls, system theme, and print CSS. A
future TUI must publish and test a keyboard map; proposed defaults are `j/k` or
arrows to move, `n/p` for next/previous change, `/` for search, `Enter` to
expand, and `q` to quit. Shortcuts must have discoverable alternatives and must
not shadow terminal interrupt behavior.

## Large-result behavior

The UI presents exactly the bounded `ChangeSet` returned by the comparator. It
must show total, returned, and omitted counts and `limit_reason` before the
change list. It cannot fetch, recompute, or imply omitted details.

View-model construction and terminal rendering are linear in returned payload
size. HTML output has a separate deterministic output-byte limit; exceeding it
is a renderer failure and cannot mutate a completed comparison outcome. The
renderer may omit optional presentation indexes to stay within its own budget,
but it must state that navigation aids were omitted and preserve every returned
change or fail safely. TUI virtualization, if implemented, operates on the
already bounded returned set.

## HTML and local-file security

The UI treats every label, line, message, diagnostic detail, plugin field, URI,
and media type as untrusted.

- Escape text and attributes with context-appropriate escaping; never concatenate
  untrusted values into HTML, CSS, URLs, or terminal control sequences.
- U1 contains no script and includes an early HTML `<meta http-equiv>` CSP with
  `default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none';
  form-action 'none'`. Meta CSP can enforce these fetch/form/base restrictions,
  but cannot enforce `frame-ancestors`; that directive is deliberately absent.
- Do not use `innerHTML`, executable templates, remote assets, inline event
  handlers, forms, iframes, or automatic navigation.
- Artifact URIs remain inert text in U1. Future links require the RFC 0001 safe
  artifact-root resolver, hash verification, and a media-type allowlist.
- The report contains comparison content by design; documentation must warn
  users that publishing a CI artifact may disclose source text, labels, hashes,
  diagnostics, and provenance.
- Absolute local paths, environment variables, usernames, temporary paths,
  tokens, and stack traces are excluded from reports.
- A standalone `file://` report has no trusted HTTP response headers and may be
  framed by other local content. Users should open it as a standalone file.
  When a CI or future local HTTP server serves the report, it must add the
  response header `Content-Security-Policy: frame-ancestors 'none'` (and may add
  `X-Frame-Options: DENY` for legacy defense). Meta CSP is defense in depth, not
  a complete sandbox; browser extensions, browser vulnerabilities, screenshots,
  copied content, and deliberate report publication remain residual risks.
- Both modes anchor the existing parent directory once and perform temporary
  creation and publication relative to that same directory handle where the
  platform supports it. They render into a newly created `0600` temporary file
  (`0600`-equivalent owner-only access where supported), flush it, `fsync` where
  supported, and close it before publication. If parent-directory replacement
  or final-component no-follow behavior cannot be bounded by available platform
  primitives, rendering fails safely rather than weakening the contract.
  The default no-overwrite mode atomically links that completed temporary inode
  to an absent target with exclusive/no-follow semantics, then removes the
  temporary name. If the filesystem/platform cannot guarantee this no-clobber
  installation, rendering fails safely and never falls back to check-then-replace.
  An existing file, directory, or symlink always fails in default mode.
- Explicit overwrite mode still never opens or follows the target. It rejects a
  target observed as a symlink, then atomically replaces the directory entry
  with the completed temporary file. A race that substitutes a symlink is safe
  because replacement acts on the entry, not its referent. Directory targets
  and unsupported atomic-replace filesystems fail. Directory `fsync` is used
  where available; lack of directory `fsync` weakens crash durability, not
  no-clobber or symlink safety, and is reported as a platform limitation.

## Themes and visual language

The report should look like a scientific review tool rather than a decorative
dashboard. Use a restrained system-font stack, high-density but readable
spacing, monospaced diff content, clear hierarchy, and stable semantic tokens
for pass, warn, fail, unavailable, insertion, deletion, diagnostic, and muted
provenance. Themes change only presentation tokens, never wording or meaning.

No custom font, icon package, CSS framework, or chart library enters U1. Any
later dependency needs purpose, optionality, license, size, platform, security,
maintenance, and no-dependency alternative review. Icons must have text labels
or accessible names and redistribution permission.

## Testing and acceptance gates

UI-U1 would require:

- one shared view-model test matrix over all outcome, fidelity, completeness,
  metric-value, problem, diagnostic, attempt, artifact-reference, text-hunk,
  and binary-span states;
- terminal and HTML golden tests from the same validated outcomes;
- adversarial escaping tests for HTML, attributes, controls, bidi text, plugin
  payloads, URIs, labels, and `</script>`-like strings even though U1 has no
  script;
- newline, BOM, tab, trailing-space, missing-final-newline, long-line, Unicode,
  and narrow-terminal fixtures;
- binary replacement/insertion/deletion spans, zero/large/chunk-boundary offsets,
  truncated span lists, absent source files, and proof that no source byte is
  read or emitted by the renderer;
- keyboard-only, screen-reader structure, contrast, reflow, print, light/dark,
  and reduced-motion review;
- complete/truncated/partial and renderer-byte-limit tests;
- atomic-write, overwrite, symlink, permissions, and local-path redaction tests;
- deterministic output apart from explicitly normalized execution timestamps;
- existing JSON snapshots and CLI exits unchanged;
- Ruff, strict mypy, full pytest, build, package-content inspection, and CI.

Accessibility automation may supplement but cannot replace keyboard and
screen-reader review. Browser-specific snapshot tooling, if later introduced,
must be a development-only dependency with pinned provenance and license review.

## Proposed commits and ownership gates

No UI owner is assigned while this RFC is `Proposed`. If UI-U1 is separately
accepted, use these commits:

1. `refactor(renderers): add a validated outcome view model`
   - Gate: every schema-v1 state maps without semantic recomputation; both
     current renderers retain compatible output.
2. `feat(terminal): improve human review navigation and detail`
   - Gate: safe control rendering, narrow layouts, state distinctions, and
     existing exit behavior pass.
3. `feat(html): add a self-contained accessible report`
   - Gate: JavaScript-free meta CSP with documented framing residual risk,
     escaping, race-safe no-clobber/overwrite output, binary spans,
     accessibility structure, deterministic snapshots, and renderer limits pass.
4. `docs: document local and CI review reports`
   - Gate: bilingual examples, disclosure warnings, browser/platform notes, and
     dependency/license impact match verified behavior.

Do not combine UI-U2 or UI-U3 with UI-U1. Independent review must confirm that
the view model does not reinterpret RFC 0001, that malicious content cannot
escape its context, and that JSON behavior remains compatible before merge.

## Approved roadmap decisions

The user approved U1-U7 as roadmap direction on 2026-09-09. This approval does
not change this RFC from `Proposed` and does not authorize implementation:

| ID | Decision | Approved roadmap boundary | Governs |
| --- | --- | --- | --- |
| U1 | First polished surface | Improve terminal and add self-contained HTML from one view model | UI-U1 scope |
| U2 | HTML behavior | JavaScript-free document with native anchors/disclosure, enforceable meta CSP, and documented lack of file framing control | Security architecture |
| U3 | File delivery | Require `--output`; atomic no-clobber by default; explicit entry-replacement overwrite; safe failure when unsupported | CLI and filesystem behavior |
| U4 | Dependency budget | Standard library and embedded CSS only for UI-U1 | Packaging/license gate |
| U5 | Scheduling | UI-U1 becomes eligible for separate authorization only after the Phase 2 schema decision; its view-model design may review Phase 2 | Implementation ordering |
| U6 | TUI framework | Defer selection until UI-U2 is accepted after Phase 3 or 4 evidence | Optional dependency |
| U7 | Desktop/local web | Defer shell choice until multimodal artifact requirements are measured | UI-U3 architecture |

UI-U1 still requires a separate user authorization after the accepted Phase 2
schema contract reaches `main` and is stable enough to implement against.
UI-U2 and UI-U3 require their own later evidence and authorization. No UI code,
dependency, owner, or delivery schedule is approved by this decision record.

## Consequences

This proposal gives people a polished review path without coupling comparison
truth to a particular UI toolkit. A static report is easy to inspect locally or
retain in CI, while the strict boundary preserves machine JSON as the durable
contract. Deferring richer shells prevents current text-only assumptions from
hardening into a multimodal interface prematurely.
