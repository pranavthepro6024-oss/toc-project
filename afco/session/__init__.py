"""AFCO Session Automaton Package.

Provides the 18-state, 28-symbol canonical DFA (M_S), runtime session tracking,
and diagnostic verification with synthesized repair paths.
"""

from afco.session.alphabet import (
    STATES,
    ALPHABET,
    START_STATE,
    ACCEPTING_STATES,
    PHYSICAL_SYMBOLS,
    POWER_SYMBOLS,
    AUTH_SYMBOLS,
    TELEMETRY_SYMBOLS,
    ADMIN_SYMBOLS,
    SessionState,
    SessionSymbol,
)
from afco.session.canonical import (
    build_canonical_session_dfa,
    build_canonical_transitions,
    get_canonical_dfa,
    verify_canonical_structure,
)
from afco.session.instance import (
    SessionInstance,
    VerificationVerdict,
    find_shortest_repair_path,
)
from afco.session.scenarios import (
    D1_CANONICAL_TRACE,
    D2_BILLING_SKIP_DIRECT_AUTH,
    D2_BILLING_SKIP_RESERVED,
    run_scenario_d1,
    run_scenario_d2,
)

__all__ = [
    "STATES",
    "ALPHABET",
    "START_STATE",
    "ACCEPTING_STATES",
    "PHYSICAL_SYMBOLS",
    "POWER_SYMBOLS",
    "AUTH_SYMBOLS",
    "TELEMETRY_SYMBOLS",
    "ADMIN_SYMBOLS",
    "SessionState",
    "SessionSymbol",
    "build_canonical_session_dfa",
    "build_canonical_transitions",
    "get_canonical_dfa",
    "verify_canonical_structure",
    "SessionInstance",
    "VerificationVerdict",
    "find_shortest_repair_path",
    "D1_CANONICAL_TRACE",
    "D2_BILLING_SKIP_DIRECT_AUTH",
    "D2_BILLING_SKIP_RESERVED",
    "run_scenario_d1",
    "run_scenario_d2",
]
