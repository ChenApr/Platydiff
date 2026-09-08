# Platydiff RFCs

[Chinese documentation](README_zh.md)

This directory contains accepted and proposed design decisions for Platydiff. English RFCs are canonical. Chinese translations use the `_zh.md` suffix and must remain aligned with their English source.

## Status definitions

- **Proposed**: open for design review and not authorized for implementation.
- **Accepted**: approved as an implementation contract.
- **Implemented**: present on the default branch, aligned with its documentation,
  and covered by the required compatibility tests. Release status is tracked
  separately.
- **Superseded**: replaced by another RFC; the replacement must be linked.

## Index

| RFC | Status | Decision |
| --- | --- | --- |
| [0001](0001-comparison-outcome-and-diff-result.md) | Implemented | Separate execution outcomes from completed difference results and define schema-v1 result semantics |
| [0002](0002-development-phases-and-text-slice.md) | Implemented | Gate the first Python/text slice and defer later capabilities behind explicit contract reviews |
| [0003](0003-automatic-detection-capability-resolution-and-binary-comparison.md) | Implemented | Define bounded automatic detection, deterministic internal capability resolution, and exact binary comparison |
| [0004](0004-human-review-ui-and-renderer-boundary.md) | Proposed | Keep human review surfaces downstream of validated outcomes and stage terminal, HTML, TUI, and desktop work |

Planned behavior must remain explicitly marked as planned until implementation and verification are complete.
