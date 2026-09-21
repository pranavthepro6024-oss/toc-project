"""Station invariants I1-I5, kept as predicates over composite states."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Iterable

from afco.session.alphabet import CHARGING, PAUSED_DISPATCH, PRECHARGE, SUSPENDED_EV, SUSPENDED_EVSE
from .resource import GridMode, ResourceConfig


@dataclass(frozen=True)
class InvariantResult:
    name: str
    holds: bool
    reason: str = ""


def invariant_i1_connectors(state, config: ResourceConfig) -> bool:
    return 0 <= state.resource.occupied_connectors <= config.connectors


def invariant_i2_power_cap(state, config: ResourceConfig) -> bool:
    limit = config.curtailed_power_limit_kw if state.resource.grid_mode is GridMode.CURTAILED and config.curtailed_power_limit_kw is not None else (0 if state.resource.grid_mode is GridMode.EMERGENCY else config.power_limit_kw)
    return 0 <= state.resource.power_kw <= limit


def invariant_i3_power_requires_connector(state, config: ResourceConfig) -> bool:
    return state.resource.power_kw == 0 or state.resource.occupied_connectors > 0


def invariant_i4_valid_grid_mode(state, config: ResourceConfig) -> bool:
    return isinstance(state.resource.grid_mode, GridMode)


def invariant_i5_session_state_shape(state, config: ResourceConfig) -> bool:
    return all(isinstance(value, str) for value in state.session_states)


def check_invariants(state, config: ResourceConfig) -> tuple[InvariantResult, ...]:
    checks: tuple[tuple[str, Callable], ...] = (
        ("I1_connector_capacity", invariant_i1_connectors),
        ("I2_grid_power_cap", invariant_i2_power_cap),
        ("I3_power_requires_connector", invariant_i3_power_requires_connector),
        ("I4_valid_grid_mode", invariant_i4_valid_grid_mode),
        ("I5_session_state_shape", invariant_i5_session_state_shape),
    )
    return tuple(InvariantResult(name, fn(state, config), "invariant violated" if not fn(state, config) else "") for name, fn in checks)
