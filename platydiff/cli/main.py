"""Command-line execution, safe exception boundary, and exit mapping."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from platydiff.api import compare
from platydiff.cli.parser import parse_command
from platydiff.core.models import (
    CompareOutcome,
    CompletedOutcome,
    ExecutionProblem,
    ExecutionRecord,
    FailedOutcome,
    PathSource,
    PipelineStage,
    StageDisposition,
    StageRecord,
    Verdict,
)
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


def exit_code(outcome: CompareOutcome) -> int:
    """Map an outcome to the stable Phase 1 shell exit contract."""
    if isinstance(outcome, CompletedOutcome):
        return 1 if outcome.result.verdict is Verdict.FAIL else 0
    return 3


def main(argv: list[str] | None = None) -> int:
    """Run one comparison; argparse owns usage errors and exit code 2."""
    command = parse_command(argv)
    try:
        outcome = compare(
            PathSource(Path(command.before)),
            PathSource(Path(command.after)),
            command.spec,
        )
    except MemoryError:
        raise
    except Exception:
        outcome = _internal_error_outcome()

    try:
        rendered = (
            render_json(outcome)
            if command.output_format == "json"
            else render_terminal(outcome)
        )
    except MemoryError:
        raise
    except Exception:
        print("platydiff: rendering failed safely")
        return 3
    print(rendered)
    return exit_code(outcome)
