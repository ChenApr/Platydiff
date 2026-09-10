# RFC 0012: P7-A1 Audio Pre-Code Contract Closure

[Chinese documentation](0012-p7a1-audio-pre-code-contract-closure_zh.md)

- Status: Proposed
- Date: 2026-09-10
- Amends: [RFC 0009](0009-audio-and-video-comparison.md) and
  [RFC 0011](0011-rfc-0009-audio-preflight-amendment.md)
- Owners: Platydiff maintainers
- Implementation owner: none; this proposal does not start code

## Summary and authorization boundary

This Proposed amendment closes remaining P7-A1 pre-code audio contract gaps. It
does not authorize implementation, video, UI, FFmpeg, new dependencies,
automatic media detection, SDK v2, or any schema successor outside audio
schema-v6.

The proposal preserves RFC 0009 and RFC 0011 direction: P7-A1 is audio-only,
uses the stdlib WAV/PCM profile for decoded-sample relations, and remains gated
by accepted RFC 0010 Option A/SP1-SP6 plus actual P4-C1, P5-A1/schema-v4, and
P6-C0/schema-v5 merges. P7-A1 dispatch also requires RFC 0011 and this
amendment, if accepted, to have merged.

## Proposed decisions

These IDs are proposed decisions. They are not implementation contracts until
this amendment is explicitly accepted.

| ID | Proposed decision | Alternative not selected |
| --- | --- | --- |
| P7A-PC1 | Freeze the public carrier fields for equal results and complete decoded-audio facts. | Let renderers infer equal audio identity from backend-local metadata. |
| P7A-PC2 | Freeze continuous grouping for sample and encoded-byte changes, including `change_count`, `samples_changed`, and `bytes_changed` counting. | Emit one change per sample or byte run without stable aggregation rules. |
| P7A-PC3 | Freeze resource limit names, ranges, and units for `max_compare_work`, `max_packets`, `max_decoded_bytes`, and `max_resident_bytes`, with separate single-input and dual-input accounting. | Use backend-dependent or host-dependent resource names and units. |
| P7A-PC4 | Define `encoded_bytes` as a raw byte relation that bypasses WAV probing and decoding, accepts arbitrary byte streams, and allows limit value `0` to mean no bytes may be compared. | Require WAV validity before encoded-byte comparison. |
| P7A-PC5 | Freeze the timestamp, delay, and padding chunk recognition list and require every user-facing explanation to appear only in `problem.message`; structured values appear only in `problem.details`. | Duplicate explanatory prose inside detail values. |
| P7A-PC6 | Preserve schema-v6 as exclusively audio and keep video roadmap-only. | Let this closure allocate video schema membership. |

## Equal result carrier

For P7-A1 audio, an equal result is still a normal schema-v6 `DiffResult`.
The public carrier for audio-specific equality is:

| Field | Required value |
| --- | --- |
| `schema_version` | `6` |
| `modality` | `"audio"` |
| `outcome` | `"equal"` |
| `media_evaluations` | ordered list of selected audio relation evaluations |
| `changes.change_count` | `0` |
| `changes.items` | empty list |
| `metrics` | includes comparison totals for every selected relation |
| `provenance` | includes selected comparator, backend, profile, resource limits, normalization, alignment, and input digests |

For equal decoded-sample comparison, the first `media_evaluations` entry has:

| Field | Required value |
| --- | --- |
| `kind` | `"media_view_evaluation"` |
| `modality` | `"audio"` |
| `relation` | `"decoded_samples"` |
| `status` | `"compared"` |
| `comparison` | `"exact"` |
| `backend` | `"stdlib_wave_pcm"` |
| `profile` | `"p7_a1_wav_pcm"` |
| `stream.index` | `null` or `0` after default insertion, reported as selected stream `0` in provenance |

Complete decoded-audio fact carriers are closed objects with key order:

```text
name, value, unit, stream_index, coordinate, source
```

`source` is one of `"container"`, `"format"`, `"decode"`, `"derived"`, or
`"policy"`. Equal decoded-sample results must carry, at minimum, facts for:

```text
container.form
container.endianness
format.tag
format.extensible
sample_rate
channel_count
channel_layout
sample_format
signedness
endianness
container_bits
valid_bits
block_align
byte_rate
sample_count
duration_seconds_exact
duration_seconds_binary64
encoder_delay_samples
encoder_padding_samples
timestamp_origin
```

Absent optional timing facts use value `null`, unit `null`, and source
`"policy"` when the absence is mandated by P7-A1. Recognized but unsupported
metadata uses value `"unknown"` and the unit documented by the fact.

## Change grouping and counts

`ChangeSet.change_count` is the number of emitted `AudioChange` items after
continuous grouping and before renderer truncation. Renderer truncation may
shorten `changes.items`, but it must not change `change_count` or metric
values.

For `decoded_samples`, sample changes are grouped into maximal continuous runs
with the same:

```text
relation, operation, stream_index, channel, before_step, after_step
```

`before_step` and `after_step` are each `1` for replacement runs, `1` and `0`
for deletions, or `0` and `1` for insertions. P7-A1 only enables
sample-index alignment, so insertions and deletions are reserved for later
gates and must not be emitted by decoded-sample comparison. A P7-A1
decoded-sample difference is therefore a `sample_update` run.

For `encoded_bytes`, byte changes are grouped into maximal continuous byte runs
with the same:

```text
relation, operation, before_step, after_step
```

`encoded_byte_update` uses one before byte and one after byte at each step.
`encoded_byte_delete` uses one before byte and no after byte.
`encoded_byte_insert` uses no before byte and one after byte.

Metric counting rules:

| Metric | Count rule |
| --- | --- |
| `audio.samples_changed` | Sum of changed decoded sample positions across all channels after grouping; grouping must not change the total. |
| `audio.bytes_changed` | Sum of changed encoded byte positions; an update counts one byte position, a delete counts one before byte, and an insert counts one after byte. |
| `audio.samples_compared` | Number of decoded sample positions compared, multiplied by selected channel count. |
| `audio.channels_compared` | Number of selected channels that reached comparison. |
| `change_count` | Number of grouped `AudioChange` items. |

## Resource limits

All resource limits are non-negative integers. Unknown limit names are invalid.
Default values are inserted by the schema-v6 reader before comparison.

| Limit | Unit | Single-input range | Dual-input accounting | P7-A1 default |
| --- | --- | --- | --- | --- |
| `max_compare_work` | abstract work units | `0..2^63-1` | sum of both inputs plus comparison work | `100000000` |
| `max_packets` | packet or chunk records | `0..2^31-1` | sum of packets/chunks read from both inputs | `1048576` |
| `max_decoded_bytes` | decoded PCM bytes | `0..2^63-1` | sum of decoded PCM bytes materialized from both inputs | `268435456` |
| `max_resident_bytes` | resident memory bytes | `0..2^63-1` | maximum simultaneous resident bytes for the whole comparison | `134217728` |

`max_compare_work=0` permits only comparisons that can complete with zero
relation work: identical empty encoded-byte inputs or metadata-only failures
before relation work begins. `max_packets=0` forbids reading any packet or WAV
chunk record. `max_decoded_bytes=0` forbids decoding PCM payload bytes.
`max_resident_bytes=0` requires the comparator to fail before allocating
comparison buffers.

Problem details for limit failures use:

| Detail key | Value |
| --- | --- |
| `limit_name` | one of the names above |
| `limit_value` | configured integer |
| `limit_unit` | exact unit string from the table |
| `accounting_scope` | `"single_input"`, `"dual_input_sum"`, or `"comparison_peak"` |
| `measured_value` | integer in the same unit |
| `input_side` | `"before"`, `"after"`, or `"both"` |

## Encoded bytes relation

`encoded_bytes` is a byte relation, not a WAV relation. Selecting
`encoded_bytes` bypasses WAV profile probing, WAV header validation, sample
decoding, channel selection, audio facts derived from WAV headers, and
decoded-sample alignment. It accepts arbitrary byte streams, including empty
streams and malformed WAV files.

For `encoded_bytes`, limit value `0` is legal. With both inputs empty and
`max_compare_work=0`, the result is equal. With any non-empty input and a zero
limit that prevents reading or comparison, the result is a resource-limit
failure at the stage where the limit is proven.

Even though WAV probing is bypassed, source acquisition still applies:
unreadable paths, missing inputs, permission failures, and source size policy
failures remain `sourcing` problems.

## Timestamp, delay, and padding recognition

P7-A1 recognizes only these timing, delay, and padding sources:

| Chunk or source | Facts |
| --- | --- |
| no recognized timestamp source | `timestamp_origin=null`, `timestamp_value=null` |
| RIFF `bext` time reference | `timestamp_origin="bext.time_reference"`, `timestamp_value` as sample count |
| RIFF `smpl` sample period | `timestamp_origin="smpl.sample_period"`, `timestamp_value` as exact rational seconds when internally consistent |
| no recognized delay source | `encoder_delay_samples=null` |
| no recognized padding source | `encoder_padding_samples=null` |
| recognized but unsupported delay/padding metadata | corresponding value `"unknown"` |

All other chunks are metadata facts only when RFC 0011 already allows them as
bounded chunk facts. They must not silently affect sample coordinates,
duration, alignment, or equality.

## Problem message and details

`problem.message` is the only location for user-facing explanatory prose.
`problem.details` is the only location for structured values. Detail values
must be strings, integers, finite JSON numbers, booleans, or `null`; arrays and
objects remain invalid unless a later schema revision explicitly permits them.

Allowed detail keys for this amendment are:

```text
relation
operation
stage
input_side
fact_name
chunk_id
byte_offset
limit_name
limit_value
limit_unit
accounting_scope
measured_value
```

Detail values must not contain backend stderr, exception class names, host
paths, source filenames, safe labels, explanatory sentences, or arbitrary
dictionaries.

## Canonical vectors

These vectors are normative examples for acceptance tests. They are expressed
as canonical JSON fragments after default insertion and before renderer
truncation.

### Vector PC-A: equal empty encoded bytes

```json
{
  "schema_version": 6,
  "modality": "audio",
  "outcome": "equal",
  "media_evaluations": [
    {
      "kind": "media_view_evaluation",
      "modality": "audio",
      "relation": "encoded_bytes",
      "status": "compared",
      "comparison": "exact"
    }
  ],
  "changes": {
    "change_count": 0,
    "items": []
  },
  "metrics": {
    "audio.bytes_changed": 0
  }
}
```

### Vector PC-B: one continuous sample update

```json
{
  "operation": "sample_update",
  "before_coordinate": {
    "stream_index": 0,
    "channel_index": 0,
    "channel_label": null,
    "sample_start": 10,
    "sample_count": 3,
    "time_start_seconds": null,
    "time_duration_seconds": null
  },
  "after_coordinate": {
    "stream_index": 0,
    "channel_index": 0,
    "channel_label": null,
    "sample_start": 10,
    "sample_count": 3,
    "time_start_seconds": null,
    "time_duration_seconds": null
  },
  "metrics": {
    "audio.samples_changed": 3,
    "change_count": 1
  }
}
```

### Vector PC-C: byte insert with zero WAV assumptions

```json
{
  "relation": "encoded_bytes",
  "operation": "encoded_byte_insert",
  "before_coordinate": null,
  "after_coordinate": {
    "stream_index": null,
    "channel_index": null,
    "channel_label": null,
    "sample_start": null,
    "sample_count": null,
    "time_start_seconds": null,
    "time_duration_seconds": null,
    "byte_start": 4,
    "byte_count": 2
  },
  "metrics": {
    "audio.bytes_changed": 2,
    "change_count": 1
  }
}
```

### Vector PC-D: resource limit detail

```json
{
  "stage": "comparing",
  "code": "resource_limit_exceeded",
  "message": "audio comparison exceeded max_decoded_bytes",
  "details": {
    "limit_name": "max_decoded_bytes",
    "limit_value": 0,
    "limit_unit": "decoded PCM bytes",
    "accounting_scope": "dual_input_sum",
    "measured_value": 2,
    "input_side": "both"
  }
}
```

## Acceptance conditions

This amendment can be accepted only when reviewers confirm all of the
following:

1. RFC 0010 Option A/SP1-SP6 and the actual P4-C1, P5-A1/schema-v4, and
   P6-C0/schema-v5 predecessor gates remain required.
2. Schema-v6 remains exclusively audio.
3. Decoded-sample comparison remains stdlib WAV/PCM only.
4. `encoded_bytes` bypasses WAV probing and decoding and accepts arbitrary
   byte streams.
5. Equal result carriers and complete decoded-audio fact carriers are closed
   and renderer-independent.
6. Continuous grouping and metric counts are deterministic and independent of
   renderer truncation.
7. Resource limit names, ranges, units, and accounting scopes are stable.
8. Problem prose is only in `problem.message`; structured data is only in
   `problem.details`.
9. English and Chinese texts are aligned.
10. No P7-A1 implementation, video, UI, FFmpeg, dependency, or PR work starts
    from this Proposed amendment.
