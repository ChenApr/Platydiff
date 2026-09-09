"""Command-line execution, safe exception boundary, and exit mapping."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

from platydiff.api import compare
from platydiff.cli.parser import parse_command
from platydiff.core.models import (
    AnyCompareOutcome,
    CompletedOutcome,
    CompletedOutcomeV2,
    ExecutionProblem,
    ExecutionRecord,
    FailedOutcome,
    PathSource,
    PipelineStage,
    StageDisposition,
    StageRecord,
    Verdict,
)
from platydiff.plugin_sdk import RendererPresentationOptionsV1
from platydiff.plugins import PluginDiscoveryPolicy, PluginHost
from platydiff.renderers.json import render_json
from platydiff.renderers.terminal import render_terminal


def _internal_error_outcome() -> FailedOutcome:
    stamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    stage = StageRecord(
        PipelineStage.VALIDATING,
        stamp,
        stamp,
        0,
        StageDisposition.FAILED,
    )
    execution = ExecutionRecord(stamp, stamp, 0, (stage,))
    return FailedOutcome(
        execution=execution,
        problem=ExecutionProblem(
            "internal_error",
            500,
            PipelineStage.VALIDATING,
            "An unexpected internal error prevented comparison.",
        ),
    )


def exit_code(outcome: AnyCompareOutcome) -> int:
    """Map an outcome to the stable Phase 1 shell exit contract."""
    if isinstance(outcome, (CompletedOutcome, CompletedOutcomeV2)):
        return 1 if outcome.result.verdict is Verdict.FAIL else 0
    return 3


def main(argv: list[str] | None = None) -> int:
    """Run one comparison; argparse owns usage errors and exit code 2."""
    command = parse_command(argv)
    host: PluginHost | None = None
    outcome: AnyCompareOutcome
    try:
        before = PathSource(Path(command.before))
        after = PathSource(Path(command.after))
        if command.uses_plugin_host:
            host = PluginHost.discover(
                PluginDiscoveryPolicy(command.enabled_plugin_ids)
            )
            outcome = host.compare(
                before,
                after,
                command.spec,
                detector_id=command.detector_id,
                comparator_id=command.comparator_id,
            )
        else:
            outcome = compare(before, after, command.spec)
    except MemoryError:
        raise
    except Exception:
        outcome = _internal_error_outcome()

    try:
        if command.renderer_id is not None:
            if host is None:
                raise RuntimeError("plugin renderer requires a plugin host")
            plugin_output = host.render(
                outcome,
                renderer_id=command.renderer_id,
                options=RendererPresentationOptionsV1(
                    media_type=command.renderer_media_type,
                    max_output_bytes=command.max_render_bytes,
                ),
            )
            if plugin_output.is_text:
                sys.stdout.write(plugin_output.text or "")
            else:
                sys.stdout.buffer.write(plugin_output.data)
            sys.stdout.flush()
            return exit_code(outcome)
        rendered = (
            render_json(outcome)
            if command.output_format == "json"
            else render_terminal(outcome)
        )
    except MemoryError:
        raise
    except Exception:
        print("platydiff: rendering failed safely", file=sys.stderr)
        return 3
    print(rendered)
    return exit_code(outcome)
