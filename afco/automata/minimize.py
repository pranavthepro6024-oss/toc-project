"""Hopcroft's DFA Minimization Algorithm.

Runs in O(|Sigma| * |Q| log |Q|) using partition refinement.
Adapted for partial transition functions (AFCO undefined-transition semantics)
via distinguished non-merging sink isolation.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Any, Dict, FrozenSet, List, Set, Tuple

from afco.automata.dfa import DFA
from afco.automata.reachability import forward_reachable


class _SinkToken:
    """Unique sentinel representing the temporary completion sink state."""
    def __repr__(self) -> str:
        return "<__PARTIAL_SINK__>"


_SINK = _SinkToken()


def minimize_dfa(dfa: DFA) -> DFA:
    """Compute the minimal equivalent DFA using Hopcroft's algorithm.

    Preserves partial transition semantics: undefined transitions in the original
    DFA remain undefined in the minimized DFA, rather than collapsing into an
    explicit sink state.
    """
    # 1. Prune unreachable states first
    reachable = forward_reachable(dfa)
    if not reachable:
        return dfa

    active_states = reachable
    active_accepting = dfa.accepting_states & active_states
    active_non_accepting = active_states - active_accepting

    # Edge cases:
    if not active_accepting:
        # All states reject: minimal DFA is a single non-accepting state
        rep = min(active_states, key=str)
        return DFA(
            states=frozenset({rep}),
            alphabet=dfa.alphabet,
            transitions={},
            start_state=rep,
            accepting_states=frozenset(),
        )

    # 2. Totalize transition function using distinguished _SINK
    total_states: Set[Any] = set(active_states) | {_SINK}
    total_transitions: Dict[Tuple[Any, Any], Any] = {}

    for q in active_states:
        for a in dfa.alphabet:
            tgt = dfa.step(q, a)
            if tgt is not None and tgt in active_states:
                total_transitions[(q, a)] = tgt
            else:
                total_transitions[(q, a)] = _SINK

    # Self-loops for _SINK
    for a in dfa.alphabet:
        total_transitions[(_SINK, a)] = _SINK

    # 3. Inverted index: predecessors[target, symbol] -> set of source states
    predecessors: Dict[Tuple[Any, Any], Set[Any]] = defaultdict(set)
    for (src, sym), tgt in total_transitions.items():
        predecessors[(tgt, sym)].add(src)

    # 4. Initial partition P:
    # F, Q \ F, and {_SINK} in its own block to prevent dead states from collapsing into _SINK
    sink_block = frozenset({_SINK})
    p_blocks: Set[FrozenSet[Any]] = {sink_block}
    if active_accepting:
        p_blocks.add(frozenset(active_accepting))
    if active_non_accepting:
        p_blocks.add(frozenset(active_non_accepting))

    # Worklist W: initialize with sink_block and active_accepting blocks
    # Including sink_block is critical for partial DFAs so that states with
    # undefined transitions on symbol a are immediately distinguished from states
    # with defined transitions to non-sink states on symbol a.
    w_blocks: Set[FrozenSet[Any]] = {sink_block}
    if active_accepting:
        w_blocks.add(frozenset(active_accepting))

    # Hopcroft refinement loop
    while w_blocks:
        A = w_blocks.pop()
        for sym in sorted(dfa.alphabet, key=str):
            # X = set of all states that lead to a state in A on symbol sym
            X: Set[Any] = set()
            for target_state in A:
                X.update(predecessors[(target_state, sym)])

            if not X:
                continue

            new_p: Set[FrozenSet[Any]] = set()
            for Y in p_blocks:
                intersect = Y & X
                difference = Y - X

                if intersect and difference:
                    new_p.add(intersect)
                    new_p.add(difference)

                    if Y in w_blocks:
                        w_blocks.remove(Y)
                        w_blocks.add(intersect)
                        w_blocks.add(difference)
                    else:
                        if len(intersect) <= len(difference):
                            w_blocks.add(intersect)
                        else:
                            w_blocks.add(difference)
                else:
                    new_p.add(Y)

            p_blocks = new_p

    # 5. Build minimal DFA
    # Filter out the block containing _SINK
    quotient_blocks = [b for b in p_blocks if _SINK not in b]

    # Map each original state to its block representative
    # We choose a deterministic representative name
    def block_rep(block: FrozenSet[Any]) -> Any:
        if len(block) == 1:
            return next(iter(block))
        # If multiple states collapsed, use sorted tuple or canonical composite string
        sorted_members = sorted(list(block), key=str)
        return "/".join(str(s) for s in sorted_members)

    state_to_rep: Dict[Any, Any] = {}
    rep_blocks: Set[Any] = set()
    new_accepting: Set[Any] = set()
    new_start: Any = None

    for block in quotient_blocks:
        rep = block_rep(block)
        rep_blocks.add(rep)
        for s in block:
            state_to_rep[s] = rep
        if dfa.start_state in block:
            new_start = rep
        if block & active_accepting:
            new_accepting.add(rep)

    if new_start is None:
        raise RuntimeError("Start state was lost during minimization.")

    # Reconstruct transitions without any transitions to _SINK
    new_transitions: Dict[Tuple[Any, Any], Any] = {}
    for block in quotient_blocks:
        rep = block_rep(block)
        # Any representative state in block has identical behavior
        sample_q = next(iter(block))
        for a in dfa.alphabet:
            target = total_transitions.get((sample_q, a))
            if target is not None and target is not _SINK:
                target_rep = state_to_rep[target]
                new_transitions[(rep, a)] = target_rep

    return DFA(
        states=frozenset(rep_blocks),
        alphabet=dfa.alphabet,
        transitions=new_transitions,
        start_state=new_start,
        accepting_states=frozenset(new_accepting),
    )
