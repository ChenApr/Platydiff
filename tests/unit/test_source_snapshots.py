"""Tests for Phase 2 private bounded replayable source snapshots."""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from platydiff import BytesSource, PathSource, TextSource
from platydiff.core._sources import SourceSnapshot, open_source_snapshot
from platydiff.core.models import PipelineStage, SourceKind
from platydiff.core.problems import (
    InputOutputError,
    ResourceLimitError,
    SourceChangedError,
)


def _read_all(source: BytesSource | TextSource | PathSource, chunk_bytes: int) -> bytes:
    with open_source_snapshot(source, max_input_bytes=1024) as snapshot:
        return b"".join(
            snapshot.iter_chunks(chunk_bytes, stage=PipelineStage.COMPARING)
        )


@pytest.mark.parametrize(
    ("source", "kind", "expected"),
    [
        (BytesSource(b"abcdef", label="bytes"), SourceKind.BYTES, b"abcdef"),
        (TextSource("a界c", label="text"), SourceKind.TEXT, "a界c".encode()),
    ],
)
def test_owned_snapshots_are_bounded_and_replayable(
    source: BytesSource | TextSource, kind: SourceKind, expected: bytes
) -> None:
    with open_source_snapshot(source, max_input_bytes=len(expected)) as snapshot:
        assert snapshot.source_kind is kind
        assert snapshot.label is not None
        assert snapshot.size_bytes == len(expected)
        assert snapshot.read_prefix(2, stage=PipelineStage.DETECTING) == expected[:2]
        assert (
            b"".join(snapshot.iter_chunks(2, stage=PipelineStage.COMPARING)) == expected
        )


@pytest.mark.parametrize(
    "source",
    [BytesSource(b"abc"), TextSource("界")],
)
def test_owned_snapshot_limit_is_inclusive(source: BytesSource | TextSource) -> None:
    expected = source.data if isinstance(source, BytesSource) else source.text.encode()
    assert _read_all(source, 1) == expected
    with pytest.raises(ResourceLimitError) as raised:
        open_source_snapshot(source, max_input_bytes=len(expected) - 1)
    assert raised.value.stage is PipelineStage.SOURCING


def test_path_snapshot_opens_once_and_replays_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "input.bin"
    path.write_bytes(b"abcdefgh")
    open_calls = 0
    real_open = os.open

    def counted_open(*args: object, **kwargs: object) -> int:
        nonlocal open_calls
        open_calls += 1
        return real_open(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "open", counted_open)
    with open_source_snapshot(PathSource(path), max_input_bytes=8) as snapshot:
        assert snapshot.metadata is not None
        assert snapshot.read_prefix(3, stage=PipelineStage.DETECTING) == b"abc"
        assert (
            b"".join(snapshot.iter_chunks(3, stage=PipelineStage.COMPARING))
            == b"abcdefgh"
        )
    assert open_calls == 1


def test_path_snapshot_accepts_symlink_to_regular_file(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_bytes(b"data")
    link = tmp_path / "link"
    link.symlink_to(target)

    assert _read_all(PathSource(link), 2) == b"data"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO files are unavailable")
def test_path_snapshot_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    started = time.monotonic()
    with pytest.raises(InputOutputError) as raised:
        open_source_snapshot(PathSource(fifo), max_input_bytes=10)
    assert time.monotonic() - started < 1.0
    assert raised.value.retryable is False


def test_path_snapshot_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(InputOutputError) as raised:
        open_source_snapshot(PathSource(tmp_path), max_input_bytes=10)
    assert raised.value.retryable is False


@pytest.mark.parametrize(
    "stage",
    [PipelineStage.DETECTING, PipelineStage.DECODING, PipelineStage.COMPARING],
)
def test_path_snapshot_reports_mutation_at_observing_stage(
    tmp_path: Path, stage: PipelineStage
) -> None:
    path = tmp_path / "mutable"
    path.write_bytes(b"before")
    with open_source_snapshot(PathSource(path), max_input_bytes=20) as snapshot:
        path.write_bytes(b"after-after")
        with pytest.raises(SourceChangedError) as raised:
            snapshot.ensure_unchanged(stage=stage)
    assert raised.value.stage is stage


def test_read_prefix_respects_zero_and_snapshot_limit() -> None:
    with open_source_snapshot(BytesSource(b"abc"), max_input_bytes=3) as snapshot:
        assert snapshot.read_prefix(0, stage=PipelineStage.DETECTING) == b""
        assert snapshot.read_prefix(100, stage=PipelineStage.DETECTING) == b"abc"


def test_zero_prefix_budget_does_not_advance_source_iterator() -> None:
    class SpySnapshot(SourceSnapshot):
        source_kind = SourceKind.BYTES
        label = None
        size_bytes = 3

        def __init__(self) -> None:
            super().__init__(max_input_bytes=3)
            self.iterator_advances = 0

        def iter_chunks(
            self, chunk_bytes: int, *, stage: PipelineStage
        ) -> Iterator[bytes]:
            del chunk_bytes, stage
            self.iterator_advances += 1
            yield b"abc"

    snapshot = SpySnapshot()
    assert snapshot.read_prefix(0, stage=PipelineStage.DETECTING) == b""
    assert snapshot.iterator_advances == 0


def test_bounded_path_prefix_checks_integrity_before_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "mutable-prefix"
    path.write_bytes(b"abc")
    real_read = os.read

    def mutate_after_read(descriptor: int, count: int) -> bytes:
        data = real_read(descriptor, count)
        path.write_bytes(b"changed-after-prefix")
        return data

    with open_source_snapshot(PathSource(path), max_input_bytes=32) as snapshot:
        monkeypatch.setattr(os, "read", mutate_after_read)
        with pytest.raises(SourceChangedError) as raised:
            snapshot.read_prefix(1, stage=PipelineStage.DETECTING)
    assert raised.value.stage is PipelineStage.DETECTING
