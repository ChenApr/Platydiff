"""Public, versioned declarations for third-party Platydiff plugins.

Importing this module never enumerates or loads installed plugins.
"""

from platydiff.plugin_sdk._models import (
    HOST_FEATURES_V1,
    PLUGIN_API_MAJOR,
    PLUGIN_API_MINOR,
    PLUGIN_ENTRY_POINT_GROUP,
    PLUGIN_MANIFEST_SCHEMA_VERSION,
    CapabilityDeclarationV1,
    CapabilityKind,
    ComponentDeclarationV1,
    ComponentKind,
    PluginManifestFactoryV1,
    PluginManifestV1,
    RuntimeDependencyV1,
)

__all__ = [
    "HOST_FEATURES_V1",
    "PLUGIN_API_MAJOR",
    "PLUGIN_API_MINOR",
    "PLUGIN_ENTRY_POINT_GROUP",
    "PLUGIN_MANIFEST_SCHEMA_VERSION",
    "CapabilityDeclarationV1",
    "CapabilityKind",
    "ComponentDeclarationV1",
    "ComponentKind",
    "PluginManifestFactoryV1",
    "PluginManifestV1",
    "RuntimeDependencyV1",
]
