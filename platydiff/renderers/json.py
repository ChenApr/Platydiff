"""Exact schema-v1 and schema-v2 JSON outcome rendering."""

from __future__ import annotations

from platydiff.core.models import AnyCompareOutcome
from platydiff.core.serialization import dumps_outcome


def render_json(outcome: AnyCompareOutcome) -> str:
    """Render the complete outcome envelope without changing semantics."""
    return dumps_outcome(outcome, pretty=True)
