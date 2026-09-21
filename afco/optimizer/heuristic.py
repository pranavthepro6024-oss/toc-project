"""Non-authoritative scheduling heuristics. Their output always needs gating."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ScheduleItem:
    session_id: str
    power_kw: int
    priority: int = 0
    arrival_time: int = 0


@dataclass(frozen=True)
class ScheduleProposal:
    items: tuple[ScheduleItem, ...]
    name: str = "heuristic"

    @property
    def total_power_kw(self) -> int:
        return sum(item.power_kw for item in self.items)


class HeuristicOptimizer:
    """Greedy proposer; it deliberately does not enforce station invariants."""

    def propose(self, items: Iterable[ScheduleItem], *, strategy: str = "priority") -> ScheduleProposal:
        values = tuple(items)
        if strategy == "arrival":
            key = lambda x: (x.arrival_time, -x.priority)
        elif strategy == "power":
            key = lambda x: (x.power_kw, x.arrival_time, -x.priority)
        elif strategy == "priority":
            key = lambda x: (-x.priority, x.arrival_time, x.session_id)
        else:
            raise ValueError("strategy must be priority, arrival, or power")
        return ScheduleProposal(tuple(sorted(values, key=key)), strategy)

    optimize = propose
