"""Session runtime instance and explainable execution verification.

Tracks individual charging session lifecycles, maintains event history,
and produces explainable verdicts with BFS-synthesized repair paths.
"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
import uuid

from afco.automata.dfa import DFA
from afco.automata.reachability import trap_states
from afco.session.alphabet import (
    COMPLETED,
    IDLE,
    METER_TICK,
    RESERVE,
    RESERVE_REQ,
)
from afco.session.canonical import get_canonical_dfa


@dataclass(frozen=True)
class VerificationVerdict:
    """Structured, explainable verification verdict conforming to §16."""
    is_safe: bool
    failure_index: Optional[int] = None
    rejected_symbol: Optional[str] = None
    violated_property: Optional[str] = None
    admissible_symbols: Optional[Set[str]] = None
    counterexample: Optional[List[str]] = None
    repair_path: Optional[List[str]] = None

    def format_report(self) -> str:
        """Renders standard human-readable explanation matching report §13/§16."""
        if self.is_safe:
            return "VERDICT: ACCEPT — Trace is formally safe and admits valid completion."
        return (
            f"VERDICT: REJECT\n"
            f"  - Failure Position   : Step {self.failure_index}\n"
            f"  - Rejected Symbol    : '{self.rejected_symbol}'\n"
            f"  - Violated Invariant : {self.violated_property}\n"
            f"  - Admissible Symbols : {sorted(list(self.admissible_symbols or []))}\n"
            f"  - Counterexample     : {' -> '.join(self.counterexample or [])}\n"
            f"  - Synthesized Repair : {' -> '.join(self.repair_path or [])}"
        )


def find_shortest_repair_path(dfa: DFA, from_state: Any) -> Optional[List[str]]:
    """Compute the shortest sequence of symbols from from_state to any accepting state in F.

    Uses Breadth-First Search (BFS) over the DFA transition graph.
    Returns None if no accepting state is reachable (e.g. from FAULT_TERMINAL).
    """
    if from_state in dfa.accepting_states:
        return []

    visited: Set[Any] = {from_state}
    queue: deque[Tuple[Any, List[str]]] = deque([(from_state, [])])

    while queue:
        state, path = queue.popleft()
        for sym in sorted(dfa.admissible_symbols(state), key=str):
            nxt = dfa.step(state, sym)
            if nxt is None or nxt in visited:
                continue

            new_path = path + [str(sym)]
            if nxt in dfa.accepting_states:
                return new_path

            visited.add(nxt)
            queue.append((nxt, new_path))

    return None


class SessionInstance:
    """Runtime instance for an EV charging session governed by M_S.

    Attributes:
        session_id: Unique session identifier.
        current_state: Current lifecycle state in Q_S.
        dfa: Governing DFA (defaults to canonical M_S).
        history: Sequence of executed transitions (from_state, symbol, to_state).
        meter_kwh: Cumulative energy transferred in kWh.
        last_verdict: Most recent verification verdict.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        dfa: Optional[DFA] = None,
        initial_state: Optional[str] = None,
    ) -> None:
        self.session_id: str = session_id or f"sess-{uuid.uuid4().hex[:8]}"
        self.dfa: DFA = dfa or get_canonical_dfa()
        self.current_state: str = initial_state or self.dfa.start_state
        self.history: List[Tuple[str, str, str]] = []
        self.meter_kwh: float = 0.0
        self.last_verdict: Optional[VerificationVerdict] = None

    def _normalize_symbol(self, symbol: str) -> str:
        """Map convenience aliases (e.g. 'reserve' -> 'reserve_req') to formal symbols."""
        if symbol == RESERVE:
            return RESERVE_REQ
        return symbol

    def step(self, symbol: str) -> bool:
        """Attempt to advance the session by executing an input symbol.

        Returns:
            True if the transition is defined and state advanced;
            False if undefined (rejection), preserving current state.
        """
        canonical_symbol = self._normalize_symbol(symbol)
        nxt = self.dfa.step(self.current_state, canonical_symbol)

        if nxt is None:
            repair = find_shortest_repair_path(self.dfa, self.current_state)
            self.last_verdict = VerificationVerdict(
                is_safe=False,
                failure_index=len(self.history),
                rejected_symbol=symbol,
                violated_property="PartialDeltaUndefined",
                admissible_symbols=self.admissible_symbols(),
                counterexample=[sym for _, sym, _ in self.history] + [symbol],
                repair_path=repair,
            )
            return False

        # Transition is defined
        from_st = self.current_state
        self.current_state = nxt
        self.history.append((from_st, canonical_symbol, nxt))

        if canonical_symbol == METER_TICK:
            self.meter_kwh += 0.25

        if self.is_accepted():
            self.last_verdict = VerificationVerdict(
                is_safe=True,
                repair_path=[],
            )
        return True

    def admissible_symbols(self) -> Set[str]:
        """Compute the set of currently admissible symbols from the active state."""
        return {str(s) for s in self.dfa.admissible_symbols(self.current_state)}

    def is_accepted(self) -> bool:
        """Determine whether the current session state is accepting."""
        return self.current_state in self.dfa.accepting_states

    def is_trap(self) -> bool:
        """Check if the session has entered a dead-end trap state."""
        return self.current_state in trap_states(self.dfa)

    def synthesize_repair_path(self) -> Optional[List[str]]:
        """Synthesize the shortest path from the active state to an accepting state."""
        return find_shortest_repair_path(self.dfa, self.current_state)

    def evaluate_trace(self, word: Iterable[str]) -> VerificationVerdict:
        """Evaluate an entire event sequence through the DFA with full diagnostic feedback."""
        current = self.dfa.start_state
        consumed: List[str] = []

        for idx, raw_sym in enumerate(word):
            sym = self._normalize_symbol(raw_sym)
            nxt = self.dfa.step(current, sym)
            if nxt is None:
                repair = find_shortest_repair_path(self.dfa, current)
                return VerificationVerdict(
                    is_safe=False,
                    failure_index=idx,
                    rejected_symbol=raw_sym,
                    violated_property="PartialDeltaUndefined",
                    admissible_symbols={str(s) for s in self.dfa.admissible_symbols(current)},
                    counterexample=consumed + [raw_sym],
                    repair_path=repair,
                )
            consumed.append(sym)
            current = nxt

        if current in self.dfa.accepting_states:
            return VerificationVerdict(
                is_safe=True,
                counterexample=None,
                repair_path=[],
            )

        repair = find_shortest_repair_path(self.dfa, current)
        return VerificationVerdict(
            is_safe=False,
            failure_index=len(consumed),
            rejected_symbol=None,
            violated_property="NonAcceptingTerminalState",
            admissible_symbols={str(s) for s in self.dfa.admissible_symbols(current)},
            counterexample=consumed,
            repair_path=repair,
        )
