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
| P7A-PC3 | 冻结每个 accepted `AudioResourceLimits` field 的 scope 与 unit clarification，同时保留 accepted name、default 和 zero-budget semantic。 | 用更小的 backend-specific limit set 取代 accepted resource object。 |
| P7A-PC4 | 将 `encoded_bytes` 定义为 raw byte relation：绕过 WAV probe/decode，接受任意 byte stream，并允许 limit value `0` 表示不得比较任何 byte。 | 在 encoded-byte comparison 前要求 WAV valid。 |
| P7A-PC5 | 冻结 timestamp、delay 与 padding chunk 识别清单，并要求所有用户可见解释只出现在 `problem.message`；结构化值只出现在 `problem.details`。 | 在 detail value 中重复解释性 prose。 |
| P7A-PC6 | 保持 schema-v6 exclusively audio，并保持 video roadmap-only。 | 让本 closure 分配 video schema membership。 |

## Equal result carrier

P7-A1 audio 的 equal result 仍是普通 schema-v6 `DiffResult`。RFC 0012 不替换 accepted
schema-v6 `DiffResult` 或 `MediaViewEvaluation` hierarchy。Audio-specific equality 的 public
carrier 是 accepted RFC 0009/RFC 0011 envelope：

| Field | Required value |
| --- | --- |
| `schema_version` | `6` |
| `relation` | `"equal"` |
| `verdict` | `"pass"` |
| `fidelity` | `"full"` |
| `completeness` | full count 已知后的 producer-side result-detail truncation 未发生时为 `"complete"` |
| `media_evaluations` | selected audio relation evaluation 的有序 list |
| `summary.change_count` | `0` |
| `changes.total_count` | `0` |
| `changes.items` | empty list |
| `metrics` | 包含每个 selected relation 的 comparison total |
| `provenance` | 包含 selected comparator、backend、profile、resource limit、normalization、alignment 和 input digest |

Equal decoded-sample comparison 的第一个 `media_evaluations` entry 为：

| Field | Required value |
| --- | --- |
| `kind` | `"media_view_evaluation"` |
| `media_kind` | `"audio"` |
| `selector` | `"decoded_samples"` |
| `relation` | `"equal"` |
| `verdict` | `"pass"` |
| `fidelity` | `"full"` |
| `completeness` | `"complete"` |
| `metric_names` | relation 使用的 metric name 排序 tuple |
| `policy_rule_ids` | relation 使用的 policy rule ID 排序 tuple |
| `transformation_ids` | relation 使用的 transformation ID 排序 tuple |
| `warning_codes` | 除非记录 visible warning，否则为空 tuple |
| `change_count` | `0` |
| `failure_stage` | `null` |
| `failure_code` | `null` |

Backend、profile 与 `stream.index` 记录在 provenance 和 selected spec field 中，不作为替代
`MediaViewEvaluation` field。

Schema-v6 为 audio 闭合 result-level `completeness` carrier：新增
`DiffResult.completeness`，其 closed value 与语义与 `MediaViewEvaluation.completeness`
相同，只能是 `"complete"` 或 `"truncated"`。Completed audio result 不使用 `partial`。
只有在 relation、verdict、fidelity、全部 metric 与 total change count 已知后，producer-owned
result detail 省略 whole change item 时，result completeness 才是 `"truncated"`。它绝不表示
failed comparison。

Stable ID 保持 RFC 0011 accepted ID：

| Purpose | Stable ID |
| --- | --- |
| Built-in comparator/capability | `builtin.audio` |
| Decoded-sample algorithm | `audio.decoded_samples.exact.v1` |
| Encoded-byte algorithm | `audio.encoded_bytes.exact.v1` |
| WAV/PCM decode transformation | `audio.decode.stdlib_wave_pcm.v1` |
| Resource profile | `audio.resource.p7_a1.v1` |
| Resource defaults | `audio.resource.p7_a1.defaults.v1` |

RFC 0012 supersede 任何早期 Proposed vector 中的
`audio.comparator.stdlib_wave_pcm.v1`、`audio.decoded_samples.exact_grouped.v1`
或 `audio.encoded_bytes.prefix_suffix.v1`。Reader 必须把这些字符串视为 pre-acceptance
draft，而不是 alias。

## Result-level audio facts carrier

RFC 0012 在既有 completed-outcome hierarchy 内提出一个新的 schema-v6 audio fact carrier。它不替换
`CompletedOutcome`、`DiffResult`、`MediaViewEvaluation` 或 `AudioFact`。

Completed outcome hierarchy 保持：

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

`DiffResult.audio_facts` 出现在每个 schema-v6 completed result 中。它是 accepted
`AudioFact` record 的 tuple，按以下顺序排序：

```text
stream_index, coordinate, name, unit, value_type_rank, value
```

Audio result 用它在 result level 携带 relation-significant audio fact，使 equal decoded-sample
result 可以暴露 complete fact，而不发明 metadata update change。Non-audio predecessor upgrade
将其设为空 tuple。它不得包含 renderer-only label、backend stderr、host path、source filename 或
explanatory prose。

Complete decoded-audio fact 保留 accepted `AudioFact` closed object。RFC 0012 不向
`AudioFact` 增加 `source`、array 或 nested object。Key order 保持：

```text
name, value, unit, stream_index, coordinate
```

权威 P7-A1 fact registry 是下表中的 RFC 0011 first-gate fact order。它 supersede 较早的
Proposed 名称：`container.endianness`、`format.tag`、`format.extensible`、`signedness`、
`endianness`、`container_bits`、`valid_bits`、`block_align`、`byte_rate`、`sample_count`、
`duration_seconds_exact`、`duration_seconds_binary64`、`timestamp_origin`、`timestamp_value`、
`encoder_delay_samples` 和 `encoder_padding_samples`。

| Order | Name | Value type | Unit | Complete decoded result required | Nullable | Unknown value | Coordinate | Uniqueness |
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
| 12 | `duration_numerator` | integer | `samples` | yes | no | no | `null` | once per selected stream |
| 13 | `duration_denominator` | integer | `Hz` | yes | no | no | `null` | once per selected stream |
| 14 | `duration_seconds` | finite number | `s` | yes | no | no | `null` | once per selected stream |
| 15 | `timestamp_status` | string | `name` | yes | no | `"unknown"` | `null` | once per selected stream |
| 16 | `encoder_delay_status` | string | `name` | yes | no | `"unknown"` | `null` | once per selected stream |
| 17 | `encoder_padding_status` | string | `name` | yes | no | `"unknown"` | `null` | once per selected stream |

Complete decoded-sample equality 必须为 selected stream 携带全部 17 条 record。`AudioFact`
仍是 accepted closed shape：`name`、`value`、`unit`、`stream_index` 和 `coordinate`；P7-A1
fact 不允许 source field、array 或 nested value。Fact 由 `(stream_index, coordinate, name)`
唯一标识。排序先按上表 registry order，再按 `stream_index`、coordinate、unit、value type
rank 与 value。Value ordering 在 accepted value type 之间是 total order：`null`、boolean
（`false` 在 `true` 前）、integer、finite number、非 `"unknown"` 的 string，最后是 string
`"unknown"`。Integer 与 finite number 在各自 type 内按 exact numeric value 比较；string 使用
Unicode scalar lexical order。该顺序只用于 deterministic serialization，不改变 relation semantic。

RFC 0012 保留 RFC 0011 duration recording：`duration_numerator`、
`duration_denominator` 与 binary64 `duration_seconds` 是分离 fact。`duration_seconds` 是
`duration_numerator / duration_denominator` 的 IEEE-754 binary64 nearest-even 值，并序列化为可
round-trip 到同一 binary64 的 shortest decimal。

Predecessor v1-v5 upgrader 必须添加 `DiffResult.completeness`、
`DiffResult.media_evaluations` 和 `DiffResult.audio_facts`。对于 non-audio 或 pre-media result，
`completeness` 为 `"complete"`，`media_evaluations` 为空 tuple，`audio_facts` 为空 tuple。Upgrader
不得从旧 metadata 推断 audio fact。

## Change grouping and counts

`DiffSummary.change_count` 是连续分组之后、producer-side result-detail truncation 之前 grouped
`AudioChange` item 的数量。Renderer 绝不得缩短 `changes.items`、mutate summary 或 change-set
count，或 mutate overall relation/verdict/fidelity/completeness。Truncation 只是 producer
result-detail policy，并且在 full count 已知后通过 accepted completeness/truncation metadata 体现。

Count binding 是精确的：

| Field | Binding |
| --- | --- |
| `DiffSummary.change_count` | 非 null 时等于 `ChangeSet.total_count` |
| `ChangeSet.total_count` | 所有 selected audio relation 的 grouped `AudioChange` 总数 |
| `ChangeSet.returned_count` | producer-side result-detail limit 之后的 `ChangeSet.items` 长度 |
| `ChangeSet.omitted_count` | 对 `complete` 或 `truncated` change set，为 `total_count - returned_count` |
| `MediaViewEvaluation.change_count` | 该 evaluation 的 `selector` 对应 grouped `AudioChange` 总数 |

P7-A1 completed result 仍不允许 `partial` change set。因此 `summary.change_count`、
`changes.total_count` 与 `changes.omitted_count` 均为 non-null。`complete` 时 `total_count`
等于 `returned_count`，且 `omitted_count` 为 `0`。`truncated` 时 total 与 omitted count 仍已知，
overall relation/verdict/fidelity 不变。所有 selected audio evaluation 的
`MediaViewEvaluation.change_count` 之和等于 `ChangeSet.total_count`。

Detail limit 是 result-detail limit，不是 comparison-failure limit。当 relation 与 total count
已知后超过 `max_change_items` 或 `max_change_payload_bytes`，结果是 completed result，且
`changes.completeness="truncated"`、`result.completeness="truncated"`、
`selection="source_order_prefix"`、`limit` 等于 configured limit、`limit_reason` 为
`"change_items"` 或 `"change_payload_bytes"`，并在 `aggregating` 记录
`change_details_truncated` warning diagnostic。保留的 item 是 canonical encoded payload 满足
相应 limit 的 whole-item source-order prefix。`0` detail limit 且 `total_count=0` 时仍为
`complete`、`selection="all"`，且无 warning。`0` detail limit 且 `total_count>0` 时是
completed/truncated result，`returned_count=0`、`omitted_count=total_count`；不得变成
`failed/compare_resource_limit`。

Canonical change payload byte 使用 UTF-8 JSON 计算：object key 排序、无 insignificant
whitespace、digest 为 lowercase hex，并使用插入 null field 后的 wire-visible `AudioChange`
object。对于包含 `n` 个 complete change 的 retained prefix，且每个 encoded byte length 为 `b_i`，
array payload byte count 为 `2 + sum(b_i) + max(n - 1, 0)`：`[` 与 `]` byte、每个 retained
item，以及相邻 item 之间的一个 comma byte。Payload accounting 绝不在单个 change item 内截断。

对于 `decoded_samples`，sample change 按以下字段相同的 maximal continuous run 分组：

```text
relation, operation, stream_index, channel, before_step, after_step
```

Replacement run 的 `before_step` 和 `after_step` 都是 `1`；deletion 为 `1` 和 `0`；insertion 为
`0` 和 `1`。P7-A1 保留 RFC 0009 的 length-difference semantics：重叠 sample position 上 decoded
value 不同的部分分组为 `sample_update`；trailing before-only decoded sample 分组为
`sample_delete`；trailing after-only decoded sample 分组为 `sample_insert`。Insert/delete run 只需要
accepted RFC 0009 所规定的 present-side coordinate。

对于 `encoded_bytes`，byte change 按以下字段相同的 maximal continuous byte run 分组：

```text
relation, operation, before_step, after_step
```

`encoded_byte_update` 每一步使用一个 before byte 和一个 after byte。`encoded_byte_delete` 使用一个
before byte 且无 after byte。`encoded_byte_insert` 无 before byte 且使用一个 after byte。

`AudioChange` output ordering 冻结。Producer 先按 canonical relation order 排序，再按 encoded
operation order 排序：`encoded_byte_update`、`encoded_byte_delete`、`encoded_byte_insert`、
`sample_update`、`sample_delete`、`sample_insert`、`format_update`、`channel_update`、
`timing_update`、`metadata_update`。对于 `encoded_bytes`，same-offset deletion 排在
same-offset insertion 之前，以便 middle length 不等的 replacement 保持稳定。剩余 tie-break
依次是 before coordinate、after coordinate、channel（`null` 在具体 channel 前）、before digest、
after digest、before fact 和 after fact。只有在该顺序确定后，才对相邻 compatible operation 做
grouping。

Encoded-byte work accounting 是 deterministic：

| Operation/path | Work increment | Pre-check checkpoint |
| --- | --- | --- |
| Prefix comparison | 每个 byte pair 1 个 work unit | 比较下一个 prefix byte pair 前 |
| Suffix comparison | 每个 byte pair 1 个 work unit | 比较下一个不与 prefix 重叠的 suffix byte pair 前 |
| `encoded_byte_update` grouping | 每个 middle byte pair 1 个 work unit | 扩展 update run 前 |
| `encoded_byte_delete` grouping | 每个 before-only byte 1 个 work unit | 扩展 delete run 前 |
| `encoded_byte_insert` grouping | 每个 after-only byte 1 个 work unit | 扩展 insert run 前 |

`max_compare_work=0` 时，只有 empty-vs-empty `encoded_bytes` 可以完成。算法先执行
longest-common-prefix，再执行 non-overlapping suffix，然后分类 middle。长度相等的 middle 形成一个
`encoded_byte_update` run。不等且非空的 middle 在同一 source offset 形成 delete-before-insert
run。Middle 只存在于一侧时，形成恰好一个 insert 或 delete run。这些规则覆盖 empty input、common
prefix/suffix、长度不等和 unequal-middle replacement，不留 implementation choice。

Metric 计数规则：

| Metric | Count rule |
| --- | --- |
| `audio.samples_changed` | 所有 channel 上 changed decoded sample position 的总数；update 计 overlapping changed position，insert 计 after-side sample position，delete 计 before-side sample position。 |
| `audio.bytes_changed` | changed encoded byte position 的总数；update 算一个 byte position，delete 算一个 before byte，insert 算一个 after byte。 |
| `audio.samples_compared` | compared decoded sample position 数量乘以 selected channel count。 |
| `audio.channels_compared` | 到达 comparison 的 selected channel 数量。 |
| `change_count` | grouped `AudioChange` item 的数量。 |

## Resource limits

所有 resource limit 都是 non-negative integer。Unknown limit name 非法。Default value 由 schema-v6
reader 在 comparison 前插入。RFC 0012 不 rename、remove 或 narrow 任何 accepted
`AudioResourceLimits` field；它只澄清 accepted object 的 accounting scope 与 unit。
`accounting_scope` detail value 是单一 closed enum：
`"single_input"`、`"dual_input_sum"`、`"relation"`、`"comparison"`、
`"comparison_peak"` 和 `"backend_execution"`。

RFC 0009 当前定义 19 个 accepted `AudioResourceLimits` field，包括 reserved
`max_spectral_cells`。RFC 0012 保留全部 19 个 accepted field。若 review note 提到 18-field
object，除非后续 RFC 删除 field，否则以 accepted RFC 0009/RFC 0011 model 为准。

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

Deterministic counter rule：

| Limit | Increment/checkpoint | Stage | Code | Zero behavior |
| --- | --- | --- | --- | --- |
| `max_input_bytes` | bounded snapshot 已知后、retain 前，统计单个 input acquired immutable source bytes。 | `sourcing` | `resource_limit_exceeded` | 只允许 zero-byte source |
| `max_streams` | stream identity 被证明时统计单个 input discovered stream 数量。 | `resolving` | `resource_limit_exceeded` | 任何 discovered stream 都失败 |
| `max_duration_seconds` | header duration 被证明或 payload duration decode 出来时，统计 exact decoded duration 向上取整到 whole seconds。 | `resolving` 或 `decoding` | `resource_limit_exceeded` | 只允许 zero-duration decoded stream |
| `max_sample_rate_hz` | 接受 stream 前统计 declared 或 decoded sample rate。 | `resolving` 或 `decoding` | `resource_limit_exceeded` | 任何 positive sample rate 都失败 |
| `max_channels` | 分配 channel buffer 前统计单个 stream decoded channel count。 | `resolving` 或 `decoding` | `resource_limit_exceeded` | 任何 channel 都失败 |
| `max_decoded_samples_per_channel` | 接受 decoded payload 前统计每个 channel decoded sample count。 | `decoding` | `resource_limit_exceeded` | 每个 channel 只允许 zero decoded sample |
| `max_total_decoded_bytes` | 每次 commit decode buffer 前，累加两个 input 的 materialized decoded PCM bytes。 | `decoding` | `resource_limit_exceeded` | decoded-sample relation 在 payload decode 前失败，除非不需要 decoded byte |
| `max_resident_buffer_bytes` | 分配前记录 live decoded/sample comparison buffer byte peak。 | `normalizing`、`aligning` 或 `comparing` | `compare_resource_limit` | 分配 comparison buffer 前失败 |
| `max_packets` | retain 每个 record 前，累加两个 input 读取的 packet 或 chunk record。 | `resolving` 或 `decoding` | `resource_limit_exceeded` | 读取任何 packet 或 chunk record 前失败 |
| `max_metadata_entries` | 插入前统计单个 input retained metadata entry。 | `resolving` 或 `decoding` | `resource_limit_exceeded` | 任何 retained metadata entry 都失败 |
| `max_metadata_value_bytes` | retain metadata value 前统计单个 metadata value 的 byte 数。 | `resolving` 或 `decoding` | `resource_limit_exceeded` | 任何 non-empty metadata value 都失败 |
| `max_spectral_cells` | materialize spectral block 前累加 generated spectral cell。 | `normalizing` 或 `comparing` | `compare_resource_limit` | spectral relation 在生成 cell 前失败 |
| `max_backend_seconds` | backend start 前与每次 bounded backend wait 后检查 monotonic elapsed backend nanoseconds；serialized seconds 为 elapsed nanoseconds 除以 1,000,000,000 后向上取整的 integer。 | backend execution stage | `resource_limit_exceeded` | 无 backend runtime budget；若需要 backend，则 backend start 前失败 |
| `max_stdout_stderr_bytes` | append capture buffer 前累加 captured backend stdout/stderr bytes。 | backend execution stage | `resource_limit_exceeded` | 任何 captured byte 都失败 |
| `max_temp_bytes` | create 或 extend temp data 前累加 temporary bytes。 | 创建 temp data 的任意 stage | `resource_limit_exceeded` | 任何 temp byte 都失败 |
| `max_materialized_bytes` | retain materialized data 前累加 host-owned snapshot 与 materialized bytes。 | `sourcing` 或 materialization stage | `resource_limit_exceeded` | 任何 materialized byte 都失败 |
| `max_compare_work` | 每个 comparison work batch 前累加 deterministic relation work unit。Encoded bytes 使用下文 byte-work table；decoded samples 每个 compared sample-channel position 为一个 work unit。 | `comparing` | `compare_resource_limit` | 只有 zero-work comparison 可以完成 |
| `max_change_items` | 所有 selected relation count 已知后，统计 whole completed result 中的 grouped changes。 | `aggregating` | completed/truncated result, not a problem code | 计算 relation 与 total count；`total_count>0` 时 emit truncated empty change list；`total_count=0` 时保持 complete |
| `max_change_payload_bytes` | append 每个 complete change item 前统计 canonical result `changes.items` JSON array payload bytes。 | `aggregating` | completed/truncated result, not a problem code | 计算 relation 与 total count；`total_count>0` 时省略 payload-bearing change；`total_count=0` 时保持 complete |

`max_compare_work=0` 只允许可以用 zero relation work 完成的 comparison：identical empty encoded-byte
input，或 relation work 开始前的 metadata-only failure。`max_packets=0` 禁止读取任何 packet 或
WAV chunk record。`max_total_decoded_bytes=0` 对 decoded-sample relation 禁止 decode PCM payload
byte。`max_resident_buffer_bytes=0` 要求 producer 在分配 decoded/sample comparison buffer 前失败。

Integer seconds 使用 exact rational seconds 的 ceiling division：`ceil(numerator / denominator)`，
其中 denominator 为正，且 rational 在 serialization 前已约分。Zero-duration stream 计为 `0`；
任何正的 sub-second duration 计为 `1`。

Limit failure 的 problem detail 使用：

| Detail key | Value |
| --- | --- |
| `limit_name` | 上表中的 name |
| `limit_value` | configured integer |
| `limit_unit` | 上表中的 exact unit string |
| `accounting_scope` | 上文 closed enum 中的一个值 |
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

Encoded-byte alignment 是 immutable source snapshot 上的 byte-index alignment。Producer 先比较
longest common prefix，然后最多 emit 一个 middle run，再比较不与 prefix 重叠的 longest common
suffix。Tie-break deterministic：

1. 最大化 common prefix length。
2. 最大化 common suffix length。
3. before 与 after middle length 相等时，优先使用一个 `encoded_byte_update` run。
4. 否则按 source order emit 一个 `encoded_byte_delete` 和/或一个 `encoded_byte_insert`。

相同 operation 与 step pattern 的 adjacent encoded-byte operation 分组为一个 maximal run。
`audio.bytes_changed` 按上文定义计 update position、deleted before byte 与 inserted after byte；
grouping 不得改变 count。

对于 limit value `0` 的 `encoded_bytes`，stage 与 counter 固定为：

| Limit | Stage when proven | Counter behavior |
| --- | --- | --- |
| `max_input_bytes=0` | `sourcing` | non-empty input 在 relation work 前失败 |
| `max_materialized_bytes=0` | `sourcing` | non-empty materialization 在 relation work 前失败 |
| `max_compare_work=0` | `comparing` | empty-vs-empty 可以完成；任何 byte comparison work 失败 |
| `max_change_items=0` | `aggregating` | relation 与 total count 已计算；`returned_count=0`、`omitted_count=total_count` |
| `max_change_payload_bytes=0` | `aggregating` | relation 与 total count 已知后省略 payload-bearing change |

## Timestamp, delay, and padding recognition

P7-A1 只识别以下 timing、delay 与 padding status fact。它们是上文 registry fact，这里重复列出
recognized source：

| Fact name | Value type | Unit | Absence value | Unknown value | Recognized source |
| --- | --- | --- | --- | --- | --- |
| `duration_seconds` | string rational 或 finite number | `s` | exact decoded duration | no | decoded sample count 与 sample rate；`smpl.sample_period` 可提供 exact scale evidence |
| `timestamp_status` | string | `name` | `"absent"` | `"unknown"` | no source 或 `bext.time_reference` |
| `encoder_delay_status` | string | `name` | `"absent"` | `"unknown"` | recognized delay metadata |
| `encoder_padding_status` | string | `name` | `"absent"` | `"unknown"` | recognized padding metadata |

Status semantic：

- no recognized source 记录 absence value；
- recognized and supported metadata 记录 typed value 与 unit；
- recognized but unsupported metadata 记录 `"unknown"`，unit 使用已知的 documented unit，否则为 `null`；
- malformed recognized metadata 在证明 malformed 的 stage 失败，不变成 `"unknown"` fact。

`smpl.sample_period` 只是 sample-period scale fact。它不得填充 `timestamp_origin`、移动 sample
coordinate，或建立 timestamp epoch。

P7-A1 recognized timing chunk 和 field 是 closed set：

| Chunk/field | Type | Fact affected | Malformed behavior |
| --- | --- | --- | --- |
| no recognized timing chunk | absent | `timestamp_status="absent"` | not an error |
| `bext.time_reference` | unsigned 64-bit sample count | `timestamp_status="present"` | malformed `bext` 在证明 malformed 的 stage 失败 |
| `smpl.sample_period` | unsigned 32-bit nanoseconds per sample | only `duration_seconds` scale evidence | malformed `smpl` 在证明 malformed 的 stage 失败 |
| recognized encoder delay field | non-negative integer samples | `encoder_delay_status="present"` | malformed field 在证明 malformed 的 stage 失败 |
| recognized encoder padding field | non-negative integer samples | `encoder_padding_status="present"` | malformed field 在证明 malformed 的 stage 失败 |

Exact rational string 使用以下 grammar：

```text
rational = numerator "/" denominator
numerator = "0" / (["-"] nonzero_digit *digit)
denominator = nonzero_digit *digit
```

Denominator 始终为正。Serialized rational 必须约分到 lowest terms，不得包含 whitespace 或 plus sign，
且只能使用 ASCII digit。只有在表格允许 finite number 的位置才可使用 decimal finite JSON number；
exact duration 与 sample-period fact 在 binary64 会丢失信息时使用 rational string。

所有其他 chunk 只有在 RFC 0011 已允许它们作为 bounded chunk fact 时才是 metadata fact。它们不得静默影响
sample coordinate、duration、alignment 或 equality。

## Problem message and details

`problem.message` 是用户可见解释性 prose 的唯一位置。`problem.details` 是 structured value 的唯一位置。
Detail value 必须是 string、integer、finite JSON number、boolean、`null`，或 RFC 0011
`expected`/`actual` array，且 array element 只能是 string、integer、finite JSON number 或 boolean。
其他 array 与所有 object 仍非法，除非后续 schema revision 明确允许。

RFC 0012 保留并 supersede RFC 0011 problem-details allowlist，只增加上文所需的 resource
accounting、operation 与 fact key。Problem detail object 是 closed object，并使用下表 key order。
Optional key 在 unavailable 时省略；除非 type 明确包含 `null`，否则不填 `null`。

| Key | Type |
| --- | --- |
| `stage` | canonical lifecycle stage string |
| `code` | stable problem code string |
| `media_kind` | `"audio"` |
| `relation` | selected relation string |
| `backend` | backend string |
| `profile` | profile string |
| `input_side` | `"before"`、`"after"` 或 `"both"` |
| `byte_offset` | non-negative integer |
| `chunk_id` | four-byte ASCII chunk ID string |
| `field` | schema 或 header field name |
| `value_kind` | `"string"`、`"integer"`、`"finite_number"`、`"boolean"`、`"null"` 或 `"array"` |
| `expected` | string、finite number、boolean，或这些 primitive value 的 array |
| `actual` | string、finite number、boolean，或这些 primitive value 的 array |
| `limit_name` | accepted resource limit name |
| `limit_value` | non-negative integer |
| `limit_unit` | resource table 中的 exact unit string |
| `accounting_scope` | closed accounting-scope enum 中的一个值 |
| `measured_value` | `limit_unit` 中的 non-negative integer |
| `operation` | accepted `AudioChange.operation` string |
| `fact_name` | accepted `AudioFact.name` string |

Detail value 不得包含 backend stderr、exception class name、host path、source filename、safe label、
解释性 sentence 或 arbitrary dictionary。

## Canonical vectors

这些 vector 是 acceptance test 的 normative example。它们是 default insertion 之后、任何
producer-side result-detail truncation 之前的完整 schema-v6 outcome envelope。PC-F 是 explicit
predecessor upgrade vector：它展示 v1-v5 upgrader 添加的 schema-v6 defaulted media field，且
不推断 audio fact。PC-G 到 PC-I 冻结 canonical detail-limit truncation behavior。

### Vector PC-A： equal empty encoded bytes

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
      "implementation_version": "p7-a1-proposed",
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

### Vector PC-B： one continuous sample update from real WAV payloads

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
          "before_digest": "sha256:e10fcab70a6455011b76f60e9774b33ed52c4aa9ef51e2c4a1cfcda3003c29f1",
          "after_digest": "sha256:e493bc94d15fc37e05153d7b7649ab038d8e88a5e81e040c8878a36e11dc3b4f",
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
      "implementation_version": "p7-a1-proposed",
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

### Vector PC-C： byte insert with zero WAV assumptions

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
      "implementation_version": "p7-a1-proposed",
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

### Vector PC-D： decoded resource limit failure

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

### Vector PC-E： equal decoded facts from one-sample WAV payloads

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
      "implementation_version": "p7-a1-proposed",
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
        "value": "unknown",
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
        "name": "duration_seconds",
        "value": 0.000125,
        "unit": "s",
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

### Vector PC-F： predecessor upgrade defaults

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

### Vector PC-G： dual-relation item-limit truncation

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
          "value": 2
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
          "value": 2
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
          "size_bytes": 72,
          "sha256": "b33d2b6174518c106ffecb640edd4eac74a67203ed70088953fd91ee4e431fd7",
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
          "max_change_items": 1,
          "max_change_payload_bytes": 4194304
        }
      },
      "transformations": [],
      "comparator_id": "builtin.audio",
      "comparator_version": "1",
      "algorithm_id": "audio.encoded_bytes.exact.v1",
      "implementation_version": "p7-a1-proposed",
      "seeds": [],
      "resources": [
        {
          "name": "max_change_items",
          "limit": 1,
          "used": 2
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
        "completeness": "complete",
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

### Vector PC-H： payload-limit zero truncation

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
      "implementation_version": "p7-a1-proposed",
      "seeds": [],
      "resources": [
        {
          "name": "max_change_payload_bytes",
          "limit": 0,
          "used": 2
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

### Vector PC-I： item-limit zero with zero total remains complete

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
      "implementation_version": "p7-a1-proposed",
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

## Acceptance conditions

只有 reviewers 确认以下全部事项后，本 amendment 才可 accepted：

1. RFC 0010 Option A/SP1-SP6，以及实际 P4-C1、P5-A1/schema-v4、P6-C0/schema-v5 predecessor
   gate 仍为必要条件。
2. Schema-v6 仍 exclusively audio。
3. Decoded-sample comparison 仍只限 stdlib WAV/PCM。
4. `encoded_bytes` 绕过 WAV probe/decode，并接受任意 byte stream。
5. Equal result carrier 与 complete decoded-audio fact carrier 使用 accepted schema-v6、
   `MediaViewEvaluation` 和 `AudioFact` shape。
6. Continuous grouping 和 metric count 是 deterministic，且不受 producer-side result-detail
   truncation 影响。
7. Accepted `AudioResourceLimits` object 保持完整；本 amendment 只增加 scope 与 unit clarification。
8. Problem prose 只在 `problem.message`；structured data 只在 `problem.details`。
9. 英文与中文文本保持一致。
10. 本 Proposed amendment 不启动 P7-A1 implementation、video、UI、FFmpeg、dependency 或 PR 工作。
