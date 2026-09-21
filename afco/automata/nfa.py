"""Nondeterministic Finite Automaton (NFA) implementation.

Supports epsilon-transitions, epsilon-closure, multi-state stepping,
and acceptance testing.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Iterable, Optional, Set, Tuple


EPSILON = None  # None represents an epsilon transition


@dataclass(frozen=True)
class NFA:
    """A Nondeterministic Finite Automaton (Q, Sigma, delta, q0, F).

    Attributes:
        states: Finite set of states Q.
        alphabet: Finite set of input symbols Sigma (excluding epsilon).
        transitions: Transition function delta: Q x (Sigma U {EPSILON}) -> P(Q).
        start_state: Initial state q0 in Q (or initial states set).
        accepting_states: Set of accepting states F subseteq Q.
    """
    states: FrozenSet[Any]
    alphabet: FrozenSet[Any]
    transitions: Dict[Tuple[Any, Optional[Any]], FrozenSet[Any]]
    start_state: Any
    accepting_states: FrozenSet[Any]

    def __post_init__(self) -> None:
        """Validate NFA invariants."""
        if self.start_state not in self.states:
            raise ValueError(f"Start state '{self.start_state}' is not in states Q.")
        if not self.accepting_states.issubset(self.states):
            extra = self.accepting_states - self.states
            raise ValueError(f"Accepting states contains elements not in Q: {extra}")
        for (q, a), targets in self.transitions.items():
            if q not in self.states:
                raise ValueError(f"Transition source '{q}' not in Q.")
            if a is not None and a not in self.alphabet:
                raise ValueError(f"Transition symbol '{a}' not in Sigma or EPSILON.")
            if not targets.issubset(self.states):
                raise ValueError(f"Transition targets '{targets}' contain states not in Q.")

    def epsilon_closure(self, states: Iterable[Any]) -> FrozenSet[Any]:
        """Compute the epsilon-closure of a set of states."""
        closure: Set[Any] = set(states)
        stack: list[Any] = list(states)

        while stack:
            q = stack.pop()
            # Follow epsilon transitions
            for nxt in self.transitions.get((q, EPSILON), frozenset()):
                if nxt not in closure:
                    closure.add(nxt)
                    stack.append(nxt)

        return frozenset(closure)

    def step(self, current_states: Iterable[Any], symbol: Any) -> FrozenSet[Any]:
        """Given a set of states and an input symbol, compute next states with epsilon-closure."""
        if symbol not in self.alphabet:
            raise ValueError(f"Symbol '{symbol}' not in alphabet {self.alphabet}")

        next_states: Set[Any] = set()
        for q in current_states:
            targets = self.transitions.get((q, symbol), frozenset())
            next_states.update(targets)

        return self.epsilon_closure(next_states)

    def accepts(self, word: Iterable[Any]) -> bool:
        """Determine whether the word is accepted by the NFA."""
        current = self.epsilon_closure([self.start_state])
        for sym in word:
            current = self.step(current, sym)
            if not current:
                return False
        return bool(current & self.accepting_states)
