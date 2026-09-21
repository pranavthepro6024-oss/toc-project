"""Reachability analysis for Finite State Automata.

Provides forward reachability (orphan state discovery),
backward co-reachability (accepting path existence),
and trap / dead-end state detection.
"""

from __future__ import annotations
from collections import defaultdict, deque
from typing import Any, Dict, List, Set

from afco.automata.dfa import DFA


def forward_reachable(dfa: DFA) -> Set[Any]:
    """Compute the set of all states reachable from the start state q0."""
    visited: Set[Any] = {dfa.start_state}
    queue: deque[Any] = deque([dfa.start_state])

    while queue:
        state = queue.popleft()
        for sym in dfa.alphabet:
            nxt = dfa.step(state, sym)
            if nxt is not None and nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)

    return visited


def unreachable_states(dfa: DFA) -> Set[Any]:
    """Find states in Q that cannot be reached from the start state."""
    return dfa.states - forward_reachable(dfa)


def backward_reachable(dfa: DFA) -> Set[Any]:
    """Compute the set of states from which at least one accepting state is reachable."""
    # Build reverse transition graph: target -> list of (source, symbol)
    reverse_graph: Dict[Any, List[Any]] = defaultdict(list)
    for (src, _), tgt in dfa.transitions.items():
        reverse_graph[tgt].append(src)

    visited: Set[Any] = set(dfa.accepting_states)
    queue: deque[Any] = deque(dfa.accepting_states)

    while queue:
        state = queue.popleft()
        for predecessor in reverse_graph[state]:
            if predecessor not in visited:
                visited.add(predecessor)
                queue.append(predecessor)

    return visited


def trap_states(dfa: DFA) -> Set[Any]:
    """Identify trap / dead states.

    A trap state is reachable from q0, but cannot reach any accepting state in F.
    In AFCO, FAULT_TERMINAL is an intentional trap state.
    """
    reachable = forward_reachable(dfa)
    can_reach_final = backward_reachable(dfa)
    return reachable - can_reach_final
