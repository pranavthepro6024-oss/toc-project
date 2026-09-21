"""The finite shared station resource automaton R.

R deliberately contains no vehicle lifecycle logic.  It only admits resource
changes that preserve connector capacity, the grid power envelope, and the
configured discrete power tiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional


class GridMode(str, Enum):
    NORMAL = "normal"
    CURTAILED = "curtailed"
    EMERGENCY = "emergency"


class ResourceEvent(str, Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    POWER_START = "power_start"
    POWER_SET = "power_set"
    POWER_STOP = "power_stop"
    GRID_CURTAIL = "grid_curtail"
    GRID_RESTORE = "grid_restore"
    EMERGENCY_STOP = "emergency_stop"


@dataclass(frozen=True)
class ResourceConfig:
    connectors: int = 3
    power_limit_kw: int = 150
    power_tiers: tuple[int, ...] = (0, 50, 100, 150)
    curtailed_power_limit_kw: Optional[int] = None

    def __post_init__(self) -> None:
        if self.connectors < 0:
            raise ValueError("connectors must be non-negative")
        if self.power_limit_kw < 0:
            raise ValueError("power_limit_kw must be non-negative")
        tiers = tuple(sorted(set(self.power_tiers)))
        if not tiers or tiers[0] != 0 or any(t < 0 for t in tiers):
            raise ValueError("power_tiers must include 0 and contain non-negative values")
        if tiers[-1] > self.power_limit_kw:
            raise ValueError("a power tier cannot exceed power_limit_kw")
        object.__setattr__(self, "power_tiers", tiers)
        if self.curtailed_power_limit_kw is not None and not 0 <= self.curtailed_power_limit_kw <= self.power_limit_kw:
            raise ValueError("curtailed limit must be between 0 and power_limit_kw")


@dataclass(frozen=True)
class ResourceState:
    occupied_connectors: int = 0
    power_kw: int = 0
    grid_mode: GridMode = GridMode.NORMAL

    @property
    def available_connectors(self) -> int:
        return 0  # replaced by SharedResourceAutomaton.available_connectors


class SharedResourceAutomaton:
    """A small deterministic automaton for the station-wide resource state."""

    def __init__(self, config: Optional[ResourceConfig] = None) -> None:
        self.config = config or ResourceConfig()
        self.states: FrozenSet[ResourceState] = frozenset()
        self.start_state = ResourceState()

    def power_limit(self, state: ResourceState) -> int:
        if state.grid_mode is GridMode.CURTAILED:
            return self.config.curtailed_power_limit_kw if self.config.curtailed_power_limit_kw is not None else self.config.power_limit_kw
        if state.grid_mode is GridMode.EMERGENCY:
            return 0
        return self.config.power_limit_kw

    def available_connectors(self, state: ResourceState) -> int:
        return self.config.connectors - state.occupied_connectors

    def _power(self, value: int) -> int:
        if value not in self.config.power_tiers:
            raise ValueError(f"power must be one of {self.config.power_tiers}, got {value}")
        return value

    def step(self, state: ResourceState, event: ResourceEvent | str, power_kw: int = 0) -> Optional[ResourceState]:
        event = ResourceEvent(event)
        if event is ResourceEvent.CONNECT:
            if self.available_connectors(state) <= 0:
                return None
            return ResourceState(state.occupied_connectors + 1, state.power_kw, state.grid_mode)
        if event is ResourceEvent.DISCONNECT:
            if state.occupied_connectors <= 0 or power_kw != 0:
                return None
            return ResourceState(state.occupied_connectors - 1, state.power_kw, state.grid_mode)
        if event in (ResourceEvent.POWER_START, ResourceEvent.POWER_SET):
            requested = self._power(power_kw)
            if requested < 0 or requested + state.power_kw > self.power_limit(state):
                return None
            if state.occupied_connectors <= 0:
                return None
            return ResourceState(state.occupied_connectors, state.power_kw + requested, state.grid_mode)
        if event is ResourceEvent.POWER_STOP:
            if not 0 <= power_kw <= state.power_kw:
                return None
            return ResourceState(state.occupied_connectors, state.power_kw - power_kw, state.grid_mode)
        if event is ResourceEvent.GRID_CURTAIL:
            nxt = ResourceState(state.occupied_connectors, state.power_kw, GridMode.CURTAILED)
            return nxt if nxt.power_kw <= self.power_limit(nxt) else None
        if event is ResourceEvent.GRID_RESTORE:
            return ResourceState(state.occupied_connectors, state.power_kw, GridMode.NORMAL)
        if event is ResourceEvent.EMERGENCY_STOP:
            return ResourceState(state.occupied_connectors, 0, GridMode.EMERGENCY)
        raise AssertionError(event)

    # Common aliases used by callers treating R as a transition system.
    transition = step
    successors = lambda self, state: tuple(
        (event, nxt) for event in ResourceEvent
        if (nxt := self.step(state, event, 0)) is not None
    )
