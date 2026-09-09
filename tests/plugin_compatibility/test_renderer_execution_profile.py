"""P3-C renderer authority, output bounds, and failure compatibility profile."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from platydiff import CompletedOutcome, PluginHost, TextCompareSpec, TextSource, compare
from platydiff.core.models import AnyCompareOutcome
from platydiff.core.serialization import dumps_outcome
from platydiff.plugin_sdk import (
    CapabilityAvailabilityV1,
    CapabilityKind,
    RendererHandleV1,
    RendererPresentationOptionsV1,
    RendererSinkV1,
)
from platydiff.plugins import (
    RendererExecutionError,
    RendererOutputLimitError,
    RendererUnavailableError,
)
from tests.plugin_compatibility.profiles import terminal_text_is_safe
from tests.unit.test_plugin_host_execution import _capability


@dataclass
class _Renderer:
    capability_id: str = "org.example.scidiff.safe_text"
    media_types: tuple[str, ...] = ("text/plain; charset=utf-8",)
    seen: list[AnyCompareOutcome] = field(default_factory=list)

    def availability(self) -> CapabilityAvailabilityV1:
        return CapabilityAvailabilityV1(
            True,
            "org.example.scidiff.stdlib",
            "1",
        )

    def render(
        self,
        outcome: AnyCompareOutcome,
        options: RendererPresentationOptionsV1,
        sink: RendererSinkV1,
    ) -> None:
        self.seen.append(outcome)
        assert not hasattr(options, "source")
        assert not hasattr(sink, "path")
        assert not hasattr(sink, "registry")
        assert not hasattr(sink, "compare")
        sink.write_text(f"{outcome.kind}:{outcome.schema_version}")


def _outcome() -> CompletedOutcome:
    outcome = compare(TextSource("same"), TextSource("same"), TextCompareSpec())
    assert isinstance(outcome, CompletedOutcome)
    return outcome


def _renderer_host(
    renderer: RendererHandleV1,
) -> PluginHost:
    return _capability(renderer, CapabilityKind.RENDERER, backend=True)[0]


def test_renderer_receives_only_validated_outcome_options_and_bounded_sink() -> None:
    renderer = _Renderer()
    host = _renderer_host(renderer)
    outcome = _outcome()
    before = dumps_outcome(outcome)
    rendered = host.render(
        outcome,
        renderer_id=renderer.capability_id,
        options=RendererPresentationOptionsV1(
            media_type="text/plain; charset=utf-8",
            max_output_bytes=64,
        ),
    )

    assert renderer.seen == [outcome]
    assert dumps_outcome(outcome) == before
    assert rendered.renderer_id == renderer.capability_id
    assert rendered.media_type == "text/plain; charset=utf-8"
    assert rendered.text == "completed:1"
    assert rendered.data == b"completed:1"
    assert rendered.provider.plugin_id == "org.example.scidiff"


def test_renderer_sink_supports_exact_bounded_utf8_and_binary_output() -> None:
    @dataclass
    class BoundaryRenderer(_Renderer):
        media_types: tuple[str, ...] = (
            "application/octet-stream",
            "text/plain; charset=utf-8",
        )

        def render(
            self,
            outcome: AnyCompareOutcome,
            options: RendererPresentationOptionsV1,
            sink: RendererSinkV1,
        ) -> None:
            del outcome
            if options.media_type == "application/octet-stream":
                sink.write_bytes(b"\x00\xff")
            else:
                sink.write_text("界")

    renderer = BoundaryRenderer()
    host = _renderer_host(renderer)
    text = host.render(
        _outcome(),
        renderer_id=renderer.capability_id,
        options=RendererPresentationOptionsV1(
            "text/plain; charset=utf-8", len("界".encode())
        ),
    )
    binary = host.render(
        _outcome(),
        renderer_id=renderer.capability_id,
        options=RendererPresentationOptionsV1("application/octet-stream", 2),
    )
    assert text.text == "界"
    assert binary.text is None
    assert binary.data == b"\x00\xff"


def test_renderer_output_overflow_is_typed_safe_and_preserves_outcome() -> None:
    renderer = _Renderer()
    host = _renderer_host(renderer)
    outcome = _outcome()
    with pytest.raises(RendererOutputLimitError) as caught:
        host.render(
            outcome,
            renderer_id=renderer.capability_id,
            options=RendererPresentationOptionsV1("text/plain; charset=utf-8", 1),
        )
    assert caught.value.outcome is outcome
    assert "completed" not in str(caught.value)


def test_renderer_failure_is_typed_safe_and_never_mutates_outcome() -> None:
    class FailingRenderer(_Renderer):
        def render(
            self,
            outcome: AnyCompareOutcome,
            options: RendererPresentationOptionsV1,
            sink: RendererSinkV1,
        ) -> None:
            del outcome, options, sink
            raise RuntimeError("private /tmp/source.txt")

    renderer = FailingRenderer()
    host = _renderer_host(renderer)
    outcome = _outcome()
    before = dumps_outcome(outcome)
    with pytest.raises(RendererExecutionError) as caught:
        host.render(outcome, renderer_id=renderer.capability_id)
    assert caught.value.outcome is outcome
    assert dumps_outcome(outcome) == before
    assert "private" not in str(caught.value)
    assert "/tmp" not in str(caught.value)


def test_explicit_unavailable_renderer_never_falls_back() -> None:
    class UnavailableRenderer(_Renderer):
        def availability(self) -> CapabilityAvailabilityV1:
            return CapabilityAvailabilityV1(
                False,
                "org.example.scidiff.stdlib",
                "1",
                "backend_missing",
            )

    renderer = UnavailableRenderer()
    host = _renderer_host(renderer)
    outcome = _outcome()
    with pytest.raises(RendererUnavailableError) as caught:
        host.render(outcome, renderer_id=renderer.capability_id)
    assert caught.value.outcome is outcome
    assert caught.value.reason_code == "backend_missing"


def test_renderer_cannot_mix_text_and_binary_sink_modes() -> None:
    class MixingRenderer(_Renderer):
        def render(
            self,
            outcome: AnyCompareOutcome,
            options: RendererPresentationOptionsV1,
            sink: RendererSinkV1,
        ) -> None:
            del outcome, options
            sink.write_text("safe")
            sink.write_bytes(b"unsafe")

    renderer = MixingRenderer()
    host = _renderer_host(renderer)
    with pytest.raises(RendererExecutionError):
        host.render(_outcome(), renderer_id=renderer.capability_id)


def test_renderer_profile_distinguishes_escaped_from_hostile_terminal_text() -> None:
    hostile = "\x1b]0;spoofed\x07\t\ufeff\u202e"

    class UnsafeRenderer(_Renderer):
        def render(
            self,
            outcome: AnyCompareOutcome,
            options: RendererPresentationOptionsV1,
            sink: RendererSinkV1,
        ) -> None:
            del outcome, options
            sink.write_text(hostile)

    class SafeRenderer(_Renderer):
        def render(
            self,
            outcome: AnyCompareOutcome,
            options: RendererPresentationOptionsV1,
            sink: RendererSinkV1,
        ) -> None:
            del outcome, options
            sink.write_text(r"\x1b]0;spoofed\x07\t\ufeff\u202e")

    unsafe = UnsafeRenderer()
    unsafe_output = _renderer_host(unsafe).render(
        _outcome(), renderer_id=unsafe.capability_id
    )
    safe = SafeRenderer()
    safe_output = _renderer_host(safe).render(
        _outcome(), renderer_id=safe.capability_id
    )

    assert unsafe_output.text is not None
    assert safe_output.text is not None
    assert not terminal_text_is_safe(unsafe_output.text)
    assert terminal_text_is_safe(safe_output.text)


@pytest.mark.parametrize(
    "interruption", [KeyboardInterrupt(), SystemExit(9), MemoryError()]
)
def test_renderer_process_control_exceptions_propagate(
    interruption: BaseException,
) -> None:
    class InterruptingRenderer(_Renderer):
        def render(
            self,
            outcome: AnyCompareOutcome,
            options: RendererPresentationOptionsV1,
            sink: RendererSinkV1,
        ) -> None:
            del outcome, options, sink
            raise interruption

    renderer = InterruptingRenderer()
    host = _renderer_host(renderer)
    with pytest.raises(type(interruption)):
        host.render(_outcome(), renderer_id=renderer.capability_id)
