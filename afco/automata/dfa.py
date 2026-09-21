"""Deterministic Finite Automaton (DFA) implementation.

Includes formal language recognition, explainable trace diagnostics,
and dynamic admissibility computation from transition rules.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple


@dataclass(frozen=True)
class TraceResult:
    """Result of tracing a word through a DFA, detailing acceptance or rejection."""
    accepted: bool
    path: List[Any]
    failure_index: Optional[int] = None
    rejected_symbol: Optional[Any] = None
    admissible_symbols: Optional[Set[Any]] = None
    terminal_state: Optional[Any] = None

    def explain(self) -> str:
        """Format a detailed explanation of the trace outcome."""
        if self.accepted:
            return f"ACCEPTED: Word completed in accepting state '{self.terminal_state}' along path: {self.path}."
        if self.failure_index is not None:
            return (
                f"REJECTED at step {self.failure_index}: Symbol '{self.rejected_symbol}' is invalid from "
                f"state '{self.terminal_state}'. Admissible symbols are: {sorted(list(self.admissible_symbols or []))}."
            )
        return f"REJECTED: Word consumed entirely, but halted in non-accepting state '{self.terminal_state}'."


@dataclass(frozen=True)
class DFA:
    """A Deterministic Finite Automaton (Q, Sigma, delta, q0, F).

    Attributes:
        states: Finite set of states Q.
        alphabet: Finite set of input symbols Sigma.
        transitions: Transition function delta: Q x Sigma -> Q.
                     Undefined pairs represent partial transitions (rejections).
        start_state: Initial state q0 in Q.
        accepting_states: Subset of states F subseteq Q.
    """
    states: FrozenSet[Any]
    alphabet: FrozenSet[Any]
    transitions: Dict[Tuple[Any, Any], Any]
    start_state: Any
    accepting_states: FrozenSet[Any]

    def __post_init__(self) -> None:
        """Validate DFA invariants."""
        if self.start_state not in self.states:
            raise ValueError(f"Start state '{self.start_state}' is not in states Q.")
        if not self.accepting_states.issubset(self.states):
            extra = self.accepting_states - self.states
            raise ValueError(f"Accepting states contains elements not in Q: {extra}")
        for (q, a), target in self.transitions.items():
            if q not in self.states:
                raise ValueError(f"Transition source '{q}' not in Q.")
            if a not in self.alphabet:
                raise ValueError(f"Transition symbol '{a}' not in Sigma.")
            if target not in self.states:
                raise ValueError(f"Transition target '{target}' not in Q.")

    def step(self, state: Any, symbol: Any) -> Optional[Any]:
        """Apply delta(state, symbol). Returns None if transition is undefined."""
        return self.transitions.get((state, symbol))

    def admissible_symbols(self, state: Any) -> Set[Any]:
        """Compute Admissible(state) = {a in Sigma | delta(state, a) is defined}."""
        return {a for a in self.alphabet if (state, a) in self.transitions}

    def accepts(self, word: Iterable[Any]) -> bool:
        """Determine whether the input word is accepted by the DFA."""
        current = self.start_state
        for sym in word:
            next_state = self.step(current, sym)
            if next_state is None:
                return False
            current = next_state
        return current in self.accepting_states

    def trace(self, word: Iterable[Any]) -> TraceResult:
        """Execute a word through the DFA with full diagnostic tracing."""
        current = self.start_state
        path = [current]

        for idx, sym in enumerate(word):
            next_state = self.step(current, sym)
            if next_state is None:
                return TraceResult(
                    accepted=False,
                    path=path,
                    failure_index=idx,
                    rejected_symbol=sym,
                    admissible_symbols=self.admissible_symbols(current),
                    terminal_state=current,
                )
            current = next_state
            path.append(current)

        return TraceResult(
            accepted=current in self.accepting_states,
            path=path,
            failure_index=None,
            rejected_symbol=None,
            admissible_symbols=self.admissible_symbols(current),
            terminal_state=current,
        )
