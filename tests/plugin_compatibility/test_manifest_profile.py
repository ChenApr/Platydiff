"""P3-A manifest compatibility profile."""

from __future__ import annotations

from dataclasses import fields

import pytest

from platydiff.plugin_sdk import (
    PLUGIN_API_MINOR,
    CapabilityDeclarationV1,
    CapabilityKind,
    ComponentDeclarationV1,
    ComponentKind,
    PluginManifestV1,
    RuntimeDependencyV1,
)
from tests.plugin_compatibility.profiles import (
    canonical_profile_json,
    manifest_profile_data,
)

_GOLDEN_MANIFEST = (
    '{"api_major":1,"capabilities":[{"backend_id":'
    '"org.example.scidiff.python","backend_version":"3.12",'
    '"capability_id":"org.example.scidiff.text_exact","components":'
    '[{"component_id":"ffmpeg","component_version":"7","kind":"external",'
    '"optional":true}],"implementation_version":"1.0","kind":"comparator",'
    '"priority":7,"runtime_dependencies":[{"distribution_name":"numpy",'
    '"optional":false,"version_specifier":">=2"}],"supported_platforms":'
    '["darwin-arm64","linux-x86_64"],"supported_python_versions":[">=3.12"]}],'
    '"license_expression":"Apache-2.0","manifest_schema_version":1,'
    '"maximum_api_minor":0,"minimum_api_minor":0,"plugin_id":'
    '"org.example.scidiff","plugin_version":"1.0","profile_id":'
    '"platydiff.p3a.manifest.v1","required_host_features":[]}'
)


def _golden_manifest() -> PluginManifestV1:
    return PluginManifestV1(
        manifest_schema_version=1,
        plugin_id="org.example.scidiff",
        plugin_version="1.0",
        api_major=1,
        minimum_api_minor=0,
        maximum_api_minor=0,
        required_host_features=(),
        capabilities=(
            CapabilityDeclarationV1(
                capability_id="org.example.scidiff.text_exact",
                kind=CapabilityKind.COMPARATOR,
                implementation_version="1.0",
                backend_id="org.example.scidiff.python",
                backend_version="3.12",
                priority=7,
                runtime_dependencies=(RuntimeDependencyV1("numpy", ">=2"),),
                supported_python_versions=(">=3.12",),
                supported_platforms=("linux-x86_64", "darwin-arm64"),
                components=(
                    ComponentDeclarationV1(
                        "ffmpeg", "7", ComponentKind.EXTERNAL, optional=True
                    ),
                ),
            ),
        ),
        license_expression="Apache-2.0",
    )


def test_manifest_profile_has_exact_golden_evidence() -> None:
    assert canonical_profile_json(manifest_profile_data(_golden_manifest())) == (
        _GOLDEN_MANIFEST
    )


def test_api_minor_zero_is_a_declaration_only_compatibility_baseline() -> None:
    assert PLUGIN_API_MINOR == 0
    field_names = {item.name for item in fields(CapabilityDeclarationV1)}
    assert field_names.isdisjoint(
        {
            "callback",
            "comparator",
            "detector",
            "executor",
            "renderer",
            "source_service",
        }
    )


@pytest.mark.parametrize(
    "field",
    [
        "plugin_version",
        "implementation_version",
        "backend_version",
        "component_version",
    ],
)
def test_manifest_profile_rejects_local_paths_in_provider_inventory(
    field: str,
) -> None:
    manifest = _golden_manifest()
    capability = manifest.capabilities[0]
    component = capability.components[0]
    with pytest.raises(ValueError, match="filesystem path"):
        if field == "plugin_version":
            PluginManifestV1(
                1,
                manifest.plugin_id,
                "/private/plugin.py",
                1,
                0,
                0,
                (),
                (),
                "Apache-2.0",
            )
        elif field == "implementation_version":
            CapabilityDeclarationV1(
                capability.capability_id,
                capability.kind,
                "/private/plugin.py",
            )
        elif field == "backend_version":
            CapabilityDeclarationV1(
                capability.capability_id,
                capability.kind,
                capability.implementation_version,
                capability.backend_id,
                "/private/backend",
            )
        else:
            ComponentDeclarationV1(
                component.component_id,
                "/private/component",
                component.kind,
            )


def test_manifest_profile_keeps_distribution_and_plugin_versions_separate() -> None:
    data = manifest_profile_data(_golden_manifest())
    assert data["plugin_version"] == "1.0"
    assert "distribution_version" not in data


@pytest.mark.parametrize(
    "field",
    [
        "license_expression",
        "version_specifier",
        "supported_python_versions",
        "supported_platforms",
    ],
)
def test_manifest_profile_rejects_paths_in_all_serialized_inventory(
    field: str,
) -> None:
    with pytest.raises(ValueError, match="filesystem path"):
        if field == "license_expression":
            PluginManifestV1(
                1,
                "org.example.scidiff",
                "1",
                1,
                0,
                0,
                (),
                (),
                "/local/license",
            )
        elif field == "version_specifier":
            RuntimeDependencyV1("numpy", "/local/version")
        elif field == "supported_python_versions":
            CapabilityDeclarationV1(
                "org.example.scidiff.text_exact",
                CapabilityKind.COMPARATOR,
                "1",
                supported_python_versions=("/local/python",),
            )
        else:
            CapabilityDeclarationV1(
                "org.example.scidiff.text_exact",
                CapabilityKind.COMPARATOR,
                "1",
                supported_platforms=(r"C:\\local\\platform",),
            )


@pytest.mark.parametrize(
    "field",
    [
        "license_expression",
        "version_specifier",
        "supported_python_versions",
        "supported_platforms",
    ],
)
def test_manifest_profile_rejects_controls_in_all_serialized_inventory(
    field: str,
) -> None:
    with pytest.raises(ValueError, match="control"):
        if field == "license_expression":
            PluginManifestV1(
                1,
                "org.example.scidiff",
                "1",
                1,
                0,
                0,
                (),
                (),
                "Apache-2.0\n",
            )
        elif field == "version_specifier":
            RuntimeDependencyV1("numpy", ">=2\n")
        elif field == "supported_python_versions":
            CapabilityDeclarationV1(
                "org.example.scidiff.text_exact",
                CapabilityKind.COMPARATOR,
                "1",
                supported_python_versions=(">=3.12\n",),
            )
        else:
            CapabilityDeclarationV1(
                "org.example.scidiff.text_exact",
                CapabilityKind.COMPARATOR,
                "1",
                supported_platforms=("linux\x7f",),
            )


@pytest.mark.parametrize("distribution_name", ["friendly--bard", "FrIeNdLy-._.-bArD"])
def test_dependency_accepts_pypa_separator_runs(distribution_name: str) -> None:
    dependency = RuntimeDependencyV1(distribution_name, ">=1")
    capability = CapabilityDeclarationV1(
        "org.example.scidiff.text_exact",
        CapabilityKind.COMPARATOR,
        "1",
        runtime_dependencies=(dependency,),
    )
    assert capability.runtime_dependencies[0].distribution_name == distribution_name


def test_dependency_separator_runs_preserve_normalized_collision_detection() -> None:
    with pytest.raises(ValueError, match="unique after normalization"):
        CapabilityDeclarationV1(
            "org.example.scidiff.text_exact",
            CapabilityKind.COMPARATOR,
            "1",
            runtime_dependencies=(
                RuntimeDependencyV1("friendly--bard", ">=1"),
                RuntimeDependencyV1("FrIeNdLy-._.-bArD", ">=1"),
            ),
        )


@pytest.mark.parametrize(
    "distribution_name",
    ["-leading", "trailing_", ".period", "newline\n", "café", ""],
)
def test_dependency_rejects_invalid_pypa_distribution_names(
    distribution_name: str,
) -> None:
    with pytest.raises(ValueError):
        RuntimeDependencyV1(distribution_name, ">=1")
