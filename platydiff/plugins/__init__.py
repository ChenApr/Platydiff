"""Explicit third-party plugin discovery and host-owned execution."""

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
from platydiff.plugins._host import PluginHost

__all__ = [
    "DiscoveredCapabilityV1",
    "LoadedPluginV1",
    "PluginCatalogV1",
    "PluginDiscoveryIssueV1",
    "PluginDiscoveryPolicy",
    "PluginDiscoveryReason",
    "PluginEntryPointV1",
    "PluginHost",
    "discover_plugins",
]
