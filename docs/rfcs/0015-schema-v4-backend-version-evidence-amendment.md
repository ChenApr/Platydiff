# RFC 0015: Schema-v4 Backend-Version Evidence Amendment

[Chinese documentation](0015-schema-v4-backend-version-evidence-amendment_zh.md)

- Status: Proposed
- Date: 2026-09-11
- Decision IDs: BVE-1-BVE-8
- Owners: Platydiff maintainers
- Amends: [RFC 0013](0013-p5a1-image-wire-contract-amendment.md)
- Related RFCs: [RFC 0005](0005-third-party-plugin-discovery-sdk-and-compatibility.md),
  [RFC 0007](0007-image-comparison.md),
  [RFC 0008](0008-source-code-and-pdf-comparison.md), and
  [RFC 0009](0009-audio-and-video-comparison.md)
- Evidence baseline: `main` at `84c06d3`
- Existing implementation authorization: the user separately authorized P5-A1
  on 2026-09-11 and implementation is in progress; this RFC grants no new
  authority, and the P5-A1 merge remains blocked until this amendment is
  accepted and implemented

## Summary and authorization boundary

RFC 0013 requires schema-v4 attempts with a non-null backend ID to carry a
non-null backend version and requires a null backend ID to carry a null backend
version. It also requires every valid v1, v2, and v3 outcome to upgrade to v4
without losing or inventing wire facts. Those requirements conflict with the
implemented predecessor.

The implemented schema-v1 text pipeline records a selected attempt with
`backend_id="stdlib"`; schema v1 has no backend-version member. The implemented
v1-to-v2 upgrader preserves that ID, records the comparator version as the
capability version for completed outcomes, and leaves `backend_version=null`.
Schema-v2 and schema-v3 built-in attempts also permit either backend field to
be absent independently. Consequently a blanket v4 pairing requirement cannot
accept every valid predecessor attempt.

This proposed amendment adds a closed, explicit evidence state to each
schema-v4 attempt. It preserves predecessor facts without inventing a version
or deleting an ID, while keeping native schema-v4 producers on the strict
paired-backend rule. The user separately authorized P5-A1 implementation on
2026-09-11, and that work is in progress. This RFC does not expand that
authorization and does not authorize image runtime work, P5-A2/P5-A3, Phase 6,
Phase 7, artifacts, automatic detection, plugins, or UI.

P5-A1 must not merge while this RFC is Proposed. If BVE-1 through BVE-8 are
accepted, the existing P5-A1 authorization continues to cover implementation
of this exact amendment together with the rest of RFC 0013; the implementation
still requires separate code review and may not expand its existing scope.

## Predecessor evidence and contradiction

The relevant implemented v1 attempt is equivalent to:

```json
{
  "backend_id": "stdlib",
  "capability_id": "text",
  "disposition": "selected",
  "reason_code": null
}
```

After the exact v1-to-v2 upgrade of a completed text outcome, its seven
schema-v2 fields include:

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

The version string is evidence from the current baseline, not a permanently
frozen project version. The invariant is that `capability_version` may be
non-null while the predecessor has no backend-version fact.

`CapabilityAttemptV2` validates backend ID/version pairing only for a
provider-backed attempt. A built-in attempt with no provider can therefore
carry any of the four nullability pairs. A lossless v3-to-v4 migration must
cover all four, including the unusual but valid predecessor shape with a null
backend ID and non-null backend version. This RFC closes both asymmetric cases
rather than special-casing the current text fixture.

The following are rejected resolutions:

- synthesizing `"unknown"`, the Python version, the Platydiff version, or any
  other backend version;
- clearing `backend_id="stdlib"` or discarding a predecessor backend version;
- accepting unpaired backend identity as ordinary native-v4 provenance; or
- making the promised predecessor upgrades partial or silently fallible.

## Proposed decisions

| ID | Proposed decision |
| --- | --- |
| BVE-1 | Add the public `BackendVersionEvidence` `StrEnum` with exactly `not_applicable`, `recorded`, and `predecessor_unpaired`. |
| BVE-2 | Add required schema-v4 wire member `backend_version_evidence` to every `CapabilityAttemptV4`; retain `backend_components` and all seven inherited fields. |
| BVE-3 | Permit `predecessor_unpaired` only as an explicit migration declaration for a provider-free attempt with exactly one non-null backend identity field and no components. |
| BVE-4 | Require native v4 producers to emit only `not_applicable` or `recorded`; they may not use `predecessor_unpaired`. |
| BVE-5 | Derive the evidence state during every v1/v2/v3-to-v4 upgrade without changing an inherited field. |
| BVE-6 | Treat the evidence state as a derived v4 encoding fact during a representable v4-to-v3 downgrade; preserve the two predecessor backend fields exactly. |
| BVE-7 | Add the field to both schema-v4 canonical fixtures and freeze the exact key set, canonical order, rejection matrix, migration fixtures, and predecessor-byte stability tests below. |
| BVE-8 | Require schema v5 and v6 to inherit and preserve the corrected v4 evidence contract; this requirement grants no successor implementation authority. |

## Public model and closed states

The proposed public additions are:

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

The Python default makes a backend-free direct schema specimen concise. It
does not make the JSON member optional. The schema-v4 reader requires the
member, and the constructor validates it against the other attempt fields.
`BackendVersionEvidence` is foundational and is exported from
`platydiff.core.models` and `platydiff.core`, not from the curated top-level
package.

Exactly these combinations are valid:

| Evidence | `backend_id` | `backend_version` | `provider` | `backend_components` | Origin |
| --- | --- | --- | --- | --- | --- |
| `not_applicable` | null | null | null or non-null | empty | Native v4 or upgrade |
| `recorded` | non-null | non-null | null or valid provider | empty or valid sorted components | Native v4 or upgrade |
| `predecessor_unpaired` | exactly one backend field is non-null | exactly one backend field is non-null | null | empty | Explicit v1/v2/v3-to-v4 upgrade only |

For the last row, “exactly one” applies to the pair
`(backend_id, backend_version)`: one value is non-null and the other is null.
The two table cells intentionally describe the same XOR constraint.

All other combinations are invalid. In particular, components require a
`recorded` backend ID/version pair; provider-backed attempts remain subject to
the inherited pairing rule and can never be `predecessor_unpaired`.
`capability_version` does not participate in these three states and is
preserved independently.

`predecessor_unpaired` is a wire declaration made by a migration producer.
Like comparator version, provider identity, hashes, and other provenance, a
detached reader validates its closed shape but cannot independently prove the
producer's history. Project-owned native-v4 writers and outcome factories must
never originate that state. Tests enforce that producer obligation.

## Exact wire keys and canonical order

The schema-v4 attempt object has exactly nine required members. Because the
RFC 0013 canonical writer recursively sorts object keys lexicographically,
their exact canonical order is:

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

Readers remain object-order-insensitive but reject any missing or unknown
member. Schema-v1 readers accept only their existing four attempt keys;
schema-v2 and schema-v3 readers accept only their existing seven keys. They
reject both `backend_components` and `backend_version_evidence`. The
schema-v4 reader requires both additional keys and rejects an unknown evidence
value rather than treating it as a future extension.

RFC 0013 statements that `backend_components` is the sole new attempt member
are replaced by this RFC: schema v4 adds exactly those two members. The
version-explicit attempt serializer and reader signatures remain otherwise
unchanged.

## Upgrade contract

The exact compositions in RFC 0013 remain:

```text
upgrade_outcome_v3_to_v4(v3) -> v4
upgrade_outcome_v2_to_v4(v2) = upgrade_outcome_v3_to_v4(upgrade_outcome_v2_to_v3(v2))
upgrade_outcome_v1_to_v4(v1) = upgrade_outcome_v2_to_v4(upgrade_outcome_v1_to_v2(v1))
```

For each predecessor attempt, the v3-to-v4 step preserves all seven fields,
sets `backend_components=[]`, and derives exactly one evidence value:

| Predecessor pair `(backend_id, backend_version)` | V4 evidence |
| --- | --- |
| `(null, null)` | `not_applicable` |
| `(non-null, non-null)` | `recorded` |
| Exactly one value non-null | `predecessor_unpaired` |

The helper does not infer provenance from capability ID, capability version,
the Python runtime, installed distributions, or the current Platydiff version.
It does not modify provider, disposition, reason, or ordering. The same mapping
applies to completed, unavailable, and failed outcomes.

## Downgrade contract

`downgrade_outcome_v4_to_v3` retains every representability rejection in RFC
0013, including image-only facts, `unsupported_image_profile`, and non-empty
backend components. When all those gates pass, it validates the evidence state,
drops only `backend_version_evidence`, and preserves `backend_id` and
`backend_version` exactly.

Dropping the field is lossless because, for a v4 attempt eligible for downgrade,
the evidence value is uniquely derived from the two preserved predecessor
fields by the upgrade table above. Re-upgrading the resulting v3 attempt
restores the same evidence state. A downgrade does not manufacture a backend
pair and does not reject an otherwise representable `predecessor_unpaired`
attempt.

## Canonical fixtures and compatibility tests

The two schema-v4 contract specimens required by RFC 0013 remain the only
P5-A1 canonical v4 JSON files. Their backend-free image attempts add:

```json
"backend_version_evidence": "not_applicable"
```

Their exact bytes and expected digests are frozen only after this field is
present. Existing schema-v1, schema-v2, and schema-v3 fixture bytes and digests
must not change.

The P5-A1 implementation gate adds tests that prove:

1. the actual v1 text outcome with `backend_id="stdlib"` upgrades through v2
   and v3 to a v4 `predecessor_unpaired` attempt without changing inherited
   fields;
2. all four predecessor backend nullability pairs map according to the upgrade
   table, including a provider-free reverse-unpaired v2/v3 specimen;
3. each upgraded completed, unavailable, and failed shape round-trips through
   the schema-v4 writer and reader;
4. every representable upgraded attempt downgrades to byte-equivalent v3
   backend fields and re-upgrades to the same evidence state;
5. the two image contract fixtures use `not_applicable`, contain the exact nine
   attempt keys, and retain all RFC 0013 image bindings;
6. a directly constructed versioned native-v4 backend uses `recorded`;
7. mismatched evidence, unpaired native-v4 producer output, provider-backed
   unpaired identity, components without `recorded`, missing keys, extra keys,
   and unknown evidence strings are rejected; and
8. every existing v1-v3 fixture remains byte-identical and every predecessor
   reader rejects the two v4-only attempt members.

Normal project checks and RFC 0013's complete P5-A1 acceptance matrix remain
required. These tests add no image decoder, backend, runtime registration, or
CLI route.

## Public-model and serialization validation layers

RFC 0013's image cross-field invariants apply to direct construction of the
public `DiffResultV4`; they are not deferred wholesale to serialization. When
`provenance.spec.kind="image"`, `DiffResultV4.__post_init__()` must reject an
empty, missing, duplicate, extra, or incorrectly ordered image `resources`
tuple. It requires the complete RFC 0007 resource-name set:

```text
image.{before|after}.{input_bytes|metadata_wire_bytes|
metadata_decompressed_bytes|icc_profile_bytes|pixels|decoded_bytes}
image.compare.sample_pairs
image.changes.items
image.changes.payload_bytes
```

The public-model layer also validates every cross-field relationship that can
be computed from model values: normalized-spec limits, per-role decode facts,
dimensions and channel arithmetic, comparison counts, change-item counts,
summary/metric/evaluation bindings, ordering, and the evidence-state matrix in
this RFC. Therefore a directly constructed image `DiffResultV4` with empty
resources is invalid even before a writer is called.

Only a relationship that depends on the exact versioned JSON representation is
serializer-boundary validation. Specifically,
`image.changes.payload_bytes.used` must equal the sum of
`serialized_change_size(item, schema_version=4)` for retained changes. The v4
encoder checks this before emitting bytes; the v4 reader checks it after
version-explicit decoding and before returning the outcome. Direct construction
can validate that the resource exists, is uniquely ordered, has the normalized
limit, and carries a non-negative value, but it does not claim that payload-byte
equality has been established until that serializer-boundary check runs. The
canonical fixture construction test must exercise both layers.

## Schema-v5 and schema-v6 inheritance

Schema-v5 source/PDF and schema-v6 audio are successors of the corrected v4
contract. Their future attempt models, exact readers/writers, upgrade helpers,
and compatibility fixtures must carry `backend_version_evidence` unchanged.
A successor-native producer obeys the same native rule and cannot originate
`predecessor_unpaired`; a migration chain preserves that declared predecessor
state.

Before P6-C0 begins, its coordinator must revalidate the merged schema-v4
reader, writer, all predecessor upgrades, downgrade, and fixtures against this
RFC. Before the Phase 7 schema-v6 closure or implementation begins, it must do
the same for the merged v4/v5 chain. No source-code, PDF, audio, or video
comparison semantics are changed, and this RFC does not satisfy either phase's
implementation gate.

## Alternatives considered

### Execution-level migration marker

An outcome-level or execution-level predecessor marker could gate the
exception with fewer repeated wire fields. It would make a detached
`CapabilityAttemptV4` unable to validate itself, would be coarse for mixed
attempt histories, and would complicate exact composed upgrades. Per-attempt
evidence keeps the public attempt contract closed.

### Relax the native-v4 pairing rule

Allowing any provider-free, component-free unpaired attempt requires no new
wire key, but a detached reader cannot distinguish a migrated predecessor from
under-specified native-v4 provenance. This loses the evidence quality RFC 0013
intended to add.

### Reject or rewrite predecessor facts

Partial upgrades, invented version strings, or cleared IDs violate the
accepted lossless-migration rule. They are not compatibility strategies.

## Acceptance and merge gate

This RFC is Proposed. Human acceptance of BVE-1 through BVE-8 is required
before its status can become Accepted. The documentation amendment must merge
before P5-A1. The implementation owner must then either create a replacement
P5-A1 branch from the amended `main` or merge the amended `main` into the
existing P5-A1 branch without rewriting history. The branch implements the
exact contract, regenerates only schema-v4 fixtures, and passes the full Python
and compatibility checks before its own review. Rebase, force-push, and other
shared-history rewriting are prohibited.

Acceptance of this RFC does not create new implementation authority; the
user's existing 2026-09-11 P5-A1 dispatch remains the sole authority for the
in-progress contract-only implementation. No later phase may treat Proposed
text or an unmerged P5-A1 branch as predecessor evidence.
