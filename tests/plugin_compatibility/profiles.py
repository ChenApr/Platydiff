"""Canonical evidence projections for the P3-A compatibility profiles."""

from __future__ import annotations

import json

from platydiff.plugin_sdk import PluginManifestV1
from platydiff.plugins import PluginCatalogV1

type JsonPrimitive = bool | int | str | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]

MANIFEST_PROFILE_ID = "platydiff.p3a.manifest.v1"
DISCOVERY_PROFILE_ID = "platydiff.p3a.discovery.v1"


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
