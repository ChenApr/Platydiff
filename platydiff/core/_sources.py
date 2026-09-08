"""Private bounded, replayable source snapshots for automatic and binary routes."""

from __future__ import annotations

import os
import stat
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from types import TracebackType

from platydiff.core.models import (
    BytesSource,
    PathSource,
    PipelineStage,
    Source,
    SourceKind,
    TextSource,
)
from platydiff.core.problems import (
    InputOutputError,
    ResourceLimitError,
    SourceChangedError,
    SourceNotFoundError,
    SourcePermissionError,
)

_TEXT_ENCODING_SLICE_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class SnapshotMetadata:
    """Stable metadata captured from an opened regular file."""

    device: int
    inode: int
    size: int
    mtime_ns: int


class SourceSnapshot(ABC):
    """A bounded source that can replay detection bytes for later processing."""

    source_kind: SourceKind
    label: str | None
    size_bytes: int
    metadata: SnapshotMetadata | None = None

    def __init__(self, *, max_input_bytes: int) -> None:
        self._max_input_bytes = max_input_bytes

    def __enter__(self) -> SourceSnapshot:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def read_prefix(self, max_bytes: int, *, stage: PipelineStage) -> bytes:
        """Read a bounded prefix without consuming later full-source reads."""
        if max_bytes < 0:
            raise ValueError("max_bytes must be non-negative")
        limit = min(max_bytes, self._max_input_bytes)
        chunks: list[bytes] = []
        remaining = limit
        for chunk in self.iter_chunks(max(1, min(limit, 64 * 1024)), stage=stage):
            if not remaining:
                break
            selected = chunk[:remaining]
            chunks.append(selected)
            remaining -= len(selected)
            if remaining == 0:
                break
        return b"".join(chunks)

    @abstractmethod
    def iter_chunks(self, chunk_bytes: int, *, stage: PipelineStage) -> Iterator[bytes]:
        """Replay the complete source in chunks no larger than ``chunk_bytes``."""

    def ensure_unchanged(self, *, stage: PipelineStage) -> None:
        """Validate mutable backing state when the snapshot has any."""
        return None

    def close(self) -> None:
        """Release resources owned by the snapshot."""
        return None


class _BytesSnapshot(SourceSnapshot):
    def __init__(self, source: BytesSource, *, max_input_bytes: int) -> None:
        super().__init__(max_input_bytes=max_input_bytes)
        self.source_kind = SourceKind.BYTES
        self.label = source.label
        self._data = source.data
        self.size_bytes = len(source.data)
        _check_size(self.size_bytes, max_input_bytes)

    def iter_chunks(self, chunk_bytes: int, *, stage: PipelineStage) -> Iterator[bytes]:
        _check_chunk_bytes(chunk_bytes)
        del stage
        for offset in range(0, self.size_bytes, chunk_bytes):
            yield self._data[offset : offset + chunk_bytes]


class _TextSnapshot(SourceSnapshot):
    def __init__(self, source: TextSource, *, max_input_bytes: int) -> None:
        super().__init__(max_input_bytes=max_input_bytes)
        self.source_kind = SourceKind.TEXT
        self.label = source.label
        self._text = source.text
        self.size_bytes = _encoded_size(source.text, max_input_bytes)

    def iter_chunks(self, chunk_bytes: int, *, stage: PipelineStage) -> Iterator[bytes]:
        _check_chunk_bytes(chunk_bytes)
        del stage
        pending = bytearray()
        for encoded in _encoded_slices(self._text, chunk_bytes):
            pending.extend(encoded)
            while len(pending) >= chunk_bytes:
                yield bytes(pending[:chunk_bytes])
                del pending[:chunk_bytes]
        if pending:
            yield bytes(pending)


class _PathSnapshot(SourceSnapshot):
    def __init__(self, source: PathSource, *, max_input_bytes: int) -> None:
        super().__init__(max_input_bytes=max_input_bytes)
        self.source_kind = SourceKind.PATH
        self.label = source.path.name
        self._descriptor = _open_regular_file(source)
        try:
            metadata = _path_metadata(self._descriptor)
            _check_size(metadata.size, max_input_bytes)
        except BaseException:
            os.close(self._descriptor)
            self._descriptor = -1
            raise
        self.metadata = metadata
        self.size_bytes = metadata.size

    def iter_chunks(self, chunk_bytes: int, *, stage: PipelineStage) -> Iterator[bytes]:
        _check_chunk_bytes(chunk_bytes)
        self.ensure_unchanged(stage=stage)
        try:
            os.lseek(self._descriptor, 0, os.SEEK_SET)
            consumed = 0
            while True:
                chunk = os.read(self._descriptor, chunk_bytes)
                if not chunk:
                    break
                consumed += len(chunk)
                if consumed > self._max_input_bytes:
                    self.ensure_unchanged(stage=stage)
                    raise ResourceLimitError(
                        "A source exceeded the configured byte limit.", stage=stage
                    )
                yield chunk
            self.ensure_unchanged(stage=stage)
        except SourceChangedError:
            raise
        except OSError as error:
            raise InputOutputError("A source could not be read.") from error

    def ensure_unchanged(self, *, stage: PipelineStage) -> None:
        if self._descriptor < 0:
            raise RuntimeError("source snapshot is closed")
        try:
            current = _path_metadata(self._descriptor)
        except OSError as error:
            raise InputOutputError("A source could not be inspected.") from error
        if current != self.metadata:
            raise SourceChangedError(stage=stage)

    def close(self) -> None:
        if self._descriptor >= 0:
            os.close(self._descriptor)
            self._descriptor = -1


def open_source_snapshot(source: Source, *, max_input_bytes: int) -> SourceSnapshot:
    """Open one Phase 2 source snapshot without changing Phase 1 eager sourcing."""
    if max_input_bytes < 0:
        raise ValueError("max_input_bytes must be non-negative")
    if isinstance(source, PathSource):
        return _PathSnapshot(source, max_input_bytes=max_input_bytes)
    if isinstance(source, BytesSource):
        return _BytesSnapshot(source, max_input_bytes=max_input_bytes)
    if isinstance(source, TextSource):
        return _TextSnapshot(source, max_input_bytes=max_input_bytes)
    raise TypeError("unsupported source type")


def _open_regular_file(source: PathSource) -> int:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(source.path, flags)
    except FileNotFoundError as error:
        raise SourceNotFoundError("A source file was not found.") from error
    except PermissionError as error:
        raise SourcePermissionError(
            "Permission was denied while reading a source."
        ) from error
    except OSError as error:
        raise InputOutputError("A source could not be opened.") from error
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise InputOutputError("A source is not a regular file.", retryable=False)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _path_metadata(descriptor: int) -> SnapshotMetadata:
    metadata = os.fstat(descriptor)
    return SnapshotMetadata(
        device=metadata.st_dev,
        inode=metadata.st_ino,
        size=metadata.st_size,
        mtime_ns=metadata.st_mtime_ns,
    )


def _check_size(size: int, limit: int) -> None:
    if size > limit:
        raise ResourceLimitError(
            "A source exceeded the configured byte limit.",
            stage=PipelineStage.SOURCING,
        )


def _check_chunk_bytes(chunk_bytes: int) -> None:
    if chunk_bytes <= 0:
        raise ValueError("chunk_bytes must be positive")


def _encoded_size(text: str, limit: int) -> int:
    size = 0
    for chunk in _encoded_slices(text, _TEXT_ENCODING_SLICE_BYTES):
        size += len(chunk)
        _check_size(size, limit)
    return size


def _encoded_slices(text: str, target_bytes: int) -> Iterator[bytes]:
    character_count = max(1, target_bytes // 4)
    for offset in range(0, len(text), character_count):
        yield text[offset : offset + character_count].encode("utf-8", errors="strict")
