# RFC 0006：结构化数据比较

[English documentation](0006-structured-data-comparison.md)

- Status: Proposed
- Date: 2026-09-10
- Owners: Platydiff maintainers
- Implementation owner: 尚未指派，等待接受 RFC 并另行授权

## 摘要与授权边界

本 RFC 提议 Phase 4 的 JSON、受约束 YAML 1.2 profile、分隔符表格与稠密数组
契约，并定义 schema 演进、相等性、路径、对齐、限制、失败与交付门禁。它不授权
实现、依赖变更、新 plugin SDK、结构化数据自动探测或 UI 工作。每个实现门禁都要
基于更新后的 `main` 单独派发；后续门禁不会自动开始。

## 证据账本

| `main` `7346d5e` 的当前证据 | Phase 4 约束 |
| --- | --- |
| outcome schema v1 围绕 text/binary spec 与 change 冻结。 | 新 public spec 与内建 change kind 需要新 outcome schema。 |
| schema v2 在保留相同模态表面的同时增加 provider facts。 | schema v3 应是 v2 的加法式语义后继。 |
| auto spec、candidate 与 detector evidence 对 text/binary 封闭。 | 既有 auto 行为保持不变；Phase 4 只能显式选择。 |
| SDK v1.1 comparator 与 detector 对 text/binary 封闭。 | Phase 4 仅限 built-in；新 plugin modality 需要 SDK v2 与后继 RFC。 |
| snapshot 已为 path/bytes/text 管理有界重放、hash、突变检查与安全 label。 | JSON、YAML、table 复用这些 source type 与 host ownership。 |
| `ChangeSet` 已区分 complete、truncated 与 partial。 | Phase 4 在裁剪明细前完成比较，且绝不产出 partial。 |
| renderer 消费 validated outcome，RFC 0004 又将 UI 工作独立隔离。 | 新 change shape 需要有界展示，而不是 renderer 自有语义或 UI 授权。 |
| runtime dependency 当前为空。 | JSON/table 使用标准库；YAML 是可选、惰性加载、单独评审的依赖。 |

此账本记录已实现约束，不授权修改这些约束。

## 目标与非目标

目标包括：确定性的显式 JSON/YAML、table 与 dense-array 比较；可见的 normalization
与 alignment；精确的特殊值语义；有界工作和返回明细；稳定的 schema-v3 change 与
provenance；以及证明既有 text、binary、auto、plugin 行为不变的测试。

Phase 4 不包含 structured auto detection、TOML/XML/JSON5、JSON comment、YAML merge
语义/custom tag/object constructor、schema language、模糊或推断式 alignment、streaming/
sparse/ragged/masked/decimal/complex/datetime/categorical/unit-bearing array、NumPy、pandas、
xarray、Arrow、Parquet、spreadsheet、压缩容器、URL、directory、stdin、statistical
equivalence、ULP policy、patch、artifact、新 plugin modality，以及 HTML/TUI/desktop/
local-web UI 实现。

## 需要人类批准的决策

| ID | 提议决策 | 需要修订的替代方案 |
| --- | --- | --- |
| S1 | 每个 Phase 4 outcome 使用 schema v3；保留 v1/v2 reader 与 writer。 | 原地扩展 v2，使旧 v2 reader 错误解释变化后的封闭联合。 |
| S2 | 既有 auto 保持 text/binary-only，直至后继 detection RFC；Phase 4 type 必须显式选择。 | 先定义 structured ambiguity、precedence、probing 与 attribution。 |
| S3 | Phase 4 comparator 为 built-in；SDK v1.1 保持 text/binary-only。 | 在 Phase 4 实现前接受 SDK v2。 |
| S4 | JSON 默认语义值相等：忽略 object order 与 number spelling，array order 有意义，重复 decoded key 失败。 | 默认采用 lexical JSON 或 order-sensitive object。 |
| S5 | YAML 使用受约束 `yaml12_core_safe` profile 和可选 `yaml` extra，不回退 YAML 1.1。 | 更广泛 YAML 语义或 core 必需依赖。 |
| S6 | table 要求显式 dialect/header policy；没有 column schema 时 cell 保持 string。 | 推断 dialect、header、key、missing token 或 dtype。 |
| S7 | table 默认 positional alignment；keyed alignment 必须显式且拒绝 missing/duplicate key。 | 推断 key 或按出现次序配对重复项。 |
| S8 | 首个 array 门禁只提供 Python API 的复制后 immutable source；生态 adapter 属于后续门禁。 | 现在加入 CLI 文件格式或生态依赖。 |
| S9 | tolerance 为 `abs(after-before) <= atol + rtol * abs(before)`；NaN 默认不等，同号无穷与 signed zero 相等。 | 对称 tolerance 或不同特殊值默认值。 |
| S10 | Phase 4 不产出 partial；完成前触限失败，只有完成后的明细可 truncated。 | 从未完成工作返回 relation。 |
| S11 | P4-A1、P4-A2、P4-B1、P4-B2 分别授权。 | 把 Phase 4 作为单一批次交付。 |
| S12 | Phase 4 不产出 artifact；renderer 只展示 validated bounded facts。 | 现在加入 patch、preview、downloadable value 或 report。 |

在接受的决策写回本文前，本 RFC 保持 `Proposed`，且不授权任何实现门禁。

## Schema v3 兼容性契约

schema v3 在保留 RFC 0001 outcome 和 RFC 0005 provider field 的同时增加 public spec
与 built-in change variant：

```python
CompareSpecV3 = (
    AutoCompareSpec | TextCompareSpec | BinaryCompareSpec
    | JsonCompareSpec | YamlCompareSpec | TableCompareSpec | ArrayCompareSpec
)
ChangeV3 = (
    TextHunk | BinarySpan | StructuredChange
    | TableChange | ArrayChange | ExtensionChange
)
```

- 既有三参数 text、binary、auto 调用保持 schema v1。
- 既有 `PluginHost` text/binary 调用保持 schema v2。
- 每个 Phase 4 spec 都产出 schema v3，包括 resolution 前失败。
- v3 reader 接受 v1/v2/v3；旧 reader 继续拒绝未知版本。
- 显式 v1/v2-to-v3 upgrader 保留全部 facts，仅加入有文档的中性默认值。不自动
  downgrade；只有 legacy-only v3 outcome 可在验证后由显式无损 helper 降级。
- 未知 built-in spec/change kind 仍是错误；未知 namespaced extension change 保持
  RFC 0001 行为。

只有另行授权的 P4-A1 实现合并后，schema-v3 field 与 fixture 才成为 public。

### 兼容性矩阵

| producer/path | schema | modality | plugin 参与 | 必需行为 |
| --- | --- | --- | --- | --- |
| 既有 `compare()` 与默认 CLI | v1 | text、binary、解析到二者的 auto | 无 | 既有 byte-stable fixture 继续有效。 |
| 既有显式 `PluginHost` | v2 | text、binary、解析到二者的 auto | SDK v1.1 | 既有 v2 fixture 与 receipt 继续有效。 |
| 提议的 Phase 4 built-in path | v3 | 显式 json/yaml/table/array | 无 | v3 验证新 variant 与全部继承 invariant。 |
| 提议的 `PluginHost` + Phase 4 spec | 无 | 不支持 | 执行前拒绝 | Python 返回 resolving-stage unavailable；CLI 的 plugin flag + Phase 4 type 为 usage exit 2。 |
| 对 structured-looking bytes 使用既有 auto | v1 | 仅 text/binary | 仅既有规则 | result 与 detection evidence 不变。 |
| 未来 SDK v2 或 structured auto | 未指定 | 未指定 | 未指定 | 需要后继 RFC。 |

## 通用结构化值契约

JSON 与 YAML decode 为 private immutable tree：

```text
null | boolean | integer | decimal | string | sequence | mapping
```

parser-specific object 不进入 result。mapping key 必须是唯一 Unicode scalar string；
其他 key type 失败。path 是 canonical RFC 6901 JSON Pointer：root 为空，`~` 转为 `~0`，
`/` 转为 `~1`，array index 是除 `0` 外无前导零的十进制数。

不执行 Unicode normalization、case folding、string whitespace change 或 scalar coercion。
mapping order 不是比较维度；traversal 按 Unicode code point 排序 decoded key。sequence
保持 positional。

integer 在 digit limit 内为任意精度。decimal number 保存 sign、coefficient digit 与 base-10
exponent，不使用 binary float。value mode 去除无意义的零，因此 `1`、`1.0`、`1e0` 相等，
正负零相等。仅 JSON 支持的 lexical mode 比较已验证的 source number token，并记录该
normalization choice。

```python
class StructuredChange:
    kind: Literal["structured_change"]
    operation: Literal["add", "remove", "replace"]
    path: str
    before_type: StructuredType | None
    after_type: StructuredType | None
    before_digest: str | None
    after_digest: str | None
```

digest 是 schema-v3 canonical typed value 的 SHA-256，不泄露 payload。add 没有 before
facts，remove 没有 after facts，replace 两者都有。type change 是 replace；不推断 move。
change 是观察结果，不是 patch。确定性 depth-first pre-order 使用排序后的 mapping key 与
递增 sequence index。整个 added/removed subtree 在最高 pointer 产生一个 change。完整 count
已知后才应用 item/payload truncation。
pointer 作为比较坐标必然暴露有界 decoded mapping-key name；它不暴露 scalar value，且
renderer 必须把它作为 untrusted text 转义。

## JSON 契约

```python
class JsonCompareSpec:
    kind: Literal["json"] = "json"
    encoding: Literal["utf-8", "utf-8-sig"] = "utf-8"
    number_mode: Literal["value", "lexical"] = "value"
    limits: StructuredResourceLimits = StructuredResourceLimits()
```

只接受一个 RFC 8259 value，之后仅可有 JSON whitespace。UTF-8 strict；仅显式
`utf-8-sig` 移除 BOM。comment、trailing comma、NaN、infinity、unpaired surrogate escape
与 escape decoding 后 duplicate object key 都失败。duplicate detection 在 host mapping
构造前完成。

忽略 object order 与 string escape spelling；array order 有意义。value/lexical number
mode 遵循通用模型。默认 policy 仍是 equal/pass、different/fail。畸形 syntax 产生
failed/decode_error；越过配置边界产生 failed/resource_limit_exceeded。

## YAML 契约与依赖门禁

```python
class YamlCompareSpec:
    kind: Literal["yaml"] = "yaml"
    profile: Literal["yaml12_core_safe"] = "yaml12_core_safe"
    encoding: Literal["utf-8", "utf-8-sig"] = "utf-8"
    limits: YamlResourceLimits = YamlResourceLimits()
```

该 profile 是带有刻意限制的 YAML 1.2.2 Core：

- 恰好一个 document；empty 与 multi-document stream 失败；
- key 解析为唯一 string；
- 只有 null、boolean、integer、finite decimal、string、sequence、mapping value 进入 private tree；
- 七种允许 Core value type 以外的 tag、object constructor、merge key (`<<`)、timestamp/
  binary tag、set、
  ordered map、pair 失败；
- alias 可表达无环 graph；cycle 失败，并分别限制 alias、depth、composed/expanded-node count；
- 只允许兼容的 `%YAML 1.2` directive；以及
- comment、scalar/collection style、key order、anchor name 与 tag spelling 不是比较维度。

不回退到 YAML 1.1 resolution：`yes`、`no`、`on`、`off` 是 string，`true`、`false`
是 boolean。即使更广的 Core schema 可识别 non-finite YAML float，本 safe profile 仍拒绝。

候选 backend 是可选 `yaml` extra 中的 `ruamel.yaml`，实现时 pin 到已评审范围。host 使用
pure-Python safe YAML 1.2 event path，而不是 eager object construction；failure 后重建 parser，
验证 tag/event，并在分配下一个 host node 前执行 counter 以构造自身 tree。只在显式 YAML
时 import。backend 缺失/不兼容返回
resolving-stage unavailable/backend_unavailable，绝不回退 text、JSON 或 YAML 1.1。

依赖门禁记录 version、MIT license、Python/platform support、source/wheel size、transitive
dependency、advisory，以及 PyYAML YAML 1.1 resolver 不等价的原因。接受前需要 hostile alias、
tag、duplicate-key、depth 与 multi-doc test。安装 extra 不能改变 default/auto 行为。

## 分隔符表格契约

```python
class TableCompareSpec:
    kind: Literal["table"] = "table"
    dialect: Literal["csv", "tsv"]
    header: Literal["first_row", "none"] = "first_row"
    alignment: Literal["position", "key"] = "position"
    key_columns: tuple[str, ...] = ()
    column_order: Literal["exact", "by_name"] = "exact"
    columns: tuple[ColumnSpec, ...] = ()
    limits: TableResourceLimits = TableResourceLimits()

class ColumnSpec:
    name: str
    dtype: Literal["string", "integer", "float64", "boolean"]
    missing_tokens: tuple[str, ...] = ()
    numeric: NumericPolicy | None = None
```

CSV 使用 Python `csv` 的 `excel` 设置与 comma delimiter；TSV 替换为 tab。两者都采用
double quote、doubled-quote escaping、strict parsing 与 embedded newline。禁止 sniffing。
encoding 为 strict UTF-8，可显式选择 `utf-8-sig`。

`first_row` 要求非空且 name 唯一的 header。`none` 从第一行分配 `column_1`、
`column_2`……；零行意味着零列。所有行必须具有已建立的宽度。empty string 是 value。
missing 只来自 `ColumnSpec` 显式声明的精确 token，并在 typed parsing 前匹配。

没有完整 column schema 时，所有 cell 都是 string。完整 schema 对每列恰好列出一次，type
为 `string`、`integer`、`float64` 或 `boolean`，并声明 missing token。不做推断。
integer 为无 separator 的 base-10；float 接受 finite decimal/scientific 与精确 `nan`、
`inf`、`-inf`；boolean 仅精确 `true`/`false`。typed parse failure 是 decode error。
`numeric` 对 `float64` 必填，对其他 dtype 禁止。column name 与 missing token 是唯一、
case-sensitive 的 Unicode scalar string。CSV record terminator 与 quoting 是可见且被记录的
decoding transformation，但不是 table value 的比较维度。

positional alignment 比较 row/column position。key alignment 要求 header、至少一个
string/integer non-missing key column，且每侧 key 完整唯一。missing/duplicate key 在 aligning
失败且绝不配对。matched、removed、added row 各自按 canonical key 排序。exact column order
把 reorder 视为 schema difference；by-name 按 canonical name 对齐唯一 name。

```python
class TableChange:
    kind: Literal["table_change"]
    operation: Literal[
        "column_add", "column_remove", "column_reorder",
        "row_add", "row_remove", "cell_replace"
    ]
    row: int | None
    key_digest: str | None
    column: str | None
    before_digest: str | None
    after_digest: str | None
```

row 是不含 header 的一基 data row。key/cell value 只用 canonical typed SHA-256 digest
表示。schema change 先于 row change，随后是 cell change；组内使用确定性 alignment order。

## 稠密数组契约

第一个 array 门禁仅供 API 使用：

```python
class ArraySource:
    shape: tuple[int, ...]
    dtype: Literal["bool", "int64", "uint64", "float64"]
    values: tuple[bool | int | float, ...]
    label: str

class ArrayCompareSpec:
    kind: Literal["array"] = "array"
    alignment: Literal["position"] = "position"
    numeric: NumericPolicy = NumericPolicy()
    limits: ArrayResourceLimits = ArrayResourceLimits()
```

construction 验证并复制 value。row-major C order 是规范，length 等于 checked shape product。
允许 zero-length dimension 与 rank-zero scalar。boolean 不是 integer；integer 必须符合声明
dtype；float value 转换一次为 IEEE 754 binary64。转换与 source kind 被记录。禁止 object
coercion、construction 后 iteration、buffer aliasing 与 mutation。

shape/dtype 必须匹配。不做 broadcast、squeeze、reshape、transpose、relabel、跨 dtype cast
或 coordinate alignment。shape/dtype mismatch 是带一个 schema-level change 的 completed
difference，而不是 alignment failure。

```python
class ArrayChange:
    kind: Literal["array_change"]
    operation: Literal["shape_replace", "dtype_replace", "element_replace"]
    index: tuple[int, ...] | None
    before_digest: str
    after_digest: str
    absolute_error: MetricNumber | None
    relative_error: MetricNumber | None
```

element change 按 row-major index order，使用 canonical typed scalar digest。仅 finite numeric
pair 有 error。单独选择 file representation 前没有 array CLI。生态 adapter 需要 dependency、
ownership、dtype、coordinate、missing-value 与 license review。

## 数值与 missing-value 语义

```python
class NumericPolicy:
    atol: float = 0.0
    rtol: float = 0.0
    relative_reference: Literal["before"] = "before"
    nan_equal: bool = False
    signed_zero_equal: bool = True
```

finite value 仅在下式成立时相等：

```text
abs(after - before) <= atol + rtol * abs(before)
```

tolerance 是 finite、non-negative binary64，边界为 inclusive。integer/boolean 不使用 tolerance。
同号 infinity 相等，其他 infinite pair 不同。NaN 只有 opt-in 后才与 NaN 相等。signed zero
默认相等；关闭时先按 sign bit 判不同，再应用 tolerance。

missing 是独立 tagged state：missing 与 missing 相等，与所有 present value 不同。key 不能
missing；首个 array gate 没有 missing state。decimal、complex、datetime、unit、ULP、symmetric
tolerance 与 statistical equivalence 延后。

metric 报告 compared/equal/changed、missing、NaN、infinity 与 finite-numeric pair count。
numeric comparison 报告 finite unequal pair 的 maximum absolute/relative error；空 population
使用显式 unavailable metric。不定义 mean，避免未指定 floating-point accumulation order。
tolerance 因为是显式 intent，所以改变 relation；renderer 不得应用或重新解释。strict default
policy 仍为 equal/pass 与 different/fail。

## 资源与失败

序列化 limit field name 由以下概念 record 固定；YAML 扩展而不重新解释通用 structured limit：

```python
class StructuredResourceLimits:
    max_input_bytes: int = 16 * 1024 * 1024
    max_scalar_bytes: int = 1024 * 1024
    max_depth: int = 256
    max_nodes: int = 1_000_000
    max_number_digits: int = 10_000
    max_abs_exponent: int = 1_000_000
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

class YamlResourceLimits(StructuredResourceLimits):
    max_aliases: int = 10_000
    max_expanded_nodes: int = 1_000_000

class TableResourceLimits:
    max_input_bytes: int = 16 * 1024 * 1024
    max_cell_bytes: int = 1024 * 1024
    max_rows: int = 200_000
    max_columns: int = 10_000
    max_cells: int = 1_000_000
    max_number_digits: int = 10_000
    max_abs_exponent: int = 1_000_000
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024

class ArrayResourceLimits:
    max_rank: int = 32
    max_elements: int = 2_000_000
    max_compare_work: int = 5_000_000
    max_change_items: int = 10_000
    max_change_payload_bytes: int = 4 * 1024 * 1024
```

| 默认限制 | JSON/YAML | Table | Array |
| --- | ---: | ---: | ---: |
| 每个 serialized input bytes | 16 MiB | 16 MiB | n/a |
| 每个 scalar/cell 的 UTF-8 bytes | 1 MiB | 1 MiB | n/a |
| nesting depth/rank | 256 | n/a | 32 |
| node/element | 1,000,000 | 1,000,000 cells | 2,000,000 elements |
| row/column | n/a | 200,000 / 10,000 | n/a |
| number digit / absolute exponent | 10,000 / 1,000,000 | 10,000 / 1,000,000 | fixed dtype |
| YAML alias / expanded node | 10,000 / 1,000,000 | n/a | n/a |
| compare work unit | 5,000,000 | 5,000,000 | 5,000,000 |
| returned change / payload | 10,000 / 4 MiB | 10,000 / 4 MiB | 10,000 / 4 MiB |

dimension product 在 allocation 前使用 checked arithmetic。decoder 在构造 node、row、cell
或 expanded alias 前增加 counter。comparator work unit 由 implementation 分别记录，绝不使用
wall-clock time。

触限使用既有 `resource_limit_exceeded` 或 `compare_resource_limit` 与 observed stage。
syntax/typed-cell failure 使用 `decode_error`；YAML backend 缺失是 unavailable；unsupported source
使用 `source_type_unsupported`。duplicate/missing table key 使用新增稳定 code
`alignment_failed`、HTTP-style status 422 与 aligning stage。library 不吞掉 unknown exception。

完整 semantic comparison 与 total change count 完成前不返回 relation。因此 Phase 4 只产生
complete/truncated change set；truncation 不改变 relation、verdict、fidelity、metric 或 total。
不允许 fallback，所以 fidelity 为 full。artifact 为空。diagnostic/provenance 不含 raw value、key、
cell、traceback、absolute/environment path 或无界 backend message。structured path 与 table column
name 是 change 中的有界比较坐标，并始终作为 untrusted text 处理。

## CLI 与 public API 边界

```text
platydiff json BEFORE AFTER
platydiff compare --type json BEFORE AFTER
platydiff yaml BEFORE AFTER
platydiff compare --type yaml BEFORE AFTER
platydiff table --dialect csv BEFORE AFTER
platydiff compare --type table --dialect csv BEFORE AFTER
```

alias 共用一条 path。array 仅供 Python 使用。既有 renderer 在自身门禁后接受 validated v3
outcome。exit code 保持 0 equal/pass、1 completed non-pass、2 usage、3 unavailable/failed/
renderer failure。

structured command 在 discovery 前由 argparse 以 exit 2 拒绝 plugin/detector/comparator flag。
它们不接受 stdin、directory、URL、configuration、推断 type/dialect 或 artifact output。
top-level export 只增加已接受的 spec、source、policy、outcome 与 enum。parser、IR、canonical
encoder、alignment index、counter、registry 保持 private。既有 `compare(before, after, spec)`
signature 不变。

## 交付门禁、commit 与测试

以下内容是计划，不构成实现授权。

### P4-A1：schema v3 与 JSON

1. `feat(core): add schema-v3 structured comparison contracts`
2. `feat(json): add bounded semantic JSON comparison`
3. `feat(cli): add explicit JSON comparison commands`
4. `docs: document schema v3 and JSON comparison`

测试覆盖 v1/v2 stability/migration、strict v3 round trip、全部 model invariant、duplicate key、
number mode、pointer、ordering、所有 limit、truncation、source mutation、CLI alias/exit 与
randomized tree oracle。

### P4-A2：YAML backend

1. `build(yaml): add the reviewed optional YAML backend`
2. `feat(yaml): add the bounded YAML 1.2 safe profile`
3. `feat(cli): add explicit YAML comparison commands`
4. `docs: document YAML semantics and dependency provenance`

测试覆盖 missing backend、pure safe loading、YAML 1.1 ambiguity token、tag、merge、duplicate、
alias、cycle、multi-doc、parser recreation、hostile depth/expansion、dependency inventory，以及
既有 auto fixture 不变。

### P4-B1：分隔符表格

1. `feat(table): add typed delimited-table contracts`
2. `feat(table): add bounded positional and keyed comparison`
3. `feat(cli): add explicit table comparison commands`
4. `docs: document table schemas alignment and numeric policy`

测试覆盖 malformed quoting、embedded newline、empty/header-only/ragged input、duplicate header/key、
每种 dtype/missing token、alignment、column order、tolerance boundary、NaN/Inf/signed zero、limit、
determinism 与 exit。

### P4-B2：稠密数组

1. `feat(array): add immutable dense-array sources and contracts`
2. `feat(array): add deterministic dense-array comparison`
3. `docs: document array dtype shape and numeric semantics`

测试覆盖 scalar/empty/multidimensional shape、checked product、copy/mutation isolation、dtype bound、
row-major index、schema change、numeric special case/boundary、deterministic metric、truncation 与 work limit。

每个门禁运行 Ruff format/lint、strict mypy、完整 pytest、build、wheel/sdist inspection 与 docs/link
check。public model 增加 serialization/migration fixture；dependency gate 增加 license/package evidence。

## 后续阶段回调

structured auto detection 必须先在 RFC 0003 后继 RFC 中定义 probe budget、JSON/YAML/text
ambiguity、pair selection、ordering、override 与 attribution。新 plugin modality 必须在 RFC 0005
后继 RFC 中定义 SDK v2 ownership、source view、canonicalization、validation、receipt 与 version。

生态/sparse/unit-aware data 必须定义 ownership、dtype、mask、coordinate、chunk、endianness、
memory mapping、decompression、dependency、license 与 platform。statistical 工作必须定义 hypothesis、
correction、sample size、effect size、confidence、seed、aggregation 与 verdict impact。更丰富的
presentation 回到 RFC 0004；它可展示 validated fact，但不能读取 value 或执行比较。

## 参考资料

- [RFC 8259：JSON](https://www.rfc-editor.org/rfc/rfc8259)
- [RFC 6901：JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901)
- [YAML 1.2.2 specification](https://yaml.org/spec/1.2.2/)
- [YAML 1.2.2 changes](https://yaml.org/spec/1.2.2/ext/changes/)
- [Python `csv` documentation](https://docs.python.org/3/library/csv.html)
- [`ruamel.yaml` metadata](https://pypi.org/project/ruamel.yaml/)
- [`ruamel.yaml` safe/pure loader](https://yaml.dev/doc/ruamel.yaml/basicuse/)
