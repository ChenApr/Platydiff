# RFC 0011: RFC 0009 Audio Preflight Amendment

[Chinese documentation](0011-rfc-0009-audio-preflight-amendment_zh.md)

- Status: Accepted
- Date: 2026-09-10
- Accepted: 2026-09-10
- Amends: [RFC 0009](0009-audio-and-video-comparison.md)
- Approved decisions: P7A-AM1 through P7A-AM10; P7A-W1 through P7A-W5
- Schema prerequisites: accepted RFC 0010 Option A/SP1-SP6 and actual P4-C1, P5-A1/schema-v4, and P6-C0/schema-v5 merges
- Dispatch prerequisite: RFC 0011 itself has merged
- Conditional implementation authorization: recorded for coordinator dispatch only after schema prerequisites and the dispatch prerequisite are satisfied
- Owners: Platydiff maintainers
- Implementation owner: coordinator-dispatched after schema prerequisites and RFC 0011 merge

## Summary and authorization boundary

This RFC accepts a contract amendment to RFC 0009 for P7-A1 audio
implementation preflight blockers. RFC acceptance itself does not start code;
conditional human authorization is recorded for coordinator-dispatched P7-A1
implementation after schema prerequisites and RFC 0011 itself merge. Acceptance
does not authorize dependency changes, FFmpeg, artifacts, UI, SDK v2, automatic
media detection, video implementation, or independent schema renumbering.

The amendment preserves all RFC 0009 predecessor gates and defers global schema
numbering to RFC 0010 Option A/SP1-SP6. Audio remains schema v6 only if RFC
0010 Option A/SP1-SP6 is accepted first and the P4-C1, P5-A1/schema-v4,
P6-C0/schema-v5 predecessors actually merge. P4-A1 JSON/schema-v3 must be
revalidated from current `main`, and P7-A1 remains gated until coordinator
dispatch after RFC 0011 itself has merged and the predecessor implementations
and compatibility fixtures are available. Video remains roadmap-only and waits
for a separate backend/worker amendment and the next schema successor.

## Recommended decisions

These IDs are approved P7-A1 contract decisions, subject to the prerequisites
and authorization boundary above.

| ID | Recommended decision | Alternative not selected |
| --- | --- | --- |
| P7A-AM1 | Freeze public audio option wire shapes, defaults, key order, and unknown-key rejection for stream selection, decode, waveform, spectral, and perceptual options. | Leave option objects partially implicit and discover behavior from implementation defaults. |
| P7A-AM2 | Represent encoded-byte differences as `AudioChange` entries and associate metrics/evaluations through `MediaViewEvaluation`, not through heterogeneous `ChangeSet` entries. | Add a separate encoded-byte change type or embed evaluation identifiers in changes. |
| P7A-AM3 | Freeze the P7-A1 `stdlib_wave_pcm` WAV/PCM profile, including RIFF/RIFX classification, classic PCM versus WAVE_FORMAT_EXTENSIBLE, bit depths, valid bits, channel masks, `fmt` extras, data chunks, padding, and trailing chunks. | Let the standard-library decoder decide which WAV variants are equivalent. |
| P7A-AM4 | Add a bounded pre-resolution WAV profile probe so valid-but-unsupported profiles fail at `resolving` with stable problem details before decode begins. | Report all unsupported-but-valid WAV profiles as decoding failures. |
| P7A-AM5 | Define absence and unknown semantics for timestamps, encoder delay/padding, and channel layout facts. | Treat absent facts as zero, empty, or backend metadata outside the result. |
| P7A-AM6 | Freeze change grouping, coordinate meaning, digest framing, fact names, units, ordering, and stable rule/comparator/algorithm/transformation/resource IDs. | Let renderers or tests infer grouping and identifiers from prose. |
| P7A-AM7 | Freeze duration and timebase binary64 determinism while preserving exact rational facts. | Allow platform-dependent float formatting or extended precision. |
| P7A-AM8 | Freeze first-gate CLI flags and require SDK-v1 plugin audio flags to be rejected before plugin execution. | Let generic plugin or media flags reach SDK v1.1 hosts. |
| P7A-AM9 | Freeze stable problem detail keys, value types, ordering, and omission rules for P7-A1 failures. | Pass through backend-specific detail dictionaries. |
| P7A-AM10 | Keep audio schema v6 conditional on approved RFC 0010 Option A/SP1-SP6 and the actual P4-C1, P5-A1/schema-v4, and P6-C0/schema-v5 merges. | Resolve cross-RFC closed-union numbering inside this audio-specific amendment. |
| P7A-W1 | Keep classic PCM `fmt ` chunk size 16 as the only P7-A1 decodable classic PCM form; valid size-18 chunks with `cbSize=0` are valid but unsupported. | Accept size-18 classic PCM as equivalent to size 16. |
| P7A-W2 | Keep multiple `data` chunks valid but unsupported for P7-A1. | Concatenate multiple `data` chunks and add explicit chunk-boundary facts. |
| P7A-W3 | For WAVE_FORMAT_EXTENSIBLE with `valid_bits < container_bits`, require profile-mandated unused padding bits to be zero, retain valid-bits and container-bits facts, and compare the validated stored integer representation exactly with no hidden masking; non-zero padding bits are malformed. | Mask unused bits before sample comparison. |
| P7A-W4 | Expose both `platydiff audio` and `platydiff compare --type audio`; both construct the same `CompareSpec` and execute the same comparison path, consistent with other built-ins. | Keep only the generic compare command. |
| P7A-W5 | Retain audio schema v6 only if RFC 0010 Option A/SP1-SP6 is accepted and the P4-C1, P5-A1/schema-v4, and P6-C0/schema-v5 predecessors actually merge. | Assign audio v6 independently inside this amendment. |

## Wire shapes and parsing rules

All option objects are JSON objects with closed keys. Unknown keys are invalid.
Keys are serialized in the order listed below. Defaults are inserted by the
schema-v6 reader before comparison, and omitted fields are equivalent only to
the documented defaults.

### `AudioStreamSelection`

This amendment tightens the accepted RFC 0009 `AudioStreamSelection` shape; it
does not replace it with a different field family.

Key order and defaults:

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `index` | integer or null | `null` | Preserves RFC 0009 `stream.index`. P7-A1 WAV has exactly one stream; `null` and `0` select it, while non-zero values are rejected as invalid intent before source inspection. |
| `require_channel_labels` | boolean | `false` | If true, missing or unknown source channel labels fail at `resolving` when proven by header facts, or at `decoding` if only proven after decode begins. |

### `AudioDecodeOptions`

Key order and defaults:

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `backend` | string | `"stdlib_wave_pcm"` | The only P7-A1 backend. |
| `profile` | string | `"p7_a1_wav_pcm"` | Selects the bounded WAV/PCM profile below. |
| `sample_representation` | string | `"native_pcm_integer"` | Preserves RFC 0009 `decode.sample_representation`; no integer-to-float conversion is part of exact equality. |
| `unsupported_profile` | `"unavailable"` | `"unavailable"` | Valid-but-unsupported profiles produce `unavailable/capability_unavailable`. |
| `max_probe_bytes` | non-negative integer | `65536` | Upper bound for the resolving-stage profile probe. |

### `AudioAlignmentOptions`

This amendment preserves RFC 0009's separate `AudioAlignmentOptions` object.
P7-A1 defaults remain:

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `mode` | string | `"sample_index"` | Only `sample_index` is enabled in P7-A1. |
| `fixed_offset_samples` | integer | `0` | Reserved until P7-A2. |
| `max_search_offset_samples` | non-negative integer | `0` | Reserved until P7-A2. |
| `max_drift_ppm` | finite JSON number | `0.0` | Reserved until P7-A2. |
| `ambiguity_margin_samples` | non-negative integer | `0` | Reserved until P7-A2. |

### `AudioWaveformOptions`

Key order and defaults:

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `enabled` | boolean | `false` | P7-A1 keeps waveform numeric relations disabled. |
| `sample_metric` | string | `"absolute_error"` | Reserved first waveform metric name. |
| `atol` | finite JSON number | `0.0` | Absolute tolerance when a later gate enables the relation. |
| `rtol` | finite JSON number | `0.0` | Relative tolerance when a later gate enables the relation. |
| `alignment_mode` | string | `"sample_index"` | Other modes require P7-A2. |

### `AudioSpectralOptions`

Key order and defaults:

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `enabled` | boolean | `false` | P7-A1 keeps spectral relations disabled. |
| `window_function` | string | `"hann"` | Reserved value; no P7-A1 computation. |
| `window_size` | positive integer | `2048` | Reserved value. |
| `hop_size` | positive integer | `512` | Reserved value and must be `<= window_size`. |
| `fft_size` | positive integer | `2048` | Reserved value and must be `>= window_size`. |
| `power_scale` | `"power"` or `"db"` | `"power"` | Reserved value. |

### `AudioPerceptualOptions`

Key order and defaults:

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `enabled` | boolean | `false` | P7-A1 keeps perceptual relations disabled. |
| `backend` | string or null | `null` | Non-null requires a later optional backend gate. |
| `model` | string or null | `null` | Non-null requires a later optional backend gate. |
| `score_name` | string or null | `null` | Non-null requires a later optional backend gate. |
| `license_acknowledged` | boolean | `false` | Does not authorize model use. |

## Encoded-byte changes and evaluation association

`encoded_bytes` remains an audio relation. It uses homogeneous `AudioChange`
entries with `operation="encoded_byte_update"`, `operation="encoded_byte_insert"`,
or `operation="encoded_byte_delete"`. Coordinates use absolute byte offsets in
the source snapshot, not decoded sample coordinates. Payloads carry digests;
the byte interval is represented by `AudioCoordinate.byte_start` and
`AudioCoordinate.byte_count`. Raw source bytes and bounded byte snippets are
never serialized unless a later artifact/source-disclosure RFC explicitly
authorizes them.

`AudioChange` preserves the accepted RFC 0009 shape and is a closed object with
key order:

```text
kind, relation, operation, before_coordinate, after_coordinate, channel,
before_digest, after_digest, before_fact, after_fact
```

Common invariants:

- `kind` is always `"audio_change"`;
- `relation` is one selected relation name;
- `before_coordinate` and `after_coordinate` are `AudioCoordinate` objects or
  `null`;
- detail truncation remains result/change-list metadata after total counts are
  known; it is not a per-change field.

This amendment extends the accepted operation set with
`encoded_byte_update`, `encoded_byte_insert`, and `encoded_byte_delete`. It also
extends `AudioCoordinate` for the `encoded_bytes` relation with `byte_start`
and `byte_count`. For encoded-byte changes, sample and time coordinate fields
are `null`.

Operation-specific fields:

| Operation | Required fields | Null fields |
| --- | --- | --- |
| `encoded_byte_update` | `before_coordinate.byte_start`, `before_coordinate.byte_count`, `after_coordinate.byte_start`, `after_coordinate.byte_count`, `before_digest`, `after_digest` | `before_fact`, `after_fact` |
| `encoded_byte_insert` | `after_coordinate.byte_start`, `after_coordinate.byte_count`, `after_digest` | `before_coordinate`, `before_digest`, `before_fact`, `after_fact` |
| `encoded_byte_delete` | `before_coordinate.byte_start`, `before_coordinate.byte_count`, `before_digest` | `after_coordinate`, `after_digest`, `before_fact`, `after_fact` |
| `sample_update` | `before_coordinate.sample_start`, `after_coordinate.sample_start`, `before_digest`, `after_digest` | `before_fact`, `after_fact` |
| `format_update`, `channel_update`, `timing_update`, `metadata_update` | `before_fact`, `after_fact` | digests unless the fact update also carries a bounded affected interval |

The `ChangeSet` remains homogeneous: it contains `AudioChange` values only for
audio results. Relation-level association is recorded in
`DiffResult.media_evaluations`: each `MediaViewEvaluation` lists the relation,
selector, `metric_names`, `change_count`, `policy_rule_ids`, and
`transformation_ids`. Changes never contain evaluation IDs, and metrics never
contain source evaluation IDs.

## P7-A1 WAV/PCM profile

The `p7_a1_wav_pcm` profile recognizes RIFF-family WAV containers with a
bounded resolving-stage probe. It classifies:

- `RIFF` + `WAVE` as the only decodable container form;
- `RIFX` + `WAVE` as valid RIFF-family WAV but unsupported for P7-A1;
- all other form identifiers as unsupported or corrupt according to whether the
  RIFF structure is otherwise valid.

The only decodable sample encodings are:

- classic `WAVE_FORMAT_PCM` (`wFormatTag=0x0001`) with `fmt ` chunk size 16,
  no extras, and container bits 8, 16, 24, or 32;
- `WAVE_FORMAT_EXTENSIBLE` (`wFormatTag=0xFFFE`) with `fmt ` chunk size 40,
  `cbSize=22`, PCM subformat GUID, valid bits from 1 through the container bit
  width, and container bits 8, 16, 24, or 32.

Eight-bit PCM is unsigned. Sixteen-, 24-, and 32-bit PCM are signed two's
complement little-endian integers. Twenty-four-bit PCM is packed as exactly
three bytes per sample. IEEE float, A-law, mu-law, ADPCM, extensible non-PCM
GUIDs, big-endian `RIFX` sample bytes, and compressed profiles are valid but
unsupported unless the header is malformed, in which case they are corrupt.
Classic PCM `fmt ` chunks with size 18 and `cbSize=0` are also valid but
unsupported in P7-A1.

`nBlockAlign`, `nAvgBytesPerSec`, channel count, sample rate, container bits,
valid bits, and channel mask must be internally consistent. Classic PCM has
unknown channel labels and ordered channels. WAVE_FORMAT_EXTENSIBLE with a
non-zero mask records labels from the mask; a zero mask records unknown labels
with ordered channels. Valid bits are recorded as a fact and do not silently
mask stored container bits. When WAVE_FORMAT_EXTENSIBLE has
`valid_bits < container_bits`, the profile-mandated unused padding bits must be
zero before exact comparison; non-zero padding bits are malformed input.

Exactly one `fmt ` chunk and at least one `data` chunk are required. Multiple
`data` chunks are valid but unsupported for P7-A1. A single `data` chunk may be
followed by well-formed non-audio chunks; their chunk IDs and byte sizes are
recorded as metadata facts but ignored for decoded samples. RIFF pad bytes for
odd-sized chunks are ignored. Non-zero trailing bytes outside a chunk, truncated
chunk headers, chunk sizes that exceed the file, or `data` before `fmt ` are
corrupt inputs.

## Resolving and decoding boundary

The bounded pre-resolution probe runs during `resolving` and reads only RIFF
headers, chunk headers, the first `fmt ` chunk, and the data-chunk inventory up
to `max_probe_bytes`.
Unsupported-but-valid profiles fail as:

```text
outcome=unavailable
stage=resolving
code=capability_unavailable
```

Malformed bytes that prevent opening or bounded snapshot reads fail at
`sourcing`. Malformed RIFF/WAV headers or chunk structure proven by the
resolving probe fail as `failed/resolving/decode_error`; this uses the existing
problem code at the stage that proved the malformed media. Malformed sample
payload discovered only after decode starts fails as `failed/decoding/decode_error`.
After decode starts, fallback to bytes, another backend, another profile, or a
perceptual relation is forbidden.

## Absence and unknown semantics

Absence is distinct from zero. Unknown is distinct from absence.

- Timestamps: PCM WAV without timestamp chunks records `timestamp_status="absent"`;
  unavailable or unparsed timestamp-bearing chunks record `"unknown"`.
- Encoder delay and padding: no delay/padding metadata records status
  `"absent"`; recognized but unsupported metadata records `"unknown"`; numeric
  values are sample counts.
- Channel layout: classic PCM and extensible zero masks record
  `channel_layout="unknown_ordered"`; extensible non-zero masks record
  `channel_layout="mask"` with the numeric mask and derived labels.

These facts participate in `audio.relation_facts_changed` and must not be
treated as backend-only metadata.

## Grouping, coordinates, digests, facts, and IDs

Changes are grouped by relation, stream index, operation, then coordinate.
Ordering is stable and ascending. `AudioCoordinate.sample_start` is zero-based
within the selected decoded stream after deinterleaving, and
`AudioCoordinate.sample_count` records the interval length before any alignment
other than `sample_index`. `AudioCoordinate.byte_start` and
`AudioCoordinate.byte_count` identify absolute byte intervals in the immutable
source snapshot.

Digest algorithm is SHA-256. Digest inputs are byte-exact and use this framing:

- `frame(tag, payload) = tag || uint32_be(len(payload)) || payload`;
- string values use tag `S` and UTF-8 payload;
- unsigned integers use tag `U` and canonical decimal ASCII payload;
- signed integers use tag `I` and canonical decimal ASCII payload;
- bytes use tag `B` and raw bytes;
- absent optional values use tag `N` with zero-length payload;
- lists use tag `L` and payload `uint32_be(item_count) || item_frame...`;
- name/value pairs are lists of exactly two items: `S(name)`, then the framed
  value.

Digest input is:

```text
S("platydiff.audio.digest.v1") ||
S(domain) ||
L([pair(name, value), ...])
```

Digest domains are:

- `audio.encoded_bytes.v1`: selected encoded byte ranges with source length and
  byte offsets;
- `audio.decoded_samples.v1`: stream index, sample rate, channel count,
  channel labels, sample format, signedness, endianness, container bits, valid
  bits, sample count, and per-channel sample bytes;
- `audio.fact_set.v1`: sorted fact names, units, value types, and values.

Normative vectors:

| Domain | Fields | SHA-256 |
| --- | --- | --- |
| `audio.encoded_bytes.v1` | `source_length=0`, `ranges=[]` | `e2361113e7d5fe9d32fcf689ea057c9950deee12f0272191f810df4ac5e3fae4` |
| `audio.encoded_bytes.v1` | `source_length=3`, `ranges=[(0,3,"abc")]` | `1127cf48354fc7b2e82205a4a37b41b2ab15f37f7504a569b4ecf96e9beb540d` |
| `audio.decoded_samples.v1` | 8 kHz mono signed 16-bit little-endian, one zero sample | `571b0712e3cab0285232543121c61d8d79217483f7800e22636464f8be6641a2` |
| `audio.fact_set.v1` | `facts=[]` | `a71820ac77a1695045cc22037a58821a619210cfaf2b8ea332a888b1ff276431` |

Vector field order is normative. The encoded vectors use pairs
`source_length`, then `ranges`; each range is `start`, `end`, `bytes`. The
decoded vector uses pairs `stream_index=0`, `sample_rate=8000`,
`channel_count=1`, `channel_labels=[N]`, `sample_format="pcm_s16le"`,
`signedness="signed"`, `endianness="little"`, `container_bits=16`,
`valid_bits=16`, `sample_count=1`, `samples=[0x0000]`. The fact vector uses
only `facts=[]`.

Required first-gate fact order is:

1. `container.form` (unit `tag`)
2. `codec.profile` (unit `name`)
3. `stream.index` (unit `index`)
4. `sample_rate` (unit `Hz`)
5. `channel_count` (unit `count`)
6. `channel_layout` (unit `name`)
7. `channel_mask` (unit `bitmask`, nullable)
8. `sample_format` (unit `name`)
9. `container_bits_per_sample` (unit `bits`)
10. `valid_bits_per_sample` (unit `bits`)
11. `sample_count_per_channel` (unit `samples`)
12. `duration_seconds` (unit `s`)
13. `timestamp_status` (unit `name`)
14. `encoder_delay_status` (unit `name`)
15. `encoder_padding_status` (unit `name`)

Stable identifiers are lowercase ASCII dotted names. The complete P7-A1 set is:

- comparator: `builtin.audio`
- P7-A1 algorithm: `audio.decoded_samples.exact.v1`
- encoded algorithm: `audio.encoded_bytes.exact.v1`
- transformation: `audio.decode.stdlib_wave_pcm.v1`
- resource profile: `audio.resource.p7_a1.v1`
- resource limits: `audio.resource.p7_a1.defaults.v1`
- policy rules: `audio.policy.exact_decoded_samples.v1`,
  `audio.policy.encoded_bytes.v1`, `audio.policy.no_hidden_transforms.v1`,
  `audio.policy.no_fallback_after_backend_start.v1`
- metrics: `audio.samples_changed`, `audio.bytes_changed`,
  `audio.samples_compared`, `audio.channels_compared`,
  `audio.relation_facts_changed`, `audio.duration_delta`,
  `audio.duration_delta_abs`

## Duration and timebase determinism

Exact duration is the rational `sample_count_per_channel / sample_rate`. Results
record `duration_numerator`, `duration_denominator`, and `duration_seconds`.
`duration_seconds` is the IEEE-754 binary64 nearest-even value of that rational,
computed without extended precision or fused operations and serialized as the
shortest decimal that round-trips to the same binary64 value. Infinite, NaN,
negative zero, locale-dependent, and platform-specific float strings are
invalid.

## CLI and SDK-v1 plugin rejection

P7-A1 reserves two equivalent CLI entry points:

```text
platydiff audio LEFT RIGHT
  --audio-relation decoded_samples
  --audio-backend stdlib_wave_pcm
  --audio-profile p7_a1_wav_pcm
  --audio-stream-index 0
  --format json

platydiff compare --type audio LEFT RIGHT
  --audio-relation decoded_samples
  --audio-backend stdlib_wave_pcm
  --audio-profile p7_a1_wav_pcm
  --audio-stream-index 0
  --format json
```

Both entry points construct the same `CompareSpec` and execute the same built-in
comparison path.
`--audio-stream-index` maps to accepted `stream.index`; P7-A1 accepts only `0`.
`encoded_bytes` is selected by `--audio-relation encoded_bytes`. Waveform,
spectral, perceptual, channel-selection, and non-`sample_index` alignment flags
remain rejected until their later gates.

Any attempt to route audio through SDK v1.1 plugin comparator flags is rejected
before plugin discovery or execution with `usage_error/plugin_sdk_modalities`.
The rejection must mention that SDK v1.1 supports text/binary only and that
media plugins require a future SDK-v2 contract.

## Problem detail keys

Problem detail objects are closed JSON objects with stable key order. Optional
keys are omitted when unavailable; they are not filled with `null` unless the
type below explicitly allows null.

| Key | Type |
| --- | --- |
| `stage` | one of the canonical lifecycle stage strings |
| `code` | stable problem code string |
| `message` | human-readable string |
| `media_kind` | `"audio"` |
| `relation` | selected relation string |
| `backend` | backend string |
| `profile` | profile string |
| `input_side` | `"before"`, `"after"`, or `"both"` |
| `byte_offset` | non-negative integer |
| `chunk_id` | four-byte ASCII chunk ID string |
| `field` | schema or header field name |
| `expected` | string, number, boolean, or array of those |
| `actual` | string, number, boolean, or array of those |
| `limit_name` | resource limit name |
| `limit_value` | non-negative integer |

Backend stderr, exception classes, host paths, source filenames, safe labels,
and arbitrary dictionaries must not enter problem details.

## Migration and compatibility impact

This accepted amendment updates RFC 0009 before P7-A1 code starts. It does not
change schema v1-v5 payloads, does not allocate video schema membership, does
not independently choose the audio successor number, and does not authorize
implementation. RFC acceptance itself does not start code; conditional human
authorization is recorded, and coordinator dispatch is still required after RFC
0010, P4-C1, P5-A1/schema-v4, and P6-C0/schema-v5 actually merge and RFC 0011
itself has merged. The eventual audio successor fixtures, using schema v6 only
after the schema predecessor merges, must cover omitted defaults, explicit
defaults, unknown-key rejection, encoded-byte changes, unsupported valid WAV
profiles, corrupt WAV inputs, absent versus unknown facts, duration
determinism, CLI rejection, and stable problem detail objects.

## Implementation test matrix

| Area | Required coverage |
| --- | --- |
| Wire shapes | omitted defaults, explicit defaults, key order, unknown keys, bad types, duplicate channel indices |
| WAV profile | RIFF PCM 8/16/24/32, unsigned 8-bit, extensible PCM, valid bits, masks, fmt extras, RIFX, multiple data chunks, padding, trailing chunks |
| Resolution boundary | valid unsupported profile at `resolving`, corrupt structure at sourcing/decode, probe byte limit |
| Relations | encoded bytes, decoded samples, relation fact changes, homogeneous `AudioChange` set |
| Facts | timestamps absent/unknown, encoder delay/padding absent/unknown, channel layout unknown/mask |
| Digests | encoded domain, decoded domain, fact-set domain, length framing, repeated-run determinism |
| Duration | exact rational, binary64 nearest-even, shortest round-trip JSON, no NaN/Inf/negative zero |
| CLI/SDK | first-gate flags, invalid combinations, SDK-v1 plugin rejection before discovery |
| Problems | key order, value types, omission rules, no backend stderr or host paths |

## Human approval record

Approved on 2026-09-10: P7A-AM1 through P7A-AM10 and P7A-W1 through P7A-W5.
Conditional human authorization for P7-A1 implementation is recorded, but RFC
acceptance itself does not start code. P7-A1 remains gated and requires
coordinator dispatch after RFC 0010, P4-C1, P5-A1/schema-v4, and
P6-C0/schema-v5 actually merge and RFC 0011 itself has merged.
