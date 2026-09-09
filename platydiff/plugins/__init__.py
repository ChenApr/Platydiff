"""Explicit third-party plugin discovery without capability execution."""

from platydiff.plugins._discovery import (
    DiscoveredCapabilityV1,
    LoadedPluginV1,
    PluginCatalogV1,
    PluginDiscoveryIssueV1,
    PluginDiscoveryPolicy,
    PluginDiscoveryReason,
    PluginEntryPointV1,
    discover_plugins,
)

__all__ = [
    "DiscoveredCapabilityV1",
    "LoadedPluginV1",
    "PluginCatalogV1",
    "PluginDiscoveryIssueV1",
    "PluginDiscoveryPolicy",
    "PluginDiscoveryReason",
    "PluginEntryPointV1",
    "discover_plugins",
]
