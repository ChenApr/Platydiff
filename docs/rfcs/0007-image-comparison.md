# RFC 0007: Image Comparison

[Chinese documentation](0007-image-comparison_zh.md)

- Status: Accepted
- Date: 2026-09-10
- Review revision: 2026-09-10
- Acceptance date: 2026-09-10
- Owners: Platydiff maintainers
- Implementation owner: unassigned; conditional authorization recorded for
  coordinator dispatch after the actual predecessor merge gate passes
- Predecessor amendment: RFC 0010 records conditional authorization for P5-A1
  dispatch only after RFC 0010, P4-C1/schema-v3, and predecessor compatibility
  fixtures merge to `main`; P5-A1 does not start automatically
- Proposed P5-A1 wire amendment: [RFC 0011](0011-p5a1-image-wire-contract-amendment.md)
  closes enum, transformation, fixture, problem, terminal, and downgrade choices;
  it has no effect unless separately accepted

## Summary and authorization boundary

This RFC defines the accepted Phase 5 contract for image comparison. It
deliberately starts with one narrow executable slice: explicit, built-in comparison of the
decoded sample matrix of a single static PNG. Encoded-byte identity remains the
existing binary contract. Perceptual similarity, color conversion, registration,
animation, artifacts, plugin execution, and automatic image detection remain
separate later gates.

Human approval accepts I1-I16 below as the Phase 5 design contract. Acceptance
does not authorize image code, dependencies, SDK changes, automatic detection,
UI work, or artifact publication. It also does not start P5-R, P5-A1, P5-A2, or
P5-A3. Every implementation gate still requires a separate dispatch from
updated `main`.

Phase 4 RFC 0006 is accepted, but its P4-A1 schema-v3 implementation is not
present in the code evidence reviewed for this RFC. Phase 5 therefore has a hard
revalidation prerequisite: schema v3 must first be merged, verified against RFC
0006, and treated as the actual predecessor. This RFC does not assume or stack
on an unmerged Phase 4 branch. No image product code is present at the accepted
evidence revision, and this acceptance-only change adds none.

## Evidence ledger

| Evidence reviewed at `main` `fde2bd4` | Phase 5 constraint |
| --- | --- |
| Runtime code accepts only outcome schema v1/v2; RFC 0006 accepts schema v3 but its implementation is not on this revision. | Image implementation is blocked until the merged schema-v3 code and fixtures are revalidated. Image variants then use schema v4 rather than reopening a frozen predecessor. |
| The public spec/change unions contain only text/binary variants in code. | `ImageCompareSpec` and `ImageChange` require a schema successor and strict reader/writer compatibility tests. |
| `BinaryCompareSpec` already defines collision-safe exact byte identity for any bounded byte source. | Image code must not duplicate or reinterpret encoded-file equality. |
| Existing automatic detection and SDK v1.1 are closed to text/binary. | Image is explicit and built-in only. Auto image detection and third-party image comparators require successors to RFC 0003 and RFC 0005. |
| Source snapshots own bounded reads, hashes, mutation checks, and safe labels. | The image backend consumes host-owned replayable services and never reopens a path by name. |
| Renderers consume validated outcomes and receive no source or artifact root. | Image facts must be bounded in the outcome. A renderer cannot reread pixels, calculate metrics, or create a heatmap. |
| `ArtifactRef` is safe inert metadata, but no comparison artifact sink/root is implemented. | The first image slice emits `artifacts=()`; preview/heatmap delivery needs a separate artifact-authority contract. |
| Core runtime dependencies are empty. | Pillow is optional, lazy, independently reviewed, and cannot become a core dependency. |
| Pillow 12.3.0 is the current candidate reviewed on 2026-09-10; official metadata declares Python 3.10+ and MIT-CMU, and 12.3.0 fixes multiple 2026 memory-safety issues affecting earlier versions. | The dependency gate starts at `Pillow>=12.3,<13`, rechecks advisories at implementation time, inventories bundled native libraries, and does not claim that Pillow is a sandbox. |

The ledger records constraints, not implementation authorization. Evidence from
an unmerged P4-A1 branch may inform review but cannot satisfy the prerequisite.

## Design-to-existing-contract matrix

| Existing contract | Reused without reinterpretation | Phase 5 addition / callback |
| --- | --- | --- |
| RFC 0001 outcome/result | completed/unavailable/failed, relation/verdict/fidelity separation, complete/truncated semantics, metric/evaluation split, safe `ArtifactRef` | Add one schema-v4 built-in `ImageChange`; no new outcome kind or fidelity meaning |
| RFC 0002 phase gate | explicit intent, one public `compare()` entry, focused commits, deterministic limits, independent authorization | Add P5-R/P5-A1/P5-A2/P5-A3; later image capabilities return to a contract gate |
| RFC 0003 binary/detection | encoded equality remains binary; explicit type bypasses detection; host snapshots and no post-start fallback remain | Image auto probing, ambiguity, candidates, and ranking are deferred to a successor |
| RFC 0004 renderer/UI | UI consumes validated bounded outcomes and cannot reread sources or recompute truth | Image tiles may be displayed after schema support; previews/heatmaps and UI-U1/U2/U3 stay unimplemented |
| RFC 0005 SDK | built-in-only default, host-owned sources/stages/outcomes, renderer least authority, SDK v1.1 text/binary closure | Image plugin capability and source/profile validation require SDK v2 review |
| RFC 0006 schema/structured lessons | use a new schema for closed-union growth; keep predecessors; explicit transforms; no partial; facts before rendering | Schema v4 depends on actual merged v3; image-specific descriptors, tiles, metrics, and limits are added only after revalidation |
| Current package | flat package, Python 3.12+, existing CLI exits, zero core dependencies, terminal/JSON downstream | Optional `image` extra and private decoder/comparator only in later authorized gates |

No row grants implementation authority or changes an older schema's meaning.

## Accepted decisions

| ID | Accepted decision | Alternative not selected |
| --- | --- | --- |
| I1 | Accept I1-I16 as the Phase 5 design contract; acceptance does not start P5-R or any implementation gate. | Treat acceptance or a roadmap entry as implementation authorization. |
| I2 | Require merged and independently verified P4-A1/schema v3 before any Phase 5 implementation; then use outcome schema v4. | Stack on unmerged code or extend v2/v3 in place without validating the actual predecessor. |
| I3 | Make Phase 5 explicit and built-in only; do not change auto detection or SDK v1.1. | Let file extensions, Pillow sniffing, or installed plugins silently select image semantics. |
| I4 | Keep encoded-byte identity under `BinaryCompareSpec`; do not add an image alias that returns a different shape for the same fact. | Duplicate byte comparison inside `ImageCompareSpec`. |
| I5 | Limit the first decoded slice to one static PNG using 8-bit `L`, `LA`, `RGB`, or `RGBA` samples. | Start with every Pillow codec, palette/low-bit/16-bit PNG, JPEG, animation, or multipage content. |
| I6 | Compare stored orientation, exact dimensions, native channel order, straight alpha, exact color-description identity, and every decoded sample; perform no implicit conversion. | Auto-rotate, resize, crop, palette-expand, premultiply, color-convert, or ignore interpretation metadata. |
| I7 | Ignore non-interpretive metadata such as DPI, timestamps, comments, and application fields for relation; record only bounded policy facts, never raw metadata. | Make arbitrary metadata part of pixel equality or silently disclose it. |
| I8 | Use deterministic descriptor and fixed-tile changes without raw pixel payloads; complete comparison precedes detail truncation. | Emit one change per pixel, embed images, or let renderers reread inputs. |
| I9 | Define exact count/error metrics and strict equality evaluation; metrics never become hidden normalizations. | Let terminal/HTML recompute scores or infer a verdict. |
| I10 | Emit only full-fidelity complete/truncated results; no fallback, retry, degraded, or partial result in the first slice. | Fall back to binary, another decoder, resized comparison, or incomplete equality. |
| I11 | Emit no artifacts in the first slice. Heatmaps/previews require an explicit host-owned artifact sink/root and renewed RFC 0004 review. | Give comparators or renderers arbitrary filesystem paths. |
| I12 | Treat Pillow as trusted in-process optional code behind an `image` extra, restricted to the PNG decoder and a reviewed version range. | Add Pillow to core, load all registered decoders, or claim sandboxing. |
| I13 | Enforce source, dimension, pixel, decoded-byte, metadata, work, change-item, and payload limits before the next logical allocation/work unit where possible. | Rely only on Pillow's global decompression-bomb threshold or wall-clock timeout. |
| I14 | Use stable unavailable/failed outcomes; corrupt, hostile, or over-limit input is never reported as a content difference. | Return a placeholder `DiffResult` or a best-effort relation. |
| I15 | Use only generated, license-recorded image fixtures and retain exact encoder-independent expected sample matrices. | Commit personal, scraped, competition-restricted, or license-unclear images. |
| I16 | Split image delivery into independently authorized gates; decoded exact PNG is first, perceptual/color/artifact/animation work does not start automatically. | Deliver “image support” as one broad batch. |

## Three different questions

Phase 5 must not use one label for three different predicates.

### Encoded-file identity

The existing `BinaryCompareSpec` answers whether lengths and every encoded byte
are equal. It applies to a PNG, JPEG, or any other file without understanding
the container. Its algorithm, `BinarySpan`, metrics, policy, provenance, and
schema remain governed by RFC 0003.

Two differently compressed PNG files can therefore be binary-different while
decoding to the same sample matrix. That is not a contradiction. The two
outcomes answer different explicit specifications. Phase 5 adds no
`encoded_bytes` image mode and no `platydiff image --encoded` alias.

### Decoded-sample equality

The first image slice answers whether both inputs decode under the selected
profile to the same image descriptor and sample matrix. `relation="equal"`
means all comparison-significant descriptor fields match and every sample at
every `(x, y, channel)` coordinate is identical. The algorithm never uses a
digest alone to establish equality.

This is sample equality, not displayed-color, perceptual, structural, or
metadata equality. An unprofiled image and a profiled image are different under
the accepted native-profile contract even if their integer samples match,
because the samples do not have the same declared interpretation.

### Perceptual similarity

Perceptual equivalence is not part of the first public image spec. A later P5-P
successor must introduce a new schema/spec mode and state that `relation` means
the selected perceptual predicate passed, not pixel identity. It must expose all
thresholds as policy evaluations and preserve exact decoded metrics as facts.
It may not silently replace exact comparison when a backend or budget fails.

Before SSIM is accepted, that successor must freeze: color space and transfer
function; alpha/background treatment; dimension/alignment policy; window size,
weights, sigma, covariance convention, constants, border handling, channel
aggregation, accumulation order, numeric precision, score range, empty/small
image behavior, and inclusive threshold. Learned metrics such as LPIPS require
a further model-weight, license, hash, hardware, determinism, and supply-chain
review. PSNR alone must not be marketed as perceptual equivalence.

## Schema-v4 and compatibility contract

Under accepted decision I2, schema v4 is an additive semantic successor to the
actually merged schema v3:

```python
CompareSpecV4 = CompareSpecV3 | ImageCompareSpec
ChangeV4 = ChangeV3 | ImageChange
```

- Existing built-in text/binary/auto calls remain schema v1.
- Existing SDK-v1.1 text/binary host calls remain schema v2.
- Merged Phase 4 calls remain schema v3 exactly as implemented and verified.
- Every `ImageCompareSpec` outcome is schema v4, including validation,
  sourcing, or resolution failure.
- The v4 reader accepts v1/v2/v3/v4; existing writers remain available.
- Explicit v1/v2/v3-to-v4 upgraders add only documented neutral defaults.
- There is no automatic downgrade. A lossless helper may downgrade only an
  outcome whose facts are representable in the requested older schema.
- Unknown built-in spec/change/transformation IDs remain errors. Namespaced
  extension changes retain RFC 0001 behavior.
- Existing byte-stable fixtures, CLI routes, plugin receipts, and schema-v3
  fixtures remain unchanged.

If the merged P4-A1 schema differs from RFC 0006, Phase 5 stops and amends this
RFC before code. Image implementation may not “reserve” v4 against hypothetical
types or ship image models before the predecessor audit passes.

### Compatibility matrix

| Producer/path | Schema | Image participation | Required behavior |
| --- | --- | --- | --- |
| Existing `compare()` / default CLI | v1 | none | Existing text/binary/auto payloads remain byte-stable. |
| Existing `PluginHost` | v2 | none | SDK v1.1 stays text/binary-only; receipts remain valid. |
| Merged Phase 4 built-ins | v3 | none | Actual v3 models, migration, and fixtures are the predecessor. |
| Accepted built-in image path | v4 | explicit static PNG only | Strict v4 validation and inherited invariants. |
| `PluginHost` with `ImageCompareSpec` | none | unsupported | Python returns resolving-stage unavailable; CLI plugin flags with image are usage exit 2. |
| Existing auto on PNG bytes | v1 | none | Existing text/binary evidence and selection remain unchanged. |
| Future image auto/SDK/perceptual | unspecified | unspecified | Requires a successor RFC and its own schema decision. |

## Public image intent

The accepted normalized public shapes are:

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

Every field is emitted in normalized schema JSON even when it has the only
first-slice value. This makes intended transformations and future migration
explicit. Integers reject booleans and use checked arithmetic. Count-like
public values use the existing exact-integer bound where serialized through the
current numeric model.

`PathSource` and `BytesSource` are supported. `TextSource` fails at `sourcing`
with `source_type_unsupported`; text is not implicitly encoded into an image.
`compare(before, after, spec)` remains the sole built-in Python entry point.
Top-level exports add only accepted spec/limits/enums/change types after the
schema gate; decoder objects, image IR, tile walkers, and Pillow adapters remain
private.

The CLI shape, if its gate is later authorized, is:

```text
platydiff image BEFORE AFTER
platydiff compare --type image BEFORE AFTER
```

Both routes construct the same spec and call the same path. They do not infer a
type or accept plugin, detector, comparator, stdin, URL, directory, recursive,
configuration, artifact, resize, crop, rotate, or color-conversion flags.
Existing exits remain `0/1/2/3`.

## Supported PNG profile

The first decoder accepts a single non-animated PNG datastream whose decoded
mode is exactly one of:

| Mode | Sample layout | Depth | Alpha |
| --- | --- | ---: | --- |
| `L` | grey | 8 bits | none |
| `LA` | grey, alpha | 8 bits each | straight/unassociated |
| `RGB` | red, green, blue | 8 bits each | none |
| `RGBA` | red, green, blue, alpha | 8 bits each | straight/unassociated |

Palette/indexed images, 1/2/4-bit greyscale, 16-bit samples, premultiplied modes,
CMYK, floating point, APNG, multiple frames/pages, and non-PNG codecs are
unsupported in the first slice. PNG `tRNS` transparency that would require
palette or implicit alpha expansion is rejected. A later profile may add an
explicit, recorded expansion, but cannot reinterpret this one.

Before Pillow receives bytes, the host runs the bounded source-level scanner
specified below. It then passes `formats=("PNG",)` to the backend and verifies
the backend-reported format, frame count, animation flag, mode, dimensions, and
interpretation metadata before and after pixel load. A filename extension or
MIME string is never authority. No other globally registered Pillow decoder is
eligible.

### Normative pre-decode PNG scanner

The host scanner, not Pillow, decides whether a datastream is in the first-slice
profile. It consumes only the host snapshot, uses checked unsigned arithmetic,
and completes these checks before `Image.open()`:

1. Verify the eight-byte signature. For every chunk, read the unsigned 32-bit
   big-endian length, four ASCII-letter type bytes, exactly that many data
   bytes, and the CRC-32 over type plus data. Reject truncation, overflow, a
   non-letter type byte, a lowercase reserved third type byte, a bad CRC, data
   after `IEND`, or a missing `IEND`.
2. Require exactly one 13-byte `IHDR` first, at least one consecutive run of
   `IDAT` chunks, and exactly one zero-length `IEND` last. Enforce PNG Third
   Edition ordering, multiplicity, length, and combination rules for every
   recognized chunk. An invalid legal value or invalid chunk structure is
   malformed input, not an unsupported profile.
3. Validate the `IHDR` width/height and compression/filter/interlace fields.
   Legal but unsupported color-type/bit-depth pairs—including 1/2/4-bit
   greyscale, indexed color, and every 16-bit form—are rejected before Pillow.
   Only `(color type, bit depth)` `(0,8)`, `(4,8)`, `(2,8)`, and `(6,8)` map to
   `L`, `LA`, `RGB`, and `RGBA`. Invalid PNG pairs are malformed input.
4. Reject any `tRNS`, `acTL`, `fcTL`, or `fdAT` chunk as an unsupported profile.
   Reject every unknown critical chunk as unsupported. Unknown ancillary chunks
   may be ignored semantically only after their framing, CRC, reserved bit, and
   resource accounting pass.
5. Validate `PLTE` where PNG permits it: at most once, before `IDAT`, with a
   positive length divisible by three and no greater than 768 bytes. It is
   forbidden for color types 0 and 4. Indexed color remains unsupported;
   optional `PLTE` in color types 2 and 6 is non-interpretive.
6. Validate at most one each of `cHRM`, `gAMA`, `iCCP`, `sBIT`, `sRGB`, `cICP`,
   `mDCV`, and `cLLI`, including their normative placement and combinations.
   Their data lengths are respectively 32, 4, variable, mode-dependent
   (1/3/2/4 here), 1, 4, 24, and 8 bytes. Validate registered values and field
   constraints required by PNG Third Edition. `iCCP` profile-name and
   compression framing is validated and its zlib stream is bounded-inflated by
   the host before Pillow; trailing or malformed compressed data is rejected.
7. Bounded-inflate compressed `zTXt` and compressed `iTXt` for accounting and
   validation, then discard it. Validate uncompressed text chunk framing without
   retaining its content. No textual, EXIF, or application payload enters a
   public result.

The scanner classifies bad signature/framing/CRC/order/multiplicity, invalid
PNG values, and malformed compressed metadata as `decode_error`. A valid PNG
feature outside the accepted profile—an allowed low/16-bit pair, indexed color,
`tRNS`, APNG, or unknown critical chunk—is
`unsupported_image_profile`. Crossing a source, metadata, ICC, dimension,
pixel, or decoded-byte limit is `resource_limit_exceeded`. These classifications
are stable and happen at `decoding`; Pillow cannot reclassify or expand the
accepted profile.

### Orientation, color, alpha, and metadata

- `orientation="stored"` compares the decoded matrix in stored row/column
  order. EXIF orientation is not applied or parsed in this slice. Only bounded
  `eXIf` presence and on-wire byte count are recorded in provenance; neither
  raw bytes nor a tag value is retained. This is not a pixel transformation.
  Inputs requiring display-oriented equality need a future explicit
  `apply_exif` profile and transformation record.
- `color_profile="require_exact"` performs no color conversion. The bounded
  canonical description of PNG color-signaling chunks—`cHRM`, `gAMA`, `iCCP`,
  `sBIT`, `sRGB`, `cICP`, `mDCV`, and `cLLI`—including the presence and digest
  of ICC data and the exact bounded values of the other chunks, must match
  before samples are compared.
  Raw profiles are never serialized. A descriptor mismatch is a completed
  difference, not a conversion or decode fallback.
- `alpha="straight"` follows PNG's unassociated alpha. Alpha is compared as a
  channel, and color samples behind a zero-alpha pixel still participate. No
  premultiplication, compositing, background selection, or invisible-RGB
  elision occurs.
- DPI, timestamps, comments, textual chunks, camera/application fields, and
  other non-interpretive metadata do not affect relation. They are neither
  copied into the result nor counted as changes. Their bounded parsing still
  participates in resource enforcement. The project does not call this
  metadata redacted or anonymous.

Dimension, pixel format, or color-description mismatch suppresses sample
comparison because coordinates or sample meanings are not comparable. It
produces a completed `different/fail` result with descriptor changes and zero
compared pixels, not `alignment_failed`.

## Image changes and evidence

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

Descriptor changes require one component, no rectangle, no pixel count, and no
error. They are ordered dimensions, pixel format, then color description.
Unchanged components produce no change. If any descriptor changes, no tile
change is emitted.

For compatible descriptors, the image is partitioned into 64-by-64 tiles from
the top-left; edge tiles use their actual positive dimensions. A tile change is
emitted only when at least one pixel differs. It requires zero-based `(x, y)`,
positive width/height, no component, exact changed-pixel count inside the tile,
and maximum absolute sample error. Tiles are ordered by `y`, then `x`, never
overlap, and stay in bounds. `ChangeSet.total_count` is the full descriptor or
changed-tile count, not the changed-pixel count.

`before_digest` and `after_digest` are lowercase 64-hex SHA-256 values over the
corresponding side. The digest input is frozen as:

```text
RAW_ASCII("platydiff/v4/image/" + domain) || 00 || U64BE(len(payload)) || payload
```

`RAW_ASCII(s)` is exactly the ASCII bytes of `s`. `U64BE` is an unsigned
eight-byte big-endian integer; all lengths and counts use it. The field encoding
`ASCII(s)` is `U64BE(len(s)) || RAW_ASCII(s)`. `U8` is one byte. There is no
Unicode normalization or terminal NUL. The four domain strings are exactly
`descriptor/dimensions`, `descriptor/pixel_format`,
`descriptor/color_description`, and `tile/samples`.

Canonical payloads are:

- dimensions: `U64BE(width) || U64BE(height)`;
- pixel format: `ASCII(mode) || U8(bit_depth) || U8(channel_count) ||`
  `ASCII(band)` for each band in sample order, then `ASCII(alpha)` where alpha
  is exactly `none` or `straight`;
- color description: for each of `cHRM`, `gAMA`, `iCCP`, `sBIT`, `sRGB`,
  `cICP`, `mDCV`, and `cLLI` in that order, append its four type bytes and a
  `U8` presence byte. Absence is `00`. Presence is `01 || U64BE(length) ||`
  canonical value. The canonical value is the validated raw chunk data except
  for `iCCP`, where it is only the bounded decompressed ICC profile bytes; the
  profile name, compression bytes, and chunk CRC are not interpretation facts;
- tile samples: `U64BE(x) || U64BE(y) || U64BE(width) || U64BE(height) ||`
  the pixel-format payload through the final band, followed by the sample bytes.
  Samples are unsigned one-byte values in stored top-to-bottom row order,
  left-to-right pixel order, and declared band order, with no row padding. Tile
  width and height are the actual edge dimensions.

The following normative vector uses a 1-by-1 `RGBA`, 8-bit, straight-alpha
image, no color-description chunks, and tile samples `00 7f ff 80`:

| Domain | Payload hex | SHA-256 |
| --- | --- | --- |
| `descriptor/dimensions` | `00000000000000010000000000000001` | `37b783ef79ab757a531e50f76237eb9c870203f7003c5b9dcfc0280ded598a12` |
| `descriptor/pixel_format` | `000000000000000452474241080400000000000000015200000000000000014700000000000000014200000000000000014100000000000000087374726169676874` | `9e7453f90b6a38c85e068b2aaa31ee0836422caf523192cdd8c39faa9021bf0c` |
| `descriptor/color_description` | `6348524d0067414d410069434350007342495400735247420063494350006d44435600634c4c4900` | `71d104a33d792f584bb9f5ed92ab1feee8625a59b3012513d08d905fa4a08145` |
| `tile/samples` | `00000000000000000000000000000000000000000000000100000000000000010000000000000004524742410804000000000000000152000000000000000147000000000000000142000000000000000141007fff80` | `85c3961556e42038b134b2a3864231be5e533aad78c1cb68d95210f5d2b5fa55` |

These digests detect serialization mistakes; they do not establish equality,
conceal low-entropy content, or authorize a renderer to fetch source pixels. A
tile item contains no raw or encoded pixels.

The comparator computes every descriptor/tile fact and total before retaining a
bounded row-major prefix. Truncation uses whole items and the inherited exact
canonical-payload accounting. It changes neither relation, verdict, fidelity,
metrics, nor totals. Phase 5 never emits `partial`.

`DiffSummary.change_count` equals `image.changed_items` and
`ChangeSet.total_count`. Summary counts, in stable name order, are
`changed_pixels` with unit `pixels`, `changed_tiles` with unit `tiles`, and
`descriptor_changes` with unit `items`. On descriptor mismatch,
`changed_pixels` and `changed_tiles` are zero because no comparable sample pair
was evaluated; this does not imply that the images are equal.

## Metrics, relation, and policy

Metric order and meanings are fixed:

| Metric | When present | Unit | Direction | Aggregation |
| --- | --- | --- | --- | --- |
| `image.compared_pixels` | always | `pixels` | `neutral` | `count` |
| `image.equal_pixels` | always | `pixels` | `neutral` | `count` |
| `image.changed_pixels` | always | `pixels` | `lower_is_better` | `count` |
| `image.compared_samples` | always | `samples` | `neutral` | `count` |
| `image.changed_items` | always | `items` | `lower_is_better` | `count` |
| `image.mean_absolute_error` | compatible descriptors and at least one sample | `sample_levels` | `lower_is_better` | `mean` |
| `image.root_mean_square_error` | same | `sample_levels` | `lower_is_better` | `root_mean_square` |
| `image.peak_signal_to_noise_ratio` | same | `decibels` | `higher_is_better` | `peak_signal_to_noise_ratio` |

When descriptors are compatible, equal plus changed pixels equals compared
pixels; compared samples equals compared pixels times channel count. A pixel is
changed when at least one channel differs. MAE and RMSE aggregate absolute and
squared errors over every sample in row-major pixel and declared channel order.
The peak sample value is 255. PSNR is positive infinity when MSE is zero and
otherwise `10 * log10(255**2 / MSE)`.

The metric operation order is normative. For each sample pair in stored
row-major/band order, let `difference = int(before) - int(after)`, then update
the checked arbitrary-precision integer accumulators
`absolute_sum += abs(difference)` and
`squared_sum += difference * difference`. Pixel-change counting is also integer
and is completed before any floating operation. After all `sample_count`
samples, perform these binary64 operations in exactly this order:

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

MAE and RMSE are always `FiniteValue`; PSNR is `PositiveInfinityValue` only
when `squared_sum == 0`. This slice never emits `NaNValue` or
`NegativeInfinityValue`. It does not use chunk-local floating partials,
`math.fsum`, decimal arithmetic, fused operations, or presentation-rounded
values for stored metrics. For sample pairs `[0, 255]` and `[0, 0]`, the
normative facts are `absolute_sum=255`, `squared_sum=65025`,
`sample_count=2`, MAE `127.5`, RMSE `180.31222920256963`, and PSNR
`3.010299956639812` on the reviewed Python binary64 path.

Repeated runs on the same supported runtime must serialize byte-identically.
Cross-platform golden tests require absolute distance no greater than
`8 * math.ulp(expected)` for finite `sqrt`/`log10` results; zero and exact rational results compare
exactly, and infinity compares by its exact tagged representation. This testing
tolerance is not a comparison policy tolerance. Threshold evaluation, if a
future schema adds it, uses the stored unrounded binary64 result; rounding is
presentation only. The first slice has no content tolerance.

`relation="equal"` exactly when `image.changed_items == 0`; otherwise it is
`different`. The sole evaluation is `image.decoded_sample_equality`, observing
`image.changed_items` with operator `eq` and threshold zero. Pass means zero and
fail means non-zero. No default rule yields warn. Fidelity is always full.

## Provenance vocabulary

The normalized spec records all defaults. Actual behavior uses these stable
transformation records in this order:

| Stage | Transformation ID | Required parameters |
| --- | --- | --- |
| decoding | `image.png.decode` | backend/version, profile, mode, dimensions, frame count, IHDR bit depth/color type/interlace, and bounded resource facts per role |
| normalizing | `image.orientation.stored` | before/after `eXIf` presence and on-wire byte count |
| normalizing | `image.color.native_exact` | bounded color-description identity/digest per role |
| normalizing | `image.alpha.straight` | channel layout and unassociated-alpha policy |
| aligning | `image.coordinates.exact` | origin=`top_left`, x=`right`, y=`down`, dimensions policy |

These records make no claim that a conversion occurred. They state the profile
that actually executed. No record may contain raw ICC/EXIF/text metadata, an
absolute path, source bytes, local module paths, or backend exception text.

The exact `ResourceUsage.name` values are
`image.{before|after}.{input_bytes|metadata_wire_bytes|metadata_decompressed_bytes|icc_profile_bytes|pixels|decoded_bytes}`,
`image.compare.sample_pairs`, `image.changes.items`, and
`image.changes.payload_bytes`. Each uses its matching normalized-spec limit;
the six source facts and their limits apply independently to `before` and
`after`. Only counts, booleans, dimensions, stable enum values, and descriptor
digests enter public/provenance data. Raw or excerpted chunk payloads, profile
names, text keywords/values, EXIF values, and palette entries do not.

Comparison provenance records input hashes, comparator
`image.decoded_samples`, algorithm `image.decoded_samples.tiles.v1`, Platydiff
implementation version, Pillow version, relevant linked library versions where
available, normalized spec, and every configured/effective/used resource.

## Optional backend review

The candidate dependency is `Pillow>=12.3,<13` in an optional `image` extra.
The range is provisional until the implementation gate repeats the review.

- Purpose: bounded PNG identification and sample decoding.
- Optionality: imported only after explicit image resolution; installing it
  cannot alter text, binary, auto, or plugin behavior.
- License: MIT-CMU according to project metadata and license text; NOTICE/SBOM
  treatment and bundled native-library licenses remain an implementation gate.
- Size/platform: official 12.3.0 metadata supports Python 3.10+ and publishes
  platform wheels; exact wheel/source sizes and supported targets are recorded
  for the chosen build.
- Security: 12.3.0 fixes multiple 2026 memory-safety and denial-of-service
  issues affecting older versions. Advisories must be rechecked at lock/merge
  time. A pinned hash and isolated environment are deployment concerns.
- Alternatives: a standard-library PNG decoder would enlarge the security and
  maintenance surface; OpenCV adds a much heavier native dependency; external
  ImageMagick introduces subprocess/policy/version complexity. Neither is a
  silent fallback.

Pillow is trusted in-process code and includes native decoders. Its
decompression-bomb warning is useful defense in depth, not the resource
contract. The host keeps its own lower per-run limits, treats every
`DecompressionBombWarning` as an error, never disables `MAX_IMAGE_PIXELS`, and
passes an exact format allowlist. Pillow's global mutable format registry is a
remaining in-process trust risk; implementation must audit the selected PNG
factory identity or use an isolated environment before making a support claim.

## Resources, hostile input, and failures

`max_input_bytes` is enforced while the host creates the immutable snapshot and
before decode. The PNG scanner increments `metadata_wire_bytes` by each
ancillary chunk's declared data length before reading or retaining its data;
`IDAT` and critical `PLTE` are excluded, while color, text, `eXIf`, and unknown
ancillary chunks are included. Chunk headers and CRC bytes remain covered by
`max_input_bytes`, not the metadata subtotal.

`metadata_decompressed_bytes` is the sum of decompressed payload bytes from
`iCCP`, compressed `iTXt`, and `zTXt`. The scanner checks both the aggregate
`max_metadata_decompressed_bytes` and, for `iCCP`, the independent
`max_icc_profile_bytes`. ICC bytes count against both limits; they are not
double-counted within either counter. Each declared on-wire increment is
checked before reading that chunk. Each inflate increment is checked before
appending or exposing the next output block; text output is discarded, and an
ICC buffer never grows beyond its dedicated limit. A truncated stream,
trailing compressed stream data, or invalid compression method is a decode
error, while exceeding any counter is a resource-limit failure.

Width, height, pixel product, channel count, and decoded-byte products use
checked arithmetic as soon as `IHDR` is validated and before Pillow. Backend
mode/dimensions and the same products are rechecked before and after `load()`.
Comparison work is checked before each sample pair; change-item and canonical
payload totals are checked before retaining the next whole item. No check is
deferred merely because Pillow also exposes a limit or warning.

One comparison work unit is one sample-pair equality/error update. The default
`67_108_864` units admits the maximum configured pixel count in four-channel
RGBA; callers may explicitly lower or raise the limit within exact-integer
bounds. The check happens before the next unit. A
limit reached before complete comparison returns failed
`compare_resource_limit`, never a partial relation.

Pillow may allocate parser/native temporary memory before a host check can
observe it. In-process logical limits therefore do not constitute a hard memory
sandbox. The implementation gate must measure representative peak memory and
document this residual risk. Hard containment for untrusted images requires a
future process-isolation contract.

Stable mappings are:

| Scenario | Outcome/code | Stage |
| --- | --- | --- |
| Optional backend missing/incompatible | unavailable/`backend_unavailable` | resolving |
| No built-in image capability | unavailable/`capability_unavailable` | resolving |
| Unsupported source kind | failed/`source_type_unsupported` | sourcing |
| Wrong codec/profile, animation, unsupported mode/depth/transparency | failed/`unsupported_image_profile` (415) | decoding |
| Malformed/truncated PNG or invalid interpretation metadata | failed/`decode_error` | decoding |
| Source/decode/metadata/pixel limit or decompression-bomb signal | failed/`resource_limit_exceeded` | observed stage |
| Comparison work limit | failed/`compare_resource_limit` | comparing |
| Source mutation or I/O error | existing stable code | observed stage |
| Dimension/format/color descriptor mismatch | completed/different/fail | aggregating after comparison facts |
| Unexpected CLI exception | failed/`internal_error` | outer CLI boundary |

No decode or comparison failure falls back to binary, another Pillow decoder,
resizing, color conversion, or a different provider. `KeyboardInterrupt`,
`SystemExit`, `MemoryError`, and programming defects retain existing library
boundaries.

## Artifacts and human review

The first slice returns `artifacts=()`. A tile change plus metrics is enough for
machine evidence and bounded terminal/JSON presentation, but it is not a visual
preview. The existing terminal renderer may display descriptor/tile coordinates
and metrics only after its schema-v4 gate. It does not open source files.

Heatmaps, overlays, thumbnails, before/after previews, and self-contained image
reports are deferred together. A successor must define:

- explicit user request and confidentiality warning;
- host-owned `ArtifactSink`/root authority, atomic publication, byte/count/pixel
  limits, media allowlist, SHA-256 verification, cleanup, and no-clobber rules;
- whether output encodes source-derived pixels and how alpha/color are handled;
- deterministic heatmap scale, legend, dimensions, and algorithm identity;
- RFC 0001 `ArtifactRef` URI validation and RFC 0004 view-model behavior;
- proof that renderers consume validated references without arbitrary reads or
  writes, and that HTML embedding does not bypass CSP or disclosure policy.

Accepting image comparison does not authorize UI-U1/U2/U3. Image evidence may
inform a future RFC 0004 revision, especially side-by-side layout, synchronized
zoom, pixel coordinates, and artifact disclosure.

## Corpus, determinism, and platform evidence

Fixtures are generated by repository-owned scripts or embedded from documented
public-domain/explicitly redistributable sources. Each fixture records source,
generator version, license, dimensions, mode, profile, expected sample matrix,
and SHA-256. Tests must not derive their oracle solely from Pillow; small PNGs
use independently specified expected samples and malformed byte fixtures.

The acceptance matrix includes:

- equal/different/minimal one-pixel content, one pixel/channel change, edge
  tiles, all supported modes, transparent RGB, and descriptor mismatches;
- palette, low/16-bit, `tRNS`, APNG, wrong codec, corrupt chunks, truncation,
  CRC/order/multiplicity faults, unknown critical chunks, oversized
  dimensions/pixels, exact wire/decompressed/ICC limit boundaries, and
  decompression bombs; these tests assert pre-Pillow rejection and stable codes;
- byte-different/pixel-equal pairs proving the binary/image distinction;
- all four digest fixtures byte-for-byte; metric formulas, tagged PSNR infinity,
  eight-ULP cross-platform goldens, integer/floating order, change invariants,
  item/payload truncation, exact budget boundaries, and repeated determinism;
- source mutation, no path reopen, backend missing/version mismatch, global
  decoder-registry tampering, and no fallback;
- v1/v2/v3 fixtures, v4 round trips/migration, unknown kinds/versions, public
  exports, terminal safety, CLI aliases/exits, and package contents;
- representative peak memory and runtime on Linux/Python 3.12. Each additional
  platform requires its own wheel/native-library and deterministic-output
  evidence before support is claimed.

## Independent delivery gates and commits

These are plans, not authorization. No gate starts automatically.

### P5-R: predecessor and dependency revalidation

No product commit. Confirm P4-A1/schema v3 is merged and map its actual models,
serializers, migrations, renderers, tests, and docs to RFC 0006. Repeat Pillow
version/advisory/license/wheel/native-library review. Any mismatch blocks Phase
5 and returns to this RFC.

### P5-A1: schema v4 image contracts

1. `feat(core): add schema-v4 image comparison contracts`
2. `test(core): add schema-v4 compatibility and migration fixtures`

Gate: v1/v2/v3 fixtures remain stable; all image spec/change/metric/provenance
invariants round-trip; no decoder, Pillow dependency, CLI route, image plugin,
auto detection, artifact, or UI exists.

### P5-A2: optional static PNG decoding

1. `build(image): add the reviewed optional Pillow backend`
2. `feat(image): add bounded static PNG decoding`
3. `test(image): add PNG profile and hostile-input coverage`

Gate: exact decoder allowlist, supported-profile checks, limits, mutation,
missing/incompatible backend, advisory/license inventory, peak memory, and
unchanged default imports/auto behavior pass. No comparison result is claimed.

### P5-A3: decoded-sample comparison and CLI

1. `feat(image): add exact decoded-sample comparison`
2. `feat(cli): add explicit image comparison commands`
3. `docs: document the first image comparison slice`

Gate: relation, changes, metrics, policy, provenance, truncation, safe rendering,
aliases/exits, determinism, and cross-schema compatibility pass. Full Ruff
format/lint, strict mypy, complete pytest, build, wheel/sdist inspection, link
checks, CI, and independent RFC-to-code review are green.

### Later independent callbacks

- **P5-C:** explicit color conversion and display-oriented transforms, only
  after ICC/Exif algorithms, dependencies, deterministic provenance, and
  compatibility are accepted.
- **P5-P:** perceptual comparison, only after the complete SSIM/threshold
  contract above is accepted in a schema successor.
- **P5-F:** JPEG and other still formats, independently reviewed per codec and
  native-library security/determinism surface.
- **P5-M:** APNG, GIF, TIFF, or other frame/page sequences, only after timeline,
  disposal/blend, duration, frame-alignment, limits, and change semantics exist.
- **P5-H:** heatmap/preview artifacts, only after artifact authority and RFC
  0004 presentation contracts are accepted.
- **P5-S:** SDK v2 image plugins and automatic image detection, only through
  successors to RFC 0005 and RFC 0003.

## Rejected alternatives

### Use Pillow's default `Image.open()` behavior as the contract

Rejected because it sniffs every registered codec, has a mutable global
registry, may apply backend-specific mode behavior, and cannot express
Platydiff's explicit resource, provenance, or schema guarantees.

### Convert every input to RGBA/sRGB automatically

Rejected because palette expansion, color management, bit-depth reduction,
orientation, and alpha conversion can discard or reinterpret information. Such
transforms require explicit intent and provenance.

### Put a thumbnail or heatmap directly in `DiffResult`

Rejected because the current API has no artifact authority, output root, or
safe publication lifecycle, and inline pixels would defeat bounded/privacy
contracts.

### Make SSIM the default relation

Rejected because SSIM depends on a fully specified viewing/sample profile and
threshold, is not pixel equality, and needs independent algorithm evidence.

## Consequences

The first image slice is smaller than users may expect from “image diff,” but
its truth is precise: byte identity remains binary, decoded-sample identity is
auditable, and perceptual similarity is not implied. Restricting codec, mode,
transform, artifact, and plugin scope keeps security and compatibility claims
testable. The cost is that common palette, JPEG, oriented-photo, color-managed,
animated, and visual-report workflows wait for measured, independently approved
follow-up gates.

## References

- [RFC 0001: Comparison outcome and diff result](0001-comparison-outcome-and-diff-result.md)
- [RFC 0003: Detection, resolution, and exact binary comparison](0003-automatic-detection-capability-resolution-and-binary-comparison.md)
- [RFC 0004: Human review UI and renderer boundary](0004-human-review-ui-and-renderer-boundary.md)
- [RFC 0005: Third-party plugin SDK and compatibility](0005-third-party-plugin-discovery-sdk-and-compatibility.md)
- [RFC 0006: Structured data comparison](0006-structured-data-comparison.md)
- [W3C PNG Specification, Third Edition](https://www.w3.org/TR/png-3/)
- [Pillow 12.3.0 project metadata](https://pypi.org/project/pillow/)
- [Pillow image-open contract](https://pillow.readthedocs.io/en/stable/reference/Image.html)
- [Pillow security guidance](https://pillow.readthedocs.io/en/stable/handbook/security.html)
- [Pillow image concepts](https://pillow.readthedocs.io/en/stable/handbook/concepts.html)
- [Pillow image-format documentation](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
- [Pillow security advisories](https://github.com/python-pillow/Pillow/security/advisories)
- [Pillow MIT-CMU license](https://github.com/python-pillow/Pillow/blob/main/LICENSE)
- [ICC.1:2022 color-management specification](https://www.color.org/specification/ICC.1-2022-05.pdf)
- [Wang et al., “Image quality assessment: from error visibility to structural similarity”](https://www.colorado.edu/lab/live/publications/zwang_ssim_ieeeip2004.pdf)
