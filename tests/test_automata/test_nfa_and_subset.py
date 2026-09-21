"""Tests for NFA and Subset Construction."""

from afco.automata.nfa import NFA, EPSILON
from afco.automata.subset import subset_construction


def test_nfa_ends_in_abb() -> None:
    """NFA recognizing (a|b)*abb with nondeterministic guess at start."""
    nfa = NFA(
        states=frozenset({"0", "1", "2", "3"}),
        alphabet=frozenset({"a", "b"}),
        transitions={
            ("0", "a"): frozenset({"0", "1"}),
            ("0", "b"): frozenset({"0"}),
            ("1", "b"): frozenset({"2"}),
            ("2", "b"): frozenset({"3"}),
        },
        start_state="0",
        accepting_states=frozenset({"3"}),
    )

    # NFA acceptance tests
    assert nfa.accepts(["a", "b", "b"]) is True
    assert nfa.accepts(["b", "a", "a", "b", "b"]) is True
    assert nfa.accepts(["a", "b"]) is False
    assert nfa.accepts(["a", "b", "b", "a"]) is False

    # Subset construction to DFA
    dfa = subset_construction(nfa)

    # DFA acceptance matches NFA exactly
    assert dfa.accepts(["a", "b", "b"]) is True
    assert dfa.accepts(["b", "a", "a", "b", "b"]) is True
    assert dfa.accepts(["a", "b"]) is False
    assert dfa.accepts(["a", "b", "b", "a"]) is False


def test_nfa_with_epsilon_transitions() -> None:
    """NFA with epsilon transitions: recognizes 'a*' or 'b*'."""
    nfa = NFA(
        states=frozenset({"start", "A", "B"}),
        alphabet=frozenset({"a", "b"}),
        transitions={
            ("start", EPSILON): frozenset({"A", "B"}),
            ("A", "a"): frozenset({"A"}),
            ("B", "b"): frozenset({"B"}),
        },
        start_state="start",
        accepting_states=frozenset({"A", "B"}),
    )

    closure = nfa.epsilon_closure({"start"})
    assert closure == frozenset({"start", "A", "B"})

    dfa = subset_construction(nfa)
    assert dfa.accepts([]) is True
    assert dfa.accepts(["a", "a", "a"]) is True
    assert dfa.accepts(["b", "b"]) is True
    assert dfa.accepts(["a", "b"]) is False
