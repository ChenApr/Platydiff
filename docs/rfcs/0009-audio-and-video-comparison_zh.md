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

| `origin/main` `fde2bd4` 上的当前证据 | Phase 7 约束 |
| --- | --- |
| RFC 0001 将 failed/unavailable 执行终态与 completed `DiffResult` 事实分离。 | decode、backend、timeout、resource、sandbox、model 和 rendering 失败不得变成空或伪造的媒体差异。 |
| RFC 0002 要求每个新模态在实现前定义 spec、change、metric、artifact、等价关系、policy、failure 与 gate。 | 本 RFC 只记录契约与门禁，不启动音视频代码工作。 |
| RFC 0003 保持自动探测有界且只对 text/binary 封闭。 | 音视频不参与 auto detection；extension、MIME、magic byte、stream probe 或 codec probe 不得改变既有 auto 行为。 |
| RFC 0003 的 snapshot path 为 path/bytes/text source 管理有界 replay、hash、mutation check 与安全 label。 | 媒体门禁依赖它处理大型或可变媒体前，必须重新验证 snapshot 行为。 |
| RFC 0004 要求 renderer 与 UI 消费 validated outcome，不重读 source 或重算事实。 | 媒体 thumbnail、waveform、heatmap 和 frame preview 需要显式有界 artifact 契约；UI 工作仍未授权。 |
| RFC 0005 实现的 SDK v1.1 只覆盖 text/binary detector、comparator 与 renderer handle。 | 音视频插件需要 SDK-v2 后继 RFC；SDK v1.1 不能引入媒体 spec 或内建媒体 change kind。 |
| RFC 0006 接受 schema v3 用于结构化数据，但后续门禁启动时必须重新验证其实现状态。 | 音视频 schema 决策必须从已实现 v1/v2 和已接受 v3 迁移，不能假设未合并 P4-A1 行为。 |
| RFC 0007 提议 schema v4 作为首个 image slice，前提是通过实际合并的 schema-v3 前驱审计。 | Phase 7 不得与 Phase 5 争用 v4，也不得重开冻结前驱；媒体需要单独的全局 schema successor。 |
| RFC 0008 提议 source-code/PDF 契约，现协调为 schema v5，并保持重量级后端、artifact、auto detection 和 SDK v2 分离。 | Phase 7 使用下一个全局 successor schema v6。媒体也采用同样分离：后端和可选 artifact 是独立门禁。 |
| 当前运行时依赖为空；音视频后端仍是架构层计划。 | 任何依赖或 subprocess path 进入前，必须审查 codec、model、patent、export 与 FFmpeg build/license 影响。 |
| P4-A1 和 Phase 5 实现工作仍可能缺失，或与 `main` 分歧。 | 只能把这些工作当作设计证据；本文中所有依赖代码状态的假设都是后续 revalidation gate。 |

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
- 与已实现 v1/v2、实际 P4 schema-v3 前驱、Phase 5 schema-v4 预留和 Phase 6 schema-v5 预留兼容，并在实现开始时重新验证。

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
| P7X3 | 审计实际 P4 schema-v3 前驱、Phase 5 schema-v4 预留和 Phase 6 schema-v5 预留后，使用全局分配的 schema v6 media successor。 | 扩展 v1/v2 closed union、重开 v3、复用 image v4 或 source/PDF v5，或假设已接受但未实现的前驱细节。 |
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

Phase 7 使用全局分配的 schema v6 media successor。分配顺序是稳定人工决策：P4 structured data
使用 schema v3，P5 image 使用 schema v4，P6 source/PDF 使用 schema v5，P7 audio/video 使用
schema v6。Design、backend、dependency 与 fixture research 可以跨 phase 并发推进，但 public
schema implementation 与 merge 必须遵守此前驱顺序及其兼容性 fixture。后续实现门禁必须重新验证
`main` 状态，并在仓库级 schema ledger 中记录最终 schema 编号后才可写代码。它不得重开 schema
v3、占用 schema v4 或 v5，或与其他模态并行分配冲突的 successor。

媒体 successor 是实际合并前驱链的 additive semantic successor：

```python
CompareSpecV6 = CompareSpecV5 | AudioCompareSpec | VideoCompareSpec
ChangeV6 = ChangeV5 | AudioChange | VideoChange
```

如果 P4-A1 schema v3 没有在 `main` 上实现、实际实现与 RFC 0006 不一致，或 Phase 5 schema
v4 缺失或改变其分配，或 Phase 6 schema v5 缺失或改变其分配，Phase 7 实现门禁必须停止并先
修订本文。媒体 schema 工作依赖真实的 v3/v4/v5 reader、writer、upgrader 与 fixture，而不是只依赖
已接受的设计文本。无论哪种情况：

- 既有内建 text、binary 与 auto 调用保持 schema v1；
- 既有 `PluginHost` text/binary 调用保持 schema v2；
- 已合并 Phase 4 structured-data 调用保持实际实现的 schema v3；
- 已合并 Phase 5 image 调用保持 schema v4；
- 已合并 Phase 6 source/PDF 调用保持 schema v5；
- audio/video 内建 spec 使用选定媒体 successor，即使 validation、sourcing、resolution、decode
  或 backend 阶段失败也是如此；
- 选定媒体 reader 接受 v1/v2/v3/v4/v5/v6 payload，并先按显式 schema version 分派，
  再检查 spec 或 change kind；
- v1/v2/v3/v4/v5-to-v6 upgrader 保留原始事实，只加入文档化的中性默认值，例如空媒体字段集合；
- byte-stable v1/v2 fixture、P4 schema-v3 fixture、P5 schema-v4 fixture、P6 schema-v5 fixture 与
  新的 media round-trip fixture 保持在兼容性 corpus 中；
- 每个新的 media fixture 都包含期望 JSON schema version、public spec/change name、metric name、
  ordering、omitted/null field 与 failure reason code；
- audio/video outcome 不存在自动 downgrade。只有 media-free result 的事实能由目标前驱表示时，
  才允许 lossless helper downgrade；不得丢弃或汇总 audio/video spec、change、fact、metric、
  transformation 或 artifact 来适配旧 schema；
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
| 已合并 Phase 4 path | v3 | 显式 json/yaml/table/array | 无 | 实际 v3 model、migration 与 fixture 是前驱。 |
| 提议中的 Phase 5 image path | v4 | 显式 static PNG image | 无 | 媒体不得复用 v4，也不得要求 image 实现改变。 |
| 提议中的 Phase 6 source/PDF path | v5 | source-code/PDF | 单独授权前无 | 前驱 schema 预留；design evidence 可并发推进，但 media merge 等待 v5 fixture。 |
| 提议中的 Phase 7 audio path | v6 | 显式 audio | 首批门禁无 | 产生 validated audio spec、change、metric、transformation 与 failure。 |
| 提议中的 Phase 7 video path | v6 | 显式 video | 首批门禁无 | backend 与 worker contract 冻结前保持 pending。 |
| 对 media-looking bytes 使用既有 auto | v1 | 仅 text 或 binary | 仅既有规则 | detection evidence 与 result 不变。 |
| 未来 SDK v2 或 media auto | 未指定 | 未指定 | 未指定 | 需要后继 RFC。 |

## Relation、view 与 evaluation 不变量

Audio `relations` 与 video `views` 是以 tuple 编码、用于稳定 JSON 的规范集合。它们必须非空、
不得重复、拒绝未知值，并在序列化输出中规范化为 canonical order。Audio canonical order 为
`encoded_bytes`、`decoded_samples`、`waveform_numeric`、`spectral`、`perceptual`。Video canonical
order 为 `encoded_bytes`、`stream_structure`、`decoded_frames`、`frame_numeric`、
`perceptual_video`、`audio_tracks`。空集合、重复值或门禁外值都是 invalid spec，不是 no-op。

每个选中的 relation 或 view 产生一条 evaluation record，包含自己的 relation/view name、作为事实的
metric、threshold/policy decision、verdict、fidelity、completeness、transformation、warning 与可选
failure stage。Metric record 只表示测量；pass/fail decision 存在于 evaluation record 中，并可按名称和
稳定 ID 引用 metric。Evaluation record 按 canonical relation/view order 排序，且不重算或重新解释 metric。

一个 completed `DiffResult` 只有一个 overall `relation`、`verdict`、`fidelity` 与 `completeness`。
只有所有选中 evaluation 都是 equal/pass，overall relation 才是 equal。任一选中 evaluation 为
different/fail 时，overall 为 different/fail。Overall fidelity 取最差 selected fidelity；首批媒体门禁
只允许 full fidelity。任一 selected evaluation 在 full count 与 overall relation 已知后被截断时，
overall completeness 为 `truncated`；否则为 `complete`。`partial` 不在 Phase 7 首批门禁授权范围内。

以下示例属于契约：

- encoded bytes 不同但 decoded samples 相同：只选择 `decoded_samples` 时 overall equal/pass；
  同时选择 `encoded_bytes` 与 `decoded_samples` 时，有一条 encoded evaluation different，overall
  different/fail。
- decoded video frame 相同但选中的 audio-track evaluation 不同时，`decoded_frames` evaluation pass，
  `audio_tracks` evaluation fail，overall video result 为 different/fail。
- 如果选中的 audio-track backend 在产生 evaluation 前不可用或失败，外层 outcome 是记录 lifecycle
  stage 的 `unavailable` 或 `failed`，而不是 completed video equality result。

## 音频比较契约

### Public intent

提议的首个 public shape 是一个稳定 schema family，但 P7-A1 只公开下列首批 exact relation。
后续门禁只有在各自审查后，才可激活保留字段。

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

P7-A1 public option 冻结为以下 JSON name 与 invariant：

| Field | 首批门禁不变量 |
| --- | --- |
| `kind` | 必填 string，且只能是 `audio`。 |
| `relations` | 必填或默认的非空 tuple，规范化到首批子集 `encoded_bytes` 与 `decoded_samples`；重复值和后续门禁值非法。 |
| `stream.index` | 默认 audio stream 用 `null`，或显式选择 zero-based integer；backend default 不得静默选择其他 stream。 |
| `decode.backend` | 必填或默认 string，P7-A1 只能是 `stdlib_wave_pcm`。 |
| `decode.sample_representation` | 必填或默认 string，只能是 `native_pcm_integer`；exact decoded equality 不包含 integer-to-float conversion。 |
| `alignment.mode` | P7-A1 为 `sample_index`；下文定义 `fixed_offset`，但须等 P7-A2 才可启用。 |
| `artifact_policy` | P7-M1 前始终为 `none`；artifact gate 前 `record_refs` 非法。 |
| `limits.*` | 非负 JSON integer，且在 safe integer 范围内；`null`、boolean、负数与 non-finite number 非法。 |

首批 source kind 是 `PathSource` 与 `BytesSource`。除非后续门禁定义显式字节编码 relation，
`TextSource` 对 audio 不受支持；不支持的 source 返回 `failed/source_type_unsupported`。

Relation 含义彼此独立：

- `encoded_bytes` 复用精确二进制语义，不说明 decoded signal 是否等价；
- `decoded_samples` 在显式选择 sample representation 后，精确比较选中 decoded PCM stream；
- `waveform_numeric` 预留给 P7-A2；它使用显式 numeric tolerance 比较 aligned sample，并报告 sample-domain error metric；
- `spectral` 预留给 P7-A2；它比较显式 windowed spectrum，不能推出 sample equality；
- `perceptual` 预留给 P7-A3；它使用命名的可选 perceptual backend，不能覆盖 exact 或 spectral difference。

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
    fixed_offset_samples: int = 0
    max_search_offset_samples: int = 0
    max_drift_ppm: float = 0.0
    ambiguity_margin_samples: int = 0
```

`fixed_offset_samples` 是按选中 stream sample rate 计量的有符号 sample；正值表示 after stream
开始晚于 before，比较时向前移动。`max_search_offset_samples` 是 correlation search 的绝对 sample
预算。`max_drift_ppm` 是比较区间内 sample-clock drift 的百万分率。`ambiguity_margin_samples`
是 best 与 second-best alignment candidate 之间的整数 sample-distance margin；落在 margin 内即为
ambiguous。

Offset 与 drift compensation 是 transformation，需记录参数、观测估计、tie-break order 以及 confidence
或 ambiguity fact。Timeline candidate 按 exact timestamp match、较小 absolute offset、较小 absolute
drift、较小 before coordinate、较小 after coordinate 排序。Correlation candidate 按较高 deterministic
score、较小 absolute offset、较小 absolute drift、较小 before coordinate、较小 after coordinate 排序。
如果两个 alignment 在配置 margin 下不可区分、drift 超过 policy，或 search budget 耗尽，outcome
对 budget exhaustion 使用 `failed/compare_resource_limit`，对无法使用的 decoded timing fact 使用
`failed/decode_error`，而不是近似完成的 equality claim。Media-specific `alignment_failed` problem
code 需要后续 RFC 0001 registry update 后才可使用。

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

Audio coordinate 使用 stream index、zero-based channel index 或稳定 channel label、sample interval、
timestamp interval，以及适用时的 spectral bin/time cell。Change 是 observation，不是 patch。
只有 relation、metric 与 total change count 已知后，才可执行 detail truncation。

首批门禁的 `AudioCoordinate` wire shape 固定为 JSON object field：`stream_index`、`channel_index`、
`channel_label`、`sample_start`、`sample_count`、`time_start_seconds` 与
`time_duration_seconds`。Stream 与 channel index 都是 zero-based integer。除非选中 source 具有稳定
label，否则 `channel_label` 为 `null`。Sample interval 是 half-open 且非负。只有 timestamp fact
可用时，time field 才以 finite JSON number 的 decimal seconds 编码；否则为 `null`。

首批门禁的 `AudioFact` wire shape 限定为 JSON object field：`name`、`value`、`unit`、
`stream_index` 与 `coordinate`。`value` 是 string、integer、finite number、boolean 或 `null`；
array 与 nested object 需要后续 schema revision。`AudioChange` record 按 relation、operation、
before coordinate、after coordinate、digest 排序。`sample_update` 要求两个 coordinate 与两个 digest；
`sample_insert` 只要求 after coordinate；`sample_delete` 只要求 before coordinate。`metadata_update`
要求 fact 且 coordinate 为 null。Digest 是带 algorithm prefix 的 lowercase hex string；只有 operation
没有 byte/sample payload 时才可为 `null`。

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

Metric 是事实，不是 verdict。每个 metric record 只包含 stable name、numeric value、unit、direction、
aggregation method 与 source evaluation ID。Policy evaluation 包含 threshold、tolerance formula、
inclusive/exclusive boundary rule 与 pass/fail verdict。Renderer 不得直接从 metric value 推断 pass/fail。

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

对于使用 `stdlib_wave_pcm` 的 P7-A1，这些是 proposed normative default value。Implementation 仍需
benchmark gate 证明它们 deterministic、bounded 且 practical，但接受 P7-S0/audio decision 不再延后
这些 default value 本身。Limit check 必须在 allocation、decode、packet expansion、metadata
materialization、comparison work 或 temp-file write 之前执行。Limit 值为 `0` 表示该资源没有预算：
zero decoded bytes 只接受选中 relation 不需要 decoded byte 的输入；zero duration 只接受
zero-duration decoded stream；zero packets 拒绝任何会读取 packet 的 stream；zero change items 仍计算
overall relation 与 total count，但输出 truncated empty change list。`max_resident_buffer_bytes` 限制
live decoded/sample buffer，而不只是 total output bytes。`max_materialized_bytes` 限制传给 backend 的
host-owned snapshot 与 temporary materialization。所有 counter 都是 monotonic，并在 chunk boundary
先检查再预留下一个 buffer。

Corrupt、truncated、unsupported-codec、hostile-container、over-duration、huge-sample-rate、
huge-channel-count、decode-bomb、infinite stream、packet-storm、metadata-bomb、backend-hang、
backend-crash 和 over-output 都是必测 case。Backend 不可用是 `unavailable/backend_unavailable`；
unsupported codec 或 profile 是 `unavailable/capability_unavailable`，除非选定 decoder 已启动后失败，
此时按实际观测 failure 返回 `failed`。

## 视频比较契约

### Public intent

提议的 video shape 仍只是 schema proposal。P7-S0 窄化 candidate first public field，但 P7-V1 在
后续 review 冻结 video backend 与 worker protocol 前不授权实现。

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

如果后续门禁授权实现，candidate P7-V1 public option 冻结为以下 JSON name 与 invariant：

| Field | 首批门禁不变量 |
| --- | --- |
| `kind` | 必填 string，且只能是 `video`。 |
| `views` | 必填或默认的非空 tuple；只有在 backend 冻结后才可规范化到 P7-V1 子集 `encoded_bytes`、`stream_structure` 与 `decoded_frames`。在此之前所有 video view 都只是 documentation-only。重复值和后续门禁值非法。 |
| `streams.video_index` | 显式定义的默认 video stream 用 `null`，或 zero-based integer。Backend default stream choice 不足够。 |
| `streams.audio_indexes` | 只在选择 `audio_tracks` 时使用的 zero-based integer tuple；empty 表示不比较 audio track，不表示 all tracks。 |
| `decode.backend` | 本 RFC revision 不授权默认 backend。P7-V1 写代码前必须命名已审查 backend 与 version profile。 |
| `timeline.mode` | Exact decoded frame 使用 `presentation_timestamp`，除非后续门禁授权 fixed-offset 或 fingerprint alignment。 |
| `spatial.mode` | `exact_geometry`；resize、crop、rotate、deinterlace、tone-map 与 color conversion 都是非法首批 transform。 |
| `artifact_policy` | P7-M1 前始终为 `none`；artifact gate 前 `record_refs` 非法。 |
| `limits.*` | 非负 JSON integer，且在 safe integer 范围内；`null`、boolean、负数与 non-finite number 非法。 |

`encoded_bytes` 复用精确二进制语义。`stream_structure` 比较 container 和 stream layout、codec
parameter、packet index、timebase、metadata、edit list、keyframe、attachment、chapter 与选定
side data。`decoded_frames` 只有在 backend 冻结后才比较显式 decoded frame sequence 与 timestamp。
`frame_numeric` 预留给 P7-V2，并允许显式 pixel tolerance。`perceptual_video` 预留给 P7-V3，
作为可选 model/backend gate。`audio_tracks` 预留给 P7-V2；一旦授权，它委托 audio contract，并记录
video timeline association，且绝不静默丢弃 track。

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

Video `fixed_offset_ticks` 是以选中 stream timebase 计量的有符号 tick；正值表示 after timeline
开始晚于 before，比较时向前移动。Duration delta 同时以 seconds 与原始 timebase tick 报告。Timeline
matching 按 exact presentation timestamp、较小 absolute offset ticks、较小 absolute drift ppm、
较小 stream index、较小 before frame ordinal、较小 after frame ordinal 排序。Feature 或 fingerprint
matching 必须定义 score unit，并用相同 score unit 定义 ambiguity margin；tie 退回上述 timeline order。

Missing frame、duplicate frame、duplicate timestamp、dropped frame、inserted frame、stream add/remove
和 drift 是一等 observation 或 failure。任何 frame matching policy 都必须指定确定性 tie-break。
Ambiguity、unsupported timestamp structure 或 alignment 超预算对 budget exhaustion 使用
`failed/compare_resource_limit`，对无法使用的 decoded timing fact 使用 `failed/decode_error`，不是隐藏的
内容差异。Media-specific `alignment_failed` problem code 需要后续 RFC 0001 registry update 后才可使用。

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

Candidate `VideoCoordinate` wire shape 固定为 JSON object field：`stream_index`、`frame_index`、
`pts`、`timebase_num`、`timebase_den`、`time_seconds`、`x`、`y`、`width`、`height`、`plane`
与 `audio_coordinate`。Frame index 是 zero-based。Pixel rectangle 是 half-open、非负，并且只有选择
decoded-frame 或 frame-numeric view 时有效。`pts` 是选中 stream timebase 中的 integer timestamp。
`time_seconds` 是从 `pts` 派生的 finite number，仅作为展示辅助；equality 使用 tick。
`audio_coordinate` 只有在 `audio_tracks` view 记录 delegated audio observation 时非 null。

Candidate `VideoFact` wire shape 限定为 JSON object field：`name`、`value`、`unit`、`stream_index`
与 `coordinate`。`value` 是 string、integer、finite number、boolean 或 `null`；array 与 nested
object 需要后续 schema revision。`VideoChange` record 按 view、operation、before coordinate、
after coordinate、digest 排序。Frame 与 region update 要求两个 coordinate 与两个 digest。
Insert/delete operation 只要求存在侧的 coordinate。Stream 与 metadata update 要求 fact，frame
coordinate 可为 null。

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
| `video.audio_tracks_changed` | delegated relation 为 different 或 timeline association fact 改变的 selected audio track 数量 | `tracks` | `lower_is_better` | `count` | zero |

Metric 是事实，本身绝不定义 policy。Per-view evaluation 引用 metric，并包含 threshold、tolerance、
inclusive boundary、verdict、fidelity 与 completeness。`video.audio_tracks_changed` 统计 observed
delegated relation difference 或 association fact change；它不依赖 pass/fail policy，不复制 audio
metric，也不重新解释 audio evaluation verdict。

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

Video resource value 在 P7-V1 backend amendment 冻结 backend 与 worker profile 前是 non-normative
planning placeholder。接受 P7-S0 或 audio default 不会冻结这些 video default。完成 amendment 后，
limit check 必须在 allocation、decode、packet expansion、metadata materialization、frame buffering、
comparison work 或 temp-file write 之前执行。Limit 值为 `0` 表示该资源没有预算：zero frames 拒绝
任何包含 frame 的 decoded-frame view；zero decoded bytes 只允许不需要 decoded frame 的 view；zero
packets 拒绝 packet read；zero change items 仍计算 overall relation 与 total count，但输出 truncated
empty change list。`max_resident_buffer_bytes` 限制 live decoded frame/audio buffer；
`max_total_decoded_bytes` 限制累计 decoded media；`max_materialized_bytes` 限制 host-owned snapshot 与
temporary materialization。Counter 都是 monotonic，并在 chunk/frame boundary 先检查再预留下一个
buffer。

Adversarial test 包括 malformed container、unsupported codec、resolution bomb、huge frame count、
long duration、many stream、packet storm、metadata bomb、decompression bomb、infinite/non-terminating
stream、corrupt frame、timestamp wraparound、backend hang、backend crash、excessive stdout/stderr
和 temp-output explosion。

## 后端与执行边界

首个 audio backend 固定为 Python 3.12 标准库 WAV parsing，只支持 uncompressed PCM WAV，并公开为
`stdlib_wave_pcm`。它只消费 host-owned snapshot bytes 或 materialized file，记录 `wave` module
capability profile，并将 compressed codec 或 unsupported WAV variant 拒绝为
`unavailable/capability_unavailable`。本 RFC 不选择 video backend。P7-V1 保持 pending，在后续
review 冻结 backend、worker isolation、materialization format 与 conformance profile 前，不授权
video worker。

其他标准库能力仅限精确 encoded-byte 比较。可选 Python library 只有在完成 dependency、license、
size、platform、native-code 和 security review 后，才可处理 metadata 或 numeric array。`ffprobe`、
`ffmpeg` 或 model runner 等外部程序是独立 backend role，需要自己的 conformance profile。

所有 backend role 只消费 host-owned immutable snapshot 或 materialization。Snapshot 可用时，不得把
调用者 original path 传给 backend；不得 dereference URL、playlist、manifest、device、逃出 snapshot
root 的 symlink，或 media metadata 产生的 path。Protocol allowlist 必须显式；首批门禁只允许本地
host file descriptor 或 `file` materialization。Network protocol、remote resource、camera/microphone
capture、hardware device 与 host temp/artifact root 之外的 writable output path 均被禁止。

每次 external program invocation 必须使用：

- argument array 与 `shell=False`；
- 不把 untrusted input 插入 command string；
- close-on-exec descriptor 与有界 temporary directory；
- 显式 timeout、terminate/kill escalation、child-process reaping，以及所有 exit path 上的 temp cleanup；
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

### Lifecycle stage 与 failure

| Stage | 责任 | Failure 或 unavailable reason |
| --- | --- | --- |
| `validating` | 验证 schema version、relation/view set、public option name、nullability、ordering 与 limit value。 | `failed/invalid_spec` |
| `sourcing` | 获取 immutable host-owned source bytes、label、hash、mutation check 与有界 materialization。 | `failed/source_not_found`、`failed/source_type_unsupported`、`failed/source_changed`、`failed/resource_limit_exceeded`、`failed/io_error` |
| `resolving` | 选择匹配请求 relation/view 与冻结 capability profile 的 backend。 | `unavailable/backend_unavailable`、`unavailable/capability_unavailable` |
| `decoding` | 在 limit 内解析 container packet、metadata、sample、frame、timestamp、side data 与 backend decode output。 | `failed/decode_error`、`failed/resource_limit_exceeded`、`failed/io_error` |
| `normalizing` | 构建显式 IR，并记录每个请求的 representation transform。不支持的 requested transform 应更早在 `validating` 拒绝。 | `failed/decode_error`、`failed/resource_limit_exceeded`、`failed/internal_error` |
| `aligning` | 确定性匹配 sample、timestamp、frame、stream 或 delegated audio track。 | `failed/compare_resource_limit`、`failed/decode_error` |
| `comparing` | 产生 policy-neutral metric 与 change observation，且不改变 policy semantics。 | `failed/compare_resource_limit`、`failed/io_error`、`failed/internal_error` |
| `aggregating` | 构建 per-relation/view evaluation 与唯一 overall result。 | `failed/internal_error` |

P7-S0 不引入新的 problem code。Media implementation 只有通过单独 RFC 0001 registry update 固定
status、HTTP-style code、合法 stage 与 JSON fixture 后，才可增加 `alignment_failed`、`timeout`
或 `unsupported_transform` 等 code。在此之前复用上方 RFC 0001/RFC 0003 code。Renderer execution
位于 `CompareOutcome` 之外；renderer failure 不得改写已经完成、unavailable 或 failed 的比较 outcome。

Failed 或 unavailable outcome 记录达到的最深 public stage、已知 backend role、适用时的 limit name，
以及是否 terminate、kill、reap 或 cleanup 过 child process。Completed media outcome 不得把 stage
failure 隐藏在 empty change list 中。

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

首批 audio/video 比较门禁不产生 artifact，且只公开 `artifact_policy="none"`。P7-M1 或后继
artifact gate 接受前，任何其他 artifact policy value 都是 invalid。有界 waveform PNG、spectrogram、
thumbnail、frame capture、difference heatmap 与 short clip 只有在单独 artifact gate 接受下列内容后才允许：

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

Gate：schema-v6 media migration test 基于实际 v3/v4/v5 前驱链通过；既有 v1/v2/v3/v4/v5 fixture
保持兼容；`encoded_bytes` 与 `decoded_samples` 保持独立；唯一首个 backend 是针对 uncompressed
PCM WAV 的 `stdlib_wave_pcm`；不存在隐藏 resampling/remixing/gain 或 integer-to-float conversion；
empty、single-sample、different、corrupt、unsupported、over-limit、limit-zero、endianness、
sample-format、channel-layout、gapless-delay、timestamp、host-owned materialization 与 deterministic
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

P7-S0 之后，P7-V1 有意保持 pending。本 RFC revision 没有冻结 video backend 或 worker profile，
因此不授权任何 video implementation commit。

1. `docs: freeze video backend and worker conformance profile`
2. `feat(core): add video schema contracts`
3. `feat(video): add stream structure comparison`
4. `feat(video): add explicit decoded-frame comparison`
5. `feat(cli): add explicit video comparison commands`
6. `docs: document video stream and frame contracts`

Gate：重新验证 schema migration；stream selection、timebase、timestamp、duration、VFR、frame
reordering、keyframe、edit list、multi-stream inventory、pixel format、bit depth、color metadata、
chroma siting、orientation、alpha、interlacing、corrupt input、unsupported codec、over-limit、
limit-zero、host-owned materialization、backend timeout kill/reap/cleanup 与 deterministic repeated
run 均通过。如果首个 video backend 或 worker protocol 无法冻结，P7-V1 保持 documentation-only
且独立 pending。

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
| Hostile media | corrupt/truncated file、unsupported codec、malformed container、decode bomb、huge sample rate/channel count、huge resolution/frame count、long duration、packet storm、metadata bomb、limit-zero case、hang、crash |
| Backends | missing backend、incompatible version、version mismatch、只使用 host-owned snapshot/materialization、protocol/device allowlist、stderr redaction、timeout terminate/kill/reap、temp cleanup、exit-code validation、path redaction、有界 stdout/stderr/temp file、无 network/device access |
| Lifecycle | canonical `validating`、`sourcing`、`resolving`、`decoding`、`normalizing`、`aligning`、`comparing` 与 `aggregating` stage failure，包含 stable reason code，且 stage failure 不得产生 completed equality；renderer failure 保持在 `CompareOutcome` 之外 |
| Contracts | media schema-successor migration fixture、继承 v1/v2/v3/v4 fixture、spec/change invariant rejection、relation/view set ordering、metric/evaluation separation、non-finite JSON value、启用时 artifact-reference validation、既有 text/binary/auto/plugin/CLI 行为不变 |
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
