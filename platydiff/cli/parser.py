"""Argument parsing for explicit text, binary, and automatic routes."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from platydiff.core.models import (
    AutoCompareSpec,
    AutoResourceLimits,
    BinaryCompareSpec,
    BinaryResourceLimits,
    CompareSpec,
    NewlinePolicy,
    ResourceLimits,
    TextCompareSpec,
    TextEncoding,
)


def _number(value: str, *, positive: bool = False) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if parsed < (1 if positive else 0):
        raise argparse.ArgumentTypeError(
            "must be positive" if positive else "must be non-negative"
        )
    return parsed


def _non_negative(value: str) -> int:
    return _number(value)


def _positive(value: str) -> int:
    return _number(value, positive=True)


def _common(parser: argparse.ArgumentParser) -> None:
    defaults = ResourceLimits()
    parser.add_argument("before", metavar="BEFORE")
    parser.add_argument("after", metavar="AFTER")
    parser.add_argument("--format", choices=("terminal", "json"), default="terminal")
    parser.add_argument(
        "--max-input-bytes", type=_non_negative, default=defaults.max_input_bytes
    )
    parser.add_argument(
        "--max-change-items", type=_non_negative, default=defaults.max_change_items
    )
    parser.add_argument(
        "--max-change-payload-bytes",
        type=_non_negative,
        default=defaults.max_change_payload_bytes,
    )


def _text(parser: argparse.ArgumentParser) -> None:
    defaults = ResourceLimits()
    parser.add_argument(
        "--encoding", choices=tuple(TextEncoding), default=TextEncoding.UTF8.value
    )
    parser.add_argument(
        "--newline", choices=tuple(NewlinePolicy), default=NewlinePolicy.PRESERVE.value
    )
    parser.add_argument("--context-lines", type=_non_negative, default=3)
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


def _binary(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--chunk-bytes", type=_positive, default=BinaryResourceLimits().chunk_bytes
    )


def _auto(parser: argparse.ArgumentParser) -> None:
    defaults = AutoResourceLimits()
    parser.add_argument(
        "--max-detection-bytes",
        type=_non_negative,
        default=defaults.max_detection_bytes,
    )
    parser.add_argument(
        "--binary-chunk-bytes", type=_positive, default=defaults.binary_chunk_bytes
    )
    parser.add_argument("--minimum-confidence", type=_non_negative, default=800)
    parser.add_argument("--ambiguity-margin", type=_non_negative, default=100)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="platydiff")
    commands = parser.add_subparsers(dest="command", required=True)
    compare_parser = commands.add_parser("compare")
    compare_parser.add_argument(
        "--type", choices=("text", "binary", "auto"), required=True
    )
    for add in (_common, _text, _binary, _auto):
        add(compare_parser)
    text_parser = commands.add_parser("text")
    _common(text_parser)
    _text(text_parser)
    binary_parser = commands.add_parser("binary")
    _common(binary_parser)
    _binary(binary_parser)
    return parser


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    before: str
    after: str
    output_format: str
    spec: CompareSpec


def parse_command(argv: list[str] | None = None) -> ParsedCommand:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    values = vars(parser.parse_args(arguments))
    kind = str(values.get("type") or values["command"])
    text_flags = {
        "--encoding",
        "--newline",
        "--context-lines",
        "--max-input-lines",
        "--max-encoded-line-bytes",
        "--max-myers-work",
    }
    if kind != "text" and any(
        item.split("=", 1)[0] in text_flags for item in arguments
    ):
        parser.error("text-only options require text")
    common = dict(
        max_input_bytes=int(values["max_input_bytes"]),
        max_change_items=int(values["max_change_items"]),
        max_change_payload_bytes=int(values["max_change_payload_bytes"]),
    )
    if kind == "text":
        spec: CompareSpec = TextCompareSpec(
            encoding=TextEncoding(str(values["encoding"])),
            newline=NewlinePolicy(str(values["newline"])),
            context_lines=int(values["context_lines"]),
            limits=ResourceLimits(
                **common,
                max_input_lines=int(values["max_input_lines"]),
                max_encoded_line_bytes=int(values["max_encoded_line_bytes"]),
                max_myers_work=int(values["max_myers_work"]),
            ),
        )
    elif kind == "binary":
        spec = BinaryCompareSpec(
            limits=BinaryResourceLimits(
                **common, chunk_bytes=int(values["chunk_bytes"])
            )
        )
    else:
        defaults = AutoResourceLimits()
        spec = AutoCompareSpec(
            minimum_confidence=int(values["minimum_confidence"]),
            ambiguity_margin=int(values["ambiguity_margin"]),
            limits=AutoResourceLimits(
                **common,
                max_input_lines=defaults.max_input_lines,
                max_encoded_line_bytes=defaults.max_encoded_line_bytes,
                max_myers_work=defaults.max_myers_work,
                max_detection_bytes=int(values["max_detection_bytes"]),
                binary_chunk_bytes=int(values["binary_chunk_bytes"]),
            ),
        )
    return ParsedCommand(
        str(values["before"]), str(values["after"]), str(values["format"]), spec
    )
