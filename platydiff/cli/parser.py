"""Argument parser construction for the two equivalent text routes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from platydiff.core.models import (
    NewlinePolicy,
    ResourceLimits,
    TextCompareSpec,
    TextEncoding,
)


def _non_negative(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def _add_text_arguments(parser: argparse.ArgumentParser) -> None:
    defaults = ResourceLimits()
    parser.add_argument("before", metavar="BEFORE")
    parser.add_argument("after", metavar="AFTER")
    parser.add_argument("--format", choices=("terminal", "json"), default="terminal")
    parser.add_argument(
        "--encoding", choices=tuple(TextEncoding), default=TextEncoding.UTF8.value
    )
    parser.add_argument(
        "--newline", choices=tuple(NewlinePolicy), default=NewlinePolicy.PRESERVE.value
    )
    parser.add_argument("--context-lines", type=_non_negative, default=3)
    parser.add_argument(
        "--max-input-bytes", type=_non_negative, default=defaults.max_input_bytes
    )
    parser.add_argument(
        "--max-input-lines", type=_non_negative, default=defaults.max_input_lines
    )
    parser.add_argument(
        "--max-encoded-line-bytes",
        type=_non_negative,
        default=defaults.max_encoded_line_bytes,
    )
    parser.add_argument(
        "--max-myers-work", type=_non_negative, default=defaults.max_myers_work
    )
    parser.add_argument(
        "--max-change-items", type=_non_negative, default=defaults.max_change_items
    )
    parser.add_argument(
        "--max-change-payload-bytes",
        type=_non_negative,
        default=defaults.max_change_payload_bytes,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the complete Phase 1 command-line parser."""
    parser = argparse.ArgumentParser(
        prog="platydiff",
        description="Compare scientific and multimodal data.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    compare_parser = commands.add_parser(
        "compare", help="compare sources with an explicit modality"
    )
    compare_parser.add_argument("--type", choices=("text",), required=True)
    _add_text_arguments(compare_parser)

    text_parser = commands.add_parser("text", help="compare two text files")
    _add_text_arguments(text_parser)
    return parser


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    before: str
    after: str
    output_format: str
    spec: TextCompareSpec


def parse_command(argv: list[str] | None = None) -> ParsedCommand:
    """Parse either route into one normalized command value."""
    namespace = build_parser().parse_args(argv)
    values = vars(namespace)
    limits = ResourceLimits(
        max_input_bytes=int(values["max_input_bytes"]),
        max_input_lines=int(values["max_input_lines"]),
        max_encoded_line_bytes=int(values["max_encoded_line_bytes"]),
        max_myers_work=int(values["max_myers_work"]),
        max_change_items=int(values["max_change_items"]),
        max_change_payload_bytes=int(values["max_change_payload_bytes"]),
    )
    return ParsedCommand(
        before=str(values["before"]),
        after=str(values["after"]),
        output_format=str(values["format"]),
        spec=TextCompareSpec(
            encoding=TextEncoding(str(values["encoding"])),
            newline=NewlinePolicy(str(values["newline"])),
            context_lines=int(values["context_lines"]),
            limits=limits,
        ),
    )
