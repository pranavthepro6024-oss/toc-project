"""Subset Construction (Powerset Determinization): NFA -> DFA.

Converts a nondeterministic finite automaton (with epsilon transitions)
into an equivalent deterministic finite automaton.
"""

from __future__ import annotations
from collections import deque
from typing import Any, Dict, FrozenSet, Set, Tuple

from afco.automata.dfa import DFA
from afco.automata.nfa import NFA


def subset_construction(nfa: NFA) -> DFA:
    """Convert an NFA to an equivalent DFA using subset construction.

    Each state in the resulting DFA corresponds to a frozenset of NFA states.
    Only reachable subset states are materialized.
    """
    initial_subset: FrozenSet[Any] = nfa.epsilon_closure([nfa.start_state])

    dfa_states: Set[FrozenSet[Any]] = {initial_subset}
    dfa_transitions: Dict[Tuple[FrozenSet[Any], Any], FrozenSet[Any]] = {}
    dfa_accepting: Set[FrozenSet[Any]] = set()

    queue: deque[FrozenSet[Any]] = deque([initial_subset])

    while queue:
        current_subset = queue.popleft()

        # Mark accepting if any NFA state in the subset is accepting
        if current_subset & nfa.accepting_states:
            dfa_accepting.add(current_subset)

        for sym in sorted(list(nfa.alphabet), key=str):
            target_subset = nfa.step(current_subset, sym)
            if not target_subset:
                continue  # Keep partial transition semantics (no sink state)

            dfa_transitions[(current_subset, sym)] = target_subset

            if target_subset not in dfa_states:
                dfa_states.add(target_subset)
                queue.append(target_subset)

    return DFA(
        states=frozenset(dfa_states),
        alphabet=nfa.alphabet,
        transitions=dfa_transitions,
        start_state=initial_subset,
        accepting_states=frozenset(dfa_accepting),
    )
