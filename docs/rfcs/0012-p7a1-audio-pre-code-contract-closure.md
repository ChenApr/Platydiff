# RFC 0012: P7-A1 Audio Pre-Code Contract Closure

[Chinese documentation](0012-p7a1-audio-pre-code-contract-closure_zh.md)

- Status: Accepted
- Date: 2026-09-10
- Accepted: 2026-09-10
- Approved decisions: P7A-PC1 through P7A-PC6
- Amends: [RFC 0009](0009-audio-and-video-comparison.md) and
  [RFC 0011](0011-rfc-0009-audio-preflight-amendment.md)
- Owners: Platydiff maintainers
- Implementation owner: none; this accepted amendment does not start code

## Summary and authorization boundary

This accepted amendment closes remaining P7-A1 pre-code audio contract gaps. It
does not authorize implementation, video, UI, FFmpeg, new dependencies,
automatic media detection, SDK v2, or any schema successor outside audio
schema-v6.

This amendment preserves RFC 0009 and RFC 0011 direction: P7-A1 is audio-only,
uses the stdlib WAV/PCM profile for decoded-sample relations, and remains gated
by accepted RFC 0010 Option A/SP1-SP6 plus actual P4-C1, P5-A1/schema-v4, and
P6-C0/schema-v5 merges. P7-A1 dispatch also requires RFC 0011 and RFC 0012 to
have merged and still needs an independent human dispatch from updated `main`.

## Approved decisions

These IDs are accepted closure decisions. They freeze pre-code P7-A1 audio
contracts but do not authorize implementation.

| ID | Approved decision | Alternative not selected |
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
| `completeness` | `"complete"` unless producer-side result-detail truncation has occurred after full counts are known |
| `media_evaluations` | ordered list of selected audio relation evaluations |
| `summary.change_count` | `0` |
| `changes.total_count` | `0` |
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
| `algorithm_id` | stable algorithm ID used by the relation |
| `warning_codes` | empty tuple unless a visible warning was recorded |
| `change_count` | `0` |
| `failure_stage` | `null` |
| `failure_code` | `null` |

Backend, profile, and `stream.index` are recorded in provenance and selected
spec fields, not as replacement `MediaViewEvaluation` fields. RFC 0012
proposes `MediaViewEvaluation.algorithm_id` for schema-v6 audio so aggregate
results can bind each selected relation to its deterministic algorithm without
overloading top-level comparison provenance.

Schema-v6 closes the result-level `completeness` carrier for audio by adding
`DiffResult.completeness` with the same closed values and semantics as
`MediaViewEvaluation.completeness`: `"complete"` or `"truncated"` only.
Completed audio results never use `partial`. Result completeness is
`"truncated"` only when relation, verdict, fidelity, all metrics, and total
change counts are known and producer-owned result detail omitted whole change
items after comparison. It never represents a failed comparison.

Stable IDs accepted by RFC 0011 remain:

| Purpose | Stable ID |
| --- | --- |
| Built-in comparator/capability | `builtin.audio` |
| Decoded-sample algorithm | `audio.decoded_samples.exact.v1` |
| Encoded-byte algorithm | `audio.encoded_bytes.exact.v1` |
| WAV/PCM decode transformation | `audio.decode.stdlib_wave_pcm.v1` |
| Resource profile | `audio.resource.p7_a1.v1` |
| Resource defaults | `audio.resource.p7_a1.defaults.v1` |

RFC 0012 additionally proposes this schema-v6 audio registry entry:

| Purpose | Stable ID |
| --- | --- |
| Multi-relation aggregate algorithm | `audio.aggregate.selected_relations.v1` |

Schema-v6 audio readers must reject unknown comparator, algorithm,
transformation, resource profile, and resource default IDs rather than aliasing
or accepting them. Predecessor v1-v5 upgraders do not synthesize the aggregate
algorithm ID; they only add the defaulted schema-v6 media carriers described
below.

RFC 0012 supersedes any earlier Proposed vector text that used
`audio.comparator.stdlib_wave_pcm.v1`,
`audio.decoded_samples.exact_grouped.v1`, or
`audio.encoded_bytes.prefix_suffix.v1`. Readers must treat those strings as
pre-acceptance drafts, not aliases.

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

`DiffResult.audio_facts` is present on every schema-v6 completed result. It is
a tuple of accepted `AudioFact` records sorted by:

```text
registry_order, stream_index, coordinate, unit, value_type_rank, value
```

Audio results use it to carry relation-significant audio facts at result level
so equal decoded-sample results can expose complete facts without inventing
metadata update changes. Non-audio predecessor upgrades set it to an empty
tuple. It must not contain renderer-only labels, backend stderr, host paths,
source filenames, or explanatory prose.

Complete decoded-audio facts preserve the accepted `AudioFact` closed object.
RFC 0012 does not add `source`, arrays, or nested objects to `AudioFact`.
Key order remains:

```text
name, value, unit, stream_index, coordinate
```

The authoritative P7-A1 fact registry is the RFC 0011 first-gate fact order
below. It supersedes the older Proposed names
`container.endianness`, `format.tag`, `format.extensible`, `signedness`,
`endianness`, `container_bits`, `valid_bits`, `block_align`, `byte_rate`,
`sample_count`, `duration_seconds_exact`, `duration_seconds_binary64`,
`timestamp_origin`, `timestamp_value`, `encoder_delay_samples`, and
`encoder_padding_samples`.

| Order | Name | Value type | Unit | Required for complete decoded result | Nullable | Unknown value | Coordinate | Uniqueness |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `container.form` | string | `tag` | yes | no | no | `null` | once per selected stream |
| 2 | `codec.profile` | string | `name` | yes | no | no | `null` | once per selected stream |
| 3 | `stream.index` | integer | `index` | yes | no | no | `null` | once per selected stream |
| 4 | `sample_rate` | integer | `Hz` | yes | no | no | `null` | once per selected stream |
| 5 | `channel_count` | integer | `count` | yes | no | no | `null` | once per selected stream |
| 6 | `channel_layout` | string | `name` | yes | no | `"unknown"` | `null` | once per selected stream |
| 7 | `channel_mask` | integer or null | `bitmask` | yes | yes | no | `null` | once per selected stream |
| 8 | `sample_format` | string | `name` | yes | no | no | `null` | once per selected stream |
| 9 | `container_bits_per_sample` | integer | `bits` | yes | no | no | `null` | once per selected stream |
| 10 | `valid_bits_per_sample` | integer | `bits` | yes | no | no | `null` | once per selected stream |
| 11 | `sample_count_per_channel` | integer | `samples` | yes | no | no | `null` | once per selected stream |
| 12 | `duration_seconds` | finite number | `s` | yes | no | no | `null` | once per selected stream |
| 13 | `duration_numerator` | integer | `samples` | yes | no | no | `null` | once per selected stream |
| 14 | `duration_denominator` | integer | `Hz` | yes | no | no | `null` | once per selected stream |
| 15 | `timestamp_status` | string | `name` | yes | no | `"unknown"` | `null` | once per selected stream |
| 16 | `encoder_delay_status` | string | `name` | yes | no | `"unknown"` | `null` | once per selected stream |
| 17 | `encoder_padding_status` | string | `name` | yes | no | `"unknown"` | `null` | once per selected stream |

Complete decoded-sample equality must carry all 17 records for the selected
stream. `AudioFact` remains the closed accepted shape `name`, `value`, `unit`,
`stream_index`, and `coordinate`; no source field, arrays, or nested values are
legal in P7-A1 facts. Facts are unique by `(stream_index, coordinate, name)`.
Ordering is first by the registry order above, then `stream_index`, coordinate,
unit, value type rank, and value. Value ordering is total across accepted value
types: `null`, booleans (`false` before `true`), integers, finite numbers,
strings other than `"unknown"`, and finally the string `"unknown"`. Integers
and finite numbers are compared by exact numeric value within their type;
strings use Unicode scalar lexical order. This order is for deterministic
serialization only and never changes relation semantics.

RFC 0012 preserves RFC 0011 duration recording: `duration_seconds` remains the
accepted duration fact, and `duration_numerator` plus `duration_denominator`
are required adjacent companion facts in the same total order.
`duration_seconds` is the IEEE-754 binary64 nearest-even value of
`duration_numerator / duration_denominator`, serialized as the shortest decimal
that round-trips to the same binary64 value.

Predecessor v1-v5 upgraders must add `DiffResult.completeness`,
`DiffResult.media_evaluations`, and `DiffResult.audio_facts`. For non-audio or
pre-media results, `completeness` is `"complete"`, `media_evaluations` is an
empty tuple, and `audio_facts` is an empty tuple. Upgraders must not infer
audio facts from earlier metadata.

## Change grouping and counts

`DiffSummary.change_count` is the number of grouped `AudioChange` items after
continuous grouping and before producer-side result-detail truncation. A
renderer must never shorten `changes.items`, mutate summary or change-set
counts, or mutate the overall relation/verdict/fidelity/completeness.
Truncation is a producer result-detail policy only and is reflected by accepted
completeness/truncation metadata after full counts are known.

Count binding is exact:

| Field | Binding |
| --- | --- |
| `DiffSummary.change_count` | equals `ChangeSet.total_count` when non-null |
| `ChangeSet.total_count` | total grouped `AudioChange` count across all selected audio relations |
| `ChangeSet.returned_count` | length of `ChangeSet.items` after producer-side result-detail limits |
| `ChangeSet.omitted_count` | `total_count - returned_count` for `complete` or `truncated` change sets |
| `MediaViewEvaluation.change_count` | total grouped `AudioChange` count for that evaluation's `selector` |

For P7-A1 completed results, `partial` change sets remain unauthorized.
Therefore `summary.change_count`, `changes.total_count`, and
`changes.omitted_count` are non-null. For `complete`, `total_count` equals
`returned_count` and `omitted_count` is `0`. For `truncated`, total and omitted
counts remain known and the overall relation/verdict/fidelity are unchanged.
The sum of `MediaViewEvaluation.change_count` across selected audio evaluations
equals `ChangeSet.total_count`.

Detail limits are result-detail limits, not comparison-failure limits.
Exceeding `max_change_items` or `max_change_payload_bytes` after relation and
total counts are known produces a completed result with
`changes.completeness="truncated"`, `result.completeness="truncated"`,
`selection="source_order_prefix"`, `limit` equal to the configured limit,
`limit_reason` equal to `"change_items"` or `"change_payload_bytes"`, and a
`change_details_truncated` warning diagnostic at `aggregating`. The retained
items are the whole-item source-order prefix whose canonical encoded payload
fits the relevant limit. A `0` detail limit with `total_count=0` remains
`complete` with `selection="all"` and no warning. A `0` detail limit with
`total_count>0` is a completed/truncated result with `returned_count=0` and
`omitted_count=total_count`; it must not become
`failed/compare_resource_limit`.

Canonical change payload bytes are computed from UTF-8 JSON with sorted object
keys, no insignificant whitespace, lowercase hex digests, and the exact
wire-visible `AudioChange` object after null fields have been inserted. For a
retained prefix of `n` complete changes with encoded byte lengths `b_i`, the
retained payload byte count is `sum(b_i) + max(n - 1, 0)`: each retained item
plus one comma byte between adjacent items; the outer `[` and `]` bytes are not
counted. For `n=0`, retained payload byte count is `0`. Payload accounting
never cuts inside one change item, and reported `ResourceUsage.used` is
retained usage that must be less than or equal to the configured limit.

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

`AudioChange` output ordering is frozen. Producers sort first by canonical
relation order, then by encoded operation order:
`encoded_byte_update`, `encoded_byte_delete`, `encoded_byte_insert`,
`sample_update`, `sample_delete`, `sample_insert`, `format_update`,
`channel_update`, `timing_update`, and `metadata_update`. For
`encoded_bytes`, same-offset deletions sort before same-offset insertions so a
replacement with unequal middle lengths is stable. Remaining tie-breaks are
before coordinate, after coordinate, channel with `null` before concrete
channels, before digest, after digest, before fact, and after fact. Adjacent
compatible operations are grouped only after this order is established.

Encoded-byte work accounting is deterministic:

| Operation/path | Work increment | Pre-check checkpoint |
| --- | --- | --- |
| Prefix comparison | one work unit per byte pair before reading the pair | before comparing the next prefix byte pair |
| Suffix comparison | one work unit per byte pair before reading the pair | before comparing the next non-overlapping suffix byte pair |
| `encoded_byte_update` grouping | one work unit per middle byte pair | before extending the update run |
| `encoded_byte_delete` grouping | one work unit per before-only byte | before extending the delete run |
| `encoded_byte_insert` grouping | one work unit per after-only byte | before extending the insert run |

With `max_compare_work=0`, only empty-vs-empty `encoded_bytes` may complete.
The longest-common-prefix step runs first, then the non-overlapping suffix
step, then the middle is classified. Equal middle lengths form one
`encoded_byte_update` run. Unequal non-empty middles form delete-before-insert
runs at the same source offset. A middle present on only one side forms exactly
one insert or delete run. These rules cover empty inputs, shared prefix/suffix,
length inequality, and unequal-middle replacement without implementation
choice.

Metric counting rules:

| Metric | Count rule |
| --- | --- |
| `audio.samples_changed` | Sum of changed decoded sample positions across all channels after grouping; an update counts overlapping changed positions, an insert counts after-side sample positions, and a delete counts before-side sample positions. |
| `audio.bytes_changed` | Sum of actually unequal encoded byte positions; an update run counts positions whose before and after byte values differ, a delete counts one before byte, and an insert counts one after byte. This may be smaller than an `AudioChange` coordinate `byte_count` because canonical middle ranges preserve prefix/suffix determinism rather than splitting around equal bytes inside the middle. |
| `audio.samples_compared` | Number of decoded sample positions compared, multiplied by selected channel count. |
| `audio.channels_compared` | Number of selected channels that reached comparison. |
| `change_count` | Number of grouped `AudioChange` items. |

## Resource limits

All resource limits are non-negative integers. Unknown limit names are invalid.
Default values are inserted by the schema-v6 reader before comparison. RFC 0012
does not rename, remove, or narrow any accepted `AudioResourceLimits` field; it
only clarifies accounting scope and units for the accepted object. The
`accounting_scope` detail value is a single closed enum:
`"single_input"`, `"dual_input_sum"`, `"relation"`, `"comparison"`,
`"comparison_peak"`, and `"backend_execution"`.

RFC 0009 currently defines 19 accepted `AudioResourceLimits` fields, including
the reserved `max_spectral_cells` field. RFC 0012 preserves all 19 accepted
fields. Reviews or notes that refer to an 18-field object are superseded by the
accepted RFC 0009/RFC 0011 model unless a later RFC removes a field.

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
| `max_spectral_cells` | spectral cells per selected relation | relation | `20000000` |
| `max_backend_seconds` | wall-clock backend seconds | backend_execution | `30` |
| `max_stdout_stderr_bytes` | captured backend output bytes | backend_execution | `4194304` |
| `max_temp_bytes` | temporary file bytes | comparison | `536870912` |
| `max_materialized_bytes` | host-owned snapshot and materialized bytes | comparison | `536870912` |
| `max_compare_work` | abstract comparison work units | comparison | `10000000` |
| `max_change_items` | producer-emitted change items across completed result | comparison | `10000` |
| `max_change_payload_bytes` | producer-emitted change payload bytes across completed result | comparison | `4194304` |

Deterministic counter rules:

| Limit | Increment/checkpoint | Stage | Code | Zero behavior |
| --- | --- | --- | --- | --- |
| `max_input_bytes` | Count immutable source bytes acquired for one input after the bounded snapshot is known and before retaining it. | `sourcing` | `resource_limit_exceeded` | only zero-byte sources are allowed |
| `max_streams` | Count discovered streams in one input as soon as stream identity is proven. | `resolving` | `resource_limit_exceeded` | any discovered stream fails |
| `max_duration_seconds` | Count exact decoded duration rounded up to whole seconds when header duration is proven or payload duration is decoded. | `resolving` or `decoding` | `resource_limit_exceeded` | only zero-duration decoded streams are allowed |
| `max_sample_rate_hz` | Count declared or decoded sample rate before accepting the stream. | `resolving` or `decoding` | `resource_limit_exceeded` | any positive sample rate fails |
| `max_channels` | Count decoded channel count for one stream before channel buffers are allocated. | `resolving` or `decoding` | `resource_limit_exceeded` | any channel fails |
| `max_decoded_samples_per_channel` | Count decoded sample count for each channel before accepting decoded payload. | `decoding` | `resource_limit_exceeded` | only zero decoded samples per channel are allowed |
| `max_total_decoded_bytes` | Add decoded PCM bytes materialized across both inputs before each decode buffer commit. | `decoding` | `resource_limit_exceeded` | decoded-sample relations fail before payload decode unless no decoded bytes are needed |
| `max_resident_buffer_bytes` | Track peak live decoded/sample comparison buffer bytes before allocation. | `normalizing`, `aligning`, or `comparing` | `compare_resource_limit` | fail before allocating comparison buffers |
| `max_packets` | Add packet or chunk records read across both inputs before retaining each record. | `resolving` or `decoding` | `resource_limit_exceeded` | fail before reading any packet or chunk record |
| `max_metadata_entries` | Count retained metadata entries per input before insertion. | `resolving` or `decoding` | `resource_limit_exceeded` | any retained metadata entry fails |
| `max_metadata_value_bytes` | Count bytes in one metadata value before retaining the value. | `resolving` or `decoding` | `resource_limit_exceeded` | any non-empty metadata value fails |
| `max_spectral_cells` | Add generated spectral cells before materializing a spectral block. | `normalizing` or `comparing` | `compare_resource_limit` | spectral relations fail before producing cells |
| `max_backend_seconds` | Check monotonic elapsed backend nanoseconds before backend start and after each bounded backend wait; serialize seconds as integer ceiling of elapsed nanoseconds divided by 1,000,000,000. | `resolving`, `decoding`, or `comparing` | `resource_limit_exceeded` | no backend runtime budget; fail before backend start if a backend would be needed |
| `max_stdout_stderr_bytes` | Add captured backend stdout/stderr bytes before appending to capture buffers. | `resolving`, `decoding`, or `comparing` | `resource_limit_exceeded` | any captured byte fails |
| `max_temp_bytes` | Add temporary bytes before creating or extending temp data. | first concrete pipeline stage that creates temp data | `resource_limit_exceeded` | any temp byte fails |
| `max_materialized_bytes` | Add host-owned snapshot and materialized bytes before retaining materialized data. | first concrete pipeline stage that retains materialized data | `resource_limit_exceeded` | any materialized byte fails |
| `max_compare_work` | Add deterministic relation work units before each comparison work batch. Encoded bytes use the byte-work table below; decoded samples use one work unit per compared sample-channel position. | `comparing` | `compare_resource_limit` | only zero-work comparisons may complete |
| `max_change_items` | Count grouped changes across the whole completed result after all selected relation counts are known. | `aggregating` | completed/truncated result, not a problem code | compute relation and total counts, then emit a truncated empty change list when `total_count>0`; remain complete when `total_count=0` |
| `max_change_payload_bytes` | Count canonical result `changes.items` JSON array payload bytes before appending each complete change item. | `aggregating` | completed/truncated result, not a problem code | compute relation and total counts, then omit payload-bearing changes when `total_count>0`; remain complete when `total_count=0` |

When a row lists more than one possible stage, the canonical problem stage is
the first lifecycle stage in the actual execution at which the breach is
proven. `last_completed_stage` is the immediately preceding completed
pipeline stage. Temp-byte and materialization breaches use the concrete
pipeline stage that first attempts the temp write or materialized retention;
no non-enum stage names are serialized.

`max_compare_work=0` permits only comparisons that can complete with zero
relation work: identical empty encoded-byte inputs or metadata-only failures
before relation work begins. `max_packets=0` forbids reading any packet or WAV
chunk record. `max_total_decoded_bytes=0` forbids decoding PCM payload bytes
for decoded-sample relations. `max_resident_buffer_bytes=0` requires the
producer to fail before allocating decoded/sample comparison buffers.

Integer seconds use ceiling division over exact rational seconds:
`ceil(numerator / denominator)`, where the denominator is positive and the
rational has been reduced before serialization. A zero-duration stream counts
as `0`; any positive sub-second duration counts as `1`.

Problem details for limit failures use:

| Detail key | Value |
| --- | --- |
| `limit_name` | one of the names above |
| `limit_value` | configured integer |
| `limit_unit` | exact unit string from the table |
| `accounting_scope` | one value from the closed enum above |
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
grouped into one maximal run. `audio.bytes_changed` counts actually unequal
update positions, deleted before bytes, and inserted after bytes as defined
above; grouping must not change the count.

For `encoded_bytes` with limit value `0`, stage and counters are fixed:

| Limit | Stage when proven | Counter behavior |
| --- | --- | --- |
| `max_input_bytes=0` | `sourcing` | non-empty input fails before relation work |
| `max_materialized_bytes=0` | `sourcing` | non-empty materialization fails before relation work |
| `max_compare_work=0` | `comparing` | empty-vs-empty may complete; any byte comparison work fails |
| `max_change_items=0` | `aggregating` | relation and total counts are computed; `returned_count=0`, `omitted_count=total_count` |
| `max_change_payload_bytes=0` | `aggregating` | payload-bearing changes are omitted after relation and total counts are known |

## Timestamp, delay, and padding recognition

P7-A1 recognizes only these timing, delay, and padding status facts. They are
the registry facts above, repeated here with their recognized sources:

| Fact name | Value type | Unit | Absence value | Unknown value | Recognized source |
| --- | --- | --- | --- | --- | --- |
| `duration_seconds` | finite number | `s` | exact decoded duration | no | decoded sample count and sample rate |
| `timestamp_status` | string | `name` | `"absent"` | `"unknown"` | no source or `bext.time_reference` |
| `encoder_delay_status` | string | `name` | `"absent"` | `"unknown"` | recognized delay metadata |
| `encoder_padding_status` | string | `name` | `"absent"` | `"unknown"` | recognized padding metadata |

Status semantics are:

- no recognized source records the absence value;
- recognized and supported metadata records the typed value and unit;
- recognized but unsupported metadata records `"unknown"` with the documented
  unit when known, otherwise unit `null`;
- malformed recognized metadata fails at the stage that proves malformation and
  does not become an `"unknown"` fact.

`smpl.sample_period` is a sample-period scale fact only. It must not populate
`timestamp_origin`, shift sample coordinates, or establish a timestamp epoch.

Recognized timing chunks and fields are closed for P7-A1:

| Chunk/field | Type | Fact affected | Malformed behavior |
| --- | --- | --- | --- |
| no recognized timing chunk | absent | `timestamp_status="absent"` | not an error |
| `bext.time_reference` | unsigned 64-bit sample count | `timestamp_status="present"` | malformed `bext` fails at the stage that proves malformation |
| `smpl.sample_period` | unsigned 32-bit nanoseconds per sample | consistency evidence only | malformed `smpl` fails at the stage that proves malformation |
| encoder delay source | none in P7-A1 | `encoder_delay_status="absent"` | not applicable |
| encoder padding source | none in P7-A1 | `encoder_padding_status="absent"` | not applicable |

Exact rational strings use this grammar:

```text
rational = numerator "/" denominator
numerator = "0" / (["-"] nonzero_digit *digit)
denominator = nonzero_digit *digit
```

The denominator is always positive. Serialized rationals must be reduced to
lowest terms, must not contain whitespace or plus signs, and must use ASCII
digits only. Decimal finite JSON numbers may appear only where the table above
allows finite numbers.

P7-A1 duration is always derived from decoded `sample_count_per_channel` and
`sample_rate`. `smpl.sample_period` is a consistency check only; it is an
integer nanoseconds-per-sample declaration and must not be compared to total
duration or override duration. Let `sample_period_ns` be the unsigned integer
from `smpl.sample_period`, `sample_rate_hz` be the selected decoded sample
rate, and:

```text
q, r = divmod(1_000_000_000, sample_rate_hz)
expected = q      when 2 * r < sample_rate_hz
expected = q + 1  when 2 * r > sample_rate_hz
expected = the even value among q and q + 1 when 2 * r == sample_rate_hz
```

This is nearest-even rounding of the exact rational nanoseconds-per-sample
period. The `smpl.sample_period` value is consistent exactly when
`sample_period_ns == expected`; adjacent values are not accepted even at an
exact half-nanosecond tie. This accepts the unique integer nanosecond
representation of rates such as 44.1 kHz without using binary floating point.
If it conflicts, the outcome is
`failed/resolving/decode_error` when the bounded resolving probe has proven both
the sample rate and `smpl.sample_period`; otherwise it is
`failed/decoding/decode_error` at the first decoding step that proves the
conflict. Problem details include `media_kind="audio"`,
`field="smpl.sample_period"`, `value_kind="integer"`, `expected` as the nearest
accepted integer nanoseconds per sample, and `actual` as the declared
`sample_period_ns`.

Minimal `smpl.sample_period` consistency vectors:

```json
[
  {
    "case": "exact",
    "sample_rate_hz": 8000,
    "q": 125000,
    "r": 0,
    "expected": 125000,
    "sample_period_ns": 125000,
    "consistent": true
  },
  {
    "case": "rounded_44100",
    "sample_rate_hz": 44100,
    "q": 22675,
    "r": 32500,
    "expected": 22676,
    "sample_period_ns": 22676,
    "consistent": true
  },
  {
    "case": "conflict_44100",
    "sample_rate_hz": 44100,
    "q": 22675,
    "r": 32500,
    "expected": 22676,
    "sample_period_ns": 22675,
    "consistent": false,
    "failure_stage": "resolving",
    "failure_code": "decode_error",
    "details": {
      "media_kind": "audio",
      "field": "smpl.sample_period",
      "value_kind": "integer",
      "expected": 22676,
      "actual": 22675
    }
  },
  {
    "case": "tie_1024_even_accepted",
    "sample_rate_hz": 1024,
    "q": 976562,
    "r": 512,
    "expected": 976562,
    "sample_period_ns": 976562,
    "consistent": true
  },
  {
    "case": "tie_1024_odd_rejected",
    "sample_rate_hz": 1024,
    "q": 976562,
    "r": 512,
    "expected": 976562,
    "sample_period_ns": 976563,
    "consistent": false,
    "failure_stage": "resolving",
    "failure_code": "decode_error",
    "details": {
      "media_kind": "audio",
      "field": "smpl.sample_period",
      "value_kind": "integer",
      "expected": 976562,
      "actual": 976563
    }
  }
]
```

All other chunks are metadata facts only when RFC 0011 already allows them as
bounded chunk facts. They must not silently affect sample coordinates,
duration, alignment, or equality.

## Problem message and details

`problem.message` is the only location for user-facing explanatory prose.
`problem.details` is the only location for structured values. Detail values
must be strings, integers, finite JSON numbers, booleans, `null`, or RFC 0011
`expected`/`actual` arrays whose elements are strings, integers, finite JSON
numbers, or booleans. Other arrays and all objects remain invalid unless a
later schema revision explicitly permits them.

RFC 0012 keeps and supersedes the RFC 0011 problem-details allowlist by adding
only the resource accounting and operation/fact keys needed above. Problem
detail objects are closed and use the key order shown here. Optional keys are
omitted when unavailable; they are not filled with `null` unless the type
explicitly includes `null`.

| Key | Type |
| --- | --- |
| `stage` | canonical lifecycle stage string |
| `code` | stable problem code string |
| `media_kind` | `"audio"` |
| `relation` | selected relation string |
| `backend` | backend string |
| `profile` | profile string |
| `input_side` | `"before"`, `"after"`, or `"both"` |
| `byte_offset` | non-negative integer |
| `chunk_id` | four-byte ASCII chunk ID string |
| `field` | schema or header field name |
| `value_kind` | one of `"string"`, `"integer"`, `"finite_number"`, `"boolean"`, `"null"`, or `"array"` |
| `expected` | string, finite number, boolean, or array of those primitive values |
| `actual` | string, finite number, boolean, or array of those primitive values |
| `limit_name` | accepted resource limit name |
| `limit_value` | non-negative integer |
| `limit_unit` | exact unit string from the resource table |
| `accounting_scope` | one value from the closed accounting-scope enum |
| `measured_value` | non-negative integer in `limit_unit` |
| `operation` | accepted `AudioChange.operation` string |
| `fact_name` | accepted `AudioFact.name` string |

Detail values must not contain backend stderr, exception class names, host
paths, source filenames, safe labels, explanatory sentences, or arbitrary
dictionaries.

## Fixture recipe and oracle

The canonical vectors below are generated from this Python 3.12 stdlib recipe.
The recipe is the single source of truth for WAV bytes, input SHA-256 values,
decoded PCM payloads, RFC 0011 framed change digests, decoded byte usage, and
comparison work:

```python
import io
import struct
import wave


def pcm_s16le_wav(samples: list[int]) -> bytes:
    out = io.BytesIO()
    with wave.open(out, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))
    return out.getvalue()


PC_B_BEFORE_SAMPLES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
PC_B_AFTER_SAMPLES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 100, 101, 102]
PC_E_SAMPLES = [0]
```

Expected bytes and hashes:

| Name | Samples | Size | SHA-256 | Hex |
| --- | --- | ---: | --- | --- |
| `PC_B_BEFORE` | `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]` | `70` | `832bba329af2eaf85edb3c0453e172af87c206d1cb956026b450bb8feb413481` | `524946463e00000057415645666d74201000000001000100401f0000803e000002001000646174611a00000000000100020003000400050006000700080009000a000b000c00` |
| `PC_B_AFTER` | `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 100, 101, 102]` | `70` | `dfd8c66124c26c5754bb84896fc764a21ab5d1aacd93c95eb1684943edd96c71` | `524946463e00000057415645666d74201000000001000100401f0000803e000002001000646174611a0000000000010002000300040005000600070008000900640065006600` |
| `PC_E_ONE_ZERO` | `[0]` | `46` | `4aebda3a657a0d8f532d11ceacb1679081d7bdf7d7d301a53f1096af3580be91` | `524946462600000057415645666d74201000000001000100401f0000803e00000200100064617461020000000000` |

The PC-B decoded run is samples 10 through 12. Its RFC 0011
`audio.decoded_samples.v1` framed digests are:

| Side | Digest |
| --- | --- |
| before | `2d835305250ffbf0bc5ee2278d5f9d015c7481547881cdcfdc09c325a4013ec6` |
| after | `1c88a697051262817a32ed38cda1e89a62dd0eb5af31844914596374de180d06` |

The same byte fixtures produce PC-G. Their encoded bytes are unequal at source
offsets `64`, `66`, and `68`; the longest common suffix is one byte, so the
canonical middle run is source byte range `[64, 69)`. The framed middle digests
are before `5bd6bdbcf274f74dd10af75c59d9d1eba0b81f5bae04f0c20a1a3d2aaa393ef6`
and after `31d9ec12b520aa2b3ab905224a6d9796602d5765de0d68f8d46ba57ecb44f805`.
`audio.bytes_changed` is `3`, while the emitted change coordinate
`byte_count` is `5`. Work remains `64` prefix comparisons, `1` suffix
comparison, `5` middle grouping units, and `13` decoded-sample work units, for
a total of `83`. The decoded relation differs at sample range `[10, 13)`.

## Canonical vectors

These vectors are normative examples for acceptance tests. They are complete
wire envelopes after default insertion. PC-F is the explicit predecessor
upgrade vector: it shows the schema-v6 defaulted media fields that v1-v5
upgraders add without inferring audio facts. PC-G through PC-I are completed
producer-side truncation results after comparison and aggregation.

### Vector PC-A: equal empty encoded bytes

```json
{
  "schema_version": 6,
  "kind": "completed",
  "execution": {
    "started_at": "2026-09-10T00:00:00Z",
    "finished_at": "2026-09-10T00:00:00Z",
    "duration_ns": 0,
    "stages": [
      {
        "stage": "validating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "sourcing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "resolving",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "decoding",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "normalizing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aligning",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "comparing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aggregating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      }
    ],
    "attempts": [
      {
        "capability_id": "builtin.audio",
        "backend_id": null,
        "disposition": "selected",
        "reason_code": null,
        "capability_version": "1",
        "backend_version": null,
        "provider": null
      }
    ],
    "diagnostics": [],
    "last_completed_stage": "aggregating",
    "plugin_host": null
  },
  "result": {
    "relation": "equal",
    "verdict": "pass",
    "fidelity": "full",
    "completeness": "complete",
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
    "evaluations": [
      {
        "rule_id": "audio.policy.encoded_bytes.v1",
        "verdict": "pass",
        "metric_name": "audio.bytes_changed",
        "operator": "eq",
        "threshold": {
          "kind": "finite",
          "value": 0
        },
        "observed": {
          "kind": "finite",
          "value": 0
        }
      }
    ],
    "artifacts": [],
    "provenance": {
      "inputs": [
        {
          "role": "before",
          "source_kind": "bytes",
          "size_bytes": 0,
          "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
          "label": null
        },
        {
          "role": "after",
          "source_kind": "bytes",
          "size_bytes": 0,
          "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
          "label": null
        }
      ],
      "spec": {
        "kind": "audio",
        "relations": [
          "encoded_bytes"
        ],
        "stream": {
          "index": null,
          "require_channel_labels": false
        },
        "decode": {
          "backend": "stdlib_wave_pcm",
          "profile": "p7_a1_wav_pcm",
          "sample_representation": "native_pcm_integer",
          "unsupported_profile": "unavailable",
          "max_probe_bytes": 65536
        },
        "alignment": {
          "mode": "sample_index",
          "fixed_offset_samples": 0,
          "max_search_offset_samples": 0,
          "max_drift_ppm": 0.0,
          "ambiguity_margin_samples": 0
        },
        "waveform": {
          "enabled": false,
          "sample_metric": "absolute_error",
          "atol": 0.0,
          "rtol": 0.0,
          "alignment_mode": "sample_index"
        },
        "spectral": {
          "enabled": false,
          "window_function": "hann",
          "window_size": 2048,
          "hop_size": 512,
          "fft_size": 2048,
          "power_scale": "power"
        },
        "perceptual": {
          "enabled": false,
          "backend": null,
          "model": null,
          "score_name": null,
          "license_acknowledged": false
        },
        "artifact_policy": "none",
        "limits": {
          "max_input_bytes": 268435456,
          "max_streams": 32,
          "max_duration_seconds": 3600,
          "max_sample_rate_hz": 384000,
          "max_channels": 64,
          "max_decoded_samples_per_channel": 50000000,
          "max_total_decoded_bytes": 536870912,
          "max_resident_buffer_bytes": 134217728,
          "max_packets": 1000000,
          "max_metadata_entries": 10000,
          "max_metadata_value_bytes": 1048576,
          "max_spectral_cells": 20000000,
          "max_backend_seconds": 30,
          "max_stdout_stderr_bytes": 4194304,
          "max_temp_bytes": 536870912,
          "max_materialized_bytes": 536870912,
          "max_compare_work": 10000000,
          "max_change_items": 10000,
          "max_change_payload_bytes": 4194304
        }
      },
      "transformations": [],
      "comparator_id": "builtin.audio",
      "comparator_version": "1",
      "algorithm_id": "audio.encoded_bytes.exact.v1",
      "implementation_version": "p7-a1-accepted",
      "seeds": [],
      "resources": [
        {
          "name": "max_compare_work",
          "limit": 10000000,
          "used": 0
        }
      ],
      "provider": null,
      "detector_provider": null
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
        "algorithm_id": "audio.encoded_bytes.exact.v1",
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

### Vector PC-B: one continuous sample update from real WAV payloads

```json
{
  "schema_version": 6,
  "kind": "completed",
  "execution": {
    "started_at": "2026-09-10T00:00:00Z",
    "finished_at": "2026-09-10T00:00:00Z",
    "duration_ns": 0,
    "stages": [
      {
        "stage": "validating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "sourcing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "resolving",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "decoding",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "normalizing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aligning",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "comparing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aggregating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      }
    ],
    "attempts": [
      {
        "capability_id": "builtin.audio",
        "backend_id": "stdlib_wave_pcm",
        "disposition": "selected",
        "reason_code": null,
        "capability_version": "1",
        "backend_version": "stdlib_wave_pcm.p7_a1",
        "provider": null
      }
    ],
    "diagnostics": [],
    "last_completed_stage": "aggregating",
    "plugin_host": null
  },
  "result": {
    "relation": "different",
    "verdict": "fail",
    "fidelity": "full",
    "completeness": "complete",
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
          "before_digest": "sha256:2d835305250ffbf0bc5ee2278d5f9d015c7481547881cdcfdc09c325a4013ec6",
          "after_digest": "sha256:1c88a697051262817a32ed38cda1e89a62dd0eb5af31844914596374de180d06",
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
      },
      {
        "name": "audio.samples_compared",
        "value": {
          "kind": "finite",
          "value": 13
        },
        "unit": "samples",
        "direction": "neutral",
        "aggregation": "count"
      },
      {
        "name": "audio.channels_compared",
        "value": {
          "kind": "finite",
          "value": 1
        },
        "unit": "channels",
        "direction": "neutral",
        "aggregation": "count"
      }
    ],
    "evaluations": [
      {
        "rule_id": "audio.policy.exact_decoded_samples.v1",
        "verdict": "fail",
        "metric_name": "audio.samples_changed",
        "operator": "eq",
        "threshold": {
          "kind": "finite",
          "value": 0
        },
        "observed": {
          "kind": "finite",
          "value": 3
        }
      }
    ],
    "artifacts": [],
    "provenance": {
      "inputs": [
        {
          "role": "before",
          "source_kind": "bytes",
          "size_bytes": 70,
          "sha256": "832bba329af2eaf85edb3c0453e172af87c206d1cb956026b450bb8feb413481",
          "label": null
        },
        {
          "role": "after",
          "source_kind": "bytes",
          "size_bytes": 70,
          "sha256": "dfd8c66124c26c5754bb84896fc764a21ab5d1aacd93c95eb1684943edd96c71",
          "label": null
        }
      ],
      "spec": {
        "kind": "audio",
        "relations": [
          "decoded_samples"
        ],
        "stream": {
          "index": 0,
          "require_channel_labels": false
        },
        "decode": {
          "backend": "stdlib_wave_pcm",
          "profile": "p7_a1_wav_pcm",
          "sample_representation": "native_pcm_integer",
          "unsupported_profile": "unavailable",
          "max_probe_bytes": 65536
        },
        "alignment": {
          "mode": "sample_index",
          "fixed_offset_samples": 0,
          "max_search_offset_samples": 0,
          "max_drift_ppm": 0.0,
          "ambiguity_margin_samples": 0
        },
        "waveform": {
          "enabled": false,
          "sample_metric": "absolute_error",
          "atol": 0.0,
          "rtol": 0.0,
          "alignment_mode": "sample_index"
        },
        "spectral": {
          "enabled": false,
          "window_function": "hann",
          "window_size": 2048,
          "hop_size": 512,
          "fft_size": 2048,
          "power_scale": "power"
        },
        "perceptual": {
          "enabled": false,
          "backend": null,
          "model": null,
          "score_name": null,
          "license_acknowledged": false
        },
        "artifact_policy": "none",
        "limits": {
          "max_input_bytes": 268435456,
          "max_streams": 32,
          "max_duration_seconds": 3600,
          "max_sample_rate_hz": 384000,
          "max_channels": 64,
          "max_decoded_samples_per_channel": 50000000,
          "max_total_decoded_bytes": 536870912,
          "max_resident_buffer_bytes": 134217728,
          "max_packets": 1000000,
          "max_metadata_entries": 10000,
          "max_metadata_value_bytes": 1048576,
          "max_spectral_cells": 20000000,
          "max_backend_seconds": 30,
          "max_stdout_stderr_bytes": 4194304,
          "max_temp_bytes": 536870912,
          "max_materialized_bytes": 536870912,
          "max_compare_work": 10000000,
          "max_change_items": 10000,
          "max_change_payload_bytes": 4194304
        }
      },
      "transformations": [
        {
          "stage": "decoding",
          "transformation_id": "audio.decode.stdlib_wave_pcm.v1",
          "parameters": {
            "backend": "stdlib_wave_pcm",
            "profile": "p7_a1_wav_pcm"
          }
        },
        {
          "stage": "aligning",
          "transformation_id": "audio.align.sample_index.v1",
          "parameters": {}
        }
      ],
      "comparator_id": "builtin.audio",
      "comparator_version": "1",
      "algorithm_id": "audio.decoded_samples.exact.v1",
      "implementation_version": "p7-a1-accepted",
      "seeds": [],
      "resources": [
        {
          "name": "max_compare_work",
          "limit": 10000000,
          "used": 13
        },
        {
          "name": "max_total_decoded_bytes",
          "limit": 536870912,
          "used": 52
        }
      ],
      "provider": null,
      "detector_provider": null
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
          "audio.channels_compared",
          "audio.samples_changed",
          "audio.samples_compared"
        ],
        "policy_rule_ids": [
          "audio.policy.exact_decoded_samples.v1"
        ],
        "transformation_ids": [
          "audio.decode.stdlib_wave_pcm.v1",
          "audio.align.sample_index.v1"
        ],
        "algorithm_id": "audio.decoded_samples.exact.v1",
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
  "schema_version": 6,
  "kind": "completed",
  "execution": {
    "started_at": "2026-09-10T00:00:00Z",
    "finished_at": "2026-09-10T00:00:00Z",
    "duration_ns": 0,
    "stages": [
      {
        "stage": "validating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "sourcing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "resolving",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "decoding",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "normalizing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aligning",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "comparing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aggregating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      }
    ],
    "attempts": [
      {
        "capability_id": "builtin.audio",
        "backend_id": null,
        "disposition": "selected",
        "reason_code": null,
        "capability_version": "1",
        "backend_version": null,
        "provider": null
      }
    ],
    "diagnostics": [],
    "last_completed_stage": "aggregating",
    "plugin_host": null
  },
  "result": {
    "relation": "different",
    "verdict": "fail",
    "fidelity": "full",
    "completeness": "complete",
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
    "evaluations": [
      {
        "rule_id": "audio.policy.encoded_bytes.v1",
        "verdict": "fail",
        "metric_name": "audio.bytes_changed",
        "operator": "eq",
        "threshold": {
          "kind": "finite",
          "value": 0
        },
        "observed": {
          "kind": "finite",
          "value": 2
        }
      }
    ],
    "artifacts": [],
    "provenance": {
      "inputs": [
        {
          "role": "before",
          "source_kind": "bytes",
          "size_bytes": 4,
          "sha256": "0000000000000000000000000000000000000000000000000000000000000201",
          "label": null
        },
        {
          "role": "after",
          "source_kind": "bytes",
          "size_bytes": 6,
          "sha256": "0000000000000000000000000000000000000000000000000000000000000202",
          "label": null
        }
      ],
      "spec": {
        "kind": "audio",
        "relations": [
          "encoded_bytes"
        ],
        "stream": {
          "index": null,
          "require_channel_labels": false
        },
        "decode": {
          "backend": "stdlib_wave_pcm",
          "profile": "p7_a1_wav_pcm",
          "sample_representation": "native_pcm_integer",
          "unsupported_profile": "unavailable",
          "max_probe_bytes": 65536
        },
        "alignment": {
          "mode": "sample_index",
          "fixed_offset_samples": 0,
          "max_search_offset_samples": 0,
          "max_drift_ppm": 0.0,
          "ambiguity_margin_samples": 0
        },
        "waveform": {
          "enabled": false,
          "sample_metric": "absolute_error",
          "atol": 0.0,
          "rtol": 0.0,
          "alignment_mode": "sample_index"
        },
        "spectral": {
          "enabled": false,
          "window_function": "hann",
          "window_size": 2048,
          "hop_size": 512,
          "fft_size": 2048,
          "power_scale": "power"
        },
        "perceptual": {
          "enabled": false,
          "backend": null,
          "model": null,
          "score_name": null,
          "license_acknowledged": false
        },
        "artifact_policy": "none",
        "limits": {
          "max_input_bytes": 268435456,
          "max_streams": 32,
          "max_duration_seconds": 3600,
          "max_sample_rate_hz": 384000,
          "max_channels": 64,
          "max_decoded_samples_per_channel": 50000000,
          "max_total_decoded_bytes": 536870912,
          "max_resident_buffer_bytes": 134217728,
          "max_packets": 1000000,
          "max_metadata_entries": 10000,
          "max_metadata_value_bytes": 1048576,
          "max_spectral_cells": 20000000,
          "max_backend_seconds": 30,
          "max_stdout_stderr_bytes": 4194304,
          "max_temp_bytes": 536870912,
          "max_materialized_bytes": 536870912,
          "max_compare_work": 10000000,
          "max_change_items": 10000,
          "max_change_payload_bytes": 4194304
        }
      },
      "transformations": [],
      "comparator_id": "builtin.audio",
      "comparator_version": "1",
      "algorithm_id": "audio.encoded_bytes.exact.v1",
      "implementation_version": "p7-a1-accepted",
      "seeds": [],
      "resources": [
        {
          "name": "max_compare_work",
          "limit": 10000000,
          "used": 6
        }
      ],
      "provider": null,
      "detector_provider": null
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
        "algorithm_id": "audio.encoded_bytes.exact.v1",
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

### Vector PC-D: decoded resource limit failure

```json
{
  "schema_version": 6,
  "kind": "failed",
  "execution": {
    "started_at": "2026-09-10T00:00:00Z",
    "finished_at": "2026-09-10T00:00:00Z",
    "duration_ns": 0,
    "stages": [
      {
        "stage": "validating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "sourcing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "resolving",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "decoding",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "failed"
      }
    ],
    "attempts": [
      {
        "capability_id": "builtin.audio",
        "backend_id": "stdlib_wave_pcm",
        "disposition": "failed",
        "reason_code": "resource_limit_exceeded",
        "capability_version": "1",
        "backend_version": "stdlib_wave_pcm.p7_a1",
        "provider": null
      }
    ],
    "diagnostics": [],
    "last_completed_stage": "resolving",
    "plugin_host": null
  },
  "problem": {
    "code": "resource_limit_exceeded",
    "status_code": 413,
    "stage": "decoding",
    "message": "audio decoding exceeded max_total_decoded_bytes",
    "details": {
      "media_kind": "audio",
      "relation": "decoded_samples",
      "backend": "stdlib_wave_pcm",
      "profile": "p7_a1_wav_pcm",
      "limit_name": "max_total_decoded_bytes",
      "limit_value": 0,
      "limit_unit": "decoded PCM bytes across both inputs",
      "accounting_scope": "dual_input_sum",
      "measured_value": 2,
      "input_side": "both"
    },
    "retryable": false
  }
}
```

### Vector PC-E: equal decoded facts from one-sample WAV payloads

```json
{
  "schema_version": 6,
  "kind": "completed",
  "execution": {
    "started_at": "2026-09-10T00:00:00Z",
    "finished_at": "2026-09-10T00:00:00Z",
    "duration_ns": 0,
    "stages": [
      {
        "stage": "validating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "sourcing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "resolving",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "decoding",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "normalizing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aligning",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "comparing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aggregating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      }
    ],
    "attempts": [
      {
        "capability_id": "builtin.audio",
        "backend_id": "stdlib_wave_pcm",
        "disposition": "selected",
        "reason_code": null,
        "capability_version": "1",
        "backend_version": "stdlib_wave_pcm.p7_a1",
        "provider": null
      }
    ],
    "diagnostics": [],
    "last_completed_stage": "aggregating",
    "plugin_host": null
  },
  "result": {
    "relation": "equal",
    "verdict": "pass",
    "fidelity": "full",
    "completeness": "complete",
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
        "name": "audio.samples_changed",
        "value": {
          "kind": "finite",
          "value": 0
        },
        "unit": "samples",
        "direction": "lower_is_better",
        "aggregation": "count"
      },
      {
        "name": "audio.samples_compared",
        "value": {
          "kind": "finite",
          "value": 1
        },
        "unit": "samples",
        "direction": "neutral",
        "aggregation": "count"
      },
      {
        "name": "audio.channels_compared",
        "value": {
          "kind": "finite",
          "value": 1
        },
        "unit": "channels",
        "direction": "neutral",
        "aggregation": "count"
      }
    ],
    "evaluations": [
      {
        "rule_id": "audio.policy.exact_decoded_samples.v1",
        "verdict": "pass",
        "metric_name": "audio.samples_changed",
        "operator": "eq",
        "threshold": {
          "kind": "finite",
          "value": 0
        },
        "observed": {
          "kind": "finite",
          "value": 0
        }
      }
    ],
    "artifacts": [],
    "provenance": {
      "inputs": [
        {
          "role": "before",
          "source_kind": "bytes",
          "size_bytes": 46,
          "sha256": "4aebda3a657a0d8f532d11ceacb1679081d7bdf7d7d301a53f1096af3580be91",
          "label": null
        },
        {
          "role": "after",
          "source_kind": "bytes",
          "size_bytes": 46,
          "sha256": "4aebda3a657a0d8f532d11ceacb1679081d7bdf7d7d301a53f1096af3580be91",
          "label": null
        }
      ],
      "spec": {
        "kind": "audio",
        "relations": [
          "decoded_samples"
        ],
        "stream": {
          "index": 0,
          "require_channel_labels": false
        },
        "decode": {
          "backend": "stdlib_wave_pcm",
          "profile": "p7_a1_wav_pcm",
          "sample_representation": "native_pcm_integer",
          "unsupported_profile": "unavailable",
          "max_probe_bytes": 65536
        },
        "alignment": {
          "mode": "sample_index",
          "fixed_offset_samples": 0,
          "max_search_offset_samples": 0,
          "max_drift_ppm": 0.0,
          "ambiguity_margin_samples": 0
        },
        "waveform": {
          "enabled": false,
          "sample_metric": "absolute_error",
          "atol": 0.0,
          "rtol": 0.0,
          "alignment_mode": "sample_index"
        },
        "spectral": {
          "enabled": false,
          "window_function": "hann",
          "window_size": 2048,
          "hop_size": 512,
          "fft_size": 2048,
          "power_scale": "power"
        },
        "perceptual": {
          "enabled": false,
          "backend": null,
          "model": null,
          "score_name": null,
          "license_acknowledged": false
        },
        "artifact_policy": "none",
        "limits": {
          "max_input_bytes": 268435456,
          "max_streams": 32,
          "max_duration_seconds": 3600,
          "max_sample_rate_hz": 384000,
          "max_channels": 64,
          "max_decoded_samples_per_channel": 50000000,
          "max_total_decoded_bytes": 536870912,
          "max_resident_buffer_bytes": 134217728,
          "max_packets": 1000000,
          "max_metadata_entries": 10000,
          "max_metadata_value_bytes": 1048576,
          "max_spectral_cells": 20000000,
          "max_backend_seconds": 30,
          "max_stdout_stderr_bytes": 4194304,
          "max_temp_bytes": 536870912,
          "max_materialized_bytes": 536870912,
          "max_compare_work": 10000000,
          "max_change_items": 10000,
          "max_change_payload_bytes": 4194304
        }
      },
      "transformations": [
        {
          "stage": "decoding",
          "transformation_id": "audio.decode.stdlib_wave_pcm.v1",
          "parameters": {
            "backend": "stdlib_wave_pcm",
            "profile": "p7_a1_wav_pcm"
          }
        },
        {
          "stage": "aligning",
          "transformation_id": "audio.align.sample_index.v1",
          "parameters": {}
        }
      ],
      "comparator_id": "builtin.audio",
      "comparator_version": "1",
      "algorithm_id": "audio.decoded_samples.exact.v1",
      "implementation_version": "p7-a1-accepted",
      "seeds": [],
      "resources": [
        {
          "name": "max_compare_work",
          "limit": 10000000,
          "used": 1
        },
        {
          "name": "max_total_decoded_bytes",
          "limit": 536870912,
          "used": 4
        }
      ],
      "provider": null,
      "detector_provider": null
    },
    "media_evaluations": [
      {
        "kind": "media_view_evaluation",
        "media_kind": "audio",
        "selector": "decoded_samples",
        "relation": "equal",
        "verdict": "pass",
        "fidelity": "full",
        "completeness": "complete",
        "metric_names": [
          "audio.channels_compared",
          "audio.samples_changed",
          "audio.samples_compared"
        ],
        "policy_rule_ids": [
          "audio.policy.exact_decoded_samples.v1"
        ],
        "transformation_ids": [
          "audio.decode.stdlib_wave_pcm.v1",
          "audio.align.sample_index.v1"
        ],
        "algorithm_id": "audio.decoded_samples.exact.v1",
        "warning_codes": [],
        "change_count": 0,
        "failure_stage": null,
        "failure_code": null
      }
    ],
    "audio_facts": [
      {
        "name": "container.form",
        "value": "RIFF/WAVE",
        "unit": "tag",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "codec.profile",
        "value": "p7_a1_wav_pcm",
        "unit": "name",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "stream.index",
        "value": 0,
        "unit": "index",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "sample_rate",
        "value": 8000,
        "unit": "Hz",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "channel_count",
        "value": 1,
        "unit": "count",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "channel_layout",
        "value": "unknown_ordered",
        "unit": "name",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "channel_mask",
        "value": null,
        "unit": "bitmask",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "sample_format",
        "value": "pcm_s16le",
        "unit": "name",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "container_bits_per_sample",
        "value": 16,
        "unit": "bits",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "valid_bits_per_sample",
        "value": 16,
        "unit": "bits",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "sample_count_per_channel",
        "value": 1,
        "unit": "samples",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "duration_seconds",
        "value": 0.000125,
        "unit": "s",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "duration_numerator",
        "value": 1,
        "unit": "samples",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "duration_denominator",
        "value": 8000,
        "unit": "Hz",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "timestamp_status",
        "value": "absent",
        "unit": "name",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "encoder_delay_status",
        "value": "absent",
        "unit": "name",
        "stream_index": 0,
        "coordinate": null
      },
      {
        "name": "encoder_padding_status",
        "value": "absent",
        "unit": "name",
        "stream_index": 0,
        "coordinate": null
      }
    ]
  }
}
```

### Vector PC-F: predecessor upgrade defaults

```json
{
  "schema_version": 6,
  "kind": "completed",
  "execution": {
    "started_at": "2026-09-10T00:00:00Z",
    "finished_at": "2026-09-10T00:00:00Z",
    "duration_ns": 0,
    "stages": [
      {
        "stage": "validating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "sourcing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "resolving",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "decoding",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "normalizing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aligning",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "comparing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aggregating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      }
    ],
    "attempts": [
      {
        "capability_id": "text",
        "backend_id": null,
        "disposition": "selected",
        "reason_code": null,
        "capability_version": "1",
        "backend_version": null,
        "provider": null
      }
    ],
    "diagnostics": [],
    "last_completed_stage": "aggregating",
    "plugin_host": null
  },
  "result": {
    "relation": "equal",
    "verdict": "pass",
    "fidelity": "full",
    "completeness": "complete",
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
    "metrics": [],
    "evaluations": [
      {
        "rule_id": "strict_equality",
        "verdict": "pass",
        "metric_name": null,
        "operator": null,
        "threshold": null,
        "observed": null
      }
    ],
    "artifacts": [],
    "provenance": {
      "inputs": [
        {
          "role": "before",
          "source_kind": "text",
          "size_bytes": 1,
          "sha256": "0000000000000000000000000000000000000000000000000000000000000401",
          "label": null
        },
        {
          "role": "after",
          "source_kind": "text",
          "size_bytes": 1,
          "sha256": "0000000000000000000000000000000000000000000000000000000000000401",
          "label": null
        }
      ],
      "spec": {
        "kind": "text",
        "algorithm": "myers"
      },
      "transformations": [],
      "comparator_id": "text",
      "comparator_version": "1",
      "algorithm_id": "text.myers.linear_space.v1",
      "implementation_version": "1",
      "seeds": [],
      "resources": [],
      "provider": null,
      "detector_provider": null
    },
    "media_evaluations": [],
    "audio_facts": []
  }
}
```

### Vector PC-G: dual-relation item-limit truncation from PC-B WAV payloads

```json
{
  "schema_version": 6,
  "kind": "completed",
  "execution": {
    "started_at": "2026-09-10T00:00:00Z",
    "finished_at": "2026-09-10T00:00:00Z",
    "duration_ns": 0,
    "stages": [
      {
        "stage": "validating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "sourcing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "resolving",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "decoding",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "normalizing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aligning",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "comparing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aggregating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      }
    ],
    "attempts": [
      {
        "capability_id": "builtin.audio",
        "backend_id": "stdlib_wave_pcm",
        "disposition": "selected",
        "reason_code": null,
        "capability_version": "1",
        "backend_version": "stdlib_wave_pcm.p7_a1",
        "provider": null
      }
    ],
    "diagnostics": [
      {
        "code": "change_details_truncated",
        "severity": "warning",
        "stage": "aggregating",
        "message": "Change details were truncated.",
        "details": {
          "limit_reason": "change_items"
        }
      }
    ],
    "last_completed_stage": "aggregating",
    "plugin_host": null
  },
  "result": {
    "relation": "different",
    "verdict": "fail",
    "fidelity": "full",
    "completeness": "truncated",
    "summary": {
      "change_count": 2,
      "counts": []
    },
    "changes": {
      "completeness": "truncated",
      "items": [
        {
          "kind": "audio_change",
          "relation": "encoded_bytes",
          "operation": "encoded_byte_update",
          "before_coordinate": {
            "stream_index": null,
            "channel_index": null,
            "channel_label": null,
            "sample_start": null,
            "sample_count": null,
            "time_start_seconds": null,
            "time_duration_seconds": null,
            "byte_start": 64,
            "byte_count": 5
          },
          "after_coordinate": {
            "stream_index": null,
            "channel_index": null,
            "channel_label": null,
            "sample_start": null,
            "sample_count": null,
            "time_start_seconds": null,
            "time_duration_seconds": null,
            "byte_start": 64,
            "byte_count": 5
          },
          "channel": null,
          "before_digest": "sha256:5bd6bdbcf274f74dd10af75c59d9d1eba0b81f5bae04f0c20a1a3d2aaa393ef6",
          "after_digest": "sha256:31d9ec12b520aa2b3ab905224a6d9796602d5765de0d68f8d46ba57ecb44f805",
          "before_fact": null,
          "after_fact": null
        }
      ],
      "total_count": 2,
      "returned_count": 1,
      "omitted_count": 1,
      "selection": "source_order_prefix",
      "limit": 1,
      "limit_reason": "change_items"
    },
    "metrics": [
      {
        "name": "audio.bytes_changed",
        "value": {
          "kind": "finite",
          "value": 3
        },
        "unit": "bytes",
        "direction": "lower_is_better",
        "aggregation": "count"
      },
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
    "evaluations": [
      {
        "rule_id": "audio.policy.encoded_bytes.v1",
        "verdict": "fail",
        "metric_name": "audio.bytes_changed",
        "operator": "eq",
        "threshold": {
          "kind": "finite",
          "value": 0
        },
        "observed": {
          "kind": "finite",
          "value": 6
        }
      },
      {
        "rule_id": "audio.policy.exact_decoded_samples.v1",
        "verdict": "fail",
        "metric_name": "audio.samples_changed",
        "operator": "eq",
        "threshold": {
          "kind": "finite",
          "value": 0
        },
        "observed": {
          "kind": "finite",
          "value": 3
        }
      }
    ],
    "artifacts": [],
    "provenance": {
      "inputs": [
        {
          "role": "before",
          "source_kind": "bytes",
          "size_bytes": 70,
          "sha256": "832bba329af2eaf85edb3c0453e172af87c206d1cb956026b450bb8feb413481",
          "label": null
        },
        {
          "role": "after",
          "source_kind": "bytes",
          "size_bytes": 70,
          "sha256": "dfd8c66124c26c5754bb84896fc764a21ab5d1aacd93c95eb1684943edd96c71",
          "label": null
        }
      ],
      "spec": {
        "kind": "audio",
        "relations": [
          "encoded_bytes",
          "decoded_samples"
        ],
        "stream": {
          "index": 0,
          "require_channel_labels": false
        },
        "decode": {
          "backend": "stdlib_wave_pcm",
          "profile": "p7_a1_wav_pcm",
          "sample_representation": "native_pcm_integer",
          "unsupported_profile": "unavailable",
          "max_probe_bytes": 65536
        },
        "alignment": {
          "mode": "sample_index",
          "fixed_offset_samples": 0,
          "max_search_offset_samples": 0,
          "max_drift_ppm": 0.0,
          "ambiguity_margin_samples": 0
        },
        "waveform": {
          "enabled": false,
          "sample_metric": "absolute_error",
          "atol": 0.0,
          "rtol": 0.0,
          "alignment_mode": "sample_index"
        },
        "spectral": {
          "enabled": false,
          "window_function": "hann",
          "window_size": 2048,
          "hop_size": 512,
          "fft_size": 2048,
          "power_scale": "power"
        },
        "perceptual": {
          "enabled": false,
          "backend": null,
          "model": null,
          "score_name": null,
          "license_acknowledged": false
        },
        "artifact_policy": "none",
        "limits": {
          "max_input_bytes": 268435456,
          "max_streams": 32,
          "max_duration_seconds": 3600,
          "max_sample_rate_hz": 384000,
          "max_channels": 64,
          "max_decoded_samples_per_channel": 50000000,
          "max_total_decoded_bytes": 536870912,
          "max_resident_buffer_bytes": 134217728,
          "max_packets": 1000000,
          "max_metadata_entries": 10000,
          "max_metadata_value_bytes": 1048576,
          "max_spectral_cells": 20000000,
          "max_backend_seconds": 30,
          "max_stdout_stderr_bytes": 4194304,
          "max_temp_bytes": 536870912,
          "max_materialized_bytes": 536870912,
          "max_compare_work": 10000000,
          "max_change_items": 1,
          "max_change_payload_bytes": 4194304
        }
      },
      "transformations": [
        {
          "stage": "decoding",
          "transformation_id": "audio.decode.stdlib_wave_pcm.v1",
          "parameters": {
            "backend": "stdlib_wave_pcm",
            "profile": "p7_a1_wav_pcm"
          }
        },
        {
          "stage": "aligning",
          "transformation_id": "audio.align.sample_index.v1",
          "parameters": {}
        }
      ],
      "comparator_id": "builtin.audio",
      "comparator_version": "1",
      "algorithm_id": "audio.aggregate.selected_relations.v1",
      "implementation_version": "p7-a1-accepted",
      "seeds": [],
      "resources": [
        {
          "name": "max_change_items",
          "limit": 1,
          "used": 1
        },
        {
          "name": "max_compare_work",
          "limit": 10000000,
          "used": 83
        },
        {
          "name": "max_total_decoded_bytes",
          "limit": 536870912,
          "used": 52
        }
      ],
      "provider": null,
      "detector_provider": null
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
        "algorithm_id": "audio.encoded_bytes.exact.v1",
        "warning_codes": [],
        "change_count": 1,
        "failure_stage": null,
        "failure_code": null
      },
      {
        "kind": "media_view_evaluation",
        "media_kind": "audio",
        "selector": "decoded_samples",
        "relation": "different",
        "verdict": "fail",
        "fidelity": "full",
        "completeness": "truncated",
        "metric_names": [
          "audio.samples_changed"
        ],
        "policy_rule_ids": [
          "audio.policy.exact_decoded_samples.v1"
        ],
        "transformation_ids": [
          "audio.decode.stdlib_wave_pcm.v1",
          "audio.align.sample_index.v1"
        ],
        "algorithm_id": "audio.decoded_samples.exact.v1",
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

### Vector PC-H: payload-limit zero truncation

```json
{
  "schema_version": 6,
  "kind": "completed",
  "execution": {
    "started_at": "2026-09-10T00:00:00Z",
    "finished_at": "2026-09-10T00:00:00Z",
    "duration_ns": 0,
    "stages": [
      {
        "stage": "validating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "sourcing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "resolving",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "decoding",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "normalizing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aligning",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "comparing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aggregating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      }
    ],
    "attempts": [
      {
        "capability_id": "builtin.audio",
        "backend_id": null,
        "disposition": "selected",
        "reason_code": null,
        "capability_version": "1",
        "backend_version": null,
        "provider": null
      }
    ],
    "diagnostics": [
      {
        "code": "change_details_truncated",
        "severity": "warning",
        "stage": "aggregating",
        "message": "Change details were truncated.",
        "details": {
          "limit_reason": "change_payload_bytes"
        }
      }
    ],
    "last_completed_stage": "aggregating",
    "plugin_host": null
  },
  "result": {
    "relation": "different",
    "verdict": "fail",
    "fidelity": "full",
    "completeness": "truncated",
    "summary": {
      "change_count": 1,
      "counts": []
    },
    "changes": {
      "completeness": "truncated",
      "items": [],
      "total_count": 1,
      "returned_count": 0,
      "omitted_count": 1,
      "selection": "source_order_prefix",
      "limit": 0,
      "limit_reason": "change_payload_bytes"
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
    "evaluations": [
      {
        "rule_id": "audio.policy.encoded_bytes.v1",
        "verdict": "fail",
        "metric_name": "audio.bytes_changed",
        "operator": "eq",
        "threshold": {
          "kind": "finite",
          "value": 0
        },
        "observed": {
          "kind": "finite",
          "value": 2
        }
      }
    ],
    "artifacts": [],
    "provenance": {
      "inputs": [
        {
          "role": "before",
          "source_kind": "bytes",
          "size_bytes": 4,
          "sha256": "0000000000000000000000000000000000000000000000000000000000000201",
          "label": null
        },
        {
          "role": "after",
          "source_kind": "bytes",
          "size_bytes": 6,
          "sha256": "0000000000000000000000000000000000000000000000000000000000000202",
          "label": null
        }
      ],
      "spec": {
        "kind": "audio",
        "relations": [
          "encoded_bytes"
        ],
        "stream": {
          "index": null,
          "require_channel_labels": false
        },
        "decode": {
          "backend": "stdlib_wave_pcm",
          "profile": "p7_a1_wav_pcm",
          "sample_representation": "native_pcm_integer",
          "unsupported_profile": "unavailable",
          "max_probe_bytes": 65536
        },
        "alignment": {
          "mode": "sample_index",
          "fixed_offset_samples": 0,
          "max_search_offset_samples": 0,
          "max_drift_ppm": 0.0,
          "ambiguity_margin_samples": 0
        },
        "waveform": {
          "enabled": false,
          "sample_metric": "absolute_error",
          "atol": 0.0,
          "rtol": 0.0,
          "alignment_mode": "sample_index"
        },
        "spectral": {
          "enabled": false,
          "window_function": "hann",
          "window_size": 2048,
          "hop_size": 512,
          "fft_size": 2048,
          "power_scale": "power"
        },
        "perceptual": {
          "enabled": false,
          "backend": null,
          "model": null,
          "score_name": null,
          "license_acknowledged": false
        },
        "artifact_policy": "none",
        "limits": {
          "max_input_bytes": 268435456,
          "max_streams": 32,
          "max_duration_seconds": 3600,
          "max_sample_rate_hz": 384000,
          "max_channels": 64,
          "max_decoded_samples_per_channel": 50000000,
          "max_total_decoded_bytes": 536870912,
          "max_resident_buffer_bytes": 134217728,
          "max_packets": 1000000,
          "max_metadata_entries": 10000,
          "max_metadata_value_bytes": 1048576,
          "max_spectral_cells": 20000000,
          "max_backend_seconds": 30,
          "max_stdout_stderr_bytes": 4194304,
          "max_temp_bytes": 536870912,
          "max_materialized_bytes": 536870912,
          "max_compare_work": 10000000,
          "max_change_items": 10000,
          "max_change_payload_bytes": 0
        }
      },
      "transformations": [],
      "comparator_id": "builtin.audio",
      "comparator_version": "1",
      "algorithm_id": "audio.encoded_bytes.exact.v1",
      "implementation_version": "p7-a1-accepted",
      "seeds": [],
      "resources": [
        {
          "name": "max_change_payload_bytes",
          "limit": 0,
          "used": 0
        }
      ],
      "provider": null,
      "detector_provider": null
    },
    "media_evaluations": [
      {
        "kind": "media_view_evaluation",
        "media_kind": "audio",
        "selector": "encoded_bytes",
        "relation": "different",
        "verdict": "fail",
        "fidelity": "full",
        "completeness": "truncated",
        "metric_names": [
          "audio.bytes_changed"
        ],
        "policy_rule_ids": [
          "audio.policy.encoded_bytes.v1"
        ],
        "transformation_ids": [],
        "algorithm_id": "audio.encoded_bytes.exact.v1",
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

### Vector PC-I: item-limit zero with zero total remains complete

```json
{
  "schema_version": 6,
  "kind": "completed",
  "execution": {
    "started_at": "2026-09-10T00:00:00Z",
    "finished_at": "2026-09-10T00:00:00Z",
    "duration_ns": 0,
    "stages": [
      {
        "stage": "validating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "sourcing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "resolving",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "decoding",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "normalizing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aligning",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "comparing",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      },
      {
        "stage": "aggregating",
        "started_at": "2026-09-10T00:00:00Z",
        "finished_at": "2026-09-10T00:00:00Z",
        "duration_ns": 0,
        "disposition": "completed"
      }
    ],
    "attempts": [
      {
        "capability_id": "builtin.audio",
        "backend_id": null,
        "disposition": "selected",
        "reason_code": null,
        "capability_version": "1",
        "backend_version": null,
        "provider": null
      }
    ],
    "diagnostics": [],
    "last_completed_stage": "aggregating",
    "plugin_host": null
  },
  "result": {
    "relation": "equal",
    "verdict": "pass",
    "fidelity": "full",
    "completeness": "complete",
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
    "evaluations": [
      {
        "rule_id": "audio.policy.encoded_bytes.v1",
        "verdict": "pass",
        "metric_name": "audio.bytes_changed",
        "operator": "eq",
        "threshold": {
          "kind": "finite",
          "value": 0
        },
        "observed": {
          "kind": "finite",
          "value": 0
        }
      }
    ],
    "artifacts": [],
    "provenance": {
      "inputs": [
        {
          "role": "before",
          "source_kind": "bytes",
          "size_bytes": 0,
          "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
          "label": null
        },
        {
          "role": "after",
          "source_kind": "bytes",
          "size_bytes": 0,
          "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
          "label": null
        }
      ],
      "spec": {
        "kind": "audio",
        "relations": [
          "encoded_bytes"
        ],
        "stream": {
          "index": null,
          "require_channel_labels": false
        },
        "decode": {
          "backend": "stdlib_wave_pcm",
          "profile": "p7_a1_wav_pcm",
          "sample_representation": "native_pcm_integer",
          "unsupported_profile": "unavailable",
          "max_probe_bytes": 65536
        },
        "alignment": {
          "mode": "sample_index",
          "fixed_offset_samples": 0,
          "max_search_offset_samples": 0,
          "max_drift_ppm": 0.0,
          "ambiguity_margin_samples": 0
        },
        "waveform": {
          "enabled": false,
          "sample_metric": "absolute_error",
          "atol": 0.0,
          "rtol": 0.0,
          "alignment_mode": "sample_index"
        },
        "spectral": {
          "enabled": false,
          "window_function": "hann",
          "window_size": 2048,
          "hop_size": 512,
          "fft_size": 2048,
          "power_scale": "power"
        },
        "perceptual": {
          "enabled": false,
          "backend": null,
          "model": null,
          "score_name": null,
          "license_acknowledged": false
        },
        "artifact_policy": "none",
        "limits": {
          "max_input_bytes": 268435456,
          "max_streams": 32,
          "max_duration_seconds": 3600,
          "max_sample_rate_hz": 384000,
          "max_channels": 64,
          "max_decoded_samples_per_channel": 50000000,
          "max_total_decoded_bytes": 536870912,
          "max_resident_buffer_bytes": 134217728,
          "max_packets": 1000000,
          "max_metadata_entries": 10000,
          "max_metadata_value_bytes": 1048576,
          "max_spectral_cells": 20000000,
          "max_backend_seconds": 30,
          "max_stdout_stderr_bytes": 4194304,
          "max_temp_bytes": 536870912,
          "max_materialized_bytes": 536870912,
          "max_compare_work": 10000000,
          "max_change_items": 0,
          "max_change_payload_bytes": 4194304
        }
      },
      "transformations": [],
      "comparator_id": "builtin.audio",
      "comparator_version": "1",
      "algorithm_id": "audio.encoded_bytes.exact.v1",
      "implementation_version": "p7-a1-accepted",
      "seeds": [],
      "resources": [
        {
          "name": "max_change_items",
          "limit": 0,
          "used": 0
        }
      ],
      "provider": null,
      "detector_provider": null
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
        "algorithm_id": "audio.encoded_bytes.exact.v1",
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

## Acceptance record

Reviewers confirmed all of the following on 2026-09-10:

1. RFC 0010 Option A/SP1-SP6 and the actual P4-C1, P5-A1/schema-v4, and
   P6-C0/schema-v5 predecessor gates remain required.
2. Schema-v6 remains exclusively audio.
3. Decoded-sample comparison remains stdlib WAV/PCM only.
4. `encoded_bytes` bypasses WAV probing and decoding and accepts arbitrary
   byte streams.
5. Equal result carriers and complete decoded-audio fact carriers are closed
   and use accepted schema-v6, `MediaViewEvaluation`, and `AudioFact` shapes.
6. Continuous grouping and metric counts are deterministic and independent of
   producer-side result-detail truncation.
7. The accepted `AudioResourceLimits` object remains complete; only scope and
   unit clarifications are added.
8. Problem prose is only in `problem.message`; structured data is only in
   `problem.details`.
9. English and Chinese texts are aligned.
10. No P7-A1 implementation, video, UI, FFmpeg, dependency, or PR work starts
    from this accepted amendment.
