"""Internal text intermediate representation and edit operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class TextLine:
    """A decoded text line with its original or normalized terminator."""

    content: str
    terminator: Literal["", "\n", "\r\n", "\r"]


@dataclass(frozen=True, slots=True)
class EditOperation:
    """One canonical operation in source order."""

    kind: Literal["equal", "delete", "insert"]
    line: TextLine
    before_index: int | None
    after_index: int | None

    def __post_init__(self) -> None:
        if self.kind == "equal" and (
            self.before_index is None or self.after_index is None
        ):
            raise ValueError("equal operations require both indexes")
        if self.kind == "delete" and (
            self.before_index is None or self.after_index is not None
        ):
            raise ValueError("delete operations require only a before index")
        if self.kind == "insert" and (
            self.before_index is not None or self.after_index is None
        ):
            raise ValueError("insert operations require only an after index")


@dataclass(frozen=True, slots=True)
class MyersResult:
    """A complete shortest edit script and its deterministic work count."""

    operations: tuple[EditOperation, ...]
    work_units: int
