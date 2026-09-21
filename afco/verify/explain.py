"""Counterexample extraction and repair path synthesis for the verification layer.

Provides:
- extract_counterexample: BFS parent-pointer traceback through the product automaton
  to find the shortest word in L(M_S) ∩ L(M_{unsafe}).
- synthesize_repair_path: BFS from a failing M_S state to the nearest safe
  accepting state (identical to the instance-level BFS, but operating
  directly on a DFA).

These functions are the *explainability* core of the checker.
"""

from __future__ import annotations
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

from afco.automata.dfa import DFA


def extract_counterexample(product: DFA) -> Optional[List[str]]:
    """BFS over the product DFA to extract the shortest forbidden trace.

    Performs a Breadth-First Search from the product start state, recording
    parent pointers at every visited state.  The moment an accepting (forbidden)
    state is discovered, the shortest path is reconstructed by walking the
    parent pointer chain backwards.

    Args:
        product: The synchronous product DFA (M_S × M_{U,k}).  Its accepting
                 states are exactly the jointly-accepting pairs that prove
                 L(M_S) ∩ L(M_U) ≠ ∅.

    Returns:
        The shortest list of symbols forming a counterexample, or None if
        the product accepting set is empty (property holds).
    """
    if not product.accepting_states:
        return None

    start = product.start_state

    # Guard: is the start state itself accepting? (degenerate violation at step 0)
    if start in product.accepting_states:
        return []

    # BFS with parent pointers: state -> (parent_state, symbol_taken)
    parent: Dict[Any, Optional[Tuple[Any, str]]] = {start: None}
    queue: deque[Any] = deque([start])

    while queue:
        current = queue.popleft()

        for sym in sorted(product.alphabet, key=str):
            nxt = product.step(current, sym)
            if nxt is None or nxt in parent:
                continue

            parent[nxt] = (current, str(sym))
            queue.append(nxt)

            if nxt in product.accepting_states:
                # Reconstruct path from start → nxt
                return _reconstruct_path(parent, nxt)

    return None  # No counterexample found — property holds


def _reconstruct_path(
    parent: Dict[Any, Optional[Tuple[Any, str]]],
    goal: Any,
) -> List[str]:
    """Walk parent pointers backwards from goal to start, reversing to get forward path."""
    path: List[str] = []
    node = goal
    while parent[node] is not None:
        prev, sym = parent[node]  # type: ignore[misc]
        path.append(sym)
        node = prev
    path.reverse()
    return path


def synthesize_repair_path(dfa: DFA, from_state: Any) -> Optional[List[str]]:
    """Compute the shortest symbol sequence from from_state to any accepting state.

    Uses BFS over the M_S transition graph.  Returns an empty list [] if
    from_state is already accepting.  Returns None if no accepting state is
    reachable (e.g. from FAULT_TERMINAL).

    Args:
        dfa: The session DFA M_S (or any DFA whose accepting states are safe targets).
        from_state: The state from which to search for recovery.

    Returns:
        A list of symbols forming the shortest repair path, or None.
    """
    if from_state in dfa.accepting_states:
        return []

    # BFS: track (current_state, path_so_far)
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
