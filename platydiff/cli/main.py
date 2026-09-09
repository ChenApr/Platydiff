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
    CompletedOutcomeV3,
    ExecutionProblem,
    ExecutionProblemV2,
    ExecutionRecord,
    ExecutionRecordV2,
    FailedOutcome,
    FailedOutcomeV2,
    FailedOutcomeV3,
    JsonCompareSpec,
    PathSource,
    PipelineStage,
    PluginHostExecutionRecord,
    ProviderIdentity,
    StageDisposition,
    StageRecord,
    Verdict,
)
from platydiff.plugin_sdk import RendererPresentationOptionsV1
from platydiff.plugins import PluginDiscoveryPolicy, PluginHost
from platydiff.renderers.json import render_json
from platydiff.renderers.terminal import _terminal_text_is_safe, render_terminal


def _internal_error_outcome(
    plugin_host: PluginHostExecutionRecord | None = None,
    *,
    schema_v3: bool = False,
) -> FailedOutcome | FailedOutcomeV2 | FailedOutcomeV3:
    stamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    stage = StageRecord(
        PipelineStage.VALIDATING,
        stamp,
        stamp,
        0,
        StageDisposition.FAILED,
    )
    message = "An unexpected internal error prevented comparison."
    if plugin_host is not None:
        return FailedOutcomeV2(
            execution=ExecutionRecordV2(
                stamp,
                stamp,
                0,
                (stage,),
                plugin_host=plugin_host,
            ),
            problem=ExecutionProblemV2(
                "internal_error", 500, PipelineStage.VALIDATING, message
            ),
        )
    if schema_v3:
        return FailedOutcomeV3(
            execution=ExecutionRecordV2(
                stamp,
                stamp,
                0,
                (stage,),
                plugin_host=None,
            ),
            problem=ExecutionProblemV2(
                "internal_error", 500, PipelineStage.VALIDATING, message
            ),
        )
    return FailedOutcome(
        execution=ExecutionRecord(stamp, stamp, 0, (stage,)),
        problem=ExecutionProblem(
            "internal_error", 500, PipelineStage.VALIDATING, message
        ),
    )


def _plugin_host_snapshot(host: PluginHost) -> PluginHostExecutionRecord:
    providers = tuple(
        ProviderIdentity(
            plugin_id=plugin.manifest.plugin_id,
            plugin_version=plugin.manifest.plugin_version,
            distribution_name=plugin.entry_point.distribution_name,
            distribution_version=plugin.entry_point.distribution_version,
            manifest_schema_version=plugin.manifest.manifest_schema_version,
            api_major=plugin.manifest.api_major,
            negotiated_api_minor=plugin.negotiated_api_minor,
            negotiated_host_features=plugin.negotiated_host_features,
        )
        for plugin in host.catalog.plugins
    )
    return PluginHostExecutionRecord(host.catalog.enabled_plugin_ids, providers)


def exit_code(outcome: AnyCompareOutcome) -> int:
    """Map an outcome to the stable Phase 1 shell exit contract."""
    if isinstance(outcome, (CompletedOutcome, CompletedOutcomeV2, CompletedOutcomeV3)):
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
        outcome = _internal_error_outcome(
            (
                _plugin_host_snapshot(host)
                if host is not None
                else PluginHostExecutionRecord(command.enabled_plugin_ids, ())
            )
            if command.uses_plugin_host
            else None,
            schema_v3=isinstance(command.spec, JsonCompareSpec),
        )

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
                text = plugin_output.text
                if text is None or not _terminal_text_is_safe(text):
                    raise ValueError("plugin renderer text is unsafe for a terminal")
                sys.stdout.write(text)
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
