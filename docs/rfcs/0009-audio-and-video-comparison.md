# RFC 0009: Audio and Video Comparison

[Chinese documentation](0009-audio-and-video-comparison_zh.md)

- Status: Accepted
- Date: 2026-09-10
- Accepted: 2026-09-10
- Approved decisions: P7X1-P7X8, A1-A7; V1-V6 roadmap-only
- Owners: Platydiff maintainers
- Implementation owner: unassigned pending separate implementation authorization

## Summary and authorization boundary

This RFC accepts Phase 7 contracts for explicit audio comparison and accepts
the Phase 7 video direction as roadmap-only design. It does not authorize audio
or video implementation, dependency changes, FFmpeg or model installation, SDK
v2, automatic detection, UI work, artifact generation, plugin execution for new
media modalities, or any backend integration.

Audio and video are grouped as Phase 7 roadmap work because both are time-based
media, but they are not one implementation gate. Audio and video have separate
equivalence relations, IRs, codecs, timing models, metrics, artifacts, backend
risks, and dependency reviews. P7X1-P7X8 and A1-A7 are accepted decisions.
V1-V6 are accepted roadmap direction only: they do not freeze video
implementation, video backend selection, worker protocol, schema membership, or
public fixture shape. Each delivery gate below requires a later explicit human
authorization from updated `main`; accepting or merging this RFC text alone
does not start implementation.

All behavior remains explicit-only. A caller must choose `AudioCompareSpec` or
`VideoCompareSpec` directly. Existing `AutoCompareSpec` remains text/binary-only
until a successor to RFC 0003 defines media probing, ambiguity, pair selection,
and provenance.

## P7-S0 review-revision gate

P7-S0 is the completed documentation-only review gate introduced after PR #14.
It closed Phase 7 contract gaps before any implementation authorization. Its
outputs are this accepted RFC revision, the aligned architecture/index
references, and compatibility-fixture requirements for later gates. It does not
authorize code, dependency changes, backend installation, video workers, SDK v2,
auto detection, artifacts, UI, or implementation of the accepted audio schema
allocation.

P7-S0 evidence was collected from `origin/main` `fde2bd4`, where RFC 0007 and
RFC 0008 were still Proposed. Reviewers have since approved the Phase 5 and
Phase 6 acceptance revisions, and this Phase 7 branch is intended to merge only
after those acceptance PRs. Therefore the accepted design state is schema v4
for Phase 5 image, schema v5 for Phase 6 source/PDF, and schema v6 for Phase 7
audio. Public schema implementation and merge still wait for the accepted
predecessor revisions, their code, and their compatibility fixtures to land and
be revalidated.

## Evidence ledger

| Current evidence at `origin/main` `fde2bd4` | Phase 7 constraint |
| --- | --- |
| RFC 0001 separates failed/unavailable execution outcomes from completed `DiffResult` facts. | Decode, backend, timeout, resource, sandbox, model, and rendering failures must not become empty or synthetic media differences. |
| RFC 0002 requires every new modality to define spec, change, metric, artifact, equivalence relation, policy, failures, and gates before implementation. | This RFC records accepted contracts and gates only; no audio/video code may start from it. |
| RFC 0003 keeps automatic detection bounded and closed to text/binary. | Audio/video do not participate in auto detection; extension, MIME, magic bytes, stream probes, or codec probes must not change existing auto behavior. |
| RFC 0003 snapshot paths own bounded replay, hashes, mutation checks, and safe labels for path/bytes/text sources. | Media gates must revalidate snapshot behavior before depending on it for large or mutable media. |
| RFC 0004 makes renderers and UI consume validated outcomes without rereading sources or recomputing facts. | Media thumbnails, waveforms, heatmaps, and frame previews require explicit bounded artifact contracts; UI work remains unauthorized. |
| RFC 0005 implements SDK v1.1 for text/binary detector, comparator, and renderer handles only. | Audio/video plugins require an SDK-v2 successor RFC; SDK v1.1 cannot introduce media specs or built-in media change kinds. |
| RFC 0006 accepts schema v3 for structured data, but its implementation state must be revalidated when a later gate starts. | Audio/video schema decisions must migrate from implemented v1/v2 and accepted v3 without assuming unmerged P4-A1 behavior. |
| At `fde2bd4`, RFC 0007 proposed schema v4 for the first image slice, subject to an actual merged schema-v3 predecessor audit. | Phase 5 schema-v4 design allocation is now accepted, but P7-A1 must wait for the accepted revision, implementation, and fixtures to merge before relying on it. |
| At `fde2bd4`, RFC 0008 proposed source-code/PDF contracts and kept heavyweight backends, artifacts, auto detection, and SDK v2 separate. | Phase 6 schema-v5 design allocation is now accepted, but P7-A1 must wait for the accepted revision, implementation, and fixtures to merge before relying on it. |
| Runtime dependencies are currently empty; audio/video backends are architecture-level plans. | Codec, model, patent, export, and FFmpeg build/license impact must be reviewed before any dependency or subprocess path is added. |
| P4-A1 and Phase 5 implementation work may still be absent or divergent from `main`. | Treat that work as design evidence only; every code-dependent assumption below is a later revalidation gate. |

## Goals and non-goals

Phase 7 goals are:

- explicit audio specs that distinguish encoded bytes, decoded samples,
  waveform/numeric tolerance, spectral similarity, and perceptual similarity;
- explicit video specs that distinguish encoded bytes, stream/container
  structure, decoded frames, frame/pixel metrics, perceptual video, and audio
  track comparison;
- visible, deterministic decode, normalization, alignment, metric, aggregation,
  policy, artifact, backend, and provenance contracts;
- exact container, codec, channel, sample, timestamp, frame, color, HDR, and
  stream-selection semantics;
- no hidden resampling, remixing, loudness normalization, gain, resize, crop,
  frame-rate conversion, deinterlace, tone-map, color conversion, track
  dropping, or synchronization change;
- resource and security rules for corrupt, truncated, hostile, long-duration,
  high-rate, high-channel-count, high-resolution, high-frame-count, and
  multi-stream inputs;
- schema compatibility with implemented v1/v2, the actual P4 schema-v3
  predecessor, the accepted Phase 5 schema-v4 allocation, and the accepted
  Phase 6 schema-v5 allocation, subject to code and fixture revalidation at
  implementation start.

Phase 7 does not include:

- automatic audio/video detection or stream inference in `AutoCompareSpec`;
- codec installation, model download, FFmpeg bundling, dependency resolver, or
  backend package selection;
- fallback from one relation to another after a backend starts;
- lossy relation changes hidden behind a metric name;
- perceptual metrics by default;
- source mutation, media repair, transcoding, clipping, filtering, OCR, speech
  recognition, transcription, scene understanding, object recognition, or
  semantic video understanding;
- directory, URL, device, camera, microphone, stream, archive, or stdin input;
- audio/video plugin comparators through SDK v1.1;
- HTML, TUI, desktop, local-web, or review UI work;
- media artifact writing except behind the optional artifact gates below.

## Accepted decisions and roadmap direction

The following stable IDs are the accepted human decision list. P7X1-P7X8 and
A1-A7 are accepted as Phase 7 audio and cross-media contract decisions. V1-V6
are accepted roadmap direction only; they do not authorize or freeze video
implementation until a later backend/worker amendment accepts P7-V1 and assigns
the next global schema successor.

| ID | Accepted decision or roadmap direction | Alternative not selected |
| --- | --- | --- |
| P7X1 | Keep audio/video comparison explicit-only; existing auto remains text/binary. | Add media candidates to RFC 0003 without defining expensive probes and ambiguity. |
| P7X2 | Split audio and video into independently authorized gates. | Treat all time-based media as one implementation batch. |
| P7X3 | Use globally allocated schema v6 for audio only after auditing the actual P4 schema-v3 predecessor, accepted Phase 5 schema-v4 allocation, and accepted Phase 6 schema-v5 allocation; allocate video in the next global successor only after the P7-V1 backend/worker amendment is accepted. | Extend v1/v2 closed unions, reopen v3, reuse image v4 or source/PDF v5, put pending video into audio v6, or assume accepted but unimplemented predecessor details. |
| P7X4 | Reject audio/video plugin comparators under SDK v1.1; require SDK v2 for media modalities. | Let plugin installation introduce media specs or change kinds. |
| P7X5 | Keep RFC 0004 artifact/UI work separate; first comparison gates may produce no files. | Let decoding or rendering implicitly write previews, thumbnails, clips, heatmaps, or waveforms. |
| P7X6 | Forbid fallback that changes relation after backend execution begins. | On failure, silently retry as bytes, another codec/backend, a lower-fidelity decode, or a perceptual metric. |
| P7X7 | Treat perceptual metrics as separately reviewed optional/external gates. | Ship ViSQOL, VMAF, or model-based scores as default behavior. |
| P7X8 | Make every code-dependent assumption, including P4-A1, Phase 5, and RFC 0008 state, a revalidation gate. | Treat concurrent unmerged work as compatibility proof. |
| A1 | Audio exposes `encoded_bytes`, `decoded_samples`, `waveform_numeric`, `spectral`, and `perceptual` as distinct relations. | Collapse all audio results into one "same audio" bit. |
| A2 | Default first audio relation is `decoded_samples` for explicitly decoded PCM-capable inputs; `encoded_bytes` is selected separately. | Default to perceptual similarity or byte equality for all audio. |
| A3 | No resampling, channel remixing, gain, loudness normalization, silence trimming, clipping, dithering, filtering, or delay compensation is implicit. | Hide common audio preprocessing inside metrics. |
| A4 | Sample-rate, format, endianness, channel layout/order, duration, timestamps, encoder delay, and padding are comparison facts. | Treat them as backend metadata outside the result. |
| A5 | Audio alignment is explicit and deterministic; ambiguity or over-budget search fails rather than claiming an approximate match. | Use best-effort cross-correlation without recording uncertainty. |
| A6 | Waveform and spectral metrics must define units, direction, aggregation, empty-population behavior, and deterministic floating-point order. | Reuse informal DSP labels without stable metric contracts. |
| A7 | ViSQOL/PESQ/POLQA-style perceptual metrics require separate model/license/platform/patent review and optional gates. | Add perceptual scoring as a normal dependency. |
| V1 | Video exposes `encoded_bytes`, `stream_structure`, `decoded_frames`, `frame_numeric`, `perceptual_video`, and `audio_tracks` as separate views. | Let visual equality override stream, timestamp, or audio differences. |
| V2 | Stream selection, timebase, timestamps, duration, variable frame rate, frame reordering, keyframes, edit lists, and multi-stream behavior are explicit. | Let the backend choose default streams and timeline interpretation. |
| V3 | Pixel format, bit depth, range, transfer function, primaries, matrix coefficients, ICC/HDR metadata, chroma subsampling/siting, orientation, alpha, and interlacing are recorded facts. | Allow hidden color, geometry, or field-order conversions. |
| V4 | No resize, crop, frame-rate conversion, deinterlace, tone-map, color conversion, track dropping, or synchronization change is implicit. | Normalize video silently before metric calculation. |
| V5 | Spatial and temporal alignment use deterministic tie-breaking; missing/duplicate frames and offset/drift are first-class outcomes. | Merge alignment uncertainty into content differences. |
| V6 | VMAF-style metrics require optional/external gates with model/version/license and CPU/GPU reproducibility evidence. | Treat VMAF as an always-available numeric metric. |

## Schema and compatibility contract

Phase 7 accepts globally allocated schema v6 for audio only. The allocation
order is a stable human decision for the intended merge sequence: P4 structured
data uses schema v3, P5 image uses schema v4, P6 source/PDF uses schema v5, and
P7 audio uses schema v6. Design, backend, dependency, and fixture research may
proceed concurrently across phases, but this branch must merge after the P5 and
P6 acceptance PRs and public schema implementation must respect predecessor
order and compatibility fixtures. P7-A1 still requires a later implementation
gate to revalidate the actual merged v3/v4/v5 predecessor chain and record the
final schema number in the repository-wide schema ledger before adding code. It
may not reopen schema v3, consume schema v4 or v5, put pending video types into
audio v6, or allocate a competing successor in parallel with another modality.

The audio successor is an additive semantic successor to the actually merged
predecessor chain:

```python
CompareSpecV6 = CompareSpecV5 | AudioCompareSpec
ChangeV6 = ChangeV5 | AudioChange
```

If P4-A1 schema v3 is not implemented on `main`, if the implemented v3 differs
from RFC 0006, if Phase 5 schema v4 is absent or changes its allocation, or if
Phase 6 schema v5 is absent or changes its allocation, a Phase 7 audio
implementation gate stops and updates this RFC before code. Audio schema work
therefore depends on the real v3/v4/v5 readers, writers, upgraders, and
fixtures, not on accepted design text alone. In every case:

- existing built-in text, binary, and auto calls keep schema v1;
- existing `PluginHost` text/binary calls keep schema v2;
- merged Phase 4 structured-data calls keep the actual implemented schema v3;
- merged Phase 5 image calls keep schema v4;
- merged Phase 6 source/PDF calls keep schema v5;
- audio built-in specs produce schema v6, including validation, sourcing,
  resolution, decode, and backend failures;
- video built-in specs do not enter schema v6. Video receives the next global
  schema successor only after the P7-V1 backend/worker amendment is accepted;
- the audio v6 reader accepts v1/v2/v3/v4/v5/v6 payloads and
  dispatches by explicit schema version before inspecting spec or change kinds;
- v1/v2/v3/v4/v5-to-v6 upgraders preserve original facts and add only
  documented neutral defaults such as empty audio field collections;
- byte-stable v1/v2 fixtures, P4 schema-v3 fixtures, P5 schema-v4 fixtures, P6
  schema-v5 fixtures, and new audio round-trip fixtures remain in the
  compatibility corpus;
- each new audio fixture includes the expected JSON schema version, public
  spec/change names, metric names, ordering, omitted/null fields, and failure
  reason codes;
- no automatic downgrade exists for audio outcomes. A lossless helper may
  downgrade only a media-free result whose facts are representable in the target
  predecessor; audio specs, changes, facts, metrics, transformations, and
  artifacts are not dropped or summarized to fit an older schema. A future video
  successor must define its own downgrade rule;
- unknown built-in spec and change kinds remain invalid;
- unknown namespaced extension changes retain RFC 0001 behavior.

Phase 3 SDK v1.1 remains text/binary-only. Audio/video plugins require an
SDK-v2 successor RFC that defines media source views, lifecycle stages, backend
roles, sandboxing, artifact authority, compatibility receipts, and schema
migration. Existing auto detection remains text/binary-only unless a successor
detection RFC is separately accepted.

### Compatibility matrix

| Producer/path | Schema | Modalities | Plugin participation | Required behavior |
| --- | --- | --- | --- | --- |
| Existing `compare()` and default CLI | v1 | text, binary, auto to either | none | Existing byte-stable fixtures remain valid. |
| Existing explicit `PluginHost` | v2 | text, binary, auto to either | SDK v1.1 | Existing v2 fixtures and receipts remain valid. |
| Merged Phase 4 path | v3 | explicit json/yaml/table/array | none | Actual v3 models, migrations, and fixtures are the predecessor. |
| Accepted Phase 5 image path | v4 | explicit static PNG image | none until separately authorized | Media must not reuse v4 or require image implementation to change. |
| Accepted Phase 6 source/PDF path | v5 | source-code/PDF | none until separately authorized | Audio v6 implementation waits for merged v5 readers, writers, upgraders, and fixtures. |
| Accepted Phase 7 audio path | v6, dependent on v5 predecessor availability | explicit audio | none in first gates | Produces validated audio specs, changes, metrics, transformations, and failures after separate implementation authorization. |
| Accepted Phase 7 video roadmap path | next global successor after v6 | explicit video | none in first gates | Remains pending until backend and worker contracts are frozen in a later amendment; no video type is added to audio v6. |
| Existing auto on media-looking bytes | v1 | text or binary only | existing rules | Detection evidence and result do not change. |
| Future SDK v2 or media auto | unspecified | unspecified | unspecified | Requires successor RFCs. |

## Relation, view, and evaluation invariants

Audio `relations` and video `views` are normative sets encoded as tuples for
stable JSON. They are non-empty, contain no duplicates, reject unknown values,
and are normalized to canonical order in serialized output. The canonical audio
order is `encoded_bytes`, `decoded_samples`, `waveform_numeric`, `spectral`,
`perceptual`. The canonical video order is `encoded_bytes`,
`stream_structure`, `decoded_frames`, `frame_numeric`, `perceptual_video`,
`audio_tracks`. An empty collection, repeated value, or out-of-gate value is an
invalid spec, not a no-op.

Schema v6 adds a new `DiffResult.media_evaluations` field for audio relation
aggregation. It does not extend the existing `PolicyEvaluation` model.
Predecessor upgraders set `media_evaluations` to an empty tuple. Audio v6
fixtures must include at least one non-empty `media_evaluations` example and
one v1/v2/v3/v4/v5 upgrade example with the field defaulted.

```python
class MediaViewEvaluation:
    kind: Literal["media_view_evaluation"] = "media_view_evaluation"
    media_kind: Literal["audio", "video"]
    selector: str
    relation: Literal["equal", "different"]
    verdict: Literal["pass", "warn", "fail"]
    fidelity: Literal["full", "degraded"]
    completeness: Literal["complete", "truncated"]
    metric_names: tuple[str, ...] = ()
    policy_rule_ids: tuple[str, ...] = ()
    transformation_ids: tuple[str, ...] = ()
    warning_codes: tuple[str, ...] = ()
    change_count: int = 0
    failure_stage: Literal[
        "validating", "sourcing", "resolving", "decoding",
        "normalizing", "aligning", "comparing", "aggregating",
    ] | None = None
    failure_code: str | None = None
```

For schema v6, `media_kind` is always `audio` and `selector` is one of the
selected audio relations. Video `MediaViewEvaluation` records are not legal
until the later video schema successor explicitly reuses or revises this shape.
`metric_names`, `policy_rule_ids`, `transformation_ids`, and `warning_codes`
contain stable IDs already present elsewhere in the result/provenance; they are
deduplicated and sorted lexicographically. `change_count` is the untruncated
count for that relation. `failure_stage` and `failure_code` are both null for a
completed relation evaluation and both non-null only when a future schema allows
per-selector failure records inside a completed aggregate.

Metric records remain measurements only. `PolicyEvaluation` remains the RFC
0001 shape with `rule_id`, `verdict`, and optional metric/operator/threshold/
observed fields; it is not extended with media selector, fidelity,
completeness, transformation, or warning fields. Media evaluation records are
sorted by canonical relation order and never recompute or reinterpret metrics.

One completed `DiffResult` has exactly one overall `relation`, `verdict`,
`fidelity`, and `completeness`. The overall relation is equal only when every
selected evaluation is equal/pass. It is different/fail when any selected
evaluation is different/fail. Overall fidelity is the worst selected fidelity;
the first media gates permit only full fidelity. Overall completeness is
`truncated` when any selected evaluation is truncated after full counts and
overall relation are known; otherwise it is `complete`. `partial` remains
unauthorized for Phase 7 first gates.

Examples are part of the contract:

- If encoded bytes differ but decoded samples are identical, selecting only
  `decoded_samples` yields overall equal/pass, while selecting both
  `encoded_bytes` and `decoded_samples` yields one different encoded evaluation
  and an overall different/fail result.
- If decoded video frames are identical but a selected audio-track evaluation
  differs, the `decoded_frames` evaluation passes, the `audio_tracks`
  evaluation fails, and the overall video result is different/fail.
- If the selected audio-track backend is unavailable or fails before producing
  its evaluation, the outer outcome is `unavailable` or `failed` at the
  recorded lifecycle stage rather than a completed video equality result.

## Audio comparison contract

### Public intent

The accepted first public shape is a stable schema family, but P7-A1 exposes
only the exact relations listed as first-gate values. Later gates may activate
the retained fields only after their own review.

```python
class AudioCompareSpec:
    kind: Literal["audio"] = "audio"
    relations: tuple[
        Literal["encoded_bytes", "decoded_samples"],
        ...
    ] = ("decoded_samples",)
    stream: AudioStreamSelection = AudioStreamSelection()
    decode: AudioDecodeOptions = AudioDecodeOptions()
    alignment: AudioAlignmentOptions = AudioAlignmentOptions()
    waveform: AudioWaveformOptions = AudioWaveformOptions()
    spectral: AudioSpectralOptions = AudioSpectralOptions()
    perceptual: AudioPerceptualOptions = AudioPerceptualOptions()
    artifact_policy: Literal["none"] = "none"
    limits: AudioResourceLimits = AudioResourceLimits()
```

P7-A1 public options are frozen to these JSON names and invariants:

| Field | First-gate invariant |
| --- | --- |
| `kind` | Required string, exactly `audio`. |
| `relations` | Required or defaulted non-empty tuple, canonicalized to the first-gate subset `encoded_bytes` and `decoded_samples`; duplicates and later-gate values are invalid. |
| `stream.index` | `null` for the default audio stream or a zero-based integer selected explicitly; no backend default may silently pick another stream. |
| `decode.backend` | Required or defaulted string, exactly `stdlib_wave_pcm` for P7-A1. |
| `decode.sample_representation` | Required or defaulted string, exactly `native_pcm_integer`; no integer-to-float conversion is part of exact decoded equality. |
| `alignment.mode` | `sample_index` in P7-A1; `fixed_offset` is defined below but not enabled until P7-A2. |
| `artifact_policy` | Always `none` before P7-M1; `record_refs` is invalid before the artifact gate. |
| `limits.*` | Non-negative JSON integers within the safe integer range; `null`, booleans, negative values, and non-finite numbers are invalid. |

`PathSource` and `BytesSource` are the first source kinds. `TextSource` is
unsupported for audio unless a later gate defines an explicit byte encoding
relation; an unsupported source returns `failed/source_type_unsupported`.

Relation meanings are independent:

- `encoded_bytes` reuses exact binary semantics and says nothing about decoded
  signal equivalence;
- `decoded_samples` compares the selected decoded PCM stream exactly after an
  explicit sample representation is chosen;
- `waveform_numeric` is reserved for P7-A2; it compares aligned samples using
  explicit numeric tolerance and reports sample-domain error metrics;
- `spectral` is reserved for P7-A2; it compares explicitly windowed spectra and
  cannot imply sample equality;
- `perceptual` is reserved for P7-A3; it uses a named optional perceptual
  backend and cannot override exact or spectral differences.

### Decoded sample equality closure

For `decoded_samples`, equality requires both sample values and their
comparison-significant interpretation facts to match. The relation is different
if any of these facts differ, even when decoded sample value arrays are
byte-for-byte identical:

- selected stream index and stream identity facts;
- sample rate;
- sample format, bit depth, endianness, signedness, and integer scale policy;
- channel count, channel layout, channel labels, and channel order;
- decoded sample count per selected channel;
- duration ticks, timebase, and derived duration seconds;
- selected packet/frame timestamp facts;
- gapless encoder delay and padding facts when present or selected.

`audio.samples_changed` counts unequal selected sample positions only.
Interpretation-fact differences are counted separately in
`audio.relation_facts_changed` and represented as `format_update`,
`channel_update`, `timing_update`, or `metadata_update` changes. Sample count or
duration mismatches produce `sample_insert`/`sample_delete` observations for
the unmatched interval and a `timing_update` fact change when timing facts also
differ. This prevents a result from reporting `decoded_samples` equal when the
same sample bytes have a different sample rate, channel interpretation,
duration, timestamp model, delay, or padding.

### Decode and IR facts

The private `AudioIR` must carry at least:

```text
container_format
codec_id and codec_profile
stream_index
sample_rate_hz
sample_format: pcm_s8 | pcm_s16 | pcm_s24 | pcm_s32 | pcm_f32 | pcm_f64 | ...
endianness
integer_scale_policy
float_special_value_policy
channel_count
channel_layout and channel_order
sample_count per channel
duration_ticks and timebase
packet and frame timestamps where available
gapless_encoder_delay_samples
gapless_padding_samples
metadata fields selected by spec
```

PCM integer-to-float conversion, float-to-float widening, endian conversion,
packed-to-planar conversion, and signedness conversion are transformations.
They are legal only when the spec requests them or the relation requires a
canonical representation, and every executed transformation is recorded.
Floating-point NaN, infinity, signed zero, denormal handling, clipping, and
out-of-range decoded values must be specified before comparison starts.

Container metadata, tags, codec side data, channel labels, delay/padding, and
timestamps are comparison facts when selected; they are not hidden backend
notes. Gapless delay and padding may be either compared as metadata or applied
as an explicit alignment transform, never both silently.

### Audio alignment and changes

Default alignment is by decoded sample index and channel order with zero offset.
Optional timestamp alignment, fixed-offset alignment, and bounded
cross-correlation search require explicit spec fields:

```python
class AudioAlignmentOptions:
    mode: Literal["sample_index", "timestamp", "fixed_offset", "correlation"] = "sample_index"
    fixed_offset_samples: int = 0
    max_search_offset_samples: int = 0
    max_drift_ppm: float = 0.0
    ambiguity_margin_samples: int = 0
```

`fixed_offset_samples` is signed samples at the selected stream sample rate;
positive values mean the after stream starts later than before and is shifted
left for comparison. `max_search_offset_samples` is an absolute sample budget
for correlation search. `max_drift_ppm` is parts per million of sample-clock
drift over the compared interval. `ambiguity_margin_samples` is an integer
sample-distance margin between the best and second-best alignment candidates;
values within the margin are ambiguous.

Offset and drift compensation are transformations with recorded parameters,
observed estimates, tie-break order, and confidence or ambiguity facts.
Timeline candidates are ordered by exact timestamp match, lower absolute
offset, lower absolute drift, lower before coordinate, then lower after
coordinate. Correlation candidates are ordered by higher deterministic score,
lower absolute offset, lower absolute drift, lower before coordinate, then lower
after coordinate. If two alignments are indistinguishable under the configured
margin, if drift exceeds policy, or if the search budget is exhausted, the
outcome is `failed/compare_resource_limit` for budget exhaustion or
`failed/decode_error` for unusable decoded timing facts, not an approximate
completed equality claim. A media-specific `alignment_failed` problem code
requires a later RFC 0001 registry update before use.

The accepted built-in audio change set is:

```python
class AudioChange:
    kind: Literal["audio_change"]
    relation: Literal[
        "encoded_bytes", "decoded_samples", "waveform_numeric",
        "spectral", "perceptual"
    ]
    operation: Literal[
        "stream_add", "stream_remove", "metadata_update",
        "format_update", "channel_update", "timing_update",
        "sample_update", "sample_insert", "sample_delete",
        "spectral_update", "alignment_shift", "perceptual_update"
    ]
    before_coordinate: AudioCoordinate | None
    after_coordinate: AudioCoordinate | None
    channel: str | int | None
    before_digest: str | None
    after_digest: str | None
    before_fact: AudioFact | None
    after_fact: AudioFact | None
```

Audio coordinates use stream index, zero-based channel index or stable channel
label, sample interval, timestamp interval, and spectral bin/time cell where
applicable. Changes are observations, not patches. Detail truncation occurs
only after the relation, metrics, and total change count are known.

The first-gate `AudioCoordinate` wire shape is fixed to JSON object fields
`stream_index`, `channel_index`, `channel_label`, `sample_start`,
`sample_count`, `time_start_seconds`, and `time_duration_seconds`. Stream and
channel indexes are zero-based integers. `channel_label` is `null` unless the
selected source has a stable label. Sample intervals are half-open and
non-negative. Time fields are decimal seconds encoded as finite JSON numbers
only when timestamp facts are available; otherwise they are `null`.

The first-gate `AudioFact` wire shape is limited to JSON object fields
`name`, `value`, `unit`, `stream_index`, and `coordinate`. `value` is a string,
integer, finite number, boolean, or `null`; arrays and nested objects require a
later schema revision. `AudioChange` records are sorted by relation, operation,
before coordinate, after coordinate, then digest. `sample_update` requires both
coordinates and both digests. `sample_insert` requires only an after coordinate;
`sample_delete` requires only a before coordinate. `format_update`,
`channel_update`, `timing_update`, and `metadata_update` require facts and have
null sample coordinates unless they also describe a bounded affected interval.
Digests are lowercase algorithm-prefixed hex strings or `null` only when the
operation has no byte/sample payload.

### Audio metrics and policy

The accepted first audio metric registry is:

| Metric name | Meaning | Unit | Direction | Aggregation | Empty population |
| --- | --- | --- | --- | --- | --- |
| `audio.samples_compared` | aligned sample pairs across selected channels | `samples` | `neutral` | `count` | zero |
| `audio.samples_changed` | unequal or tolerance-failing sample pairs | `samples` | `lower_is_better` | `count` | zero |
| `audio.channels_compared` | selected channels compared | `channels` | `neutral` | `count` | zero |
| `audio.duration_delta` | after duration minus before duration after selected alignment | `seconds` | `neutral` | `difference` | zero |
| `audio.duration_delta_abs` | absolute duration difference after selected alignment | `seconds` | `lower_is_better` | `absolute_difference` | zero |
| `audio.relation_facts_changed` | comparison-significant non-sample facts that differ for the selected relation | `facts` | `lower_is_better` | `count` | zero |
| `audio.sample_peak_error` | maximum absolute sample error after scaling policy | `amplitude_full_scale` | `lower_is_better` | `maximum` | metric omitted |
| `audio.sample_rms_error` | root mean square sample error | `amplitude_full_scale` | `lower_is_better` | `rms` | metric omitted |
| `audio.snr` | signal-to-noise ratio using before as reference | `db` | `higher_is_better` | `ratio_db` | positive infinity for zero error, omitted for zero reference energy |
| `audio.spectral_peak_error` | maximum spectral magnitude error | `db` | `lower_is_better` | `maximum` | metric omitted |
| `audio.spectral_rms_error` | RMS spectral magnitude error | `db` | `lower_is_better` | `rms` | metric omitted |
| `audio.perceptual_score` | named backend perceptual similarity score | backend-defined stable unit | backend-defined | backend-defined | metric omitted |

Metrics are facts, not verdicts. Each metric record uses the existing RFC 0001
shape: stable name, numeric value, unit, direction, and optional aggregation.
Metrics do not carry source evaluation IDs; `MediaViewEvaluation.metric_names`
associates metrics with a media relation. Policy evaluations contain
thresholds, tolerance formulas, inclusive/exclusive boundary rules, and
pass/fail verdicts. Absolute-duration thresholds use `audio.duration_delta_abs`
with a normal `le` policy operator. A renderer must not infer pass/fail directly
from metric values.

Waveform tolerance is comparison intent and determines relation for
`waveform_numeric`; it is not merely a verdict threshold. Count metrics are
integer-valued and stable. Floating metrics define accumulation order, rounding,
NaN/Inf behavior, reference signal, scale, and dtype before release. Spectral
metrics must define window function, window length, hop length, FFT length,
padding, magnitude/log conversion, bin alignment, and aggregation. Default
policy for each selected non-perceptual relation is equality or changed-count
zero; no default audio rule yields `warn`.

Perceptual metrics such as ViSQOL and comparable systems are not core
dependencies. A gate that selects one must record model identity, version,
license, patent considerations, platform support, training/test-data
redistribution constraints, deterministic settings, CPU/GPU variance, and
whether the score is applicable to speech, music, bandwidth-limited audio, or
other domains.

### Audio resources and failures

```python
class AudioResourceLimits:
    max_input_bytes: int = 256 * 1024 * 1024
    max_streams: int = 32
    max_duration_seconds: int = 3600
    max_sample_rate_hz: int = 384000
    max_channels: int = 64
    max_decoded_samples_per_channel: int = 50_000_000
    max_total_decoded_bytes: int = 512 * 1024 * 1024
    max_resident_buffer_bytes: int = 128 * 1024 * 1024
    max_packets: int = 1_000_000
    max_metadata_entries: int = 10_000
    max_metadata_value_bytes: int = 1 * 1024 * 1024
    max_spectral_cells: int = 20_000_000
    max_backend_seconds: int = 30
    max_stdout_stderr_bytes: int = 4 * 1024 * 1024
    max_temp_bytes: int = 512 * 1024 * 1024
    max_materialized_bytes: int = 512 * 1024 * 1024
    max_compare_work: int = 10_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024
```

For P7-A1 with `stdlib_wave_pcm`, these are accepted normative default values.
Implementation still needs a benchmark gate to prove they are deterministic,
bounded, and practical, but acceptance of P7-S0/audio decisions does not defer
the default values themselves. Limit checks happen before allocation, decode,
packet expansion, metadata materialization, comparison work, or temp-file
writes. A limit value of `0` means no budget for that resource: zero decoded
bytes accepts only inputs whose selected relation needs no decoded bytes; zero
duration accepts only zero-duration decoded streams; zero packets rejects any
stream that would read a packet; zero change items still computes the overall
relation and total count but emits a truncated empty change list.
`max_resident_buffer_bytes` caps live decoded/sample buffers, not just total
output bytes. `max_materialized_bytes` caps host-owned snapshots and temporary
materializations passed to a backend. All counters are monotonic and checked at
chunk boundaries before reserving the next buffer.

Corrupt, truncated, unsupported-codec, hostile-container, over-duration,
huge-sample-rate, huge-channel-count, decode-bomb, infinite stream,
packet-storm, metadata-bomb, backend-hang, backend-crash, and over-output cases
are required tests. Backend unavailability is
`unavailable/backend_unavailable`; unsupported codec or profile is
`unavailable/capability_unavailable` unless a selected decoder starts and then
fails, in which case the observed failure is `failed`.

## Video comparison contract

### Public intent

The accepted video roadmap shape remains documentation-only and is not part of
schema v6. P7-S0 narrowed the candidate first public fields, but P7-V1 is not
implementation-authorized until a later backend/worker amendment freezes the
video backend, worker protocol, compatibility fixtures, and next global schema
successor.

```python
class VideoCompareSpec:
    kind: Literal["video"] = "video"
    views: tuple[
        Literal[
            "encoded_bytes",
            "stream_structure",
            "decoded_frames",
            "frame_numeric",
            "perceptual_video",
            "audio_tracks",
        ],
        ...
    ] = ("decoded_frames",)
    streams: VideoStreamSelection = VideoStreamSelection()
    decode: VideoDecodeOptions = VideoDecodeOptions()
    timeline: VideoTimelineOptions = VideoTimelineOptions()
    spatial: VideoSpatialOptions = VideoSpatialOptions()
    metrics: VideoMetricOptions = VideoMetricOptions()
    audio: AudioCompareSpec | None = None
    artifact_policy: Literal["none"] = "none"
    limits: VideoResourceLimits = VideoResourceLimits()
```

Candidate P7-V1 public options are frozen to these JSON names and invariants if
a later gate authorizes implementation:

| Field | First-gate invariant |
| --- | --- |
| `kind` | Required string, exactly `video`. |
| `views` | Required or defaulted non-empty tuple, canonicalized to the P7-V1 subset `encoded_bytes`, `stream_structure`, and `decoded_frames` only after a backend is frozen; until then every video view is documentation-only. Duplicates and later-gate values are invalid. |
| `streams.video_index` | `null` for the explicitly defined default video stream or a zero-based integer. Backend default stream choice is not sufficient. |
| `streams.audio_indexes` | Tuple of zero-based integers used only when `audio_tracks` is selected; empty means no audio-track comparison, not all tracks. |
| `decode.backend` | No default backend is authorized by this RFC revision. P7-V1 must name a reviewed backend and version profile before code. |
| `timeline.mode` | `presentation_timestamp` for exact decoded frames unless a later gate authorizes fixed-offset or fingerprint alignment. |
| `spatial.mode` | `exact_geometry`; resize, crop, rotate, deinterlace, tone-map, and color conversion are invalid first-gate transforms. |
| `artifact_policy` | Always `none` before P7-M1; `record_refs` is invalid before the artifact gate. |
| `limits.*` | Non-negative JSON integers within the safe integer range; `null`, booleans, negative values, and non-finite numbers are invalid. |

`encoded_bytes` reuses exact binary semantics. `stream_structure` compares
container and stream layout, codec parameters, packet indexes, timebases,
metadata, edit lists, keyframes, attachments, chapters, and selected side data.
`decoded_frames` compares the explicit decoded frame sequence and timestamps
only after a backend is frozen. `frame_numeric` is reserved for P7-V2 and
permits explicit pixel tolerances. `perceptual_video` is reserved for P7-V3 as
an optional model/backend gate. `audio_tracks` is reserved for P7-V2; once
authorized, it delegates to the audio contract with the video timeline
association recorded and never silently drops tracks.

### Decode, timeline, color, and IR facts

The private `VideoIR` must carry at least:

```text
container_format
stream list and selected stream indexes
codec_id, codec_profile, level, extradata digest
timebase per stream
packet timestamps, decode timestamps, presentation timestamps
duration, start time, edit lists, variable-frame-rate facts
frame count where known
frame reordering and keyframe facts
pixel_format, bit_depth, endianness
range: full | limited | unspecified
transfer_function, primaries, matrix_coefficients
ICC profile and HDR metadata digests
chroma_subsampling and chroma_siting
width, height, sample aspect ratio, display aspect ratio
orientation and rotation metadata
alpha mode
interlacing and field order
audio/subtitle/attachment stream inventory
```

Pixel format, bit depth, range, transfer function, primaries, matrix
coefficients, ICC/HDR metadata, chroma subsampling/siting, orientation,
rotation, alpha, and interlacing are comparison facts. Any conversion among
them is a named transformation and must be explicit, deterministic, and
recorded. Backend defaults are not sufficient provenance.

Variable frame rate, edit lists, start offsets, B-frame reordering, missing
timestamps, duplicate timestamps, non-monotonic timestamps, keyframe placement,
multi-angle or multi-stream choices, and audio/video synchronization are
timeline facts. A gate must define whether they are compared directly, used for
alignment, or unsupported.

### Video alignment and changes

Default temporal alignment is by selected presentation timestamp and stream
index. Fixed-offset and bounded feature/fingerprint alignment are optional
explicit policies. Spatial alignment defaults to identical decoded frame
geometry and pixel coordinate. No crop, resize, rotation, deinterlace,
tone-map, color conversion, chroma resampling, frame-rate conversion, track
dropping, or sync shift is implicit.

Video `fixed_offset_ticks` is signed ticks in the selected stream timebase;
positive values mean the after timeline starts later than before and is shifted
earlier for comparison. Duration deltas are reported in seconds and original
timebase ticks. Timeline matching orders candidates by exact presentation
timestamp, lower absolute offset ticks, lower absolute drift ppm, lower stream
index, lower before frame ordinal, then lower after frame ordinal. Feature or
fingerprint matching must define score units and an ambiguity margin in the same
score units; ties fall back to the timeline order above.

Missing frames, duplicate frames, duplicate timestamps, dropped frames, inserted
frames, stream additions/removals, and drift are first-class observations or
failures. Deterministic tie-breaking must be specified for any frame matching
policy. Ambiguity, unsupported timestamp structure, or over-budget alignment is
`failed/compare_resource_limit` for budget exhaustion or `failed/decode_error`
for unusable decoded timing facts, not a hidden content difference. A
media-specific `alignment_failed` problem code requires a later RFC 0001
registry update before use.

The accepted roadmap built-in video change set is:

```python
class VideoChange:
    kind: Literal["video_change"]
    view: Literal[
        "encoded_bytes", "stream_structure", "decoded_frames",
        "frame_numeric", "perceptual_video", "audio_tracks"
    ]
    operation: Literal[
        "stream_add", "stream_remove", "stream_update",
        "frame_insert", "frame_delete", "frame_update",
        "frame_duplicate", "timestamp_update", "region_update",
        "alignment_shift", "perceptual_update", "audio_track_update"
    ]
    before_coordinate: VideoCoordinate | None
    after_coordinate: VideoCoordinate | None
    before_digest: str | None
    after_digest: str | None
    before_fact: VideoFact | None
    after_fact: VideoFact | None
```

Coordinates include stream index, frame ordinal, presentation timestamp,
timebase, pixel rectangle, plane/component, and audio-track coordinate where
applicable. Region changes are observations, not patch data or rendered
artifacts.

The candidate `VideoCoordinate` wire shape is fixed to JSON object fields
`stream_index`, `frame_index`, `pts`, `timebase_num`, `timebase_den`,
`time_seconds`, `x`, `y`, `width`, `height`, `plane`, and `audio_coordinate`.
Frame indexes are zero-based. Pixel rectangles are half-open, non-negative, and
valid only when a decoded-frame or frame-numeric view is selected. `pts` is an
integer timestamp in the selected stream timebase. `time_seconds` is a finite
number derived from `pts` and included only as display aid; equality uses ticks.
`audio_coordinate` is `null` unless the `audio_tracks` view records a delegated
audio observation.

The candidate `VideoFact` wire shape is limited to JSON object fields `name`,
`value`, `unit`, `stream_index`, and `coordinate`. `value` is a string, integer,
finite number, boolean, or `null`; arrays and nested objects require a later
schema revision. `VideoChange` records are sorted by view, operation, before
coordinate, after coordinate, then digest. Frame and region updates require both
coordinates and both digests. Insert/delete operations require only the present
side coordinate. Stream and metadata updates require facts and may have null
frame coordinates.

### Video metrics and policy

The accepted roadmap video metric registry is:

| Metric name | Meaning | Unit | Direction | Aggregation | Empty population |
| --- | --- | --- | --- | --- | --- |
| `video.frames_compared` | aligned frame pairs evaluated | `frames` | `neutral` | `count` | zero |
| `video.frames_changed` | frames with at least one failing pixel/structure observation | `frames` | `lower_is_better` | `count` | zero |
| `video.missing_frames` | before-only frame observations | `frames` | `lower_is_better` | `count` | zero |
| `video.duplicate_frames` | duplicate frame observations under selected timeline policy | `frames` | `lower_is_better` | `count` | zero |
| `video.changed_pixels` | changed pixels before region grouping | `pixels` | `lower_is_better` | `sum` | zero |
| `video.pixel_peak_error` | maximum component error after explicit scaling policy | `component_units` | `lower_is_better` | `maximum` | metric omitted |
| `video.pixel_rms_error` | RMS component error | `component_units` | `lower_is_better` | `rms` | metric omitted |
| `video.psnr` | peak signal-to-noise ratio | `db` | `higher_is_better` | `minimum` | positive infinity for zero error, omitted for no compared pixels |
| `video.ssim` | explicitly configured SSIM-style score | `ratio` | `higher_is_better` | `minimum` or `mean` as specified | metric omitted |
| `video.vmaf` | named VMAF model score | `score` | `higher_is_better` | model-defined | metric omitted |
| `video.audio_tracks_changed` | selected audio tracks whose delegated relation is different or whose timeline association facts changed | `tracks` | `lower_is_better` | `count` | zero |

Metrics are facts and never define policy by themselves. Per-view evaluations
reference metrics and contain the threshold, tolerance, inclusive boundary,
verdict, fidelity, and completeness. `video.audio_tracks_changed` counts
observed delegated relation differences or association fact changes; it does
not depend on pass/fail policy, duplicate audio metrics, or reinterpret audio
evaluation verdicts.

PSNR must define peak value, component selection, averaging, bit depth, range,
and color representation. SSIM-style metrics must define windowing, color plane,
boundary handling, constants, aggregation, and floating-point determinism. VMAF
requires model identity, version, license, feature extractor versions,
CPU/GPU/reproducibility evidence, platform support, and redistribution review.
Default policy for selected non-perceptual views is zero changed items or zero
changed pixels/frames as appropriate. No default video policy yields `warn`.

### Video resources and failures

```python
class VideoResourceLimits:
    max_input_bytes: int = 2 * 1024 * 1024 * 1024
    max_streams: int = 64
    max_duration_seconds: int = 3600
    max_frames: int = 250_000
    max_width: int = 8192
    max_height: int = 8192
    max_pixels_per_frame: int = 100_000_000
    max_decoded_frame_bytes: int = 512 * 1024 * 1024
    max_total_decoded_bytes: int = 4 * 1024 * 1024 * 1024
    max_resident_buffer_bytes: int = 512 * 1024 * 1024
    max_packets: int = 2_000_000
    max_metadata_entries: int = 25_000
    max_metadata_value_bytes: int = 1 * 1024 * 1024
    max_backend_seconds: int = 60
    max_stdout_stderr_bytes: int = 4 * 1024 * 1024
    max_temp_bytes: int = 2 * 1024 * 1024 * 1024
    max_materialized_bytes: int = 2 * 1024 * 1024 * 1024
    max_compare_work: int = 20_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024
```

Video resource values are non-normative planning placeholders until a P7-V1
backend amendment freezes the backend and worker profile. Accepting P7-S0 or
the audio defaults does not freeze these video defaults. Once amended, limit
checks happen before allocation, decode, packet expansion, metadata
materialization, frame buffering, comparison work, or temp-file writes. A limit
value of `0` means no budget for that resource: zero frames rejects any
decoded-frame view with a frame, zero decoded bytes permits only views that need
no decoded frames, zero packets rejects packet reads, and zero change items
still computes the overall relation and total count but emits a truncated empty
change list.
`max_resident_buffer_bytes` caps live decoded frame/audio buffers;
`max_total_decoded_bytes` caps cumulative decoded media; `max_materialized_bytes`
caps host-owned snapshots and temporary materializations. Counters are
monotonic and checked at chunk/frame boundaries before reserving the next
buffer.

Adversarial tests include malformed containers, unsupported codecs, resolution
bombs, huge frame counts, long durations, many streams, packet storms, metadata
bombs, decompression bombs, infinite or non-terminating streams, corrupt frames,
timestamp wraparound, backend hangs, backend crashes, excessive stdout/stderr,
and temp-output explosions.

## Backends and execution boundary

The first audio backend is fixed to Python 3.12 standard-library WAV parsing for
uncompressed PCM WAV only, exposed as `stdlib_wave_pcm`. It uses host-owned
snapshot bytes or materialized files, records the `wave` module capability
profile, and rejects compressed codecs or unsupported WAV variants as
`unavailable/capability_unavailable`. This RFC selects no video backend. P7-V1
remains pending and does not authorize video workers until a later review
freezes the backend, worker isolation, materialization format, and conformance
profile.

Other standard-library capability is limited to exact encoded-byte comparison.
Optional Python libraries may handle metadata or numeric arrays only after
dependency, license, size, platform, native-code, and security review. External
programs such as `ffprobe`, `ffmpeg`, or model runners are separate backend
roles and require their own conformance profile.

All backend roles consume only host-owned immutable snapshots or
materializations. They must not receive the caller's original path when a
snapshot is available, and they must not dereference URLs, playlists, manifests,
devices, symlinks that escape the snapshot root, or paths produced by media
metadata. Protocol allowlists are explicit; the first gates allow only local
host file descriptors or `file` materializations. Network protocols, remote
resources, camera/microphone capture, hardware devices, and writeable output
paths outside the host temp/artifact root are forbidden.

Every external program invocation must use:

- argument arrays with `shell=False`;
- no interpolation of untrusted input into command strings;
- close-on-exec descriptors and bounded temporary directories;
- explicit timeout, terminate/kill escalation, child-process reaping, and temp
  cleanup on every exit path;
- bounded stdout, stderr, decoded frames, packet metadata, and temp-file bytes;
- exit-code validation and structured stderr redaction;
- no inherited untrusted environment except an allowlist;
- no network, remote resource loading, device capture, or writes outside the
  host temp/artifact root;
- path redaction and safe labels in diagnostics;
- backend name, version, build configuration, enabled libraries/codecs, model
  identities, platform, and deterministic settings in provenance.

Backend availability is tested before selection when possible and recorded as
available/unavailable with stable reason codes. A missing unpinned backend may
be skipped before execution. A pinned or only compatible missing backend yields
`unavailable/backend_unavailable`. Once a selected backend starts decoding or
comparing, failures are `failed` at the observed stage and do not fall back to
another backend or relation. Degraded fidelity is forbidden unless a future
spec explicitly permits it and records the lost information and policy impact.

### Lifecycle stages and failures

| Stage | Responsibility | Failure or unavailable reason |
| --- | --- | --- |
| `validating` | Validate schema version, relation/view set, public option names, nullability, ordering, and limit values. | `failed/invalid_spec` |
| `sourcing` | Acquire immutable host-owned source bytes, labels, hashes, mutation checks, and bounded materializations. | `failed/source_not_found`, `failed/source_type_unsupported`, `failed/source_changed`, `failed/resource_limit_exceeded`, `failed/io_error` |
| `resolving` | Select a backend matching the requested relation/view and frozen capability profile. | `unavailable/backend_unavailable`, `unavailable/capability_unavailable` |
| `decoding` | Parse container packets, metadata, samples, frames, timestamps, side data, and backend decode output within limits. | `failed/decode_error`, `failed/resource_limit_exceeded`, `failed/io_error` |
| `normalizing` | Build the explicit IR and record every requested representation transform. Unsupported requested transforms are rejected earlier during `validating`. | `failed/decode_error`, `failed/resource_limit_exceeded`, `failed/internal_error` |
| `aligning` | Match samples, timestamps, frames, streams, or delegated audio tracks deterministically. | `failed/compare_resource_limit`, `failed/decode_error` |
| `comparing` | Produce policy-neutral metrics and change observations without altering policy semantics. | `failed/compare_resource_limit`, `failed/io_error`, `failed/internal_error` |
| `aggregating` | Build per-relation/view evaluations and the single overall result. | `failed/internal_error` |

P7-S0 does not introduce new problem codes. Media implementation may add codes
such as `alignment_failed`, `timeout`, or `unsupported_transform` only through a
separate RFC 0001 registry update that fixes status, HTTP-style code, legal
stage, and JSON fixtures. Until then it reuses the RFC 0001/RFC 0003 codes
above. Renderer execution is outside `CompareOutcome`; renderer failures must
not rewrite a completed, unavailable, or failed comparison outcome.

A failed or unavailable outcome records the deepest reached public stage,
backend role when known, limit name when applicable, and whether any child
process was terminated, killed, reaped, or cleaned up. Completed media outcomes
cannot hide a stage failure inside an empty change list.

## Dependency, license, patent, export, and fixture analysis

This RFC selects no dependency. Later gates must review, at minimum:

- FFmpeg/ffprobe project license, exact build configuration, enabled LGPL/GPL
  and `nonfree` components, dynamic/static linking, binary redistribution,
  NOTICE/SBOM impact, and platform packaging;
- codec patent and export-control risk separately from open-source license
  compliance, including H.264, H.265/HEVC, AAC, Dolby-family codecs, and
  jurisdiction-specific obligations;
- model licenses, model weights, training-data notices, patent claims,
  redistribution limits, and platform support for ViSQOL, VMAF, or similar
  perceptual systems;
- optional Python package licenses, transitive dependencies, native extensions,
  wheel/source size, supported Python versions, and security advisories;
- fixture provenance: all audio/video corpora must be synthetic, generated from
  scripts, public-domain, or explicitly redistributable; generated files need
  source scripts, parameters, hashes, and license notes;
- no restricted competition media, personal recordings, unpublished scientific
  data, proprietary codecs, or non-redistributable model outputs may enter the
  repository.

Invoking a user-installed external CLI does not eliminate license, patent, or
export obligations if Platydiff later bundles, redistributes, documents a
required build, or depends on nonfree features.

## Artifacts and renderer boundary

First audio/video comparison gates produce no artifacts and expose only
`artifact_policy="none"`. Any other artifact policy value is invalid until
P7-M1 or a successor artifact gate accepts it. Bounded waveform PNGs,
spectrograms, thumbnails, frame captures, difference heatmaps, and short clips
are allowed only after a separate artifact gate accepts:

- RFC 0001 `ArtifactRef` URI validation;
- explicit artifact roots and no-clobber or safe replacement rules;
- deterministic names, media types, hashes, and byte sizes;
- bounded dimensions, durations, frame counts, and color/sample formats;
- privacy warnings for media-derived previews;
- proof that renderers and UI consume only validated outcomes and artifact
  references, never original sources;
- RFC 0004 presentation rules if any human review surface displays them.

Renderers may display only validated bounded facts. They must not reread media,
decode streams, recompute metrics, generate thumbnails, open files, fetch remote
resources, or reinterpret relation/verdict. UI work remains unauthorized.

## Delivery gates, commits, and tests

These gates are accepted delivery plans, not implementation authorization.
P7-A1, P7-A2, and P7-A3 require separate human authorization from updated
`main`. P7-A1 in particular must revalidate the actual merged v3/v4/v5
predecessor chain before implementing the accepted audio schema-v6 allocation.
P7-V1, P7-V2, and P7-V3 are accepted roadmap direction only and remain pending
until a later video backend/worker amendment accepts the next schema successor.

### P7-A1: audio schema and exact decoded PCM relation

1. `feat(core): add audio schema contracts`
2. `feat(audio): add explicit decoded PCM comparison`
3. `feat(cli): add explicit audio comparison commands`
4. `docs: document audio exact comparison contracts`

Gate: schema-v6 audio migration tests pass against the actual v3/v4/v5
predecessor chain; existing v1/v2/v3/v4/v5 fixtures remain compatible;
`encoded_bytes` and `decoded_samples` are distinct; the only first backend is
`stdlib_wave_pcm` for uncompressed PCM WAV; no hidden resampling/remixing/gain
or integer-to-float conversion occurs; empty, single-sample, different,
corrupt, unsupported, over-limit, limit-zero, endianness, sample-format,
channel-layout, gapless-delay, timestamp, host-owned materialization, and
deterministic repeated-run tests pass.

### P7-A2: audio waveform and spectral numeric relations

1. `feat(audio): add explicit waveform numeric policies`
2. `feat(audio): add bounded spectral comparison`
3. `test(audio): add numeric and spectral determinism corpus`
4. `docs: document audio numeric and spectral semantics`

Gate: tolerance formulas, offset/drift policy, alignment ambiguity, peak/RMS/
SNR, spectral windows/bins, empty-population behavior, NaN/Inf/signed-zero
handling, deterministic float aggregation, resource limits, truncation, and
missing-backend behavior pass.

### P7-A3: optional audio perceptual backend

1. `build(audio): add reviewed optional perceptual backend`
2. `feat(audio): add explicitly selected perceptual audio relation`
3. `test(audio): add perceptual backend conformance profile`
4. `docs: document perceptual audio backend limits`

Gate: model/license/patent/platform review is complete; version/model identity,
domain applicability, CPU/GPU variance, score semantics, unavailable/failure
behavior, and no fallback to exact relations are tested. This gate is optional
and not implied by P7-A1 or P7-A2.

### P7-V1: video schema, stream structure, and decoded frames

P7-V1 is accepted roadmap direction only and remains intentionally pending
after P7-S0. This RFC revision does not freeze a video backend, worker profile,
or schema successor, so it does not authorize any video implementation commits.

1. `docs: freeze video backend and worker conformance profile`
2. `feat(core): add video schema successor contracts`
3. `feat(video): add stream structure comparison`
4. `feat(video): add explicit decoded-frame comparison`
5. `feat(cli): add explicit video comparison commands`
6. `docs: document video stream and frame contracts`

Gate: schema migration is revalidated; stream selection, timebase, timestamps,
duration, VFR, frame reordering, keyframes, edit lists, multi-stream inventory,
pixel format, bit depth, color metadata, chroma siting, orientation, alpha,
interlacing, corrupt inputs, unsupported codecs, over-limits, limit-zero,
host-owned materialization, backend timeout kill/reap/cleanup, and
deterministic repeated runs pass. If the first video backend or worker protocol
cannot be frozen, P7-V1 remains documentation-only and independently pending.

### P7-V2: video frame numeric metrics and audio-track association

1. `feat(video): add explicit frame numeric comparison`
2. `feat(video): associate selected audio-track outcomes`
3. `test(video): add timeline, color, and audio-track matrix`
4. `docs: document video numeric and audio-track semantics`

Gate: no silent resize/crop/frame-rate/color/tone/deinterlace conversion; PSNR,
SSIM-style metrics, pixel errors, missing/duplicate frames, offset/drift,
audio-track sync, deterministic tie-breaking, output truncation, and resource
limits pass.

### P7-V3: optional video perceptual backend

1. `build(video): add reviewed optional perceptual backend`
2. `feat(video): add explicitly selected perceptual video relation`
3. `test(video): add VMAF-style backend conformance profile`
4. `docs: document perceptual video backend limits`

Gate: model/version/license/platform review is complete; CPU/GPU
reproducibility, feature extractor versions, score aggregation, unsupported
content, unavailable/failure semantics, and no fallback are tested. This gate
is optional and not implied by P7-V1 or P7-V2.

### P7-M1: optional media artifact gate

1. `feat(artifacts): add bounded audio waveform and spectrogram artifacts`
2. `feat(artifacts): add bounded video thumbnail and heatmap artifacts`
3. `docs: document media artifact safety and retention`

Gate: RFC 0001 `ArtifactRef`, RFC 0004 renderer/UI boundary, safe artifact
roots, deterministic names, hash verification, media privacy warnings,
no source reread, no implicit UI, and package-content checks pass. This gate is
not implied by any comparison gate.

Every implementation gate runs Ruff format/lint, strict mypy, complete pytest,
build, wheel/sdist inspection, package-content inspection, documentation link
checks, dependency/license review for changed packages or external tools, and
secret/path leak scans. Optional-backend suites use `media` and `external`
markers and skip with explicit reasons when a backend is absent; skipped tests
are not passing evidence.

### Test matrix

| Area | Required cases |
| --- | --- |
| Audio exactness | encoded-byte equality/difference, decoded-sample equality/difference, empty inputs, single-sample change, duration mismatch, channel add/remove/reorder, sample-rate mismatch, sample-format and endianness mismatch |
| Audio numeric | tolerance boundary, NaN, Inf, signed zero, clipping/out-of-range decode, peak/RMS/error/SNR, spectral window/bin alignment, offset, drift, ambiguity, repeated-run determinism |
| Video exactness | encoded-byte equality/difference, stream structure changes, decoded-frame equality/difference, empty/no-frame streams, single-frame change, missing/duplicate frames, VFR timestamps, edit lists, keyframes |
| Video color/pixels | pixel format, bit depth, full/limited range, transfer/primaries/matrix, ICC/HDR metadata, chroma subsampling/siting, alpha, orientation/rotation, interlacing, PSNR/SSIM-style boundaries |
| Hostile media | corrupt/truncated files, unsupported codecs, malformed containers, decode bombs, huge sample rate/channel count, huge resolution/frame count, long duration, packet storms, metadata bombs, limit-zero cases, hangs, crashes |
| Backends | missing backend, incompatible version, version mismatch, host-owned snapshot/materialization only, protocol/device allowlists, stderr redaction, timeout terminate/kill/reap, temp cleanup, exit-code validation, path redaction, bounded stdout/stderr/temp files, no network/device access |
| Lifecycle | canonical `validating`, `sourcing`, `resolving`, `decoding`, `normalizing`, `aligning`, `comparing`, and `aggregating` stage failures with stable reason codes and no completed equality on stage failure; renderer failures stay outside `CompareOutcome` |
| Contracts | audio schema-v6 migration fixtures, pending video successor migration fixtures, inherited v1/v2/v3/v4/v5 fixtures, spec/change invariant rejection, relation/view set ordering, metric/evaluation separation, non-finite JSON values, artifact-reference validation when enabled, unchanged text/binary/auto/plugin/CLI behavior |
| Corpora | synthetic or explicitly licensed tiny fixtures, source scripts, hashes, provenance notes, no restricted or personal media |

## Later callbacks

Media automatic detection must define bounded magic/extension/MIME/codec probes,
probe cost, ambiguity, pair selection, stream attribution, backend availability
interaction, and text/binary/media precedence in a successor to RFC 0003.

SDK v2 must define media source services, lifecycle stages, stream views,
backend roles, model identity, artifact authority, out-of-process isolation,
compatibility receipts, and schema migration before third-party audio/video
comparators can execute. SDK v1.1 remains text/binary-only.

Speech recognition, transcription comparison, music information retrieval,
scene/object/action understanding, subtitles, captions, timed metadata, OCR,
accessibility tracks, live streams, camera/microphone devices, encrypted DRM
media, adaptive streaming manifests, and semantic video equivalence require
separate contracts.

Richer presentation returns to RFC 0004. A UI can navigate validated audio
intervals, spectral cells, video frames, regions, stream facts, and artifact
refs, but it cannot decode, render, compare, transcode, fetch, or generate media
itself.

## References

- [FFmpeg documentation](https://ffmpeg.org/documentation.html)
- [ITU-R BS.1770 loudness algorithms](https://www.itu.int/rec/R-REC-BS.1770)
- [EBU R 128 loudness recommendation](https://tech.ebu.ch/publications/r128)
- [ViSQOL repository](https://github.com/google/visqol)
- [Netflix VMAF repository](https://github.com/Netflix/vmaf)
