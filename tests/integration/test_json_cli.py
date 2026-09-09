from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from platydiff.cli.parser import parse_command
from platydiff.core.models import JsonCompareSpec


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "platydiff", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def pair(tmp_path: Path, before: str, after: str) -> tuple[Path, Path]:
    left = tmp_path / "before.json"
    right = tmp_path / "after.json"
    left.write_text(before, encoding="utf-8")
    right.write_text(after, encoding="utf-8")
    return left, right


def test_json_shortcut_and_compare_alias_share_result(tmp_path: Path) -> None:
    before, after = pair(tmp_path, '{"a":1}', '{"a":2}')

    shortcut = run_cli("json", "--format", "json", str(before), str(after))
    alias = run_cli(
        "compare",
        "--type",
        "json",
        "--format",
        "json",
        str(before),
        str(after),
    )

    assert shortcut.returncode == alias.returncode == 1
    shortcut_data = json.loads(shortcut.stdout)
    alias_data = json.loads(alias.stdout)
    assert shortcut_data["schema_version"] == 3
    assert shortcut_data["result"] == alias_data["result"]
    assert shortcut.stderr == alias.stderr == ""


def test_json_cli_accepts_every_normalized_option(tmp_path: Path) -> None:
    before, after = pair(tmp_path, "1", "1.0")

    result = run_cli(
        "json",
        "--format",
        "json",
        "--encoding",
        "utf-8-sig",
        "--number-mode",
        "lexical",
        "--detail",
        "digest_only",
        "--max-input-bytes",
        "99",
        "--max-scalar-bytes",
        "98",
        "--max-depth",
        "97",
        "--max-nodes",
        "96",
        "--max-number-digits",
        "95",
        "--max-abs-exponent",
        "94",
        "--max-compare-work",
        "93",
        "--max-change-items",
        "92",
        "--max-change-payload-bytes",
        "91",
        str(before),
        str(after),
    )

    assert result.returncode == 1
    data = json.loads(result.stdout)
    spec = data["result"]["provenance"]["spec"]
    assert spec["encoding"] == "utf-8-sig"
    assert spec["number_mode"] == "lexical"
    assert spec["detail_mode"] == "digest_only"
    assert spec["limits"] == {
        "max_input_bytes": 99,
        "max_scalar_bytes": 98,
        "max_depth": 97,
        "max_nodes": 96,
        "max_number_digits": 95,
        "max_abs_exponent": 94,
        "max_compare_work": 93,
        "max_change_items": 92,
        "max_change_payload_bytes": 91,
    }


@pytest.mark.parametrize(
    "arguments",
    [
        ("json", "--plugin", "org.example.plugin", "a", "b"),
        ("json", "--comparator", "json", "a", "b"),
        ("json", "--renderer", "org.example.renderer", "a", "b"),
        ("compare", "--type", "json", "--detector", "text", "a", "b"),
        ("json", "--newline", "preserve", "a", "b"),
        ("json", "--max-depth", str(2**53 + 1), "a", "b"),
    ],
)
def test_json_usage_errors_exit_two_before_comparison(
    arguments: tuple[str, ...],
) -> None:
    result = run_cli(*arguments)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "usage:" in result.stderr


def test_json_decode_failure_is_schema_v3_exit_three(tmp_path: Path) -> None:
    before, after = pair(tmp_path, '{"a":1,}', "{}")

    result = run_cli("json", "--format", "json", str(before), str(after))

    assert result.returncode == 3
    data = json.loads(result.stdout)
    assert data["schema_version"] == 3
    assert data["kind"] == "failed"
    assert data["problem"]["code"] == "decode_error"


def test_json_terminal_escapes_paths_and_typed_values(tmp_path: Path) -> None:
    before, after = pair(tmp_path, '{"a\\u001b":"old\\n"}', '{"a\\u001b":"new\\t"}')

    result = run_cli("json", str(before), str(after))

    assert result.returncode == 1
    assert "replace /a\\x1b" in result.stdout
    assert '[string] "old\\x0a"' in result.stdout
    assert "\x1b" not in result.stdout


def test_parse_command_constructs_json_spec() -> None:
    command = parse_command(["compare", "--type", "json", "a", "b"])

    assert isinstance(command.spec, JsonCompareSpec)
