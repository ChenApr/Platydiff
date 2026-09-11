# RFC 0013：P5-A1 图片 Wire Contract 修订

[English documentation](0013-p5a1-image-wire-contract-amendment.md)

- 状态：Accepted
- 日期：2026-09-10
- 接受日期：2026-09-11
- 负责人：Platydiff maintainers
- 修订：[RFC 0007](0007-image-comparison_zh.md)
- 前驱：[RFC 0010](0010-schema-predecessor-and-phase6-contract-amendment_zh.md)
- 后续修订：[RFC 0015](0015-schema-v4-backend-version-evidence-amendment_zh.md)
  （Proposed；仅在接受后生效，问题解决前阻塞 P5-A1 合并）
- 实现授权：无

## 摘要

本 Accepted amendment 闭合 P5-A1 派发前必须决定的 wire-level contract，且不改变
RFC 0007 已接受的 I1-I16 图片语义。它冻结 P5-A1 边界、public enum type、五种图片
transformation payload、仅用于 schema 的 provenance specimen、
`unsupported_image_profile` problem、terminal presentation、downgrade rule 与
compatibility acceptance criteria。

当前证据基线是 2026-09-11 的 `origin/main` `b84603f`。PR #20 已合并独立审阅通过的
P4-C1 实现及冻结 v1-v3 compatibility fixture，因此 schema predecessor gate 已满足。
接受本 RFC 仍不授权或派发 P5-A1 实现。

## 授权边界

P5-A1 严格为 contract-only。仅当人类随后单独授权实现时，P5-A1 才可添加：

- schema-v4 public model、validation、serialization 与显式 migration helper；
- 由 public model 直接构造的 schema-v4 canonical compatibility fixture，以及
  round-trip、rejection、export 与 predecessor-stability test；
- 对已验证 schema-v4 outcome 的有界 terminal rendering；
- 同步的 contract documentation。

P5-A1 不得添加 image decoder、scanner、comparator implementation、capability registration、
Pillow 或其他 backend、`image` dependency extra、image CLI command/option、automatic
detection、plugin image support、source-derived artifact、preview、heatmap、HTML/TUI/desktop
UI 或图片 corpus 文件。由于没有 runtime capability registration，
`compare(..., ImageCompareSpec(...))` 仍不可用。Canonical `CompletedOutcomeV4` 是测试直接
构造的 schema specimen，不是 PNG 已被 decode 或 compare 的证据。

实际 P4-C1 实现及其 v1-v3 compatibility fixture 现已合并到 `main`，并已针对下述
类型完成独立验证。这只清除 predecessor condition。P5-A1 仍未实现，且在人类单独派发前
不得启动；后续若发现 predecessor 不一致，必须回调本 RFC，不得在代码中顺手修补。

## 已接受的决策

| ID | Accepted decision |
| --- | --- |
| P5A1-1 | 按上述边界将 P5-A1 严格限定为 contract-only。 |
| P5A1-2 | 可复用的 public 图片选项使用具名 `StrEnum`；只有 discriminator 与固定 tile-size 常量保留 `Literal`。 |
| P5A1-3 | 精确冻结下述五种 transformation parameter object；missing/unknown key 均拒绝。 |
| P5A1-4 | 闭合完整 schema-v4 type/export lattice，并把 completed/failed fixture 定义为具有精确 built-in attempt/provenance binding、null backend identity、空 backend-component evidence 且不声称 Pillow 的直接 contract specimen。 |
| P5A1-5 | 只在 schema-v4 failed-problem allowlist 增加 `unsupported_image_profile`，其 details object 为 closed；v1-v3 reader 继续拒绝它。 |
| P5A1-6 | 只增加下述有界 terminal projection；仅当所有事实都能无损表达于目标前驱时才允许 downgrade。 |

用户已于 2026-09-11 批准 P5A1-1 至 P5A1-6 及本 RFC 的完整 closure rule。该批准
接受 contract，但不授予实现权限。

## Public Python 与 wire enums

Public dataclass field 中可复用的选择使用以下具名 `StrEnum`。Member name 是 Python API，
value 是 serialized wire string：

```python
class ImageSemantic(StrEnum):
    DECODED_SAMPLES = "decoded_samples"


class ImageFormat(StrEnum):
    PNG = "png"


class ImageOrientationPolicy(StrEnum):
    STORED = "stored"


class ImageColorProfilePolicy(StrEnum):
    REQUIRE_EXACT = "require_exact"


class ImageAlphaPolicy(StrEnum):
    STRAIGHT = "straight"


class ImageAlignmentPolicy(StrEnum):
    EXACT_DIMENSIONS = "exact_dimensions"


class ImageMetadataPolicy(StrEnum):
    IGNORE_NON_INTERPRETIVE = "ignore_non_interpretive"


class ImageSampleMode(StrEnum):
    L = "L"
    LA = "LA"
    RGB = "RGB"
    RGBA = "RGBA"


class ImageChangeOperation(StrEnum):
    DESCRIPTOR_REPLACE = "descriptor_replace"
    TILE_REPLACE = "tile_replace"


class ImageChangeComponent(StrEnum):
    DIMENSIONS = "dimensions"
    PIXEL_FORMAT = "pixel_format"
    COLOR_DESCRIPTION = "color_description"


class ImageDecodeProfile(StrEnum):
    STATIC_PNG_8BIT_V1 = "static_png_8bit_v1"


class UnsupportedImageProfileReason(StrEnum):
    WRONG_CODEC = "wrong_codec"
    MULTIPLE_FRAMES = "multiple_frames"
    UNSUPPORTED_BIT_DEPTH = "unsupported_bit_depth"
    UNSUPPORTED_COLOR_TYPE = "unsupported_color_type"
    TRANSPARENCY_EXPANSION_REQUIRED = "transparency_expansion_required"
    UNKNOWN_CRITICAL_CHUNK = "unknown_critical_chunk"
```

`ImageCompareSpec.kind` 保持 `Literal["image"]`，`ImageChange.kind` 保持
`Literal["image_change"]`，`ImageCompareSpec.tile_size` 保持 `Literal[64]`；它们是 closed
discriminator 或 invariant，不是可扩展 choice。`ImageChange.component` 为
`ImageChangeComponent | None`，其余已接受 image-spec field 使用上方对应 enum。

Transformation parameter 继续是经过验证的 JSON object，不新增 public Python model export。
其中 enum-valued field 使用相同 wire string，但不扩大 top-level API surface。

## Closed JSON 规则

本 RFC 指定的 object 均为 closed：所有列出的 key 必填，任何额外 key 均拒绝。JSON integer
拒绝 boolean。Count/size 是非负 exact integer；width/height 是正 exact integer；SHA-256 是
64 位小写十六进制。声明有顺序或唯一性的 array 必须遵守约束并保留文中大小写。

Role object 恰好要求 `before`/`after` 两个 member；语义来自 key 而非 object-member order。
Pretty example 只说明语义，不声称 canonical writer order；canonical writer 与
order-insensitive reader rule 在下方冻结。

### 共享 decode facts

`ImageDecodeFacts` 精确包含以下 key/type：

```json
{
  "mode": "RGBA",
  "width": 1,
  "height": 1,
  "frame_count": 1,
  "ihdr": {
    "bit_depth": 8,
    "color_type": 6,
    "interlace_method": 0
  },
  "resources": {
    "input_bytes": 67,
    "metadata_wire_bytes": 0,
    "metadata_decompressed_bytes": 0,
    "icc_profile_bytes": 0,
    "pixels": 1,
    "decoded_bytes": 4
  }
}
```

- `mode` 是 `ImageSampleMode` value；`frame_count` 固定为 `1`；`bit_depth` 固定为 `8`。
- `L`、`LA`、`RGB`、`RGBA` 对应的 `color_type` 分别为 `0`、`4`、`2`、`6`；其他组合无效。
- `interlace_method` 是 `0` 或 `1`。
- `pixels == width * height`；`decoded_bytes == pixels * channel_count`，四种 mode 的
  channel count 依次是 `1`、`2`、`3`、`4`。

六个 resource value 是 observed fact；configured limit 单独记录为 `ResourceUsage`，不在此重复。

### 1. `image.png.decode`

Stage 固定为 `decoding`，parameters 为：

```json
{
  "profile": "static_png_8bit_v1",
  "before": { "...": "ImageDecodeFacts" },
  "after": { "...": "ImageDecodeFacts" }
}
```

`profile` 是 `ImageDecodeProfile`。本 object 禁止 backend、backend version、provider 与
implementation version。Runtime backend identity 只属于 selected capability attempt；
comparator/algorithm identity 只属于 comparison provenance。

### 2. `image.orientation.stored`

Stage 固定为 `normalizing`：

```json
{
  "policy": "stored",
  "before": { "exif_present": false, "exif_wire_bytes": 0 },
  "after": { "exif_present": false, "exif_wire_bytes": 0 }
}
```

`policy` 是 `ImageOrientationPolicy`。`exif_present` 是 boolean，`exif_wire_bytes` 是非负
exact integer；present 为 false 时 byte count 为零，true 时为正。不允许 EXIF tag/payload。

### 3. `image.color.native_exact`

Stage 固定为 `normalizing`：

```json
{
  "policy": "require_exact",
  "before": {
    "present_chunks": [],
    "description_digest": "71d104a33d792f584bb9f5ed92ab1feee8625a59b3012513d08d905fa4a08145"
  },
  "after": {
    "present_chunks": [],
    "description_digest": "71d104a33d792f584bb9f5ed92ab1feee8625a59b3012513d08d905fa4a08145"
  }
}
```

`policy` 是 `ImageColorProfilePolicy`。`present_chunks` 是下列 fixed order 的 unique
subsequence：`cHRM`、`gAMA`、`iCCP`、`sBIT`、`sRGB`、`cICP`、`mDCV`、`cLLI`。
`description_digest` 是 RFC 0007 canonical color-description digest。不允许 raw/decoded profile value。

### 4. `image.alpha.straight`

Stage 固定为 `normalizing`：

```json
{
  "policy": "straight",
  "before": {
    "mode": "RGBA",
    "bands": ["R", "G", "B", "A"],
    "has_alpha": true
  },
  "after": {
    "mode": "RGBA",
    "bands": ["R", "G", "B", "A"],
    "has_alpha": true
  }
}
```

`policy` 是 `ImageAlphaPolicy`。Mode、bands、alpha 的 closed mapping 是：
`L -> (["L"], false)`、`LA -> (["L", "A"], true)`、
`RGB -> (["R", "G", "B"], false)`、`RGBA -> (["R", "G", "B", "A"], true)`。
P5-A1 不存在 premultiplication/compositing fact。

### 5. `image.coordinates.exact`

Stage 固定为 `aligning`：

```json
{
  "origin": "top_left",
  "x_direction": "right",
  "y_direction": "down",
  "dimensions_policy": "exact_dimensions",
  "tile_size": 64
}
```

所有值都必须精确相等。`dimensions_policy` 是 `ImageAlignmentPolicy`，`tile_size` 固定为
`64`。该 record 不声称 resize、crop、registration 或 coordinate conversion。

### Transformation sequence

Schema-v4 completed image specimen 必须按上方顺序恰好各含一条 record，不接受其他 built-in
image transformation ID。Failed specimen 只包含 failed stage 前已经 completed 的 stage record；
因此在 `decoding` 失败的 `unsupported_image_profile` specimen 不含 image transformation record。

## 完整 schema-v4 type lattice

P5-A1 新增以下完整、closed public lattice。未列出的名称不是 v4 public contract：

```python
SCHEMA_VERSION_V4: Literal[4] = 4


@dataclass(frozen=True, slots=True)
class BackendComponentVersion:
    component_id: str
    component_version: str


@dataclass(frozen=True, slots=True)
class CapabilityAttemptV4(CapabilityAttemptV2):
    backend_components: tuple[BackendComponentVersion, ...] = ()


@dataclass(frozen=True, slots=True)
class ExecutionRecordV4(ExecutionRecordV2):
    attempts: tuple[CapabilityAttemptV4, ...] = ()


@dataclass(frozen=True, slots=True)
class ComparisonProvenanceV4(ComparisonProvenanceV2):
    pass


CompareSpecV4 = CompareSpecV3 | ImageCompareSpec
ChangeV4 = Change | ImageChange


@dataclass(frozen=True, slots=True)
class ChangeSetV4(ChangeSet):
    items: tuple[ChangeV4, ...]


@dataclass(frozen=True, slots=True)
class DiffResultV4(DiffResult):
    changes: ChangeSetV4
    provenance: ComparisonProvenanceV4


@dataclass(frozen=True, slots=True)
class ExecutionProblemV4:
    code: str
    status_code: int
    stage: PipelineStage
    message: str
    details: JsonObject
    retryable: bool


@dataclass(frozen=True, slots=True)
class CapabilityProblemV4:
    code: str
    status_code: int
    stage: PipelineStage
    message: str
    details: JsonObject
    retryable: bool


@dataclass(frozen=True, slots=True)
class CompletedOutcomeV4:
    schema_version: Literal[4] = field(default=SCHEMA_VERSION_V4, init=False)
    kind: Literal["completed"] = field(default="completed", init=False)
    execution: ExecutionRecordV4 = field(kw_only=True)
    result: DiffResultV4 = field(kw_only=True)


@dataclass(frozen=True, slots=True)
class UnavailableOutcomeV4:
    schema_version: Literal[4] = field(default=SCHEMA_VERSION_V4, init=False)
    kind: Literal["unavailable"] = field(default="unavailable", init=False)
    execution: ExecutionRecordV4 = field(kw_only=True)
    problem: CapabilityProblemV4 = field(kw_only=True)


@dataclass(frozen=True, slots=True)
class FailedOutcomeV4:
    schema_version: Literal[4] = field(default=SCHEMA_VERSION_V4, init=False)
    kind: Literal["failed"] = field(default="failed", init=False)
    execution: ExecutionRecordV4 = field(kw_only=True)
    problem: ExecutionProblemV4 = field(kw_only=True)


CompareOutcomeV4 = CompletedOutcomeV4 | UnavailableOutcomeV4 | FailedOutcomeV4
AnyCompareOutcome = CompareOutcome | CompareOutcomeV2 | CompareOutcomeV3 | CompareOutcomeV4
```

`CapabilityAttemptV4.__post_init__()` 先调用 inherited
`CapabilityAttemptV2.__post_init__()`，再验证 v4 component field。`ExecutionRecordV4` 原样保留
`ExecutionRecordV2` 的所有 field/invariant——timestamp、duration、
contiguous stage、diagnostic、detection、last completed stage 与 `plugin_host`——但要求每条
attempt 都是 exact `CapabilityAttemptV4`。`ComparisonProvenanceV4` 原样保留
`ComparisonProvenanceV2` 的所有 field/provider invariant；它的独立 runtime type 防止把 v3
provenance object 直接放入 v4 completed outcome。`ChangeSetV4.__post_init__()` 先调用 inherited
`ChangeSet.__post_init__()`，再验证 v4 item union/order。`DiffResultV4.__post_init__()` 同样先调用
inherited result validation，再要求 exact `ChangeSetV4`/`ComparisonProvenanceV4` instance，并应用
下方 image context binding。`CompletedOutcomeV4` 要求 exact `DiffResultV4`；不能直接放入 predecessor
`DiffResult`。
启用该 subclass 前，P5-A1 把 RFC 0007 exact image metric sequence 加入 inherited normalizer 使用的
shared spec-kind metric-order table。既有 text/binary/structured entry 与 output order 不变；image
metric 不得落入 generic lexical sorting。

`ChangeSetV4` 允许 predecessor-only sequence（用于 lossless upgraded v1-v3 result）或 image-only
sequence。只要任一 item 是 exact `ImageChange`，全部 item 都必须是 exact `ImageChange`；image change
绝不与 predecessor built-in 或 `ExtensionChange` 混合。Descriptor change 唯一且按
`dimensions`、`pixel_format`、`color_description` 排序。Tile change 严格按 `(y, x)` 排序，origin
唯一、不重叠，且不与 descriptor change 混合。Empty sequence 有效，其 context 由 spec 决定。

`DiffResultV4` 提供该 context。`spec.kind="image"` 时，全部 retained item 都必须是 image change，
`artifacts=()`，provenance 使用 exact image comparator/algorithm binding，并应用 RFC 0007 与本
amendment 的 metric、evaluation、descriptor、geometry、digest-syntax、truncation、resource
invariant。Predecessor spec kind 不得出现 image change 或 `image`/`image.*` identifier，并继续应用
全部 predecessor schema-v3 result invariant。Plain `DiffResult` 中的 image spec、plain `ChangeSet`
中的 image change、`CompletedOutcomeV4` 中直接放入的 predecessor result，或 v1-v3 outcome 中直接
放入的 v4 result 均无效。

Private serializer boundary 显式接收 version，绝不从 item 推断 schema：

```python
def _attempt_to_data(
    attempt: CapabilityAttempt | CapabilityAttemptV2 | CapabilityAttemptV4,
    *,
    schema_version: Literal[1, 2, 3, 4],
) -> JsonObject: ...

@overload
def _attempt_from_data(
    value: JsonValue, *, schema_version: Literal[1]
) -> CapabilityAttempt: ...

@overload
def _attempt_from_data(
    value: JsonValue, *, schema_version: Literal[2, 3]
) -> CapabilityAttemptV2: ...

@overload
def _attempt_from_data(
    value: JsonValue, *, schema_version: Literal[4]
) -> CapabilityAttemptV4: ...

def _execution_to_data(
    record: ExecutionRecord | ExecutionRecordV2 | ExecutionRecordV4,
    *,
    schema_version: Literal[1, 2, 3, 4],
) -> JsonObject: ...

@overload
def _execution_from_data(
    value: JsonValue, *, schema_version: Literal[1]
) -> ExecutionRecord: ...

@overload
def _execution_from_data(
    value: JsonValue, *, schema_version: Literal[2, 3]
) -> ExecutionRecordV2: ...

@overload
def _execution_from_data(
    value: JsonValue, *, schema_version: Literal[4]
) -> ExecutionRecordV4: ...

def _change_to_data(
    change: ChangeV4, *, schema_version: Literal[1, 2, 3, 4]
) -> JsonObject: ...

@overload
def _change_from_data(
    value: JsonValue, *, schema_version: Literal[1, 2, 3]
) -> Change: ...

@overload
def _change_from_data(
    value: JsonValue, *, schema_version: Literal[4]
) -> ChangeV4: ...

def _result_to_data(
    result: DiffResult | DiffResultV4,
    *,
    schema_version: Literal[1, 2, 3, 4],
) -> JsonObject: ...

@overload
def _result_from_data(
    value: JsonValue, *, schema_version: Literal[1, 2, 3]
) -> DiffResult: ...

@overload
def _result_from_data(
    value: JsonValue, *, schema_version: Literal[4]
) -> DiffResultV4: ...

def serialized_change_size(
    change: ChangeV4, *, schema_version: Literal[1, 2, 3, 4]
) -> int: ...
```

Outer outcome encoder/decoder 始终把 envelope version 显式传给 execution、attempt、result 与
change serializer。Schema v1 要求 exact `ExecutionRecord`/`CapabilityAttempt`；schema v2/v3
要求 exact `ExecutionRecordV2`/`CapabilityAttemptV2`；schema v4 要求 exact
`ExecutionRecordV4`/`CapabilityAttemptV4`。因此既有
`isinstance(attempt, CapabilityAttemptV2)` writer branch 不是有效 v4 dispatch，必须换成
上方 versioned helper。V4 reader 要求每条 attempt 都存在 `backend_components`，先构造
component object 再构造 attempt；即使读取 legacy-only upgraded payload，也构造 v4
execution/set/result type。V1-v3 reader 拒绝额外 attempt member 与 `image_change`；v1-v3 encoder
在 serialization 前拒绝 v4 execution/attempt/set/result instance 与 image spec。V4
set/result/execution class 不增加 JSON key——既有 execution/result object shape 保持 closed——
`backend_components` 是唯一新增 attempt member。

Attempt reader 按 envelope 选择 exact key set：schema v1 的四个 field，schema v2/v3 的七个
field，或这七个 field 加 schema v4 required `backend_components`。Execution reader 应用 inherited
conditional `detection` key 与 schema-v2+ `plugin_host` key rule，再对每个 item 调用
`_attempt_from_data(..., schema_version=envelope_version)`。V4 缺少 `backend_components`、v1-v3
出现该 key、unknown member 或 cross-version runtime instance 都必须失败，不得隐式 upgrade/downgrade。

`serialized_change_size` 是 internal 且 version-required 的 helper，先使用同一显式 version
调用 `_change_to_data`，再使用 canonical compact JSON encoding；不提供 default schema。每个
payload-budget producer/validator 都传入 enclosing outcome version。V4 result（包括 predecessor
upgrade 而来的 result）的 `image.changes.payload_bytes.used` 等于 retained item 的
`serialized_change_size(item, schema_version=4)` 之和。V4 对 predecessor change 的 encoding 与
predecessor object encoding byte-identical；image change 对 version 1–3 被拒绝。因此 truncation
selection、recorded resource usage、detached validation 与 canonical fixture byte 测量同一 payload。

Subclassing 不削弱 version gate。Direct construction/encoding 使用 exact-type rule：exact
`ExecutionRecordV2` 只包含 exact `CapabilityAttemptV2` item；`ExecutionRecordV4` 先执行全部
inherited record check，再要求 exact `CapabilityAttemptV4` item。Exact plain `ChangeSet` 只包含
predecessor `Change` variant；`ChangeSetV4` 先执行 inherited completeness/count/limit check，再执行
v4 union check。V1-v3 completed outcome 要求 exact predecessor `DiffResult`/provenance combination；
v4 要求 exact `DiffResultV4`/`ComparisonProvenanceV4`。V4 reader 要求
`backend_components` member，先构造 `BackendComponentVersion` 再构造 attempt，并拒绝 unknown
component key、duplicate ID 或 unsorted input。V3-to-v4 upgrader 使用全部 inherited value 与
`backend_components=()` 调用 public `CapabilityAttemptV4` constructor；不 mutate 既有 v2 attempt，
也不绕过其 validation。

`BackendComponentVersion.component_id` 是稳定小写 identifier，`component_version` 是 bounded
identity text。Component 按 `component_id` 唯一并排序。七个 inherited attempt field 保留全部
P4-C1 value、provider、selected-capability、version 与 `plugin_host` binding。`backend_id=null`
的 v4 attempt 要求
`backend_version=null` 且 `backend_components=[]`。非 null backend 要求非 null backend version；
backend 暴露的 separately versioned linked component 记录在这里，而不是 transformation 或
free-form diagnostic。后续 runtime 例如可标识 `libpng`/`zlib`，但 P5-A1 不声称安装了任何
component，fixture 使用空 tuple。该 carrier 在不声称 backend 已存在的前提下闭合 RFC 0007 的
linked-library evidence 要求。

Curated top-level `platydiff` export 新增 `CompareSpecV4`、`DiffResultV4`、`CompareOutcomeV4`、三个 v4 outcome
class、本 RFC 全部 image spec/change class/named enum，以及下方四个 migration helper。
Foundational `SCHEMA_VERSION_V4`、`ChangeV4`、`ChangeSetV4`、`BackendComponentVersion`、v4 attempt/execution/
provenance/problem class 从 `platydiff.core.models` 公开，遵循 predecessor 对 curated/foundational
contract 的区分，不在 top-level 重复 export。两个 surface 都不 export private decoder/backend
implementation。Serialization export 新增 `upgrade_outcome_v1_to_v4`、`upgrade_outcome_v2_to_v4`、
`upgrade_outcome_v3_to_v4` 与 `downgrade_outcome_v4_to_v3`；`platydiff.core` 与既有
serialization entry point 一并 re-export 这四个 helper。

## Contract-only canonical fixtures

### Canonical writer 与 reader semantics

Canonical schema-v4 writer 使用 UTF-8 JSON，`ensure_ascii=false`、`allow_nan=false`、object key
递归按字典序排列、compact separator `,`/`:` 且无 trailing newline。该 writer order 只属于
byte-stability rule。Reader 接受任意 object member order，拒绝 duplicate/missing/unknown member，
并保留 normative array order。仅改变 object member order 不得改变语义；stage、attempt、input、
transformation、resource、change、metric 或 evaluation 的 array order 由其既有或图片专属规则验证。

P5-A1 恰好新增两个 byte-stable JSON fixture：

```text
tests/fixtures/schema_v4/image_completed.json
tests/fixtures/schema_v4/image_unsupported_profile_failed.json
```

测试从 public model 直接构造两种 outcome 并 serialize；不得调用 `compare()`、打开图片、import
Pillow、注册 image capability 或声称 source hash 对应已 decode 的 PNG。测试和 fixture inventory
必须把它们标记为 `contract-only schema specimens`。

Completed specimen 使用 RFC 0007 已接受的 1x1 RGBA vector 及上方五个精确 transformation
object，identity field 为：

```json
{
  "execution": {
    "plugin_host": null,
    "attempts": [
      {
        "capability_id": "image",
        "backend_id": null,
        "backend_components": [],
        "disposition": "selected",
        "reason_code": null,
        "capability_version": "1",
        "backend_version": null,
        "provider": null
      }
    ]
  },
  "result": {
    "provenance": {
      "comparator_id": "image",
      "comparator_version": "1",
      "algorithm_id": "image.decoded_samples.tiles.v1",
      "implementation_version": "contract-only",
      "provider": null,
      "detector_provider": null
    }
  },
  "schema_version": 4
}
```

上方为避免重复 inherited stage/result/metric/source provenance field 而只展示部分 object；实际
fixture 必须是完整 outcome，并使用与其他 fixture 相同的 reject-unknown-key rule decode。
`plugin_host`、两个 provider、`backend_id` 与 `backend_version` 必须为 JSON null，
`backend_components` 必须为空；两种 fixture 任何位置都不得出现 `pillow`、`PIL`、Pillow
version、distribution name、module path 或 local path。

Completed specimen 不含 detection record，且恰好有一条 attempt，其 disposition 为 `selected`。
Attempt 与 comparison provenance 必须满足机械绑定：

```text
attempt.capability_id == provenance.comparator_id == "image"
attempt.capability_version == provenance.comparator_version == "1"
attempt.provider == provenance.provider == null
attempt.backend_id == attempt.backend_version == null
attempt.backend_components == []
provenance.detector_provider == null
execution.plugin_host == null
```

`image` 是 schema contract 与所有未来 runtime implementation 唯一的 built-in
comparator/capability identifier。本 amendment 全局 supersede RFC 0007 较早的
`image.decoded_samples` comparator 名称；该 dotted value 在 P5-A1、P5-A2、P5-A3 或任何
migration 中都不是第二个合法 comparator/capability ID。Dotted string
`image.decoded_samples.tiles.v1` 仍只是 algorithm identifier。根据 inherited P4-C1 provider
invariant，provider 为 null 的 dotted comparator identifier（包括 `image.decoded_samples`）无效，
必须拒绝。

Completed specimen 必须 `artifacts=[]`、full fidelity、complete `ChangeSet` 且无 diagnostic；只使用
RFC 0007 已接受的 image metric/evaluation/change/summary/resource/digest invariant。所有
configured/used resource 使用 RFC 0007 精确名称并按字典序排列，五条 transformation 按 normative
order 出现。Failed specimen 不含 `DiffResult`、artifact、metric、change、comparison provenance 或
transformation；execution 终止于 failed `decoding` stage，并携带下述精确 problem。

P5-A1 只可在 schema validation 中 reserve `image` 与 `image.decoded_samples.tiles.v1`；
runtime registry 继续拒绝它们。P5-A2 可在 decoder contract evidence 中使用 `image`，
但不得注册 executable public comparison route；P5-A3 是首个可注册 built-in `image`
comparator/capability 的 gate。后续 runtime 必须记录实际 selected backend 与 Platydiff
implementation version，不得把 `implementation_version="contract-only"` 复制到 runtime outcome，
也不得 emit 已 superseded 的 `image.decoded_samples` comparator value。

### Cross-object bindings

Canonical completed specimen 是 equal 1x1 RGBA specimen：两个 role 都使用 RFC 0007 sample
vector `00 7f ff 80`，三种 descriptor digest 均相等，不含 change item，
relation/verdict/fidelity 为 `equal`/`pass`/`full`，且 `artifacts=[]`。下列 binding 是不依赖
object member order 的 semantic reader invariant：

| Fact | 必须满足的 binding |
| --- | --- |
| Inputs | `provenance.inputs` 恰好先 `before` 后 `after`；每个 decode role 的 `input_bytes` 等于对应 input `size_bytes`，input digest 是有效 SHA-256 evidence。Specimen 不声称这些 bytes 是可运行 PNG fixture。 |
| Spec/profile | `spec.kind=image`；每条 transformation 的 policy/profile/tile value 等于 normalized spec 对应值。 |
| Decode/resources | 每个 role 的 decode `input_bytes`、metadata counter、`pixels`、`decoded_bytes` 等于同名 `ResourceUsage.used`；resource `limit` 等于 normalized spec limit。 |
| Mode/alpha | 每个 role 的 decode `mode` 等于 alpha `mode`；bands/`has_alpha` 匹配 mode；IHDR color type 与 decoded-byte arithmetic 也匹配。 |
| Dimensions/alignment | Decode dimensions 建立 coordinate bound；coordinate policy/tile size 等于 normalized spec。Descriptor 相等要求 role dimensions、mode/bands/alpha 与 color-description digest 相等。 |
| Comparison work | `image.compare.sample_pairs.used == image.compared_samples`；limit 等于 `max_compare_work`。 |
| Changes/resources | `image.changes.items.used == changes.returned_count`；`image.changes.payload_bytes.used` 等于 `sum(serialized_change_size(item, schema_version=4) for item in changes.items)`；limit 等于两个 spec change limit。 |
| Summary/changes | `summary.change_count == changes.total_count == image.changed_items`；summary `changed_tiles` 等于 full tile-change count，`descriptor_changes` 等于 full descriptor-change count。 |
| Metrics | Equal specimen 的 compared/equal/changed pixels 为 `1/1/0`，compared samples `4`，changed items `0`，MAE/RMSE `0.0`，PSNR 是 tagged positive infinity，并遵守 RFC 0007 metric order。 |
| Evaluation | 唯一的 `image.decoded_sample_equality` evaluation observe `image.changed_items`，使用 `eq 0`，verdict 等于 result verdict；changed items 为零当且仅当 relation 为 equal。 |

### Digest verification boundary

Detached reader 只能验证 outcome 携带的事实。它验证 64 位小写十六进制 syntax，把
operation/component 映射到 RFC 0007 声明的 digest domain，并把两个
digest field 映射到 `before`/`after` role。它从 public decode/alpha fact 独立重算 dimensions 与
pixel-format descriptor digest。Color-description change 要求每个 change digest 等于相应 role 的
`image.color.native_exact.description_digest`。Tile change 可以验证 domain selection、role placement、
geometry 与 digest syntax，但 sample 被有意省略，因而不能重算 sample digest。

Content correctness 是 producer-only obligation。Producer 对实际 owned input bytes 计算
`InputProvenance` hash，从 validated stream 推导 decode fact，对完整 canonical color-description
payload 计算 hash，并对每个 role 的实际 canonical tile sample 计算 hash；changed pixels 与 maximum
error 也从这些 sample 计算。Detached reader 不得仅因 wire object 内部一致就声称独立验证了这些
producer-only fact。

Compatibility test 使用 Python standard-library SHA-256，从 literal ASCII domain string 与 literal
payload hex 独立重算 RFC 0007 的四个 digest vector。该 oracle 不得调用 Platydiff serializer、image
comparator、decoder、Pillow 或 production digest helper。测试逐 byte 对比重算 digest 与 published
constant，并单独测试 detached-reader check。Canonical equal specimen 不含 `ImageChange`，因此这些
vector test 与其 byte-stable fixture round trip 彼此独立。

这些 obligation 归属于首次拥有相应 runtime data 的 gate。P5-A1 只测试 detached
validation 与四个独立 literal domain/payload digest oracle；不使用 image source、decoder 或
comparator。P5-A2 负责 owned input byte、scanner/decode fact 与 canonical color-description byte
的 producer test。P5-A3 负责 actual tile sample、tile digest、changed-pixel/error calculation 与
comparison resource accounting 的 producer test。两组后续 test 都不是 P5-A1 merge gate。

对所有 schema-v4 image outcome（不只 canonical specimen），descriptor change 禁止 tile change，
并把 compared/equal/changed pixel 与 compared-sample metric 全部置零。Descriptor 相同时，每个 tile
都位于两个 role dimension 内，满足 `1 <= width,height <= 64`，edge geometry 遵循 fixed grid。
Tile change 满足 `1 <= changed_pixels <= width * height`，且 `maximum_absolute_error` 必须是
inclusive `1.0..255.0` 的 finite value；NaN、正负 infinity、zero 与 negative error 均无效。
Complete change set 的 tile `changed_pixels` 之和等于完整 `image.changed_pixels` metric；truncated set
的 retained sum 不得超过该 metric，producer 在 truncation 前计算完整 metric，reader 不虚构 omitted
tile fact。Digest claim 遵守上方 detached-reader/producer-only boundary。

Canonical failed specimen 不含 detection record，且恰好有一条 disposition 为 `selected` 的 attempt：
capability/version 为 `image`/`1`，provider/backend identity 为 null，`backend_components` 为空，
`plugin_host` 为 null。Failed outcome 没有 `DiffResult`，因此没有 comparison provenance；该
attempt 仍是解释 execution 为何到达 `decoding` 的必要证据。

## Schema-v4 problem model

Schema v4 沿用 P4-C1 schema-v3 execution/capability problem shape，并在
`ExecutionProblemV4` 中增加一个 failed code：

```python
class ExecutionProblemV4:
    code: str
    status_code: int
    stage: PipelineStage
    message: str
    details: JsonObject
    retryable: bool
```

现有 schema-v2/v3 failed mapping 不变。新 mapping 仅接受以下精确 tuple：

```text
code = unsupported_image_profile
status_code = 415
stage = decoding
retryable = false
```

`details` 恰好包含两个 key：

```json
{
  "profile": "static_png_8bit_v1",
  "reason": "unsupported_color_type"
}
```

`profile` 是 `ImageDecodeProfile.STATIC_PNG_8BIT_V1`，`reason` 是一个
`UnsupportedImageProfileReason`。Message 是遵守 inherited validity/terminal-escaping rule 的
Unicode-scalar text。由于 predecessor 不存在 message bound，schema v4 不新增 problem-message
wire-length bound；下方独立 terminal projection limit 约束 rendering。Message 不得含 source byte、
metadata、ICC/EXIF value、absolute/module path 或 backend exception text。Canonical fixture message 固定为
`input is outside the static PNG 8-bit profile`。

`CapabilityProblemV4` 不新增 code，其 mapping/resolving-stage rule 与 P4-C1 schema-v3 capability
problem 相同。`unsupported_image_profile` 绝不是 unavailable，也不出现在 detecting/resolving。

Allowlist 必须先按 outer envelope version gate 再 decode problem：schema v1、v2、v3 分别将该 code
作为各自 invalid failed code 拒绝；只有 schema v4 可在满足全部 tuple/detail invariant 时接受。
仅把 v4 fixture 的 outer `schema_version` 改为 `1`、`2` 或 `3` 必须 decode 失败；reader 不得静默
reinterpret、drop 或 rename 该 code。

### 完整 scenario classification

Classification 依据显式 PNG profile，而非 filename/MIME label。对于 8-byte PNG signature，若短输入
是其 exact proper prefix，则是 truncated/malformed，返回 `decode_error`；若短或完整 prefix 已经在
现有位置偏离 PNG signature，则是 wrong codec，返回
`unsupported_image_profile/wrong_codec`。该规则消除 unsupported codec 与 damaged PNG 的歧义。

| Input/execution scenario | Outcome/code | Stage | 适用时的 `reason` |
| --- | --- | --- | --- |
| Backend 缺失或不在 accepted version range | unavailable / `backend_unavailable` (503) | resolving | — |
| 未注册 built-in image capability，包括 P5-A1 的全部 runtime call | unavailable / `capability_unavailable` (501) | resolving | — |
| Invalid `ImageCompareSpec` field/type/limit | failed / `invalid_spec` (400) | validating | — |
| Path source 缺失 | failed / `source_not_found` (404) | sourcing | — |
| Source read 被拒绝 | failed / `permission_denied` (403) | sourcing | — |
| Owned snapshot 期间 source mutation | failed / `source_changed` (409) | sourcing | — |
| Directory、special file、`TextSource` 或其他 unsupported source kind | failed / `source_type_unsupported` (415) | sourcing | — |
| 其他 source read failure | failed / `io_error` (500) | sourcing | — |
| Available prefix 结束前 bytes 已偏离 PNG signature | failed / `unsupported_image_profile` (415) | decoding | `wrong_codec` |
| PNG signature 的 exact proper prefix 提前结束 | failed / `decode_error` (422) | decoding | — |
| Valid PNG 使用 1/2/4-bit greyscale 或任意 16-bit sample pair | failed / `unsupported_image_profile` (415) | decoding | `unsupported_bit_depth` |
| Valid PNG 使用 indexed color 或其他 legal unsupported color type | failed / `unsupported_image_profile` (415) | decoding | `unsupported_color_type` |
| Valid PNG 含 `tRNS` 且需要隐式 transparency expansion | failed / `unsupported_image_profile` (415) | decoding | `transparency_expansion_required` |
| Valid PNG 含 `acTL`、`fcTL`、`fdAT` 或以其他方式证明 multiple frames | failed / `unsupported_image_profile` (415) | decoding | `multiple_frames` |
| Structurally valid PNG 含 unknown critical chunk | failed / `unsupported_image_profile` (415) | decoding | `unknown_critical_chunk` |
| Signature 是 PNG，但 framing、CRC、ordering、multiplicity、chunk value、compressed metadata、`IEND` 或 stream termination malformed | failed / `decode_error` (422) | decoding | — |
| Scanner 接受 profile，但后续 backend 报告其他 codec/mode/dimensions/frame state 或 malformed decode | failed / `decode_error` (422) | decoding | — |
| Input snapshot 跨越 `max_input_bytes` | failed / `resource_limit_exceeded` (413) | sourcing | — |
| 跨越 metadata、ICC、dimension、pixel、decoded-byte 或 decompression-bomb limit | failed / `resource_limit_exceeded` (413) | decoding | — |
| 完整 sample comparison 将跨越 work budget | failed / `compare_resource_limit` (413) | comparing | — |
| Selected built-in comparator 在已分类 decode/resource condition 外失败 | failed / `comparator_failure` (502) | comparing | — |
| 由 outer CLI handler 捕获的 unexpected exception | failed / `internal_error` (500) | `validating` | — |
| 成功 decode 后 dimensions、pixel format 或 color description 不同 | completed / different / fail | aggregating | — |
| Supported descriptor 与全部 sample 相同/不同 | completed / equal/pass 或 different/fail | aggregating | — |

`unsupported_image_profile` object 必须使用匹配行的 reason；六种 reason 是 schema v4 exhaustive set。
`decode_error` 与其他 inherited problem 保留其 inherited details policy，不得获得 profile `reason`。
同时 malformed 且超出 supported profile 的条件归为 `decode_error`：必须先建立 structural validity 再做
support-profile classification，只有上方显式 signature-prefix rule 例外。

完成 source/resource enforcement 后，scanner 在选择 unsupported-profile reason 前完成 bounded
structural validation。即使已观察到 unsupported feature，任何 malformed fact 都产生 `decode_error`。
若结构有效且同时存在多个 unsupported feature，producer 按以下 total priority 选择第一个 reason，
不受 chunk discovery order 影响：

```text
1. wrong_codec
2. multiple_frames
3. unknown_critical_chunk
4. unsupported_color_type
5. unsupported_bit_depth
6. transparency_expansion_required
```

`wrong_codec` 不会与 valid PNG signature 后才解析的 feature 共存，但仍占 rank 1，使 classification
function 对所有 input 都为 total。若 resource breach 阻止完成 bounded scan，则保持
`resource_limit_exceeded`，不选择 partial reason。以下 classification case 是 normative gate
vector：

| Vector | Supported/unsupported facts | Expected classification |
| --- | --- | --- |
| `signature_jpeg` | JPEG signature；无 PNG structure | `unsupported_image_profile/wrong_codec` |
| `apng_unknown_indexed_trns` | APNG control、unknown critical chunk、indexed 4-bit color 与 `tRNS` | `unsupported_image_profile/multiple_frames` |
| `unknown_indexed_trns` | Unknown critical chunk、indexed 4-bit color 与 `tRNS` | `unsupported_image_profile/unknown_critical_chunk` |
| `indexed_4bit_trns` | Indexed 4-bit color 与 `tRNS` | `unsupported_image_profile/unsupported_color_type` |
| `grey_16bit_trns` | Greyscale 16-bit sample 与 `tRNS` | `unsupported_image_profile/unsupported_bit_depth` |
| `rgb_8bit_trns` | 其他方面 supported 的 RGB 8-bit PNG，且含 `tRNS` | `unsupported_image_profile/transparency_expansion_required` |

P5-A1 把这些 row 冻结为 contract metadata，并为每个 reason 直接构造一个 schema-v4
failed-problem specimen。其 test 只证明 enum、problem tuple、stage、detail、reader/writer 与
v1-v3 rejection behavior；vector 名称不代表 P5-A1 image file，P5-A1 不创建 PNG byte、
scanner、decoder、corpus 或 reason-selection implementation。P5-A2 负责 generated CRC/order-valid
PNG input、total-priority scanner test、discovery-order permutation 与每个 malformed bad-CRC twin。
所有 P5-A2 twin 都必须产生 `decode_error`；保持 PNG validity 的 permutation 不得改变
selected reason。P5-A3 复用 P5-A2 classification suite，但不在 comparator 内重新分类 decode failure。

`internal_error` 记录 `stage="validating"`，这是 synthetic CLI failure 使用的既有真实
`PipelineStage`。“Outer CLI handler”只描述 exception 捕获位置，不是 serialized stage value。

## 最小安全 terminal projection

P5-A1 只可扩展 terminal renderer 以消费已验证 v4 outcome。它不获得 source service/artifact root，
不计算 metric、digest、image 或 verdict。Inherited header、fidelity、summary count 与 diagnostic
保持原语义，但整个 schema-v4 projection 必须遵守以下精确上限：

```text
TERMINAL_V4_MAX_LINES = 512
TERMINAL_V4_MAX_UNICODE_SCALARS = 65_536
TERMINAL_V4_MAX_UTF8_BYTES = 65_536
TERMINAL_V4_OVERFLOW_LINE = ... terminal output truncated by schema-v4 limits
```

Renderer 按既有顺序生成完整 logical line stream，先 escape untrusted text，再用一个 ASCII LF join，
且不添加 trailing LF。Line count 包含 overflow line；scalar/byte count 包含 separator。当仍有 logical
line 时，renderer 保留能同时容纳 exact overflow line 及其 separator、并满足三个 limit 的最长 prefix。
只要有内容 omitted，就恰好 emit 一次 overflow line 后停止，绝不 emit partial logical line。若第一个
logical line 加 overflow line 都无法容纳，则 output 只包含 overflow line。算法不依赖 terminal width、
locale、color 或 environment。

对每个 retained `ImageChange` 恰好附加一行：

```text
descriptor <component> changed
tile x=<x> y=<y> width=<width> height=<height> changed_pixels=<count> maximum_absolute_error=<decimal>
```

Descriptor form 只使用已验证 component wire value。Tile form 只使用已验证 integer 与 finite error。
Coordinate 使用 grammar `0|[1-9][0-9]{0,15}` 并满足既有 exact-integer bound；width、height、changed
pixels 使用 `[1-9][0-9]{0,15}` 并满足各自 model bound。`maximum_absolute_error` 还必须在数学上
为整数，并使用 Python locale-independent `repr(float(value))`；经过 required `1.0..255.0`
validation 后，其 grammar 为
`(?:[1-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.0`。Image tile
绝不 render tagged NaN/infinity。除一般 image invariant 外，任何 line 产生前 terminal input validation
还必须验证 `changed_pixels <= width * height`。不得打印 digest、pixel、path、label、metadata、profile
或 source excerpt。Truncated result 只 render retained item 与 inherited complete total，不得暗示 omitted
tile 不存在。

Canonical failed fixture 的 inherited problem projection 精确为：

```text
failed [unsupported_image_profile/415] at decoding: input is outside the static PNG 8-bit profile
```

Unknown schema-v4 built-in change/transformation/enum/problem code 必须在 rendering 前由 reader 拒绝；
renderer 不猜测 generic image meaning。Namespaced `ExtensionChange` 保持现有显式 generic presentation。

Golden test 覆盖恰好 512 lines、65,536 scalars、65,536 UTF-8 bytes；逐一多一 line/scalar/byte；
multibyte diagnostic；单条 overbound line；以及 deterministic repetition。测试还拒绝 tile error `0`、
`NaN`、正负 infinity、超过 `255`，并拒绝 zero/over-64 dimension、zero changed pixels 与超过 tile area
的 changed pixels。

## Upgrade、downgrade 与 reader 边界

V4 reader 接受并保留有效 v1/v2/v3/v4 envelope。三个显式 upgrade helper 是精确 composition：

```text
upgrade_outcome_v3_to_v4(v3) -> v4
upgrade_outcome_v2_to_v4(v2) = upgrade_outcome_v3_to_v4(upgrade_outcome_v2_to_v3(v2))
upgrade_outcome_v1_to_v4(v1) = upgrade_outcome_v2_to_v4(upgrade_outcome_v1_to_v2(v1))
```

V3-to-v4 step 把每条 attempt 替换为保留七个 inherited field 并新增 `backend_components=[]` 的
`CapabilityAttemptV4`，把 execution/provenance/problem wrapper 替换为 exact v4 type，并把 completed
result 重构为 `ChangeSetV4`/`DiffResultV4`，保留全部 wire fact；不会把 predecessor outcome relabel
为 image。

Predecessor schema 不含 image comparator，因此 upgrade helper 不 rename comparator；也不存在已接受
的更早 schema-v4 writer 需要 migration。使用 RFC 0007 已 superseded
`comparator_id="image.decoded_samples"` 或同名 capability-attempt ID 的 v4 payload 必须拒绝，
不得 migration；有效 image fixture 与未来 runtime outcome 在两处都使用 `image`，并保留
`algorithm_id="image.decoded_samples.tiles.v1"`。

Renderer、CLI、JSON writer 或 reader 均不得自动 downgrade。P5-A1 只定义一个新 downgrade helper：

```python
def downgrade_outcome_v4_to_v3(outcome: CompareOutcomeV4) -> CompareOutcomeV3: ...
```

只有 validation 证明每个 field 都可由 schema v3 表达且所有 attempt 的
`backend_components=[]` 时才成功。包含以下任意内容即拒绝：

- image spec kind 或 image change；
- `image` 或 `image.*` built-in transformation/comparator/algorithm/metric/evaluation/resource/capability-attempt ID；
- `unsupported_image_profile`；
- 非空 `backend_components` tuple；
- 任意其他 schema-v4-only fact、enum value 或 problem shape。

成功时，把 exact v4 wrapper、attempt、change set 与 result 转回 v3 type，不改变任何剩余 value。
Caller 随后可以显式使用
已实现的 `downgrade_outcome_v3_to_v2`；P5-A1 不修改或绕过该 gate。Reviewed predecessor 不存在
v2-to-v1 downgrade helper，因此 P5-A1 不承诺或新增它；若出现用例，留待独立 contract。
所有 `ImageCompareSpec` outcome 和两个 P5-A1 canonical fixture 都不能 downgrade 到 v3 或更低。
不识别 v4 的旧 reader 必须返回现有 unknown-schema error，无需产生 lossy approximation。

## 机械验收条件

接受本 RFC 不授权代码。以后派发 P5-A1 时，merge 前必须满足：

1. 实际 merged P4-C1 commit 是 implementation branch 的祖先，完整 predecessor suite 原样通过，
   且 public v3 type 与本 amendment 一致；否则停止并回调 RFC。
2. `SCHEMA_VERSION_V4`、`BackendComponentVersion`、`CapabilityAttemptV4`、`ExecutionRecordV4`、
   `ComparisonProvenanceV4`、两个 v4 problem class、三个 v4 outcome class、`CompareSpecV4`、
   `ChangeV4`、`ChangeSetV4`、`DiffResultV4`、`CompareOutcomeV4`、扩展后的 `AnyCompareOutcome`、所有 documented image
   spec/change/enum 与恰好四个 v4 migration helper 位于上方 documented top-level/foundational
   export set；不 export decoder/backend implementation。
3. Exact predecessor/v4 constructor、reader、encoder 拒绝跨版本 attempt、change-set、result、
   provenance、problem 与 outcome mixing，且 v4 subclass 可证明先运行全部 inherited validation。
   Outer envelope version 显式传入 execution、attempt、result 与 change serializer；v4 attempt
   要求 `backend_components`，v1-v3 拒绝它；`serialized_change_size` 要求 enclosing
   version，且测量 payload truncation/validation 使用的同一 canonical change byte。所有新
   object 拒绝 missing/extra key、boolean-as-integer、invalid enum、invalid mode/IHDR/band
   combination、invalid role order/digest 与 cross-field invariant violation。
4. 五条 transformation record 各自接受 canonical payload，并拒绝错误 stage、ID、key、type、
   nesting、value 或 sequence position。
5. v1/v2/v3 canonical file 保持 byte-identical；全部 predecessor round trip、migration、plugin receipt、
   CLI output 与 public export 保持有效。
6. 两个 v4 fixture 在 canonical writer 下 byte-identical round-trip，permuted object member 以同一语义
   读取；测试证明 direct construction、精确 `image` attempt/comparator/version/provider binding、null
   backend identity、空 component、无 Pillow string、无 image runtime registration/CLI route/dependency，
   以及适用的 v1-v3 code gate rejection。
7. V4 reader 在 terminal rendering 前拒绝 duplicate key、unknown schema、unknown built-in
   kind/transformation/problem，以及 invalid image change combination、mixing、order、geometry、
   context 与 serializer-version signature。
8. Terminal golden test 覆盖 descriptor、tile、truncated、failed、unsafe message、unknown-kind、精确
   line/scalar/UTF-8 boundary、deterministic overflow、numeric grammar 与 tile value/area rejection，且不授予
   source/artifact authority。
9. Migration test 证明三个 lossless predecessor-to-v4 upgrade、精确 representable v4-to-v3 downgrade、
   后续使用既有 v3-to-v2 helper，以及所有 image-bearing、component-bearing 或
   `unsupported_image_profile` downgrade 的 hard rejection；不新增 v2-to-v1 helper。
10. P5-A1 直接构造并 round-trip 六个 schema problem reason，验证 exact tuple/detail/stage
    gate，包括位于 `validating` 的 `internal_error`，但不包含 PNG 或 scanner test。P5-A2
    而非 P5-A1 负责 generated classification vector、malformed twin、total-priority selection 与
    discovery-order permutation。
11. P5-A1 detached-reader test 只覆盖 wire-verifiable digest syntax/domain/role binding；独立
    standard-library oracle 不使用 production helper 重算 RFC 0007 四个 vector。P5-A2 负责
    input/decode/color-description producer correctness；P5-A3 负责 tile-sample、change-metric 与
    comparison-resource producer correctness。这些 runtime producer test 不是 P5-A1 acceptance criteria。
12. Problem message 保持 predecessor wire behavior，不声称 length bound；terminal test 独立证明 v4
    rendering bound。
13. Ruff format/check、strict mypy、完整 pytest、build/wheel/sdist inspection、`git diff --check` 与
    relative-link check 全通过；只能报告实际运行的命令。

Implementation diff 不得包含说明性 test/doc 之外的 Pillow reference、dependency metadata、image
decoder/scanner/comparator、capability registration、CLI image route、auto/SDK expansion、artifact、
corpus image 或 UI code。

P5-A1 commit boundary 为：

1. `feat(core): add schema-v4 image comparison contracts`
2. `feat(renderers): add bounded schema-v4 image projection`
3. `test(core): add schema-v4 compatibility and migration fixtures`

每个 commit 都必须通过相关 predecessor test；第三个是 gate commit，必须证明上方完整机械验收条件。

## 与后续门禁的关系

P5-A2 仍是首个 optional-backend/decode gate；它负责 actual source snapshot、generated scanner
vector/malformed twin、support-profile priority selection、decoded fact 与对应 producer evidence。P5-A3
仍是首个 comparator、capability-registration、terminal command 与 executable image-result gate；它负责
actual sample/tile comparison、change/metric/resource producer evidence，并注册唯一 built-in
comparator/capability ID `image`。二者独立派发，都不是隐藏的 P5-A1 acceptance gate。本
amendment 不改变或授权 P5-C/P5-P/P5-F/P5-M/P5-H/P5-S callback。

本 RFC 全局 supersede RFC 0007 的 built-in comparator identity：`image` 在 schema
fixture、attempt、provenance、migration 与所有未来 runtime gate 中取代
`image.decoded_samples`，`image.decoded_samples.tiles.v1` 仍是 algorithm ID。本 RFC 也
supersede RFC 0007 中仍开放的 P5-A1 enum representation、transformation JSON shape、schema-only
fixture identity、schema-v4 problem gate/signature classification、terminal projection 与 downgrade mechanics；
其余 I1-I16 decision 和 RFC 0007 语义继续有效。

## 参考

- [RFC 0001：Comparison outcome 与 DiffResult](0001-comparison-outcome-and-diff-result_zh.md)
- [RFC 0004：Human review UI 与 renderer boundary](0004-human-review-ui-and-renderer-boundary_zh.md)
- [RFC 0007：图片比较](0007-image-comparison_zh.md)
- [RFC 0010：Schema predecessor 与 Phase 6 amendment](0010-schema-predecessor-and-phase6-contract-amendment_zh.md)
