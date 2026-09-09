"""P3-A discovery, isolation, conflict, and ordering compatibility profile."""

from __future__ import annotations

import random
import subprocess
import sys

import pytest

from platydiff.plugin_sdk import (
    CapabilityDeclarationV1,
    CapabilityKind,
    PluginManifestV1,
)
from platydiff.plugins import PluginDiscoveryPolicy, _discovery, discover_plugins
from tests.plugin_compatibility.fakes import FakeEntryPoint
from tests.plugin_compatibility.profiles import (
    canonical_profile_json,
    catalog_profile_data,
)


def _manifest(
    plugin_id: str,
    *,
    capabilities: tuple[CapabilityDeclarationV1, ...] = (),
) -> PluginManifestV1:
    return PluginManifestV1(
        1,
        plugin_id,
        "1.0",
        1,
        0,
        0,
        (),
        capabilities,
        "Apache-2.0",
    )


def _install(
    monkeypatch: pytest.MonkeyPatch, entry_points: tuple[FakeEntryPoint, ...]
) -> None:
    monkeypatch.setattr(_discovery, "_installed_entry_points", lambda: entry_points)


def test_import_and_builtin_compare_do_not_enumerate_entry_points() -> None:
    script = """
from importlib import metadata

def forbidden(*args, **kwargs):
    raise AssertionError("entry points were enumerated")

metadata.entry_points = forbidden
import platydiff
outcome = platydiff.compare(
    platydiff.TextSource("same"),
    platydiff.TextSource("same"),
    platydiff.TextCompareSpec(),
)
assert outcome.kind == "completed"
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr


def test_randomized_enumeration_has_identical_normalized_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = [
        FakeEntryPoint(
            "org.example.alpha",
            lambda: _manifest("org.example.alpha"),
            distribution_name="Zeta.Plugin",
            distribution_version="2",
            value="alpha_plugin:manifest",
        ),
        FakeEntryPoint(
            "org.example.beta",
            lambda: _manifest("org.example.beta"),
            distribution_name="alpha-plugin",
            distribution_version="10",
            value="beta_plugin:manifest",
        ),
        FakeEntryPoint(
            "org.example.disabled",
            lambda: _manifest("org.example.disabled"),
            distribution_name="disabled-plugin",
        ),
    ]
    observed: set[str] = set()
    for seed in range(20):
        shuffled = entries.copy()
        random.Random(seed).shuffle(shuffled)
        _install(monkeypatch, tuple(shuffled))
        catalog = discover_plugins(
            PluginDiscoveryPolicy(
                enabled_plugin_ids=("org.example.beta", "org.example.alpha")
            )
        )
        observed.add(canonical_profile_json(catalog_profile_data(catalog)))
    assert len(observed) == 1


def test_issue_order_uses_normalized_distribution_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zeta = FakeEntryPoint(
        "org.example.conflict",
        lambda: _manifest("org.example.conflict"),
        distribution_name="zeta_plugin",
    )
    alpha = FakeEntryPoint(
        "org.example.conflict",
        lambda: _manifest("org.example.conflict"),
        distribution_name="Alpha.Plugin",
    )
    _install(monkeypatch, (zeta, alpha))
    catalog = discover_plugins(PluginDiscoveryPolicy(("org.example.conflict",)))
    assert [issue.distribution_name for issue in catalog.issues] == [
        "Alpha.Plugin",
        "zeta_plugin",
    ]
    assert alpha.load_count == zeta.load_count == 0


def test_one_factory_failure_does_not_discard_another_plugin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed = FakeEntryPoint(
        "org.example.failed",
        lambda: (_ for _ in ()).throw(RuntimeError("private detail")),
        distribution_name="failed-plugin",
    )
    loaded = FakeEntryPoint(
        "org.example.loaded",
        lambda: _manifest("org.example.loaded"),
        distribution_name="loaded-plugin",
    )
    _install(monkeypatch, (failed, loaded))
    catalog = discover_plugins(
        PluginDiscoveryPolicy(("org.example.loaded", "org.example.failed"))
    )
    assert [plugin.manifest.plugin_id for plugin in catalog.plugins] == [
        "org.example.loaded"
    ]
    assert [issue.reason_code for issue in catalog.issues] == ["plugin_factory_failed"]
    assert "private detail" not in repr(catalog)


@pytest.mark.parametrize(
    ("entry_point", "expected_plugin_id"),
    [
        (
            FakeEntryPoint(
                "not-reverse-domain",
                lambda: object(),
            ),
            "not-reverse-domain",
        ),
        (
            FakeEntryPoint(
                "org.example.badgroup",
                lambda: object(),
                group="platydiff.detectors",
            ),
            "org.example.badgroup",
        ),
        (
            FakeEntryPoint(
                "org.example.badvalue",
                lambda: object(),
                value="module_without_factory",
            ),
            "org.example.badvalue",
        ),
        (
            FakeEntryPoint(
                "org.example.baddist",
                lambda: object(),
                distribution_name="bad distribution",
            ),
            "org.example.baddist",
        ),
        (
            FakeEntryPoint(
                "org.example.badversion",
                lambda: object(),
                distribution_version="/private/environment",
            ),
            "org.example.badversion",
        ),
    ],
)
def test_malformed_metadata_is_quarantined_before_import(
    monkeypatch: pytest.MonkeyPatch,
    entry_point: FakeEntryPoint,
    expected_plugin_id: str,
) -> None:
    _install(monkeypatch, (entry_point,))
    catalog = discover_plugins(PluginDiscoveryPolicy())
    assert entry_point.load_count == 0
    assert catalog.issues[0].reason_code == "plugin_metadata_invalid"
    assert catalog.issues[0].plugin_id == expected_plugin_id
    assert "/private" not in repr(catalog)


def test_missing_or_broken_distribution_metadata_isolated_per_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = FakeEntryPoint("org.example.missingdist", lambda: object())
    missing.dist = None

    class BrokenEntryPoint:
        @property
        def name(self) -> str:
            raise RuntimeError("metadata failure")

        @property
        def group(self) -> str:
            return "platydiff.plugins.v1"

        @property
        def value(self) -> str:
            return "broken_plugin:manifest"

        @property
        def dist(self) -> None:
            return None

        def load(self) -> object:
            raise AssertionError("malformed metadata must not load")

    monkeypatch.setattr(
        _discovery,
        "_installed_entry_points",
        lambda: (missing, BrokenEntryPoint()),
    )
    catalog = discover_plugins(PluginDiscoveryPolicy())
    assert missing.load_count == 0
    assert [issue.reason_code for issue in catalog.issues] == [
        "plugin_metadata_invalid",
        "plugin_metadata_invalid",
    ]


def test_duplicate_capabilities_within_one_manifest_are_quarantined(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capability = CapabilityDeclarationV1(
        "org.example.scidiff.text_exact", CapabilityKind.COMPARATOR, "1"
    )
    entry_point = FakeEntryPoint(
        "org.example.scidiff",
        lambda: _manifest("org.example.scidiff", capabilities=(capability, capability)),
    )
    _install(monkeypatch, (entry_point,))
    catalog = discover_plugins(PluginDiscoveryPolicy(("org.example.scidiff",)))
    assert len(catalog.plugins) == 1
    assert catalog.capabilities == ()
    assert [issue.reason_code for issue in catalog.issues] == ["capability_id_conflict"]


def test_core_namespace_capability_is_quarantined(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capability = CapabilityDeclarationV1(
        "core.example.compare", CapabilityKind.COMPARATOR, "1"
    )
    entry_point = FakeEntryPoint(
        "core.example",
        lambda: _manifest("core.example", capabilities=(capability,)),
    )
    _install(monkeypatch, (entry_point,))
    catalog = discover_plugins(PluginDiscoveryPolicy(("core.example",)))
    assert catalog.capabilities == ()
    assert catalog.issues[0].reason_code == "capability_id_conflict"


@pytest.mark.parametrize(
    "interrupt",
    [KeyboardInterrupt(), SystemExit(4), MemoryError()],
)
def test_process_control_exceptions_from_import_propagate(
    monkeypatch: pytest.MonkeyPatch, interrupt: BaseException
) -> None:
    entry_point = FakeEntryPoint(
        "org.example.scidiff", lambda: _manifest("org.example.scidiff")
    )

    def interrupting_load() -> object:
        raise interrupt

    entry_point.load = interrupting_load  # type: ignore[method-assign]
    _install(monkeypatch, (entry_point,))
    with pytest.raises(type(interrupt)):
        discover_plugins(PluginDiscoveryPolicy(("org.example.scidiff",)))


@pytest.mark.parametrize(
    "interrupt",
    [KeyboardInterrupt(), SystemExit(4), MemoryError()],
)
def test_process_control_exceptions_from_factory_propagate(
    monkeypatch: pytest.MonkeyPatch, interrupt: BaseException
) -> None:
    def factory() -> PluginManifestV1:
        raise interrupt

    entry_point = FakeEntryPoint("org.example.scidiff", factory)
    _install(monkeypatch, (entry_point,))
    with pytest.raises(type(interrupt)):
        discover_plugins(PluginDiscoveryPolicy(("org.example.scidiff",)))


def test_mutated_typed_manifest_is_revalidated_and_quarantined(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest("org.example.scidiff")
    object.__setattr__(manifest, "plugin_version", "/private/plugin.py")
    entry_point = FakeEntryPoint("org.example.scidiff", lambda: manifest)
    _install(monkeypatch, (entry_point,))
    catalog = discover_plugins(PluginDiscoveryPolicy(("org.example.scidiff",)))
    assert catalog.plugins == ()
    assert catalog.issues[0].reason_code == "plugin_manifest_invalid"
    assert "/private" not in repr(catalog)
