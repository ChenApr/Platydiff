# RFC 0013: P5-A1 Image Wire-Contract Amendment

[Chinese documentation](0013-p5a1-image-wire-contract-amendment_zh.md)

- Status: Proposed
- Date: 2026-09-10
- Owners: Platydiff maintainers
- Amends: [RFC 0007](0007-image-comparison.md), if accepted
- Predecessor: [RFC 0010](0010-schema-predecessor-and-phase6-contract-amendment.md)
- Implementation authorization: none

## Summary

This proposed amendment closes the wire-level decisions needed before P5-A1
can be dispatched. It does not change the accepted I1-I16 image semantics in
RFC 0007. It freezes the P5-A1 boundary, public enum types, five image
transformation payloads, schema-only provenance specimens, the
`unsupported_image_profile` problem, terminal presentation, downgrade rules,
and compatibility acceptance criteria.

The evidence baseline is `origin/main` `5f23bbf` on 2026-09-10. RFC 0010 is on
that baseline. The reviewed P4-C1 candidate is `63b62d9`, and it is **not** an
ancestor of that `main`. P4-C1 therefore remains an unmerged predecessor
candidate. This RFC may be reviewed now, but neither acceptance nor merge of
this document would satisfy the P5-A1 predecessor gate.

## Authorization boundary

P5-A1 is strictly contract-only. If this amendment is accepted and the
predecessor gate later passes, P5-A1 may add only:

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

P5-A1 remains blocked until the actual P4-C1 implementation and its v1-v3
compatibility fixtures are merged to `main`, independently verified, and found
consistent with the types named below. Any mismatch returns to this RFC rather
than being repaired opportunistically in code.

## Proposed decisions requiring approval

| ID | Proposed decision |
| --- | --- |
| P5A1-1 | Make P5-A1 strictly contract-only under the boundary above. |
| P5A1-2 | Use named `StrEnum` types for reusable public image choices; retain `Literal` only for discriminators and the invariant tile-size constant. |
| P5A1-3 | Freeze the five transformation parameter objects exactly as specified below; reject missing and unknown keys. |
| P5A1-4 | Treat schema-v4 completed/failed fixtures as direct contract specimens with null provider/backend identity and no Pillow claim. |
| P5A1-5 | Add `unsupported_image_profile` only to the schema-v4 failed-problem allowlist, with a closed details object; v1-v3 readers continue to reject it. |
| P5A1-6 | Add only the bounded terminal projection below and permit downgrade only when every fact is losslessly representable in the target predecessor. |

No proposal in this table is Accepted until a human explicitly approves its
ID and this RFC status is changed in a later documentation change.

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

The role object keys are always `before` followed by `after` in the public
model. Canonical JSON byte order remains the existing serializer's order; the
pretty examples in this RFC add whitespace only for readability.

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

## Contract-only canonical fixtures

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

The displayed objects are partial only to avoid repeating inherited stage,
result, metric, and source-provenance fields; the fixture itself is a complete
outcome and is decoded with the same reject-unknown-key rules as all other
fixtures. `plugin_host`, both providers, `backend_id`, and `backend_version`
must be JSON null. The strings `pillow`, `PIL`, a Pillow version, a distribution
name, a module path, and a local path must not occur anywhere in either fixture.

The completed specimen has `artifacts=[]`, full fidelity, a complete
`ChangeSet`, and no diagnostic. It uses only the image metric, evaluation,
change, summary, resource, and digest invariants already accepted by RFC 0007.
All configured/used resources are represented by the exact RFC 0007 names,
sorted lexicographically, and all five transformations are present in the
normative order. The failed specimen has no `DiffResult`, artifacts, metrics,
changes, comparison provenance, or transformations; its execution ends with a
failed `decoding` stage and carries the exact problem below.

P5-A1 may reserve `image`, `image.decoded_samples`, and
`image.decoded_samples.tiles.v1` in schema validation only. The runtime
registry continues to reject them. A later P5-A2/P5-A3 implementation must
replace runtime identity with the actual selected backend and Platydiff
implementation version; it must not copy `implementation_version="contract-only"`
into a runtime outcome.

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
`UnsupportedImageProfileReason` value. The message is terminal-safe Unicode
text under the inherited bound and escaping rules, but must not contain source
bytes, metadata, ICC/EXIF values, absolute paths, module paths, or backend
exception text. The canonical fixture message is exactly
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

## Minimal safe terminal projection

P5-A1 may extend the terminal renderer only to consume an already validated
v4 outcome. It receives no source service or artifact root and performs no
metric, digest, image, or verdict computation. The inherited header, fidelity,
summary counts, and diagnostics remain unchanged.

For `ImageChange`, it appends exactly one bounded line per retained change:

```text
descriptor <component> changed
tile x=<x> y=<y> width=<width> height=<height> changed_pixels=<count> maximum_absolute_error=<tagged-number>
```

The descriptor form uses only the validated component wire value. The tile
form uses only validated non-negative/positive integer fields and the existing
tagged numeric rendering; finite values use the existing locale-independent
float representation and infinities/NaN use their existing explicit tags.
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

## Upgrade, downgrade, and reader boundaries

The v4 reader accepts and preserves valid v1, v2, v3, and v4 envelopes. Explicit
v1/v2/v3-to-v4 helpers add only the same neutral defaults already accepted for
predecessor migration; they do not relabel a legacy outcome as image.

There is no automatic downgrade in a renderer, CLI, JSON writer, or reader. A
requested `downgrade_outcome_v4(outcome, target_version)` succeeds only after
validation proves that every field is representable by that target. It must
reject any outcome containing at least one of:

- an image spec kind or image change;
- an `image.*` built-in transformation, comparator, algorithm, metric,
  evaluation, resource, or capability-attempt identifier;
- `unsupported_image_profile`; or
- any schema-v4-only fact, enum value, or problem shape.

The helper then applies the existing v3-to-v2 and v2-to-v1 gates rather than
bypassing them. In particular, every `ImageCompareSpec` outcome and both P5-A1
canonical fixtures are non-downgradable to v1-v3. An older reader that does not
know schema v4 must fail with its existing unknown-schema error; it is not
required to render a lossy approximation.

## Mechanical acceptance criteria

Acceptance of this RFC authorizes no code. A later P5-A1 dispatch must satisfy
all of the following before merge:

1. The actual merged P4-C1 commit is an ancestor of the implementation branch,
   its full predecessor suite passes unchanged, and its public v3 types match
   this amendment. Otherwise work stops for an RFC callback.
2. `ImageCompareSpec`, `ImageResourceLimits`, `ImageChange`, the named enums,
   v4 outcome aliases/classes, `ExecutionProblemV4`, and explicit migrations
   are present in the documented public export set; no decoder/backend object
   is exported.
3. Every new object rejects missing/extra keys, booleans-as-integers, invalid
   enum values, invalid mode/IHDR/band combinations, invalid role ordering,
   invalid digests, and violated cross-field invariants.
4. Each of the five transformation records accepts its canonical payload and
   rejects a wrong stage, ID, key, type, nesting, value, or sequence position.
5. v1/v2/v3 canonical files remain byte-identical; all predecessor round trips,
   migrations, plugin receipts, CLI outputs, and public exports remain valid.
6. The two v4 fixtures round-trip byte-identically. Tests prove their direct
   construction, null provider/backend identities, absence of Pillow strings,
   absence of an image runtime registration/CLI route/dependency, and rejection
   by v1-v3 code gates where applicable.
7. The v4 reader rejects duplicate keys, unknown schemas, unknown built-in
   kinds/transformations/problems, and invalid image change combinations before
   terminal rendering.
8. Terminal golden tests cover descriptor, tile, truncated, failed, unsafe
   message, and unknown-kind behavior without source or artifact authority.
9. Migration tests prove lossless predecessor upgrades, legacy-only v4
   downgrades where representable, and hard rejection of every image-bearing or
   `unsupported_image_profile` downgrade.
10. Ruff format/check, strict mypy, the complete pytest suite, build and
    wheel/sdist inspection, `git diff --check`, and relative-link checks all
    pass. Only commands actually run may be reported.

The implementation diff must contain no Pillow reference outside explanatory
tests/docs, dependency metadata, image decoder/scanner/comparator, capability
registration, CLI image route, auto/SDK expansion, artifact, corpus image, or
UI code.

The proposed P5-A1 commit boundaries are:

1. `feat(core): add schema-v4 image comparison contracts`
2. `feat(renderers): add bounded schema-v4 image projection`
3. `test(core): add schema-v4 compatibility and migration fixtures`

Each commit must pass the relevant predecessor tests. The third commit is the
gate commit and must prove the complete mechanical criteria above.

## Relationship to later gates

P5-A2 remains the first optional-backend and decode gate. P5-A3 remains the
first comparator, capability-registration, terminal command, and executable
image result gate. Their dispatches are independent. This amendment does not
alter the P5-C/P5-P/P5-F/P5-M/P5-H/P5-S callbacks or authorize any of them.

If accepted, this RFC supersedes only RFC 0007's open choices about P5-A1 enum
representation, transformation JSON shape, schema-only fixture identity,
schema-v4 problem gating, terminal projection, and downgrade mechanics. All
other I1-I16 decisions and RFC 0007 semantics remain authoritative.

## References

- [RFC 0001: Comparison outcome and DiffResult](0001-comparison-outcome-and-diff-result.md)
- [RFC 0004: Human review UI and renderer boundary](0004-human-review-ui-and-renderer-boundary.md)
- [RFC 0007: Image comparison](0007-image-comparison.md)
- [RFC 0010: Schema predecessor and Phase 6 amendment](0010-schema-predecessor-and-phase6-contract-amendment.md)
