"""Synthetic, non-executable distribution metadata for discovery profiles."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FakeDistribution:
    name: str
    version: str


class FakeEntryPoint:
    def __init__(
        self,
        name: str,
        factory: object,
        *,
        group: str = "platydiff.plugins.v1",
        value: str = "compat_plugin:manifest",
        distribution_name: str = "compat-plugin",
        distribution_version: str = "1.0",
        load_error: Exception | None = None,
        distribution: FakeDistribution | object | None = None,
    ) -> None:
        self.name = name
        self.group = group
        self.value = value
        self.dist = (
            FakeDistribution(distribution_name, distribution_version)
            if distribution is None
            else distribution
        )
        self.factory = factory
        self.load_error = load_error
        self.load_count = 0

    def load(self) -> object:
        self.load_count += 1
        if self.load_error is not None:
            raise self.load_error
        return self.factory
