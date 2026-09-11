# RFC 0015：Schema-v4 Backend Version Evidence 修订

[English documentation](0015-schema-v4-backend-version-evidence-amendment.md)

- 状态：Proposed
- 日期：2026-09-11
- 决策 ID：BVE-1-BVE-8
- 负责人：Platydiff maintainers
- 修订：[RFC 0013](0013-p5a1-image-wire-contract-amendment_zh.md)
- 相关 RFC：[RFC 0005](0005-third-party-plugin-discovery-sdk-and-compatibility_zh.md)、
  [RFC 0007](0007-image-comparison_zh.md)、
  [RFC 0008](0008-source-code-and-pdf-comparison_zh.md) 与
  [RFC 0009](0009-audio-and-video-comparison_zh.md)
- 证据基线：`main` 的 `84c06d3`
- 既有实现授权：用户已于 2026-09-11 单独授权 P5-A1，且实现正在进行；本 RFC 不授予
  新权限，在本 amendment 获得接受并完成实现前，P5-A1 仍不得合并

## 摘要与授权边界

RFC 0013 要求 schema-v4 attempt 的 backend ID 非 null 时 backend version 也非 null，
并要求 backend ID 为 null 时 backend version 也为 null。它同时要求所有有效 v1、v2、v3
outcome 无损且不虚构 wire fact 地升级到 v4。这些要求与已实现 predecessor 冲突。

已实现 schema-v1 text pipeline 记录 `backend_id="stdlib"` 的 selected attempt；schema v1
没有 backend-version member。已实现 v1-to-v2 upgrader 保留该 ID，并在 completed outcome 中
把 comparator version 记录为 capability version，同时保持 `backend_version=null`。Schema-v2
和 schema-v3 built-in attempt 也允许两个 backend field 各自独立缺失。因此 blanket v4 pairing
requirement 无法接受全部有效 predecessor attempt。

本 Proposed amendment 为每条 schema-v4 attempt 增加显式且 closed 的 evidence state。它既不
虚构 version，也不删除 ID，从而保留 predecessor fact；同时 native schema-v4 producer 继续受
严格 paired-backend rule 约束。用户已于 2026-09-11 单独授权 P5-A1 实现，且相关工作正在
进行。本 RFC 不扩张该授权，也不授权 image runtime、P5-A2/P5-A3、Phase 6、Phase 7、artifact、
automatic detection、plugin 或 UI 工作。

本 RFC 处于 Proposed 时 P5-A1 不得合并。如果 BVE-1 至 BVE-8 获得接受，既有 P5-A1 授权
继续覆盖本 exact amendment 及 RFC 0013 其余契约的实现；实现仍须接受独立 code review，且
不得扩大既有 scope。

## Predecessor 证据与矛盾

相关的已实现 v1 attempt 等价于：

```json
{
  "backend_id": "stdlib",
  "capability_id": "text",
  "disposition": "selected",
  "reason_code": null
}
```

Completed text outcome 完成精确 v1-to-v2 upgrade 后，其七个 schema-v2 field 包含：

```json
{
  "backend_id": "stdlib",
  "backend_version": null,
  "capability_id": "text",
  "capability_version": "0.1.0.dev0",
  "disposition": "selected",
  "provider": null,
  "reason_code": null
}
```

该 version string 是当前 baseline 的证据，不是永久冻结的项目版本。这里的不变量是：即使
predecessor 没有 backend-version fact，`capability_version` 仍可能非 null。

`CapabilityAttemptV2` 只为 provider-backed attempt 验证 backend ID/version pairing。因此
没有 provider 的 built-in attempt 可以携带四种 nullability pair 中的任意一种。无损
v3-to-v4 migration 必须覆盖全部四种组合，包括不常见但有效的“backend ID 为 null、backend
version 非 null” predecessor shape。本 RFC 闭合两种 asymmetric case，而不是只对当前 text
fixture 做特判。

下列解决方式被拒绝：

- 合成 `"unknown"`、Python version、Platydiff version 或任何其他 backend version；
- 清除 `backend_id="stdlib"` 或丢弃 predecessor backend version；
- 把 unpaired backend identity 当作普通 native-v4 provenance 接受；
- 让已经承诺的 predecessor upgrade 变成 partial 或静默 fallible。

## Proposed 决策

| ID | Proposed decision |
| --- | --- |
| BVE-1 | 增加 public `BackendVersionEvidence` `StrEnum`，且只包含 `not_applicable`、`recorded`、`predecessor_unpaired`。 |
| BVE-2 | 为每条 `CapabilityAttemptV4` 增加 required schema-v4 wire member `backend_version_evidence`；保留 `backend_components` 与全部七个 inherited field。 |
| BVE-3 | 只把 `predecessor_unpaired` 用作显式 migration declaration；此时 attempt 必须没有 provider、恰有一个 backend identity field 非 null，且没有 component。 |
| BVE-4 | Native v4 producer 只允许产生 `not_applicable` 或 `recorded`；不得使用 `predecessor_unpaired`。 |
| BVE-5 | 每个 v1/v2/v3-to-v4 upgrade 都派生 evidence state，且不得修改 inherited field。 |
| BVE-6 | 对可表示的 v4-to-v3 downgrade，把 evidence state 视为派生的 v4 encoding fact；两个 predecessor backend field 必须精确保留。 |
| BVE-7 | 两个 schema-v4 canonical fixture 都增加该字段，并冻结下述 exact key set、canonical order、rejection matrix、migration fixture 与 predecessor-byte stability test。 |
| BVE-8 | Schema v5 与 v6 必须继承并保留修正后的 v4 evidence contract；该要求不授予 successor 实现权限。 |

## Public model 与 closed state

Proposed public addition 为：

```python
class BackendVersionEvidence(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    RECORDED = "recorded"
    PREDECESSOR_UNPAIRED = "predecessor_unpaired"


@dataclass(frozen=True, slots=True)
class CapabilityAttemptV4(CapabilityAttemptV2):
    backend_components: tuple[BackendComponentVersion, ...] = ()
    backend_version_evidence: BackendVersionEvidence = (
        BackendVersionEvidence.NOT_APPLICABLE
    )
```

Python default 让 backend-free direct schema specimen 保持简洁；它不使 JSON member 变为
optional。Schema-v4 reader 要求该 member 存在，constructor 根据 attempt 的其他 field 验证它。
`BackendVersionEvidence` 是 foundational type，从 `platydiff.core.models` 与
`platydiff.core` export，不从 curated top-level package export。

只有下列组合有效：

| Evidence | `backend_id` | `backend_version` | `provider` | `backend_components` | Origin |
| --- | --- | --- | --- | --- | --- |
| `not_applicable` | null | null | null 或非 null | empty | Native v4 或 upgrade |
| `recorded` | non-null | non-null | null 或有效 provider | empty 或有效 sorted components | Native v4 或 upgrade |
| `predecessor_unpaired` | 恰有一个 backend field 非 null | 恰有一个 backend field 非 null | null | empty | 仅显式 v1/v2/v3-to-v4 upgrade |

最后一行的“恰有一个”适用于 `(backend_id, backend_version)` pair：一个值非 null，另一个值为
null。表中的两个 cell 有意描述相同 XOR constraint。

其他组合全部无效。尤其是 component 要求 `recorded` backend ID/version pair；provider-backed
attempt 继续受 inherited pairing rule 约束，绝不可能是 `predecessor_unpaired`。
`capability_version` 不参与这三个 state，并独立保留。

`predecessor_unpaired` 是 migration producer 作出的 wire declaration。与 comparator version、
provider identity、hash 及其他 provenance 一样，detached reader 验证其 closed shape，但无法独立
证明 producer history。项目自有 native-v4 writer 与 outcome factory 绝不允许产生该状态；测试
负责强制此 producer obligation。

## Exact wire key 与 canonical order

Schema-v4 attempt object 恰有九个 required member。RFC 0013 canonical writer 对 object key
递归执行 lexicographic sort，因此 exact canonical order 是：

```text
backend_components
backend_id
backend_version
backend_version_evidence
capability_id
capability_version
disposition
provider
reason_code
```

Reader 继续不依赖 object order，但拒绝 missing 或 unknown member。Schema-v1 reader 只接受既有
四个 attempt key；schema-v2 与 schema-v3 reader 只接受既有七个 key，并拒绝
`backend_components` 与 `backend_version_evidence`。Schema-v4 reader 要求两个新增 key 都存在；
unknown evidence value 必须拒绝，不得视为 future extension。

RFC 0013 中“`backend_components` 是唯一新增 attempt member”的表述由本 RFC 取代：schema v4
恰好增加这两个 member。Version-explicit attempt serializer/reader signature 除此以外保持不变。

## Upgrade contract

RFC 0013 的 exact composition 保持不变：

```text
upgrade_outcome_v3_to_v4(v3) -> v4
upgrade_outcome_v2_to_v4(v2) = upgrade_outcome_v3_to_v4(upgrade_outcome_v2_to_v3(v2))
upgrade_outcome_v1_to_v4(v1) = upgrade_outcome_v2_to_v4(upgrade_outcome_v1_to_v2(v1))
```

对于每条 predecessor attempt，v3-to-v4 step 保留全部七个 field，设置
`backend_components=[]`，并只派生一个 evidence value：

| Predecessor pair `(backend_id, backend_version)` | V4 evidence |
| --- | --- |
| `(null, null)` | `not_applicable` |
| `(non-null, non-null)` | `recorded` |
| 恰有一个值非 null | `predecessor_unpaired` |

Helper 不得从 capability ID、capability version、Python runtime、installed distribution 或当前
Platydiff version 推断 provenance。它不得修改 provider、disposition、reason 或 ordering。同一映射
适用于 completed、unavailable 与 failed outcome。

## Downgrade contract

`downgrade_outcome_v4_to_v3` 保留 RFC 0013 的全部 representability rejection，包括 image-only
fact、`unsupported_image_profile` 与非空 backend component。当这些 gate 全部通过后，它验证
evidence state，只删除 `backend_version_evidence`，并精确保留 `backend_id` 与
`backend_version`。

删除该字段是无损的：对于可 downgrade 的 v4 attempt，evidence value 可以按上述 upgrade table
从两个被保留的 predecessor field 唯一派生。重新 upgrade 得到的 v3 attempt 会恢复相同 evidence
state。Downgrade 不得制造 backend pair，也不得拒绝其他方面可表示的
`predecessor_unpaired` attempt。

## Canonical fixture 与 compatibility test

RFC 0013 要求的两个 schema-v4 contract specimen 仍是 P5-A1 唯一的 canonical v4 JSON 文件。
它们的 backend-free image attempt 增加：

```json
"backend_version_evidence": "not_applicable"
```

只有在该字段存在后才冻结其 exact byte 与 expected digest。既有 schema-v1、schema-v2 与
schema-v3 fixture byte/digest 不得改变。

P5-A1 implementation gate 增加证明下述事实的测试：

1. 实际 v1 text outcome 的 `backend_id="stdlib"` 经 v2、v3 升级到 v4
   `predecessor_unpaired` attempt，且 inherited field 不变；
2. 四种 predecessor backend nullability pair 都按 upgrade table 映射，包括 provider-free 的
   reverse-unpaired v2/v3 specimen；
3. 升级得到的 completed、unavailable、failed shape 都通过 schema-v4 writer/reader round-trip；
4. 每条可表示的 upgraded attempt 都 downgrade 为 backend field byte-equivalent 的 v3，并在
   re-upgrade 后恢复相同 evidence state；
5. 两个 image contract fixture 使用 `not_applicable`，包含 exact 九个 attempt key，并保持
   RFC 0013 的全部 image binding；
6. 直接构造且有版本的 native-v4 backend 使用 `recorded`；
7. 拒绝 mismatched evidence、unpaired native-v4 producer output、provider-backed unpaired
   identity、没有 `recorded` 的 component、missing/extra key 与 unknown evidence string；
8. 全部既有 v1-v3 fixture 保持 byte-identical，并且每个 predecessor reader 都拒绝两个
   v4-only attempt member。

项目正常检查及 RFC 0013 的完整 P5-A1 acceptance matrix 仍为必需。本测试不增加 image decoder、
backend、runtime registration 或 CLI route。

## Public model 与 serialization validation 分层

RFC 0013 的 image cross-field invariant 适用于 public `DiffResultV4` 的直接构造，不能整体延后到
serialization。当 `provenance.spec.kind="image"` 时，`DiffResultV4.__post_init__()` 必须拒绝
empty、missing、duplicate、extra 或 ordering 错误的 image `resources` tuple。它要求完整的 RFC
0007 resource-name set：

```text
image.{before|after}.{input_bytes|metadata_wire_bytes|
metadata_decompressed_bytes|icc_profile_bytes|pixels|decoded_bytes}
image.compare.sample_pairs
image.changes.items
image.changes.payload_bytes
```

Public-model layer 还验证所有能从 model value 计算的 cross-field relationship：normalized-spec
limit、每侧 decode fact、dimension/channel arithmetic、comparison count、change-item count、
summary/metric/evaluation binding、ordering，以及本 RFC 的 evidence-state matrix。因此直接构造
且 resources 为空的 image `DiffResultV4` 在调用 writer 前就无效。

只有依赖 exact versioned JSON representation 的关系才属于 serializer-boundary validation。
具体而言，`image.changes.payload_bytes.used` 必须等于 retained change 的
`serialized_change_size(item, schema_version=4)` 之和。V4 encoder 在输出 byte 前检查该等式；
v4 reader 在 version-explicit decoding 后、返回 outcome 前检查。直接构造可以验证该 resource
存在、唯一、有序、limit 与 normalized spec 一致且 value 非负，但只有 serializer-boundary check
运行后才能声称 payload-byte equality 已建立。Canonical fixture construction test 必须覆盖两层。

## Schema-v5 与 schema-v6 继承

Schema-v5 source/PDF 与 schema-v6 audio 是 corrected v4 contract 的 successor。它们未来的
attempt model、exact reader/writer、upgrade helper 与 compatibility fixture 必须原样携带
`backend_version_evidence`。Successor-native producer 遵循同一 native rule，不能产生
`predecessor_unpaired`；migration chain 则保留该 declared predecessor state。

P6-C0 开始前，其 coordinator 必须依据本 RFC 重新验证已经合并的 schema-v4 reader、writer、
全部 predecessor upgrade、downgrade 与 fixture。Phase 7 schema-v6 closure 或实现开始前，也必须
对已合并 v4/v5 chain 执行同一验证。Source-code、PDF、audio、video comparison semantics 均不
改变；本 RFC 不满足任何一个 phase 的 implementation gate。

## 考虑过的替代方案

### Execution-level migration marker

Outcome-level 或 execution-level predecessor marker 可以用较少重复 wire field 来设置 exception
gate，但会使 detached `CapabilityAttemptV4` 无法自行验证，对 mixed attempt history 过于粗糙，
并让 exact composed upgrade 更复杂。Per-attempt evidence 保持 public attempt contract closed。

### 放宽 native-v4 pairing rule

允许任意 provider-free、component-free unpaired attempt 不需要新 wire key，但 detached reader
无法区分 migrated predecessor 与信息不足的 native-v4 provenance。这会丢失 RFC 0013 试图增加的
evidence quality。

### 拒绝或改写 predecessor fact

Partial upgrade、虚构 version string 或清除 ID 都违反已接受的 lossless-migration rule，不能作为
compatibility strategy。

## 接受与合并门禁

本 RFC 状态为 Proposed。必须由人类接受 BVE-1 至 BVE-8 后才能改为 Accepted。Documentation
amendment 必须先于 P5-A1 合并。随后 implementation owner 必须从 amended `main` 新建 replacement
P5-A1 branch，或把 amended `main` 非重写地 merge 进既有 P5-A1 branch。该 branch 实现 exact
contract，只重新生成 schema-v4 fixture，并在自身 review 前通过完整 Python 与 compatibility
check。禁止 rebase、force-push 及其他 shared-history rewrite。

接受本 RFC 不产生新的实现权限；用户在 2026-09-11 的既有 P5-A1 dispatch 是正在进行的
contract-only 实现的唯一授权。任何后续阶段都不得把 Proposed 文本或未合并 P5-A1 branch 当作
predecessor evidence。
