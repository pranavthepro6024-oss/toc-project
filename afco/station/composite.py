"""Lazy product ``M_S^N x R`` with multiset symmetry reduction."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from typing import Iterable, Optional

from afco.session.alphabet import (
    CABLE_DETECTED, CHARGING, EV_CONNECTED, EV_STOP, GRID_CURTAIL,
    ISOLATING, PAUSED_DISPATCH, POWER_RAMP_DOWN, POWER_START, POWER_STOP,
    PRECHARGE, SUSPENDED_EV, SUSPENDED_EVSE, UNPLUG, UNPLUGGED,
)
from afco.session.canonical import get_canonical_dfa
from .invariants import check_invariants
from .resource import ResourceConfig, ResourceEvent, ResourceState, SharedResourceAutomaton


_POWER_ACTIVE = frozenset({CHARGING, PRECHARGE, PAUSED_DISPATCH, SUSPENDED_EV, SUSPENDED_EVSE, ISOLATING})


@dataclass(frozen=True)
class CompositeState:
    """Canonical state; sessions are stored sorted, so vehicle identities vanish."""

    session_states: tuple[str, ...]
    resource: ResourceState

    def __post_init__(self) -> None:
        object.__setattr__(self, "session_states", tuple(sorted(self.session_states)))

    @property
    def key(self) -> tuple:
        return self.session_states, self.resource


@dataclass(frozen=True)
class StationTransition:
    source: CompositeState
    session_index: int
    symbol: str
    target: CompositeState
    power_kw: int = 0


@dataclass(frozen=True)
class StateSpaceMetrics:
    naive_state_count: int
    symmetry_reduced_state_count: int
    explored_state_count: int


class LazyStationProduct:
    """On-demand station product.

    ``successors`` computes only one-step reachable states.  ``explore`` is an
    optional bounded BFS instrumentation pass and never builds the Cartesian
    product eagerly.
    """

    def __init__(self, session_count: int, resource: Optional[SharedResourceAutomaton] = None, *, initial_states: Optional[Iterable[str]] = None) -> None:
        if session_count < 0:
            raise ValueError("session_count must be non-negative")
        self.session_count = session_count
        self.resource = resource or SharedResourceAutomaton()
        dfa = get_canonical_dfa()
        states = tuple(initial_states) if initial_states is not None else (dfa.start_state,) * session_count
        if len(states) != session_count or any(s not in dfa.states for s in states):
            raise ValueError("initial_states must contain exactly session_count canonical states")
        self.initial_state = CompositeState(states, self.resource.start_state)
        self._dfa = dfa
        self._last_metrics: Optional[StateSpaceMetrics] = None

    def _resource_transition(self, current: CompositeState, before: str, after: str, symbol: str, power_kw: int) -> Optional[ResourceState]:
        r = current.resource
        # A connector is occupied when a cable is detected and released only
        # after the session is physically unplugged.
        if after == CABLE_DETECTED and before != CABLE_DETECTED:
            return self.resource.step(r, ResourceEvent.CONNECT)
        if symbol == UNPLUG or (after == UNPLUGGED and before != UNPLUGGED):
            return self.resource.step(r, ResourceEvent.DISCONNECT)
        if symbol == POWER_START:
            return self.resource.step(r, ResourceEvent.POWER_START, power_kw or self.resource.config.power_tiers[1])
        if symbol in (POWER_STOP, POWER_RAMP_DOWN):
            return self.resource.step(r, ResourceEvent.POWER_STOP, power_kw or r.power_kw)
        if symbol == GRID_CURTAIL:
            return self.resource.step(r, ResourceEvent.GRID_CURTAIL)
        if symbol == EV_STOP and after == SUSPENDED_EV:
            return self.resource.step(r, ResourceEvent.POWER_STOP, r.power_kw)
        return r

    def successors(self, state: CompositeState) -> tuple[StationTransition, ...]:
        result: list[StationTransition] = []
        for index, before in enumerate(state.session_states):
            for symbol in sorted(self._dfa.admissible_symbols(before), key=str):
                after = self._dfa.step(before, symbol)
                if after is None:
                    continue
                # Work in physical session order before canonicalizing.  The
                # target index is retained only as an explanatory action.
                power = self.resource.config.power_tiers[1] if symbol == POWER_START else 0
                resource_state = self._resource_transition(state, before, after, symbol, power)
                if resource_state is None:
                    continue
                states = list(state.session_states)
                states[index] = after
                target = CompositeState(tuple(states), resource_state)
                if all(item.holds for item in check_invariants(target, self.resource.config)):
                    result.append(StationTransition(state, index, str(symbol), target, power))
        return tuple(result)

    def transition(self, state: CompositeState, session_index: int, symbol: str, power_kw: int = 0) -> Optional[CompositeState]:
        return next((t.target for t in self.successors(state) if t.session_index == session_index and t.symbol == symbol and (not power_kw or t.power_kw == power_kw)), None)

    def transition_state(self, state: CompositeState, session_state: str, symbol: str, power_kw: int = 0) -> Optional[CompositeState]:
        """Apply an event to one occurrence of ``session_state``.

        This is the preferred identity-free API: positional indices are not
        stable after multiset canonicalization.
        """
        return next((t.target for t in self.successors(state) if t.symbol == symbol and state.session_states[t.session_index] == session_state and (not power_kw or t.power_kw == power_kw)), None)

    def explore(self, max_states: Optional[int] = None) -> StateSpaceMetrics:
        """Explore reachable canonical states and report reduction metrics."""
        seen = {self.initial_state.key}
        queue = deque([self.initial_state])
        while queue and (max_states is None or len(seen) < max_states):
            state = queue.popleft()
            for transition in self.successors(state):
                if transition.target.key not in seen:
                    seen.add(transition.target.key)
                    queue.append(transition.target)
        raw_session_states = len(self._dfa.states) ** self.session_count
        # Resource states are finite and bounded by connectors and configured tiers.
        raw_resource_states = (self.resource.config.connectors + 1) * (len(self.resource.config.power_tiers)) * 3
        naive = raw_session_states * raw_resource_states
        self._last_metrics = StateSpaceMetrics(naive, len(seen), len(seen))
        return self._last_metrics

    @property
    def metrics(self) -> Optional[StateSpaceMetrics]:
        return self._last_metrics


# Friendly aliases for callers using the roadmap terminology.
LazyProduct = LazyStationProduct
CompositeAutomaton = LazyStationProduct
