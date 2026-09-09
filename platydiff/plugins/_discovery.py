"""Explicit, allowlisted discovery for SDK-v1 plugin manifests."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from typing import Literal, Protocol, cast

from platydiff.plugin_sdk import (
    HOST_FEATURES_V1,
    PLUGIN_API_MAJOR,
    PLUGIN_API_MINOR,
    PLUGIN_ENTRY_POINT_GROUP,
    PLUGIN_MANIFEST_SCHEMA_VERSION,
    CapabilityDeclarationV1,
    ComponentDeclarationV1,
    PluginManifestV1,
    RuntimeDependencyV1,
)
from platydiff.plugin_sdk._models import (
    _bounded_integer,
    _bounded_text,
    _plugin_identifier,
    _stable_identifier,
)

type PluginDiscoveryReason = Literal[
    "plugin_disabled",
    "plugin_not_found",
    "plugin_metadata_invalid",
    "plugin_id_conflict",
    "plugin_import_failed",
    "plugin_factory_failed",
    "plugin_manifest_invalid",
    "plugin_api_incompatible",
    "plugin_feature_unsupported",
    "capability_id_conflict",
]

_ENTRY_POINT_VALUE = re.compile(
    r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$",
    re.ASCII,
)
_DISTRIBUTION_NAME = re.compile(
    r"^(?:[A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9])\Z"
)
_REASON_CODES: frozenset[str] = frozenset(
    {
        "plugin_disabled",
        "plugin_not_found",
        "plugin_metadata_invalid",
        "plugin_id_conflict",
        "plugin_import_failed",
        "plugin_factory_failed",
        "plugin_manifest_invalid",
        "plugin_api_incompatible",
        "plugin_feature_unsupported",
        "capability_id_conflict",
    }
)
_BUILTIN_CAPABILITY_IDS = frozenset({"binary", "text", "core.text_binary_prefix"})


class _DistributionLike(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...


class _EntryPointLike(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def group(self) -> str: ...

    @property
    def value(self) -> str: ...

    @property
    def dist(self) -> _DistributionLike | None: ...

    def load(self) -> object: ...


def _normalized_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _safe_metadata_text(value: object) -> str:
    try:
        text = _bounded_text(value, "metadata", allow_empty=True)
    except ValueError:
        return ""
    if "/" in text or "\\" in text:
        return ""
    return text


@dataclass(frozen=True, slots=True)
class PluginDiscoveryPolicy:
    """An exact plugin-ID allowlist; an empty tuple enables no plugins."""

    enabled_plugin_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.enabled_plugin_ids, tuple):
            raise ValueError("enabled_plugin_ids must be a tuple")
        for plugin_id in self.enabled_plugin_ids:
            _plugin_identifier(plugin_id)
        if len(self.enabled_plugin_ids) != len(set(self.enabled_plugin_ids)):
            raise ValueError("enabled_plugin_ids must be unique")
        object.__setattr__(
            self, "enabled_plugin_ids", tuple(sorted(self.enabled_plugin_ids))
        )


@dataclass(frozen=True, slots=True)
class PluginEntryPointV1:
    """Safe installed-distribution metadata captured before plugin import."""

    plugin_id: str
    group: Literal["platydiff.plugins.v1"]
    value: str
    distribution_name: str
    distribution_version: str

    def __post_init__(self) -> None:
        _plugin_identifier(self.plugin_id)
        if self.group != PLUGIN_ENTRY_POINT_GROUP:
            raise ValueError("unsupported plugin entry-point group")
        if not isinstance(self.value, str) or not _ENTRY_POINT_VALUE.fullmatch(
            self.value
        ):
            raise ValueError("entry-point value must reference one module factory")
        name = _safe_metadata_text(self.distribution_name)
        if name != self.distribution_name or not _DISTRIBUTION_NAME.fullmatch(name):
            raise ValueError("invalid plugin distribution name")
        version = _safe_metadata_text(self.distribution_version)
        if not version or version != self.distribution_version:
            raise ValueError("invalid plugin distribution version")

    @property
    def normalized_distribution_name(self) -> str:
        return _normalized_distribution_name(self.distribution_name)


@dataclass(frozen=True, slots=True)
class PluginDiscoveryIssueV1:
    """A bounded diagnostic that never includes exception or filesystem details."""

    plugin_id: str
    distribution_name: str
    distribution_version: str
    entry_point_value: str
    reason_code: PluginDiscoveryReason
    capability_id: str | None = None

    def __post_init__(self) -> None:
        for value in (
            self.plugin_id,
            self.distribution_name,
            self.distribution_version,
            self.entry_point_value,
        ):
            if _safe_metadata_text(value) != value:
                raise ValueError("plugin issue metadata must be bounded and path-free")
        if self.reason_code not in _REASON_CODES:
            raise ValueError("unknown plugin discovery reason")
        if self.capability_id is not None:
            _stable_identifier(self.capability_id, "capability_id")


@dataclass(frozen=True, slots=True)
class LoadedPluginV1:
    """One validated manifest and its negotiated SDK identity."""

    entry_point: PluginEntryPointV1
    manifest: PluginManifestV1
    negotiated_api_minor: int
    negotiated_host_features: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.entry_point.plugin_id != self.manifest.plugin_id:
            raise ValueError("entry-point and manifest plugin IDs must match")
        _bounded_integer(self.negotiated_api_minor, "negotiated_api_minor")
        if self.negotiated_api_minor != PLUGIN_API_MINOR:
            raise ValueError("catalog must use the current host API minor")
        if self.negotiated_host_features != tuple(
            sorted(self.negotiated_host_features)
        ):
            raise ValueError("negotiated host features must be sorted")


@dataclass(frozen=True, slots=True)
class DiscoveredCapabilityV1:
    """A conflict-free declaration associated with its loaded provider."""

    plugin: LoadedPluginV1
    declaration: CapabilityDeclarationV1

    def __post_init__(self) -> None:
        if self.declaration not in self.plugin.manifest.capabilities:
            raise ValueError("capability must belong to its plugin manifest")


@dataclass(frozen=True, slots=True)
class PluginCatalogV1:
    """Immutable result of one explicit SDK-v1 discovery operation."""

    enabled_plugin_ids: tuple[str, ...]
    entry_points: tuple[PluginEntryPointV1, ...]
    plugins: tuple[LoadedPluginV1, ...]
    capabilities: tuple[DiscoveredCapabilityV1, ...]
    issues: tuple[PluginDiscoveryIssueV1, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "enabled_plugin_ids",
            "entry_points",
            "plugins",
            "capabilities",
            "issues",
        ):
            if not isinstance(getattr(self, field_name), tuple):
                raise ValueError(f"{field_name} must be a tuple")
        object.__setattr__(
            self, "enabled_plugin_ids", tuple(sorted(self.enabled_plugin_ids))
        )
        object.__setattr__(
            self, "entry_points", tuple(sorted(self.entry_points, key=_metadata_key))
        )
        object.__setattr__(
            self,
            "plugins",
            tuple(
                sorted(self.plugins, key=lambda item: _metadata_key(item.entry_point))
            ),
        )
        object.__setattr__(
            self,
            "capabilities",
            tuple(
                sorted(
                    self.capabilities,
                    key=lambda item: (
                        item.declaration.capability_id,
                        item.plugin.manifest.plugin_id,
                        item.declaration.backend_id or "",
                    ),
                )
            ),
        )
        object.__setattr__(self, "issues", tuple(sorted(self.issues, key=_issue_key)))


@dataclass(frozen=True, slots=True)
class _Candidate:
    metadata: PluginEntryPointV1
    entry_point: _EntryPointLike


@dataclass(frozen=True, slots=True)
class _RawClaim:
    plugin_id: str
    distribution_name: str
    distribution_version: str
    entry_point_value: str


def _metadata_key(item: PluginEntryPointV1) -> tuple[str, str, str, str, str]:
    return (
        item.plugin_id,
        item.normalized_distribution_name,
        item.distribution_version,
        item.value,
        item.distribution_name,
    )


def _issue_key(
    item: PluginDiscoveryIssueV1,
) -> tuple[str, str, str, str, str, str, str]:
    return (
        item.plugin_id,
        _normalized_distribution_name(item.distribution_name),
        item.distribution_version,
        item.entry_point_value,
        item.reason_code,
        item.capability_id or "",
        item.distribution_name,
    )


def _issue(
    reason_code: PluginDiscoveryReason,
    metadata: PluginEntryPointV1 | None = None,
    *,
    plugin_id: str = "",
    distribution_name: str = "",
    distribution_version: str = "",
    entry_point_value: str = "",
    capability_id: str | None = None,
) -> PluginDiscoveryIssueV1:
    if metadata is not None:
        plugin_id = metadata.plugin_id
        distribution_name = metadata.distribution_name
        distribution_version = metadata.distribution_version
        entry_point_value = metadata.value
    return PluginDiscoveryIssueV1(
        plugin_id=_safe_metadata_text(plugin_id),
        distribution_name=_safe_metadata_text(distribution_name),
        distribution_version=_safe_metadata_text(distribution_version),
        entry_point_value=_safe_metadata_text(entry_point_value),
        reason_code=reason_code,
        capability_id=capability_id,
    )


def _installed_entry_points() -> tuple[_EntryPointLike, ...]:
    return tuple(importlib_metadata.entry_points(group=PLUGIN_ENTRY_POINT_GROUP))


def _enumerate() -> tuple[
    tuple[_Candidate, ...],
    tuple[PluginDiscoveryIssueV1, ...],
    tuple[_RawClaim, ...],
]:
    candidates: list[_Candidate] = []
    issues: list[PluginDiscoveryIssueV1] = []
    claims: list[_RawClaim] = []
    for entry_point in _installed_entry_points():
        raw_name = ""
        raw_distribution_name = ""
        raw_distribution_version = ""
        raw_value = ""
        metadata: PluginEntryPointV1 | None = None
        try:
            entry_point_name = entry_point.name
            entry_point_group = entry_point.group
            entry_point_value = entry_point.value
            raw_name = _safe_metadata_text(entry_point_name)
            distribution = entry_point.dist
            raw_distribution_name = (
                _safe_metadata_text(distribution.name)
                if distribution is not None
                else ""
            )
            raw_distribution_version = (
                _safe_metadata_text(distribution.version)
                if distribution is not None
                else ""
            )
            raw_value = _safe_metadata_text(entry_point_value)
            metadata = PluginEntryPointV1(
                plugin_id=entry_point_name,
                group=cast(Literal["platydiff.plugins.v1"], entry_point_group),
                value=entry_point_value,
                distribution_name=raw_distribution_name,
                distribution_version=raw_distribution_version,
            )
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception:
            issues.append(
                _issue(
                    "plugin_metadata_invalid",
                    plugin_id=raw_name,
                    distribution_name=raw_distribution_name,
                    distribution_version=raw_distribution_version,
                    entry_point_value=raw_value,
                )
            )
        if raw_name:
            try:
                _plugin_identifier(raw_name)
            except ValueError:
                pass
            else:
                claims.append(
                    _RawClaim(
                        raw_name,
                        raw_distribution_name,
                        raw_distribution_version,
                        raw_value,
                    )
                )
        if metadata is not None:
            candidates.append(_Candidate(metadata, entry_point))
    return (
        tuple(sorted(candidates, key=lambda item: _metadata_key(item.metadata))),
        tuple(sorted(issues, key=_issue_key)),
        tuple(
            sorted(
                claims,
                key=lambda item: (
                    item.plugin_id,
                    _normalized_distribution_name(item.distribution_name),
                    item.distribution_version,
                    item.entry_point_value,
                    item.distribution_name,
                ),
            )
        ),
    )


def _select(
    candidates: tuple[_Candidate, ...],
    policy: PluginDiscoveryPolicy,
    claims: tuple[_RawClaim, ...],
) -> tuple[tuple[_Candidate, ...], tuple[PluginDiscoveryIssueV1, ...]]:
    by_plugin: dict[str, list[_Candidate]] = defaultdict(list)
    for candidate in candidates:
        by_plugin[candidate.metadata.plugin_id].append(candidate)
    selected: list[_Candidate] = []
    issues: list[PluginDiscoveryIssueV1] = []
    enabled = frozenset(policy.enabled_plugin_ids)
    claims_by_plugin: dict[str, list[_RawClaim]] = defaultdict(list)
    for claim in claims:
        claims_by_plugin[claim.plugin_id].append(claim)
    conflicted_plugin_ids = {
        plugin_id
        for plugin_id, plugin_claims in claims_by_plugin.items()
        if len(plugin_claims) > 1
    }
    for plugin_id, claimants in sorted(by_plugin.items()):
        if plugin_id in conflicted_plugin_ids:
            continue
        if plugin_id in enabled:
            selected.append(claimants[0])
        else:
            issues.append(_issue("plugin_disabled", claimants[0].metadata))
    for plugin_id in sorted(conflicted_plugin_ids):
        for claim in claims_by_plugin[plugin_id]:
            issues.append(
                _issue(
                    "plugin_id_conflict",
                    plugin_id=claim.plugin_id,
                    distribution_name=claim.distribution_name,
                    distribution_version=claim.distribution_version,
                    entry_point_value=claim.entry_point_value,
                )
            )
    for plugin_id in policy.enabled_plugin_ids:
        if plugin_id not in claims_by_plugin:
            issues.append(_issue("plugin_not_found", plugin_id=plugin_id))
    return tuple(selected), tuple(sorted(issues, key=_issue_key))


def _load(
    candidates: tuple[_Candidate, ...],
) -> tuple[tuple[LoadedPluginV1, ...], tuple[PluginDiscoveryIssueV1, ...]]:
    plugins: list[LoadedPluginV1] = []
    issues: list[PluginDiscoveryIssueV1] = []
    host_features = frozenset(HOST_FEATURES_V1)
    for candidate in candidates:
        try:
            target = candidate.entry_point.load()
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception:
            issues.append(_issue("plugin_import_failed", candidate.metadata))
            continue
        if not callable(target):
            issues.append(_issue("plugin_factory_failed", candidate.metadata))
            continue
        try:
            returned_manifest = target()
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception:
            issues.append(_issue("plugin_factory_failed", candidate.metadata))
            continue
        manifest = _validated_manifest(returned_manifest)
        if manifest is None:
            issues.append(_issue("plugin_manifest_invalid", candidate.metadata))
            continue
        if manifest.plugin_id != candidate.metadata.plugin_id:
            issues.append(_issue("plugin_manifest_invalid", candidate.metadata))
            continue
        if (
            manifest.manifest_schema_version != PLUGIN_MANIFEST_SCHEMA_VERSION
            or manifest.api_major != PLUGIN_API_MAJOR
            or not manifest.minimum_api_minor
            <= PLUGIN_API_MINOR
            <= manifest.maximum_api_minor
        ):
            issues.append(_issue("plugin_api_incompatible", candidate.metadata))
            continue
        if not set(manifest.required_host_features).issubset(host_features):
            issues.append(_issue("plugin_feature_unsupported", candidate.metadata))
            continue
        plugins.append(
            LoadedPluginV1(
                candidate.metadata,
                manifest,
                PLUGIN_API_MINOR,
                tuple(
                    sorted(
                        set(manifest.required_host_features).intersection(host_features)
                    )
                ),
            )
        )
    return tuple(plugins), tuple(sorted(issues, key=_issue_key))


def _validated_manifest(value: object) -> PluginManifestV1 | None:
    """Reconstruct a returned manifest so mutated typed values cannot bypass checks."""
    if not isinstance(value, PluginManifestV1):
        return None
    try:
        if not isinstance(value.capabilities, tuple) or not isinstance(
            value.required_host_features, tuple
        ):
            raise ValueError("manifest collections must be tuples")
        capabilities: list[CapabilityDeclarationV1] = []
        for declaration in value.capabilities:
            if not isinstance(declaration, CapabilityDeclarationV1):
                raise ValueError("invalid capability declaration")
            if not isinstance(
                declaration.runtime_dependencies, tuple
            ) or not isinstance(declaration.supported_python_versions, tuple):
                raise ValueError("invalid capability collections")
            if not isinstance(declaration.supported_platforms, tuple) or not isinstance(
                declaration.components, tuple
            ):
                raise ValueError("invalid capability collections")
            dependencies = tuple(
                RuntimeDependencyV1(
                    dependency.distribution_name,
                    dependency.version_specifier,
                    dependency.optional,
                )
                for dependency in declaration.runtime_dependencies
            )
            components = tuple(
                ComponentDeclarationV1(
                    component.component_id,
                    component.component_version,
                    component.kind,
                    component.optional,
                )
                for component in declaration.components
            )
            capabilities.append(
                CapabilityDeclarationV1(
                    capability_id=declaration.capability_id,
                    kind=declaration.kind,
                    implementation_version=declaration.implementation_version,
                    backend_id=declaration.backend_id,
                    backend_version=declaration.backend_version,
                    priority=declaration.priority,
                    runtime_dependencies=dependencies,
                    supported_python_versions=declaration.supported_python_versions,
                    supported_platforms=declaration.supported_platforms,
                    components=components,
                )
            )
        return PluginManifestV1(
            manifest_schema_version=value.manifest_schema_version,
            plugin_id=value.plugin_id,
            plugin_version=value.plugin_version,
            api_major=value.api_major,
            minimum_api_minor=value.minimum_api_minor,
            maximum_api_minor=value.maximum_api_minor,
            required_host_features=value.required_host_features,
            capabilities=tuple(capabilities),
            license_expression=value.license_expression,
        )
    except (KeyboardInterrupt, SystemExit, MemoryError):
        raise
    except Exception:
        return None


def _catalog_capabilities(
    plugins: tuple[LoadedPluginV1, ...],
) -> tuple[tuple[DiscoveredCapabilityV1, ...], tuple[PluginDiscoveryIssueV1, ...]]:
    claims: dict[str, list[tuple[LoadedPluginV1, CapabilityDeclarationV1]]] = (
        defaultdict(list)
    )
    for plugin in plugins:
        for declaration in plugin.manifest.capabilities:
            claims[declaration.capability_id].append((plugin, declaration))
    capabilities: list[DiscoveredCapabilityV1] = []
    issues: list[PluginDiscoveryIssueV1] = []
    for capability_id, claimants in sorted(claims.items()):
        conflict = (
            len(claimants) > 1
            or capability_id in _BUILTIN_CAPABILITY_IDS
            or capability_id.startswith("core.")
        )
        if conflict:
            seen_plugins: set[str] = set()
            for plugin, _ in claimants:
                if plugin.manifest.plugin_id not in seen_plugins:
                    issues.append(
                        _issue(
                            "capability_id_conflict",
                            plugin.entry_point,
                            capability_id=capability_id,
                        )
                    )
                    seen_plugins.add(plugin.manifest.plugin_id)
            continue
        plugin, declaration = claimants[0]
        capabilities.append(DiscoveredCapabilityV1(plugin, declaration))
    return tuple(capabilities), tuple(sorted(issues, key=_issue_key))


def discover_plugins(policy: PluginDiscoveryPolicy) -> PluginCatalogV1:
    """Enumerate, select, and load only the exact SDK-v1 allowlist."""
    if not isinstance(policy, PluginDiscoveryPolicy):
        raise TypeError("policy must be a PluginDiscoveryPolicy")
    candidates, enumeration_issues, claims = _enumerate()
    selected, selection_issues = _select(candidates, policy, claims)
    plugins, load_issues = _load(selected)
    capabilities, capability_issues = _catalog_capabilities(plugins)
    return PluginCatalogV1(
        enabled_plugin_ids=policy.enabled_plugin_ids,
        entry_points=tuple(candidate.metadata for candidate in candidates),
        plugins=plugins,
        capabilities=capabilities,
        issues=(
            *enumeration_issues,
            *selection_issues,
            *load_issues,
            *capability_issues,
        ),
    )
