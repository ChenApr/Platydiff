"""Internal Phase 1 capability registry; not a public plugin API."""

from __future__ import annotations

from collections.abc import Callable

from platydiff.core.models import CompareSpec, Source
from platydiff.core.pipeline import ComparisonCompletion

type ComparisonExecutor = Callable[[Source, Source, CompareSpec], ComparisonCompletion]


class InternalRegistry:
    """A deliberately private exact-kind registry for built-in capabilities."""

    def __init__(self) -> None:
        self._executors: dict[str, ComparisonExecutor] = {}

    def register(self, kind: str, executor: ComparisonExecutor) -> None:
        if kind in self._executors:
            raise RuntimeError(f"duplicate internal comparator kind: {kind}")
        self._executors[kind] = executor

    def resolve(self, spec: CompareSpec) -> ComparisonExecutor:
        try:
            return self._executors[spec.kind]
        except KeyError as error:
            raise RuntimeError("no internal comparator for validated spec") from error
