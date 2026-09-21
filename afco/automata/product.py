"""Product Automaton Construction.

Supports synchronous product construction for DFAs over a shared alphabet,
used for intersection emptiness checks (verification) and multi-component composition.
"""

from __future__ import annotations
from collections import deque
from typing import Any, Dict, FrozenSet, Literal, Set, Tuple

from afco.automata.dfa import DFA


def product_dfa(
    m1: DFA,
    m2: DFA,
    mode: Literal["intersection", "union", "difference"] = "intersection"
) -> DFA:
    r"""Construct the synchronous product DFA of two DFAs over a shared alphabet.

    Only reachable product states are materialized.

    Modes:
        - "intersection": L(M1) AND L(M2) -> F = F1 x F2
        - "union": L(M1) OR L(M2) -> F = (F1 x Q2) U (Q1 x F2)
        - "difference": L(M1) \ L(M2) -> F = F1 x (Q2 \ F2)
    """
    shared_alphabet = m1.alphabet | m2.alphabet

    start_pair = (m1.start_state, m2.start_state)
    visited_states: Set[Tuple[Any, Any]] = {start_pair}
    transitions: Dict[Tuple[Tuple[Any, Any], Any], Tuple[Any, Any]] = {}
    accepting_states: Set[Tuple[Any, Any]] = set()

    queue: deque[Tuple[Any, Any]] = deque([start_pair])

    while queue:
        current_pair = queue.popleft()
        q1, q2 = current_pair

        # Determine acceptance based on mode
        in_f1 = q1 in m1.accepting_states
        in_f2 = q2 in m2.accepting_states

        if mode == "intersection" and (in_f1 and in_f2):
            accepting_states.add(current_pair)
        elif mode == "union" and (in_f1 or in_f2):
            accepting_states.add(current_pair)
        elif mode == "difference" and (in_f1 and not in_f2):
            accepting_states.add(current_pair)

        # Synchronous transition on shared alphabet
        for sym in shared_alphabet:
            nxt1 = m1.step(q1, sym)
            nxt2 = m2.step(q2, sym)

            # Both components must synchronize on defined transitions
            if nxt1 is not None and nxt2 is not None:
                next_pair = (nxt1, nxt2)
                transitions[(current_pair, sym)] = next_pair

                if next_pair not in visited_states:
                    visited_states.add(next_pair)
                    queue.append(next_pair)

    return DFA(
        states=frozenset(visited_states),
        alphabet=frozenset(shared_alphabet),
        transitions=transitions,
        start_state=start_pair,
        accepting_states=frozenset(accepting_states),
    )
