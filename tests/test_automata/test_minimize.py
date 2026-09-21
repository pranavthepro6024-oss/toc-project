"""Tests for Hopcroft minimization including textbook benchmarks and hypothesis property tests."""

from hypothesis import given, strategies as st
from afco.automata.dfa import DFA
from afco.automata.minimize import minimize_dfa


def test_textbook_hopcroft_example() -> None:
    """Classic textbook example with equivalent states collapsing.

    Original States: {A, B, C, D, E, F} (6 states)
    Alphabet: {'0', '1'}
    Start: A
    Accepting: {C, D, E}
    Expected minimal states: exactly 3 states ({A, B}, {C, D, E}, {F}).
    """
    dfa = DFA(
        states=frozenset({"A", "B", "C", "D", "E", "F"}),
        alphabet=frozenset({"0", "1"}),
        transitions={
            ("A", "0"): "B",
            ("A", "1"): "C",
            ("B", "0"): "A",
            ("B", "1"): "D",
            ("C", "0"): "E",
            ("C", "1"): "F",
            ("D", "0"): "E",
            ("D", "1"): "F",
            ("E", "0"): "E",
            ("E", "1"): "F",
            ("F", "0"): "F",
            ("F", "1"): "F",
        },
        start_state="A",
        accepting_states=frozenset({"C", "D", "E"}),
    )

    min_dfa = minimize_dfa(dfa)

    # State count must reduce to 3
    assert len(min_dfa.states) == 3

    # Minimization must preserve language acceptance
    test_words = [
        [],
        ["0"],
        ["1"],
        ["0", "1"],
        ["1", "0"],
        ["1", "1"],
        ["0", "0", "1", "0"],
        ["0", "1", "1"],
    ]
    for w in test_words:
        assert dfa.accepts(w) == min_dfa.accepts(w), f"Mismatch on word {w}"


def test_partial_dfa_minimization() -> None:
    """Ensure partial transitions remain partial and do not collapse into sink state."""
    # A -> B on 'x', C -> D on 'x'. B and D accepting.
    # States A and C are equivalent; B and D are equivalent.
    dfa = DFA(
        states=frozenset({"A", "B", "C", "D"}),
        alphabet=frozenset({"x", "y"}),
        transitions={
            ("A", "x"): "B",
            ("C", "x"): "D",
        },
        start_state="A",
        accepting_states=frozenset({"B", "D"}),
    )

    min_dfa = minimize_dfa(dfa)
    # A is reachable; C is unreachable from start_state A.
    # So reachable states are {A, B} which cannot collapse further.
    assert len(min_dfa.states) == 2
    assert min_dfa.accepts(["x"]) is True
    assert min_dfa.accepts(["y"]) is False
    assert min_dfa.accepts(["x", "x"]) is False


@given(st.lists(st.sampled_from(["0", "1"]), max_size=30))
def test_hypothesis_language_equivalence(word: list[str]) -> None:
    """Property-based invariant: Hopcroft minimization preserves exact language recognition."""
    dfa = DFA(
        states=frozenset({"q0", "q1", "q2", "q3"}),
        alphabet=frozenset({"0", "1"}),
        transitions={
            ("q0", "0"): "q1",
            ("q0", "1"): "q2",
            ("q1", "0"): "q1",
            ("q1", "1"): "q3",
            ("q2", "0"): "q1",
            ("q2", "1"): "q3",
            ("q3", "0"): "q3",
            ("q3", "1"): "q3",
        },
        start_state="q0",
        accepting_states=frozenset({"q3"}),
    )
    min_dfa = minimize_dfa(dfa)
    assert dfa.accepts(word) == min_dfa.accepts(word)
