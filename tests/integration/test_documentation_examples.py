"""Executable checks for the user-facing README examples."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from platydiff import TextCompareSpec, TextSource, compare
from platydiff.plugin_sdk import (
    CapabilityDeclarationV1,
    CapabilityKind,
    PluginManifestV1,
)


def test_readme_python_example() -> None:
    outcome = compare(
        TextSource("alpha\nbeta\n", label="before"),
        TextSource("alpha\ngamma\n", label="after"),
        TextCompareSpec(),
    )

    if outcome.kind == "completed":
        observed = (outcome.result.relation.value, outcome.result.verdict.value)
    else:
        raise AssertionError(outcome.problem.code)

    assert observed == ("different", "fail")


def test_readme_cli_examples(tmp_path: Path) -> None:
    before = tmp_path / "before.txt"
    after = tmp_path / "after.txt"
    before.write_text("same\n", encoding="utf-8", newline="")
    after.write_text("same\n", encoding="utf-8", newline="")

    for route in (
        ("compare", "--type", "text"),
        ("text",),
    ):
        result = subprocess.run(
            [sys.executable, "-m", "platydiff", *route, str(before), str(after)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "equal: pass" in result.stdout


def test_plugin_sdk_documentation_example() -> None:
    manifest = PluginManifestV1(
        manifest_schema_version=1,
        plugin_id="org.example.scidiff",
        plugin_version="1.0",
        api_major=1,
        minimum_api_minor=0,
        maximum_api_minor=0,
        required_host_features=(),
        capabilities=(
            CapabilityDeclarationV1(
                capability_id="org.example.scidiff.text_exact",
                kind=CapabilityKind.COMPARATOR,
                implementation_version="1.0",
            ),
        ),
        license_expression="Apache-2.0",
    )
    assert manifest.plugin_id == "org.example.scidiff"
