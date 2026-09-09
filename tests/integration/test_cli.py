"""End-to-end and boundary tests for the Phase 1 CLI."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from platydiff import (
    CompletedOutcome,
    PluginHost,
    TextCompareSpec,
    TextSource,
    compare,
)
from platydiff.cli.main import exit_code
from platydiff.cli.parser import parse_command
from platydiff.core.models import (
    AnyCompareOutcome,
    CapabilityProblem,
    CompareSpec,
    Diagnostic,
    DiagnosticSeverity,
    ExecutionProblem,
    ExecutionRecord,
    FailedOutcome,
    PipelineStage,
    PolicyEvaluation,
    Source,
    StageDisposition,
    StageRecord,
    UnavailableOutcome,
    Verdict,
)
from platydiff.core.serialization import dumps_outcome, loads_outcome
from platydiff.plugin_sdk import (
    RendererPresentationOptionsV1,
    RendererSinkV1,
)
from platydiff.renderers.terminal import render_terminal
from tests.plugin_compatibility.test_renderer_execution_profile import (
    _Renderer,
    _renderer_host,
)


def run_module(
    *arguments: str, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "platydiff", *arguments],
        check=False,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def parse_object(payload: str) -> dict[str, object]:
    parsed: object = json.loads(payload)
    assert isinstance(parsed, dict)
    assert all(isinstance(key, str) for key in parsed)
    return parsed


def write_pair(tmp_path: Path, before: bytes, after: bytes) -> tuple[Path, Path]:
    before_path = tmp_path / "before.txt"
    after_path = tmp_path / "after.txt"
    before_path.write_bytes(before)
    after_path.write_bytes(after)
    return before_path, after_path


def test_text_route_terminal_pass_exit_zero(tmp_path: Path) -> None:
    before, after = write_pair(tmp_path, b"same\n", b"same\n")
    result = run_module("text", str(before), str(after))
    assert result.returncode == 0
    assert "equal: pass" in result.stdout
    assert result.stderr == ""


def test_compare_route_json_fail_exit_one(tmp_path: Path) -> None:
    before, after = write_pair(tmp_path, b"before\n", b"after\n")
    result = run_module(
        "compare", "--type", "text", "--format", "json", str(before), str(after)
    )
    assert result.returncode == 1
    payload = parse_object(result.stdout)
    assert payload["schema_version"] == 1
    assert payload["kind"] == "completed"
    result_data = payload["result"]
    assert isinstance(result_data, dict)
    assert result_data["relation"] == "different"
    assert result_data["verdict"] == "fail"
    assert result.stderr == ""


def test_plugin_cli_options_are_explicit_normalized_and_bounded() -> None:
    command = parse_command(
        [
            "compare",
            "--type",
            "auto",
            "--plugin",
            "org.example.zeta",
            "--plugin",
            "org.example.alpha",
            "--detector",
            "org.example.alpha.detector",
            "--comparator",
            "org.example.zeta.comparator",
            "--renderer",
            "org.example.alpha.renderer",
            "--renderer-media-type",
            "application/octet-stream",
            "--max-render-bytes",
            "7",
            "before",
            "after",
        ]
    )

    assert command.enabled_plugin_ids == (
        "org.example.alpha",
        "org.example.zeta",
    )
    assert command.detector_id == "org.example.alpha.detector"
    assert command.comparator_id == "org.example.zeta.comparator"
    assert command.renderer_id == "org.example.alpha.renderer"
    assert command.renderer_media_type == "application/octet-stream"
    assert command.max_render_bytes == 7


@pytest.mark.parametrize(
    "arguments",
    [
        (
            "text",
            "--plugin",
            "org.example.same",
            "--plugin",
            "org.example.same",
            "a",
            "b",
        ),
        ("text", "--plugin", "not-a-plugin-id", "a", "b"),
        ("text", "--detector", "org.example.detector", "a", "b"),
        ("text", "--renderer-media-type", "application/json", "a", "b"),
        ("text", "--max-render-bytes", "10", "a", "b"),
    ],
)
def test_invalid_plugin_cli_combinations_are_usage_errors(
    arguments: tuple[str, ...],
) -> None:
    with pytest.raises(SystemExit) as caught:
        parse_command(list(arguments))
    assert caught.value.code == 2


def test_plugin_enablement_alone_uses_schema_v2_without_changing_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    before, after = write_pair(tmp_path, b"same\n", b"same\n")
    module = importlib.import_module("platydiff.cli.main")
    policies: list[object] = []

    original_discover = PluginHost.discover

    def isolated_discover(policy: object) -> PluginHost:
        policies.append(policy)
        return original_discover(policy)  # type: ignore[arg-type]

    monkeypatch.setattr(module.PluginHost, "discover", staticmethod(isolated_discover))
    status = module.main(
        [
            "text",
            "--format",
            "json",
            "--plugin",
            "org.example.absent",
            str(before),
            str(after),
        ]
    )
    payload = parse_object(capsys.readouterr().out)

    assert status == 0
    assert len(policies) == 1
    assert payload["schema_version"] == 2
    result = payload["result"]
    assert isinstance(result, dict)
    provenance = result["provenance"]
    assert isinstance(provenance, dict)
    assert provenance["comparator_id"] == "text"


def test_explicit_capability_ids_are_forwarded_to_plugin_host(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    before, after = write_pair(tmp_path, b"same", b"same")
    module = importlib.import_module("platydiff.cli.main")
    delegate = PluginHost.discover(
        module.PluginDiscoveryPolicy(("org.example.absent",))
    )
    calls: list[tuple[str | None, str | None]] = []

    class RecordingHost:
        def compare(
            self,
            before_source: Source,
            after_source: Source,
            spec: CompareSpec,
            *,
            detector_id: str | None,
            comparator_id: str | None,
        ) -> AnyCompareOutcome:
            calls.append((detector_id, comparator_id))
            return delegate.compare(
                before_source,
                after_source,
                spec,
                detector_id=detector_id,
                comparator_id=comparator_id,
            )

    monkeypatch.setattr(
        module.PluginHost,
        "discover",
        staticmethod(lambda _policy: RecordingHost()),
    )
    status = module.main(
        [
            "compare",
            "--type",
            "auto",
            "--format",
            "json",
            "--plugin",
            "org.example.absent",
            "--detector",
            "org.example.absent.detector",
            "--comparator",
            "text",
            str(before),
            str(after),
        ]
    )
    captured = capsys.readouterr()

    assert status == 3
    assert calls == [("org.example.absent.detector", "text")]
    assert parse_object(captured.out)["schema_version"] == 2


def test_explicit_plugin_renderer_writes_exact_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    before, after = write_pair(tmp_path, b"same", b"same")
    module = importlib.import_module("platydiff.cli.main")
    renderer = _Renderer()
    host = _renderer_host(renderer)
    monkeypatch.setattr(
        module.PluginHost, "discover", staticmethod(lambda _policy: host)
    )

    status = module.main(
        [
            "text",
            "--plugin",
            "org.example.scidiff",
            "--renderer",
            renderer.capability_id,
            str(before),
            str(after),
        ]
    )
    captured = capsys.readouterr()

    assert status == 0
    assert captured.out == "completed:2"
    assert captured.err == ""


def test_plugin_renderer_overflow_has_safe_stderr_and_no_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    before, after = write_pair(tmp_path, b"same", b"same")
    module = importlib.import_module("platydiff.cli.main")
    renderer = _Renderer()
    host = _renderer_host(renderer)
    monkeypatch.setattr(
        module.PluginHost, "discover", staticmethod(lambda _policy: host)
    )

    status = module.main(
        [
            "text",
            "--plugin",
            "org.example.scidiff",
            "--renderer",
            renderer.capability_id,
            "--max-render-bytes",
            "1",
            str(before),
            str(after),
        ]
    )
    captured = capsys.readouterr()

    assert status == 3
    assert captured.out == ""
    assert captured.err == "platydiff: rendering failed safely\n"


@pytest.mark.parametrize("failure_boundary", ["discover", "compare"])
def test_plugin_internal_error_remains_schema_v2_with_enabled_context(
    failure_boundary: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    before, after = write_pair(tmp_path, b"same", b"same")
    module = importlib.import_module("platydiff.cli.main")

    class ExplodingHost:
        def compare(self, *_arguments: object, **_options: object) -> object:
            raise RuntimeError(f"private path: {tmp_path}")

    def discover(_policy: object) -> object:
        if failure_boundary == "discover":
            raise RuntimeError(f"private path: {tmp_path}")
        return ExplodingHost()

    monkeypatch.setattr(module.PluginHost, "discover", staticmethod(discover))
    status = module.main(
        [
            "text",
            "--format",
            "json",
            "--plugin",
            "org.example.absent",
            str(before),
            str(after),
        ]
    )
    captured = capsys.readouterr()
    payload = parse_object(captured.out)
    execution = payload["execution"]
    assert isinstance(execution, dict)
    plugin_host = execution["plugin_host"]
    assert isinstance(plugin_host, dict)

    assert status == 3
    assert payload["schema_version"] == 2
    assert payload["kind"] == "failed"
    assert plugin_host["enabled_plugin_ids"] == ["org.example.absent"]
    assert plugin_host["loaded_providers"] == []
    assert str(tmp_path) not in captured.out
    assert captured.err == ""


def test_plugin_renderer_hostile_terminal_controls_fail_safely(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class UnsafeRenderer(_Renderer):
        def render(
            self,
            outcome: AnyCompareOutcome,
            options: RendererPresentationOptionsV1,
            sink: RendererSinkV1,
        ) -> None:
            del outcome, options
            sink.write_text("\x1b]0;spoofed\x07\t\ufeff\u202e")

    before, after = write_pair(tmp_path, b"same", b"same")
    module = importlib.import_module("platydiff.cli.main")
    renderer = UnsafeRenderer()
    host = _renderer_host(renderer)
    monkeypatch.setattr(
        module.PluginHost, "discover", staticmethod(lambda _policy: host)
    )

    status = module.main(
        [
            "text",
            "--plugin",
            "org.example.scidiff",
            "--renderer",
            renderer.capability_id,
            str(before),
            str(after),
        ]
    )
    captured = capsys.readouterr()

    assert status == 3
    assert captured.out == ""
    assert captured.err == "platydiff: rendering failed safely\n"


def test_two_routes_use_the_same_result_path(tmp_path: Path) -> None:
    before, after = write_pair(tmp_path, b"a\nb\n", b"a\nx\n")
    text_result = run_module("text", "--format", "json", str(before), str(after))
    compare_result = run_module(
        "compare", "--type", "text", "--format", "json", str(before), str(after)
    )
    text_payload = parse_object(text_result.stdout)
    compare_payload = parse_object(compare_result.stdout)
    assert text_payload["result"] == compare_payload["result"]


@pytest.mark.parametrize(
    "arguments",
    [
        (),
        ("text", "only-one-path"),
        ("compare", "a", "b"),
        ("text", "--context-lines", "-1", "a", "b"),
        ("text", "--unknown", "a", "b"),
    ],
)
def test_usage_errors_exit_two_without_outcome(arguments: tuple[str, ...]) -> None:
    result = run_module(*arguments)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "usage:" in result.stderr
    assert '"schema_version"' not in result.stderr


def test_source_failure_is_structured_exit_three(tmp_path: Path) -> None:
    missing = tmp_path / "private" / "missing.txt"
    result = run_module("text", "--format", "json", str(missing), str(missing))
    assert result.returncode == 3
    payload = parse_object(result.stdout)
    assert payload["kind"] == "failed"
    problem = payload["problem"]
    assert isinstance(problem, dict)
    assert problem["code"] == "source_not_found"
    assert str(tmp_path) not in result.stdout
    assert "Traceback" not in result.stderr


def test_decode_failure_is_structured_exit_three(tmp_path: Path) -> None:
    before, after = write_pair(tmp_path, b"\xff", b"ok")
    result = run_module("text", "--format", "json", str(before), str(after))
    payload = parse_object(result.stdout)
    problem = payload["problem"]
    assert isinstance(problem, dict)
    assert result.returncode == 3
    assert problem["code"] == "decode_error"


def test_resource_failure_is_structured_exit_three(tmp_path: Path) -> None:
    before, after = write_pair(tmp_path, b"too large", b"also large")
    result = run_module(
        "text",
        "--format",
        "json",
        "--max-input-bytes",
        "1",
        str(before),
        str(after),
    )
    payload = parse_object(result.stdout)
    problem = payload["problem"]
    assert isinstance(problem, dict)
    assert result.returncode == 3
    assert problem["code"] == "resource_limit_exceeded"


def test_cli_output_limit_reports_truncation(tmp_path: Path) -> None:
    before, after = write_pair(tmp_path, b"a\nsame\nb\n", b"x\nsame\ny\n")
    result = run_module(
        "text",
        "--format",
        "json",
        "--context-lines",
        "0",
        "--max-change-items",
        "1",
        str(before),
        str(after),
    )
    payload = parse_object(result.stdout)
    result_data = payload["result"]
    assert isinstance(result_data, dict)
    changes = result_data["changes"]
    assert isinstance(changes, dict)
    assert changes["completeness"] == "truncated"
    assert changes["total_count"] == 2
    assert changes["returned_count"] == 1
    assert result.returncode == 1


def test_console_script_help_entry_point() -> None:
    result = subprocess.run(
        [str(Path(sys.executable).with_name("platydiff")), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "{compare,text,binary}" in result.stdout


def test_binary_routes_share_the_same_result(tmp_path: Path) -> None:
    before, after = write_pair(tmp_path, b"a\x00", b"b\x00")
    shortcut = run_module("binary", "--format", "json", str(before), str(after))
    compare_result = run_module(
        "compare", "--type", "binary", "--format", "json", str(before), str(after)
    )
    assert shortcut.returncode == compare_result.returncode == 1
    assert (
        parse_object(shortcut.stdout)["result"]
        == parse_object(compare_result.stdout)["result"]
    )


def test_auto_route_and_detection_unavailable_exit(tmp_path: Path) -> None:
    text_before, text_after = write_pair(tmp_path, b"same", b"same")
    selected = run_module(
        "compare",
        "--type",
        "auto",
        "--format",
        "json",
        str(text_before),
        str(text_after),
    )
    assert selected.returncode == 0
    payload = parse_object(selected.stdout)
    execution = payload["execution"]
    assert isinstance(execution, dict)
    assert execution["detection"]["selected_modality"] == "text"

    text_before.write_bytes(b"")
    text_after.write_bytes(b"")
    unavailable = run_module(
        "compare",
        "--type",
        "auto",
        "--format",
        "json",
        str(text_before),
        str(text_after),
    )
    assert unavailable.returncode == 3
    assert parse_object(unavailable.stdout)["kind"] == "unavailable"


def test_text_only_option_is_rejected_for_binary_and_auto() -> None:
    for kind in ("binary", "auto"):
        result = run_module("compare", "--type", kind, "--context-lines", "1", "a", "b")
        assert result.returncode == 2
        assert result.stdout == ""


@pytest.mark.parametrize(
    ("kind", "option"),
    [
        ("text", "--chunk-bytes=1"),
        ("binary", "--max-detection-bytes=1"),
        ("auto", "--chunk-bytes=1"),
    ],
)
def test_compare_rejects_options_from_another_modality(kind: str, option: str) -> None:
    result = run_module("compare", "--type", kind, option, "a", "b")
    assert result.returncode == 2
    assert result.stdout == ""


def test_option_terminator_preserves_dash_prefixed_binary_path(tmp_path: Path) -> None:
    before = tmp_path / "--context-lines=1"
    after = tmp_path / "other"
    before.write_bytes(b"same")
    after.write_bytes(b"same")

    result = run_module("binary", "--", before.name, after.name, cwd=tmp_path)

    assert result.returncode == 0
    assert "equal: pass" in result.stdout
    assert result.stderr == ""


@pytest.mark.parametrize(
    "arguments",
    [
        ("binary", "--chunk-bytes", "16777217", "a", "b"),
        ("compare", "--type", "auto", "--minimum-confidence", "1001", "a", "b"),
    ],
)
def test_phase2_cli_numeric_bounds_are_usage_errors(arguments: tuple[str, ...]) -> None:
    result = run_module(*arguments)
    assert result.returncode == 2
    assert result.stdout == ""


@pytest.mark.parametrize(
    "arguments",
    [
        (
            "compare",
            "--type",
            "auto",
            "--max-detection-bytes",
            str(2**53 + 1),
            "before",
            "after",
        ),
        (
            "compare",
            "--type",
            "binary",
            "--max-input-bytes",
            str(2**53 + 1),
            "before",
            "after",
        ),
    ],
)
def test_phase2_cli_exact_integer_overflow_is_a_clean_usage_error(
    arguments: tuple[str, ...],
) -> None:
    result = run_module(*arguments)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "usage:" in result.stderr
    assert "Traceback" not in result.stderr


def test_warn_verdict_maps_to_exit_zero() -> None:
    outcome = compare(TextSource("same"), TextSource("same"), TextCompareSpec())
    assert isinstance(outcome, CompletedOutcome)
    warning_result = replace(
        outcome.result,
        verdict=Verdict.WARN,
        evaluations=(PolicyEvaluation("explicit_warning", Verdict.WARN),),
    )
    assert exit_code(replace(outcome, result=warning_result)) == 0


def test_unavailable_outcome_maps_to_exit_three() -> None:
    stamp = "2026-09-06T00:00:00Z"
    execution = ExecutionRecord(
        stamp,
        stamp,
        0,
        (
            StageRecord(
                PipelineStage.VALIDATING,
                stamp,
                stamp,
                0,
                StageDisposition.COMPLETED,
            ),
            StageRecord(
                PipelineStage.SOURCING,
                stamp,
                stamp,
                0,
                StageDisposition.COMPLETED,
            ),
            StageRecord(
                PipelineStage.RESOLVING,
                stamp,
                stamp,
                0,
                StageDisposition.UNAVAILABLE,
            ),
        ),
        last_completed_stage=PipelineStage.SOURCING,
    )
    outcome = UnavailableOutcome(
        execution=execution,
        problem=CapabilityProblem(
            "capability_unavailable",
            501,
            PipelineStage.RESOLVING,
            "No capability is available.",
        ),
    )
    assert exit_code(outcome) == 3


def test_unknown_exception_is_safe_and_suppresses_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    before, after = write_pair(tmp_path, b"a", b"a")
    module = importlib.import_module("platydiff.cli.main")

    def explode(*_arguments: object) -> object:
        raise RuntimeError(f"sensitive path: {tmp_path}")

    monkeypatch.setattr(module, "compare", explode)
    status = module.main(["text", "--format", "json", str(before), str(after)])
    captured = capsys.readouterr()
    assert status == 3
    payload = parse_object(captured.out)
    assert payload["schema_version"] == 1
    assert "internal_error" in captured.out
    assert str(tmp_path) not in captured.out
    assert "Traceback" not in captured.err


def test_terminal_renderer_escapes_untrusted_controls_without_changing_json() -> None:
    bidi_controls = (
        "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
    )
    hostile = "\x1b]0;spoofed-title\x07\t\ufeff\\literal" + bidi_controls + "猫"
    outcome = compare(TextSource(hostile), TextSource("safe"), TextCompareSpec())
    assert isinstance(outcome, CompletedOutcome)

    rendered = render_terminal(outcome)
    assert "\x1b" not in rendered
    assert "\x07" not in rendered
    assert "\t" not in rendered
    assert "\ufeff" not in rendered
    assert r"\x1b" in rendered
    assert r"\x07" in rendered
    assert r"\t" in rendered
    assert r"\ufeff" in rendered
    assert r"\\literal" in rendered
    assert "猫" in rendered
    for control in bidi_controls:
        assert control not in rendered
        assert f"\\u{ord(control):04x}" in rendered
    assert loads_outcome(dumps_outcome(outcome)) == outcome

    diagnostic_outcome = replace(
        outcome,
        execution=replace(
            outcome.execution,
            diagnostics=(
                Diagnostic(
                    "unsafe_message",
                    DiagnosticSeverity.WARNING,
                    PipelineStage.COMPARING,
                    bidi_controls,
                ),
            ),
        ),
    )
    diagnostic_rendered = render_terminal(diagnostic_outcome)
    assert all(control not in diagnostic_rendered for control in bidi_controls)

    stamp = "2026-09-07T00:00:00Z"
    failed = FailedOutcome(
        execution=ExecutionRecord(
            stamp,
            stamp,
            0,
            (
                StageRecord(
                    PipelineStage.VALIDATING,
                    stamp,
                    stamp,
                    0,
                    StageDisposition.FAILED,
                ),
            ),
        ),
        problem=ExecutionProblem(
            "internal_error", 500, PipelineStage.VALIDATING, bidi_controls
        ),
    )
    problem_rendered = render_terminal(failed)
    assert all(control not in problem_rendered for control in bidi_controls)


@pytest.mark.parametrize(
    ("output_format", "renderer_name"),
    [("terminal", "render_terminal"), ("json", "render_json")],
)
def test_renderer_failure_uses_stderr_and_leaves_stdout_empty(
    output_format: str,
    renderer_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    before, after = write_pair(tmp_path, b"same\n", b"same\n")
    module = importlib.import_module("platydiff.cli.main")

    def explode(_outcome: object) -> str:
        assert isinstance(_outcome, CompletedOutcome)
        assert _outcome.result.verdict is Verdict.PASS
        raise RuntimeError(f"sensitive path: {tmp_path}")

    monkeypatch.setattr(module, renderer_name, explode)
    status = module.main(["text", "--format", output_format, str(before), str(after)])
    captured = capsys.readouterr()
    assert status == 3
    assert captured.out == ""
    assert captured.err == "platydiff: rendering failed safely\n"


@pytest.mark.parametrize(
    "interruption",
    [KeyboardInterrupt(), SystemExit(17), MemoryError()],
)
def test_process_interruptions_are_not_swallowed(
    interruption: BaseException,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before, after = write_pair(tmp_path, b"a", b"a")
    module = importlib.import_module("platydiff.cli.main")

    def interrupt(*_arguments: object) -> object:
        raise interruption

    monkeypatch.setattr(module, "compare", interrupt)
    with pytest.raises(type(interruption)):
        module.main(["text", str(before), str(after)])


@pytest.mark.parametrize(
    "interruption",
    [KeyboardInterrupt(), SystemExit(17), MemoryError()],
)
def test_renderer_process_interruptions_are_not_swallowed(
    interruption: BaseException,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before, after = write_pair(tmp_path, b"a", b"a")
    module = importlib.import_module("platydiff.cli.main")

    def interrupt(_outcome: object) -> str:
        raise interruption

    monkeypatch.setattr(module, "render_terminal", interrupt)
    with pytest.raises(type(interruption)):
        module.main(["text", str(before), str(after)])
