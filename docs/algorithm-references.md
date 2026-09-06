# Algorithm references

[Chinese documentation](algorithm-references_zh.md)

## `text.myers.linear_space.v1`

Platydiff's text edit engine is an independent implementation of the
middle-snake, divide-and-conquer refinement described by Eugene W. Myers in
“An O(ND) Difference Algorithm and Its Variations,” *Algorithmica* 1,
251–266 (1986), [doi:10.1007/BF01840446](https://doi.org/10.1007/BF01840446).
No source code, comments, tests, or documentation text were copied from another
implementation.

The algorithm applies to sequences of normalized `TextLine` values and returns
a shortest script containing insertions and deletions. Platydiff adds a fixed
deletion-first tie-break, common-prefix and common-suffix trimming, an explicit
task stack, and deterministic work accounting as project-level behavior.

Known constraints and failure modes:

- worst-case time grows with both input size and edit distance;
- repeated lines can have several equally short scripts, so Platydiff's stable
  tie-break is part of the observable behavior;
- the algorithm compares whole normalized lines and does not provide word- or
  character-level similarity;
- exhausting the deterministic work budget returns
  `failed/compare_resource_limit` without a fallback or partial result.

The implementation is distributed under the project's Apache-2.0 license. The
paper is cited as algorithm provenance and is not redistributed. This record
does not constitute a patent opinion; release review must reassess relevant
claims for intended jurisdictions.
