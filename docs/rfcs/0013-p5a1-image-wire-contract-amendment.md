# RFC 0013: P5-A1 Image Wire-Contract Amendment

[Chinese documentation](0013-p5a1-image-wire-contract-amendment_zh.md)

- Status: Accepted
- Date: 2026-09-10
- Accepted: 2026-09-11
- Owners: Platydiff maintainers
- Amends: [RFC 0007](0007-image-comparison.md)
- Predecessor: [RFC 0010](0010-schema-predecessor-and-phase6-contract-amendment.md)
- Implementation authorization: none

## Summary

This accepted amendment closes the wire-level decisions needed before P5-A1
can be dispatched. It does not change the accepted I1-I16 image semantics in
RFC 0007. It freezes the P5-A1 boundary, public enum types, five image
transformation payloads, schema-only provenance specimens, the
`unsupported_image_profile` problem, terminal presentation, downgrade rules,
and compatibility acceptance criteria.

The current evidence baseline is `origin/main` `b84603f` on 2026-09-11. PR #20
merged the independently reviewed P4-C1 implementation and its frozen v1-v3
compatibility fixtures, so the schema predecessor gate is satisfied. Acceptance
of this RFC still does not authorize or dispatch P5-A1 implementation.

## Authorization boundary

P5-A1 is strictly contract-only. If a human separately authorizes its
implementation, P5-A1 may add only:

- schema-v4 public models, validation, serialization, and explicit migration
  helpers;
- schema-v4 canonical compatibility fixtures constructed directly from public
  models, plus round-trip, rejection, export, and predecessor-stability tests;
- bounded terminal rendering of an already validated schema-v4 outcome; and
- synchronized contract documentation.

P5-A1 must not add an image decoder, scanner, comparator implementation,
capability registration, Pillow or another backend, an `image` dependency
extra, an image CLI command or option, automatic detection, plugin image
support, source-derived artifacts, previews, heatmaps, HTML/TUI/desktop UI, or
image corpus files. `compare(..., ImageCompareSpec(...))` remains unavailable
because no runtime capability is registered. A canonical `CompletedOutcomeV4`
is a schema specimen constructed by a test; it is not evidence that a PNG was
decoded or compared.

The actual P4-C1 implementation and its v1-v3 compatibility fixtures are now
merged to `main` and have been independently verified against the types named
below. This clears only the predecessor condition. P5-A1 remains unimplemented
and must not start without a separate human dispatch; any later predecessor
mismatch returns to this RFC rather than being repaired opportunistically in
code.

## Accepted decisions

| ID | Accepted decision |
| --- | --- |
| P5A1-1 | Make P5-A1 strictly contract-only under the boundary above. |
| P5A1-2 | Use named `StrEnum` types for reusable public image choices; retain `Literal` only for discriminators and the invariant tile-size constant. |
| P5A1-3 | Freeze the five transformation parameter objects exactly as specified below; reject missing and unknown keys. |
| P5A1-4 | Close the complete schema-v4 type/export lattice and treat completed/failed fixtures as direct contract specimens with exact built-in attempt/provenance bindings, null backend identity, empty backend-component evidence, and no Pillow claim. |
| P5A1-5 | Add `unsupported_image_profile` only to the schema-v4 failed-problem allowlist, with a closed details object; v1-v3 readers continue to reject it. |
| P5A1-6 | Add only the bounded terminal projection below and permit downgrade only when every fact is losslessly representable in the target predecessor. |

The user approved P5A1-1 through P5A1-6 and the complete closure rules in this
RFC on 2026-09-11. This approval accepts the contract but grants no
implementation authority.

## Public Python and wire enums

Reusable choices in public dataclass fields use these named `StrEnum` classes.
Member names are Python API; values are serialized wire strings.

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

`ImageCompareSpec.kind` remains `Literal["image"]`,
`ImageChange.kind` remains `Literal["image_change"]`, and
`ImageCompareSpec.tile_size` remains `Literal[64]`. Those values are closed
discriminators or invariants, not extensible choices. `ImageChange.component`
is `ImageChangeComponent | None`; the other accepted image-spec fields use the
corresponding enum above.

Transformation parameters remain validated JSON objects rather than new public
Python model exports. Their enum-valued fields use the same wire strings, but
do not add another top-level API surface.

## Closed JSON rules

Every object specified in this RFC is closed: every listed key is required and
no additional key is accepted. JSON integers reject booleans. Counts and sizes
are non-negative exact integers. Width and height are positive exact integers.
SHA-256 values are 64 lowercase hexadecimal characters. Arrays are ordered,
have no duplicates where stated, and retain the displayed capitalization.

Role objects require exactly the `before` and `after` members; their semantic
meaning comes from the key, not object-member order. Pretty examples are
semantic illustrations and do not assert canonical writer order. The
canonical writer and order-insensitive reader rules are frozen below.

### Shared decode facts

`ImageDecodeFacts` has exactly these keys and types:

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

- `mode` is an `ImageSampleMode` value.
- `frame_count` is exactly `1` for this profile.
- `bit_depth` is exactly `8`.
- `color_type` is respectively `0`, `4`, `2`, or `6` for `L`, `LA`, `RGB`, or
  `RGBA`; any other pairing is invalid.
- `interlace_method` is `0` or `1`.
- `pixels == width * height` and `decoded_bytes == pixels * channel_count`,
  using the mode's `1`, `2`, `3`, or `4` channels.

The six resource values are observed facts. Their configured limits are
recorded separately as `ResourceUsage` entries and are not duplicated here.

### 1. `image.png.decode`

Stage is exactly `decoding`. Parameters are:

```json
{
  "profile": "static_png_8bit_v1",
  "before": { "...": "ImageDecodeFacts" },
  "after": { "...": "ImageDecodeFacts" }
}
```

`profile` is an `ImageDecodeProfile` value. Backend, backend version, provider,
and implementation version are forbidden in this object. Runtime backend
identity belongs only in the selected capability attempt; comparator and
algorithm identity belong only in comparison provenance.

### 2. `image.orientation.stored`

Stage is exactly `normalizing`. Parameters are:

```json
{
  "policy": "stored",
  "before": { "exif_present": false, "exif_wire_bytes": 0 },
  "after": { "exif_present": false, "exif_wire_bytes": 0 }
}
```

`policy` is an `ImageOrientationPolicy` value. `exif_present` is boolean and
`exif_wire_bytes` is a non-negative exact integer. When `exif_present` is
false, its byte count is zero; when true, the count is positive. No EXIF tag or
payload is allowed.

### 3. `image.color.native_exact`

Stage is exactly `normalizing`. Parameters are:

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

`policy` is an `ImageColorProfilePolicy` value. `present_chunks` is the unique
subsequence, in this fixed order, of `cHRM`, `gAMA`, `iCCP`, `sBIT`, `sRGB`,
`cICP`, `mDCV`, and `cLLI`. `description_digest` is the RFC 0007 canonical
color-description digest. No raw or decoded profile value is allowed.

### 4. `image.alpha.straight`

Stage is exactly `normalizing`. Parameters are:

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

`policy` is an `ImageAlphaPolicy` value. Mode, bands, and alpha are closed to
these mappings: `L -> (["L"], false)`, `LA -> (["L", "A"], true)`,
`RGB -> (["R", "G", "B"], false)`, and
`RGBA -> (["R", "G", "B", "A"], true)`. No premultiplication or compositing
fact exists in P5-A1.

### 5. `image.coordinates.exact`

Stage is exactly `aligning`. Parameters are:

```json
{
  "origin": "top_left",
  "x_direction": "right",
  "y_direction": "down",
  "dimensions_policy": "exact_dimensions",
  "tile_size": 64
}
```

Every displayed value is exact. `dimensions_policy` is an
`ImageAlignmentPolicy` value and `tile_size` is exactly `64`. This record does
not claim resize, crop, registration, or coordinate conversion.

### Transformation sequence

A schema-v4 completed image specimen contains exactly one of each record, in
the order above. No other built-in image transformation ID is accepted. A
failed specimen contains only records for stages that completed before the
failed stage; an `unsupported_image_profile` failure at `decoding` therefore
contains no image transformation record.

## Complete schema-v4 type lattice

P5-A1 adds this complete, closed public lattice. Names not shown are not v4
public contracts:

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

`CapabilityAttemptV4.__post_init__()` first calls the inherited
`CapabilityAttemptV2.__post_init__()` and then validates the v4 component
field. `ExecutionRecordV4` retains every `ExecutionRecordV2` field and invariant
unchanged—timestamps, durations, contiguous stages, diagnostics, detection,
last completed stage, and `plugin_host`—but requires every attempt to be an
exact `CapabilityAttemptV4`. `ComparisonProvenanceV4` retains every
`ComparisonProvenanceV2` field and provider invariant unchanged; its distinct
runtime type prevents a v3 provenance object from being placed directly in a
v4 completed outcome. `ChangeSetV4.__post_init__()` first calls the inherited
`ChangeSet.__post_init__()` and then validates the v4 item union and ordering.
`DiffResultV4.__post_init__()` likewise calls the inherited result validation,
then requires exact `ChangeSetV4` and `ComparisonProvenanceV4` instances and
applies the image context bindings below. `CompletedOutcomeV4` requires an
exact `DiffResultV4`; a predecessor `DiffResult` cannot be inserted directly.
Before that subclass is enabled, P5-A1 adds the exact RFC 0007 image metric
sequence to the shared spec-kind metric-order table used by the inherited
normalizer. Existing text/binary/structured entries and output order remain
unchanged; image metrics cannot fall through to generic lexical sorting.

`ChangeSetV4` permits either a predecessor-only sequence, for a lossless
upgraded v1-v3 result, or an image-only sequence. If any item is an exact
`ImageChange`, every item must be an exact `ImageChange`; image changes never
mix with predecessor built-ins or `ExtensionChange`. Descriptor changes are
unique and ordered `dimensions`, `pixel_format`, `color_description`. Tile
changes are strictly ordered by `(y, x)`, have unique origins, do not overlap,
and never mix with descriptor changes. An empty sequence is valid and its
context is decided by the spec.

`DiffResultV4` provides that context. With `spec.kind="image"`, all retained
items must be image changes, `artifacts=()`, provenance must use the exact
image comparator/algorithm bindings, and all RFC 0007 plus this amendment's
metric, evaluation, descriptor, geometry, digest-syntax, truncation, and
resource invariants apply. With a predecessor spec kind, no image change or
`image`/`image.*` identifier may occur and every predecessor schema-v3 result
invariant remains in force. An image spec in a plain `DiffResult`, an image
change in a plain `ChangeSet`, a predecessor result directly inside
`CompletedOutcomeV4`, or a v4 result directly inside a v1-v3 outcome is invalid.

The private serializer boundary is version-explicit; it never infers schema
from an item:

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

The outer outcome encoder/decoder always passes the envelope version through
execution, attempt, result, and change serialization. Schema v1 requires exact
`ExecutionRecord`/`CapabilityAttempt`; schema v2 and v3 require exact
`ExecutionRecordV2`/`CapabilityAttemptV2`; schema v4 requires exact
`ExecutionRecordV4`/`CapabilityAttemptV4`. Consequently the existing
`isinstance(attempt, CapabilityAttemptV2)` writer branch is not a valid v4
dispatch: it must be replaced by the explicit versioned helper above. A v4
reader requires `backend_components` on every attempt, constructs the component
objects before the attempt, and constructs v4 execution/set/result types even
for a legacy-only upgraded payload. V1-v3 readers reject the additional attempt
member and `image_change`; v1-v3 encoders reject v4 execution/attempt/set/result
instances and image specs before serialization. The v4 set/result/execution
classes add no JSON keys—the existing execution and result shapes stay
closed—while `backend_components` is the sole new attempt member.

The attempt reader applies exact key sets selected by the envelope: the four
schema-v1 fields, the seven schema-v2/v3 fields, or those seven plus required
`backend_components` for schema v4. The execution reader applies the inherited
conditional `detection` key and schema-v2+ `plugin_host` key rules, then calls
`_attempt_from_data(..., schema_version=envelope_version)` for every item.
Missing `backend_components` in v4, its presence in v1-v3, an unknown member,
or any cross-version runtime instance is an error rather than an implicit
upgrade or downgrade.

`serialized_change_size` is an internal, version-required helper and calls
`_change_to_data` with the same explicit version before applying the canonical
compact JSON encoding. It has no default schema. Every payload-budget producer
and validator passes its enclosing outcome version. In a v4 result, including
one upgraded from a predecessor, `image.changes.payload_bytes.used` is the sum
of `serialized_change_size(item, schema_version=4)` over retained items. The v4
encoding of every predecessor change remains byte-identical to its predecessor
object encoding; an image change is rejected for versions 1–3. Thus truncation
selection, recorded resource usage, detached validation, and canonical fixture
bytes all measure the same payload.

Subclassing does not weaken version gates. Direct construction and encoding
apply exact-type rules: an exact `ExecutionRecordV2` contains only exact
`CapabilityAttemptV2` items, while `ExecutionRecordV4` first runs all inherited
record checks and then requires exact `CapabilityAttemptV4` items; an exact
plain `ChangeSet` contains only predecessor `Change` variants, while
`ChangeSetV4` runs the inherited completeness/count/limit checks and then its
v4 union checks. V1-v3 completed outcomes require the exact predecessor
`DiffResult`/provenance combination; v4 requires exact
`DiffResultV4`/`ComparisonProvenanceV4`. The v4 reader requires the
`backend_components` member, constructs `BackendComponentVersion` before its
attempt, and rejects unknown component keys, duplicate IDs, or unsorted input.
The v3-to-v4 upgrader invokes the public `CapabilityAttemptV4` constructor with
all inherited values and `backend_components=()`; it never mutates an existing
v2 attempt or bypasses its validation.

`BackendComponentVersion.component_id` is a stable lowercase identifier and
`component_version` is bounded identity text. Components are unique and sorted
by `component_id`. The seven inherited attempt fields retain all P4-C1 value,
provider, selected-capability, version, and `plugin_host` bindings. A v4
attempt with `backend_id=null` requires
`backend_version=null` and `backend_components=[]`. A non-null backend requires
a non-null backend version; separately versioned linked components, when the
backend exposes them, are recorded here rather than in transformations or
free-form diagnostics. For example, a later runtime may identify `libpng` and
`zlib`, but P5-A1 names no installed component and its fixtures use an empty
tuple. This carrier closes RFC 0007's linked-library evidence requirement
without claiming that a backend exists.

The curated top-level `platydiff` exports add `CompareSpecV4`, `DiffResultV4`,
`CompareOutcomeV4`, the three v4 outcome classes, every image spec/change
class and named enum, and the four migration helpers below. The foundational
`SCHEMA_VERSION_V4`, `ChangeV4`, `ChangeSetV4`, `BackendComponentVersion`, v4 attempt,
execution, provenance, and problem classes are public from
`platydiff.core.models`, matching the predecessor's separation of curated and
foundational contracts; they are not duplicated in the top-level export.
Neither surface exports a private decoder or backend implementation. The
serialization exports add `upgrade_outcome_v1_to_v4`,
`upgrade_outcome_v2_to_v4`, `upgrade_outcome_v3_to_v4`, and
`downgrade_outcome_v4_to_v3`. `platydiff.core` re-exports those four migration
helpers with the existing serialization entry points.

## Contract-only canonical fixtures

### Canonical writer and reader semantics

The canonical schema-v4 writer uses UTF-8 JSON with `ensure_ascii=false`,
`allow_nan=false`, recursively lexicographic object-key ordering, compact
separators `,` and `:`, and no trailing newline. This writer order is a
byte-stability rule only. A reader accepts object members in any order, rejects
duplicate, missing, and unknown members, and preserves normative array order.
Changing object-member order alone cannot change meaning; changing the order
of stages, attempts, inputs, transformations, resources, changes, metrics, or
evaluations is validated under that array's existing or image-specific rule.

P5-A1 creates exactly these new byte-stable JSON fixtures:

```text
tests/fixtures/schema_v4/image_completed.json
tests/fixtures/schema_v4/image_unsupported_profile_failed.json
```

Tests construct both outcomes directly from public models and serialize them.
They do not call `compare()`, open an image, import Pillow, register an image
capability, or claim that the source hashes correspond to decoded PNG files.
Fixture comments are not possible in JSON, so the test and fixture inventory
must label them `contract-only schema specimens`.

The completed specimen uses the accepted RFC 0007 one-by-one RGBA vector and
the five exact transformation objects above. Its identity fields are:

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

The displayed objects are partial only to avoid repeating inherited stage,
result, metric, and source-provenance fields; the fixture itself is a complete
outcome and is decoded with the same reject-unknown-key rules as all other
fixtures. `plugin_host`, both providers, `backend_id`, and `backend_version`
must be JSON null, and `backend_components` must be empty. The strings
`pillow`, `PIL`, a Pillow version, a distribution name, a module path, and a
local path must not occur anywhere in either fixture.

The completed specimen has no detection record and exactly one attempt, whose
disposition is `selected`. The attempt and comparison provenance are bound
mechanically:

```text
attempt.capability_id == provenance.comparator_id == "image"
attempt.capability_version == provenance.comparator_version == "1"
attempt.provider == provenance.provider == null
attempt.backend_id == attempt.backend_version == null
attempt.backend_components == []
provenance.detector_provider == null
execution.plugin_host == null
```

`image` is the single built-in comparator/capability identifier for both the
schema contract and every future runtime implementation. This amendment
globally supersedes RFC 0007's earlier `image.decoded_samples` comparator name;
that dotted value is not a second legal comparator or capability ID in P5-A1,
P5-A2, P5-A3, or any migration. The dotted string
`image.decoded_samples.tiles.v1` remains only the algorithm identifier. A
dotted comparator identifier with null provider, including
`image.decoded_samples`, is invalid under the inherited P4-C1 provider
invariant and must be rejected.

The completed specimen has `artifacts=[]`, full fidelity, a complete
`ChangeSet`, and no diagnostic. It uses only the image metric, evaluation,
change, summary, resource, and digest invariants already accepted by RFC 0007.
All configured/used resources are represented by the exact RFC 0007 names,
sorted lexicographically, and all five transformations are present in the
normative order. The failed specimen has no `DiffResult`, artifacts, metrics,
changes, comparison provenance, or transformations; its execution ends with a
failed `decoding` stage and carries the exact problem below.

P5-A1 may reserve `image` and `image.decoded_samples.tiles.v1` in schema
validation only. The runtime registry continues to reject them. P5-A2 may use
`image` in decoder contract evidence without registering an executable public
comparison route; P5-A3 is the first gate allowed to register the built-in
`image` comparator/capability. A later runtime must record the actual selected
backend and Platydiff implementation version; it must not copy
`implementation_version="contract-only"` into a runtime outcome or emit the
superseded `image.decoded_samples` comparator value.

### Cross-object bindings

The canonical completed specimen is an equal one-by-one RGBA specimen: both
roles use the RFC 0007 sample vector `00 7f ff 80`, all three descriptor
digests are equal, no change item is present, relation/verdict/fidelity are
`equal`/`pass`/`full`, and `artifacts=[]`. These bindings are semantic reader
invariants, independent of object-member order:

| Fact | Required binding |
| --- | --- |
| Inputs | `provenance.inputs` has exactly `before`, then `after`; each decode role's `input_bytes` equals that input's `size_bytes`, and its input digest is a valid SHA-256 evidence value. The specimen does not claim those bytes are a runnable PNG fixture. |
| Spec/profile | `spec.kind=image`; each transformation policy/profile/tile value equals the corresponding normalized spec value. |
| Decode/resources | Per role, decode `input_bytes`, metadata counters, `pixels`, and `decoded_bytes` equal the `used` value of the correspondingly named `ResourceUsage`; each resource `limit` equals the normalized spec limit. |
| Mode/alpha | Per role, decode `mode` equals alpha `mode`; bands and `has_alpha` match that mode; IHDR color type and decoded-byte arithmetic match it. |
| Dimensions/alignment | Decode dimensions establish coordinate bounds; coordinate policy and tile size equal the normalized spec. Equal descriptors require equal role dimensions, mode/bands/alpha, and color-description digest. |
| Comparison work | `image.compare.sample_pairs.used == image.compared_samples`; its limit equals `max_compare_work`. |
| Changes/resources | `image.changes.items.used == changes.returned_count`; `image.changes.payload_bytes.used` equals `sum(serialized_change_size(item, schema_version=4) for item in changes.items)`; their limits equal the two spec change limits. |
| Summary/changes | `summary.change_count == changes.total_count == image.changed_items`; summary `changed_tiles` equals the full tile-change count and `descriptor_changes` equals the full descriptor-change count. |
| Metrics | The equal specimen has compared/equal/changed pixels `1/1/0`, compared samples `4`, changed items `0`, MAE/RMSE `0.0`, and tagged positive-infinity PSNR, in RFC 0007 metric order. |
| Evaluation | The single `image.decoded_sample_equality` evaluation observes `image.changed_items`, uses `eq 0`, and its verdict equals the result verdict. Relation is equal iff changed items is zero. |

### Digest verification boundary

A detached reader can verify only facts carried by the outcome. It validates
64-lowercase-hex syntax, maps operation/component to the declared RFC 0007
digest domain, and
maps the two digest fields to the `before`/`after` roles. It independently
recomputes dimensions and pixel-format descriptor digests from the public
decode/alpha facts. For a color-description change it requires each change
digest to equal that role's `image.color.native_exact.description_digest`.
For a tile change it can validate domain selection, role placement, geometry,
and digest syntax, but cannot recompute sample digests because samples are
deliberately absent.

Content correctness is a producer-only obligation. The producer hashes the
actual owned input bytes for `InputProvenance`, derives decode facts from the
validated stream, hashes the full canonical color-description payload, and
hashes each role's actual canonical tile samples. It also computes changed
pixels and maximum error from those samples. A detached reader must not report
these producer-only facts as independently verified merely because the wire
object is internally consistent.

Compatibility tests independently recompute all four RFC 0007 digest vectors
from the literal ASCII domain strings and literal payload hex using the Python
standard-library SHA-256 implementation. That oracle must not call the
Platydiff serializer, image comparator, decoder, Pillow, or a production digest
helper. Tests compare each recomputed digest byte-for-byte with the published
constant and separately test detached-reader checks. The canonical equal
specimen contains no `ImageChange`, so these vector tests remain distinct from
its byte-stable fixture round trip.

Those obligations are assigned to the gate that first owns the corresponding
runtime data. P5-A1 tests only detached validation and the four independent
literal domain/payload digest oracles; they use no image source, decoder, or
comparator. P5-A2 owns producer tests for owned input bytes, scanner/decode
facts, and canonical color-description bytes. P5-A3 owns producer tests for
actual tile samples, tile digests, changed-pixel/error calculations, and
comparison resource accounting. Neither later test set is a P5-A1 merge gate.

For every schema-v4 image outcome, not only the canonical specimen, a
descriptor change forbids tile changes and forces compared/equal/changed pixel
and compared-sample metrics to zero. If descriptors match, every tile is within
both role dimensions, has `1 <= width,height <= 64`, and edge geometry follows
the fixed grid. A tile change has `1 <= changed_pixels <= width * height` and a
finite `maximum_absolute_error` in the inclusive range `1.0..255.0`; NaN,
positive/negative infinity, zero, and negative error are invalid. For a
complete change set, the sum of tile `changed_pixels` equals the full
`image.changed_pixels` metric. For a truncated set, the retained sum must not
exceed that metric; the producer computes the full metric before truncation,
while the reader does not invent omitted tile facts. Digest claims follow the
detached-reader and producer-only boundary above.

The canonical failed specimen has no detection record and exactly one attempt,
whose disposition is `selected`, with capability/version `image`/`1`, null
provider/backend identities, empty `backend_components`, and null
`plugin_host`. It has no comparison
provenance because a failed outcome has no `DiffResult`; the selected attempt
is still required to explain why execution reached `decoding`.

## Schema-v4 problem model

Schema v4 uses the P4-C1 schema-v3 execution/capability problem shapes and
adds one failed code to `ExecutionProblemV4`:

```python
class ExecutionProblemV4:
    code: str
    status_code: int
    stage: PipelineStage
    message: str
    details: JsonObject
    retryable: bool
```

All existing schema-v2/v3 failed mappings remain unchanged. The new mapping is
valid only as this exact tuple:

```text
code = unsupported_image_profile
status_code = 415
stage = decoding
retryable = false
```

Its `details` object has exactly two keys:

```json
{
  "profile": "static_png_8bit_v1",
  "reason": "unsupported_color_type"
}
```

`profile` is `ImageDecodeProfile.STATIC_PNG_8BIT_V1`; `reason` is one
`UnsupportedImageProfileReason` value. The message is Unicode-scalar text
under the inherited validity and terminal-escaping rules. Schema v4 adds no
problem-message wire-length bound because no predecessor bound exists; the
separate terminal projection limit below bounds rendering. The message must
not contain source bytes, metadata, ICC/EXIF values, absolute paths, module
paths, or backend exception text. The canonical fixture message is exactly
`input is outside the static PNG 8-bit profile`.

`CapabilityProblemV4` adds no code and has the same mappings and resolving-stage
rules as the P4-C1 schema-v3 capability problem. `unsupported_image_profile`
is never unavailable and never occurs at detecting or resolving.

The allowlist is version-gated by the outer envelope before problem decoding:

- schema v1 rejects `unsupported_image_profile` as an invalid v1 failed code;
- schema v2 rejects it as an invalid v2 failed code;
- schema v3 rejects it as an invalid v3 failed code; and
- only schema v4 accepts it, with every tuple/detail invariant above.

Changing only the outer `schema_version` of a v4 fixture to `1`, `2`, or `3`
must fail decoding; readers must not silently reinterpret, drop, or rename the
code.

### Complete scenario classification

Classification is based on the explicit PNG profile, not a filename or MIME
label. For the eight-byte PNG signature, a short input that is an exact proper
prefix is truncated/malformed and therefore `decode_error`; a short or full
prefix that already differs from the PNG signature is a wrong codec and
therefore `unsupported_image_profile/wrong_codec`. This rule resolves the
previous ambiguity between an unsupported codec and a damaged PNG.

| Input/execution scenario | Outcome and code | Stage | `reason` when applicable |
| --- | --- | --- | --- |
| Backend absent or outside the accepted version range | unavailable / `backend_unavailable` (503) | resolving | — |
| No built-in image capability is registered, including all P5-A1 runtime calls | unavailable / `capability_unavailable` (501) | resolving | — |
| Invalid `ImageCompareSpec` field, type, or limit | failed / `invalid_spec` (400) | validating | — |
| Missing path source | failed / `source_not_found` (404) | sourcing | — |
| Source read is denied | failed / `permission_denied` (403) | sourcing | — |
| Source mutates during the owned snapshot | failed / `source_changed` (409) | sourcing | — |
| Directory, special file, `TextSource`, or another unsupported source kind | failed / `source_type_unsupported` (415) | sourcing | — |
| Other source read failure | failed / `io_error` (500) | sourcing | — |
| Bytes diverge from the PNG signature before the available prefix ends | failed / `unsupported_image_profile` (415) | decoding | `wrong_codec` |
| Exact proper prefix of the PNG signature ends early | failed / `decode_error` (422) | decoding | — |
| Valid PNG uses 1/2/4-bit greyscale or any 16-bit sample pair | failed / `unsupported_image_profile` (415) | decoding | `unsupported_bit_depth` |
| Valid PNG uses indexed color or another legal unsupported color type | failed / `unsupported_image_profile` (415) | decoding | `unsupported_color_type` |
| Valid PNG contains `tRNS` and needs implicit transparency expansion | failed / `unsupported_image_profile` (415) | decoding | `transparency_expansion_required` |
| Valid PNG contains `acTL`, `fcTL`, or `fdAT`, or otherwise proves multiple frames | failed / `unsupported_image_profile` (415) | decoding | `multiple_frames` |
| Structurally valid PNG contains an unknown critical chunk | failed / `unsupported_image_profile` (415) | decoding | `unknown_critical_chunk` |
| Signature is PNG but framing, CRC, ordering, multiplicity, chunk value, compressed metadata, `IEND`, or stream termination is malformed | failed / `decode_error` (422) | decoding | — |
| Scanner accepts the profile but a later backend reports a different codec, mode, dimensions, frame state, or malformed decode | failed / `decode_error` (422) | decoding | — |
| Input snapshot crosses `max_input_bytes` | failed / `resource_limit_exceeded` (413) | sourcing | — |
| Metadata, ICC, dimension, pixel, decoded-byte, or decompression-bomb limit is crossed | failed / `resource_limit_exceeded` (413) | decoding | — |
| Complete sample comparison would cross its work budget | failed / `compare_resource_limit` (413) | comparing | — |
| Selected built-in comparator fails outside classified decode/resource conditions | failed / `comparator_failure` (502) | comparing | — |
| Unexpected exception caught by the outer CLI handler | failed / `internal_error` (500) | `validating` | — |
| Dimensions, pixel format, or color description differ after successful decode | completed / different / fail | aggregating | — |
| Supported descriptors and all samples match/differ | completed / equal/pass or different/fail | aggregating | — |

An `unsupported_image_profile` object must use the reason in the matching row;
the six reasons are exhaustive for schema v4. `decode_error` and every inherited
problem retain their inherited details policy and must not acquire a profile
`reason`. A condition that is both malformed and outside the supported profile
is `decode_error`: structural validity is established before support-profile
classification, except for the explicit signature-prefix rule above.

After source and resource enforcement, the scanner completes bounded structural
validation before selecting an unsupported-profile reason. Any malformed fact
produces `decode_error` even if an unsupported feature was also observed. If
the structure is valid and more than one unsupported feature is present, the
producer chooses the first reason in this total priority order, independent of
chunk discovery order:

```text
1. wrong_codec
2. multiple_frames
3. unknown_critical_chunk
4. unsupported_color_type
5. unsupported_bit_depth
6. transparency_expansion_required
```

`wrong_codec` cannot coexist with features parsed after a valid PNG signature,
but occupies rank 1 so the classification function is total for every input.
A resource breach that prevents the complete bounded scan remains
`resource_limit_exceeded`, not a partially selected reason. The following
classification cases are normative gate vectors:

| Vector | Supported/unsupported facts | Expected classification |
| --- | --- | --- |
| `signature_jpeg` | JPEG signature; no PNG structure | `unsupported_image_profile/wrong_codec` |
| `apng_unknown_indexed_trns` | APNG control, unknown critical chunk, indexed 4-bit color, and `tRNS` | `unsupported_image_profile/multiple_frames` |
| `unknown_indexed_trns` | Unknown critical chunk, indexed 4-bit color, and `tRNS` | `unsupported_image_profile/unknown_critical_chunk` |
| `indexed_4bit_trns` | Indexed 4-bit color and `tRNS` | `unsupported_image_profile/unsupported_color_type` |
| `grey_16bit_trns` | Greyscale 16-bit samples and `tRNS` | `unsupported_image_profile/unsupported_bit_depth` |
| `rgb_8bit_trns` | Otherwise supported RGB 8-bit PNG with `tRNS` | `unsupported_image_profile/transparency_expansion_required` |

P5-A1 freezes these rows as contract metadata and directly constructs one
schema-v4 failed-problem specimen for each reason. Its tests prove enum,
problem-tuple, stage, detail, reader/writer, and v1-v3 rejection behavior only;
the vector names do not name P5-A1 image files, and P5-A1 creates no PNG bytes,
scanner, decoder, corpus, or reason-selection implementation. P5-A2 owns the
generated CRC/order-valid PNG inputs, total-priority scanner test, discovery-
order permutations, and each malformed bad-CRC twin. Every P5-A2 twin must
produce `decode_error`; permutations that preserve PNG validity must not change
the selected reason. P5-A3 reuses the P5-A2 classification suite but does not
reclassify decode failures in the comparator.

`internal_error` records `stage="validating"`, the existing real
`PipelineStage` used for synthetic CLI failures. “Outer CLI handler” describes
where the exception was caught; it is not a serialized stage value.

## Minimal safe terminal projection

P5-A1 may extend the terminal renderer only to consume an already validated
v4 outcome. It receives no source service or artifact root and performs no
metric, digest, image, or verdict computation. The inherited header, fidelity,
summary counts, and diagnostics retain their meaning, but the whole schema-v4
projection is subject to these exact bounds:

```text
TERMINAL_V4_MAX_LINES = 512
TERMINAL_V4_MAX_UNICODE_SCALARS = 65_536
TERMINAL_V4_MAX_UTF8_BYTES = 65_536
TERMINAL_V4_OVERFLOW_LINE = ... terminal output truncated by schema-v4 limits
```

The renderer produces a stream of complete logical lines in existing order,
escapes untrusted text first, and joins retained lines with one ASCII LF and no
trailing LF. Line count includes the overflow line; scalar and byte counts
include separators. It retains the longest prefix for which, when more logical
lines remain, the exact overflow line and its separator also fit all three
limits. If anything is omitted it emits that overflow line exactly once and
stops; it never emits a partial logical line. If even the first logical line
plus the overflow line cannot fit, the output is the overflow line alone. The
algorithm is independent of terminal width, locale, color, and environment.

For `ImageChange`, it appends exactly one bounded line per retained change:

```text
descriptor <component> changed
tile x=<x> y=<y> width=<width> height=<height> changed_pixels=<count> maximum_absolute_error=<decimal>
```

The descriptor form uses only the validated component wire value. The tile
form uses only validated integers and a validated finite error. Coordinates
use grammar `0|[1-9][0-9]{0,15}` and remain within the existing exact-integer
bound; width, height, and changed pixels use `[1-9][0-9]{0,15}` plus their
model bounds. `maximum_absolute_error` must also be mathematically integral
and is rendered with Python's locale-independent `repr(float(value))`; after
the required `1.0..255.0` validation its grammar is
`(?:[1-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.0`.
An image tile never renders a tagged NaN or infinity. In addition to the
general image invariant, terminal input validation requires
`changed_pixels <= width * height` before any line is produced.
Digests, pixels, paths, labels, metadata, profiles, and source excerpts are not
printed. A truncated result renders only retained items and the inherited
complete total; it never implies that omitted tiles are absent.

For the canonical failed fixture, the inherited problem projection is exactly:

```text
failed [unsupported_image_profile/415] at decoding: input is outside the static PNG 8-bit profile
```

An unknown schema-v4 built-in change, transformation, enum, or problem code is
rejected by the reader before rendering. The renderer does not guess a generic
image meaning. Namespaced `ExtensionChange` retains the existing explicit
generic presentation.

Golden tests cover output at exactly 512 lines, 65,536 scalars, and 65,536
UTF-8 bytes; one-line/one-scalar/one-byte overflow; a multibyte diagnostic; an
individual overbound line; and deterministic repetition. They also reject tile
errors `0`, `NaN`, both infinities, and values above `255`, and reject zero or
over-64 dimensions, zero changed pixels, and changed pixels above tile area.

## Upgrade, downgrade, and reader boundaries

The v4 reader accepts and preserves valid v1, v2, v3, and v4 envelopes. The
three explicit upgrade helpers are exact compositions:

```text
upgrade_outcome_v3_to_v4(v3) -> v4
upgrade_outcome_v2_to_v4(v2) = upgrade_outcome_v3_to_v4(upgrade_outcome_v2_to_v3(v2))
upgrade_outcome_v1_to_v4(v1) = upgrade_outcome_v2_to_v4(upgrade_outcome_v1_to_v2(v1))
```

The v3-to-v4 step replaces each attempt with `CapabilityAttemptV4` carrying
the same seven inherited fields plus `backend_components=[]`, replaces the
execution/provenance/problem wrapper with its exact v4 type, and reconstructs
completed results as `ChangeSetV4` plus `DiffResultV4`, preserving all wire
facts. It does not relabel a predecessor outcome as image.

No predecessor schema contains an image comparator, so no upgrade helper
renames a comparator. There is also no accepted earlier schema-v4 writer to
migrate. A v4 payload that uses RFC 0007's superseded
`comparator_id="image.decoded_samples"` or the same capability-attempt ID is
invalid rather than migrated; valid image fixtures and future runtime outcomes
use `image` in both locations and retain
`algorithm_id="image.decoded_samples.tiles.v1"`.

There is no automatic downgrade in a renderer, CLI, JSON writer, or reader.
P5-A1 defines exactly one new downgrade helper:

```python
def downgrade_outcome_v4_to_v3(outcome: CompareOutcomeV4) -> CompareOutcomeV3: ...
```

It succeeds only after validation proves that every field is representable in
schema v3 and every attempt has `backend_components=[]`. It must reject any
outcome containing at least one of:

- an image spec kind or image change;
- an `image` or `image.*` built-in transformation, comparator, algorithm, metric,
  evaluation, resource, or capability-attempt identifier;
- `unsupported_image_profile`; or
- a non-empty `backend_components` tuple; or
- any other schema-v4-only fact, enum value, or problem shape.

On success it converts the exact v4 wrappers, attempts, change set, and result
back to their v3 types without changing any remaining value. A caller may then explicitly use
the already implemented `downgrade_outcome_v3_to_v2`; P5-A1 does not modify or
bypass that gate. No v2-to-v1 downgrade helper exists in the reviewed
predecessor, so P5-A1 does not promise or add one. Such a helper is deferred to
a separate contract if a use case requires it. Every `ImageCompareSpec`
outcome and both P5-A1 canonical fixtures are non-downgradable to v3 or below.
An older reader that does not know schema v4 must fail with its existing
unknown-schema error; it is not required to render a lossy approximation.

## Mechanical acceptance criteria

Acceptance of this RFC authorizes no code. A later P5-A1 dispatch must satisfy
all of the following before merge:

1. The actual merged P4-C1 commit is an ancestor of the implementation branch,
   its full predecessor suite passes unchanged, and its public v3 types match
   this amendment. Otherwise work stops for an RFC callback.
2. `SCHEMA_VERSION_V4`, `BackendComponentVersion`, `CapabilityAttemptV4`,
   `ExecutionRecordV4`, `ComparisonProvenanceV4`, both v4 problem classes,
   all three v4 outcome classes, `CompareSpecV4`, `ChangeV4`, `ChangeSetV4`,
   `DiffResultV4`, `CompareOutcomeV4`, the expanded `AnyCompareOutcome`, every documented
   image spec/change/enum, and exactly four v4 migration helpers are present in
   the documented top-level versus foundational export sets above; no
   decoder/backend implementation is exported.
3. Exact predecessor/v4 constructors, readers, and encoders reject cross-version
   attempt, change-set, result, provenance, problem, and outcome mixing while
   v4 subclasses demonstrably run all inherited validation first. The outer
   envelope version is passed explicitly through execution, attempt, result,
   and change serializers; v4 attempts require `backend_components`, v1-v3
   reject it, and `serialized_change_size` requires the enclosing version and
   measures the same canonical change bytes used for payload truncation and
   validation. Every new object rejects missing/extra keys,
   booleans-as-integers, invalid enum values, invalid mode/IHDR/band
   combinations, invalid role ordering, invalid digests, and violated
   cross-field invariants.
4. Each of the five transformation records accepts its canonical payload and
   rejects a wrong stage, ID, key, type, nesting, value, or sequence position.
5. v1/v2/v3 canonical files remain byte-identical; all predecessor round trips,
   migrations, plugin receipts, CLI outputs, and public exports remain valid.
6. The two v4 fixtures round-trip byte-identically under the canonical writer
   while permuted object members read identically. Tests prove direct
   construction, exact `image` attempt/comparator/version/provider binding,
   null backend identities, empty components, absence of Pillow strings,
   absence of image runtime registration/CLI route/dependency, and rejection
   by v1-v3 code gates where applicable.
7. The v4 reader rejects duplicate keys, unknown schemas, unknown built-in
   kinds/transformations/problems, and invalid image change combinations,
   mixing, ordering, geometry, context, and serializer-version signatures before terminal rendering.
8. Terminal golden tests cover descriptor, tile, truncated, failed, unsafe
   message, unknown-kind, exact line/scalar/UTF-8 boundaries, deterministic
   overflow, numeric grammar, and tile value/area rejection without source or
   artifact authority.
9. Migration tests prove all three lossless predecessor-to-v4 upgrades, exact
   representable v4-to-v3 downgrade, subsequent use of the existing v3-to-v2
   helper, and hard rejection of image-bearing, component-bearing, or
   `unsupported_image_profile` downgrade. No v2-to-v1 helper is added.
10. P5-A1 directly constructs and round-trips all six schema problem reasons
    with their exact tuple/detail/stage gates, including `internal_error` at
    `validating`, but contains no PNG or scanner test. P5-A2, not P5-A1, owns
    the generated classification vectors, malformed twins, total-priority
    selection, and discovery-order permutations.
11. P5-A1 detached-reader tests cover only wire-verifiable digest
    syntax/domain/role bindings, and a separate standard-library oracle
    recomputes all four RFC 0007 vectors without production helpers. P5-A2 owns
    input/decode/color-description producer correctness; P5-A3 owns tile-sample,
    change-metric, and comparison-resource producer correctness. Those runtime
    producer tests are not P5-A1 acceptance criteria.
12. Problem messages retain predecessor wire behavior without a claimed length
    bound, while terminal tests independently prove the v4 rendering bounds.
13. Ruff format/check, strict mypy, the complete pytest suite, build and
    wheel/sdist inspection, `git diff --check`, and relative-link checks all
    pass. Only commands actually run may be reported.

The implementation diff must contain no Pillow reference outside explanatory
tests/docs, dependency metadata, image decoder/scanner/comparator, capability
registration, CLI image route, auto/SDK expansion, artifact, corpus image, or
UI code.

The P5-A1 commit boundaries are:

1. `feat(core): add schema-v4 image comparison contracts`
2. `feat(renderers): add bounded schema-v4 image projection`
3. `test(core): add schema-v4 compatibility and migration fixtures`

Each commit must pass the relevant predecessor tests. The third commit is the
gate commit and must prove the complete mechanical criteria above.

## Relationship to later gates

P5-A2 remains the first optional-backend and decode gate. It owns actual source
snapshots, generated scanner vectors and malformed twins, support-profile
priority selection, decoded facts, and the corresponding producer evidence.
P5-A3 remains the first comparator, capability-registration, terminal command,
and executable image-result gate. It owns actual sample/tile comparison,
change/metric/resource producer evidence, and registration of the sole built-in
comparator/capability ID `image`. Their dispatches are independent; neither is
a hidden P5-A1 acceptance gate. This amendment does not alter the
P5-C/P5-P/P5-F/P5-M/P5-H/P5-S callbacks or authorize any of them.

This RFC supersedes RFC 0007's built-in comparator identity
globally: `image` replaces `image.decoded_samples` in schema fixtures, attempts,
provenance, migrations, and every future runtime gate, while
`image.decoded_samples.tiles.v1` remains the algorithm ID. It also supersedes
RFC 0007's open choices about P5-A1 enum representation, transformation JSON
shape, schema-only fixture identity, schema-v4 problem gating and signature
classification, terminal projection, and downgrade mechanics. All other
I1-I16 decisions and RFC 0007 semantics remain authoritative.

## References

- [RFC 0001: Comparison outcome and DiffResult](0001-comparison-outcome-and-diff-result.md)
- [RFC 0004: Human review UI and renderer boundary](0004-human-review-ui-and-renderer-boundary.md)
- [RFC 0007: Image comparison](0007-image-comparison.md)
- [RFC 0010: Schema predecessor and Phase 6 amendment](0010-schema-predecessor-and-phase6-contract-amendment.md)
