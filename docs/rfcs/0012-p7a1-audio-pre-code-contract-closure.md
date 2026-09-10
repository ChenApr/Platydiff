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
| P7A-PC3 | Freeze scope and unit clarifications for every accepted `AudioResourceLimits` field while preserving accepted names, defaults, and zero-budget semantics. | Replace the accepted resource object with a smaller backend-specific limit set. |
| P7A-PC4 | Define `encoded_bytes` as a raw byte relation that bypasses WAV probing and decoding, accepts arbitrary byte streams, and allows limit value `0` to mean no bytes may be compared. | Require WAV validity before encoded-byte comparison. |
| P7A-PC5 | Freeze the timestamp, delay, and padding chunk recognition list and require every user-facing explanation to appear only in `problem.message`; structured values appear only in `problem.details`. | Duplicate explanatory prose inside detail values. |
| P7A-PC6 | Preserve schema-v6 as exclusively audio and keep video roadmap-only. | Let this closure allocate video schema membership. |

## Equal result carrier

For P7-A1 audio, an equal result is still a normal schema-v6 `DiffResult`.
RFC 0012 does not replace the accepted schema-v6 `DiffResult` or
`MediaViewEvaluation` hierarchy. The public carrier for audio-specific equality
is the accepted RFC 0009/RFC 0011 envelope:

| Field | Required value |
| --- | --- |
| `schema_version` | `6` |
| `relation` | `"equal"` |
| `verdict` | `"pass"` |
| `fidelity` | `"full"` |
| `completeness` | `"complete"` unless producer-side serialization truncation has occurred after full counts are known |
| `media_evaluations` | ordered list of selected audio relation evaluations |
| `changes.change_count` | `0` |
| `changes.items` | empty list |
| `metrics` | includes comparison totals for every selected relation |
| `provenance` | includes selected comparator, backend, profile, resource limits, normalization, alignment, and input digests |

For equal decoded-sample comparison, the first `media_evaluations` entry has:

| Field | Required value |
| --- | --- |
| `kind` | `"media_view_evaluation"` |
| `media_kind` | `"audio"` |
| `selector` | `"decoded_samples"` |
| `relation` | `"equal"` |
| `verdict` | `"pass"` |
| `fidelity` | `"full"` |
| `completeness` | `"complete"` |
| `metric_names` | sorted tuple of metric names used by the relation |
| `policy_rule_ids` | sorted tuple of policy rule IDs used by the relation |
| `transformation_ids` | sorted tuple of transformation IDs used by the relation |
| `warning_codes` | empty tuple unless a visible warning was recorded |
| `change_count` | `0` |
| `failure_stage` | `null` |
| `failure_code` | `null` |

Backend, profile, and `stream.index` are recorded in provenance and selected
spec fields, not as replacement `MediaViewEvaluation` fields.

## Result-level audio facts carrier

RFC 0012 proposes one new schema-v6 audio fact carrier inside the existing
completed-outcome hierarchy. It does not replace `CompletedOutcome`,
`DiffResult`, `MediaViewEvaluation`, or `AudioFact`.

The completed outcome hierarchy remains:

```text
CompletedOutcomeV6.kind
CompletedOutcomeV6.result
DiffResult.relation
DiffResult.verdict
DiffResult.fidelity
DiffResult.summary
DiffResult.changes
DiffResult.metrics
DiffResult.evaluations
DiffResult.artifacts
DiffResult.provenance
DiffResult.media_evaluations
DiffResult.audio_facts
```

`DiffResult.audio_facts` is a tuple of accepted `AudioFact` records sorted by:

```text
stream_index, coordinate, name, unit, value
```

It is present only for schema-v6 audio results. Predecessor upgraders set it to
an empty tuple. It carries relation-significant audio facts at result level so
equal decoded-sample results can expose complete facts without inventing
metadata update changes. It must not contain renderer-only labels, backend
stderr, host paths, source filenames, or explanatory prose.

Complete decoded-audio facts preserve the accepted `AudioFact` closed object.
RFC 0012 does not add `source`, arrays, or nested objects to `AudioFact`.
Key order remains:

```text
name, value, unit, stream_index, coordinate
```

Equal decoded-sample results must carry, at minimum, accepted `AudioFact`
records for:

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

Absent optional timing facts use value `null` and unit `null` when absence is
mandated by P7-A1. Recognized but unsupported metadata uses value `"unknown"`
and the unit documented by the fact. Fact provenance remains in result
provenance, not inside `AudioFact`.

## Change grouping and counts

`ChangeSet.change_count` is the number of emitted `AudioChange` items after
continuous grouping and before producer-side serialization truncation. A
renderer must never shorten `changes.items`, mutate `change_count`, or mutate
the overall relation/verdict/fidelity/completeness. Truncation is a producer
serialization policy only and is reflected by accepted completeness/truncation
metadata after full counts are known.

Count binding is exact:

| Field | Binding |
| --- | --- |
| `DiffSummary.change_count` | equals `ChangeSet.total_count` when non-null |
| `ChangeSet.total_count` | total grouped `AudioChange` count across all selected audio relations |
| `ChangeSet.returned_count` | length of `ChangeSet.items` after producer-side serialization limits |
| `ChangeSet.omitted_count` | `total_count - returned_count` for `complete` or `truncated` change sets |
| `MediaViewEvaluation.change_count` | total grouped `AudioChange` count for that evaluation's `selector` |

For P7-A1 completed results, `partial` change sets remain unauthorized.
Therefore `summary.change_count`, `changes.total_count`, and
`changes.omitted_count` are non-null. For `complete`, `total_count` equals
`returned_count` and `omitted_count` is `0`. For `truncated`, total and omitted
counts remain known and the overall relation/verdict/fidelity are unchanged.
The sum of `MediaViewEvaluation.change_count` across selected audio evaluations
equals `ChangeSet.total_count`.

For `decoded_samples`, sample changes are grouped into maximal continuous runs
with the same:

```text
relation, operation, stream_index, channel, before_step, after_step
```

`before_step` and `after_step` are each `1` for replacement runs, `1` and `0`
for deletions, or `0` and `1` for insertions. P7-A1 preserves the RFC 0009
length-difference semantics: overlapping sample positions with unequal decoded
values are grouped as `sample_update`; trailing before-only decoded samples are
grouped as `sample_delete`; trailing after-only decoded samples are grouped as
`sample_insert`. Insert/delete runs require only the present-side coordinate as
accepted by RFC 0009.

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
| `audio.samples_changed` | Sum of changed decoded sample positions across all channels after grouping; an update counts overlapping changed positions, an insert counts after-side sample positions, and a delete counts before-side sample positions. |
| `audio.bytes_changed` | Sum of changed encoded byte positions; an update counts one byte position, a delete counts one before byte, and an insert counts one after byte. |
| `audio.samples_compared` | Number of decoded sample positions compared, multiplied by selected channel count. |
| `audio.channels_compared` | Number of selected channels that reached comparison. |
| `change_count` | Number of grouped `AudioChange` items. |

## Resource limits

All resource limits are non-negative integers. Unknown limit names are invalid.
Default values are inserted by the schema-v6 reader before comparison. RFC 0012
does not rename, remove, or narrow any accepted `AudioResourceLimits` field; it
only clarifies accounting scope and units for the accepted object.

| Limit | Unit | Accounting scope | P7-A1 default |
| --- | --- | --- | --- |
| `max_input_bytes` | source bytes per input | single input | `268435456` |
| `max_streams` | stream count per input | single input | `32` |
| `max_duration_seconds` | decoded duration seconds per input | single input | `3600` |
| `max_sample_rate_hz` | samples per second per stream | single input | `384000` |
| `max_channels` | channel count per stream | single input | `64` |
| `max_decoded_samples_per_channel` | decoded samples per channel | single input | `50000000` |
| `max_total_decoded_bytes` | decoded PCM bytes across both inputs | dual-input sum | `536870912` |
| `max_resident_buffer_bytes` | simultaneous live decoded/sample buffer bytes | comparison peak | `134217728` |
| `max_packets` | packet or chunk records read across both inputs | dual-input sum | `1000000` |
| `max_metadata_entries` | metadata entries per input | single input | `10000` |
| `max_metadata_value_bytes` | bytes per metadata value | single input | `1048576` |
| `max_spectral_cells` | spectral cells per selected relation | relation scope | `20000000` |
| `max_backend_seconds` | wall-clock backend seconds | comparison scope | `30` |
| `max_stdout_stderr_bytes` | captured backend output bytes | comparison scope | `4194304` |
| `max_temp_bytes` | temporary file bytes | comparison scope | `536870912` |
| `max_materialized_bytes` | host-owned snapshot and materialized bytes | comparison scope | `536870912` |
| `max_compare_work` | abstract comparison work units | comparison scope | `10000000` |
| `max_change_items` | producer-emitted change items | relation scope | `10000` |
| `max_change_payload_bytes` | producer-emitted change payload bytes | relation scope | `4194304` |

Deterministic counter rules:

| Limit | Increment | Check stage | Zero behavior |
| --- | --- | --- | --- |
| `max_input_bytes` | immutable source bytes acquired for one input | `sourcing` | only zero-byte sources are allowed |
| `max_streams` | discovered streams in one input | `resolving` | any discovered stream fails |
| `max_duration_seconds` | exact decoded duration rounded up to whole seconds | `resolving` or `decoding` | only zero-duration decoded streams are allowed |
| `max_sample_rate_hz` | declared or decoded sample rate | `resolving` or `decoding` | any positive sample rate fails |
| `max_channels` | decoded channel count for one stream | `resolving` or `decoding` | any channel fails |
| `max_decoded_samples_per_channel` | decoded sample count for each channel | `decoding` | only zero decoded samples per channel are allowed |
| `max_total_decoded_bytes` | decoded PCM bytes materialized across both inputs | `decoding` | decoded-sample relations fail before payload decode unless no decoded bytes are needed |
| `max_resident_buffer_bytes` | peak live decoded/sample comparison buffer bytes | `normalizing`, `aligning`, or `comparing` | fail before allocating comparison buffers |
| `max_packets` | packet or chunk records read across both inputs | `resolving` or `decoding` | fail before reading any packet or chunk record |
| `max_metadata_entries` | metadata entries retained per input | `resolving` or `decoding` | any retained metadata entry fails |
| `max_metadata_value_bytes` | bytes in one metadata value | `resolving` or `decoding` | any non-empty metadata value fails |
| `max_spectral_cells` | generated spectral cells | `normalizing` or `comparing` | spectral relations fail before producing cells |
| `max_backend_seconds` | monotonic elapsed backend seconds | backend execution stage | no backend runtime budget; fail before backend start if a backend would be needed |
| `max_stdout_stderr_bytes` | captured backend stdout/stderr bytes | backend execution stage | any captured byte fails |
| `max_temp_bytes` | temporary bytes created by the comparison | any stage that creates temp data | any temp byte fails |
| `max_materialized_bytes` | host-owned snapshot and materialized bytes | `sourcing` or materialization stage | any materialized byte fails |
| `max_compare_work` | deterministic relation work units | `comparing` | only zero-work comparisons may complete |
| `max_change_items` | grouped changes selected for serialization | `aggregating` | compute relation and total counts, then emit a truncated empty change list |
| `max_change_payload_bytes` | serialized change payload bytes | `aggregating` | compute relation and total counts, then omit payload-bearing changes |

`max_compare_work=0` permits only comparisons that can complete with zero
relation work: identical empty encoded-byte inputs or metadata-only failures
before relation work begins. `max_packets=0` forbids reading any packet or WAV
chunk record. `max_total_decoded_bytes=0` forbids decoding PCM payload bytes
for decoded-sample relations. `max_resident_buffer_bytes=0` requires the
producer to fail before allocating decoded/sample comparison buffers.

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

Encoded-byte alignment is byte-index alignment over immutable source snapshots.
The producer compares the longest common prefix, then emits at most one middle
run, then compares the longest common suffix that does not overlap the prefix.
Tie-breaks are deterministic:

1. Maximize common prefix length.
2. Maximize common suffix length.
3. Prefer one `encoded_byte_update` run when before and after middle lengths
   are equal.
4. Otherwise emit one `encoded_byte_delete` and/or one `encoded_byte_insert` in
   source order.

Adjacent encoded-byte operations of the same operation and step pattern are
grouped into one maximal run. `audio.bytes_changed` counts update positions,
deleted before bytes, and inserted after bytes as defined above; grouping must
not change the count.

For `encoded_bytes` with limit value `0`, stage and counters are fixed:

| Limit | Stage when proven | Counter behavior |
| --- | --- | --- |
| `max_input_bytes=0` | `sourcing` | non-empty input fails before relation work |
| `max_materialized_bytes=0` | `sourcing` | non-empty materialization fails before relation work |
| `max_compare_work=0` | `comparing` | empty-vs-empty may complete; any byte comparison work fails |
| `max_change_items=0` | `aggregating` | relation and total counts are computed; `returned_count=0`, `omitted_count=total_count` |
| `max_change_payload_bytes=0` | `aggregating` | payload-bearing changes are omitted after relation and total counts are known |

## Timestamp, delay, and padding recognition

P7-A1 recognizes only these timing, delay, and padding facts, serialized in
this order after the core format facts:

| Fact name | Value type | Unit | Absence value | Unknown value | Recognized source |
| --- | --- | --- | --- | --- | --- |
| `timestamp_origin` | string or null | `null` | `null` | `"unknown"` | no source, `bext.time_reference`, `smpl.sample_period` |
| `timestamp_value` | integer, finite number, string, or null | `samples`, `seconds`, or `null` | `null` | `"unknown"` | `bext.time_reference` sample count or `smpl.sample_period` exact rational seconds |
| `encoder_delay_samples` | integer, string, or null | `samples` or `null` | `null` | `"unknown"` | recognized delay metadata |
| `encoder_padding_samples` | integer, string, or null | `samples` or `null` | `null` | `"unknown"` | recognized padding metadata |

Status semantics are:

- no recognized source records the absence value;
- recognized and supported metadata records the typed value and unit;
- recognized but unsupported metadata records `"unknown"` with the documented
  unit when known, otherwise unit `null`;
- malformed recognized metadata fails at the stage that proves malformation and
  does not become an `"unknown"` fact.

All other chunks are metadata facts only when RFC 0011 already allows them as
bounded chunk facts. They must not silently affect sample coordinates,
duration, alignment, or equality.

## Problem message and details

`problem.message` is the only location for user-facing explanatory prose.
`problem.details` is the only location for structured values. Detail values
must be strings, integers, finite JSON numbers, booleans, or `null`; arrays and
objects remain invalid unless a later schema revision explicitly permits them.

RFC 0012 keeps the RFC 0011 problem-details allowlist and adds only the
resource accounting keys needed above. Allowed detail keys for this amendment
are:

```text
stage
code
relation
backend
profile
input_side
byte_offset
chunk_id
field
value_kind
limit_name
limit_value
limit_unit
accounting_scope
measured_value
operation
fact_name
```

Detail values must not contain backend stderr, exception class names, host
paths, source filenames, safe labels, explanatory sentences, or arbitrary
dictionaries.

## Canonical vectors

These vectors are normative examples for acceptance tests. They are expressed
as schema-v6 envelopes or complete accepted-shape fragments after default
insertion and before any producer-side serialization truncation.

### Vector PC-A: equal empty encoded bytes

```json
{
  "kind": "completed",
  "result": {
    "schema_version": 6,
    "relation": "equal",
    "verdict": "pass",
    "fidelity": "full",
    "summary": {
      "change_count": 0,
      "counts": []
    },
    "changes": {
      "completeness": "complete",
      "items": [],
      "total_count": 0,
      "returned_count": 0,
      "omitted_count": 0,
      "selection": "all",
      "limit": null,
      "limit_reason": null
    },
    "metrics": [
      {
        "name": "audio.bytes_changed",
        "value": {
          "kind": "finite",
          "value": 0
        },
        "unit": "bytes",
        "direction": "lower_is_better",
        "aggregation": "count"
      }
    ],
    "evaluations": [],
    "artifacts": [],
    "provenance": {
      "comparator_id": "audio.comparator.stdlib_wave_pcm.v1"
    },
    "media_evaluations": [
      {
        "kind": "media_view_evaluation",
        "media_kind": "audio",
        "selector": "encoded_bytes",
        "relation": "equal",
        "verdict": "pass",
        "fidelity": "full",
        "completeness": "complete",
        "metric_names": [
          "audio.bytes_changed"
        ],
        "policy_rule_ids": [
          "audio.policy.encoded_bytes.v1"
        ],
        "transformation_ids": [],
        "warning_codes": [],
        "change_count": 0,
        "failure_stage": null,
        "failure_code": null
      }
    ],
    "audio_facts": []
  }
}
```

### Vector PC-B: one continuous sample update

```json
{
  "kind": "completed",
  "result": {
    "schema_version": 6,
    "relation": "different",
    "verdict": "fail",
    "fidelity": "full",
    "summary": {
      "change_count": 1,
      "counts": []
    },
    "changes": {
      "completeness": "complete",
      "items": [
        {
          "kind": "audio_change",
          "relation": "decoded_samples",
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
          "channel": 0,
          "before_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000001",
          "after_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000002",
          "before_fact": null,
          "after_fact": null
        }
      ],
      "total_count": 1,
      "returned_count": 1,
      "omitted_count": 0,
      "selection": "all",
      "limit": null,
      "limit_reason": null
    },
    "metrics": [
      {
        "name": "audio.samples_changed",
        "value": {
          "kind": "finite",
          "value": 3
        },
        "unit": "samples",
        "direction": "lower_is_better",
        "aggregation": "count"
      }
    ],
    "evaluations": [],
    "artifacts": [],
    "provenance": {
      "comparator_id": "audio.comparator.stdlib_wave_pcm.v1"
    },
    "media_evaluations": [
      {
        "kind": "media_view_evaluation",
        "media_kind": "audio",
        "selector": "decoded_samples",
        "relation": "different",
        "verdict": "fail",
        "fidelity": "full",
        "completeness": "complete",
        "metric_names": [
          "audio.samples_changed"
        ],
        "policy_rule_ids": [
          "audio.policy.exact_decoded_samples.v1"
        ],
        "transformation_ids": [],
        "warning_codes": [],
        "change_count": 1,
        "failure_stage": null,
        "failure_code": null
      }
    ],
    "audio_facts": []
  }
}
```

### Vector PC-C: byte insert with zero WAV assumptions

```json
{
  "kind": "completed",
  "result": {
    "schema_version": 6,
    "relation": "different",
    "verdict": "fail",
    "fidelity": "full",
    "summary": {
      "change_count": 1,
      "counts": []
    },
    "changes": {
      "completeness": "complete",
      "items": [
        {
          "kind": "audio_change",
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
          "channel": null,
          "before_digest": null,
          "after_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000003",
          "before_fact": null,
          "after_fact": null
        }
      ],
      "total_count": 1,
      "returned_count": 1,
      "omitted_count": 0,
      "selection": "all",
      "limit": null,
      "limit_reason": null
    },
    "metrics": [
      {
        "name": "audio.bytes_changed",
        "value": {
          "kind": "finite",
          "value": 2
        },
        "unit": "bytes",
        "direction": "lower_is_better",
        "aggregation": "count"
      }
    ],
    "evaluations": [],
    "artifacts": [],
    "provenance": {
      "comparator_id": "audio.comparator.stdlib_wave_pcm.v1"
    },
    "media_evaluations": [
      {
        "kind": "media_view_evaluation",
        "media_kind": "audio",
        "selector": "encoded_bytes",
        "relation": "different",
        "verdict": "fail",
        "fidelity": "full",
        "completeness": "complete",
        "metric_names": [
          "audio.bytes_changed"
        ],
        "policy_rule_ids": [
          "audio.policy.encoded_bytes.v1"
        ],
        "transformation_ids": [],
        "warning_codes": [],
        "change_count": 1,
        "failure_stage": null,
        "failure_code": null
      }
    ],
    "audio_facts": []
  }
}
```

### Vector PC-D: resource limit detail

```json
{
  "stage": "comparing",
  "code": "compare_resource_limit",
  "message": "audio comparison exceeded max_total_decoded_bytes",
  "details": {
    "limit_name": "max_total_decoded_bytes",
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
   and use accepted schema-v6, `MediaViewEvaluation`, and `AudioFact` shapes.
6. Continuous grouping and metric counts are deterministic and independent of
   producer-side serialization truncation.
7. The accepted `AudioResourceLimits` object remains complete; only scope and
   unit clarifications are added.
8. Problem prose is only in `problem.message`; structured data is only in
   `problem.details`.
9. English and Chinese texts are aligned.
10. No P7-A1 implementation, video, UI, FFmpeg, dependency, or PR work starts
    from this Proposed amendment.
