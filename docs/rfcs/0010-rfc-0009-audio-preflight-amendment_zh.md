# RFC 0010：RFC 0009 Audio Preflight Amendment

[English documentation](0010-rfc-0009-audio-preflight-amendment.md)

- Status: Proposed
- Date: 2026-09-10
- Amends: [RFC 0009](0009-audio-and-video-comparison_zh.md)
- Owners: Platydiff 维护者
- Implementation owner: 尚未指派，等待单独的实现授权

## 摘要与授权边界

本 RFC 提议为 RFC 0009 增加 P7-A1 audio implementation preflight blocker
修订。它不是 Accepted，不授权代码、依赖变更、FFmpeg、artifact、UI、SDK v2、自动媒体
探测、video implementation，或独立 schema renumbering。

本修订保留 RFC 0009 的所有前驱门禁，并把全局 schema numbering 交给 pending human-approved
predecessor resolution。只有该全局 resolution 仍让 RFC 0009 留在已接受 audio path 上时，audio
才是首个 media schema successor；本 amendment 不独立选择或重编号 v4、v5 或 v6。必须从当前
`main` 复验 P4-A1 JSON/schema-v3，且 P7-A1 仍被阻塞，直到全局 predecessor resolution、前驱
implementation 与 compatibility fixture 可用。Video 仍只是 roadmap-only，并等待单独的
backend/worker amendment 和下一个 schema successor。

## 推荐决策

这些 ID 是提议建议。只有本 amendment 被明确接受后，它们才成为实现契约。

| ID | 推荐决策 | 未选择的替代方案 |
| --- | --- | --- |
| P7A-AM1 | 冻结 stream selection、decode、waveform、spectral 与 perceptual option 的 public audio wire shape、default、key order 与 unknown-key rejection。 | 让 option object 保持部分隐式，并从实现 default 推断行为。 |
| P7A-AM2 | 将 encoded-byte difference 表示为 `AudioChange`，并通过 `MediaViewEvaluation` 关联 metric/evaluation，不破坏 homogeneous `ChangeSet`。 | 增加另一种 encoded-byte change type，或在 change 中嵌入 evaluation identifier。 |
| P7A-AM3 | 冻结 P7-A1 `stdlib_wave_pcm` WAV/PCM profile，包括 RIFF/RIFX classification、classic PCM 与 WAVE_FORMAT_EXTENSIBLE、bit depth、valid bits、channel mask、`fmt` extra、data chunk、padding 与 trailing chunk。 | 让标准库 decoder 自行决定哪些 WAV variant 等价。 |
| P7A-AM4 | 增加有界 pre-resolution WAV profile probe，使 valid-but-unsupported profile 在 decode 开始前以稳定 problem detail 于 `resolving` 失败。 | 将所有 unsupported-but-valid WAV profile 报告为 decoding failure。 |
| P7A-AM5 | 定义 timestamp、encoder delay/padding 与 channel layout fact 的 absence 和 unknown 语义。 | 将 absent fact 当作 zero、empty，或作为 result 外部的 backend metadata。 |
| P7A-AM6 | 冻结 change grouping、coordinate meaning、digest framing、fact name、unit、ordering，以及稳定 rule/comparator/algorithm/transformation/resource ID。 | 让 renderer 或测试从 prose 推断 grouping 与 identifier。 |
| P7A-AM7 | 冻结 duration 与 timebase binary64 determinism，同时保留精确 rational fact。 | 允许平台相关 float formatting 或 extended precision。 |
| P7A-AM8 | 冻结首批 CLI flag，并要求 SDK-v1 plugin audio flag 在 plugin execution 前被拒绝。 | 让 generic plugin 或 media flag 进入 SDK v1.1 host。 |
| P7A-AM9 | 冻结 P7-A1 failure 的 stable problem detail key、value type、ordering 与 omission rule。 | 透传 backend-specific detail dictionary。 |
| P7A-AM10 | 让 audio schema successor 取决于 pending global predecessor resolution 对 schema v3/v4/v5/v6 numbering 的处理。 | 在这个 audio-specific amendment 中解决 cross-RFC closed-union numbering。 |

## Wire shape 与解析规则

所有 option object 都是 closed-key JSON object。Unknown key 非法。Key 必须按下列顺序序列化。
schema-v6 reader 在比较前插入 default；omitted field 只有在等同于文档化 default 时才等价。

### `AudioStreamSelection`

Key order 与 default：

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `stream_index` | 非负 integer | `0` | 解码前选择 audio stream。P7-A1 拒绝没有该 stream 的文件。 |
| `channel_mode` | `"all"` 或 `"indices"` | `"all"` | `"all"` 按文件顺序选择所有 decoded channel。 |
| `channel_indices` | 非负 integer tuple | `[]` | `channel_mode="all"` 时必须为空；`"indices"` 时必须非空、唯一且升序。 |
| `require_channel_labels` | boolean | `false` | 为 true 时，unknown channel label 在 `validating` 失败。 |

### `AudioDecodeOptions`

Key order 与 default：

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `backend` | string | `"stdlib_wave_pcm"` | P7-A1 唯一 backend。 |
| `profile` | string | `"p7_a1_wav_pcm"` | 选择下文有界 WAV/PCM profile。 |
| `unsupported_profile` | `"unavailable"` | `"unavailable"` | valid-but-unsupported profile 产生 `unavailable/capability_unavailable`。 |
| `preserve_integer_width` | boolean | `true` | Decoded sample 保留 signedness、container width 与 valid-bit fact。 |
| `max_probe_bytes` | 非负 integer | `65536` | resolving-stage profile probe 的上限。 |

### `AudioWaveformOptions`

Key order 与 default：

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `enabled` | boolean | `false` | P7-A1 保持 waveform numeric relation 禁用。 |
| `sample_metric` | string | `"absolute_error"` | 保留的首个 waveform metric name。 |
| `atol` | finite JSON number | `0.0` | 后续 gate 启用该 relation 时的 absolute tolerance。 |
| `rtol` | finite JSON number | `0.0` | 后续 gate 启用该 relation 时的 relative tolerance。 |
| `alignment_mode` | string | `"sample_index"` | 其他 mode 需要 P7-A2。 |

### `AudioSpectralOptions`

Key order 与 default：

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `enabled` | boolean | `false` | P7-A1 保持 spectral relation 禁用。 |
| `window_function` | string | `"hann"` | 保留值；P7-A1 不计算。 |
| `window_size` | positive integer | `2048` | 保留值。 |
| `hop_size` | positive integer | `512` | 保留值，且必须 `<= window_size`。 |
| `fft_size` | positive integer | `2048` | 保留值，且必须 `>= window_size`。 |
| `power_scale` | `"power"` 或 `"db"` | `"power"` | 保留值。 |

### `AudioPerceptualOptions`

Key order 与 default：

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `enabled` | boolean | `false` | P7-A1 保持 perceptual relation 禁用。 |
| `backend` | string 或 null | `null` | 非 null 需要后续 optional backend gate。 |
| `model` | string 或 null | `null` | 非 null 需要后续 optional backend gate。 |
| `score_name` | string 或 null | `null` | 非 null 需要后续 optional backend gate。 |
| `license_acknowledged` | boolean | `false` | 不授权 model 使用。 |

## Encoded-byte change 与 evaluation 关联

`encoded_bytes` 仍是 audio relation。它使用 homogeneous `AudioChange`，其中
`operation="encoded_byte_update"`、`operation="encoded_byte_insert"` 或
`operation="encoded_byte_delete"`。Coordinate 使用 source snapshot 中的 absolute byte offset，
不是 decoded sample coordinate。Payload 携带 `before_digest`、`after_digest`、`byte_start`、
`byte_end` 与 `byte_count`。大型 byte range 按既有 change payload limit 使用 digest 与有界 snippet
摘要。

`ChangeSet` 保持 homogeneous：audio result 只包含 `AudioChange`。Relation-level association 记录在
`DiffResult.media_evaluations`：每个 `MediaViewEvaluation` 列出 relation、selector、
`metric_names`、`change_count`、`policy_rule_ids` 与 `transformation_ids`。Change 绝不包含
evaluation ID，metric 也不包含 source evaluation ID。

## P7-A1 WAV/PCM profile

`p7_a1_wav_pcm` profile 使用有界 resolving-stage probe 识别 RIFF-family WAV container。分类如下：

- `RIFF` + `WAVE` 是唯一可解码 container form；
- `RIFX` + `WAVE` 是有效 RIFF-family WAV，但 P7-A1 不支持；
- 其他 form identifier 根据 RIFF 结构是否仍有效，归类为 unsupported 或 corrupt。

唯一可解码 sample encoding 是：

- classic `WAVE_FORMAT_PCM`（`wFormatTag=0x0001`），`fmt ` chunk size 为 16，无 extra，
  container bits 为 8、16、24 或 32；
- `WAVE_FORMAT_EXTENSIBLE`（`wFormatTag=0xFFFE`），`fmt ` chunk size 为 40，
  `cbSize=22`，PCM subformat GUID，valid bits 从 1 到 container bit width，container bits 为
  8、16、24 或 32。

8-bit PCM 是 unsigned。16/24/32-bit PCM 是 signed two's complement little-endian integer。
24-bit PCM 每个 sample 正好打包为 3 byte。IEEE float、A-law、mu-law、ADPCM、extensible
non-PCM GUID、big-endian `RIFX` sample byte 与 compressed profile 是 valid but unsupported；
header malformed 时则为 corrupt。

`nBlockAlign`、`nAvgBytesPerSec`、channel count、sample rate、container bits、valid bits 与
channel mask 必须内部一致。Classic PCM 的 channel label unknown，channel 有序。
WAVE_FORMAT_EXTENSIBLE 且 mask 非零时，从 mask 记录 label；zero mask 记录 unknown label 与
ordered channel。Valid bits 记录为 fact，不会静默 mask stored container bit。

必须正好有一个 `fmt ` chunk，且至少有一个 `data` chunk。多个 `data` chunk 是 valid but unsupported
for P7-A1。单个 `data` chunk 后可以跟 well-formed non-audio chunk；它们的 chunk ID 与 byte size
记录为 metadata fact，但不参与 decoded sample。Odd-sized chunk 的 RIFF pad byte 被忽略。Chunk
外的非零 trailing byte、truncated chunk header、超过文件长度的 chunk size、或 `data` 早于 `fmt `
都是 corrupt input。

## Resolving 与 decoding 边界

有界 pre-resolution probe 只读取 RIFF header、chunk header、第一个 `fmt ` chunk，以及不超过
`max_probe_bytes` 的 data-chunk inventory。Unsupported-but-valid profile 按如下方式失败：

```text
outcome=unavailable
stage=resolving
code=capability_unavailable
```

Malformed RIFF/WAV structure 根据第一个证明 corruption 的阶段返回 `failed/sourcing_error` 或
`failed/decode_error`。Decode 开始后，禁止 fallback 到 bytes、另一 backend、另一 profile 或
perceptual relation。

## Absence 与 unknown 语义

Absence 不等于 zero。Unknown 不等于 absence。

- Timestamp：没有 timestamp chunk 的 PCM WAV 记录 `timestamp_status="absent"`；存在但不可用或未解析的
  timestamp-bearing chunk 记录 `"unknown"`。
- Encoder delay 与 padding：没有 fact 记录 `"absent"`；识别到但不支持的 metadata 记录 `"unknown"`；
  numeric value 是 sample count。
- Channel layout：classic PCM 和 extensible zero mask 记录 `channel_layout="unknown_ordered"`；
  extensible non-zero mask 记录 `channel_layout="mask"`，并带 numeric mask 和派生 label。

这些 fact 参与 `audio.relation_facts_changed`，不得作为 backend-only metadata。

## Grouping、coordinate、digest、fact 与 ID

Change 按 relation、stream index、operation、coordinate 分组。Ordering 稳定且升序。
`AudioCoordinate.sample_index` 是 selected decoded stream 中 deinterleave 后的 zero-based index，
位于除 `sample_index` 外任何 alignment 之前。`AudioCoordinate.byte_start` 和 `byte_end` 是 immutable
source snapshot 中的 absolute half-open byte offset。

Digest domain 使用 length-framed 且 domain-separated：

- `audio.encoded_bytes.v1`：selected encoded byte range，以及 source length 和 byte offset；
- `audio.decoded_samples.v1`：stream index、sample rate、channel count、channel label、sample
  format、signedness、endianness、container bits、valid bits、sample count 与 per-channel sample byte；
- `audio.fact_set.v1`：排序后的 fact name、unit、value type 与 value。

首批门禁要求的 fact order 是：

1. `container.form`（unit `tag`）
2. `codec.profile`（unit `name`）
3. `stream.index`（unit `index`）
4. `sample_rate`（unit `Hz`）
5. `channel_count`（unit `count`）
6. `channel_layout`（unit `name`）
7. `channel_mask`（unit `bitmask`，nullable）
8. `sample_format`（unit `name`）
9. `container_bits_per_sample`（unit `bits`）
10. `valid_bits_per_sample`（unit `bits`）
11. `sample_count_per_channel`（unit `samples`）
12. `duration_seconds`（unit `s`）
13. `timestamp_status`（unit `name`）
14. `encoder_delay_status`（unit `name`）
15. `encoder_padding_status`（unit `name`）

Stable identifier 使用 lowercase ASCII dotted name：

- comparator：`builtin.audio`
- P7-A1 algorithm：`audio.decoded_samples.exact.v1`
- encoded algorithm：`audio.encoded_bytes.exact.v1`
- transformation：`audio.decode.stdlib_wave_pcm.v1`
- resource profile：`audio.resource.p7_a1.v1`
- policy rule prefix：`audio.policy.`

## Duration 与 timebase determinism

Exact duration 是 rational `sample_count_per_channel / sample_rate`。Result 记录
`duration_numerator`、`duration_denominator` 和 `duration_seconds`。`duration_seconds` 是该 rational
的 IEEE-754 binary64 nearest-even 值，不使用 extended precision 或 fused operation，并序列化为可
round-trip 到同一 binary64 的最短 decimal。Infinite、NaN、negative zero、locale-dependent 和
platform-specific float string 都非法。

## CLI 与 SDK-v1 plugin rejection

P7-A1 预留以下 CLI flag：

```text
platydiff audio LEFT RIGHT
  --audio-relation decoded_samples
  --audio-backend stdlib_wave_pcm
  --audio-profile p7_a1_wav_pcm
  --audio-stream-index 0
  --audio-channel-mode all
  --audio-channel-indices 0,1
  --audio-output json
```

`--audio-channel-indices` 只有与 `--audio-channel-mode indices` 同时使用时合法。`encoded_bytes`
通过 `--audio-relation encoded_bytes` 选择。Waveform、spectral 与 perceptual relation flag 在后续
gate 前继续被拒绝。

任何通过 SDK v1.1 plugin comparator flag 路由 audio 的尝试，都必须在 plugin discovery 或 execution
前以 `usage_error/plugin_sdk_modalities` 拒绝。错误必须说明 SDK v1.1 只支持 text/binary，media plugin
需要未来 SDK-v2 contract。

## Problem detail key

Problem detail object 是 closed JSON object，key order 稳定。Optional key 不可用时省略；除非下表
type 明确允许 null，否则不得填入 `null`。

| Key | Type |
| --- | --- |
| `stage` | canonical lifecycle stage string 之一 |
| `code` | stable problem code string |
| `message` | human-readable string |
| `media_kind` | `"audio"` |
| `relation` | selected relation string |
| `backend` | backend string |
| `profile` | profile string |
| `path_label` | safe source label string |
| `byte_offset` | 非负 integer |
| `chunk_id` | 四字节 ASCII chunk ID string |
| `field` | schema 或 header field name |
| `expected` | string、number、boolean，或这些类型的 array |
| `actual` | string、number、boolean，或这些类型的 array |
| `limit_name` | resource limit name |
| `limit_value` | 非负 integer |

Backend stderr、exception class、host path 和 arbitrary dictionary 不得进入 problem detail。

## Migration 与 compatibility impact

如果被接受，本 amendment 会在 P7-A1 代码开始前更新 RFC 0009。它不改变 schema v1-v5 payload，
不为 video 分配 schema membership，不独立选择 audio successor number，也不授权实现。最终 audio
successor fixture 必须使用 global predecessor resolution 选定的编号，并覆盖 omitted default、
explicit default、unknown-key rejection、encoded-byte change、unsupported valid WAV profile、corrupt
WAV input、absent versus unknown fact、duration determinism、CLI rejection，以及 stable problem
detail object。

## Implementation test matrix

| Area | Required coverage |
| --- | --- |
| Wire shapes | omitted default、explicit default、key order、unknown key、bad type、duplicate channel index |
| WAV profile | RIFF PCM 8/16/24/32、unsigned 8-bit、extensible PCM、valid bits、mask、fmt extra、RIFX、multiple data chunk、padding、trailing chunk |
| Resolution boundary | valid unsupported profile at `resolving`、corrupt structure at sourcing/decode、probe byte limit |
| Relations | encoded bytes、decoded samples、relation fact change、homogeneous `AudioChange` set |
| Facts | timestamp absent/unknown、encoder delay/padding absent/unknown、channel layout unknown/mask |
| Digests | encoded domain、decoded domain、fact-set domain、length framing、repeated-run determinism |
| Duration | exact rational、binary64 nearest-even、shortest round-trip JSON、no NaN/Inf/negative zero |
| CLI/SDK | first-gate flag、invalid combination、SDK-v1 plugin rejection before discovery |
| Problems | key order、value type、omission rule、no backend stderr or host path |

## 需要人工批准的问题

1. Classic PCM `fmt ` chunk size 18 且 `cbSize=0` 时是否应接受，还是 P7-A1 继续采用更严格的
   size-16-only rule？
2. Multiple `data` chunk 是否继续 valid-but-unsupported，还是 P7-A1 应拼接它们并记录显式
   chunk-boundary fact？
3. WAVE_FORMAT_EXTENSIBLE 的 valid bits 小于 container bits 时，是否如本文提议一样精确比较 stored
   container bit，还是在 sample comparison 前 mask unused bit？
4. CLI command 应为 `platydiff audio`，还是保留在既有 compare command 下使用 `--kind audio`？
5. 单独的 cross-RFC predecessor resolution 在协调 RFC 0006、RFC 0008 和已实现 schema-v3 closed
   union 后，应为 audio 分配哪个 schema successor number？
