"""Shared-resource station composition for concurrent AFCO sessions."""

from .resource import (
    GridMode,
    ResourceConfig,
    ResourceEvent,
    ResourceState,
    SharedResourceAutomaton,
)
from .composite import (
    CompositeState,
    LazyStationProduct,
    StationTransition,
    StateSpaceMetrics,
)
from .invariants import (
    InvariantResult,
    check_invariants,
    invariant_i1_connectors,
    invariant_i2_power_cap,
    invariant_i3_power_requires_connector,
    invariant_i4_valid_grid_mode,
    invariant_i5_session_state_shape,
)
from .scenario_d9 import D9Result, run_scenario_d9

__all__ = [
    "GridMode", "ResourceConfig", "ResourceEvent", "ResourceState",
    "SharedResourceAutomaton", "CompositeState", "LazyStationProduct",
    "StationTransition", "StateSpaceMetrics", "InvariantResult",
    "check_invariants", "invariant_i1_connectors", "invariant_i2_power_cap",
    "invariant_i3_power_requires_connector", "invariant_i4_valid_grid_mode",
    "invariant_i5_session_state_shape",
    "D9Result", "run_scenario_d9",
]
