# RFC 0012：P7-A1 Audio Pre-Code Contract Closure

[English documentation](0012-p7a1-audio-pre-code-contract-closure.md)

- Status: Proposed
- Date: 2026-09-10
- Amends: [RFC 0009](0009-audio-and-video-comparison_zh.md) 和
  [RFC 0011](0011-rfc-0009-audio-preflight-amendment_zh.md)
- Owners: Platydiff 维护者
- Implementation owner: 无；本 proposal 不启动代码

## 摘要与授权边界

本 Proposed amendment 补齐 P7-A1 pre-code audio contract 的剩余缺口。它不授权
implementation、video、UI、FFmpeg、新依赖、automatic media detection、SDK v2，或 audio
schema-v6 之外的任何 schema successor。

本 proposal 保留 RFC 0009 与 RFC 0011 的方向：P7-A1 仅限 audio；decoded-sample relation
使用 stdlib WAV/PCM profile；并且仍受 accepted RFC 0010 Option A/SP1-SP6，以及实际 P4-C1、
P5-A1/schema-v4、P6-C0/schema-v5 merge 的门禁约束。P7-A1 dispatch 还要求 RFC 0011 与本
amendment 在被接受后均已 merge。

## Proposed decisions

这些 ID 是 proposed decision。只有本 amendment 被明确 accepted 后，它们才成为实现契约。

| ID | Proposed decision | 未选择的替代方案 |
| --- | --- | --- |
| P7A-PC1 | 冻结 equal result 与 complete decoded-audio fact 的 public carrier field。 | 让 renderer 从 backend-local metadata 推断 equal audio identity。 |
| P7A-PC2 | 冻结 sample 与 encoded-byte change 的连续分组规则，包括 `change_count`、`samples_changed` 与 `bytes_changed` 计数。 | 在没有稳定 aggregation rule 的情况下逐 sample 或逐 byte run 发出 change。 |
| P7A-PC3 | 冻结 `max_compare_work`、`max_packets`、`max_decoded_bytes` 与 `max_resident_bytes` 的 resource limit name、range 和 unit，并区分 single-input 与 dual-input accounting。 | 使用 backend-dependent 或 host-dependent resource name 和 unit。 |
| P7A-PC4 | 将 `encoded_bytes` 定义为 raw byte relation：绕过 WAV probe/decode，接受任意 byte stream，并允许 limit value `0` 表示不得比较任何 byte。 | 在 encoded-byte comparison 前要求 WAV valid。 |
| P7A-PC5 | 冻结 timestamp、delay 与 padding chunk 识别清单，并要求所有用户可见解释只出现在 `problem.message`；结构化值只出现在 `problem.details`。 | 在 detail value 中重复解释性 prose。 |
| P7A-PC6 | 保持 schema-v6 exclusively audio，并保持 video roadmap-only。 | 让本 closure 分配 video schema membership。 |

## Equal result carrier

P7-A1 audio 的 equal result 仍是普通 schema-v6 `DiffResult`。Audio-specific equality 的
public carrier 为：

| Field | Required value |
| --- | --- |
| `schema_version` | `6` |
| `modality` | `"audio"` |
| `outcome` | `"equal"` |
| `media_evaluations` | selected audio relation evaluation 的有序 list |
| `changes.change_count` | `0` |
| `changes.items` | empty list |
| `metrics` | 包含每个 selected relation 的 comparison total |
| `provenance` | 包含 selected comparator、backend、profile、resource limit、normalization、alignment 和 input digest |

Equal decoded-sample comparison 的第一个 `media_evaluations` entry 为：

| Field | Required value |
| --- | --- |
| `kind` | `"media_view_evaluation"` |
| `modality` | `"audio"` |
| `relation` | `"decoded_samples"` |
| `status` | `"compared"` |
| `comparison` | `"exact"` |
| `backend` | `"stdlib_wave_pcm"` |
| `profile` | `"p7_a1_wav_pcm"` |
| `stream.index` | default insertion 后为 `null` 或 `0`，并在 provenance 中报告 selected stream `0` |

Complete decoded-audio fact carrier 是 closed object，key order 为：

```text
name, value, unit, stream_index, coordinate, source
```

`source` 是 `"container"`、`"format"`、`"decode"`、`"derived"` 或 `"policy"`。
Equal decoded-sample result 至少必须携带以下 fact：

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

Absent optional timing fact 使用 value `null`、unit `null`，并在 P7-A1 规定该 absence 时使用
source `"policy"`。Recognized but unsupported metadata 使用 value `"unknown"` 和该 fact 文档化的
unit。

## Change grouping and counts

`ChangeSet.change_count` 是连续分组之后、renderer truncation 之前 emitted `AudioChange` item 的数量。
Renderer truncation 可以缩短 `changes.items`，但不得改变 `change_count` 或 metric value。

对于 `decoded_samples`，sample change 按以下字段相同的 maximal continuous run 分组：

```text
relation, operation, stream_index, channel, before_step, after_step
```

Replacement run 的 `before_step` 和 `after_step` 都是 `1`；deletion 为 `1` 和 `0`；insertion 为
`0` 和 `1`。P7-A1 只启用 sample-index alignment，因此 insertion 和 deletion 保留到后续 gate，
decoded-sample comparison 不得 emit。P7-A1 decoded-sample difference 因此是 `sample_update` run。

对于 `encoded_bytes`，byte change 按以下字段相同的 maximal continuous byte run 分组：

```text
relation, operation, before_step, after_step
```

`encoded_byte_update` 每一步使用一个 before byte 和一个 after byte。`encoded_byte_delete` 使用一个
before byte 且无 after byte。`encoded_byte_insert` 无 before byte 且使用一个 after byte。

Metric 计数规则：

| Metric | Count rule |
| --- | --- |
| `audio.samples_changed` | 所有 channel 上 changed decoded sample position 的总数；grouping 不得改变 total。 |
| `audio.bytes_changed` | changed encoded byte position 的总数；update 算一个 byte position，delete 算一个 before byte，insert 算一个 after byte。 |
| `audio.samples_compared` | compared decoded sample position 数量乘以 selected channel count。 |
| `audio.channels_compared` | 到达 comparison 的 selected channel 数量。 |
| `change_count` | grouped `AudioChange` item 的数量。 |

## Resource limits

所有 resource limit 都是 non-negative integer。Unknown limit name 非法。Default value 由 schema-v6
reader 在 comparison 前插入。

| Limit | Unit | Single-input range | Dual-input accounting | P7-A1 default |
| --- | --- | --- | --- | --- |
| `max_compare_work` | abstract work units | `0..2^63-1` | 两个 input 与 comparison work 的总和 | `100000000` |
| `max_packets` | packet 或 chunk record | `0..2^31-1` | 从两个 input 读取的 packet/chunk 总和 | `1048576` |
| `max_decoded_bytes` | decoded PCM bytes | `0..2^63-1` | 两个 input materialized decoded PCM byte 的总和 | `268435456` |
| `max_resident_bytes` | resident memory bytes | `0..2^63-1` | 整个 comparison 的 simultaneous resident byte peak | `134217728` |

`max_compare_work=0` 只允许可以用 zero relation work 完成的 comparison：identical empty encoded-byte
input，或 relation work 开始前的 metadata-only failure。`max_packets=0` 禁止读取任何 packet 或
WAV chunk record。`max_decoded_bytes=0` 禁止 decode PCM payload byte。`max_resident_bytes=0`
要求 comparator 在分配 comparison buffer 前失败。

Limit failure 的 problem detail 使用：

| Detail key | Value |
| --- | --- |
| `limit_name` | 上表中的 name |
| `limit_value` | configured integer |
| `limit_unit` | 上表中的 exact unit string |
| `accounting_scope` | `"single_input"`、`"dual_input_sum"` 或 `"comparison_peak"` |
| `measured_value` | 同一 unit 中的 integer |
| `input_side` | `"before"`、`"after"` 或 `"both"` |

## Encoded bytes relation

`encoded_bytes` 是 byte relation，不是 WAV relation。选择 `encoded_bytes` 时绕过 WAV profile probe、
WAV header validation、sample decoding、channel selection、derived WAV header audio fact，以及
decoded-sample alignment。它接受任意 byte stream，包括 empty stream 和 malformed WAV file。

对于 `encoded_bytes`，limit value `0` 合法。当两个 input 都为空且 `max_compare_work=0` 时，result
为 equal。当任一 input 非空且 zero limit 阻止读取或 comparison 时，result 在证明该 limit 的 stage
产生 resource-limit failure。

虽然绕过 WAV probing，source acquisition 仍然适用：unreadable path、missing input、permission
failure 和 source size policy failure 仍是 `sourcing` problem。

## Timestamp, delay, and padding recognition

P7-A1 只识别以下 timing、delay 与 padding source：

| Chunk or source | Facts |
| --- | --- |
| no recognized timestamp source | `timestamp_origin=null`、`timestamp_value=null` |
| RIFF `bext` time reference | `timestamp_origin="bext.time_reference"`、`timestamp_value` 为 sample count |
| RIFF `smpl` sample period | `timestamp_origin="smpl.sample_period"`、`timestamp_value` 为 internally consistent 时的 exact rational seconds |
| no recognized delay source | `encoder_delay_samples=null` |
| no recognized padding source | `encoder_padding_samples=null` |
| recognized but unsupported delay/padding metadata | 对应 value 为 `"unknown"` |

所有其他 chunk 只有在 RFC 0011 已允许它们作为 bounded chunk fact 时才是 metadata fact。它们不得静默影响
sample coordinate、duration、alignment 或 equality。

## Problem message and details

`problem.message` 是用户可见解释性 prose 的唯一位置。`problem.details` 是 structured value 的唯一位置。
Detail value 必须是 string、integer、finite JSON number、boolean 或 `null`；array 与 object 仍非法，
除非后续 schema revision 明确允许。

本 amendment 允许的 detail key 为：

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

Detail value 不得包含 backend stderr、exception class name、host path、source filename、safe label、
解释性 sentence 或 arbitrary dictionary。

## Canonical vectors

这些 vector 是 acceptance test 的 normative example。它们表示 default insertion 后、renderer
truncation 前的 canonical JSON fragment。

### Vector PC-A：equal empty encoded bytes

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

### Vector PC-B：one continuous sample update

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

### Vector PC-C：byte insert with zero WAV assumptions

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

### Vector PC-D：resource limit detail

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

只有 reviewers 确认以下全部事项后，本 amendment 才可 accepted：

1. RFC 0010 Option A/SP1-SP6，以及实际 P4-C1、P5-A1/schema-v4、P6-C0/schema-v5 predecessor
   gate 仍为必要条件。
2. Schema-v6 仍 exclusively audio。
3. Decoded-sample comparison 仍只限 stdlib WAV/PCM。
4. `encoded_bytes` 绕过 WAV probe/decode，并接受任意 byte stream。
5. Equal result carrier 与 complete decoded-audio fact carrier 是 closed 且 renderer-independent。
6. Continuous grouping 和 metric count 是 deterministic，且不受 renderer truncation 影响。
7. Resource limit name、range、unit 与 accounting scope 稳定。
8. Problem prose 只在 `problem.message`；structured data 只在 `problem.details`。
9. 英文与中文文本保持一致。
10. 本 Proposed amendment 不启动 P7-A1 implementation、video、UI、FFmpeg、dependency 或 PR 工作。
