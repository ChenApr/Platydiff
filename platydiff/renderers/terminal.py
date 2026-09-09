"""Human-readable schema-v1 and schema-v2 outcome rendering."""

from __future__ import annotations

from platydiff.core.models import (
    AnyCompareOutcome,
    CompletedOutcome,
    CompletedOutcomeV2,
    CompletedOutcomeV3,
    ExtensionChange,
    ScalarFact,
    StructuredChange,
    SubtreeFact,
    TextHunk,
)

_BIDI_CONTROLS = frozenset(
    (0x061C, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A))
)


def _terminal_text_is_safe(value: str) -> bool:
    return all(
        character == "\n"
        or (
            ord(character) >= 0x20
            and not 0x7F <= ord(character) <= 0x9F
            and ord(character) != 0xFEFF
            and ord(character) not in _BIDI_CONTROLS
        )
        for character in value
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
        elif codepoint in _BIDI_CONTROLS:
            escaped.append(f"\\u{codepoint:04x}")
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


def _render_fact(fact: ScalarFact | SubtreeFact | None) -> str:
    if fact is None:
        return "fact omitted by detail_mode=digest_only"
    if isinstance(fact, SubtreeFact):
        return (
            f"[{fact.kind}] descendants={fact.descendant_count} "
            f"scalars={fact.scalar_count}"
        )
    if fact.kind == "string":
        if not isinstance(fact.value, str):
            raise RuntimeError("string fact lacks text")
        value = f'"{_escape_terminal_text(fact.value)}"'
    elif fact.kind == "boolean":
        value = "true" if fact.value is True else "false"
    elif fact.value is None:
        value = "null"
    else:
        if not isinstance(fact.value, str):
            raise RuntimeError("typed scalar fact lacks text")
        value = _escape_terminal_text(fact.value)
    lexical = (
        ""
        if fact.lexical is None
        else f" lexical={_escape_terminal_text(fact.lexical)}"
    )
    return f"[{fact.kind}] {value}{lexical}"


def _render_structured_change(change: StructuredChange) -> list[str]:
    path = "<root>" if not change.path else _escape_terminal_text(change.path)
    output = [f"{change.operation} {path}"]
    if change.before_type is not None:
        output.append(f"  before: {_render_fact(change.before_fact)}")
        output.append(f"  before evidence digest: {change.before_digest}")
    if change.after_type is not None:
        output.append(f"  after: {_render_fact(change.after_fact)}")
        output.append(f"  after evidence digest: {change.after_digest}")
    return output


def render_terminal(outcome: AnyCompareOutcome) -> str:
    """Render fields already decided by the pipeline."""
    if not isinstance(
        outcome, (CompletedOutcome, CompletedOutcomeV2, CompletedOutcomeV3)
    ):
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
        elif isinstance(change, StructuredChange):
            output.extend(_render_structured_change(change))
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
