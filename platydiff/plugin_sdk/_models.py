"""Immutable declarations for the Platydiff plugin SDK v1."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, Protocol

from platydiff.core.models import (
    ArtifactRef,
    BinaryCompareSpec,
    ChangeSet,
    Diagnostic,
    DiffSummary,
    Fidelity,
    JsonObject,
    Metric,
    PolicyEvaluation,
    Relation,
    ResourceUsage,
    SourceKind,
    TextCompareSpec,
    TransformationRecord,
    Verdict,
)

PLUGIN_ENTRY_POINT_GROUP = "platydiff.plugins.v1"
PLUGIN_MANIFEST_SCHEMA_VERSION: Literal[1] = 1
PLUGIN_API_MAJOR: Literal[1] = 1
PLUGIN_API_MINOR = 1
HOST_FEATURES_V1: tuple[str, ...] = ("host.execution.v1",)

_MAX_EXACT_INTEGER = 2**53
_MAX_IDENTIFIER_BYTES = 255
_MAX_TEXT_BYTES = 1024
_PLUGIN_ID = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)+$")
_STABLE_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_DISTRIBUTION_NAME = re.compile(
    r"^(?:[A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9])\Z"
)


def _bounded_text(value: object, field_name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise ValueError(
            f"{field_name} must contain valid Unicode scalar values"
        ) from error
    if (not allow_empty and not value) or len(encoded) > _MAX_TEXT_BYTES:
        qualifier = "non-empty and " if not allow_empty else ""
        raise ValueError(
            f"{field_name} must be {qualifier}at most {_MAX_TEXT_BYTES} UTF-8 bytes"
        )
    if any(
        ord(character) < 0x20 or 0x7F <= ord(character) <= 0x9F for character in value
    ):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _identity_text(value: object, field_name: str, *, allow_empty: bool = False) -> str:
    text = _bounded_text(value, field_name, allow_empty=allow_empty)
    if "/" in text or "\\" in text:
        raise ValueError(f"{field_name} must not contain a filesystem path")
    return text


def _stable_identifier(value: object, field_name: str) -> str:
    text = _bounded_text(value, field_name)
    if len(
        text.encode("utf-8")
    ) > _MAX_IDENTIFIER_BYTES or not _STABLE_IDENTIFIER.fullmatch(text):
        raise ValueError(f"{field_name} must be a stable lowercase ASCII identifier")
    return text


def _plugin_identifier(value: object, field_name: str = "plugin_id") -> str:
    text = _bounded_text(value, field_name)
    if len(text.encode("utf-8")) > _MAX_IDENTIFIER_BYTES or not _PLUGIN_ID.fullmatch(
        text
    ):
        raise ValueError(f"{field_name} must be a lowercase reverse-domain identifier")
    return text


def _plugin_scoped_identifier(value: object, field_name: str, plugin_id: str) -> str:
    text = _stable_identifier(value, field_name)
    if not text.startswith(f"{plugin_id}."):
        raise ValueError(f"{field_name} must use the plugin_id prefix")
    return text


def _bounded_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    if not 0 <= value <= _MAX_EXACT_INTEGER:
        raise ValueError(f"{field_name} must be in 0..{_MAX_EXACT_INTEGER}")
    return value


def _string_tuple(
    value: object,
    field_name: str,
    *,
    identifiers: bool = False,
    path_free: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        if identifiers:
            normalized.append(_stable_identifier(item, field_name))
        elif path_free:
            normalized.append(_identity_text(item, field_name))
        else:
            normalized.append(_bounded_text(item, field_name))
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized))


class CapabilityKind(StrEnum):
    """The three capability roles reserved by SDK v1."""

    DETECTOR = "detector"
    COMPARATOR = "comparator"
    RENDERER = "renderer"


class ComponentKind(StrEnum):
    """Inventory-only native and external component categories."""

    NATIVE = "native"
    EXTERNAL = "external"


@dataclass(frozen=True, slots=True)
class CapabilityAvailabilityV1:
    """One deterministic, input-independent capability availability result."""

    available: bool
    backend_id: str | None = None
    backend_version: str | None = None
    reason_code: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.available, bool):
            raise ValueError("available must be a boolean")
        if (self.backend_id is None) != (self.backend_version is None):
            raise ValueError("backend_id and backend_version must be provided together")
        if self.backend_id is not None:
            _stable_identifier(self.backend_id, "backend_id")
            _identity_text(self.backend_version, "backend_version")
        if self.reason_code is not None:
            _stable_identifier(self.reason_code, "reason_code")
        if self.available and self.reason_code is not None:
            raise ValueError("an available capability cannot have a reason code")
        if not self.available and self.reason_code is None:
            raise ValueError("an unavailable capability requires a reason code")


@dataclass(frozen=True, slots=True)
class DetectorInputV1:
    """The complete bounded input visible to an SDK-v1 detector."""

    source_kind: SourceKind
    prefix: bytes
    reached_eof: bool
    effective_limit: int

    def __post_init__(self) -> None:
        if not isinstance(self.source_kind, SourceKind):
            raise ValueError("source_kind must be a SourceKind")
        if not isinstance(self.prefix, bytes):
            raise ValueError("prefix must be bytes")
        if not isinstance(self.reached_eof, bool):
            raise ValueError("reached_eof must be a boolean")
        limit = _bounded_integer(self.effective_limit, "effective_limit")
        if len(self.prefix) > limit:
            raise ValueError("prefix exceeds effective_limit")


@dataclass(frozen=True, slots=True)
class DetectorCandidateV1:
    """One plugin detector claim for an existing Phase 2 modality."""

    modality_id: Literal["text", "binary"]
    confidence: int
    evidence_codes: tuple[str, ...]
    evidence_counts: JsonObject

    def __post_init__(self) -> None:
        if self.modality_id not in ("text", "binary"):
            raise ValueError("unknown detection modality")
        _bounded_integer(self.confidence, "confidence")
        if self.confidence > 1000:
            raise ValueError("confidence must be in 0..1000")
        object.__setattr__(
            self,
            "evidence_codes",
            _string_tuple(self.evidence_codes, "evidence_codes", identifiers=True),
        )
        if not isinstance(self.evidence_counts, dict):
            raise ValueError("evidence_counts must be a JSON object")


class DetectorHandleV1(Protocol):
    """Executable SDK-v1 detector handle associated with one declaration."""

    capability_id: str

    def availability(self) -> CapabilityAvailabilityV1: ...

    def detect(self, source: DetectorInputV1) -> tuple[DetectorCandidateV1, ...]: ...


class SourceServiceV1(Protocol):
    """Replayable, bounded source access controlled by the host lifecycle."""

    source_kind: SourceKind
    label: str | None
    size_bytes: int

    def read(self) -> bytes: ...

    def iter_chunks(self, chunk_bytes: int) -> Iterator[bytes]: ...


class ComparatorRunV1(Protocol):
    """One weak-referenceable single-use lifecycle owned and ordered by the host."""

    def decode(self) -> None: ...

    def normalize(self) -> None: ...

    def align(self) -> None: ...

    def compare(self) -> None: ...

    def aggregate(self) -> PluginComparisonV1: ...


class ComparatorHandleV1(Protocol):
    """Executable SDK-v1 comparator handle associated with one declaration."""

    capability_id: str
    modality: Literal["text", "binary"]
    source_stage: Literal["decoding", "normalizing", "aligning", "comparing"]

    def availability(self) -> CapabilityAvailabilityV1: ...

    def create_run(
        self,
        before: SourceServiceV1,
        after: SourceServiceV1,
        spec: TextCompareSpec | BinaryCompareSpec,
    ) -> ComparatorRunV1: ...


type CapabilityHandleV1 = DetectorHandleV1 | ComparatorHandleV1


@dataclass(frozen=True, slots=True)
class PluginComparisonV1:
    """Validated comparison facts returned before host-owned provenance wrapping."""

    relation: Relation
    verdict: Verdict
    fidelity: Fidelity
    summary: DiffSummary
    changes: ChangeSet
    metrics: tuple[Metric, ...]
    evaluations: tuple[PolicyEvaluation, ...]
    artifacts: tuple[ArtifactRef, ...]
    transformations: tuple[TransformationRecord, ...]
    algorithm_id: str
    implementation_version: str
    resources: tuple[ResourceUsage, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        _stable_identifier(self.algorithm_id, "algorithm_id")
        _identity_text(self.implementation_version, "implementation_version")
        for field_name, expected_type in (
            ("metrics", Metric),
            ("evaluations", PolicyEvaluation),
            ("artifacts", ArtifactRef),
            ("transformations", TransformationRecord),
            ("resources", ResourceUsage),
            ("diagnostics", Diagnostic),
        ):
            values = getattr(self, field_name)
            if not isinstance(values, tuple) or not all(
                isinstance(item, expected_type) for item in values
            ):
                raise ValueError(f"{field_name} contains invalid values")
        if self.summary.change_count != self.changes.total_count:
            raise ValueError("summary and ChangeSet totals must agree")


class PluginErrorV1(Exception):
    """Base class for expected, safely mappable SDK-v1 plugin failures."""


class PluginExecutionErrorV1(PluginErrorV1):
    """A selected plugin could not complete its current lifecycle method."""


class PluginResourceLimitErrorV1(PluginErrorV1):
    """A selected plugin exhausted a deterministic host or plugin budget."""


class PluginUnavailableErrorV1(PluginErrorV1):
    """A deterministic capability probe reported pre-execution unavailability."""

    def __init__(self, reason_code: str) -> None:
        super().__init__("The plugin capability is unavailable.")
        self.reason_code = _stable_identifier(reason_code, "reason_code")


@dataclass(frozen=True, slots=True)
class RuntimeDependencyV1:
    """An inventory declaration for one Python distribution dependency."""

    distribution_name: str
    version_specifier: str
    optional: bool = False

    def __post_init__(self) -> None:
        name = _bounded_text(self.distribution_name, "distribution_name")
        if not _DISTRIBUTION_NAME.fullmatch(name):
            raise ValueError(
                "distribution_name must be a valid Python distribution name"
            )
        _identity_text(self.version_specifier, "version_specifier", allow_empty=True)
        if not isinstance(self.optional, bool):
            raise ValueError("optional must be a boolean")


@dataclass(frozen=True, slots=True)
class ComponentDeclarationV1:
    """Inventory-only declaration for a native or external component."""

    component_id: str
    component_version: str
    kind: ComponentKind
    optional: bool = False

    def __post_init__(self) -> None:
        _stable_identifier(self.component_id, "component_id")
        _identity_text(self.component_version, "component_version")
        if not isinstance(self.kind, ComponentKind):
            raise ValueError("kind must be a ComponentKind")
        if not isinstance(self.optional, bool):
            raise ValueError("optional must be a boolean")


@dataclass(frozen=True, slots=True)
class CapabilityDeclarationV1:
    """A non-executable capability declaration in one plugin manifest."""

    capability_id: str
    kind: CapabilityKind
    implementation_version: str
    backend_id: str | None = None
    backend_version: str | None = None
    priority: int = 0
    runtime_dependencies: tuple[RuntimeDependencyV1, ...] = ()
    supported_python_versions: tuple[str, ...] = ()
    supported_platforms: tuple[str, ...] = ()
    components: tuple[ComponentDeclarationV1, ...] = ()

    def __post_init__(self) -> None:
        _stable_identifier(self.capability_id, "capability_id")
        if not isinstance(self.kind, CapabilityKind):
            raise ValueError("kind must be a CapabilityKind")
        _identity_text(self.implementation_version, "implementation_version")
        if (self.backend_id is None) != (self.backend_version is None):
            raise ValueError("backend_id and backend_version must be provided together")
        if self.backend_id is not None:
            _stable_identifier(self.backend_id, "backend_id")
            _identity_text(self.backend_version, "backend_version")
        _bounded_integer(self.priority, "priority")
        if not isinstance(self.runtime_dependencies, tuple) or not all(
            isinstance(item, RuntimeDependencyV1) for item in self.runtime_dependencies
        ):
            raise ValueError(
                "runtime_dependencies must contain RuntimeDependencyV1 values"
            )
        dependency_names = [
            re.sub(r"[-_.]+", "-", item.distribution_name).lower()
            for item in self.runtime_dependencies
        ]
        if len(dependency_names) != len(set(dependency_names)):
            raise ValueError(
                "runtime dependency names must be unique after normalization"
            )
        object.__setattr__(
            self,
            "runtime_dependencies",
            tuple(
                item
                for _, item in sorted(
                    zip(dependency_names, self.runtime_dependencies, strict=True),
                    key=lambda pair: pair[0],
                )
            ),
        )
        object.__setattr__(
            self,
            "supported_python_versions",
            _string_tuple(
                self.supported_python_versions,
                "supported_python_versions",
                path_free=True,
            ),
        )
        object.__setattr__(
            self,
            "supported_platforms",
            _string_tuple(
                self.supported_platforms, "supported_platforms", path_free=True
            ),
        )
        if not isinstance(self.components, tuple) or not all(
            isinstance(item, ComponentDeclarationV1) for item in self.components
        ):
            raise ValueError("components must contain ComponentDeclarationV1 values")
        component_ids = [item.component_id for item in self.components]
        if len(component_ids) != len(set(component_ids)):
            raise ValueError("component identifiers must be unique")
        object.__setattr__(
            self,
            "components",
            tuple(sorted(self.components, key=lambda item: item.component_id)),
        )


@dataclass(frozen=True, slots=True)
class PluginManifestV1:
    """The complete immutable value returned by an SDK-v1 manifest factory."""

    manifest_schema_version: Literal[1]
    plugin_id: str
    plugin_version: str
    api_major: Literal[1]
    minimum_api_minor: int
    maximum_api_minor: int
    required_host_features: tuple[str, ...]
    capabilities: tuple[CapabilityDeclarationV1, ...]
    license_expression: str
    capability_handles: tuple[CapabilityHandleV1, ...] = ()

    def __post_init__(self) -> None:
        _bounded_integer(self.manifest_schema_version, "manifest_schema_version")
        if self.manifest_schema_version != PLUGIN_MANIFEST_SCHEMA_VERSION:
            raise ValueError("unsupported plugin manifest schema version")
        plugin_id = _plugin_identifier(self.plugin_id)
        _identity_text(self.plugin_version, "plugin_version")
        _bounded_integer(self.api_major, "api_major")
        if self.api_major != PLUGIN_API_MAJOR:
            raise ValueError("unsupported plugin API major")
        minimum = _bounded_integer(self.minimum_api_minor, "minimum_api_minor")
        maximum = _bounded_integer(self.maximum_api_minor, "maximum_api_minor")
        if minimum > maximum:
            raise ValueError("minimum_api_minor must not exceed maximum_api_minor")
        object.__setattr__(
            self,
            "required_host_features",
            _string_tuple(
                self.required_host_features,
                "required_host_features",
                identifiers=True,
            ),
        )
        if not isinstance(self.capabilities, tuple) or not all(
            isinstance(item, CapabilityDeclarationV1) for item in self.capabilities
        ):
            raise ValueError("capabilities must contain CapabilityDeclarationV1 values")
        for capability in self.capabilities:
            _plugin_scoped_identifier(
                capability.capability_id, "capability_id", plugin_id
            )
            if capability.backend_id is not None:
                _plugin_scoped_identifier(
                    capability.backend_id, "backend_id", plugin_id
                )
        object.__setattr__(
            self,
            "capabilities",
            tuple(
                sorted(
                    self.capabilities,
                    key=lambda item: (item.capability_id, item.backend_id or ""),
                )
            ),
        )
        _identity_text(self.license_expression, "license_expression")
        if not isinstance(self.capability_handles, tuple):
            raise ValueError("capability_handles must be a tuple")
        handle_ids: list[str] = []
        for handle in self.capability_handles:
            try:
                handle_id = _stable_identifier(handle.capability_id, "capability_id")
            except (AttributeError, TypeError) as error:
                raise ValueError(
                    "capability_handles contains an invalid handle"
                ) from error
            handle_ids.append(handle_id)
        if len(handle_ids) != len(set(handle_ids)):
            raise ValueError("capability handle identifiers must be unique")
        declaration_ids = {item.capability_id for item in self.capabilities}
        if not set(handle_ids).issubset(declaration_ids):
            raise ValueError("each capability handle requires a declaration")
        object.__setattr__(
            self,
            "capability_handles",
            tuple(
                handle
                for _, handle in sorted(
                    zip(handle_ids, self.capability_handles, strict=True),
                    key=lambda pair: pair[0],
                )
            ),
        )


class PluginManifestFactoryV1(Protocol):
    """The callable contract targeted by ``platydiff.plugins.v1`` entry points."""

    def __call__(self) -> PluginManifestV1: ...
