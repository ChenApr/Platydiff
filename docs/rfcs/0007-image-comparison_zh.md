# RFC 0007：图片比较

[English documentation](0007-image-comparison.md)

- 状态：Accepted
- 日期：2026-09-10
- 评审修订：2026-09-10
- 接受日期：2026-09-10
- Owners：Platydiff 维护者
- 实现 owner：尚未指派；已记录条件授权，coordinator 只有在实际 predecessor merge gate
  通过后才能派发
- Predecessor amendment：RFC 0010 记录 P5-A1 的条件授权；只有 RFC 0010、P4-C1/schema-v3
  与 predecessor compatibility fixture 都合并到 `main` 后才能派发；P5-A1 不会自动启动
- Proposed P5-A1 wire amendment：[RFC 0011](0011-p5a1-image-wire-contract-amendment_zh.md)
  闭合 enum、transformation、fixture、problem、terminal 与 downgrade 选择；只有单独获接受后
  才有效

## 摘要与授权边界

本 RFC 定义已接受的 Phase 5 图片比较契约。它刻意从一个狭窄的可执行切片开始：显式、
内建地比较单张静态 PNG 的解码 sample matrix。encoded-byte identity 继续使用既有 binary
契约。感知相似、色彩转换、配准、动画、artifact、plugin 执行与自动图片探测仍是彼此
独立的后续门禁。

人类批准已将下列 I1-I16 接受为 Phase 5 设计契约。接受本文不授权图片代码、依赖、SDK
修改、自动探测、UI 工作或 artifact 发布，也不启动 P5-R、P5-A1、P5-A2 或 P5-A3。每个
实现门禁仍须从更新后的 `main` 单独派发。

Phase 4 RFC 0006 已接受，但本 RFC 评审所依据的代码还没有 P4-A1/schema-v3 实现。因此
Phase 5 有一个硬性重新验证前置条件：schema v3 必须先合并、按 RFC 0006 验证，并作为
实际前驱。本文不假设或 stack 在未合并的 Phase 4 分支之上；已接受的 evidence revision
不存在 image product code，本次 acceptance-only 变更也不添加任何代码。

## 证据账本

| 在 `main` `fde2bd4` 评审的证据 | Phase 5 约束 |
| --- | --- |
| runtime code 只接受 outcome schema v1/v2；RFC 0006 接受 schema v3，但该 revision 尚未实现。 | 图片实现须等待合并后的 schema-v3 代码与 fixture 重新验证；之后图片 variant 使用 schema v4，不重新打开冻结的前驱。 |
| 代码中的 public spec/change union 只有 text/binary variant。 | `ImageCompareSpec` 与 `ImageChange` 需要 schema successor 和严格 reader/writer 兼容测试。 |
| `BinaryCompareSpec` 已为任意有界 byte source 定义不受哈希碰撞影响的 exact byte identity。 | 图片代码不得重复或重新解释 encoded-file equality。 |
| 既有 automatic detection 与 SDK v1.1 对 text/binary 封闭。 | 图片只显式选择且只使用 built-in；auto image detection 与第三方 image comparator 需要 RFC 0003/0005 的后继 RFC。 |
| source snapshot 负责有界读取、hash、mutation check 和安全 label。 | 图片 backend 消费 host-owned replayable service，绝不按名称重新打开 path。 |
| renderer 消费 validated outcome，且没有 source/artifact root。 | 图片事实必须在 outcome 内有界；renderer 不得重读 pixel、计算 metric 或创建 heatmap。 |
| `ArtifactRef` 是安全的 inert metadata，但尚无 comparison artifact sink/root。 | 首个图片切片发出 `artifacts=()`；preview/heatmap 交付需要独立 artifact-authority 契约。 |
| core runtime dependency 为空。 | Pillow 必须 optional、lazy、独立评审，不能成为 core dependency。 |
| 2026-09-10 评审的当前候选是 Pillow 12.3.0；官方 metadata 声明 Python 3.10+ 与 MIT-CMU，12.3.0 修复多个影响旧版本的 2026 memory-safety 问题。 | dependency gate 从 `Pillow>=12.3,<13` 开始，实现时重新检查 advisory，盘点 bundled native library，且不声称 Pillow 是 sandbox。 |

该账本只记录约束，不授权实现。未合并 P4-A1 分支的证据可以辅助评审，但不能满足前置条件。

## 设计与既有契约矩阵

| 既有契约 | 不重新解释地复用 | Phase 5 增量/回调 |
| --- | --- | --- |
| RFC 0001 outcome/result | completed/unavailable/failed、relation/verdict/fidelity 分离、complete/truncated 语义、metric/evaluation 分层、安全 `ArtifactRef` | 增加一个 schema-v4 built-in `ImageChange`；不增加 outcome kind 或改变 fidelity 含义 |
| RFC 0002 phase gate | 显式 intent、唯一 public `compare()` 入口、聚焦 commit、确定性 limit、独立授权 | 增加 P5-R/P5-A1/P5-A2/P5-A3；后续 image 能力重新进入 contract gate |
| RFC 0003 binary/detection | encoded equality 继续属于 binary；显式 type 绕过 detection；host snapshot 与执行开始后不 fallback 保持 | Image auto probing、ambiguity、candidate 与 ranking 延后到 successor |
| RFC 0004 renderer/UI | UI 消费 validated bounded outcome，不能重读 source 或重算真值 | schema 支持后可展示 image tile；preview/heatmap 与 UI-U1/U2/U3 仍未实现 |
| RFC 0005 SDK | built-in-only default、host-owned source/stage/outcome、renderer least authority、SDK v1.1 对 text/binary 封闭 | Image plugin capability 与 source/profile validation 需要 SDK v2 评审 |
| RFC 0006 schema/structured 经验 | closed-union 增长使用新 schema、保留前驱、显式 transform、不产生 partial、fact 先于 rendering | Schema v4 依赖实际合并 v3；重新验证后才增加 image descriptor/tile/metric/limit |
| 当前 package | flat package、Python 3.12+、既有 CLI exit、零 core dependency、terminal/JSON downstream | optional `image` extra 与 private decoder/comparator 只在后续授权门禁加入 |

矩阵中的任何一行都不授予实现权限，也不改变旧 schema 的含义。

## 已接受的决策

| ID | 已接受的决策 | 未选择的替代方案 |
| --- | --- | --- |
| I1 | 接受 I1-I16 作为 Phase 5 设计契约；接受不启动 P5-R 或任何实现门禁。 | 把 RFC 接受或 roadmap 项目当作实现授权。 |
| I2 | 任何 Phase 5 实现前，必须合并并独立验证 P4-A1/schema v3；随后使用 outcome schema v4。 | stack 在未合并代码上，或在未验证实际前驱时原地扩展 v2/v3。 |
| I3 | Phase 5 只显式选择且只使用 built-in；不改变 auto detection 或 SDK v1.1。 | 让扩展名、Pillow sniffing 或已安装 plugin 静默选择图片语义。 |
| I4 | encoded-byte identity 继续由 `BinaryCompareSpec` 负责；不增加为同一事实返回另一种形状的 image alias。 | 在 `ImageCompareSpec` 内复制 byte comparison。 |
| I5 | 首个 decoded slice 只支持一张静态 PNG，sample mode 为 8-bit `L`、`LA`、`RGB` 或 `RGBA`。 | 一开始支持全部 Pillow codec、palette/低位深/16-bit PNG、JPEG、动画或多页内容。 |
| I6 | 比较 stored orientation、精确尺寸、native channel order、straight alpha、精确 color-description identity 与每个 decoded sample；不做隐式转换。 | 自动旋转、resize、crop、palette expand、premultiply、color convert，或忽略解释 metadata。 |
| I7 | DPI、timestamp、comment 与 application field 等非解释性 metadata 不影响 relation；只记录有界 policy fact，绝不记录 raw metadata。 | 把任意 metadata 计入 pixel equality 或静默泄露。 |
| I8 | 使用确定性的 descriptor/fixed-tile change，且不包含 raw pixel payload；完成比较后才截断 detail。 | 每像素一个 change、嵌入图片，或让 renderer 重读 input。 |
| I9 | 定义精确 count/error metric 与 strict equality evaluation；metric 不能成为隐藏 normalization。 | 由 terminal/HTML 重算 score 或推断 verdict。 |
| I10 | 只产生 full-fidelity 的 complete/truncated result；首切片没有 fallback、retry、degraded 或 partial。 | fallback 到 binary/其他 decoder/resized comparison，或从未完成工作返回 equality。 |
| I11 | 首切片不产生 artifact；heatmap/preview 需要显式 host-owned artifact sink/root 与 RFC 0004 的重新评审。 | 向 comparator 或 renderer 提供任意 filesystem path。 |
| I12 | Pillow 作为受信任的进程内 optional code 放在 `image` extra 后，只启用 PNG decoder 与已评审版本范围。 | 把 Pillow 加入 core、加载所有注册 decoder，或声称 sandbox。 |
| I13 | 尽可能在下一次 logical allocation/work unit 前执行 source、dimension、pixel、decoded-byte、metadata、work、change-item/payload limit。 | 只依赖 Pillow global decompression-bomb threshold 或墙钟 timeout。 |
| I14 | 使用稳定 unavailable/failed outcome；损坏、恶意或越界 input 绝不报告为 content difference。 | 返回占位 `DiffResult` 或 best-effort relation。 |
| I15 | 只使用生成且有 license 记录的 image fixture，并保留不依赖 encoder 的准确 expected sample matrix。 | 提交个人、抓取、竞赛受限或 license 不明图片。 |
| I16 | 把 image 交付拆成独立授权门禁；先做 decoded exact PNG，perceptual/color/artifact/animation 不自动开始。 | 把“image support”作为一个宽泛批次交付。 |

## 三个不同问题

Phase 5 不得用一个标签表示三种不同 predicate。

### 编码文件 identity

既有 `BinaryCompareSpec` 回答长度与每个 encoded byte 是否相等。它可用于 PNG、JPEG 或
任何其他文件，且不理解 container。其 algorithm、`BinarySpan`、metric、policy、provenance
和 schema 继续由 RFC 0003 管理。

因此，两份压缩方式不同的 PNG 可以 binary-different，却解码为相同 sample matrix。这不是
矛盾；两个 outcome 回答不同的显式 spec。Phase 5 不增加 `encoded_bytes` image mode，也
不增加 `platydiff image --encoded` alias。

### 解码 sample equality

首个图片切片回答：两侧能否在所选 profile 下解码为相同 image descriptor 与 sample matrix。
`relation="equal"` 表示所有具有比较意义的 descriptor field 相同，且每个
`(x, y, channel)` coordinate 的 sample 完全相同。算法不能只凭 digest 建立 equality。

这是 sample equality，不是 displayed-color、perceptual、structural 或 metadata equality。
在已接受的 native-profile 契约下，即使 integer sample 一致，unprofiled image 与 profiled
image 仍不同，因为 sample 的声明解释不同。

### 感知相似

Perceptual equivalence 不属于首个 public image spec。后续 P5-P successor 必须增加新的
schema/spec mode，并说明 `relation` 表示选定 perceptual predicate 通过，而不是 pixel
identity。所有阈值必须通过 policy evaluation 暴露，exact decoded metric 继续作为事实；
backend 或 budget 失败时不能静默替换 exact comparison。

接受 SSIM 前，后继 RFC 必须冻结：color space/transfer function、alpha/background 处理、
dimension/alignment policy、window size/weight/sigma、covariance convention、constant、border
handling、channel aggregation、accumulation order、numeric precision、score range、empty/small
image 行为和 inclusive threshold。LPIPS 等 learned metric 还需要 model weight、license、hash、
hardware、determinism 与 supply-chain 评审。不得把 PSNR 单独宣传为 perceptual equivalence。

## Schema-v4 与兼容性契约

按已接受决策 I2，在其前置条件满足后，schema v4 是实际已合并 schema v3 的 additive
semantic successor：

```python
CompareSpecV4 = CompareSpecV3 | ImageCompareSpec
ChangeV4 = ChangeV3 | ImageChange
```

- 既有 built-in text/binary/auto 调用保持 schema v1。
- 既有 SDK-v1.1 text/binary host 调用保持 schema v2。
- 已合并 Phase 4 调用保持实际已实现且验证的 schema v3。
- 每个 `ImageCompareSpec` outcome 使用 schema v4，包括 validation、sourcing 或 resolution failure。
- v4 reader 接受 v1/v2/v3/v4；保留既有 writer。
- 显式 v1/v2/v3-to-v4 upgrader 只增加有文档的中性默认值。
- 不自动 downgrade；只有事实能由目标旧 schema 表示时，才允许显式 lossless helper。
- 未知 built-in spec/change/transformation ID 仍是错误；namespaced extension change 保持 RFC 0001 行为。
- 既有 byte-stable fixture、CLI route、plugin receipt 与 schema-v3 fixture 保持不变。

如果合并后的 P4-A1 schema 与 RFC 0006 不一致，Phase 5 停止并先修订本文。图片实现不得
针对假想类型“预留”v4，也不能在 predecessor audit 前发布 image model。

### 兼容性矩阵

| producer/path | schema | 图片参与 | 必需行为 |
| --- | --- | --- | --- |
| 既有 `compare()`/default CLI | v1 | 无 | 既有 text/binary/auto payload 保持 byte-stable。 |
| 既有 `PluginHost` | v2 | 无 | SDK v1.1 保持 text/binary-only；receipt 有效。 |
| 已合并 Phase 4 built-in | v3 | 无 | 实际 v3 model、migration 与 fixture 是前驱。 |
| 已接受的 built-in image path | v4 | 仅显式 static PNG | strict v4 validation 与继承 invariant。 |
| `PluginHost` + `ImageCompareSpec` | 无 | 不支持 | Python 返回 resolving-stage unavailable；CLI plugin flag + image 为 usage exit 2。 |
| 既有 auto 遇到 PNG byte | v1 | 无 | 既有 text/binary evidence 与 selection 不变。 |
| 未来 image auto/SDK/perceptual | 未指定 | 未指定 | 需要 successor RFC 与自己的 schema 决策。 |

## Public image intent

已接受的 normalized public shape 为：

```python
class ImageResourceLimits:
    max_input_bytes: int = 16 * 1024 * 1024
    max_width: int = 16_384
    max_height: int = 16_384
    max_pixels: int = 16_777_216
    max_decoded_bytes: int = 64 * 1024 * 1024
    max_metadata_wire_bytes: int = 1024 * 1024
    max_metadata_decompressed_bytes: int = 4 * 1024 * 1024
    max_icc_profile_bytes: int = 1024 * 1024
    max_compare_work: int = 67_108_864
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024


class ImageCompareSpec:
    kind: Literal["image"] = "image"
    semantic: Literal["decoded_samples"] = "decoded_samples"
    format: Literal["png"] = "png"
    orientation: Literal["stored"] = "stored"
    color_profile: Literal["require_exact"] = "require_exact"
    alpha: Literal["straight"] = "straight"
    alignment: Literal["exact_dimensions"] = "exact_dimensions"
    metadata: Literal["ignore_non_interpretive"] = "ignore_non_interpretive"
    tile_size: Literal[64] = 64
    limits: ImageResourceLimits = ImageResourceLimits()
```

即使 field 在首切片只有一个值，也要全部写入 normalized schema JSON，使意图转换与未来
migration 明确。integer 拒绝 boolean 并使用 checked arithmetic；通过当前 numeric model
序列化的 count-like public value 使用既有 exact-integer 上限。

支持 `PathSource` 与 `BytesSource`。`TextSource` 在 `sourcing` 阶段以
`source_type_unsupported` 失败；text
不能隐式编码成图片。`compare(before, after, spec)` 继续作为唯一 built-in Python 入口。
schema gate 后，top-level 只增加已接受 spec/limits/enum/change；decoder、image IR、tile
walker 与 Pillow adapter 保持 private。

若 CLI gate 后续获得授权，形状为：

```text
platydiff image BEFORE AFTER
platydiff compare --type image BEFORE AFTER
```

两个 route 构造同一 spec 并调用同一路径；不推断类型，也不接受 plugin、detector、comparator、
stdin、URL、directory、recursive、configuration、artifact、resize、crop、rotate 或 color-conversion
flag。既有 exit 保持 `0/1/2/3`。

## 支持的 PNG profile

首个 decoder 只接受一个非动画 PNG datastream，decoded mode 必须严格为：

| Mode | Sample layout | Depth | Alpha |
| --- | --- | ---: | --- |
| `L` | grey | 8 bits | 无 |
| `LA` | grey, alpha | 每通道 8 bits | straight/unassociated |
| `RGB` | red, green, blue | 每通道 8 bits | 无 |
| `RGBA` | red, green, blue, alpha | 每通道 8 bits | straight/unassociated |

首切片不支持 palette/indexed、1/2/4-bit greyscale、16-bit sample、premultiplied mode、CMYK、
floating point、APNG、multiple frame/page 和非 PNG codec。需要 palette/隐式 alpha expansion
的 PNG `tRNS` transparency 被拒绝；后续 profile 可加入显式且有记录的 expansion，但不能
重新解释当前 profile。

Pillow 收到 byte 前，host 先执行下述有界 source-level scanner；随后向 backend 传
`formats=("PNG",)`，并在 pixel load 前后验证 backend 报告的 format、frame count、
animation flag、mode、dimension 与 interpretation metadata。filename extension/MIME string
从不作为 authority；其他 Pillow global decoder 都不 eligible。

### 规范性 pre-decode PNG scanner

由 host scanner 而不是 Pillow 决定 datastream 是否属于首切片 profile。它只消费 host
snapshot，使用 checked unsigned arithmetic，并在 `Image.open()` 前完成以下检查：

1. 验证 8-byte signature。对每个 chunk，依次读取 unsigned 32-bit big-endian length、4 个
   ASCII letter type byte、严格相应数量的 data byte，以及 type+data 的 CRC-32。truncation、
   overflow、非 letter type byte、reserved 第三个 type byte 为小写、bad CRC、`IEND` 后仍有
   data 或缺少 `IEND` 都被拒绝。
2. 要求首个 chunk 是唯一的 13-byte `IHDR`，至少有一段连续 `IDAT`，最后一个 chunk 是唯一的
   zero-length `IEND`。对每个 recognized chunk 执行 PNG Third Edition 的 ordering、
   multiplicity、length 与 combination rule。非法值或非法 chunk 结构属于 malformed input，
   不是 unsupported profile。
3. 验证 `IHDR` width/height 与 compression/filter/interlace field。合法但不支持的
   color-type/bit-depth pair——包括 1/2/4-bit greyscale、indexed color 与所有 16-bit form——
   必须在 Pillow 前拒绝。只有 `(color type, bit depth)` `(0,8)`、`(4,8)`、`(2,8)`、`(6,8)`
   分别映射到 `L`、`LA`、`RGB`、`RGBA`；PNG 本身非法的 pair 属于 malformed input。
4. 任意 `tRNS`、`acTL`、`fcTL` 或 `fdAT` 均作为 unsupported profile 拒绝；任何 unknown
   critical chunk 也作为 unsupported 拒绝。unknown ancillary chunk 只有在 framing、CRC、
   reserved bit 与 resource accounting 通过后才能被语义忽略。
5. 在 PNG 允许处验证 `PLTE`：最多一次、位于 `IDAT` 前、长度大于零且能被三整除，并且不超过
   768 byte；color type 0/4 禁止 `PLTE`。indexed color 仍不支持；color type 2/6 的 optional
   `PLTE` 属于非解释性信息。
6. `cHRM`、`gAMA`、`iCCP`、`sBIT`、`sRGB`、`cICP`、`mDCV`、`cLLI` 各最多一个，并验证
   normative placement 与 combination。data length 依次为 32、4、variable、随 mode 而定
   （本 profile 为 1/3/2/4）、1、4、24、8 byte；还须验证 PNG Third Edition 要求的 registered
   value 与 field constraint。host 验证 `iCCP` profile name/compression framing，并在 Pillow 前
   有界 inflate 其 zlib stream；trailing 或 malformed compressed data 被拒绝。
7. 有界 inflate compressed `zTXt` 与 compressed `iTXt` 以完成 accounting/validation，随后丢弃；
   验证 uncompressed text chunk framing，但不保留内容。任何 textual、EXIF 或 application
   payload 都不进入 public result。

scanner 将 bad signature/framing/CRC/order/multiplicity、PNG 非法值及 malformed compressed
metadata 分类为 `decode_error`。合法 PNG 中超出 accepted profile 的 feature——合法的低/16-bit
pair、indexed color、`tRNS`、APNG 或 unknown critical chunk——分类为
`unsupported_image_profile`。跨越 source、metadata、ICC、dimension、pixel 或 decoded-byte
limit 分类为 `resource_limit_exceeded`。这些稳定分类均发生在 `decoding`；Pillow 不能重新分类或
扩大 accepted profile。

### Orientation、color、alpha 与 metadata

- `orientation="stored"` 以 stored row/column order 比较 decoded matrix；不应用 EXIF orientation。
  首切片也不解析它。provenance 只记录有界的 `eXIf` presence 与 on-wire byte count；不保留 raw
  byte 或 tag value。这不是 pixel transformation。
  display-oriented equality 需要未来显式 `apply_exif` profile 与 transformation record。
- `color_profile="require_exact"` 不做 color conversion。PNG color-signaling chunk `cHRM`、
  `gAMA`、`iCCP`、`sBIT`、`sRGB`、`cICP`、`mDCV` 与 `cLLI` 的有界 canonical
  description 必须匹配后才比较 sample，包括 ICC data 的 presence/digest 与其他 chunk 的精确
  有界值。raw profile 永不
  serialization。descriptor mismatch 是 completed difference，不触发 conversion/decode fallback。
- `alpha="straight"` 遵循 PNG unassociated alpha。alpha 作为 channel 比较，zero-alpha pixel
  背后的 color sample 仍参与。不 premultiply、composite、选择 background 或忽略 invisible RGB。
- DPI、timestamp、comment、textual chunk、camera/application field 等非解释性 metadata 不影响
  relation，不复制到 result，也不计为 change；其解析仍受资源边界限制。项目不称之为 redacted
  或 anonymous。

dimension、pixel format 或 color-description mismatch 会停止 sample comparison，因为 coordinate
或 sample meaning 不可比较；它产生 completed `different/fail`、descriptor change 与零
compared pixel，而不是 `alignment_failed`。

## Image change 与 evidence

```python
class ImageChange:
    kind: Literal["image_change"] = "image_change"
    operation: Literal["descriptor_replace", "tile_replace"]
    component: Literal[
        "dimensions", "pixel_format", "color_description"
    ] | None
    x: int | None
    y: int | None
    width: int | None
    height: int | None
    before_digest: str
    after_digest: str
    changed_pixels: int | None
    maximum_absolute_error: NumericValue | None
```

descriptor change 要求一个 component，不含 rectangle、pixel count 或 error；顺序为 dimensions、
pixel format、color description。未变 component 不产生 change；只要有 descriptor change 就不
产生 tile change。

descriptor 兼容时，从左上开始分割 64x64 tile，边缘 tile 使用实际 positive dimension。只有
至少一个 pixel 不同时才产生 tile change；它要求 zero-based `(x,y)`、positive width/height、
component 为空、tile 内精确 changed-pixel count 和 maximum absolute sample error。tile 依
`y`、`x` 排序，不重叠且在边界内。`ChangeSet.total_count` 是完整 descriptor/changed-tile
数量，不是 changed-pixel 数量。

`before_digest` 与 `after_digest` 是对应一侧的小写 64-hex SHA-256。digest input 固定为：

```text
RAW_ASCII("platydiff/v4/image/" + domain) || 00 || U64BE(len(payload)) || payload
```

`RAW_ASCII(s)` 严格是 `s` 的 ASCII byte。`U64BE` 是 unsigned 8-byte big-endian integer，所有
length/count 都使用它；field encoding `ASCII(s)` 是
`U64BE(len(s)) || RAW_ASCII(s)`；`U8` 是一个 byte。不执行 Unicode normalization，也没有末尾
NUL。四个 domain string 严格为 `descriptor/dimensions`、`descriptor/pixel_format`、
`descriptor/color_description` 与 `tile/samples`。

canonical payload 为：

- dimensions：`U64BE(width) || U64BE(height)`；
- pixel format：`ASCII(mode) || U8(bit_depth) || U8(channel_count) ||` sample order 中每个 band 的
  `ASCII(band)`，最后是 `ASCII(alpha)`；alpha 严格为 `none` 或 `straight`；
- color description：按 `cHRM`、`gAMA`、`iCCP`、`sBIT`、`sRGB`、`cICP`、`mDCV`、`cLLI`
  顺序，对每项追加 4 个 type byte 和一个 `U8` presence byte。absent 为 `00`；present 为
  `01 || U64BE(length) || canonical value`。除 `iCCP` 外，canonical value 是已验证的 raw chunk
  data；`iCCP` 只使用有界解压后的 ICC profile byte，profile name、compression byte 与 chunk CRC
  不属于 interpretation fact；
- tile samples：`U64BE(x) || U64BE(y) || U64BE(width) || U64BE(height) ||` pixel-format payload
  到最后一个 band，再接 sample byte。sample 是 unsigned one-byte value，依 stored top-to-bottom
  row、left-to-right pixel、declared band order 排列，无 row padding；边缘 tile 使用实际 width/height。

下列规范 vector 使用 1x1、8-bit、straight-alpha `RGBA` 图片，无 color-description chunk，tile
sample 为 `00 7f ff 80`：

| Domain | Payload hex | SHA-256 |
| --- | --- | --- |
| `descriptor/dimensions` | `00000000000000010000000000000001` | `37b783ef79ab757a531e50f76237eb9c870203f7003c5b9dcfc0280ded598a12` |
| `descriptor/pixel_format` | `000000000000000452474241080400000000000000015200000000000000014700000000000000014200000000000000014100000000000000087374726169676874` | `9e7453f90b6a38c85e068b2aaa31ee0836422caf523192cdd8c39faa9021bf0c` |
| `descriptor/color_description` | `6348524d0067414d410069434350007342495400735247420063494350006d44435600634c4c4900` | `71d104a33d792f584bb9f5ed92ab1feee8625a59b3012513d08d905fa4a08145` |
| `tile/samples` | `00000000000000000000000000000000000000000000000100000000000000010000000000000004524742410804000000000000000152000000000000000147000000000000000142000000000000000141007fff80` | `85c3961556e42038b134b2a3864231be5e533aad78c1cb68d95210f5d2b5fa55` |

这些 digest 用于发现 serialization 错误，不建立 equality、不隐藏低熵内容，也不授权 renderer
获取 source pixel。tile item 不含 raw/encoded pixel。

Comparator 先计算全部 descriptor/tile fact 与 total，再保留有界 row-major prefix。Truncation
使用完整 item 与继承的精确 canonical-payload 计数，不改变 relation、verdict、fidelity、metric
或 total。Phase 5 不产生 `partial`。

`DiffSummary.change_count` 等于 `image.changed_items` 与 `ChangeSet.total_count`。Summary
count 按稳定 name 顺序为：unit `pixels` 的 `changed_pixels`、unit `tiles` 的 `changed_tiles`
和 unit `items` 的 `descriptor_changes`。descriptor mismatch 时 `changed_pixels` 与
`changed_tiles` 为零，因为没有 evaluated comparable sample pair；这不表示图片相等。

## Metric、relation 与 policy

Metric 顺序与含义固定：

| Metric | 出现条件 | Unit | Direction | Aggregation |
| --- | --- | --- | --- | --- |
| `image.compared_pixels` | 始终 | `pixels` | `neutral` | `count` |
| `image.equal_pixels` | 始终 | `pixels` | `neutral` | `count` |
| `image.changed_pixels` | 始终 | `pixels` | `lower_is_better` | `count` |
| `image.compared_samples` | 始终 | `samples` | `neutral` | `count` |
| `image.changed_items` | 始终 | `items` | `lower_is_better` | `count` |
| `image.mean_absolute_error` | descriptor 兼容且至少一个 sample | `sample_levels` | `lower_is_better` | `mean` |
| `image.root_mean_square_error` | 同上 | `sample_levels` | `lower_is_better` | `root_mean_square` |
| `image.peak_signal_to_noise_ratio` | 同上 | `decibels` | `higher_is_better` | `peak_signal_to_noise_ratio` |

descriptor 兼容时，equal + changed pixel = compared pixel；compared sample = compared pixel *
channel count。至少一个 channel 不同则 pixel changed。MAE/RMSE 按 row-major pixel 与声明的
channel order 聚合所有 sample 的 absolute/squared error。peak sample value 为 255。MSE 为零时
PSNR 是 positive infinity，否则为 `10 * log10(255**2 / MSE)`。

metric operation order 是规范性的。对 stored row-major/band order 中每个 sample pair，令
`difference = int(before) - int(after)`，再更新 checked arbitrary-precision integer accumulator：
`absolute_sum += abs(difference)` 与 `squared_sum += difference * difference`。pixel-change count
也是 integer，且在任何 floating operation 前完成。全部 `sample_count` 个 sample 后，严格按此顺序
执行 binary64 operation：

```python
mae = float(absolute_sum) / float(sample_count)
mse = float(squared_sum) / float(sample_count)
rmse = math.sqrt(mse)
psnr = (
    PositiveInfinityValue()
    if squared_sum == 0
    else FiniteValue(10.0 * math.log10((255.0 * 255.0) / mse))
)
```

MAE/RMSE 始终为 `FiniteValue`；只有 `squared_sum == 0` 时 PSNR 才是
`PositiveInfinityValue`。首切片从不产生 `NaNValue` 或 `NegativeInfinityValue`，也不使用
chunk-local floating partial、`math.fsum`、decimal arithmetic、fused operation，或把 presentation
rounded value 存为 metric。sample pair `[0, 255]` 与 `[0, 0]` 的规范事实是
`absolute_sum=255`、`squared_sum=65025`、`sample_count=2`、MAE `127.5`、RMSE
`180.31222920256963`、PSNR `3.010299956639812`（在已评审 Python binary64 path 上）。

同一 supported runtime 的重复运行必须 byte-identical serialization。跨平台 golden test 要求有限的
`sqrt`/`log10` 结果与 expected 的绝对距离不超过 `8 * math.ulp(expected)`；zero 与 exact rational result
精确比较，infinity 按 exact tagged representation 比较。该测试容差不是 comparison policy
tolerance。若未来 schema 加入 threshold，则使用 stored unrounded binary64 result；rounding 只属于
展示。首切片没有 content tolerance。

当且仅当 `image.changed_items == 0` 时 `relation="equal"`，否则为 `different`。唯一
evaluation 是 `image.decoded_sample_equality`，观察 `image.changed_items`，operator 为 `eq`、
threshold 为 zero。zero 为 pass，非 zero 为 fail。不产生默认 warn；fidelity 始终 full。

## Provenance vocabulary

normalized spec 记录全部 default。实际行为按下列稳定 transformation record 顺序记录：

| Stage | Transformation ID | 必需 parameter |
| --- | --- | --- |
| decoding | `image.png.decode` | backend/version、profile、mode、dimensions、frame count、IHDR bit depth/color type/interlace，以及各 role 的有界 resource fact |
| normalizing | `image.orientation.stored` | before/after 的 `eXIf` presence 与 on-wire byte count |
| normalizing | `image.color.native_exact` | 每个 role 的有界 color-description identity/digest |
| normalizing | `image.alpha.straight` | channel layout 与 unassociated-alpha policy |
| aligning | `image.coordinates.exact` | origin=`top_left`、x=`right`、y=`down`、dimensions policy |

这些 record 不声称发生 conversion，只说明实际执行 profile。record 不含 raw ICC/EXIF/text
metadata、absolute path、source byte、local module path 或 backend exception text。

精确的 `ResourceUsage.name` 是
`image.{before|after}.{input_bytes|metadata_wire_bytes|metadata_decompressed_bytes|icc_profile_bytes|pixels|decoded_bytes}`、
`image.compare.sample_pairs`、`image.changes.items` 与 `image.changes.payload_bytes`。每项使用
normalized spec 中对应的 limit；六项 source fact 与 limit 分别独立应用于 `before`/`after`。
public/provenance 只记录 count、boolean、dimension、stable enum value 与 descriptor digest；不记录
raw/excerpted chunk payload、profile name、text keyword/value、EXIF value 或 palette entry。

comparison provenance 记录 input hash、comparator `image.decoded_samples`、algorithm
`image.decoded_samples.tiles.v1`、Platydiff implementation version、Pillow version、可获得时
相关 linked library version、normalized spec，以及所有 configured/effective/used resource。

## Optional backend 评审

候选依赖是 optional `image` extra 中的 `Pillow>=12.3,<13`；该范围只是候选，implementation
gate 必须重新评审。

- 用途：有界 PNG identification 与 sample decoding。
- 可选性：仅在显式 image resolution 后 import；安装它不能改变 text、binary、auto 或 plugin 行为。
- License：项目 metadata/license text 为 MIT-CMU；NOTICE/SBOM 与 bundled native-library license
  仍是 implementation gate。
- Size/platform：官方 12.3.0 metadata 支持 Python 3.10+ 并发布多平台 wheel；选定 build 的
  精确 wheel/source size 与 target 要记录。
- Security：12.3.0 修复多个影响旧版本的 2026 memory-safety/DoS 问题；lock/merge 时必须重新查
  advisory。pinned hash 与 isolated environment 属于部署关注点。
- Alternative：标准库 PNG decoder 会扩大安全/维护面；OpenCV 是更重 native dependency；外部
  ImageMagick 带来 subprocess/policy/version 复杂性；它们都不是 silent fallback。

Pillow 是含 native decoder 的受信任进程内 code。decompression-bomb warning 只是纵深防御，
不是资源契约。host 保持更低的 per-run limit，把所有 `DecompressionBombWarning` 当作 error，
绝不关闭 `MAX_IMAGE_PIXELS`，并传入 exact format allowlist。Pillow 的 global mutable format
registry 是剩余 in-process trust risk；implementation 必须审计被选择的 PNG factory identity，
或使用 isolated environment 后才作出支持声明。

## Resource、恶意 input 与 failure

Host 创建 immutable snapshot 时、decode 前执行 `max_input_bytes`。PNG scanner 在读取或保留每个
ancillary chunk data 前，把其 declared data length 加入 `metadata_wire_bytes`；`IDAT` 与 critical
`PLTE` 不计入，而 color、text、`eXIf` 与 unknown ancillary chunk 计入。chunk header 与 CRC byte
由 `max_input_bytes` 覆盖，不计入 metadata subtotal。

`metadata_decompressed_bytes` 是 `iCCP`、compressed `iTXt` 与 `zTXt` 的 decompressed payload byte
总和。scanner 同时检查 aggregate `max_metadata_decompressed_bytes`，并对 `iCCP` 检查独立的
`max_icc_profile_bytes`。ICC byte 同时计入两个 limit，但在各 counter 内不重复。每个 declared
on-wire increment 在读取 chunk 前检查；每个 inflate increment 在 append 或暴露下一 output block
前检查。text output 直接丢弃；ICC buffer 不得增长到 dedicated limit 之外。truncated stream、trailing
compressed stream data 或非法 compression method 属于 decode error；超过 counter 属于 resource-limit
failure。

`IHDR` 一经验证，立刻用 checked arithmetic 检查 width、height、pixel product、channel count 与
decoded-byte product，并在 Pillow 前完成。backend mode/dimension 与相同 product 在 `load()` 前后
复查。每个 sample pair 前检查 comparison work；保留下一个完整 item 前检查 change-item 与
canonical-payload total。不得因为 Pillow 也有 limit/warning 而推迟任何检查。

每个 sample-pair equality/error update 是一个 comparison work unit。默认 `67_108_864` unit
可接受配置中最大 pixel count 的 four-channel RGBA；caller 可以在 exact-integer bound 内显式
降低或提高。执行下一个 unit 前检查；完成比较前触限返回 failed
`compare_resource_limit`，绝不返回 partial relation。

Pillow 可能在 host 能观察检查点前分配 parser/native temporary memory。因此 in-process logical
limit 不构成 hard memory sandbox。implementation gate 必须测量代表性 peak memory 并记录该
residual risk；不可信图片的硬隔离需要未来 process-isolation contract。

稳定 mapping 为：

| 场景 | Outcome/code | Stage |
| --- | --- | --- |
| optional backend 缺失/不兼容 | unavailable/`backend_unavailable` | resolving |
| 无 built-in image capability | unavailable/`capability_unavailable` | resolving |
| unsupported source kind | failed/`source_type_unsupported` | sourcing |
| 错误 codec/profile、animation、unsupported mode/depth/transparency | failed/`unsupported_image_profile` (415) | decoding |
| malformed/truncated PNG 或非法 interpretation metadata | failed/`decode_error` | decoding |
| source/decode/metadata/pixel limit 或 decompression-bomb signal | failed/`resource_limit_exceeded` | observed stage |
| comparison work limit | failed/`compare_resource_limit` | comparing |
| source mutation 或 I/O error | 既有 stable code | observed stage |
| dimension/format/color descriptor mismatch | completed/different/fail | comparison fact 后 aggregating |
| 非预期 CLI exception | failed/`internal_error` | outer CLI boundary |

decode/comparison failure 不 fallback 到 binary、其他 Pillow decoder、resize、color conversion 或
其他 provider。`KeyboardInterrupt`、`SystemExit`、`MemoryError` 与 programming defect 保持既有
library boundary。

## Artifact 与人类评审

首切片返回 `artifacts=()`。tile change 与 metric 足以提供 machine evidence 和有界 terminal/JSON
展示，但不是 visual preview。既有 terminal renderer 只有通过 schema-v4 gate 后才能展示 descriptor/
tile coordinate 与 metric，且不能打开 source file。

Heatmap、overlay、thumbnail、before/after preview 和 self-contained image report 一起延后。
后继 RFC 必须定义：

- 显式 user request 与 confidentiality warning；
- host-owned `ArtifactSink`/root authority、atomic publication、byte/count/pixel limit、media allowlist、
  SHA-256 verification、cleanup 与 no-clobber rule；
- output 是否编码 source-derived pixel，以及 alpha/color 处理方式；
- deterministic heatmap scale、legend、dimension 与 algorithm identity；
- RFC 0001 `ArtifactRef` URI validation 与 RFC 0004 view-model 行为；
- renderer 只消费 validated ref 且不能任意 read/write，以及 HTML embed 不绕过 CSP/disclosure policy 的证明。

接受 image comparison 不授权 UI-U1/U2/U3。image evidence 可以输入未来 RFC 0004 修订，尤其是
side-by-side layout、synchronized zoom、pixel coordinate 与 artifact disclosure。

## Corpus、determinism 与 platform evidence

Fixture 由 repository-owned script 生成，或来自有记录的 public-domain/明确可再分发来源。每个
fixture 记录 source、generator version、license、dimension、mode、profile、expected sample matrix
与 SHA-256。测试 oracle 不能只来自 Pillow；小型 PNG 使用独立指定 expected sample 与 malformed
byte fixture。

接受矩阵包含：

- equal/different/minimal one-pixel content、单 pixel/channel change、edge tile、全部支持 mode、
  transparent RGB 与 descriptor mismatch；
- palette、低/16-bit、`tRNS`、APNG、错误 codec、corrupt chunk、truncation、oversized dimension/
  pixel、CRC/order/multiplicity fault、unknown critical chunk、精确 wire/decompressed/ICC limit
  boundary 与 decompression bomb；这些测试断言在 Pillow 前拒绝并产生 stable code；
- byte-different/pixel-equal pair，证明 binary/image 区别；
- 四个 digest fixture 的 byte-for-byte 验证、metric formula、tagged PSNR infinity、跨平台 8-ULP
  golden、integer/floating order、change invariant、item/payload truncation、精确 budget boundary 与
  重复运行 determinism；
- source mutation、no path reopen、backend missing/version mismatch、global decoder-registry tampering 与 no fallback；
- v1/v2/v3 fixture、v4 round trip/migration、unknown kind/version、public export、terminal safety、CLI
  alias/exit 与 package content；
- Linux/Python 3.12 上代表性 peak memory/runtime。声明额外平台前，需要对应 wheel/native-library
  与 deterministic-output evidence。

## 独立交付门禁与 commit

以下只是计划，不构成授权；门禁不会自动开始。

### P5-R：前驱与依赖重新验证

不产生 product commit。确认 P4-A1/schema v3 已合并，把其实际 model、serializer、migration、
renderer、test、docs 映射到 RFC 0006；重新检查 Pillow version/advisory/license/wheel/native
library。任何不一致都会阻塞 Phase 5，并返回本文。

### P5-A1：schema v4 image contract

1. `feat(core): add schema-v4 image comparison contracts`
2. `test(core): add schema-v4 compatibility and migration fixtures`

门禁：v1/v2/v3 fixture 保持稳定；全部 image spec/change/metric/provenance invariant 可 round-trip；
不存在 decoder、Pillow dependency、CLI route、image plugin、auto detection、artifact 或 UI。

### P5-A2：optional static PNG decoding

1. `build(image): add the reviewed optional Pillow backend`
2. `feat(image): add bounded static PNG decoding`
3. `test(image): add PNG profile and hostile-input coverage`

门禁：exact decoder allowlist、supported-profile check、limit、mutation、missing/incompatible backend、
advisory/license inventory、peak memory 与 unchanged default import/auto behavior 通过；不声称已有 comparison result。

### P5-A3：decoded-sample comparison 与 CLI

1. `feat(image): add exact decoded-sample comparison`
2. `feat(cli): add explicit image comparison commands`
3. `docs: document the first image comparison slice`

门禁：relation、change、metric、policy、provenance、truncation、safe rendering、alias/exit、determinism
与跨 schema 兼容性通过。Ruff format/lint、strict mypy、完整 pytest、build、wheel/sdist inspection、
link check、CI 与独立 RFC-to-code review 全部绿色。

### 后续独立 callback

- **P5-C：** 显式 color conversion 与 display-oriented transform；须先接受 ICC/Exif algorithm、dependency、
  deterministic provenance 与 compatibility。
- **P5-P：** perceptual comparison；只有在 schema successor 中接受完整 SSIM/threshold contract 后开始。
- **P5-F：** JPEG 与其他 still format；按 codec/native-library security/determinism surface 独立评审。
- **P5-M：** APNG/GIF/TIFF 等 frame/page sequence；须先定义 timeline、disposal/blend、duration、frame
  alignment、limit 与 change semantics。
- **P5-H：** heatmap/preview artifact；须先接受 artifact authority 与 RFC 0004 presentation contract。
- **P5-S：** SDK v2 image plugin 与 automatic image detection；只能通过 RFC 0005/0003 的后继 RFC。

## 被拒绝的替代方案

### 直接把 Pillow 默认 `Image.open()` 行为作为契约

拒绝原因：它 sniff 所有 registered codec，使用 mutable global registry，可能产生 backend-specific
mode 行为，也无法表达 Platydiff 的显式 resource/provenance/schema 保证。

### 自动把所有 input 转成 RGBA/sRGB

拒绝原因：palette expansion、color management、bit-depth reduction、orientation 与 alpha conversion
可能丢失或重新解释信息；这类 transform 需要显式 intent 与 provenance。

### 直接把 thumbnail/heatmap 放进 `DiffResult`

拒绝原因：当前 API 没有 artifact authority、output root 或安全 publication lifecycle；inline pixel
也会破坏 bounded/privacy contract。

### 把 SSIM 设为默认 relation

拒绝原因：SSIM 依赖完整指定的 viewing/sample profile 与 threshold，不是 pixel equality，也需要
独立 algorithm evidence。

## 后果

首个图片切片比用户想象中的“image diff”更窄，但其真值精确：byte identity 仍是 binary；
decoded-sample identity 可审计；且不暗示 perceptual similarity。限制 codec、mode、transform、
artifact 与 plugin 范围，使 security/compatibility claim 可测试。代价是 palette、JPEG、带方向
photo、color-managed、animated 与 visual-report workflow 要等待有测量证据且独立批准的后续门禁。

## 参考资料

- [RFC 0001：comparison outcome 与 diff result](0001-comparison-outcome-and-diff-result_zh.md)
- [RFC 0003：detection、resolution 与 exact binary comparison](0003-automatic-detection-capability-resolution-and-binary-comparison_zh.md)
- [RFC 0004：human review UI 与 renderer boundary](0004-human-review-ui-and-renderer-boundary_zh.md)
- [RFC 0005：第三方 plugin SDK 与 compatibility](0005-third-party-plugin-discovery-sdk-and-compatibility_zh.md)
- [RFC 0006：structured data comparison](0006-structured-data-comparison_zh.md)
- [W3C PNG Specification, Third Edition](https://www.w3.org/TR/png-3/)
- [Pillow 12.3.0 project metadata](https://pypi.org/project/pillow/)
- [Pillow image-open contract](https://pillow.readthedocs.io/en/stable/reference/Image.html)
- [Pillow security guidance](https://pillow.readthedocs.io/en/stable/handbook/security.html)
- [Pillow image concepts](https://pillow.readthedocs.io/en/stable/handbook/concepts.html)
- [Pillow image-format documentation](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
- [Pillow security advisories](https://github.com/python-pillow/Pillow/security/advisories)
- [Pillow MIT-CMU license](https://github.com/python-pillow/Pillow/blob/main/LICENSE)
- [ICC.1:2022 color-management specification](https://www.color.org/specification/ICC.1-2022-05.pdf)
- [Wang 等，《Image quality assessment: from error visibility to structural similarity》](https://www.colorado.edu/lab/live/publications/zwang_ssim_ieeeip2004.pdf)
