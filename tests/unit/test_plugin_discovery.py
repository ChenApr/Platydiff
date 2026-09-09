"""Explicit SDK-v1 discovery and negotiation tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

import platydiff
from platydiff import BytesSource, TextCompareSpec, compare
from platydiff.plugin_sdk import (
    CapabilityDeclarationV1,
    CapabilityKind,
    PluginManifestV1,
)
from platydiff.plugins import PluginDiscoveryPolicy, _discovery, discover_plugins


@dataclass(frozen=True)
class _Distribution:
    name: str
    version: str


class _EntryPoint:
    def __init__(
        self,
        name: str,
        factory: object,
        *,
        value: str = "example_plugin:manifest",
        distribution_name: str = "example-plugin",
        distribution_version: str = "1.0",
        load_error: Exception | None = None,
    ) -> None:
        self.name = name
        self.group = "platydiff.plugins.v1"
        self.value = value
        self.dist = _Distribution(distribution_name, distribution_version)
        self.factory = factory
        self.load_error = load_error
        self.load_count = 0

    def load(self) -> object:
        self.load_count += 1
        if self.load_error is not None:
            raise self.load_error
        return self.factory


def _manifest(
    plugin_id: str = "org.example.scidiff",
    *,
    capabilities: tuple[CapabilityDeclarationV1, ...] = (),
    minimum_api_minor: int = 0,
    maximum_api_minor: int = 0,
    required_host_features: tuple[str, ...] = (),
) -> PluginManifestV1:
    return PluginManifestV1(
        1,
        plugin_id,
        "1.0",
        1,
        minimum_api_minor,
        maximum_api_minor,
        required_host_features,
        capabilities,
        "Apache-2.0",
    )


def _install(
    monkeypatch: pytest.MonkeyPatch, entry_points: tuple[_EntryPoint, ...]
) -> None:
    monkeypatch.setattr(_discovery, "_installed_entry_points", lambda: entry_points)


def test_empty_policy_and_builtin_compare_never_load_plugins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry_point = _EntryPoint("org.example.scidiff", lambda: _manifest())
    _install(monkeypatch, (entry_point,))
    outcome = compare(BytesSource(b"same"), BytesSource(b"same"), TextCompareSpec())
    catalog = discover_plugins(PluginDiscoveryPolicy())
    assert outcome.kind == "completed"
    assert entry_point.load_count == 0
    assert catalog.plugins == ()
    assert [issue.reason_code for issue in catalog.issues] == ["plugin_disabled"]


def test_exact_allowlist_loads_and_negotiates_one_manifest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry_point = _EntryPoint("org.example.scidiff", lambda: _manifest())
    _install(monkeypatch, (entry_point,))
    catalog = discover_plugins(
        PluginDiscoveryPolicy(enabled_plugin_ids=("org.example.scidiff",))
    )
    assert entry_point.load_count == 1
    assert [plugin.manifest.plugin_id for plugin in catalog.plugins] == [
        "org.example.scidiff"
    ]
    assert catalog.plugins[0].negotiated_api_minor == 0
    assert catalog.issues == ()


def test_missing_and_malformed_metadata_are_reported_without_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid = _EntryPoint(
        "org.example.invalid",
        lambda: _manifest("org.example.invalid"),
        value="/private/plugin.py:manifest",
    )
    _install(monkeypatch, (invalid,))
    catalog = discover_plugins(
        PluginDiscoveryPolicy(
            enabled_plugin_ids=("org.example.invalid", "org.example.missing")
        )
    )
    assert invalid.load_count == 0
    assert [issue.reason_code for issue in catalog.issues] == [
        "plugin_metadata_invalid",
        "plugin_not_found",
    ]
    assert catalog.issues[0].entry_point_value == ""


def test_duplicate_plugin_ids_quarantine_every_claimant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _EntryPoint("org.example.scidiff", lambda: _manifest())
    second = _EntryPoint(
        "org.example.scidiff",
        lambda: _manifest(),
        distribution_name="other-dist",
    )
    _install(monkeypatch, (second, first))
    catalog = discover_plugins(
        PluginDiscoveryPolicy(enabled_plugin_ids=("org.example.scidiff",))
    )
    assert first.load_count == second.load_count == 0
    assert catalog.plugins == ()
    assert [issue.reason_code for issue in catalog.issues] == [
        "plugin_id_conflict",
        "plugin_id_conflict",
    ]


@pytest.mark.parametrize(
    ("entry_point", "reason"),
    [
        (
            _EntryPoint(
                "org.example.scidiff",
                lambda: _manifest(),
                load_error=ImportError("secret traceback"),
            ),
            "plugin_import_failed",
        ),
        (_EntryPoint("org.example.scidiff", object()), "plugin_factory_failed"),
        (
            _EntryPoint(
                "org.example.scidiff",
                lambda: (_ for _ in ()).throw(RuntimeError("secret traceback")),
            ),
            "plugin_factory_failed",
        ),
        (
            _EntryPoint("org.example.scidiff", lambda: object()),
            "plugin_manifest_invalid",
        ),
        (
            _EntryPoint(
                "org.example.scidiff",
                lambda: _manifest("org.example.other"),
            ),
            "plugin_manifest_invalid",
        ),
        (
            _EntryPoint(
                "org.example.scidiff",
                lambda: _manifest(minimum_api_minor=1, maximum_api_minor=1),
            ),
            "plugin_api_incompatible",
        ),
        (
            _EntryPoint(
                "org.example.scidiff",
                lambda: _manifest(required_host_features=("host.future",)),
            ),
            "plugin_feature_unsupported",
        ),
    ],
)
def test_load_and_negotiation_failures_are_isolated(
    monkeypatch: pytest.MonkeyPatch,
    entry_point: _EntryPoint,
    reason: str,
) -> None:
    _install(monkeypatch, (entry_point,))
    catalog = discover_plugins(
        PluginDiscoveryPolicy(enabled_plugin_ids=("org.example.scidiff",))
    )
    assert catalog.plugins == ()
    assert [issue.reason_code for issue in catalog.issues] == [reason]
    assert "secret" not in repr(catalog)


def test_capability_conflicts_are_removed_without_executing_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capability_id = "org.example.child.compare"
    parent_capability = CapabilityDeclarationV1(
        capability_id,
        CapabilityKind.COMPARATOR,
        "1",
    )
    child_capability = CapabilityDeclarationV1(
        capability_id,
        CapabilityKind.COMPARATOR,
        "1",
    )
    parent = _EntryPoint(
        "org.example",
        lambda: _manifest("org.example", capabilities=(parent_capability,)),
    )
    child = _EntryPoint(
        "org.example.child",
        lambda: _manifest("org.example.child", capabilities=(child_capability,)),
        distribution_name="child-plugin",
    )
    _install(monkeypatch, (child, parent))
    catalog = discover_plugins(
        PluginDiscoveryPolicy(enabled_plugin_ids=("org.example.child", "org.example"))
    )
    assert len(catalog.plugins) == 2
    assert catalog.capabilities == ()
    assert [issue.reason_code for issue in catalog.issues] == [
        "capability_id_conflict",
        "capability_id_conflict",
    ]


def test_discovery_api_is_curated_at_package_root() -> None:
    assert {"PluginCatalogV1", "PluginDiscoveryPolicy", "discover_plugins"}.issubset(
        platydiff.__all__
    )
    assert "CapabilityRequest" not in platydiff.__all__
    assert "CapabilityCatalog" not in platydiff.__all__
