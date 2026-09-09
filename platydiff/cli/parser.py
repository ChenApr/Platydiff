"""Argument parsing for explicit text, binary, and automatic routes."""

from __future__ import annotations

import argparse
import re
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
from platydiff.plugin_sdk import RendererPresentationOptionsV1

_PLUGIN_ID = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)+$")
_CAPABILITY_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


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


def _chunk(value: str) -> int:
    parsed = _positive(value)
    if parsed > 16 * 1024 * 1024:
        raise argparse.ArgumentTypeError("must not exceed 16777216")
    return parsed


def _confidence(value: str) -> int:
    parsed = _non_negative(value)
    if parsed > 1000:
        raise argparse.ArgumentTypeError("must not exceed 1000")
    return parsed


def _plugin_id(value: str) -> str:
    if len(value.encode("utf-8")) > 255 or not _PLUGIN_ID.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "must be a lowercase reverse-domain plugin identifier"
        )
    return value


def _capability_id(value: str) -> str:
    if len(value.encode("utf-8")) > 255 or not _CAPABILITY_ID.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "must be a stable lowercase ASCII capability identifier"
        )
    return value


def _media_type(value: str) -> str:
    try:
        RendererPresentationOptionsV1(media_type=value, max_output_bytes=0)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    return value


def _common(parser: argparse.ArgumentParser) -> None:
    defaults = ResourceLimits()
    renderer_defaults = RendererPresentationOptionsV1()
    parser.add_argument("before", metavar="BEFORE")
    parser.add_argument("after", metavar="AFTER")
    parser.add_argument("--format", choices=("terminal", "json"), default="terminal")
    parser.add_argument(
        "--plugin",
        action="append",
        default=[],
        type=_plugin_id,
        metavar="PLUGIN_ID",
        help="enable one exact installed plugin ID; repeat to enable more",
    )
    parser.add_argument("--detector", type=_capability_id, metavar="CAPABILITY_ID")
    parser.add_argument("--comparator", type=_capability_id, metavar="CAPABILITY_ID")
    parser.add_argument("--renderer", type=_capability_id, metavar="CAPABILITY_ID")
    parser.add_argument(
        "--renderer-media-type",
        type=_media_type,
        default=renderer_defaults.media_type,
        metavar="MEDIA_TYPE",
    )
    parser.add_argument(
        "--max-render-bytes",
        type=_non_negative,
        default=renderer_defaults.max_output_bytes,
        metavar="BYTES",
    )
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
        "--chunk-bytes", type=_chunk, default=BinaryResourceLimits().chunk_bytes
    )


def _auto(parser: argparse.ArgumentParser) -> None:
    defaults = AutoResourceLimits()
    parser.add_argument(
        "--max-detection-bytes",
        type=_non_negative,
        default=defaults.max_detection_bytes,
    )
    parser.add_argument(
        "--binary-chunk-bytes", type=_chunk, default=defaults.binary_chunk_bytes
    )
    parser.add_argument("--minimum-confidence", type=_confidence, default=800)
    parser.add_argument("--ambiguity-margin", type=_confidence, default=100)


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
    enabled_plugin_ids: tuple[str, ...]
    detector_id: str | None
    comparator_id: str | None
    renderer_id: str | None
    renderer_media_type: str
    max_render_bytes: int

    @property
    def uses_plugin_host(self) -> bool:
        return bool(
            self.enabled_plugin_ids
            or self.detector_id
            or self.comparator_id
            or self.renderer_id
        )


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
    binary_flags = {"--chunk-bytes"}
    auto_flags = {
        "--max-detection-bytes",
        "--binary-chunk-bytes",
        "--minimum-confidence",
        "--ambiguity-margin",
    }
    option_arguments = (
        arguments[: arguments.index("--")] if "--" in arguments else arguments
    )
    supplied = {item.split("=", 1)[0] for item in option_arguments}
    plugin_ids = tuple(str(item) for item in values["plugin"])
    if len(plugin_ids) != len(set(plugin_ids)):
        parser.error("--plugin values must be unique")
    if values["detector"] is not None and kind != "auto":
        parser.error("--detector only applies to auto comparison")
    if values["renderer"] is None and (
        "--renderer-media-type" in supplied or "--max-render-bytes" in supplied
    ):
        parser.error("renderer options require --renderer")
    if int(values["max_render_bytes"]) > 2**53:
        parser.error(f"--max-render-bytes must not exceed {2**53}")
    disallowed = {
        "text": binary_flags | auto_flags,
        "binary": text_flags | auto_flags,
        "auto": text_flags | binary_flags,
    }[kind]
    if supplied & disallowed:
        parser.error(f"options do not apply to {kind}")
    if kind in ("binary", "auto"):
        exact_limit_names = {
            "max_input_bytes",
            "max_change_items",
            "max_change_payload_bytes",
        }
        if kind == "auto":
            exact_limit_names.add("max_detection_bytes")
        overflow = next(
            (name for name in sorted(exact_limit_names) if int(values[name]) > 2**53),
            None,
        )
        if overflow is not None:
            parser.error(f"--{overflow.replace('_', '-')} must not exceed {2**53}")
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
        str(values["before"]),
        str(values["after"]),
        str(values["format"]),
        spec,
        tuple(sorted(plugin_ids)),
        None if values["detector"] is None else str(values["detector"]),
        None if values["comparator"] is None else str(values["comparator"]),
        None if values["renderer"] is None else str(values["renderer"]),
        str(values["renderer_media_type"]),
        int(values["max_render_bytes"]),
    )
