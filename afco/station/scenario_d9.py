"""Executable D9 benchmark: six vehicles, three connectors, 150 kW cap."""

from __future__ import annotations

from dataclasses import dataclass

from .composite import LazyStationProduct, StateSpaceMetrics
from .invariants import check_invariants
from .resource import ResourceConfig, SharedResourceAutomaton


@dataclass(frozen=True)
class D9Result:
    state: object
    metrics: StateSpaceMetrics
    invariant_breaches: tuple[str, ...]

    @property
    def is_safe(self) -> bool:
        return not self.invariant_breaches


def _advance(product: LazyStationProduct, state, lifecycle: tuple[tuple[str, str], ...]):
    for source, symbol in lifecycle:
        state = product.transition_state(state, source, symbol)
        if state is None:
            raise RuntimeError(f"D9 transition {source} -> {symbol} was rejected")
    return state


def run_scenario_d9(*, explore_limit: int | None = 5000) -> D9Result:
    product = LazyStationProduct(
        6,
        SharedResourceAutomaton(ResourceConfig(connectors=3, power_limit_kw=150, power_tiers=(0, 50, 100, 150))),
    )
    state = product.initial_state
    lifecycle = (
        ("IDLE", "reserve_req"), ("RESERVED", "auth_req"),
        ("AUTH_PENDING", "auth_ok"), ("AUTHORIZED", "plug_in"),
        ("CABLE_DETECTED", "lock_ok"), ("EV_CONNECTED", "ev_ready"),
        ("PRECHARGE", "power_start"),
    )
    for _ in range(3):
        state = _advance(product, state, lifecycle)
    metrics = product.explore(max_states=explore_limit)
    breaches = tuple(result.name for result in check_invariants(state, product.resource.config) if not result.holds)
    return D9Result(state, metrics, breaches)
