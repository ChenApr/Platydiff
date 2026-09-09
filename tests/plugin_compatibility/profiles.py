"""Canonical evidence projections for the P3-A compatibility profiles."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256

from platydiff import __version__
from platydiff.plugin_sdk import PLUGIN_API_MAJOR, PLUGIN_API_MINOR, PluginManifestV1
from platydiff.plugins import LoadedPluginV1, PluginCatalogV1

type JsonPrimitive = bool | int | str | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]

MANIFEST_PROFILE_ID = "platydiff.p3a.manifest.v1"
DISCOVERY_PROFILE_ID = "platydiff.p3a.discovery.v1"
DETECTOR_PROFILE_ID = "platydiff.p3b.detector.v1"
COMPARATOR_PROFILE_ID = "platydiff.p3b.comparator.v1"
RENDERER_PROFILE_ID = "platydiff.p3c.renderer.v1"
ISOLATION_PROFILE_ID = "platydiff.p3c.isolation.v1"
SUPPLY_CHAIN_PROFILE_ID = "platydiff.p3c.supply_chain.v1"
COMPATIBILITY_SUITE_VERSION = "1.0"
COMPATIBILITY_PROFILE_IDS = (
    MANIFEST_PROFILE_ID,
    DISCOVERY_PROFILE_ID,
    DETECTOR_PROFILE_ID,
    COMPARATOR_PROFILE_ID,
    RENDERER_PROFILE_ID,
    ISOLATION_PROFILE_ID,
    SUPPLY_CHAIN_PROFILE_ID,
)
FAILURE_ISOLATION_MATRIX: tuple[tuple[str, str, str], ...] = (
    ("discovery", "quarantined", "continue unrelated plugins"),
    ("availability", "unavailable or failed outcome", "no invocation or fallback"),
    ("detector", "failed outcome", "no retry or fallback"),
    ("comparator", "failed outcome", "no retry or content difference"),
    ("renderer", "typed renderer error", "preserve outcome and no fallback"),
    ("cli", "exit 3 with safe stderr", "emit no replacement output"),
)
_BIDI_CONTROLS = frozenset(
    (0x061C, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A))
)
_PROFILE_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_FORBIDDEN_EVIDENCE_KEYS = frozenset(
    {
        "before",
        "after",
        "source",
        "source_content",
        "source_path",
        "username",
        "environment_variables",
        "traceback",
        "token",
    }
)


def _normalized_evidence(value: object, *, key: str | None = None) -> JsonValue:
    if key in _FORBIDDEN_EVIDENCE_KEYS:
        raise ValueError("profile evidence must not contain sensitive fields")
    if value is None or type(value) in (bool, int):
        return value  # type: ignore[return-value]
    if isinstance(value, str):
        if (
            len(value.encode("utf-8")) > 4096
            or any(
                ord(character) < 0x20 or 0x7F <= ord(character) <= 0x9F
                for character in value
            )
            or value.startswith("/")
            or re.search(r"(?:^|\s)[A-Za-z]:\\", value) is not None
        ):
            raise ValueError("profile evidence must be bounded and path-free")
        return value
    if isinstance(value, list):
        return [_normalized_evidence(item) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(item, str) for item in value):
            raise ValueError("profile evidence keys must be strings")
        return {
            item: _normalized_evidence(value[item], key=item) for item in sorted(value)
        }
    raise ValueError("profile evidence must contain only JSON values")


@dataclass(frozen=True, slots=True)
class CompatibilityProfileResultV1:
    """One actually executed profile result and its normalized evidence summary."""

    profile_id: str
    passed: bool
    summary: JsonObject

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or not _PROFILE_ID.fullmatch(
            self.profile_id
        ):
            raise ValueError("profile_id must be a stable lowercase ASCII identifier")
        if type(self.passed) is not bool:
            raise ValueError("passed must be a boolean")
        normalized = _normalized_evidence(self.summary)
        if not isinstance(normalized, dict) or not normalized:
            raise ValueError("summary must be a non-empty JSON object")
        object.__setattr__(self, "summary", normalized)


def _receipt_environment_text(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value.encode("utf-8")) > 255
        or "/" in value
        or "\\" in value
        or any(ord(character) < 0x20 for character in value)
    ):
        raise ValueError("receipt environment values must be bounded and path-free")
    return value


def terminal_text_is_safe(value: str) -> bool:
    """Report whether renderer text is safe to emit to a plain terminal."""
    return all(
        character == "\n"
        or (
            ord(character) >= 0x20
            and not 0x7F <= ord(character) <= 0x9F
            and ord(character) != 0xFEFF
            and ord(character) not in _BIDI_CONTROLS
        )
        for character in value
    )


def manifest_profile_data(manifest: PluginManifestV1) -> JsonObject:
    """Project a validated manifest into deterministic compatibility evidence."""
    capabilities: list[JsonValue] = []
    for capability in manifest.capabilities:
        dependencies: list[JsonValue] = [
            {
                "distribution_name": dependency.distribution_name,
                "optional": dependency.optional,
                "version_specifier": dependency.version_specifier,
            }
            for dependency in capability.runtime_dependencies
        ]
        components: list[JsonValue] = [
            {
                "component_id": component.component_id,
                "component_version": component.component_version,
                "kind": component.kind.value,
                "optional": component.optional,
            }
            for component in capability.components
        ]
        capabilities.append(
            {
                "backend_id": capability.backend_id,
                "backend_version": capability.backend_version,
                "capability_id": capability.capability_id,
                "components": components,
                "implementation_version": capability.implementation_version,
                "kind": capability.kind.value,
                "priority": capability.priority,
                "runtime_dependencies": dependencies,
                "supported_platforms": list(capability.supported_platforms),
                "supported_python_versions": list(capability.supported_python_versions),
            }
        )
    return {
        "api_major": manifest.api_major,
        "capabilities": capabilities,
        "license_expression": manifest.license_expression,
        "manifest_schema_version": manifest.manifest_schema_version,
        "maximum_api_minor": manifest.maximum_api_minor,
        "minimum_api_minor": manifest.minimum_api_minor,
        "plugin_id": manifest.plugin_id,
        "plugin_version": manifest.plugin_version,
        "profile_id": MANIFEST_PROFILE_ID,
        "required_host_features": list(manifest.required_host_features),
    }


def catalog_profile_data(catalog: PluginCatalogV1) -> JsonObject:
    """Project a discovery catalog without executable targets or unsafe details."""
    entry_points: list[JsonValue] = [
        {
            "distribution_name": item.distribution_name,
            "distribution_version": item.distribution_version,
            "group": item.group,
            "plugin_id": item.plugin_id,
            "value": item.value,
        }
        for item in catalog.entry_points
    ]
    plugins: list[JsonValue] = [
        {
            "distribution_name": item.entry_point.distribution_name,
            "distribution_version": item.entry_point.distribution_version,
            "manifest": manifest_profile_data(item.manifest),
            "negotiated_api_minor": item.negotiated_api_minor,
            "negotiated_host_features": list(item.negotiated_host_features),
        }
        for item in catalog.plugins
    ]
    capabilities: list[JsonValue] = [
        {
            "backend_id": item.declaration.backend_id,
            "capability_id": item.declaration.capability_id,
            "kind": item.declaration.kind.value,
            "plugin_id": item.plugin.manifest.plugin_id,
        }
        for item in catalog.capabilities
    ]
    issues: list[JsonValue] = [
        {
            "capability_id": item.capability_id,
            "distribution_name": item.distribution_name,
            "distribution_version": item.distribution_version,
            "entry_point_value": item.entry_point_value,
            "plugin_id": item.plugin_id,
            "reason_code": item.reason_code,
        }
        for item in catalog.issues
    ]
    return {
        "capabilities": capabilities,
        "enabled_plugin_ids": list(catalog.enabled_plugin_ids),
        "entry_points": entry_points,
        "issues": issues,
        "plugins": plugins,
        "profile_id": DISCOVERY_PROFILE_ID,
    }


def canonical_profile_json(data: JsonObject) -> str:
    """Encode normalized profile evidence without locale or spacing variance."""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compatibility_receipt_data(
    plugin: LoadedPluginV1,
    *,
    profile_results: tuple[CompatibilityProfileResultV1, ...],
    python_implementation: str,
    python_version: str,
    operating_system: str,
    architecture: str,
) -> JsonObject:
    """Build a deterministic self-attestation without local or source details."""
    if not isinstance(profile_results, tuple) or not all(
        isinstance(item, CompatibilityProfileResultV1) for item in profile_results
    ):
        raise ValueError("profile_results must be a tuple of executed results")
    normalized_results = tuple(
        sorted(profile_results, key=lambda item: item.profile_id)
    )
    normalized_profiles = tuple(item.profile_id for item in normalized_results)
    if (
        not normalized_profiles
        or len(normalized_profiles) != len(set(normalized_profiles))
        or any(item not in COMPATIBILITY_PROFILE_IDS for item in normalized_profiles)
    ):
        raise ValueError(
            "profile_results must name unique supported compatibility profiles"
        )
    conforms = all(item.passed for item in normalized_results)
    manifest = plugin.manifest
    dependencies: list[JsonValue] = []
    backends: list[JsonValue] = []
    components: list[JsonValue] = []
    for capability in manifest.capabilities:
        dependencies.extend(
            {
                "capability_id": capability.capability_id,
                "distribution_name": dependency.distribution_name,
                "optional": dependency.optional,
                "version_specifier": dependency.version_specifier,
            }
            for dependency in capability.runtime_dependencies
        )
        if capability.backend_id is not None:
            backends.append(
                {
                    "backend_id": capability.backend_id,
                    "backend_version": capability.backend_version,
                    "capability_id": capability.capability_id,
                }
            )
        components.extend(
            {
                "capability_id": capability.capability_id,
                "component_id": component.component_id,
                "component_version": component.component_version,
                "kind": component.kind.value,
                "optional": component.optional,
            }
            for component in capability.components
        )
    entry_point = plugin.entry_point
    supported_platforms: list[JsonValue] = list(
        sorted(
            {
                platform
                for capability in manifest.capabilities
                for platform in capability.supported_platforms
            }
        )
    )
    supported_python_versions: list[JsonValue] = list(
        sorted(
            {
                version
                for capability in manifest.capabilities
                for version in capability.supported_python_versions
            }
        )
    )
    negotiated_host_features: list[JsonValue] = list(plugin.negotiated_host_features)
    normalized_profile_values: list[JsonValue] = list(normalized_profiles)
    receipt_profile_results: list[JsonValue] = [
        {
            "profile_id": item.profile_id,
            "result": "passed" if item.passed else "failed",
            "summary": item.summary,
        }
        for item in normalized_results
    ]
    receipt: JsonObject = {
        "claims": (
            [
                "conforms to Platydiff plugin profile "
                f"{profile_id} under suite version {COMPATIBILITY_SUITE_VERSION}."
                for profile_id in normalized_profiles
            ]
            if conforms
            else []
        ),
        "environment": {
            "architecture": _receipt_environment_text(architecture),
            "operating_system": _receipt_environment_text(operating_system),
            "python_implementation": _receipt_environment_text(python_implementation),
            "python_version": _receipt_environment_text(python_version),
        },
        "host": {
            "distribution_name": "platydiff",
            "outcome_schema_versions": [1, 2],
            "plugin_api_major": PLUGIN_API_MAJOR,
            "plugin_api_minor": PLUGIN_API_MINOR,
            "version": __version__,
        },
        "inventory": {
            "backends": backends,
            "components": components,
            "license_expression": manifest.license_expression,
            "runtime_dependencies": dependencies,
            "supported_platforms": supported_platforms,
            "supported_python_versions": supported_python_versions,
        },
        "plugin": {
            "api_major": manifest.api_major,
            "distribution_name": entry_point.distribution_name,
            "distribution_version": entry_point.distribution_version,
            "manifest_schema_version": manifest.manifest_schema_version,
            "negotiated_api_minor": plugin.negotiated_api_minor,
            "negotiated_host_features": negotiated_host_features,
            "plugin_id": manifest.plugin_id,
            "plugin_version": manifest.plugin_version,
        },
        "profile_results": receipt_profile_results,
        "receipt_schema_version": 1,
        "result": "conforms" if conforms else "does_not_conform",
        "suite": {
            "name": "platydiff-plugin-compatibility",
            "profile_ids": normalized_profile_values,
            "version": COMPATIBILITY_SUITE_VERSION,
        },
    }
    digest = sha256(canonical_profile_json(receipt).encode("utf-8")).hexdigest()
    return {**receipt, "digest": f"sha256:{digest}"}
