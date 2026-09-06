# AGENTS.md

[Chinese documentation](AGENTS_zh.md)

## Scope and precedence

This file applies to the entire repository. A deeper `AGENTS.md` may supplement these rules, and an `AGENTS.override.md` may override them within its directory tree. When rules conflict, follow the file closest to the target file.

## Project overview

Platydiff is an extensible multimodal diff engine for scientific data, experimental regression testing, and competition workflows. It uses one detection, decoding, normalization, alignment, comparison, aggregation, and rendering pipeline for binary data, text, source code, structured configuration, images, audio, video, PDFs, tables, and statistical data.

Primary technical direction:

- Python 3.12+; the primary deliverables are a Python library and the `platydiff` CLI.
- The standard library provides core file, hashing, text, concurrency, and subprocess capabilities.
- NumPy, SciPy, pandas, and xarray provide optional array, statistical, and scientific-data capabilities.
- Pillow, OpenCV, scikit-image, Tree-sitter, FFmpeg, and PDF backends are optional plugins or external backends.
- Performance-critical paths may use Rust extensions after interfaces stabilize, but the core API must not depend on a particular FFI.

The project is still in its documentation and architecture phase. The repository does not yet contain a `pyproject.toml`, Python package, or automated tests. Never claim that commands which do not yet exist have passed.

## Repository structure

Currently present:

- `README.md`: project goals, scope, and design principles. `README_zh.md` is its Chinese translation.
- `docs/architecture.md`: authoritative architecture, interface direction, modality fundamentals, milestones, and compliance boundaries. `docs/architecture_zh.md` is its Chinese translation.

Target structure:

- `platydiff/core/`: public models, plugin registration, pipeline, policies, and provenance; keep it lightweight.
- `platydiff/comparators/`: modality-specific comparators; load heavyweight dependencies only when required.
- `platydiff/renderers/`: terminal, JSON, HTML, JUnit, and other outputs; consume only the public result model.
- `platydiff/cli/`: argument parsing, configuration loading, exit codes, and user-facing errors.
- `platydiff/plugins/`: built-in extension entry points and third-party plugin adapters.
- `tests/unit/`: pure unit tests with no network or external-program dependencies.
- `tests/integration/`: cross-module, CLI, and optional-backend tests.
- `tests/corpus/`: explicitly licensed, size-bounded synthetic test data.
- `docs/`: architecture, public behavior, algorithm provenance, and compliance documentation.

The core dependency direction must remain:

```text
CLI / renderers / comparators / plugins
                 ↓
               core
```

`core` must not import concrete comparators, renderers, or heavyweight optional dependencies.

## Development commands

### Current repository

Before the Python project scaffold exists, documentation changes must run at least:

```bash
git diff --check
```

Also verify manually that relative Markdown links resolve and that documented commands match the repository's actual state.

### Required baseline after Python bootstrap

The first `pyproject.toml` must make the following commands the repository's standard development interface. Do not create overlapping helper scripts.

Install the development environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the CLI:

```bash
python -m platydiff --help
platydiff --help
```

Format and lint:

```bash
python -m ruff format --check .
python -m ruff check .
```

Type-check:

```bash
python -m mypy platydiff tests
```

Test:

```bash
python -m pytest
python -m pytest -m "not media and not external"
python -m pytest -m media
python -m pytest -m external
```

Build:

```bash
python -m build
```

Use the `media` marker for tests that require large media fixtures and `external` for tests that require system programs such as FFmpeg or a PDF renderer. The scaffold must register these markers in `pyproject.toml` and report clear skip reasons when optional backends are unavailable.

## Coding conventions

- Use `snake_case` for modules, functions, and variables; `PascalCase` for types; and `UPPER_SNAKE_CASE` for constants.
- Use stable lowercase ASCII identifiers for plugin IDs, capability names, metric names, and serialized fields. Do not rename public identifiers merely for aesthetics.
- New code must have complete type annotations. Avoid `Any`; parse untrusted data as `object`, validate it, and then narrow the type.
- Prefer standard, serializable data structures for public models. `DiffResult` must not contain third-party objects that cannot be serialized consistently.
- `CompareSpec` describes user intent; the capability registry resolves algorithms and backends. Do not leak backend-specific parameters into unrelated modalities.
- Normalization and alignment must remain visible, must be possible to disable, and must be recorded. A metric implementation must never silently resize, crop, resample, sort, or discard data.
- Results must state metric name, value, unit, direction, threshold, and aggregation method. Do not conflate exact equality, structural equality, perceptual similarity, and statistical equivalence.
- Prefer determinism: keep ordering stable, pass explicit seeds to random processes, and test floating-point and time-dependent behavior.
- Core code must not call `print` or exit the process. Raise project-defined exceptions or return structured errors; let the CLI map them to messages and exit codes.
- Do not catch a bare `Exception` and continue silently. Degradation must produce a visible warning and record the selected backend and lost information.
- Invoke subprocesses with argument arrays and `shell=False`; set timeouts, validate exit codes, bound temporary-file scope, and never interpolate untrusted input into a command string.
- Configuration must not use `eval`, `exec`, or executable templates. Custom rules must use a restricted DSL or an explicit Python plugin.
- Prefer the standard library and existing dependencies. Before adding a dependency, document its purpose, optionality, license, size, platform support, and alternatives.
- Heavyweight or strong-copyleft dependencies must not enter default core dependencies. Integrate them through extras, plugins, or external-program boundaries and document the compliance conditions.
- Do not expand scope with opportunistic cleanup, and do not overwrite unrelated local changes.

## Public contracts

Once included in the first public release, the following are public API:

- The fields and serialized forms of `CompareSpec` and `DiffResult`.
- Plugin protocols, capability names, plugin discovery entry points, and error types.
- CLI commands, options, exit codes, and JSON output.
- Metric names, units, directions, and default aggregation rules.
- Configuration keys and their default behavior.

Any public-contract change must update the documentation, migration notes, and compatibility tests. Unless a task explicitly requires it, do not remove fields, change their meaning, reuse exit codes, or silently change default comparison strategies.

## Safety and modification boundaries

You may modify:

- Source, tests, documentation, and configuration directly related to the current task.
- Synthetic fixtures, schemas, and compatibility tests added for new behavior.

Do not modify casually:

- The bytes, license, or expected result of an existing fixture under `tests/corpus/`; add a versioned fixture and explain why instead.
- Published public APIs, configuration schemas, plugin IDs, metric semantics, or CLI exit codes.
- Unrelated dependencies in lockfiles; dependency additions and upgrades must be intentional.
- Third-party licenses, NOTICE files, SBOMs, or algorithm-provenance records.
- Data migrations or compatibility layers; never delete old migrations or replace them by rewriting history.

The following are generated artifacts. Do not edit or commit them manually unless a release process explicitly requires it:

- `dist/`, `build/`, `*.egg-info/`
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `.coverage`, `htmlcov/`
- Local decode caches, temporary frames, waveforms, heatmaps, and report previews

Never commit secrets, tokens, `.env` files, unpublished scientific data, competition-restricted data, personal information, or media whose license prohibits redistribution.

## Testing and verification

Match verification effort to change risk:

| Change type | Minimum verification |
| --- | --- |
| Documentation only | `git diff --check`; verify links, paths, and command accuracy |
| Python source | Ruff format, Ruff lint, mypy, and the complete pytest suite |
| One comparator | All Python checks; tests for normal, boundary, corrupt-input, threshold, and deterministic behavior |
| CLI or configuration | All checks; CLI integration tests, exit codes, error text, and backward compatibility |
| Public models or plugin protocol | All checks; serialization snapshots, compatibility tests, documentation, and changelog |
| Audio/video/PDF backend | All checks; relevant marker tests; record external-program versions and missing-backend behavior |
| Packaging or dependencies | All checks; `python -m build`; inspect wheel/sdist contents and license inventory |
| Performance or large-file path | Correctness checks; representative benchmarks; confirm memory use is bounded |

When fixing a bug, first add a test that reproduces it. Comparator tests must cover at least identical inputs, completely different inputs, empty inputs, a single-point change, repeated elements, ordering changes, corrupt inputs, and over-limit inputs. Numeric tests must also cover NaN, Inf, dtype, units, `atol`/`rtol`, and boundary values.

If optional dependencies are missing, report that targeted tests were skipped; never describe an unrun test as passing. When handing off work, list the commands actually executed and their results.

## Documentation

- English is the canonical and default documentation language for people and agents.
- Keep English documentation at the default path and store Chinese translations beside it with the `_zh.md` suffix, for example `README.md` and `README_zh.md`.
- Keep each translation aligned with its English source when behavior or policy changes. Link the English and Chinese versions to each other.
- When behavior, configuration, CLI, public API, defaults, or supported formats change, update `README.md` and `docs/` in the same change.
- Record a new algorithm's papers or standards, applicability, known failure modes, and license or patent considerations.
- Examples must be executable and use synthetic or explicitly licensed data.
- Mark planned capabilities as planned; never describe them as implemented.

## Git and review workflow

- Create short-lived branches from `main`; agents use `codex/<short-description>` by default.
- Keep commits small and focused. Conventional Commits are recommended: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `build:`, and `chore:`.
- Do not rewrite shared history or force-push. Do not mix unrelated formatting, dependency upgrades, and feature changes in one commit.
- PR descriptions must state motivation, behavior changes, comparison semantics, verification commands actually run, optional-dependency changes, and data or license impact.
- Public-behavior changes require a changelog entry; breaking changes also require migration notes.
- Before committing, inspect `git diff` and `git status` to ensure there are no generated artifacts, secrets, restricted data, or unrelated files.

## Code review rules

Prioritize the following project-specific risks during review:

1. **Semantics**: Is the code comparing byte, structural, perceptual, or statistical equivalence, and do its name and documentation match?
2. **Alignment**: How are lines, keys, coordinates, pages, samples, and timelines matched? Can an alignment failure be misreported as a content difference?
3. **Hidden transformations**: Are color space, orientation, alpha, sample rate, frame rate, units, dtype, time zones, key ordering, or NaN behavior changed silently?
4. **Reproducibility**: Do input hashes, configuration, plugins, backend versions, seeds, and aggregation methods enter provenance?
5. **Numeric correctness**: Are tolerance formulas, overflow, precision, normalization, units, and metric direction correct? Are p-values accompanied by effect size and sample size?
6. **Resource boundaries**: Are large files streamed? Do compressed bombs, corrupt media, infinite streams, overlong lines, and malicious PDFs have explicit limits?
7. **Optional dependencies**: Do core imports and the basic CLI still work without media, PDF, or AST backends?
8. **Error behavior**: Are unsupported, failed, skipped, and degraded outcomes distinguishable? Can an error incorrectly return success?
9. **Result contract**: Is JSON stable and serializable? Do renderers interpret results without recomputing or changing their semantics?
10. **Compliance**: Do new code, models, fixtures, codecs, and external binaries have clear provenance, licenses, and redistribution permission?

## Subdirectory-specific guidance

Add subdirectory rules only when the root rules are insufficient; do not duplicate this entire file:

- `platydiff/comparators/AGENTS.md`: modality IRs, numeric constraints, and fixture requirements.
- `platydiff/core/AGENTS.override.md`: stricter public-contract, dependency-direction, and compatibility rules.
- `tests/corpus/AGENTS.override.md`: data provenance, license, size, redaction, and determinism rules.
- `docs/AGENTS.md`: citation format, algorithm provenance, and documentation verification.

Each subdirectory file should contain only its differences and clearly state which root rules it overrides or supplements.

## AgentGit workflow

This project requires AgentGit to preserve and synchronize every Codex and development-agent conversation. Project code remains under the current Git repository; AgentGit manages only session context, VIEWs, events, shared memory, and skills. The fixed Agent repo is the public repository `chenapr/platydiff`.

- At the start of every session, run `agit status`. If the current session is unmanaged, run `agit status --check-missing` and import the active conversation into a unique session branch in `chenapr/platydiff`; never choose a different Agent repo based only on the directory name.
- Adopt an already running Codex conversation with `agit import @ --repo chenapr/platydiff -b <unique-session-branch>`; do not use `agit new` instead of importing the current conversation.
- Use a short, unique task name for a session branch. Do not use `main` or a name beginning with `agit-`. `main` is reserved for AgentGit shared files.
- One user turn normally corresponds to one AgentGit commit. After completing a phase, run `agit commit --milestone "<summary>"`; add `--code` only when also committing project code and establishing a cross-link.
- `agit commit` writes only to the local Agent repo and does not upload automatically. After committing, explicitly run `agit push chenapr/platydiff -b <session-branch>`; when the shared file line changes, separately run `agit push chenapr/platydiff -b main`.
- The first publication and repository visibility must be public; never make this project's Agent repo private. Before uploading, ensure the conversation contains no secrets, tokens, restricted competition data, personal information, or unpublished scientific data.
- Before ending a task, run `agit status` and report any uncommitted or unpushed state. The currently executing turn cannot be fully settled until it ends, so run `agit commit` and `agit push` again in the next turn when necessary.
- Do not confuse project Git with AgentGit, and do not rewrite history manually under `~/.agit/repos`. Rebase, amend, and force-push are prohibited for AgentGit.

<!-- agit:begin -->
## Session version control (agit)

This project's agent sessions are managed by agit. Rules:

- Settle when a phase completes: `agit commit --milestone "<summary>"` (add `--code` when relevant).
- `agit status` at session start; if you were resumed as a merge agent, follow the `AGIT_MERGE_TX` protocol (see the agit skill).
- Never rebase / force-push; remove context with `agit revert @#n.k`.
<!-- agit:end -->
