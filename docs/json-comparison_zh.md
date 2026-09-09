# JSON 比较

[English documentation](json-comparison.md)

Phase 4 门禁 P4-A1 实现 [RFC 0006](rfcs/0006-structured-data-comparison_zh.md)
中的 JSON 部分。它不增加运行时依赖，也不实现 YAML、table、array、structured auto
detection 或新版 plugin SDK。

## 入口与 schema

下面两个 CLI alias 执行同一内建路径：

```bash
platydiff json before.json after.json
platydiff compare --type json before.json after.json
```

Python 调用方把 `JsonCompareSpec` 传给既有三参数 `compare`。所有 JSON outcome 都使用
schema v3，包括 sourcing、decoding 与 comparison failure。既有直接 text、binary、auto
比较保持 schema v1；既有 SDK-v1.1 plugin-host 比较保持 schema v2。`PluginHost` 会把
JSON intent 拒绝为 resolving-stage `capability_unavailable`；JSON CLI 路径则会在 plugin
discovery 前把 plugin 相关参数拒绝为用法退出码 `2`。

schema-v3 reader 也接受 v1 与 v2。显式迁移使用 `upgrade_outcome_v1_to_v3` 或
`upgrade_outcome_v2_to_v3`。`downgrade_outcome_v3_to_v2` 只有在验证 legacy intent/change，
或 terminal outcome 保留了 legacy host context 后才成功；它绝不会丢弃 structured change，
也不会在缺少 legacy provenance 时猜测。

## 相等性与 change

parser 只接受一个 strict RFC 8259 value，后面可以有 JSON whitespace。UTF-8 是严格的；
只有 `utf-8-sig` 会移除 BOM。comment、trailing comma、重复 decoded key、NaN、infinity
与不成对 surrogate escape 都以 `decode_error` 失败。

encoding 选项只适用于 byte 与 path source。`TextSource` 已经完成 decoding，会严格按照调用方
提供的 Unicode 文本解析；尤其不会静默移除开头的 U+FEFF，因此该字符会使 JSON 无效。

mapping 按 decoded Unicode key 的 code-point 顺序比较；member 顺序与 escape 拼写被忽略。
sequence 按位置比较。string 不做 case fold、whitespace normalization 或 Unicode
normalization。change 使用 canonical RFC 6901 JSON Pointer 与确定性 depth-first pre-order。
整个新增或删除的 subtree 只在最高 pointer 产生一个 change；不推断 move。

默认 `number_mode="value"` 不使用 binary floating point，而是比较 sign、coefficient 与
调整后的十进制 exponent，因此 `1`、`1.0` 与 `1e0` 相等，signed zero 也相等。
`number_mode="lexical"` 则精确比较每个合法 source token。

result 记录 `json.compared_values`、`json.equal_values` 与 `json.changed_values`；equal 加
changed 等于 compared，changed 等于 `changes.total_count`。唯一 evaluation
`json.semantic_equality` 只在 changed values 为零时通过。比较会先完整结束再截断明细，
所以限制不会弱化 relation、verdict、total 或 metric。

## Fact、digest 与隐私

`detail_mode="values"` 返回 typed scalar fact 或有界、非递归的 subtree count。
`detail_mode="digest_only"` 在 rendering 前省略所有 fact，但保留比较真值与确定性 evidence
digest。evidence digest 是带 domain separation 的 SHA-256 完整性指纹，不是加密或匿名
脱敏：低熵 value 可能被猜出，path、input hash、type、count 与 digest equality 仍然可见。
两种 outcome 都应作为 source-derived metadata 保护。

terminal renderer 会 escape path 与 fact 中的 control/bidirectional character。JSON
renderer 输出精确、已验证的 schema-v3 envelope。renderer 不会重读输入，也无法恢复省略的
fact。

## 限制与失败

所有 limit 都接受不超过 `2**53` 的非负 exact integer：

| CLI 参数 | 默认值 | 含义 |
| --- | ---: | --- |
| `--max-input-bytes` | 16 MiB | decoding 前每个 source 的原始 byte |
| `--max-scalar-bytes` | 1 MiB | 单个 decoded string 或 key 的 UTF-8 byte |
| `--max-depth` | 256 | 相对 root 的 container depth |
| `--max-nodes` | 1,000,000 | 每个 source 解析出的 value node |
| `--max-number-digits` | 10,000 | 单个合法 number token 的 digit |
| `--max-abs-exponent` | 1,000,000 | 调整后十进制 exponent 的绝对值 |
| `--max-compare-work` | 5,000,000 | 访问的 paired/unmatched tree node |
| `--max-change-items` | 10,000 | 返回的 source-order change |
| `--max-change-payload-bytes` | 4 MiB | 返回 change 的 compact UTF-8 schema byte |

输入边界在实际 sourcing 或 decoding stage 以 `resource_limit_exceeded` 失败；work 耗尽时在
comparing stage 以 `compare_resource_limit` 失败。change item 或 payload 耗尽会返回 completed
result，其中包含 `truncated` source-order prefix 和 `change_details_truncated` diagnostic。
CLI 退出码保持：pass 为 `0`，completed fail 为 `1`，用法错误为 `2`，unavailable、failed
或 renderer failure 为 `3`。
