"""Deterministic machine-readable P3 compatibility receipt profile."""

from __future__ import annotations

from hashlib import sha256

import pytest

from platydiff.plugin_sdk import (
    CapabilityDeclarationV1,
    CapabilityKind,
    ComponentDeclarationV1,
    ComponentKind,
    PluginManifestV1,
    RuntimeDependencyV1,
)
from platydiff.plugins import LoadedPluginV1, PluginEntryPointV1
from tests.plugin_compatibility.profiles import (
    COMPATIBILITY_SUITE_VERSION,
    ISOLATION_PROFILE_ID,
    MANIFEST_PROFILE_ID,
    RENDERER_PROFILE_ID,
    JsonObject,
    canonical_profile_json,
    compatibility_receipt_data,
)


def _loaded_plugin() -> LoadedPluginV1:
    declaration = CapabilityDeclarationV1(
        "org.example.scidiff.render_text",
        CapabilityKind.RENDERER,
        "2",
        "org.example.scidiff.stdlib",
        "3.12",
        runtime_dependencies=(RuntimeDependencyV1("example-runtime", ">=4"),),
        supported_python_versions=(">=3.12",),
        supported_platforms=("darwin-arm64", "linux-x86_64"),
        components=(
            ComponentDeclarationV1(
                "example_tool", "7", ComponentKind.EXTERNAL, optional=True
            ),
        ),
    )
    manifest = PluginManifestV1(
        1,
        "org.example.scidiff",
        "2.1",
        1,
        0,
        1,
        ("host.execution.v1",),
        (declaration,),
        "Apache-2.0",
    )
    entry_point = PluginEntryPointV1(
        "org.example.scidiff",
        "platydiff.plugins.v1",
        "example_plugin:manifest",
        "example-plugin",
        "2.1",
    )
    return LoadedPluginV1(entry_point, manifest, 1, ("host.execution.v1",))


def _receipt(*profile_ids: str) -> JsonObject:
    return compatibility_receipt_data(
        _loaded_plugin(),
        profile_ids=profile_ids,
        python_implementation="cpython",
        python_version="3.12.10",
        operating_system="darwin",
        architecture="arm64",
    )


def test_receipt_is_deterministic_and_digest_covers_normalized_results() -> None:
    first = _receipt(RENDERER_PROFILE_ID, MANIFEST_PROFILE_ID, ISOLATION_PROFILE_ID)
    second = _receipt(ISOLATION_PROFILE_ID, RENDERER_PROFILE_ID, MANIFEST_PROFILE_ID)
    assert first == second
    digest = first.pop("digest")
    assert (
        digest
        == "sha256:" + sha256(canonical_profile_json(first).encode("utf-8")).hexdigest()
    )


def test_receipt_records_exact_identity_inventory_platform_and_profiles() -> None:
    receipt = _receipt(RENDERER_PROFILE_ID, MANIFEST_PROFILE_ID)
    assert receipt["receipt_schema_version"] == 1
    assert receipt["result"] == "conforms"
    suite = receipt["suite"]
    plugin = receipt["plugin"]
    environment = receipt["environment"]
    inventory = receipt["inventory"]
    assert isinstance(suite, dict)
    assert isinstance(plugin, dict)
    assert isinstance(environment, dict)
    assert isinstance(inventory, dict)
    assert suite == {
        "name": "platydiff-plugin-compatibility",
        "profile_ids": [MANIFEST_PROFILE_ID, RENDERER_PROFILE_ID],
        "version": COMPATIBILITY_SUITE_VERSION,
    }
    assert plugin["plugin_id"] == "org.example.scidiff"
    assert plugin["plugin_version"] == "2.1"
    assert plugin["distribution_name"] == "example-plugin"
    assert plugin["distribution_version"] == "2.1"
    assert plugin["negotiated_api_minor"] == 1
    assert environment == {
        "architecture": "arm64",
        "operating_system": "darwin",
        "python_implementation": "cpython",
        "python_version": "3.12.10",
    }
    assert inventory["license_expression"] == "Apache-2.0"
    assert inventory["runtime_dependencies"] == [
        {
            "capability_id": "org.example.scidiff.render_text",
            "distribution_name": "example-runtime",
            "optional": False,
            "version_specifier": ">=4",
        }
    ]
    assert inventory["backends"] == [
        {
            "backend_id": "org.example.scidiff.stdlib",
            "backend_version": "3.12",
            "capability_id": "org.example.scidiff.render_text",
        }
    ]
    assert inventory["components"] == [
        {
            "capability_id": "org.example.scidiff.render_text",
            "component_id": "example_tool",
            "component_version": "7",
            "kind": "external",
            "optional": True,
        }
    ]


def test_receipt_claims_only_conformance_not_certification_or_endorsement() -> None:
    receipt = _receipt(RENDERER_PROFILE_ID, MANIFEST_PROFILE_ID)
    claims = receipt["claims"]
    assert isinstance(claims, list)
    assert claims == [
        f"conforms to Platydiff plugin profile {MANIFEST_PROFILE_ID} "
        f"under suite version {COMPATIBILITY_SUITE_VERSION}.",
        f"conforms to Platydiff plugin profile {RENDERER_PROFILE_ID} "
        f"under suite version {COMPATIBILITY_SUITE_VERSION}.",
    ]
    encoded = canonical_profile_json(receipt).lower()
    for forbidden in ("certified", "endorsed", "security-reviewed"):
        assert forbidden not in encoded


def test_receipt_contains_no_source_or_local_environment_fields() -> None:
    receipt = _receipt(RENDERER_PROFILE_ID, MANIFEST_PROFILE_ID)

    def all_keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return {
                *(str(key) for key in value),
                *(key for item in value.values() for key in all_keys(item)),
            }
        if isinstance(value, list):
            return {key for item in value for key in all_keys(item)}
        return set()

    assert all_keys(receipt).isdisjoint(
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


@pytest.mark.parametrize(
    "profile_ids",
    [(), (MANIFEST_PROFILE_ID, MANIFEST_PROFILE_ID), ("unknown.profile",)],
)
def test_receipt_requires_unique_supported_profiles(
    profile_ids: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError, match="profile_ids"):
        compatibility_receipt_data(
            _loaded_plugin(),
            profile_ids=profile_ids,
            python_implementation="cpython",
            python_version="3.12.10",
            operating_system="darwin",
            architecture="arm64",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("python_implementation", "cpython\x1b"),
        ("python_version", "/Users/alice/private"),
        ("operating_system", r"C:\\private"),
        ("architecture", "arm64\nsecret"),
    ],
)
def test_receipt_rejects_local_paths_and_controls(field: str, value: str) -> None:
    environment = {
        "python_implementation": "cpython",
        "python_version": "3.12.10",
        "operating_system": "darwin",
        "architecture": "arm64",
    }
    environment[field] = value
    with pytest.raises(ValueError, match="receipt environment"):
        compatibility_receipt_data(
            _loaded_plugin(),
            profile_ids=(MANIFEST_PROFILE_ID,),
            **environment,
        )
