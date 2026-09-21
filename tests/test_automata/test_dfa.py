"""Tests for DFA and diagnostic trace functionality."""

import pytest
from afco.automata.dfa import DFA, TraceResult


@pytest.fixture
def mod3_binary_counter() -> DFA:
    """A total DFA recognizing binary strings representing integers divisible by 3.

    Alphabet: {'0', '1'}
    States: {q0, q1, q2} representing remainder modulo 3.
    Start state: q0
    Accepting state: {q0}
    """
    return DFA(
        states=frozenset({"q0", "q1", "q2"}),
        alphabet=frozenset({"0", "1"}),
        transitions={
            ("q0", "0"): "q0",
            ("q0", "1"): "q1",
            ("q1", "0"): "q2",
            ("q1", "1"): "q0",
            ("q2", "0"): "q1",
            ("q2", "1"): "q2",
        },
        start_state="q0",
        accepting_states=frozenset({"q0"}),
    )


@pytest.fixture
def partial_dfa() -> DFA:
    """A partial DFA over {'a', 'b', 'c'} where undefined transitions mean immediate rejection."""
    return DFA(
        states=frozenset({"S0", "S1", "S2"}),
        alphabet=frozenset({"a", "b", "c"}),
        transitions={
            ("S0", "a"): "S1",
            ("S1", "b"): "S2",
        },
        start_state="S0",
        accepting_states=frozenset({"S2"}),
    )


def test_mod3_acceptance(mod3_binary_counter: DFA) -> None:
    # 0 in decimal is 0 (0 % 3 == 0) -> accept
    assert mod3_binary_counter.accepts(["0"]) is True
    # 3 in decimal is "1", "1" -> accept
    assert mod3_binary_counter.accepts(["1", "1"]) is True
    # 6 in decimal is "1", "1", "0" -> accept
    assert mod3_binary_counter.accepts(["1", "1", "0"]) is True
    # 5 in decimal is "1", "0", "1" (5 % 3 != 0) -> reject
    assert mod3_binary_counter.accepts(["1", "0", "1"]) is False
    # 7 in decimal is "1", "1", "1" (7 % 3 != 0) -> reject
    assert mod3_binary_counter.accepts(["1", "1", "1"]) is False


def test_mod3_trace_acceptance(mod3_binary_counter: DFA) -> None:
    res = mod3_binary_counter.trace(["1", "1", "0"])
    assert res.accepted is True
    assert res.path == ["q0", "q1", "q0", "q0"]
    assert res.failure_index is None
    assert res.terminal_state == "q0"


def test_partial_dfa_rejection_trace(partial_dfa: DFA) -> None:
    # Valid word: ['a', 'b']
    valid_res = partial_dfa.trace(["a", "b"])
    assert valid_res.accepted is True
    assert valid_res.path == ["S0", "S1", "S2"]

    # Invalid word: ['a', 'c'] -> rejected at step 1
    bad_res = partial_dfa.trace(["a", "c"])
    assert bad_res.accepted is False
    assert bad_res.failure_index == 1
    assert bad_res.rejected_symbol == "c"
    assert bad_res.terminal_state == "S1"
    assert bad_res.admissible_symbols == {"b"}
    assert "REJECTED at step 1" in bad_res.explain()


def test_invalid_start_or_accepting_states() -> None:
    with pytest.raises(ValueError, match="Start state 'INVALID' is not in states Q"):
        DFA(
            states=frozenset({"A"}),
            alphabet=frozenset({"x"}),
            transitions={},
            start_state="INVALID",
            accepting_states=frozenset({"A"}),
        )

    with pytest.raises(ValueError, match="Accepting states contains elements not in Q"):
        DFA(
            states=frozenset({"A"}),
            alphabet=frozenset({"x"}),
            transitions={},
            start_state="A",
            accepting_states=frozenset({"B"}),
        )
