"""Human-readable Phase 1 outcome rendering."""

from __future__ import annotations

from platydiff.core.models import (
    CompareOutcome,
    CompletedOutcome,
    ExtensionChange,
    TextHunk,
)


def _escape_terminal_text(value: str) -> str:
    escaped: list[str] = []
    for character in value:
        codepoint = ord(character)
        if character == "\\":
            escaped.append("\\\\")
        elif character == "\t":
            escaped.append("\\t")
        elif codepoint == 0xFEFF:
            escaped.append("\\ufeff")
        elif codepoint < 0x20 or 0x7F <= codepoint <= 0x9F:
            escaped.append(f"\\x{codepoint:02x}")
        else:
            escaped.append(character)
    return "".join(escaped)


def _render_hunk(hunk: TextHunk) -> list[str]:
    output = [
        f"@@ -{hunk.before_start_line},{hunk.before_line_count} "
        f"+{hunk.after_start_line},{hunk.after_line_count} @@"
    ]
    prefixes = {"equal": " ", "delete": "-", "insert": "+"}
    for line in hunk.lines:
        output.append(f"{prefixes[line.kind]}{_escape_terminal_text(line.content)}")
        if line.terminator == "":
            output.append("\\ No newline at end of file")
        elif line.terminator != "\n":
            name = "CRLF" if line.terminator == "\r\n" else "CR"
            output.append(f"\\ Line terminator: {name}")
    return output


def render_terminal(outcome: CompareOutcome) -> str:
    """Render fields already decided by the pipeline."""
    if not isinstance(outcome, CompletedOutcome):
        return (
            f"{outcome.kind} [{outcome.problem.code}/{outcome.problem.status_code}] "
            f"at {outcome.problem.stage.value}: "
            f"{_escape_terminal_text(outcome.problem.message)}"
        )
    result = outcome.result
    output = [
        f"{result.relation.value}: {result.verdict.value}",
        f"fidelity: {result.fidelity.value}",
        f"changes: {result.summary.change_count} ({result.changes.completeness.value})",
    ]
    output.extend(
        f"{count.name}: {count.value} {count.unit}" for count in result.summary.counts
    )
    for change in result.changes.items:
        if isinstance(change, TextHunk):
            output.extend(_render_hunk(change))
        elif isinstance(change, ExtensionChange):
            output.append(
                f"extension change: {change.kind} "
                f"({change.plugin_id} schema {change.schema_version})"
            )
    for diagnostic in outcome.execution.diagnostics:
        output.append(
            f"{diagnostic.severity.value} [{diagnostic.code}]: "
            f"{_escape_terminal_text(diagnostic.message)}"
        )
    return "\n".join(output)
