"""Lightweight public contracts and pipeline infrastructure."""

from platydiff.core.serialization import (
    SerializationError,
    dumps_outcome,
    loads_outcome,
    outcome_from_data,
    outcome_to_data,
    spec_from_data,
    spec_to_data,
)

__all__ = [
    "SerializationError",
    "dumps_outcome",
    "loads_outcome",
    "outcome_from_data",
    "outcome_to_data",
    "spec_from_data",
    "spec_to_data",
]
