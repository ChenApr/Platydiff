# RFC 0009: Audio and Video Comparison

[Chinese documentation](0009-audio-and-video-comparison_zh.md)

- Status: Proposed
- Date: 2026-09-10
- Owners: Platydiff maintainers
- Implementation owner: unassigned pending separate implementation authorization

## Summary and authorization boundary

This RFC proposes Phase 7 contracts for explicit audio and video comparison.
It is design work only. It does not authorize audio or video implementation,
dependency changes, FFmpeg or model installation, SDK v2, automatic detection,
UI work, artifact generation, plugin execution for new media modalities, or any
backend integration.

Audio and video are grouped as Phase 7 roadmap work because both are time-based
media, but they are not one implementation gate. Audio and video have separate
equivalence relations, IRs, codecs, timing models, metrics, artifacts, backend
risks, and dependency reviews. Each gate below requires a later explicit human
authorization from updated `main`; accepting or merging this RFC text alone
does not start implementation.

All behavior remains explicit-only. A caller must choose `AudioCompareSpec` or
`VideoCompareSpec` directly. Existing `AutoCompareSpec` remains text/binary-only
until a successor to RFC 0003 defines media probing, ambiguity, pair selection,
and provenance.

## Evidence ledger

| Current evidence at `origin/main` `4b3e129` | Phase 7 constraint |
| --- | --- |
| RFC 0001 separates failed/unavailable execution outcomes from completed `DiffResult` facts. | Decode, backend, timeout, resource, sandbox, model, and rendering failures must not become empty or synthetic media differences. |
| RFC 0002 requires every new modality to define spec, change, metric, artifact, equivalence relation, policy, failures, and gates before implementation. | This RFC records contracts and gates only; no audio/video code may start from it. |
| RFC 0003 keeps automatic detection bounded and closed to text/binary. | Audio/video do not participate in auto detection; extension, MIME, magic bytes, stream probes, or codec probes must not change existing auto behavior. |
| RFC 0003 snapshot paths own bounded replay, hashes, mutation checks, and safe labels for path/bytes/text sources. | Media gates must revalidate snapshot behavior before depending on it for large or mutable media. |
| RFC 0004 makes renderers and UI consume validated outcomes without rereading sources or recomputing facts. | Media thumbnails, waveforms, heatmaps, and frame previews require explicit bounded artifact contracts; UI work remains unauthorized. |
| RFC 0005 implements SDK v1.1 for text/binary detector, comparator, and renderer handles only. | Audio/video plugins require an SDK-v2 successor RFC; SDK v1.1 cannot introduce media specs or built-in media change kinds. |
| RFC 0006 accepts schema v3 for structured data, but its implementation state must be revalidated when a later gate starts. | Audio/video schema decisions must migrate from implemented v1/v2 and accepted v3 without assuming unmerged P4-A1 behavior. |
| RFC 0008 proposes source-code/PDF contracts and keeps heavyweight backends, artifacts, auto detection, and SDK v2 separate. | The same separation applies to media: backends and optional artifacts are independent gates. |
| Runtime dependencies are currently empty; audio/video backends are architecture-level plans. | Codec, model, patent, export, and FFmpeg build/license impact must be reviewed before any dependency or subprocess path is added. |
| Concurrent P4-A1 and Phase 5 work may exist outside `main`. | Treat that work as design evidence only; every code-dependent assumption below is a later revalidation gate. |

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
- schema compatibility with implemented v1/v2 and accepted schema-v3 design,
  subject to actual P4-A1 revalidation at implementation start.

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

## Proposed decisions

The following stable IDs are the human decision list for this proposal. They are
recommendations, not accepted decisions, until explicitly approved.

| ID | Proposed decision | Alternative not selected |
| --- | --- | --- |
| P7X1 | Keep audio/video comparison explicit-only; existing auto remains text/binary. | Add media candidates to RFC 0003 without defining expensive probes and ambiguity. |
| P7X2 | Split audio and video into independently authorized gates. | Treat all time-based media as one implementation batch. |
| P7X3 | Use the schema selected by a later gate: extend schema v3 only if it is still unreleased and implemented/revalidated; otherwise define a schema successor. | Extend v1/v2 closed unions or assume accepted but unimplemented schema-v3 details. |
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

The implementation gate chooses the concrete schema according to the state of
`main` at that time.

If accepted schema v3 from RFC 0006 has been implemented, remains unreleased,
and can still be extended safely, Phase 7 built-ins may extend it as follows:

```python
CompareSpecV3 = (
    AutoCompareSpec | TextCompareSpec | BinaryCompareSpec
    | JsonCompareSpec | YamlCompareSpec | TableCompareSpec | ArrayCompareSpec
    | AudioCompareSpec | VideoCompareSpec
)
ChangeV3 = (
    TextHunk | BinarySpan | StructuredChange | TableChange | ArrayChange
    | AudioChange | VideoChange | ExtensionChange
)
```

If schema v3 has been released, has not been implemented, or has closed-union
constraints that make a media extension unsafe, Phase 7 must use a schema
successor instead. In every case:

- existing built-in text, binary, and auto calls keep schema v1;
- existing `PluginHost` text/binary calls keep schema v2;
- audio/video built-in specs produce the selected media schema, including
  failures before resolution;
- readers for the selected media schema accept v1, v2, and any implemented
  v3 base according to explicit migration helpers;
- v1/v2/v3 upgraders preserve original facts and add only documented neutral
  defaults;
- no automatic downgrade exists for audio/video outcomes;
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
| Accepted, unimplemented Phase 4 path | v3 candidate | explicit json/yaml/table/array | none | Revalidate actual P4-A1 implementation before media schema work. |
| Proposed Phase 6 source/PDF path | unspecified | source-code/PDF | none until separately authorized | Design evidence only; no dependency for Phase 7. |
| Proposed Phase 7 audio path | selected media schema | explicit audio | none in first gates | Produces validated audio specs, changes, metrics, transformations, and failures. |
| Proposed Phase 7 video path | selected media schema | explicit video | none in first gates | Produces validated video specs, changes, metrics, transformations, and failures. |
| Existing auto on media-looking bytes | v1 | text or binary only | existing rules | Detection evidence and result do not change. |
| Future SDK v2 or media auto | unspecified | unspecified | unspecified | Requires successor RFCs. |

## Audio comparison contract

### Public intent

The proposed first public shape is:

```python
class AudioCompareSpec:
    kind: Literal["audio"] = "audio"
    relations: tuple[
        Literal[
            "encoded_bytes",
            "decoded_samples",
            "waveform_numeric",
            "spectral",
            "perceptual",
        ],
        ...
    ] = ("decoded_samples",)
    stream: AudioStreamSelection = AudioStreamSelection()
    decode: AudioDecodeOptions = AudioDecodeOptions()
    alignment: AudioAlignmentOptions = AudioAlignmentOptions()
    waveform: AudioWaveformOptions = AudioWaveformOptions()
    spectral: AudioSpectralOptions = AudioSpectralOptions()
    perceptual: AudioPerceptualOptions = AudioPerceptualOptions()
    artifact_policy: Literal["none", "record_refs"] = "none"
    limits: AudioResourceLimits = AudioResourceLimits()
```

`PathSource` and `BytesSource` are the first source kinds. `TextSource` is
unsupported for audio unless a later gate defines an explicit byte encoding
relation; an unsupported source returns `failed/source_type_unsupported`.

Relation meanings are independent:

- `encoded_bytes` reuses exact binary semantics and says nothing about decoded
  signal equivalence;
- `decoded_samples` compares the selected decoded PCM stream exactly after an
  explicit sample representation is chosen;
- `waveform_numeric` compares aligned samples using explicit numeric tolerance
  and reports sample-domain error metrics;
- `spectral` compares explicitly windowed spectra and cannot imply sample
  equality;
- `perceptual` uses a named optional perceptual backend and cannot override
  exact or spectral differences.

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
    max_offset_samples: int = 0
    max_drift_ppm: float = 0.0
    ambiguity_margin: float = 0.0
```

Offset and drift compensation are transformations with recorded parameters,
observed estimates, tie-break order, and confidence or ambiguity facts. If two
alignments are indistinguishable under the configured margin, if drift exceeds
policy, or if the search budget is exhausted, the outcome is
`failed/alignment_failed` or `failed/compare_resource_limit`, not an approximate
completed equality claim.

The proposed built-in audio change is:

```python
class AudioChange:
    kind: Literal["audio_change"]
    relation: Literal[
        "encoded_bytes", "decoded_samples", "waveform_numeric",
        "spectral", "perceptual"
    ]
    operation: Literal[
        "stream_add", "stream_remove", "metadata_update",
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

Audio coordinates use stream index, one-based channel ordinal or stable channel
label, sample interval, timestamp interval, and spectral bin/time cell where
applicable. Changes are observations, not patches. Detail truncation occurs
only after the relation, metrics, and total change count are known.

### Audio metrics and policy

The first audio metric registry is proposed as:

| Metric name | Meaning | Unit | Direction | Aggregation | Empty population |
| --- | --- | --- | --- | --- | --- |
| `audio.samples_compared` | aligned sample pairs across selected channels | `samples` | `neutral` | `count` | zero |
| `audio.samples_changed` | unequal or tolerance-failing sample pairs | `samples` | `lower_is_better` | `count` | zero |
| `audio.channels_compared` | selected channels compared | `channels` | `neutral` | `count` | zero |
| `audio.duration_delta` | after duration minus before duration after selected alignment | `seconds` | `lower_abs_is_better` | `difference` | zero |
| `audio.sample_peak_error` | maximum absolute sample error after scaling policy | `amplitude_full_scale` | `lower_is_better` | `maximum` | metric omitted |
| `audio.sample_rms_error` | root mean square sample error | `amplitude_full_scale` | `lower_is_better` | `rms` | metric omitted |
| `audio.snr` | signal-to-noise ratio using before as reference | `db` | `higher_is_better` | `ratio_db` | positive infinity for zero error, omitted for zero reference energy |
| `audio.spectral_peak_error` | maximum spectral magnitude error | `db` | `lower_is_better` | `maximum` | metric omitted |
| `audio.spectral_rms_error` | RMS spectral magnitude error | `db` | `lower_is_better` | `rms` | metric omitted |
| `audio.perceptual_score` | named backend perceptual similarity score | backend-defined stable unit | backend-defined | backend-defined | metric omitted |

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
    max_spectral_cells: int = 20_000_000
    max_backend_seconds: int = 30
    max_stdout_stderr_bytes: int = 4 * 1024 * 1024
    max_temp_bytes: int = 512 * 1024 * 1024
    max_compare_work: int = 10_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024
```

Defaults are tentative and must be revalidated against selected backends before
acceptance. Corrupt, truncated, unsupported-codec, hostile-container,
over-duration, huge-sample-rate, huge-channel-count, decode-bomb, infinite
stream, backend-hang, backend-crash, and over-output cases are required tests.
Backend unavailability is `unavailable/backend_unavailable`; unsupported codec
or profile is `unavailable/capability_unavailable` unless a selected decoder
starts and then fails, in which case the observed failure is `failed`.

## Video comparison contract

### Public intent

The proposed first public shape is:

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
    artifact_policy: Literal["none", "record_refs"] = "none"
    limits: VideoResourceLimits = VideoResourceLimits()
```

`encoded_bytes` reuses exact binary semantics. `stream_structure` compares
container and stream layout, codec parameters, packet indexes, timebases,
metadata, edit lists, keyframes, attachments, chapters, and selected side data.
`decoded_frames` compares the explicit decoded frame sequence and timestamps.
`frame_numeric` permits explicit pixel tolerances. `perceptual_video` is an
optional model/backend gate. `audio_tracks` delegates to the audio contract
with the video timeline association recorded; it never silently drops tracks.

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

Missing frames, duplicate frames, duplicate timestamps, dropped frames, inserted
frames, stream additions/removals, and drift are first-class observations or
failures. Deterministic tie-breaking must be specified for any frame matching
policy. Ambiguity, unsupported timestamp structure, or over-budget alignment is
`failed/alignment_failed` or `failed/compare_resource_limit`, not a hidden
content difference.

The proposed built-in video change is:

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

### Video metrics and policy

The first video metric registry is proposed as:

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
| `video.audio_tracks_changed` | selected audio tracks with non-pass audio evaluation | `tracks` | `lower_is_better` | `count` | zero |

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
    max_backend_seconds: int = 60
    max_stdout_stderr_bytes: int = 4 * 1024 * 1024
    max_temp_bytes: int = 2 * 1024 * 1024 * 1024
    max_compare_work: int = 20_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024
```

Defaults are tentative and must be revalidated. Adversarial tests include
malformed containers, unsupported codecs, resolution bombs, huge frame counts,
long durations, many streams, packet storms, decompression bombs, infinite or
non-terminating streams, corrupt frames, timestamp wraparound, backend hangs,
backend crashes, excessive stdout/stderr, and temp-output explosions.

## Backends and execution boundary

Standard-library capability is limited to exact encoded-byte comparison and any
future narrowly reviewed uncompressed format support. Optional Python libraries
may handle metadata or numeric arrays only after dependency, license, size,
platform, native-code, and security review. External programs such as
`ffprobe`, `ffmpeg`, or model runners are separate backend roles and require
their own conformance profile.

Every external program invocation must use:

- argument arrays with `shell=False`;
- no interpolation of untrusted input into command strings;
- close-on-exec descriptors and bounded temporary directories;
- explicit timeout and process cleanup;
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

First audio/video comparison gates produce no artifacts. Bounded waveform PNGs,
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

These gates are proposed plans, not implementation authorization.

### P7-A1: audio schema and exact decoded PCM relation

1. `feat(core): add audio schema contracts`
2. `feat(audio): add explicit decoded PCM comparison`
3. `feat(cli): add explicit audio comparison commands`
4. `docs: document audio exact comparison contracts`

Gate: selected schema migration tests pass; existing v1/v2 and any implemented
v3 fixtures remain compatible; `encoded_bytes` and `decoded_samples` are
distinct; WAV/PCM or selected first backend behavior is reviewed; no hidden
resampling/remixing/gain occurs; empty, single-sample, different, corrupt,
unsupported, over-limit, endianness, sample-format, channel-layout,
gapless-delay, timestamp, and deterministic repeated-run tests pass.

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

1. `feat(core): add video schema contracts`
2. `feat(video): add stream structure comparison`
3. `feat(video): add explicit decoded-frame comparison`
4. `feat(cli): add explicit video comparison commands`
5. `docs: document video stream and frame contracts`

Gate: schema migration is revalidated; stream selection, timebase, timestamps,
duration, VFR, frame reordering, keyframes, edit lists, multi-stream inventory,
pixel format, bit depth, color metadata, chroma siting, orientation, alpha,
interlacing, corrupt inputs, unsupported codecs, over-limits, and deterministic
repeated runs pass.

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
| Hostile media | corrupt/truncated files, unsupported codecs, malformed containers, decode bombs, huge sample rate/channel count, huge resolution/frame count, long duration, packet storms, hangs, crashes |
| Backends | missing backend, incompatible version, version mismatch, stderr redaction, timeout, exit-code validation, path redaction, bounded stdout/stderr/temp files, no network/device access |
| Contracts | schema migration fixtures, spec/change invariant rejection, metric ordering, non-finite JSON values, artifact-reference validation when enabled, unchanged text/binary/auto/plugin/CLI behavior |
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
