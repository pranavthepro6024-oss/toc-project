"""Dijkstra recovery search and the mandatory safety verification gate."""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from enum import Enum
from itertools import count
from typing import Callable, Iterable, List, Optional, Sequence, Set

from afco.automata.dfa import DFA
from afco.session.alphabet import COMPLETED
from afco.session.canonical import get_canonical_dfa
from afco.verify.properties import ALL_PROPERTY_BUILDERS
from afco.recovery.cost import TransitionCostModel
from afco.recovery.safe_states import SafeStatePolicy, safe_states
from afco.recovery.evidence import Evidence


class RecoveryStatus(str, Enum):
    FOUND = "FOUND"
    NO_PATH = "NO_PATH"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class RecoveryPlan:
    status: RecoveryStatus
    start_state: str
    target_state: Optional[str]
    path: List[str]
    cost: Optional[float]
    reason: Optional[str] = None

    @property
    def accepted(self) -> bool:
        return self.status is RecoveryStatus.FOUND


class VerificationGate:
    """Replay a proposed trace through every forbidden-property DFA."""

    def __init__(self, builders=None) -> None:
        self.builders = builders or ALL_PROPERTY_BUILDERS

    def verify(self, trace: Iterable[str]) -> tuple[bool, Optional[str]]:
        word = list(trace)
        for name, builder in self.builders.items():
            prop = builder()
            state = prop.start_state
            for symbol in word:
                state = prop.step(state, symbol)
                if state is None:
                    break
                if state in prop.accepting_states:
                    return False, name
        return True, None


class RecoveryEngine:
    """Find the least-cost verified path from a session state to ``S``."""

    def __init__(self, dfa: Optional[DFA] = None, *, policy: Optional[SafeStatePolicy] = None,
                 cost_model: Optional[Callable[[str, str, str], float]] = None,
                 gate: Optional[VerificationGate] = None) -> None:
        self.dfa = dfa or get_canonical_dfa()
        self.policy = policy or SafeStatePolicy()
        self.safe_states = safe_states(self.policy)
        self.cost_model = cost_model or TransitionCostModel()
        self.gate = gate or VerificationGate()

    def recover(self, state: str, evidence=None, *, history: Sequence[str] = ()) -> RecoveryPlan:
        """Run Dijkstra and gate each candidate before returning it.

        ``history`` is included in verification because P1/P3 violations are
        prefix properties; checking only the suffix would permit a bypass.
        """
        active_safe_states = self.safe_states
        if isinstance(evidence, Evidence):
            active_safe_states = safe_states(SafeStatePolicy(
                meter_verified=evidence.meter_verified,
                cable_interlock=evidence.cable_interlock,
                link_integrity=evidence.link_integrity,
                payment_guaranteed=evidence.payment_guaranteed,
            ))
        if state in active_safe_states:
            ok, bad = self.gate.verify(history)
            if not ok:
                return RecoveryPlan(RecoveryStatus.REJECTED, state, None, [], None,
                                    f"verification gate rejected {bad}")
            return RecoveryPlan(RecoveryStatus.FOUND, state, state, [], 0.0)

        serial = count()
        queue = [(0.0, next(serial), state, [])]
        best = {state: 0.0}
        while queue:
            cost, _, current, path = heapq.heappop(queue)
            if cost != best.get(current):
                continue
            if current in active_safe_states:
                ok, bad = self.gate.verify(list(history) + path)
                if ok:
                    return RecoveryPlan(RecoveryStatus.FOUND, state, current, path, cost)
                # Continue searching: this is the D8 hostile-bypass defense.
                continue
            for symbol in sorted(self.dfa.admissible_symbols(current), key=str):
                nxt = self.dfa.step(current, symbol)
                if nxt is None:
                    continue
                new_cost = cost + self.cost_model(current, str(symbol), str(nxt))
                if new_cost < best.get(nxt, float("inf")):
                    best[nxt] = new_cost
                    heapq.heappush(queue, (new_cost, next(serial), nxt,
                                           path + [str(symbol)]))
        return RecoveryPlan(RecoveryStatus.NO_PATH, state, None, [], None,
                            "no verified safe state is reachable")

    def verify_candidate(self, history: Sequence[str], path: Sequence[str]) -> bool:
        """Public gate for an externally proposed (possibly hostile) plan."""
        return self.gate.verify(list(history) + list(path))[0]

    def recover_to_completed(self, state: str, *, history: Sequence[str] = ()) -> RecoveryPlan:
        """Recover specifically to COMPLETED, while retaining the safety gate."""
        old = self.safe_states
        self.safe_states = frozenset({COMPLETED})
        try:
            return self.recover(state, history=history)
        finally:
            self.safe_states = old
