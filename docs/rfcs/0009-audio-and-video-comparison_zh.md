# RFC 0009：音频与视频比较

[English documentation](0009-audio-and-video-comparison.md)

- Status: Proposed
- Date: 2026-09-10
- Owners: Platydiff 维护者
- Implementation owner: 尚未指派，等待单独的实现授权

## 摘要与授权边界

本 RFC 提议 Phase 7 的显式音频与视频比较契约。本文只进行设计工作，不授权音频或
视频实现、依赖变更、FFmpeg 或模型安装、SDK v2、自动探测、UI 工作、artifact 生成、
新媒体模态插件执行或任何后端集成。

音频和视频同属 Phase 7 路线图，是因为二者都是基于时间的媒体；但它们不是同一个实现
门禁。音频和视频具有不同的等价关系、IR、编解码器、时间模型、指标、artifact、后端
风险和依赖审查。下列每个门禁都需要后续基于更新后的 `main` 获得明确人工授权；仅接受
或合并本 RFC 文本不会启动实现。

所有行为保持显式启用。调用者必须直接选择 `AudioCompareSpec` 或 `VideoCompareSpec`。
既有 `AutoCompareSpec` 在 RFC 0003 的后继 RFC 定义媒体探测、歧义、成对选择和 provenance
之前，仍只支持 text/binary。

## 证据账本

| `origin/main` `4b3e129` 上的当前证据 | Phase 7 约束 |
| --- | --- |
| RFC 0001 将 failed/unavailable 执行终态与 completed `DiffResult` 事实分离。 | decode、backend、timeout、resource、sandbox、model 和 rendering 失败不得变成空或伪造的媒体差异。 |
| RFC 0002 要求每个新模态在实现前定义 spec、change、metric、artifact、等价关系、policy、failure 与 gate。 | 本 RFC 只记录契约与门禁，不启动音视频代码工作。 |
| RFC 0003 保持自动探测有界且只对 text/binary 封闭。 | 音视频不参与 auto detection；extension、MIME、magic byte、stream probe 或 codec probe 不得改变既有 auto 行为。 |
| RFC 0003 的 snapshot path 为 path/bytes/text source 管理有界 replay、hash、mutation check 与安全 label。 | 媒体门禁依赖它处理大型或可变媒体前，必须重新验证 snapshot 行为。 |
| RFC 0004 要求 renderer 与 UI 消费 validated outcome，不重读 source 或重算事实。 | 媒体 thumbnail、waveform、heatmap 和 frame preview 需要显式有界 artifact 契约；UI 工作仍未授权。 |
| RFC 0005 实现的 SDK v1.1 只覆盖 text/binary detector、comparator 与 renderer handle。 | 音视频插件需要 SDK-v2 后继 RFC；SDK v1.1 不能引入媒体 spec 或内建媒体 change kind。 |
| RFC 0006 接受 schema v3 用于结构化数据，但后续门禁启动时必须重新验证其实现状态。 | 音视频 schema 决策必须从已实现 v1/v2 和已接受 v3 迁移，不能假设未合并 P4-A1 行为。 |
| RFC 0008 提议 source-code/PDF 契约，并保持重量级后端、artifact、auto detection 和 SDK v2 分离。 | 媒体也采用同样分离：后端和可选 artifact 是独立门禁。 |
| 当前运行时依赖为空；音视频后端仍是架构层计划。 | 任何依赖或 subprocess path 进入前，必须审查 codec、model、patent、export 与 FFmpeg build/license 影响。 |
| 并发 P4-A1 和 Phase 5 工作可能存在于 `main` 之外。 | 只能把这些工作当作设计证据；本文中所有依赖代码状态的假设都是后续 revalidation gate。 |

## 目标与非目标

Phase 7 目标包括：

- 显式音频 spec，区分 encoded byte、decoded sample、waveform/numeric tolerance、spectral
  similarity 与 perceptual similarity；
- 显式视频 spec，区分 encoded byte、stream/container structure、decoded frame、
  frame/pixel metric、perceptual video 与 audio track comparison；
- 可见且确定性的 decode、normalization、alignment、metric、aggregation、policy、artifact、
  backend 与 provenance 契约；
- 精确的 container、codec、channel、sample、timestamp、frame、color、HDR 与 stream-selection
  语义；
- 不隐式 resampling、remixing、loudness normalization、gain、resize、crop、frame-rate conversion、
  deinterlace、tone-map、color conversion、track dropping 或 synchronization change；
- 对 corrupt、truncated、hostile、long-duration、high-rate、high-channel-count、high-resolution、
  high-frame-count 和 multi-stream input 的资源与安全规则；
- 与已实现 v1/v2 和已接受 schema-v3 设计兼容，并在实现开始时重新验证实际 P4-A1 状态。

Phase 7 不包含：

- `AutoCompareSpec` 中的自动音视频探测或 stream inference；
- codec 安装、模型下载、FFmpeg 捆绑、依赖解析器或后端 package 选择；
- backend 启动后从一种 relation fallback 到另一种 relation；
- 隐藏在 metric 名称下的有损 relation 变更；
- 默认启用 perceptual metric；
- source mutation、media repair、transcoding、clipping、filtering、OCR、speech recognition、
  transcription、scene understanding、object recognition 或 semantic video understanding；
- directory、URL、device、camera、microphone、stream、archive 或 stdin 输入；
- 通过 SDK v1.1 执行 audio/video plugin comparator；
- HTML、TUI、desktop、local-web 或 review UI 工作；
- 除下方可选 artifact gate 外的媒体 artifact 写入。

## 提议决策

下面的稳定 ID 是本提案的人工决策清单。在 reviewer 显式批准前，它们都是建议而非已接受决策。

| ID | 提议决策 | 未选择的替代方案 |
| --- | --- | --- |
| P7X1 | 音视频比较保持 explicit-only；既有 auto 仍只支持 text/binary。 | 未定义昂贵 probe 与 ambiguity 就把媒体 candidate 加入 RFC 0003。 |
| P7X2 | 将音频和视频拆分为独立授权门禁。 | 把所有 time-based media 当作一个实现批次。 |
| P7X3 | 后续门禁选择具体 schema：只有当 v3 仍未发布且已实现/重新验证时才扩展 v3；否则定义 schema successor。 | 扩展 v1/v2 closed union，或假设已接受但未实现的 schema-v3 细节。 |
| P7X4 | SDK v1.1 下拒绝 audio/video plugin comparator；媒体模态需要 SDK v2。 | 允许 plugin 安装引入媒体 spec 或 change kind。 |
| P7X5 | 保持 RFC 0004 artifact/UI 工作独立；首批比较门禁可以不产生文件。 | 让 decoding 或 rendering 隐式写出 preview、thumbnail、clip、heatmap 或 waveform。 |
| P7X6 | 后端执行开始后，禁止改变 relation 的 fallback。 | 失败时静默按 byte、另一 codec/backend、低保真 decode 或 perceptual metric 重试。 |
| P7X7 | 将 perceptual metric 作为单独审查的可选/外部门禁。 | 默认提供 ViSQOL、VMAF 或模型分数。 |
| P7X8 | 每个依赖代码状态的假设都是 revalidation gate，包括 P4-A1、Phase 5 与 RFC 0008 状态。 | 把并发未合并工作当作兼容性证明。 |
| A1 | 音频公开 `encoded_bytes`、`decoded_samples`、`waveform_numeric`、`spectral` 与 `perceptual` 这些不同 relation。 | 把所有音频结果折叠为一个 "same audio" bit。 |
| A2 | 首个音频默认 relation 是针对可显式解码 PCM input 的 `decoded_samples`；`encoded_bytes` 单独选择。 | 对所有音频默认使用 perceptual similarity 或 byte equality。 |
| A3 | 不隐式执行 resampling、channel remixing、gain、loudness normalization、silence trimming、clipping、dithering、filtering 或 delay compensation。 | 把常见音频预处理隐藏在 metric 中。 |
| A4 | sample-rate、format、endianness、channel layout/order、duration、timestamp、encoder delay 与 padding 都是比较事实。 | 把它们当作 result 之外的 backend metadata。 |
| A5 | 音频 alignment 必须显式且确定；歧义或 search 超预算以失败结束，而不是声称 approximate match。 | 使用 best-effort cross-correlation 且不记录不确定性。 |
| A6 | Waveform 与 spectral metric 必须定义 unit、direction、aggregation、empty-population 行为和确定性浮点顺序。 | 使用非正式 DSP 名称而不提供稳定 metric contract。 |
| A7 | ViSQOL/PESQ/POLQA 类 perceptual metric 需要单独的 model/license/platform/patent 审查和可选门禁。 | 把 perceptual scoring 加为普通依赖。 |
| V1 | 视频公开 `encoded_bytes`、`stream_structure`、`decoded_frames`、`frame_numeric`、`perceptual_video` 与 `audio_tracks` 这些独立 view。 | 让视觉相等覆盖 stream、timestamp 或 audio 差异。 |
| V2 | stream selection、timebase、timestamp、duration、variable frame rate、frame reordering、keyframe、edit list 与 multi-stream behavior 都是显式的。 | 让 backend 决定默认 stream 和 timeline 解释。 |
| V3 | pixel format、bit depth、range、transfer function、primaries、matrix coefficients、ICC/HDR metadata、chroma subsampling/siting、orientation、alpha 与 interlacing 都是记录事实。 | 允许隐藏 color、geometry 或 field-order conversion。 |
| V4 | 不隐式 resize、crop、frame-rate conversion、deinterlace、tone-map、color conversion、track dropping 或 synchronization change。 | 计算 metric 前静默规范化视频。 |
| V5 | spatial/temporal alignment 使用确定性 tie-break；missing/duplicate frame 与 offset/drift 是一等 outcome。 | 把 alignment uncertainty 合并进内容差异。 |
| V6 | VMAF 类 metric 需要带 model/version/license 与 CPU/GPU reproducibility 证据的可选/外部门禁。 | 把 VMAF 当成始终可用的数值 metric。 |

## Schema 与兼容性契约

实现门禁根据当时 `main` 的状态选择具体 schema。

如果 RFC 0006 接受的 schema v3 已经实现、仍未发布，且仍能安全扩展，Phase 7 内建能力可以如下扩展：

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

如果 schema v3 已发布、尚未实现，或 closed-union 约束使媒体扩展不安全，Phase 7 必须使用
schema successor。无论哪种情况：

- 既有内建 text、binary 与 auto 调用保持 schema v1；
- 既有 `PluginHost` text/binary 调用保持 schema v2；
- audio/video 内建 spec 使用选定的媒体 schema，即使在 resolution 前失败也是如此；
- 选定媒体 schema 的 reader 按显式 migration helper 接受 v1、v2 与任何已实现的 v3 base；
- v1/v2/v3 upgrader 保留原始事实，只加入文档化的中性默认值；
- audio/video outcome 不存在自动 downgrade；
- unknown built-in spec/change kind 仍然非法；
- unknown namespaced extension change 保持 RFC 0001 行为。

Phase 3 SDK v1.1 仍只支持 text/binary。Audio/video plugin 需要 SDK-v2 后继 RFC 来定义媒体
source view、lifecycle stage、backend role、sandboxing、artifact authority、compatibility receipt
和 schema migration。既有 auto detection 在单独接受后继 detection RFC 前仍只支持 text/binary。

### 兼容性矩阵

| producer/path | schema | modality | plugin 参与 | 必需行为 |
| --- | --- | --- | --- | --- |
| 既有 `compare()` 与默认 CLI | v1 | text、binary、解析到二者的 auto | 无 | 既有 byte-stable fixture 继续有效。 |
| 既有显式 `PluginHost` | v2 | text、binary、解析到二者的 auto | SDK v1.1 | 既有 v2 fixture 与 receipt 继续有效。 |
| 已接受但未实现的 Phase 4 path | v3 candidate | 显式 json/yaml/table/array | 无 | 媒体 schema 工作开始前重新验证实际 P4-A1 实现。 |
| 提议中的 Phase 6 source/PDF path | 未指定 | source-code/PDF | 单独授权前无 | 只作为设计证据；不是 Phase 7 依赖。 |
| 提议中的 Phase 7 audio path | 选定媒体 schema | 显式 audio | 首批门禁无 | 产生 validated audio spec、change、metric、transformation 与 failure。 |
| 提议中的 Phase 7 video path | 选定媒体 schema | 显式 video | 首批门禁无 | 产生 validated video spec、change、metric、transformation 与 failure。 |
| 对 media-looking bytes 使用既有 auto | v1 | 仅 text 或 binary | 仅既有规则 | detection evidence 与 result 不变。 |
| 未来 SDK v2 或 media auto | 未指定 | 未指定 | 未指定 | 需要后继 RFC。 |

## 音频比较契约

### Public intent

提议的首个 public shape 为：

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

首批 source kind 是 `PathSource` 与 `BytesSource`。除非后续门禁定义显式字节编码 relation，
`TextSource` 对 audio 不受支持；不支持的 source 返回 `failed/source_type_unsupported`。

Relation 含义彼此独立：

- `encoded_bytes` 复用精确二进制语义，不说明 decoded signal 是否等价；
- `decoded_samples` 在显式选择 sample representation 后，精确比较选中 decoded PCM stream；
- `waveform_numeric` 使用显式 numeric tolerance 比较 aligned sample，并报告 sample-domain error metric；
- `spectral` 比较显式 windowed spectrum，不能推出 sample equality；
- `perceptual` 使用命名的可选 perceptual backend，不能覆盖 exact 或 spectral difference。

### Decode 与 IR fact

私有 `AudioIR` 至少必须携带：

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

PCM integer-to-float conversion、float widening、endian conversion、packed-to-planar conversion
和 signedness conversion 都是 transformation。只有 spec 请求或 relation 需要 canonical
representation 时才合法，并且每个执行过的 transformation 都要记录。比较开始前必须定义
floating-point NaN、infinity、signed zero、denormal handling、clipping 与 out-of-range decoded value。

Container metadata、tag、codec side data、channel label、delay/padding 与 timestamp 在选中时都是
比较事实，不是隐藏的 backend note。Gapless delay 和 padding 可以作为 metadata 比较，或作为显式
alignment transform 应用，但不能静默同时做两者。

### Audio alignment 与 change

默认 alignment 按 decoded sample index 与 channel order，offset 为 zero。可选 timestamp
alignment、fixed-offset alignment 与有界 cross-correlation search 需要显式 spec field：

```python
class AudioAlignmentOptions:
    mode: Literal["sample_index", "timestamp", "fixed_offset", "correlation"] = "sample_index"
    max_offset_samples: int = 0
    max_drift_ppm: float = 0.0
    ambiguity_margin: float = 0.0
```

Offset 与 drift compensation 是 transformation，需记录参数、观测估计、tie-break order 以及 confidence
或 ambiguity fact。如果两个 alignment 在配置 margin 下不可区分、drift 超过 policy，或 search budget
耗尽，outcome 是 `failed/alignment_failed` 或 `failed/compare_resource_limit`，而不是近似完成的
equality claim。

提议的内建 audio change 为：

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

Audio coordinate 使用 stream index、一基 channel ordinal 或稳定 channel label、sample interval、
timestamp interval，以及适用时的 spectral bin/time cell。Change 是 observation，不是 patch。
只有 relation、metric 与 total change count 已知后，才可执行 detail truncation。

### Audio metric 与 policy

首批 audio metric registry 提议为：

| Metric name | 含义 | Unit | Direction | Aggregation | Empty population |
| --- | --- | --- | --- | --- | --- |
| `audio.samples_compared` | selected channel 上的 aligned sample pair | `samples` | `neutral` | `count` | zero |
| `audio.samples_changed` | 不等或 tolerance 失败的 sample pair | `samples` | `lower_is_better` | `count` | zero |
| `audio.channels_compared` | 被比较的 selected channel | `channels` | `neutral` | `count` | zero |
| `audio.duration_delta` | selected alignment 后 after duration 减 before duration | `seconds` | `lower_abs_is_better` | `difference` | zero |
| `audio.sample_peak_error` | scaling policy 后最大绝对 sample error | `amplitude_full_scale` | `lower_is_better` | `maximum` | 省略 metric |
| `audio.sample_rms_error` | root mean square sample error | `amplitude_full_scale` | `lower_is_better` | `rms` | 省略 metric |
| `audio.snr` | 以 before 为 reference 的 signal-to-noise ratio | `db` | `higher_is_better` | `ratio_db` | zero error 为 positive infinity；zero reference energy 时省略 |
| `audio.spectral_peak_error` | 最大 spectral magnitude error | `db` | `lower_is_better` | `maximum` | 省略 metric |
| `audio.spectral_rms_error` | RMS spectral magnitude error | `db` | `lower_is_better` | `rms` | 省略 metric |
| `audio.perceptual_score` | 命名 backend 的 perceptual similarity score | backend-defined stable unit | backend-defined | backend-defined | 省略 metric |

Waveform tolerance 是 comparison intent，决定 `waveform_numeric` 的 relation；它不只是 verdict
threshold。Count metric 是 integer-valued 且稳定。浮点 metric 在 release 前必须定义 accumulation
order、rounding、NaN/Inf behavior、reference signal、scale 与 dtype。Spectral metric 必须定义
window function、window length、hop length、FFT length、padding、magnitude/log conversion、bin
alignment 与 aggregation。每个 selected non-perceptual relation 的默认 policy 是 equality 或
changed-count zero；默认 audio rule 不产生 `warn`。

ViSQOL 等 perceptual metric 不是 core dependency。选择此类 metric 的门禁必须记录 model identity、
version、license、patent consideration、platform support、training/test-data redistribution
constraint、deterministic setting、CPU/GPU variance，以及 score 对 speech、music、bandwidth-limited
audio 或其他 domain 的适用性。

### Audio resource 与 failure

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

默认值仍是暂定，接受前必须基于选定后端重新验证。Corrupt、truncated、unsupported-codec、
hostile-container、over-duration、huge-sample-rate、huge-channel-count、decode-bomb、infinite stream、
backend-hang、backend-crash 和 over-output 都是必测 case。Backend 不可用是
`unavailable/backend_unavailable`；unsupported codec 或 profile 是 `unavailable/capability_unavailable`，
除非选定 decoder 已启动后失败，此时按实际观测 failure 返回 `failed`。

## 视频比较契约

### Public intent

提议的首个 public shape 为：

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

`encoded_bytes` 复用精确二进制语义。`stream_structure` 比较 container 和 stream layout、codec
parameter、packet index、timebase、metadata、edit list、keyframe、attachment、chapter 与选定
side data。`decoded_frames` 比较显式 decoded frame sequence 与 timestamp。`frame_numeric` 允许
显式 pixel tolerance。`perceptual_video` 是可选 model/backend gate。`audio_tracks` 委托 audio
contract，并记录 video timeline association；绝不静默丢弃 track。

### Decode、timeline、color 与 IR fact

私有 `VideoIR` 至少必须携带：

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

Pixel format、bit depth、range、transfer function、primaries、matrix coefficients、ICC/HDR metadata、
chroma subsampling/siting、orientation、rotation、alpha 与 interlacing 都是比较事实。任何转换都是
命名 transformation，且必须显式、确定并记录。Backend default 不足以作为 provenance。

Variable frame rate、edit list、start offset、B-frame reordering、missing timestamp、duplicate
timestamp、non-monotonic timestamp、keyframe placement、multi-angle 或 multi-stream 选择，以及
audio/video synchronization 都是 timeline fact。门禁必须定义它们是直接比较、用于 alignment，还是
unsupported。

### Video alignment 与 change

默认 temporal alignment 按 selected presentation timestamp 与 stream index。Fixed-offset 与有界
feature/fingerprint alignment 是可选显式 policy。Spatial alignment 默认要求 decoded frame geometry
和 pixel coordinate 相同。不隐式执行 crop、resize、rotation、deinterlace、tone-map、color
conversion、chroma resampling、frame-rate conversion、track dropping 或 sync shift。

Missing frame、duplicate frame、duplicate timestamp、dropped frame、inserted frame、stream add/remove
和 drift 是一等 observation 或 failure。任何 frame matching policy 都必须指定确定性 tie-break。
Ambiguity、unsupported timestamp structure 或 alignment 超预算是 `failed/alignment_failed` 或
`failed/compare_resource_limit`，不是隐藏的内容差异。

提议的内建 video change 为：

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

Coordinate 包含 stream index、frame ordinal、presentation timestamp、timebase、pixel rectangle、
plane/component，以及适用时的 audio-track coordinate。Region change 是 observation，不是 patch
data 或 rendered artifact。

### Video metric 与 policy

首批 video metric registry 提议为：

| Metric name | 含义 | Unit | Direction | Aggregation | Empty population |
| --- | --- | --- | --- | --- | --- |
| `video.frames_compared` | 已评估的 aligned frame pair | `frames` | `neutral` | `count` | zero |
| `video.frames_changed` | 至少有一个 failing pixel/structure observation 的 frame | `frames` | `lower_is_better` | `count` | zero |
| `video.missing_frames` | before-only frame observation | `frames` | `lower_is_better` | `count` | zero |
| `video.duplicate_frames` | selected timeline policy 下的 duplicate frame observation | `frames` | `lower_is_better` | `count` | zero |
| `video.changed_pixels` | region grouping 前的 changed pixel | `pixels` | `lower_is_better` | `sum` | zero |
| `video.pixel_peak_error` | explicit scaling policy 后的最大 component error | `component_units` | `lower_is_better` | `maximum` | 省略 metric |
| `video.pixel_rms_error` | RMS component error | `component_units` | `lower_is_better` | `rms` | 省略 metric |
| `video.psnr` | peak signal-to-noise ratio | `db` | `higher_is_better` | `minimum` | zero error 为 positive infinity；无 compared pixel 时省略 |
| `video.ssim` | 显式配置的 SSIM-style score | `ratio` | `higher_is_better` | 按 spec 为 `minimum` 或 `mean` | 省略 metric |
| `video.vmaf` | 命名 VMAF model score | `score` | `higher_is_better` | model-defined | 省略 metric |
| `video.audio_tracks_changed` | selected audio track 中 audio evaluation 非 pass 的数量 | `tracks` | `lower_is_better` | `count` | zero |

PSNR 必须定义 peak value、component selection、averaging、bit depth、range 与 color representation。
SSIM-style metric 必须定义 windowing、color plane、boundary handling、constant、aggregation 与
floating-point determinism。VMAF 需要 model identity、version、license、feature extractor version、
CPU/GPU/reproducibility evidence、platform support 与 redistribution review。Selected non-perceptual
view 的默认 policy 视情况要求 zero changed item 或 zero changed pixel/frame。默认 video policy
不产生 `warn`。

### Video resource 与 failure

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

默认值仍是暂定，必须重新验证。Adversarial test 包括 malformed container、unsupported codec、
resolution bomb、huge frame count、long duration、many stream、packet storm、decompression bomb、
infinite/non-terminating stream、corrupt frame、timestamp wraparound、backend hang、backend crash、
excessive stdout/stderr 和 temp-output explosion。

## 后端与执行边界

标准库能力仅限精确 encoded-byte 比较，以及未来经窄范围审查的 uncompressed format support。
可选 Python library 只有在完成 dependency、license、size、platform、native-code 和 security review
后，才可处理 metadata 或 numeric array。`ffprobe`、`ffmpeg` 或 model runner 等外部程序是独立
backend role，需要自己的 conformance profile。

每次 external program invocation 必须使用：

- argument array 与 `shell=False`；
- 不把 untrusted input 插入 command string；
- close-on-exec descriptor 与有界 temporary directory；
- 显式 timeout 和 process cleanup；
- 有界 stdout、stderr、decoded frame、packet metadata 与 temp-file bytes；
- exit-code validation 与结构化 stderr redaction；
- 除 allowlist 外不继承不可信 environment；
- 无 network、remote resource loading、device capture，且不写 host temp/artifact root 之外；
- diagnostic 中执行 path redaction 和 safe label；
- provenance 记录 backend name、version、build configuration、enabled library/codec、model identity、
  platform 与 deterministic setting。

Backend availability 在可行时先于 selection 测试，并以 stable reason code 记录 available/unavailable。
缺失的未 pin backend 可在执行前跳过。Pinned 或唯一兼容 backend 缺失产生
`unavailable/backend_unavailable`。一旦 selected backend 开始 decode 或 compare，failure 就在实际
stage 产生 `failed`，且不 fallback 到另一个 backend 或 relation。除非未来 spec 显式允许并记录
lost information 与 policy impact，否则禁止 degraded fidelity。

## 依赖、许可证、专利、出口与 fixture 分析

本 RFC 不选择任何依赖。后续门禁至少必须审查：

- FFmpeg/ffprobe 项目 license、精确 build configuration、启用的 LGPL/GPL 与 `nonfree` component、
  dynamic/static linking、binary redistribution、NOTICE/SBOM 影响和 platform packaging；
- codec patent 与 export-control risk 必须和 open-source license compliance 分开审查，包括 H.264、
  H.265/HEVC、AAC、Dolby 系列 codec，以及特定司法辖区义务；
- ViSQOL、VMAF 或类似 perceptual system 的 model license、model weight、training-data notice、
  patent claim、redistribution limit 与 platform support；
- 可选 Python package 的 license、transitive dependency、native extension、wheel/source size、
  supported Python version 与 security advisory；
- fixture provenance：所有音视频 corpus 必须是 synthetic、由脚本生成、public-domain 或明确可再分发；
  generated file 需要 source script、parameter、hash 与 license note；
- restricted competition media、personal recording、unpublished scientific data、proprietary codec 或
  不可再分发的 model output 不得进入仓库。

调用用户已安装的外部 CLI 并不会消除 license、patent 或 export 义务；如果 Platydiff 后续捆绑、
再分发、记录 required build 或依赖 nonfree feature，仍需单独承担这些义务。

## Artifact 与 renderer 边界

首批 audio/video 比较门禁不产生 artifact。有界 waveform PNG、spectrogram、thumbnail、frame capture、
difference heatmap 与 short clip 只有在单独 artifact gate 接受下列内容后才允许：

- RFC 0001 `ArtifactRef` URI validation；
- explicit artifact root 与 no-clobber 或 safe replacement rule；
- deterministic name、media type、hash 与 byte size；
- 有界 dimension、duration、frame count 与 color/sample format；
- media-derived preview 的 privacy warning；
- 证明 renderer 和 UI 只消费 validated outcome 与 artifact reference，绝不消费 original source；
- 任何 human review surface 展示它们时遵循 RFC 0004 presentation rule。

Renderer 只能展示 validated bounded fact。它们不得重读媒体、decode stream、重算 metric、生成
thumbnail、打开文件、获取 remote resource 或重新解释 relation/verdict。UI 工作仍未授权。

## 交付门禁、commit 与测试

以下 gate 是提议计划，不是实现授权。

### P7-A1：audio schema 与 exact decoded PCM relation

1. `feat(core): add audio schema contracts`
2. `feat(audio): add explicit decoded PCM comparison`
3. `feat(cli): add explicit audio comparison commands`
4. `docs: document audio exact comparison contracts`

Gate：选定 schema migration test 通过；既有 v1/v2 与任何已实现 v3 fixture 保持兼容；
`encoded_bytes` 与 `decoded_samples` 保持独立；WAV/PCM 或选定首个 backend 行为已审查；
不存在隐藏 resampling/remixing/gain；empty、single-sample、different、corrupt、unsupported、
over-limit、endianness、sample-format、channel-layout、gapless-delay、timestamp 与 deterministic
repeated-run test 通过。

### P7-A2：audio waveform 与 spectral numeric relation

1. `feat(audio): add explicit waveform numeric policies`
2. `feat(audio): add bounded spectral comparison`
3. `test(audio): add numeric and spectral determinism corpus`
4. `docs: document audio numeric and spectral semantics`

Gate：tolerance formula、offset/drift policy、alignment ambiguity、peak/RMS/SNR、spectral
window/bin、empty-population behavior、NaN/Inf/signed-zero handling、deterministic float
aggregation、resource limit、truncation 与 missing-backend behavior 通过。

### P7-A3：可选 audio perceptual backend

1. `build(audio): add reviewed optional perceptual backend`
2. `feat(audio): add explicitly selected perceptual audio relation`
3. `test(audio): add perceptual backend conformance profile`
4. `docs: document perceptual audio backend limits`

Gate：model/license/patent/platform review 完成；version/model identity、domain applicability、
CPU/GPU variance、score semantics、unavailable/failure behavior 与不 fallback 到 exact relation
均有测试。该 gate 是可选项，不由 P7-A1 或 P7-A2 隐含授权。

### P7-V1：video schema、stream structure 与 decoded frame

1. `feat(core): add video schema contracts`
2. `feat(video): add stream structure comparison`
3. `feat(video): add explicit decoded-frame comparison`
4. `feat(cli): add explicit video comparison commands`
5. `docs: document video stream and frame contracts`

Gate：重新验证 schema migration；stream selection、timebase、timestamp、duration、VFR、frame
reordering、keyframe、edit list、multi-stream inventory、pixel format、bit depth、color metadata、
chroma siting、orientation、alpha、interlacing、corrupt input、unsupported codec、over-limit 与
deterministic repeated run 均通过。

### P7-V2：video frame numeric metric 与 audio-track association

1. `feat(video): add explicit frame numeric comparison`
2. `feat(video): associate selected audio-track outcomes`
3. `test(video): add timeline, color, and audio-track matrix`
4. `docs: document video numeric and audio-track semantics`

Gate：不隐式 resize/crop/frame-rate/color/tone/deinterlace conversion；PSNR、SSIM-style metric、
pixel error、missing/duplicate frame、offset/drift、audio-track sync、deterministic tie-breaking、
output truncation 与 resource limit 通过。

### P7-V3：可选 video perceptual backend

1. `build(video): add reviewed optional perceptual backend`
2. `feat(video): add explicitly selected perceptual video relation`
3. `test(video): add VMAF-style backend conformance profile`
4. `docs: document perceptual video backend limits`

Gate：model/version/license/platform review 完成；CPU/GPU reproducibility、feature extractor
version、score aggregation、unsupported content、unavailable/failure semantics 与无 fallback
均有测试。该 gate 是可选项，不由 P7-V1 或 P7-V2 隐含授权。

### P7-M1：可选 media artifact gate

1. `feat(artifacts): add bounded audio waveform and spectrogram artifacts`
2. `feat(artifacts): add bounded video thumbnail and heatmap artifacts`
3. `docs: document media artifact safety and retention`

Gate：RFC 0001 `ArtifactRef`、RFC 0004 renderer/UI boundary、safe artifact root、deterministic
name、hash verification、media privacy warning、无 source reread、无隐式 UI 与 package-content
check 通过。该 gate 不由任何 comparison gate 隐含授权。

每个 implementation gate 都运行 Ruff format/lint、strict mypy、完整 pytest、build、wheel/sdist
inspection、package-content inspection、documentation link check、变更 package 或外部工具的
dependency/license review，以及 secret/path leak scan。Optional-backend suite 使用 `media` 与
`external` marker；backend 缺失时以明确原因 skip，skipped test 不是 passing evidence。

### 测试矩阵

| 领域 | 必需 case |
| --- | --- |
| Audio exactness | encoded-byte equality/difference、decoded-sample equality/difference、empty input、single-sample change、duration mismatch、channel add/remove/reorder、sample-rate mismatch、sample-format 与 endianness mismatch |
| Audio numeric | tolerance boundary、NaN、Inf、signed zero、clipping/out-of-range decode、peak/RMS/error/SNR、spectral window/bin alignment、offset、drift、ambiguity、repeated-run determinism |
| Video exactness | encoded-byte equality/difference、stream structure change、decoded-frame equality/difference、empty/no-frame stream、single-frame change、missing/duplicate frame、VFR timestamp、edit list、keyframe |
| Video color/pixels | pixel format、bit depth、full/limited range、transfer/primaries/matrix、ICC/HDR metadata、chroma subsampling/siting、alpha、orientation/rotation、interlacing、PSNR/SSIM-style boundary |
| Hostile media | corrupt/truncated file、unsupported codec、malformed container、decode bomb、huge sample rate/channel count、huge resolution/frame count、long duration、packet storm、hang、crash |
| Backends | missing backend、incompatible version、version mismatch、stderr redaction、timeout、exit-code validation、path redaction、有界 stdout/stderr/temp file、无 network/device access |
| Contracts | schema migration fixture、spec/change invariant rejection、metric ordering、non-finite JSON value、启用时 artifact-reference validation、既有 text/binary/auto/plugin/CLI 行为不变 |
| Corpora | synthetic 或明确许可的小型 fixture、source script、hash、provenance note、无受限或个人媒体 |

## 后续 callback

媒体自动探测必须在 RFC 0003 的后继 RFC 中定义有界 magic/extension/MIME/codec probe、probe cost、
ambiguity、pair selection、stream attribution、backend availability interaction，以及 text/binary/media
precedence。

SDK v2 必须先定义 media source service、lifecycle stage、stream view、backend role、model identity、
artifact authority、out-of-process isolation、compatibility receipt 与 schema migration，第三方
audio/video comparator 才能执行。SDK v1.1 仍只支持 text/binary。

Speech recognition、transcription comparison、music information retrieval、scene/object/action
understanding、subtitle、caption、timed metadata、OCR、accessibility track、live stream、camera/
microphone device、encrypted DRM media、adaptive streaming manifest 与 semantic video equivalence
需要单独契约。

更丰富的展示回到 RFC 0004。UI 可以导航 validated audio interval、spectral cell、video frame、
region、stream fact 与 artifact ref，但自身不能 decode、render、compare、transcode、fetch 或生成媒体。

## 参考

- [FFmpeg documentation](https://ffmpeg.org/documentation.html)
- [ITU-R BS.1770 loudness algorithms](https://www.itu.int/rec/R-REC-BS.1770)
- [EBU R 128 loudness recommendation](https://tech.ebu.ch/publications/r128)
- [ViSQOL repository](https://github.com/google/visqol)
- [Netflix VMAF repository](https://github.com/Netflix/vmaf)
