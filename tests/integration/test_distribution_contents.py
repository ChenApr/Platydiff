"""Regression coverage for bounded source and wheel distribution contents."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


def _copy_build_source(project_root: Path, destination: Path) -> None:
    for filename in (
        "CHANGELOG.md",
        "LICENSE",
        "README.md",
        "README_zh.md",
        "pyproject.toml",
    ):
        shutil.copy2(project_root / filename, destination / filename)
    for directory in (".github", "docs", "platydiff", "tests"):
        shutil.copytree(project_root / directory, destination / directory)


def test_built_distributions_use_explicit_content_boundaries(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    source = tmp_path / "source"
    source.mkdir()
    _copy_build_source(project_root, source)
    (source / "_to_delete").mkdir()
    (source / "_to_delete" / "private-sentinel.txt").write_text(
        "must not ship", encoding="utf-8"
    )
    (source / "untracked-root-sentinel.txt").write_text(
        "must not ship", encoding="utf-8"
    )
    output = tmp_path / "dist"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--sdist",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(output),
        ],
        cwd=source,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr

    sdist = next(output.glob("*.tar.gz"))
    wheel = next(output.glob("*.whl"))
    with tarfile.open(sdist, "r:gz") as archive:
        sdist_names = set(archive.getnames())
    prefix = "platydiff-0.1.0.dev0/"
    assert prefix + "pyproject.toml" in sdist_names
    assert prefix + "LICENSE" in sdist_names
    assert prefix + "platydiff/core/models.py" in sdist_names
    assert prefix + "tests/unit/test_contracts.py" in sdist_names
    assert not any("_to_delete" in name for name in sdist_names)
    assert not any("untracked-root-sentinel" in name for name in sdist_names)

    with zipfile.ZipFile(wheel) as archive:
        wheel_names = set(archive.namelist())
    assert "platydiff/core/models.py" in wheel_names
    assert "platydiff/py.typed" in wheel_names
    assert any(name.endswith(".dist-info/licenses/LICENSE") for name in wheel_names)
    assert not any("_to_delete" in name for name in wheel_names)
