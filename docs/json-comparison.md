# JSON comparison

[Chinese documentation](json-comparison_zh.md)

Phase 4 gate P4-A1 implements the JSON portion of
[RFC 0006](rfcs/0006-structured-data-comparison.md). It adds no runtime
dependency and does not implement YAML, tables, arrays, structured automatic
detection, or a new plugin SDK.

## Entry points and schema

The CLI aliases below execute the same built-in path:

```bash
platydiff json before.json after.json
platydiff compare --type json before.json after.json
```

Python callers pass `JsonCompareSpec` to the existing three-argument `compare`
function. Every JSON outcome is schema v3, including sourcing, decoding, and
comparison failures. Existing direct text, binary, and auto comparisons remain
schema v1; existing SDK-v1.1 plugin-host comparisons remain schema v2. A
`PluginHost` rejects JSON intent as resolving-stage `capability_unavailable`,
and JSON CLI routes reject plugin-related flags as usage exit `2` before plugin
discovery.

Schema-v3 readers also accept v1 and v2. Use
`upgrade_outcome_v1_to_v3` or `upgrade_outcome_v2_to_v3` explicitly. The
`downgrade_outcome_v3_to_v2` helper succeeds only after validating legacy-only
intent and changes, or preserved legacy host context for a terminal outcome; it
never drops a structured change or guesses when legacy provenance is absent.

## Equality and changes

The parser accepts exactly one strict RFC 8259 value followed by JSON
whitespace. UTF-8 is strict, and only `utf-8-sig` removes a BOM. Comments,
trailing commas, duplicate decoded keys, NaN, infinities, and unpaired surrogate
escapes fail with `decode_error`.

Mappings compare by decoded Unicode key in code-point order; member order and
escape spelling are ignored. Sequences compare by position. Strings are not
case-folded, whitespace-normalized, or Unicode-normalized. Changes use canonical
RFC 6901 JSON Pointers and deterministic depth-first pre-order. A wholly added
or removed subtree is one change at its highest pointer; moves are not inferred.

The default `number_mode="value"` compares sign, coefficient, and adjusted
base-10 exponent without binary floating point, so `1`, `1.0`, and `1e0` are
equal and signed zero is equal. `number_mode="lexical"` instead compares each
valid source token exactly.

The result records `json.compared_values`, `json.equal_values`, and
`json.changed_values`; equal plus changed equals compared, and changed equals
`changes.total_count`. The sole evaluation, `json.semantic_equality`, passes
only when changed values is zero. Comparison completes before detail truncation,
so limits never weaken relation, verdict, totals, or metrics.

## Facts, digests, and privacy

`detail_mode="values"` returns typed scalar facts or bounded non-recursive
subtree counts. `detail_mode="digest_only"` omits all facts before rendering,
but preserves comparison truth and deterministic evidence digests. Evidence
digests are domain-separated SHA-256 integrity fingerprints. They are not
encryption or anonymous redaction: low-entropy values may be guessed, and paths,
input hashes, types, counts, and digest equality remain visible. Protect either
outcome as source-derived metadata.

Terminal rendering escapes control and bidirectional characters in paths and
facts. JSON rendering emits the exact validated schema-v3 envelope. Renderers
never reread inputs and cannot recover omitted facts.

## Limits and failures

All limits accept non-negative exact integers no greater than `2**53`:

| CLI option | Default | Meaning |
| --- | ---: | --- |
| `--max-input-bytes` | 16 MiB | Original bytes per source before decoding |
| `--max-scalar-bytes` | 1 MiB | UTF-8 bytes in one decoded string or key |
| `--max-depth` | 256 | Root-relative container depth |
| `--max-nodes` | 1,000,000 | Parsed value nodes per source |
| `--max-number-digits` | 10,000 | Digits in one validated number token |
| `--max-abs-exponent` | 1,000,000 | Adjusted base-10 exponent magnitude |
| `--max-compare-work` | 5,000,000 | Visited paired or unmatched tree nodes |
| `--max-change-items` | 10,000 | Returned source-order changes |
| `--max-change-payload-bytes` | 4 MiB | Compact UTF-8 schema bytes of returned changes |

Input bounds fail with `resource_limit_exceeded` at the observed sourcing or
decoding stage. Work exhaustion fails with `compare_resource_limit` while
comparing. Change item or payload exhaustion returns a completed result with a
`truncated` source-order prefix and `change_details_truncated` diagnostic. CLI
exit codes remain `0` for pass, `1` for completed fail, `2` for usage, and `3`
for unavailable, failed, or renderer failure.
