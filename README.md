# Platydiff

[Chinese documentation](README_zh.md)

`platydiff` is a multimodal diff engine for scientific research, data analysis, and competition workflows. It aims to compare binary data, text, source code, structured configuration, images, audio, video, PDFs, tables, and statistical data through a unified command, configuration format, and result protocol, while allowing users to customize normalization, alignment, tolerances, comparison metrics, and output formats for each task.

## Project goals

- Organize comparisons across modalities with one stable pipeline instead of forcing every file into text.
- Support distinct meanings of “equal,” including exact equality, structural equality, perceptual similarity, and statistical equivalence.
- Make comparison rules configurable and reproducible, with first-class support for command-line, Python, Notebook, and CI workflows.
- Produce both machine-readable results and human-readable reports, including JSON, terminal output, HTML, JUnit, heatmaps, and time intervals.
- Extend file formats, algorithms, decoders, and renderers through plugins.
- Record input hashes, tool versions, and parameters explicitly for scientific reproducibility and competition audits.

## Planned format coverage

| Category | Primary comparison capabilities |
| --- | --- |
| Binary | Hashing, byte-by-byte comparison, and block-level differences |
| Text | Line-, word-, and character-level diffs and unified diff output |
| Source code | Syntax-tree-aware structural changes |
| Configuration | Path-level changes in JSON, YAML, TOML, and XML |
| Images | Pixel heatmaps, MAE, RMSE, PSNR, SSIM, and perceptual metrics |
| Audio | Temporal alignment, waveform, spectral, and perceptual-quality comparison |
| Video | Frame alignment, per-frame metrics, temporal aggregation, and shot changes |
| PDF | Combined text, object-structure, and rendered-page comparison |
| Statistical data | Schema, index, numeric tolerance, distribution, and effect-size comparison |

## Design principles

1. **One pipeline, modality-specific semantics**: Share the detection, normalization, alignment, comparison, aggregation, and rendering stages while using modality-specific intermediate representations.
2. **Separate policy from implementation**: Users describe what to compare; plugins decide how to compare it.
3. **Reproducibility first**: Results must include input digests, runtime parameters, backends, and version information.
4. **Composable results**: Every comparator emits the shared `DiffResult`, enabling reuse by terminal, reporting, and CI integrations.
5. **Safe defaults**: Never execute arbitrary code from configuration; apply resource limits to parsers, media decoders, and untrusted files.
6. **Auditable compliance**: Track licenses and provenance separately for core code, optional backends, test data, and generated artifacts.

See [docs/architecture.md](docs/architecture.md) for the detailed design.

## Current status

The project is in the architecture-design phase. The first implementation milestone will prioritize binary, text, structured configuration, table/array, and image comparison, followed by source code, PDF, audio, and video support.
