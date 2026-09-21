"""Tests for forward reachability, unreachable states, and trap detection."""

from afco.automata.dfa import DFA
from afco.automata.reachability import forward_reachable, unreachable_states, backward_reachable, trap_states


def test_reachability_and_traps() -> None:
    """DFA with:
    - reachable path: q0 -> q1 -> q2 (accepting)
    - trap state: q1 -> q_trap (looping on itself, cannot reach q2)
    - unreachable state: q_orphan
    """
    dfa = DFA(
        states=frozenset({"q0", "q1", "q2", "q_trap", "q_orphan"}),
        alphabet=frozenset({"step", "fail", "loop"}),
        transitions={
            ("q0", "step"): "q1",
            ("q1", "step"): "q2",
            ("q1", "fail"): "q_trap",
            ("q_trap", "loop"): "q_trap",
            ("q_orphan", "step"): "q2",
        },
        start_state="q0",
        accepting_states=frozenset({"q2"}),
    )

    # Forward reachability
    reachable = forward_reachable(dfa)
    assert reachable == {"q0", "q1", "q2", "q_trap"}
    assert unreachable_states(dfa) == {"q_orphan"}

    # Backward reachability from F = {q2}
    can_reach_f = backward_reachable(dfa)
    assert can_reach_f == {"q0", "q1", "q2", "q_orphan"}

    # Trap states: reachable, but cannot reach F
    traps = trap_states(dfa)
    assert traps == {"q_trap"}
