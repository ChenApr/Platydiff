"""Public plugin SDK manifest and capability declaration tests."""

from dataclasses import FrozenInstanceError

import pytest

from platydiff.plugin_sdk import (
    PLUGIN_API_MAJOR,
    PLUGIN_API_MINOR,
    PLUGIN_ENTRY_POINT_GROUP,
    PLUGIN_MANIFEST_SCHEMA_VERSION,
    CapabilityDeclarationV1,
    CapabilityKind,
    ComponentDeclarationV1,
    ComponentKind,
    PluginManifestV1,
    RuntimeDependencyV1,
)


def _capability(
    capability_id: str = "org.example.scidiff.text_exact",
    *,
    backend_id: str | None = "org.example.scidiff.python",
) -> CapabilityDeclarationV1:
    return CapabilityDeclarationV1(
        capability_id=capability_id,
        kind=CapabilityKind.COMPARATOR,
        implementation_version="1.0",
        backend_id=backend_id,
        backend_version="3.12" if backend_id is not None else None,
        priority=10,
        runtime_dependencies=(
            RuntimeDependencyV1("SciPy", ">=1.14", optional=True),
            RuntimeDependencyV1("numpy", ">=2"),
        ),
        supported_python_versions=(">=3.12",),
        supported_platforms=("linux-x86_64", "darwin-arm64"),
        components=(
            ComponentDeclarationV1(
                "ffmpeg", "7", ComponentKind.EXTERNAL, optional=True
            ),
        ),
    )


def _manifest(
    *,
    plugin_id: str = "org.example.scidiff",
    minimum_api_minor: int = 0,
    maximum_api_minor: int = 0,
    required_host_features: tuple[str, ...] = (),
    capabilities: tuple[CapabilityDeclarationV1, ...] | None = None,
) -> PluginManifestV1:
    return PluginManifestV1(
        manifest_schema_version=PLUGIN_MANIFEST_SCHEMA_VERSION,
        plugin_id=plugin_id,
        plugin_version="1.2.3",
        api_major=PLUGIN_API_MAJOR,
        minimum_api_minor=minimum_api_minor,
        maximum_api_minor=maximum_api_minor,
        required_host_features=required_host_features,
        capabilities=(_capability(),) if capabilities is None else capabilities,
        license_expression="Apache-2.0",
    )


def test_sdk_v1_constants_are_explicit() -> None:
    assert PLUGIN_ENTRY_POINT_GROUP == "platydiff.plugins.v1"
    assert PLUGIN_MANIFEST_SCHEMA_VERSION == 1
    assert PLUGIN_API_MAJOR == 1
    assert PLUGIN_API_MINOR == 0


def test_manifest_is_immutable_and_normalizes_ordered_inventory() -> None:
    manifest = _manifest(required_host_features=("zeta.feature", "alpha.feature"))
    capability = manifest.capabilities[0]
    assert manifest.required_host_features == ("alpha.feature", "zeta.feature")
    assert tuple(
        dependency.distribution_name for dependency in capability.runtime_dependencies
    ) == ("numpy", "SciPy")
    assert capability.supported_platforms == ("darwin-arm64", "linux-x86_64")
    with pytest.raises(FrozenInstanceError):
        manifest.plugin_id = "org.example.changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "plugin_id",
    [
        "example",
        "Org.example",
        "org..example",
        "org.example-plugin",
        "org.example/evil",
    ],
)
def test_manifest_rejects_non_reverse_domain_plugin_ids(plugin_id: str) -> None:
    with pytest.raises(ValueError):
        _manifest(plugin_id=plugin_id, capabilities=())


def test_manifest_requires_plugin_scoped_capability_and_backend_ids() -> None:
    with pytest.raises(ValueError, match="plugin_id prefix"):
        _manifest(capabilities=(_capability("org.other.text_exact"),))
    with pytest.raises(ValueError, match="plugin_id prefix"):
        _manifest(capabilities=(_capability(backend_id="org.other.python"),))


@pytest.mark.parametrize("value", [True, -1, 2**53 + 1])
def test_manifest_rejects_invalid_api_minor_bounds(value: int) -> None:
    with pytest.raises(ValueError):
        _manifest(minimum_api_minor=value)


def test_manifest_rejects_inverted_api_minor_range() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        _manifest(minimum_api_minor=2, maximum_api_minor=1)


def test_manifest_features_must_be_unique_stable_identifiers() -> None:
    with pytest.raises(ValueError, match="unique"):
        _manifest(required_host_features=("feature.a", "feature.a"))
    with pytest.raises(ValueError, match="stable lowercase"):
        _manifest(required_host_features=("Feature.A",))


def test_capability_inventory_is_typed_and_bounded() -> None:
    with pytest.raises(ValueError, match="provided together"):
        CapabilityDeclarationV1(
            capability_id="org.example.scidiff.text_exact",
            kind=CapabilityKind.COMPARATOR,
            implementation_version="1",
            backend_id="org.example.scidiff.python",
        )
    with pytest.raises(ValueError, match="unique after normalization"):
        CapabilityDeclarationV1(
            capability_id="org.example.scidiff.text_exact",
            kind=CapabilityKind.COMPARATOR,
            implementation_version="1",
            runtime_dependencies=(
                RuntimeDependencyV1("my-package", "1"),
                RuntimeDependencyV1("my_package", "2"),
            ),
        )


def test_manifest_rejects_mutable_collections_and_control_text() -> None:
    with pytest.raises(ValueError, match="must be a tuple"):
        _manifest(required_host_features=["feature.a"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="control"):
        PluginManifestV1(
            1,
            "org.example.scidiff",
            "1\n2",
            1,
            0,
            0,
            (),
            (),
            "Apache-2.0",
        )


def test_provider_identity_versions_reject_filesystem_paths() -> None:
    with pytest.raises(ValueError, match="filesystem path"):
        PluginManifestV1(
            1,
            "org.example.scidiff",
            "/private/plugin.py",
            1,
            0,
            0,
            (),
            (),
            "Apache-2.0",
        )
