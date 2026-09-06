"""Text comparison implementation."""

from platydiff.comparators.text.models import EditOperation, MyersResult, TextLine
from platydiff.comparators.text.myers import ALGORITHM_ID, shortest_edit_script

__all__ = [
    "ALGORITHM_ID",
    "EditOperation",
    "MyersResult",
    "TextLine",
    "shortest_edit_script",
]
