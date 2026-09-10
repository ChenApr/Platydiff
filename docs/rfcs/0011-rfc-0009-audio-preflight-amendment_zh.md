# RFC 0011：RFC 0009 Audio Preflight Amendment

[English documentation](0011-rfc-0009-audio-preflight-amendment.md)

- Status: Accepted
- Date: 2026-09-10
- Accepted: 2026-09-10
- Amends: [RFC 0009](0009-audio-and-video-comparison_zh.md)
- Approved decisions: P7A-AM1 到 P7A-AM10；P7A-W1 到 P7A-W5
- Schema prerequisites: accepted RFC 0010 Option A/SP1-SP6，以及实际 merge 的 P4-C1、P5-A1/schema-v4 和 P6-C0/schema-v5
- Dispatch prerequisite: RFC 0011 itself has merged
- Conditional implementation authorization: 已记录，但仅能在 schema prerequisite 和 dispatch prerequisite 均满足后由 coordinator dispatch
- Owners: Platydiff 维护者
- Implementation owner: schema prerequisite 与 RFC 0011 merge 后由 coordinator dispatch

## 摘要与授权边界

本 RFC 提议为 RFC 0009 增加 P7-A1 audio implementation preflight blocker
修订，且本修订已被 Accepted。RFC acceptance 本身不启动代码；conditional human authorization
已记录，但 P7-A1 implementation 只能在 schema prerequisite 与 RFC 0011 itself merge 后由
coordinator dispatch。Acceptance 不授权依赖变更、FFmpeg、artifact、UI、SDK v2、自动媒体探测、
video implementation，或独立 schema renumbering。

本修订保留 RFC 0009 的所有前驱门禁，并把全局 schema numbering 交给已批准路径：
RFC 0010 Option A/SP1-SP6。只有 RFC 0010 Option A/SP1-SP6 先被 accepted，并且
P4-C1、P5-A1/schema-v4 和 P6-C0/schema-v5 predecessors 实际 merge 后，audio 才保留 schema
v6。必须从当前 `main` 复验 P4-A1 JSON/schema-v3，且 P7-A1 仍需等待 RFC 0011 itself merged、
predecessor implementation 与 compatibility fixture 可用后由 coordinator dispatch。Video 仍只是
roadmap-only，并等待单独的 backend/worker amendment 和下一个 schema successor。

## 推荐决策

这些 ID 是已批准的 P7-A1 contract decision，并受上文 prerequisite 与授权边界约束。

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
| P7A-AM10 | 让 audio schema v6 取决于已批准的 RFC 0010 Option A/SP1-SP6，以及实际 P4-C1、P5-A1/schema-v4 和 P6-C0/schema-v5 merges。 | 在这个 audio-specific amendment 中解决 cross-RFC closed-union numbering。 |
| P7A-W1 | 保持 classic PCM `fmt ` chunk size 16 作为 P7-A1 唯一可解码的 classic PCM form；valid size-18 且 `cbSize=0` 的 chunk 是 valid but unsupported。 | 接受 size-18 classic PCM，并把它视为等价于 size 16。 |
| P7A-W2 | 保持 multiple `data` chunk 对 P7-A1 valid but unsupported。 | 拼接多个 `data` chunk，并增加显式 chunk-boundary fact。 |
| P7A-W3 | 对 `valid_bits < container_bits` 的 WAVE_FORMAT_EXTENSIBLE，要求 profile 规定的 unused padding bit 为零，保留 valid-bits 与 container-bits fact，并精确比较已验证的 stored integer representation，不做 hidden masking；non-zero padding bit 是 malformed。 | 在 sample comparison 前 mask unused bit。 |
| P7A-W4 | 同时暴露 `platydiff audio` 与 `platydiff compare --type audio`；二者构造相同的 `CompareSpec` 并执行相同 comparison path，以保持与其他 built-in 一致。 | 只保留 generic compare command。 |
| P7A-W5 | 只有 RFC 0010 Option A/SP1-SP6 被接受，并且 P4-C1、P5-A1/schema-v4 和 P6-C0/schema-v5 predecessors 实际 merge 后，才保留 audio schema v6。 | 在本 amendment 中独立分配 audio v6。 |

## Wire shape 与解析规则

所有 option object 都是 closed-key JSON object。Unknown key 非法。Key 必须按下列顺序序列化。
schema-v6 reader 在比较前插入 default；omitted field 只有在等同于文档化 default 时才等价。

### `AudioStreamSelection`

本 amendment 收紧已接受的 RFC 0009 `AudioStreamSelection` shape；它不以另一组字段取代既有 shape。

Key order 与 default：

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `index` | integer 或 null | `null` | 保留 RFC 0009 `stream.index`。P7-A1 WAV 正好只有一个 stream；`null` 与 `0` 选择该 stream，非零值在 source inspection 前作为 invalid intent 拒绝。 |
| `require_channel_labels` | boolean | `false` | 为 true 时，missing 或 unknown source channel label 在 header fact 可证明时于 `resolving` 失败；若只有 decode 开始后才能证明，则于 `decoding` 失败。 |

### `AudioDecodeOptions`

Key order 与 default：

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `backend` | string | `"stdlib_wave_pcm"` | P7-A1 唯一 backend。 |
| `profile` | string | `"p7_a1_wav_pcm"` | 选择下文有界 WAV/PCM profile。 |
| `sample_representation` | string | `"native_pcm_integer"` | 保留 RFC 0009 `decode.sample_representation`；exact equality 不包含 integer-to-float conversion。 |
| `unsupported_profile` | `"unavailable"` | `"unavailable"` | valid-but-unsupported profile 产生 `unavailable/capability_unavailable`。 |
| `max_probe_bytes` | 非负 integer | `65536` | resolving-stage profile probe 的上限。 |

### `AudioAlignmentOptions`

本 amendment 保留 RFC 0009 独立的 `AudioAlignmentOptions` object。P7-A1 default 保持：

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `mode` | string | `"sample_index"` | P7-A1 只启用 `sample_index`。 |
| `fixed_offset_samples` | integer | `0` | 保留到 P7-A2。 |
| `max_search_offset_samples` | 非负 integer | `0` | 保留到 P7-A2。 |
| `max_drift_ppm` | finite JSON number | `0.0` | 保留到 P7-A2。 |
| `ambiguity_margin_samples` | 非负 integer | `0` | 保留到 P7-A2。 |

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
不是 decoded sample coordinate。Payload 携带 digest；byte interval 由
`AudioCoordinate.byte_start` 与 `AudioCoordinate.byte_count` 表示。除非后续
artifact/source-disclosure RFC 明确授权，否则绝不序列化 raw source byte 或 bounded byte snippet。

`AudioChange` 保留已接受的 RFC 0009 shape，并且是 closed object，key order 为：

```text
kind, relation, operation, before_coordinate, after_coordinate, channel,
before_digest, after_digest, before_fact, after_fact
```

共同 invariant：

- `kind` 始终为 `"audio_change"`；
- `relation` 是一个 selected relation name；
- `before_coordinate` 与 `after_coordinate` 是 `AudioCoordinate` object 或 `null`；
- detail truncation 仍是 total count 已知后的 result/change-list metadata；它不是 per-change field。

本 amendment 将 `encoded_byte_update`、`encoded_byte_insert` 与 `encoded_byte_delete` 加入已接受的
operation set。它还为 `encoded_bytes` relation 扩展 `AudioCoordinate`，加入 `byte_start` 与
`byte_count`。对于 encoded-byte change，sample 与 time coordinate field 为 `null`。

Operation-specific field：

| Operation | Required fields | Null fields |
| --- | --- | --- |
| `encoded_byte_update` | `before_coordinate.byte_start`、`before_coordinate.byte_count`、`after_coordinate.byte_start`、`after_coordinate.byte_count`、`before_digest`、`after_digest` | `before_fact`、`after_fact` |
| `encoded_byte_insert` | `after_coordinate.byte_start`、`after_coordinate.byte_count`、`after_digest` | `before_coordinate`、`before_digest`、`before_fact`、`after_fact` |
| `encoded_byte_delete` | `before_coordinate.byte_start`、`before_coordinate.byte_count`、`before_digest` | `after_coordinate`、`after_digest`、`before_fact`、`after_fact` |
| `sample_update` | `before_coordinate.sample_start`、`after_coordinate.sample_start`、`before_digest`、`after_digest` | `before_fact`、`after_fact` |
| `format_update`、`channel_update`、`timing_update`、`metadata_update` | `before_fact`、`after_fact` | 除非该 fact update 也携带 bounded affected interval，否则 digest 为 null |

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
header malformed 时则为 corrupt。Classic PCM `fmt ` chunk size 18 且 `cbSize=0` 时也属于
P7-A1 valid but unsupported。

`nBlockAlign`、`nAvgBytesPerSec`、channel count、sample rate、container bits、valid bits 与
channel mask 必须内部一致。Classic PCM 的 channel label unknown，channel 有序。
WAVE_FORMAT_EXTENSIBLE 且 mask 非零时，从 mask 记录 label；zero mask 记录 unknown label 与
ordered channel。Valid bits 记录为 fact，不会静默 mask stored container bit。
当 WAVE_FORMAT_EXTENSIBLE 满足 `valid_bits < container_bits` 时，profile 规定的 unused
padding bit 必须在 exact comparison 前为零；non-zero padding bit 是 malformed input。

必须正好有一个 `fmt ` chunk，且至少有一个 `data` chunk。多个 `data` chunk 是 valid but unsupported
for P7-A1。单个 `data` chunk 后可以跟 well-formed non-audio chunk；它们的 chunk ID 与 byte size
记录为 metadata fact，但不参与 decoded sample。Odd-sized chunk 的 RIFF pad byte 被忽略。Chunk
外的非零 trailing byte、truncated chunk header、超过文件长度的 chunk size、或 `data` 早于 `fmt `
都是 corrupt input。

## Resolving 与 decoding 边界

有界 pre-resolution probe 在 `resolving` 期间运行，且只读取 RIFF header、chunk header、第一个
`fmt ` chunk，以及不超过 `max_probe_bytes` 的 data-chunk inventory。Unsupported-but-valid profile
按如下方式失败：

```text
outcome=unavailable
stage=resolving
code=capability_unavailable
```

无法打开 source 或有界 snapshot read 失败的 malformed byte 在 `sourcing` 失败。Resolving probe
证明的 malformed RIFF/WAV header 或 chunk structure 返回
`failed/resolving/decode_error`，即在证明 malformed media 的真实 stage 使用既有 problem code。
只有 decode 开始后才发现的 malformed sample payload 返回
`failed/decoding/decode_error`。Decode 开始后，禁止 fallback 到 bytes、另一 backend、另一 profile
或 perceptual relation。

## Absence 与 unknown 语义

Absence 不等于 zero。Unknown 不等于 absence。

- Timestamp：没有 timestamp chunk 的 PCM WAV 记录 `timestamp_status="absent"`；存在但不可用或未解析的
  timestamp-bearing chunk 记录 `"unknown"`。
- Encoder delay 与 padding：没有 delay/padding metadata 时记录 status `"absent"`；识别到但不支持的
  metadata 记录 `"unknown"`；numeric value 是 sample count。
- Channel layout：classic PCM 和 extensible zero mask 记录 `channel_layout="unknown_ordered"`；
  extensible non-zero mask 记录 `channel_layout="mask"`，并带 numeric mask 和派生 label。

这些 fact 参与 `audio.relation_facts_changed`，不得作为 backend-only metadata。

## Grouping、coordinate、digest、fact 与 ID

Change 按 relation、stream index、operation、coordinate 分组。Ordering 稳定且升序。
`AudioCoordinate.sample_start` 在 selected decoded stream 内、deinterleaving 后使用 zero-based
index，`AudioCoordinate.sample_count` 记录任何非 `sample_index` alignment 前的 interval length。
`AudioCoordinate.byte_start` 与 `AudioCoordinate.byte_count` 标识 immutable source snapshot
中的 absolute byte interval。

Digest algorithm 是 SHA-256。Digest input 是 byte-exact，并使用以下 framing：

- `frame(tag, payload) = tag || uint32_be(len(payload)) || payload`；
- string value 使用 tag `S` 和 UTF-8 payload；
- unsigned integer 使用 tag `U` 和 canonical decimal ASCII payload；
- signed integer 使用 tag `I` 和 canonical decimal ASCII payload；
- bytes 使用 tag `B` 和 raw bytes；
- absent optional value 使用 tag `N` 和 zero-length payload；
- list 使用 tag `L`，payload 为 `uint32_be(item_count) || item_frame...`；
- name/value pair 是正好两个 item 的 list：`S(name)`，然后是 framed value。

Digest input 是：

```text
S("platydiff.audio.digest.v1") ||
S(domain) ||
L([pair(name, value), ...])
```

Digest domain 为：

- `audio.encoded_bytes.v1`：selected encoded byte range，以及 source length 和 byte offset；
- `audio.decoded_samples.v1`：stream index、sample rate、channel count、channel label、sample
  format、signedness、endianness、container bits、valid bits、sample count 与 per-channel sample byte；
- `audio.fact_set.v1`：排序后的 fact name、unit、value type 与 value。

Normative vector：

| Domain | Fields | SHA-256 |
| --- | --- | --- |
| `audio.encoded_bytes.v1` | `source_length=0`、`ranges=[]` | `e2361113e7d5fe9d32fcf689ea057c9950deee12f0272191f810df4ac5e3fae4` |
| `audio.encoded_bytes.v1` | `source_length=3`、`ranges=[(0,3,"abc")]` | `1127cf48354fc7b2e82205a4a37b41b2ab15f37f7504a569b4ecf96e9beb540d` |
| `audio.decoded_samples.v1` | 8 kHz mono signed 16-bit little-endian，one zero sample | `571b0712e3cab0285232543121c61d8d79217483f7800e22636464f8be6641a2` |
| `audio.fact_set.v1` | `facts=[]` | `a71820ac77a1695045cc22037a58821a619210cfaf2b8ea332a888b1ff276431` |

Vector field order 是 normative。Encoded vector 使用 pair 顺序 `source_length`，然后 `ranges`；
每个 range 是 `start`、`end`、`bytes`。Decoded vector 使用 pair：
`stream_index=0`、`sample_rate=8000`、`channel_count=1`、`channel_labels=[N]`、
`sample_format="pcm_s16le"`、`signedness="signed"`、`endianness="little"`、
`container_bits=16`、`valid_bits=16`、`sample_count=1`、`samples=[0x0000]`。
Fact vector 只使用 `facts=[]`。

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

Stable identifier 使用 lowercase ASCII dotted name。完整 P7-A1 set 为：

- comparator：`builtin.audio`
- P7-A1 algorithm：`audio.decoded_samples.exact.v1`
- encoded algorithm：`audio.encoded_bytes.exact.v1`
- transformation：`audio.decode.stdlib_wave_pcm.v1`
- resource profile：`audio.resource.p7_a1.v1`
- resource limits：`audio.resource.p7_a1.defaults.v1`
- policy rules：`audio.policy.exact_decoded_samples.v1`、
  `audio.policy.encoded_bytes.v1`、`audio.policy.no_hidden_transforms.v1`、
  `audio.policy.no_fallback_after_backend_start.v1`
- metrics：`audio.samples_changed`、`audio.bytes_changed`、
  `audio.samples_compared`、`audio.channels_compared`、
  `audio.relation_facts_changed`、`audio.duration_delta`、
  `audio.duration_delta_abs`

## Duration 与 timebase determinism

Exact duration 是 rational `sample_count_per_channel / sample_rate`。Result 记录
`duration_numerator`、`duration_denominator` 和 `duration_seconds`。`duration_seconds` 是该 rational
的 IEEE-754 binary64 nearest-even 值，不使用 extended precision 或 fused operation，并序列化为可
round-trip 到同一 binary64 的最短 decimal。Infinite、NaN、negative zero、locale-dependent 和
platform-specific float string 都非法。

## CLI 与 SDK-v1 plugin rejection

P7-A1 预留两个等价 CLI entry point：

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

两个 entry point 构造相同的 `CompareSpec`，并执行相同 built-in comparison path。
`--audio-stream-index` 映射到已接受的 `stream.index`；P7-A1 只接受 `0`。`encoded_bytes`
通过 `--audio-relation encoded_bytes` 选择。Waveform、spectral、perceptual、channel-selection
以及非 `sample_index` alignment flag 在后续 gate 前继续被拒绝。

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
| `input_side` | `"before"`、`"after"` 或 `"both"` |
| `byte_offset` | 非负 integer |
| `chunk_id` | 四字节 ASCII chunk ID string |
| `field` | schema 或 header field name |
| `expected` | string、number、boolean，或这些类型的 array |
| `actual` | string、number、boolean，或这些类型的 array |
| `limit_name` | resource limit name |
| `limit_value` | 非负 integer |

Backend stderr、exception class、host path、source filename、safe label 和 arbitrary dictionary
不得进入 problem detail。

## Migration 与 compatibility impact

本 accepted amendment 会在 P7-A1 代码开始前更新 RFC 0009。它不改变 schema v1-v5 payload，
不为 video 分配 schema membership，也不独立选择 audio successor number。RFC acceptance 本身
不启动代码；conditional human authorization 已记录，但仍需 RFC 0010、P4-C1、
P5-A1/schema-v4 和 P6-C0/schema-v5 实际 merge，且 RFC 0011 itself merged 后由 coordinator
dispatch。最终 audio successor fixture 只有在 schema predecessor merge 后才使用 schema v6，
并覆盖 omitted default、explicit default、unknown-key rejection、encoded-byte change、
unsupported valid WAV profile、corrupt WAV input、absent versus unknown fact、duration
determinism、CLI rejection，以及 stable problem detail object。

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

## 人工批准记录

2026-09-10 已批准：P7A-AM1 到 P7A-AM10，以及 P7A-W1 到 P7A-W5。P7-A1 implementation 的
conditional human authorization 已记录，但 RFC acceptance 本身不启动代码。P7-A1 仍受 gate
约束，并且需要 RFC 0010、P4-C1、P5-A1/schema-v4 和 P6-C0/schema-v5 实际 merge，且
RFC 0011 itself merged 后由 coordinator dispatch。
