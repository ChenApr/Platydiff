"""Lightweight public contracts and pipeline infrastructure."""

from platydiff.core.serialization import (
    SerializationError,
    downgrade_outcome_v3_to_v2,
    dumps_outcome,
    loads_outcome,
    outcome_from_data,
    outcome_to_data,
    spec_from_data,
    spec_to_data,
    upgrade_outcome_v1_to_v2,
    upgrade_outcome_v1_to_v3,
    upgrade_outcome_v2_to_v3,
)

__all__ = [
    "SerializationError",
    "downgrade_outcome_v3_to_v2",
    "dumps_outcome",
    "loads_outcome",
    "outcome_from_data",
    "outcome_to_data",
    "spec_from_data",
    "spec_to_data",
    "upgrade_outcome_v1_to_v2",
    "upgrade_outcome_v1_to_v3",
    "upgrade_outcome_v2_to_v3",
]
