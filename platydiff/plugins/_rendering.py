"""Host-owned bounded execution for explicitly selected plugin renderers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import cast

from platydiff.core.models import (
    AnyCompareOutcome,
    CompletedOutcome,
    CompletedOutcomeV2,
    FailedOutcome,
    FailedOutcomeV2,
    ProviderIdentity,
    UnavailableOutcome,
    UnavailableOutcomeV2,
)
from platydiff.core.serialization import (
    dumps_outcome,
    outcome_from_data,
    outcome_to_data,
)
from platydiff.plugin_sdk import (
    CapabilityAvailabilityV1,
    CapabilityKind,
    PluginResourceLimitErrorV1,
    PluginUnavailableErrorV1,
    RendererHandleV1,
    RendererPresentationOptionsV1,
)
from platydiff.plugins._discovery import PluginCatalogV1

_OUTCOME_TYPES = (
    CompletedOutcome,
    UnavailableOutcome,
    FailedOutcome,
    CompletedOutcomeV2,
    UnavailableOutcomeV2,
    FailedOutcomeV2,
)
_STABLE_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_MEDIA_TYPE = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*"
    r"(?:;[ ]*[a-z0-9!#$&^_.+-]+=[a-z0-9!#$&^_.+:-]+)*$"
)


def _identity_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise ValueError(f"{field_name} must contain valid Unicode") from error
    if (
        not value
        or len(encoded) > 1024
        or "/" in value
        or "\\" in value
        or any(
            ord(character) < 0x20 or 0x7F <= ord(character) <= 0x9F
            for character in value
        )
    ):
        raise ValueError(f"{field_name} must be bounded, control-free, and path-free")
    return value


def _stable_identifier(value: object, field_name: str) -> str:
    text = _identity_text(value, field_name)
    if len(text.encode("utf-8")) > 255 or not _STABLE_IDENTIFIER.fullmatch(text):
        raise ValueError(f"{field_name} must be a stable lowercase ASCII identifier")
    return text


class RendererError(Exception):
    """Safe typed renderer failure retaining the unchanged comparison outcome."""

    def __init__(
        self,
        outcome: AnyCompareOutcome,
        message: str,
        *,
        reason_code: str,
    ) -> None:
        super().__init__(message)
        self.outcome = outcome
        self.reason_code = reason_code


class RendererUnavailableError(RendererError):
    """The exact requested renderer was unavailable before rendering."""


class RendererExecutionError(RendererError):
    """The selected renderer failed or returned invalid presentation output."""


class RendererOutputLimitError(RendererError):
    """The selected renderer exceeded the host-owned output byte budget."""


@dataclass(frozen=True, slots=True)
class RenderedOutputV1:
    """Bounded presentation bytes plus exact renderer/provider identity."""

    renderer_id: str
    renderer_version: str
    media_type: str
    data: bytes
    is_text: bool
    provider: ProviderIdentity
    backend_id: str | None = None
    backend_version: str | None = None

    def __post_init__(self) -> None:
        renderer_id = _stable_identifier(self.renderer_id, "renderer_id")
        _identity_text(self.renderer_version, "renderer_version")
        if not isinstance(self.media_type, str) or not _MEDIA_TYPE.fullmatch(
            self.media_type
        ):
            raise ValueError("media_type must be a normalized media type")
        if type(self.data) is not bytes:
            raise ValueError("data must be bytes")
        if type(self.is_text) is not bool:
            raise ValueError("is_text must be a boolean")
        if not isinstance(self.provider, ProviderIdentity):
            raise ValueError("provider must be a ProviderIdentity")
        if not renderer_id.startswith(f"{self.provider.plugin_id}."):
            raise ValueError("renderer_id must use the provider plugin namespace")
        if (self.backend_id is None) != (self.backend_version is None):
            raise ValueError("backend_id and backend_version must be provided together")
        if self.backend_id is not None:
            backend_id = _stable_identifier(self.backend_id, "backend_id")
            if not backend_id.startswith(f"{self.provider.plugin_id}."):
                raise ValueError("backend_id must use the provider plugin namespace")
            _identity_text(self.backend_version, "backend_version")
        if self.is_text:
            try:
                self.data.decode("utf-8", errors="strict")
            except UnicodeDecodeError as error:
                raise ValueError("text data must be valid UTF-8") from error

    @property
    def text(self) -> str | None:
        return self.data.decode("utf-8") if self.is_text else None


class _BoundedSink:
    def __init__(self, options: RendererPresentationOptionsV1) -> None:
        self.media_type = options.media_type
        self._maximum = options.max_output_bytes
        self._data = bytearray()
        self._mode: str | None = None
        self._invalid = False
        self._overflowed = False

    @property
    def remaining_bytes(self) -> int:
        return self._maximum - len(self._data)

    @property
    def data(self) -> bytes:
        return bytes(self._data)

    @property
    def is_text(self) -> bool:
        return self._mode != "bytes"

    @property
    def invalid(self) -> bool:
        return self._invalid

    @property
    def overflowed(self) -> bool:
        return self._overflowed

    def write_text(self, value: str) -> None:
        untrusted: object = value
        if not isinstance(untrusted, str):
            self._invalid = True
            raise TypeError("renderer text output must be a string")
        if self._mode is not None and self._mode != "text":
            self._invalid = True
            raise TypeError("renderer output modes must not be mixed")
        if len(value) > self.remaining_bytes:
            self._overflowed = True
            raise PluginResourceLimitErrorV1(
                "The renderer output byte budget was exhausted."
            )
        try:
            encoded = value.encode("utf-8", errors="strict")
        except UnicodeEncodeError:
            self._invalid = True
            raise
        self._write(encoded, "text")

    def write_bytes(self, value: bytes) -> None:
        untrusted: object = value
        if not isinstance(untrusted, bytes):
            self._invalid = True
            raise TypeError("renderer binary output must be bytes")
        self._write(value, "bytes")

    def _write(self, value: bytes, mode: str) -> None:
        if self._mode is not None and self._mode != mode:
            self._invalid = True
            raise TypeError("renderer output modes must not be mixed")
        self._mode = mode
        if len(value) > self.remaining_bytes:
            self._overflowed = True
            raise PluginResourceLimitErrorV1(
                "The renderer output byte budget was exhausted."
            )
        self._data.extend(value)


def _provider(catalog: PluginCatalogV1, plugin_id: str) -> ProviderIdentity:
    plugin = next(
        item for item in catalog.plugins if item.manifest.plugin_id == plugin_id
    )
    return ProviderIdentity(
        plugin_id=plugin.manifest.plugin_id,
        plugin_version=plugin.manifest.plugin_version,
        distribution_name=plugin.entry_point.distribution_name,
        distribution_version=plugin.entry_point.distribution_version,
        manifest_schema_version=plugin.manifest.manifest_schema_version,
        api_major=plugin.manifest.api_major,
        negotiated_api_minor=plugin.negotiated_api_minor,
        negotiated_host_features=plugin.negotiated_host_features,
    )


def _safe_outcome_copy(outcome: AnyCompareOutcome) -> AnyCompareOutcome:
    if not isinstance(outcome, _OUTCOME_TYPES):
        raise TypeError("outcome must be a typed comparison outcome")
    return outcome_from_data(outcome_to_data(outcome))


def render_plugin(
    catalog: PluginCatalogV1,
    outcome: AnyCompareOutcome,
    *,
    renderer_id: str,
    options: RendererPresentationOptionsV1 | None,
) -> RenderedOutputV1:
    """Execute one exact renderer without fallback or comparison authority."""
    presentation = options or RendererPresentationOptionsV1()
    validated = _safe_outcome_copy(outcome)
    before = dumps_outcome(validated)
    capability = next(
        (
            item
            for item in catalog.capabilities
            if item.declaration.capability_id == renderer_id
        ),
        None,
    )
    if capability is None:
        raise RendererUnavailableError(
            outcome,
            "The selected renderer is unavailable.",
            reason_code="renderer_not_found",
        )
    declaration = capability.declaration
    if declaration.kind is not CapabilityKind.RENDERER:
        raise RendererUnavailableError(
            outcome,
            "The selected renderer is unavailable.",
            reason_code="capability_kind_mismatch",
        )
    if capability.handle is None:
        raise RendererUnavailableError(
            outcome,
            "The selected renderer is unavailable.",
            reason_code="executor_missing",
        )
    handle = cast(RendererHandleV1, capability.handle)
    try:
        media_types = handle.media_types
        availability = handle.availability()
    except (KeyboardInterrupt, SystemExit, MemoryError):
        raise
    except PluginUnavailableErrorV1 as error:
        raise RendererUnavailableError(
            outcome,
            "The selected renderer is unavailable.",
            reason_code=error.reason_code,
        ) from error
    except Exception as error:
        raise RendererExecutionError(
            outcome,
            "The selected renderer could not produce output.",
            reason_code="renderer_execution_failure",
        ) from error
    if (
        not isinstance(media_types, tuple)
        or presentation.media_type not in media_types
        or not isinstance(availability, CapabilityAvailabilityV1)
    ):
        raise RendererUnavailableError(
            outcome,
            "The selected renderer is unavailable.",
            reason_code="media_type_unsupported",
        )
    if (
        availability.backend_id,
        availability.backend_version,
    ) != (declaration.backend_id, declaration.backend_version):
        raise RendererExecutionError(
            outcome,
            "The selected renderer could not produce output.",
            reason_code="renderer_execution_failure",
        )
    if not availability.available:
        raise RendererUnavailableError(
            outcome,
            "The selected renderer is unavailable.",
            reason_code=availability.reason_code or "capability_unavailable",
        )
    sink = _BoundedSink(presentation)
    try:
        handle.render(validated, presentation, sink)
    except (KeyboardInterrupt, SystemExit, MemoryError):
        raise
    except PluginResourceLimitErrorV1 as error:
        raise RendererOutputLimitError(
            outcome,
            "The selected renderer exceeded its output limit.",
            reason_code="renderer_output_limit",
        ) from error
    except Exception as error:
        raise RendererExecutionError(
            outcome,
            "The selected renderer could not produce output.",
            reason_code="renderer_execution_failure",
        ) from error
    if sink.overflowed:
        raise RendererOutputLimitError(
            outcome,
            "The selected renderer exceeded its output limit.",
            reason_code="renderer_output_limit",
        )
    try:
        unchanged = dumps_outcome(validated) == before
    except Exception:
        unchanged = False
    if sink.invalid or not unchanged:
        raise RendererExecutionError(
            outcome,
            "The selected renderer could not produce output.",
            reason_code="renderer_execution_failure",
        )
    return RenderedOutputV1(
        renderer_id=renderer_id,
        renderer_version=declaration.implementation_version,
        media_type=presentation.media_type,
        data=sink.data,
        is_text=sink.is_text,
        provider=_provider(catalog, capability.plugin.manifest.plugin_id),
        backend_id=availability.backend_id,
        backend_version=availability.backend_version,
    )
