"""Tests for Product Automaton Construction."""

from afco.automata.dfa import DFA
from afco.automata.product import product_dfa


def test_product_intersection() -> None:
    """M1: strings over {'a', 'b'} with an even number of 'a's.
    M2: strings over {'a', 'b'} ending in 'b'.
    Intersection: strings with an even number of 'a's that end in 'b'.
    """
    # M1: even number of 'a's
    m1 = DFA(
        states=frozenset({"even", "odd"}),
        alphabet=frozenset({"a", "b"}),
        transitions={
            ("even", "a"): "odd",
            ("even", "b"): "even",
            ("odd", "a"): "even",
            ("odd", "b"): "odd",
        },
        start_state="even",
        accepting_states=frozenset({"even"}),
    )

    # M2: ends in 'b'
    m2 = DFA(
        states=frozenset({"init", "ended_b", "ended_a"}),
        alphabet=frozenset({"a", "b"}),
        transitions={
            ("init", "a"): "ended_a",
            ("init", "b"): "ended_b",
            ("ended_a", "a"): "ended_a",
            ("ended_a", "b"): "ended_b",
            ("ended_b", "a"): "ended_a",
            ("ended_b", "b"): "ended_b",
        },
        start_state="init",
        accepting_states=frozenset({"ended_b"}),
    )

    m_inter = product_dfa(m1, m2, mode="intersection")

    # "a", "a", "b": 2 'a's (even) and ends in 'b' -> accept
    assert m_inter.accepts(["a", "a", "b"]) is True

    # "a", "b": 1 'a' (odd), ends in 'b' -> reject (fails M1)
    assert m_inter.accepts(["a", "b"]) is False

    # "a", "a": 2 'a's (even), ends in 'a' -> reject (fails M2)
    assert m_inter.accepts(["a", "a"]) is False

    # "b", "b": 0 'a's (even), ends in 'b' -> accept
    assert m_inter.accepts(["b", "b"]) is True
