"""Unit tests for the canonical session alphabet and state taxonomy."""

from afco.session.alphabet import (
    STATES,
    ALPHABET,
    PHYSICAL_SYMBOLS,
    POWER_SYMBOLS,
    AUTH_SYMBOLS,
    TELEMETRY_SYMBOLS,
    ADMIN_SYMBOLS,
    START_STATE,
    ACCEPTING_STATES,
    SessionState,
    SessionSymbol,
    IDLE,
    COMPLETED,
    FAULT_TERMINAL,
)


def test_alphabet_size_and_partitions():
    """Verify that Sigma_S contains exactly 28 formal symbols across 5 domains."""
    assert len(ALPHABET) == 28
    assert len(PHYSICAL_SYMBOLS) == 8
    assert len(POWER_SYMBOLS) == 6
    assert len(AUTH_SYMBOLS) == 6
    assert len(TELEMETRY_SYMBOLS) == 5
    assert len(ADMIN_SYMBOLS) == 3

    # All partitions are pairwise disjoint
    partitions = [
        PHYSICAL_SYMBOLS,
        POWER_SYMBOLS,
        AUTH_SYMBOLS,
        TELEMETRY_SYMBOLS,
        ADMIN_SYMBOLS,
    ]
    total_elements = sum(len(p) for p in partitions)
    union_elements = len(set.union(*[set(p) for p in partitions]))
    assert total_elements == 28
    assert union_elements == 28


def test_state_taxonomy_size_and_special_states():
    """Verify that Q_S contains exactly 18 states with IDLE as start and COMPLETED as accepting."""
    assert len(STATES) == 18
    assert START_STATE == IDLE
    assert ACCEPTING_STATES == frozenset({COMPLETED})
    assert FAULT_TERMINAL in STATES
    assert IDLE in STATES


def test_enum_and_string_consistency():
    """Verify that Enums and string constants are identical."""
    for state in SessionState:
        assert state.value in STATES
    for sym in SessionSymbol:
        assert sym.value in ALPHABET
