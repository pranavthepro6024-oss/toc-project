"""Unit tests for the canonical session automaton M_S."""

from afco.automata.minimize import minimize_dfa
from afco.automata.reachability import forward_reachable, unreachable_states, trap_states
from afco.session.alphabet import FAULT_TERMINAL, IDLE, COMPLETED
from afco.session.canonical import (
    build_canonical_session_dfa,
    get_canonical_dfa,
    verify_canonical_structure,
)


def test_canonical_dfa_instantiation():
    """Verify that M_S satisfies all 5-tuple DFA invariants."""
    dfa = build_canonical_session_dfa()
    assert dfa.start_state == IDLE
    assert dfa.accepting_states == frozenset({COMPLETED})
    assert len(dfa.states) == 18
    assert len(dfa.alphabet) == 28


def test_structural_reachability():
    """Verify structural reachability: 0 unreachables, FAULT_TERMINAL as sole trap."""
    dfa = get_canonical_dfa()
    is_sound, unreachables, traps = verify_canonical_structure(dfa)

    assert is_sound, f"Structural soundness failed: unreachables={unreachables}, traps={traps}"
    assert len(unreachables) == 0, f"Found unreachable states: {unreachables}"
    assert traps == {FAULT_TERMINAL}, f"Expected only FAULT_TERMINAL trap, got: {traps}"
    assert len(forward_reachable(dfa)) == 18


def test_hopcroft_minimization_preserves_language():
    """Verify that Hopcroft minimization executes on M_S and preserves language acceptance."""
    dfa = get_canonical_dfa()
    min_dfa = minimize_dfa(dfa)

    # Minimized DFA should be valid and have <= states
    assert len(min_dfa.states) <= len(dfa.states)

    # Test sample words on both original and minimized DFA
    happy_word = [
        "reserve_req", "auth_req", "auth_ok", "plug_in", "lock_ok",
        "ev_ready", "precharge_ok", "power_start", "power_ramp_down",
        "power_stop", "unplug", "meter_final", "pay_ok", "session_close",
    ]
    assert dfa.accepts(happy_word) == min_dfa.accepts(happy_word) == True

    # Test rejected word
    bad_word = ["reserve_req", "power_start"]
    assert dfa.accepts(bad_word) == min_dfa.accepts(bad_word) == False
