# RFC 0011：P5-A1 图片 Wire Contract 修订

[English documentation](0011-p5a1-image-wire-contract-amendment.md)

- 状态：Proposed
- 日期：2026-09-10
- 负责人：Platydiff maintainers
- 若获接受则修订：[RFC 0007](0007-image-comparison_zh.md)
- 前驱：[RFC 0010](0010-schema-predecessor-and-phase6-contract-amendment_zh.md)
- 实现授权：无

## 摘要

本 Proposed amendment 闭合 P5-A1 派发前必须决定的 wire-level contract，且不改变
RFC 0007 已接受的 I1-I16 图片语义。它冻结 P5-A1 边界、public enum type、五种图片
transformation payload、仅用于 schema 的 provenance specimen、
`unsupported_image_profile` problem、terminal presentation、downgrade rule 与
compatibility acceptance criteria。

证据基线是 2026-09-10 的 `origin/main` `5f23bbf`。该基线已包含 RFC 0010；已审阅的
P4-C1 candidate 为 `63b62d9`，但它**不是**该 `main` 的祖先，因此仍是未合并的前驱候选。
可以现在审阅本 RFC，但接受或合并本文都不能满足 P5-A1 predecessor gate。

## 授权边界

P5-A1 严格为 contract-only。仅当本 amendment 获接受且前驱门禁随后通过时，P5-A1 才可添加：

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

在实际 P4-C1 实现及其 v1-v3 compatibility fixture 合并到 `main`、经独立验证且与下述类型
一致前，P5-A1 仍处于 blocked 状态。发现不一致时必须回调 RFC，不能在代码中顺手修补。

## 需要批准的 Proposed decisions

| ID | Proposed decision |
| --- | --- |
| P5A1-1 | 按上述边界将 P5-A1 严格限定为 contract-only。 |
| P5A1-2 | 可复用的 public 图片选项使用具名 `StrEnum`；只有 discriminator 与固定 tile-size 常量保留 `Literal`。 |
| P5A1-3 | 精确冻结下述五种 transformation parameter object；missing/unknown key 均拒绝。 |
| P5A1-4 | schema-v4 completed/failed fixture 是 provider/backend identity 为 null 且不声称 Pillow 的直接 contract specimen。 |
| P5A1-5 | 只在 schema-v4 failed-problem allowlist 增加 `unsupported_image_profile`，其 details object 为 closed；v1-v3 reader 继续拒绝它。 |
| P5A1-6 | 只增加下述有界 terminal projection；仅当所有事实都能无损表达于目标前驱时才允许 downgrade。 |

在 human 明确批准相应 ID 并通过后续文档变更更新本 RFC 状态前，上表均不是 Accepted。

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

Public model 的 role object key 始终先 `before` 后 `after`。Canonical JSON byte order 沿用
现有 serializer；本文 pretty example 的空白仅用于阅读。

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

## Contract-only canonical fixtures

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
      "comparator_id": "image.decoded_samples",
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
`plugin_host`、两个 provider、`backend_id` 与 `backend_version` 必须为 JSON null；两种 fixture
任何位置都不得出现 `pillow`、`PIL`、Pillow version、distribution name、module path 或 local path。

Completed specimen 必须 `artifacts=[]`、full fidelity、complete `ChangeSet` 且无 diagnostic；只使用
RFC 0007 已接受的 image metric/evaluation/change/summary/resource/digest invariant。所有
configured/used resource 使用 RFC 0007 精确名称并按字典序排列，五条 transformation 按 normative
order 出现。Failed specimen 不含 `DiffResult`、artifact、metric、change、comparison provenance 或
transformation；execution 终止于 failed `decoding` stage，并携带下述精确 problem。

P5-A1 只可在 schema validation 中 reserve `image`、`image.decoded_samples` 与
`image.decoded_samples.tiles.v1`；runtime registry 继续拒绝它们。后续 P5-A2/P5-A3 runtime 必须记录
实际 selected backend 与 Platydiff implementation version，不得把
`implementation_version="contract-only"` 复制到 runtime outcome。

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
`UnsupportedImageProfileReason`。Message 遵守 inherited bound/escaping rule 的 terminal-safe
Unicode，但不得含 source byte、metadata、ICC/EXIF value、absolute/module path 或 backend
exception text。Canonical fixture message 固定为
`input is outside the static PNG 8-bit profile`。

`CapabilityProblemV4` 不新增 code，其 mapping/resolving-stage rule 与 P4-C1 schema-v3 capability
problem 相同。`unsupported_image_profile` 绝不是 unavailable，也不出现在 detecting/resolving。

Allowlist 必须先按 outer envelope version gate 再 decode problem：schema v1、v2、v3 分别将该 code
作为各自 invalid failed code 拒绝；只有 schema v4 可在满足全部 tuple/detail invariant 时接受。
仅把 v4 fixture 的 outer `schema_version` 改为 `1`、`2` 或 `3` 必须 decode 失败；reader 不得静默
reinterpret、drop 或 rename 该 code。

## 最小安全 terminal projection

P5-A1 只可扩展 terminal renderer 以消费已验证 v4 outcome。它不获得 source service/artifact root，
不计算 metric、digest、image 或 verdict。Inherited header、fidelity、summary count 与 diagnostic 不变。

对每个 retained `ImageChange` 恰好附加一行：

```text
descriptor <component> changed
tile x=<x> y=<y> width=<width> height=<height> changed_pixels=<count> maximum_absolute_error=<tagged-number>
```

Descriptor form 只使用已验证 component wire value；tile form 只使用已验证 integer field 与现有 tagged
numeric rendering。Finite value 使用现有 locale-independent float representation，Inf/NaN 使用现有
显式 tag。不得打印 digest、pixel、path、label、metadata、profile 或 source excerpt。Truncated result
只 render retained item 与 inherited complete total，不得暗示 omitted tile 不存在。

Canonical failed fixture 的 inherited problem projection 精确为：

```text
failed [unsupported_image_profile/415] at decoding: input is outside the static PNG 8-bit profile
```

Unknown schema-v4 built-in change/transformation/enum/problem code 必须在 rendering 前由 reader 拒绝；
renderer 不猜测 generic image meaning。Namespaced `ExtensionChange` 保持现有显式 generic presentation。

## Upgrade、downgrade 与 reader 边界

V4 reader 接受并保留有效 v1/v2/v3/v4 envelope。显式 v1/v2/v3-to-v4 helper 只增加 predecessor
migration 已接受的 neutral default，不把 legacy outcome relabel 为 image。

Renderer、CLI、JSON writer 或 reader 均不得自动 downgrade。只有 validation 证明每个 field 都能由
目标版本表达时，显式 `downgrade_outcome_v4(outcome, target_version)` 才成功。包含以下任意内容即拒绝：

- image spec kind 或 image change；
- `image.*` built-in transformation/comparator/algorithm/metric/evaluation/resource/capability-attempt ID；
- `unsupported_image_profile`；
- 任意 schema-v4-only fact、enum value 或 problem shape。

Helper 随后必须应用现有 v3-to-v2 与 v2-to-v1 gate，不能绕过它们。所有
`ImageCompareSpec` outcome 和两种 P5-A1 canonical fixture 都不能 downgrade 到 v1-v3。不识别 v4 的
旧 reader 必须返回现有 unknown-schema error，无需产生 lossy approximation。

## 机械验收条件

接受本 RFC 不授权代码。以后派发 P5-A1 时，merge 前必须满足：

1. 实际 merged P4-C1 commit 是 implementation branch 的祖先，完整 predecessor suite 原样通过，
   且 public v3 type 与本 amendment 一致；否则停止并回调 RFC。
2. `ImageCompareSpec`、`ImageResourceLimits`、`ImageChange`、具名 enum、v4 outcome alias/class、
   `ExecutionProblemV4` 与显式 migration 位于已记录 public export set；不 export decoder/backend object。
3. 所有新 object 拒绝 missing/extra key、boolean-as-integer、invalid enum、invalid mode/IHDR/band
   combination、invalid role order/digest 与 cross-field invariant violation。
4. 五条 transformation record 各自接受 canonical payload，并拒绝错误 stage、ID、key、type、
   nesting、value 或 sequence position。
5. v1/v2/v3 canonical file 保持 byte-identical；全部 predecessor round trip、migration、plugin receipt、
   CLI output 与 public export 保持有效。
6. 两个 v4 fixture byte-identical round-trip；测试证明 direct construction、null provider/backend、
   无 Pillow string、无 image runtime registration/CLI route/dependency，以及适用的 v1-v3 code gate rejection。
7. V4 reader 在 terminal rendering 前拒绝 duplicate key、unknown schema、unknown built-in
   kind/transformation/problem 与 invalid image change combination。
8. Terminal golden test 覆盖 descriptor、tile、truncated、failed、unsafe message、unknown-kind，且不授予
   source/artifact authority。
9. Migration test 证明 lossless predecessor upgrade、可表达的 legacy-only v4 downgrade，以及所有
   image-bearing 或 `unsupported_image_profile` downgrade 的 hard rejection。
10. Ruff format/check、strict mypy、完整 pytest、build/wheel/sdist inspection、`git diff --check` 与
    relative-link check 全通过；只能报告实际运行的命令。

Implementation diff 不得包含说明性 test/doc 之外的 Pillow reference、dependency metadata、image
decoder/scanner/comparator、capability registration、CLI image route、auto/SDK expansion、artifact、
corpus image 或 UI code。

Proposed P5-A1 commit boundary 为：

1. `feat(core): add schema-v4 image comparison contracts`
2. `feat(renderers): add bounded schema-v4 image projection`
3. `test(core): add schema-v4 compatibility and migration fixtures`

每个 commit 都必须通过相关 predecessor test；第三个是 gate commit，必须证明上方完整机械验收条件。

## 与后续门禁的关系

P5-A2 仍是首个 optional-backend/decode gate；P5-A3 仍是首个 comparator、capability-registration、
terminal command 与 executable image-result gate，二者独立派发。本 amendment 不改变或授权
P5-C/P5-P/P5-F/P5-M/P5-H/P5-S callback。

若获接受，本 RFC 只 supersede RFC 0007 中仍开放的 P5-A1 enum representation、transformation JSON
shape、schema-only fixture identity、schema-v4 problem gate、terminal projection 与 downgrade
mechanics；其余 I1-I16 decision 和 RFC 0007 语义继续有效。

## 参考

- [RFC 0001：Comparison outcome 与 DiffResult](0001-comparison-outcome-and-diff-result_zh.md)
- [RFC 0004：Human review UI 与 renderer boundary](0004-human-review-ui-and-renderer-boundary_zh.md)
- [RFC 0007：图片比较](0007-image-comparison_zh.md)
- [RFC 0010：Schema predecessor 与 Phase 6 amendment](0010-schema-predecessor-and-phase6-contract-amendment_zh.md)
