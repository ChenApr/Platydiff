# Platydiff Architecture

[Chinese documentation](architecture_zh.md)

## 1. Product positioning

`platydiff` is a multimodal difference-analysis framework for scientific visualization data, experimental regression testing, and competition workflows. It is neither a wrapper around a single algorithm nor a system that reduces every input to bytes or text. Instead, it gives different modalities a shared execution model, configuration protocol, and result protocol.

The project must answer four distinct kinds of questions:

1. **Exact equality**: Are two objects identical at the byte, sample, or element level?
2. **Transformability**: Which insert, delete, replace, or copy operations transform A into B?
3. **Structural change**: Which fields, syntax nodes, page objects, or shot structures changed?
4. **Perceptual or statistical difference**: Is a change perceptible, or does it exceed the practical tolerance defined by a scientific task?

The primary deliverables are a Python library and a command-line tool. Notebook components, desktop or web reports, and CI integrations may follow. The core must remain lightweight; expensive parsing and multimedia processing belong in optional plugins or external backends.

## 2. Overall pipeline

```text
Input A / Input B
        │
        ▼
Format Detection
        │
        ▼
Decode → Typed Intermediate Representation
        │
        ▼
Normalize → Align → Compare → Aggregate
        │
        ▼
Common DiffResult
        │
        ├── Terminal
        ├── JSON
        ├── HTML
        ├── JUnit / CI
        ├── Patch
        └── Heatmap / Waveform / Frames
```

Each stage has a distinct responsibility:

| Stage | Responsibility | Examples |
| --- | --- | --- |
| Detect | Identify the format and candidate plugins | File extension, MIME type, magic bytes, content probing |
| Decode | Convert input into a modality-specific intermediate representation | Text lines, AST, RGBA pixels, PCM samples, video frames, data tables |
| Normalize | Remove differences that are irrelevant to the task | Line endings, key order, metadata, color space, sample rate |
| Align | Establish comparable correspondences | Lines, fields, primary keys, coordinates, timestamps, frames, pages |
| Compare | Produce local differences and metrics | Edit scripts, field changes, error matrices, quality scores |
| Aggregate | Summarize results and evaluate rules | Maximum error, quantiles, failure thresholds, warnings |
| Render | Present results to people or machines | Hunks, heatmaps, HTML, JSON, JUnit |

There is no single universal intermediate representation. The framework should define typed structures such as `TextIR`, `TreeIR`, `ImageIR`, `AudioIR`, `VideoIR`, `DocumentIR`, and `TableIR`, while giving them shared metadata, provenance, and lifecycle conventions.

## 3. Module structure

```text
platydiff/
├── core/
│   ├── models.py          # CompareSpec, DiffResult, and shared types
│   ├── registry.py        # Plugin discovery, capability declarations, and priority
│   ├── pipeline.py        # Stage scheduling, caching, cancellation, and error boundaries
│   ├── policies.py        # Tolerance, ignore, and pass/fail rules
│   └── provenance.py      # Input hashes, parameters, environment, and version records
├── comparators/
│   ├── binary.py
│   ├── text.py
│   ├── source_code.py
│   ├── structured.py
│   ├── image.py
│   ├── audio.py
│   ├── video.py
│   ├── pdf.py
│   └── tabular.py
├── renderers/
│   ├── terminal.py
│   ├── json.py
│   ├── html.py
│   └── junit.py
├── plugins/               # Built-in extension entry points and third-party adapters
├── cli/                   # Argument parsing, configuration loading, and exit codes
└── tests/corpus/          # Synthetic and explicitly licensed test samples
```

The core layer must not depend directly on heavyweight media or PDF engines. Comparators declare additional capabilities and dependencies. When a backend is unavailable, the system returns a structured `capability_unavailable` result instead of silently degrading or producing irreproducible output.

## 4. Abstract interfaces

The following Python pseudocode describes the plugin boundary without prescribing a final class hierarchy or framework:

```python
class DiffPlugin(Protocol):
    id: str
    version: str
    capabilities: set[str]

    def probe(self, source: Source) -> ProbeResult: ...
    def decode(self, source: Source, spec: CompareSpec) -> ArtifactIR: ...
    def normalize(self, artifact: ArtifactIR, spec: CompareSpec) -> ArtifactIR: ...
    def align(
        self, before: ArtifactIR, after: ArtifactIR, spec: CompareSpec
    ) -> Alignment: ...
    def compare(
        self,
        before: ArtifactIR,
        after: ArtifactIR,
        alignment: Alignment,
        spec: CompareSpec,
    ) -> DiffResult: ...
```

### 4.1 CompareSpec

`CompareSpec` describes user intent rather than binding the request to a particular algorithm implementation:

```yaml
type: table
mode: statistical

align:
  keys: [case_id, timestep]

ignore:
  columns: [generated_at, run_id]

numeric:
  atol: 1.0e-8
  rtol: 1.0e-5
  nan_equal: true

statistics:
  tests: [ks, wasserstein]
  report_effect_size: true

fail_when:
  max_changed_rows: 0
  max_rmse: 1.0e-4

output:
  formats: [terminal, json, html]
```

Configuration expressions must use a restricted rule language. They must never execute arbitrary Python through `eval`, executable templates, or similar mechanisms.

### 4.2 DiffResult

The authoritative execution-outcome and completed-result contract is [RFC 0001](rfcs/0001-comparison-outcome-and-diff-result.md). The structure below is an earlier architectural sketch; implementations must follow the RFC where the two differ.

```text
DiffResult
├── equal               # Whether the inputs are equal under the active rules
├── status              # pass / warn / fail / error
├── summary             # Short cross-modality summary
├── changes[]           # Lines, fields, regions, pages, or time intervals
├── metrics[]           # Values, units, directions, and thresholds
├── artifacts[]         # Patches, heatmaps, waveforms, frame captures, and similar outputs
├── warnings[]
└── provenance
    ├── input hashes
    ├── normalized parameters
    ├── plugin/backend versions
    ├── environment
    └── timestamps and duration
```

Comparators should also declare result properties: whether the comparison is symmetric, whether it satisfies metric-space properties, whether it can produce a reversible patch, whether it is deterministic, and whether alignment or normalization is lossy.

## 5. Foundation and implementation path

### 5.1 Technology stack

The first version will use Python because of its mature scientific and data ecosystem and its ability to integrate quickly with Notebook and competition scripts:

- The standard library handles files, hashes, text, and basic concurrency.
- NumPy and SciPy handle arrays, signals, and statistical computations.
- pandas and xarray handle tables, labeled coordinates, and multidimensional scientific data.
- Pillow, OpenCV, and scikit-image are optional image backends.
- Tree-sitter is an optional source-code parsing backend.
- FFmpeg and ffprobe are optional external audio/video backends.
- PDF support uses replaceable text-extraction and page-rendering backends.

After interfaces stabilize, performance-critical paths may use Rust extensions, including large-file chunking, Myers edit paths, binary block indexes, and parallel metric computation. The core API must not depend prematurely on a particular FFI implementation.

### 5.2 Execution and caching

- Use streaming reads, memory mapping, or chunked computation for large files to avoid unbounded memory usage.
- Build intermediate-artifact cache keys from input hashes, normalization parameters, plugin versions, and backend versions.
- Run media and PDF parsing in bounded workers with time, memory, disk, and process limits.
- Record every automatic downsampling, crop, resampling operation, or color conversion in result provenance.
- Support cancellation and stage-level errors. A renderer failure must not invalidate an already produced core result.
- Keep every human review surface downstream of validated outcome semantics. The
  proposed renderer and UI sequence is defined in [RFC 0004](rfcs/0004-human-review-ui-and-renderer-boundary.md)
  and is not authorized while that RFC remains Proposed.

## 6. Modality fundamentals

### 6.1 Binary

Exact comparison includes whole-file hashes, byte-by-byte scanning, and block digests. When patch generation is required, rolling hashes, suffix indexes, or common-block searches can express the result with instructions such as `COPY` and `ADD`. Binary comparison does not understand content semantics: recompression can produce a large byte-level difference even when the perceptual content is unchanged.

### 6.2 Text

Text processing first applies explicit encoding and line-ending policies, then tokenizes by line, word, or character. The core uses an LCS/Myers-family sequence algorithm to generate insert/delete edit scripts and groups adjacent changes into hunks. Patience or Histogram diff can be optional strategies that use unique or low-frequency lines as anchors to improve readability when code is reordered.

### 6.3 Source code and configuration

Source code can be parsed into syntax trees and matched by node, reducing the weight of formatting-only changes while expressing node insertion, deletion, update, and movement. JSON, YAML, TOML, and XML should be parsed into typed trees or mappings and compared by field path. Key ordering, numeric representation, and irrelevant metadata belong to the configurable normalization stage.

Syntactic equality does not imply runtime semantic equality. AST comparison must state its parser version, error-recovery behavior, and macro or preprocessing boundaries.

### 6.4 Images

In exact mode, both images are decoded to an explicitly selected size, orientation, color space, and alpha representation before pixel-level comparison. Outputs can include changed-pixel count, MAE, RMSE, PSNR, and heatmaps. Structural or perceptual modes can use SSIM, MS-SSIM, LPIPS, or perceptual hashes.

A one-pixel translation can create a large apparent difference. Registration, cropping, and scaling therefore belong to a separate alignment stage and must never be hidden inside a metric implementation.

### 6.5 Audio

Audio comparison first applies explicit sample-rate, channel, and sample-format policies, then aligns by timestamp or cross-correlation. It can compare PCM waveforms, STFT or Mel spectra, SNR, or perceptual quality. Millisecond delays, gain changes, and resampling can all break exact sample comparison, so the system must distinguish “identical signal” from “perceptually similar.” ViSQOL, PESQ/POLQA, and comparable systems belong in optional backends rather than core dependencies.

### 6.6 Video

Video comparison requires demuxing, decoding, timeline alignment, explicit frame-rate and resolution policies, and color-space normalization before computing per-frame metrics such as PSNR, SSIM, or VMAF and aggregating them over time. Detecting edits, inserted frames, and reordered shots requires shot segmentation, frame fingerprints, or feature-sequence matching; quality metrics alone are insufficient. Audio tracks should be compared as a separate modality and associated with the video timeline.

### 6.7 PDF

A PDF contains text, drawing instructions, fonts, images, and page layout. The system should provide three composable views: extracted-text comparison, PDF object and metadata comparison, and image comparison of rendered pages. Different generators can create radically different internal objects while producing visually identical pages, so binary diff alone is insufficient.

### 6.8 Tables, arrays, and statistical data

The comparison order is schema, dimensions, coordinate or primary-key alignment, element tolerances, aggregate errors, and distribution differences. Policies must define dtype, units, missing values, NaN/Inf handling, absolute and relative error, and floating-point ULP behavior.

Statistical comparison can include KS tests, Wasserstein distance, chi-squared tests, confidence intervals, and effect sizes. A p-value alone must not determine whether a practically meaningful difference exists. Results should also report effect size, sample size, multiple-comparison correction, and the practical tolerance defined by the scientific task.

## 7. Milestones

The staged delivery plan and its implementation gates are defined by [RFC 0002](rfcs/0002-development-phases-and-text-slice.md). The proposed Phase 2 detection, internal resolution, and exact-binary contract is [RFC 0003](rfcs/0003-automatic-detection-capability-resolution-and-binary-comparison.md). The version groupings below describe product direction; they do not override the RFCs' narrower, explicitly authorized phases or imply that a capability is implemented.

Phase 1 is implemented on the default branch and contains the Python package,
schema-v1 contracts, explicit text pipeline, linear-space Myers algorithm,
CLI, and terminal/JSON renderers. It remains unreleased. Every other modality
and renderer listed below remains planned.

### v0.1: Core loop

- Plugin registration, `CompareSpec`, `DiffResult`, and provenance records.
- Binary, text, JSON/YAML, CSV/array, and image comparison.
- Terminal, JSON, and static HTML output.
- Reproducible test corpora and deterministic CI.

### v0.2: Structure and documents

- Tree-sitter-based source comparison.
- XML/TOML support and complex table alignment.
- Combined PDF text and rendered-page comparison.
- JUnit output and benchmark-result management.

### v0.3: Time-based media

- Audio temporal and spectral comparison.
- Video frame, timeline, and quality metrics.
- Optional FFmpeg, ViSQOL, and VMAF backends.
- A plugin SDK and third-party capability catalog.

## 8. Compliance and security checklist

### 8.1 Source code and algorithms

- Implement core code independently; do not copy source code, comments, tests, or documentation wording from other projects.
- Maintain `docs/algorithm-references.md` for algorithms derived from papers, standards, or other public sources.
- Confirm license compatibility before introducing code. Public visibility does not imply permission to reuse.
- If commercialization is planned, assess multimedia algorithm patent risks in every target jurisdiction.

### 8.2 Open-source licenses and dependencies

- Apache-2.0 is the candidate project license because it offers permissive usage terms and an explicit contributor patent grant. Finalize the choice before the first release.
- Record the SPDX identifier, version, source, purpose, and distribution method of every dependency.
- Provide `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES`, and an SBOM.
- Isolate GPL/AGPL, commercial dual-licensed, and license-unclear implementations behind optional backends, then assess their combination and distribution obligations separately.
- Invoking an external CLI does not automatically remove compliance obligations. Bundling its binary still requires compliance with its license.

### 8.3 Audio, video, and PDF

- Do not bundle FFmpeg or codec binaries by default; prefer discovering tools installed by the user.
- Record the FFmpeg build configuration and avoid distributing combinations built with `nonfree` components.
- Assess open-source license compliance separately from potential H.264, H.265, AAC, and similar patent-license obligations.
- Review PDF rendering backends individually to avoid unintentionally incorporating a strong-copyleft dependency into a permissively licensed core.

### 8.4 Data and competition rules

- Keep only self-generated, public-domain, or explicitly redistributable data in the test repository.
- For restricted data, use download scripts, hashes, or local fixtures rather than uploading original files.
- Follow competition rules concerning test sets, hidden labels, model outputs, derived data, and external tools.
- Do not embed complete inputs in reports by default. Require users to opt in before including thumbnails, text excerpts, or media clips.
- Provide redaction and local-processing policies for personal information, unpublished research data, and file metadata.

### 8.5 Project governance

- Determine whether the code constitutes work owned by a school, laboratory, grant-funded project, or employer.
- Use a DCO or CLA for external contributions and require clear declarations of contribution license and provenance.
- The project name, logo, and documentation must not imply an official relationship with Git, FFmpeg, or other projects.
- The release process must run license scanning, secret scanning, SBOM generation, and test-data provenance checks.

## 9. Definition of done

A comparator is releasable only when it meets all of the following requirements:

1. Its supported formats, semantics, and unsupported scenarios are documented.
2. Its normalization and alignment steps can be disabled, configured, and audited.
3. Its metrics define units, direction, thresholds, and interpretation.
4. Its behavior for empty, corrupt, oversized, and malicious inputs is explicit.
5. Its results are serializable and reproducible within the same environment.
6. The provenance of test data and the licenses of all runtime dependencies are recorded.
