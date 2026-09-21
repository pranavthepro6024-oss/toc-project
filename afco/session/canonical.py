"""Canonical Session Automaton (M_S) definition and factory.

Implements the formal 18-state, 28-symbol DFA (Q_S, Sigma_S, delta_S, q0, F_S).
Includes complete transition specification and formal reachability verification.
"""

from __future__ import annotations
from typing import Dict, Optional, Set, Tuple

from afco.automata.dfa import DFA
from afco.automata.reachability import unreachable_states, trap_states
from afco.session.alphabet import (
    STATES,
    ALPHABET,
    START_STATE,
    ACCEPTING_STATES,
    IDLE,
    RESERVED,
    AUTH_PENDING,
    AUTHORIZED,
    CABLE_DETECTED,
    EV_CONNECTED,
    PRECHARGE,
    CHARGING,
    PAUSED_DISPATCH,
    SUSPENDED_EV,
    SUSPENDED_EVSE,
    RAMP_DOWN,
    ISOLATING,
    UNLOCKED,
    UNPLUGGED,
    BILLING_PENDING,
    COMPLETED,
    FAULT_TERMINAL,
    PLUG_IN,
    UNPLUG,
    LOCK_OK,
    LOCK_FAIL,
    UNLOCK_REQ,
    UNLOCK_OK,
    CABLE_FAULT,
    PILOT_LOST,
    PRECHARGE_OK,
    POWER_START,
    POWER_RAMP_DOWN,
    POWER_STOP,
    CONTACTORS_OPEN,
    OVERCURRENT_TRIP,
    RESERVE_REQ,
    AUTH_REQ,
    AUTH_OK,
    AUTH_FAIL,
    PAY_OK,
    PAY_FAIL,
    METER_TICK,
    METER_FINAL,
    EV_READY,
    EV_STOP,
    GRID_CURTAIL,
    E_STOP,
    RESET_CMD,
    SESSION_CLOSE,
)


def build_canonical_transitions() -> Dict[Tuple[str, str], str]:
    """Construct the complete delta_S transition function for M_S."""
    delta: Dict[Tuple[str, str], str] = {}

    # 1. IDLE (Quiescent start state)
    delta[(IDLE, RESERVE_REQ)] = RESERVED
    delta[(IDLE, AUTH_REQ)] = AUTH_PENDING
    delta[(IDLE, PLUG_IN)] = CABLE_DETECTED
    delta[(IDLE, RESET_CMD)] = IDLE

    # 2. RESERVED (Allocated by fleet manager)
    delta[(RESERVED, AUTH_REQ)] = AUTH_PENDING
    delta[(RESERVED, PLUG_IN)] = CABLE_DETECTED
    delta[(RESERVED, SESSION_CLOSE)] = IDLE
    delta[(RESERVED, RESET_CMD)] = IDLE

    # 3. AUTH_PENDING (Validating fleet credential)
    delta[(AUTH_PENDING, AUTH_OK)] = AUTHORIZED
    delta[(AUTH_PENDING, AUTH_FAIL)] = IDLE
    delta[(AUTH_PENDING, SESSION_CLOSE)] = IDLE
    delta[(AUTH_PENDING, RESET_CMD)] = IDLE

    # 4. AUTHORIZED (Credential accepted; awaiting physical connection)
    delta[(AUTHORIZED, PLUG_IN)] = CABLE_DETECTED
    delta[(AUTHORIZED, SESSION_CLOSE)] = IDLE
    delta[(AUTHORIZED, RESET_CMD)] = IDLE

    # 5. CABLE_DETECTED (Cable plugged in; pilot signal detected)
    delta[(CABLE_DETECTED, LOCK_OK)] = EV_CONNECTED
    delta[(CABLE_DETECTED, LOCK_FAIL)] = FAULT_TERMINAL
    delta[(CABLE_DETECTED, UNPLUG)] = IDLE
    delta[(CABLE_DETECTED, PILOT_LOST)] = IDLE
    delta[(CABLE_DETECTED, CABLE_FAULT)] = FAULT_TERMINAL
    delta[(CABLE_DETECTED, AUTH_REQ)] = AUTH_PENDING

    # 6. EV_CONNECTED (Connector locked mechanically; isolation test)
    delta[(EV_CONNECTED, EV_READY)] = PRECHARGE
    delta[(EV_CONNECTED, UNLOCK_REQ)] = UNLOCKED
    delta[(EV_CONNECTED, CABLE_FAULT)] = FAULT_TERMINAL
    delta[(EV_CONNECTED, PILOT_LOST)] = FAULT_TERMINAL
    delta[(EV_CONNECTED, E_STOP)] = FAULT_TERMINAL

    # 7. PRECHARGE (Contactor closed; bus pre-charging)
    delta[(PRECHARGE, PRECHARGE_OK)] = PRECHARGE
    delta[(PRECHARGE, POWER_START)] = CHARGING
    delta[(PRECHARGE, POWER_STOP)] = ISOLATING
    delta[(PRECHARGE, CABLE_FAULT)] = FAULT_TERMINAL
    delta[(PRECHARGE, OVERCURRENT_TRIP)] = FAULT_TERMINAL
    delta[(PRECHARGE, E_STOP)] = FAULT_TERMINAL

    # 8. CHARGING (Active energy transfer; telemetry metering)
    delta[(CHARGING, METER_TICK)] = CHARGING
    delta[(CHARGING, POWER_START)] = CHARGING  # Idempotent power level adjustments
    delta[(CHARGING, GRID_CURTAIL)] = PAUSED_DISPATCH
    delta[(CHARGING, EV_STOP)] = SUSPENDED_EV
    delta[(CHARGING, POWER_RAMP_DOWN)] = RAMP_DOWN
    delta[(CHARGING, POWER_STOP)] = ISOLATING
    delta[(CHARGING, OVERCURRENT_TRIP)] = FAULT_TERMINAL
    delta[(CHARGING, CABLE_FAULT)] = FAULT_TERMINAL
    delta[(CHARGING, PILOT_LOST)] = FAULT_TERMINAL
    delta[(CHARGING, E_STOP)] = FAULT_TERMINAL

    # 9. PAUSED_DISPATCH (Throttled by grid curtailment / site ceiling)
    delta[(PAUSED_DISPATCH, POWER_START)] = CHARGING
    delta[(PAUSED_DISPATCH, GRID_CURTAIL)] = SUSPENDED_EVSE
    delta[(PAUSED_DISPATCH, METER_TICK)] = PAUSED_DISPATCH
    delta[(PAUSED_DISPATCH, POWER_RAMP_DOWN)] = RAMP_DOWN
    delta[(PAUSED_DISPATCH, POWER_STOP)] = ISOLATING
    delta[(PAUSED_DISPATCH, E_STOP)] = FAULT_TERMINAL

    # 10. SUSPENDED_EV (Energy transfer suspended by vehicle BMS)
    delta[(SUSPENDED_EV, EV_READY)] = CHARGING
    delta[(SUSPENDED_EV, POWER_RAMP_DOWN)] = RAMP_DOWN
    delta[(SUSPENDED_EV, POWER_STOP)] = ISOLATING
    delta[(SUSPENDED_EV, E_STOP)] = FAULT_TERMINAL

    # 11. SUSPENDED_EVSE (Suspended by station control policy)
    delta[(SUSPENDED_EVSE, POWER_START)] = CHARGING
    delta[(SUSPENDED_EVSE, POWER_RAMP_DOWN)] = RAMP_DOWN
    delta[(SUSPENDED_EVSE, POWER_STOP)] = ISOLATING
    delta[(SUSPENDED_EVSE, E_STOP)] = FAULT_TERMINAL

    # 12. RAMP_DOWN (Graceful current reduction to zero)
    delta[(RAMP_DOWN, POWER_STOP)] = ISOLATING
    delta[(RAMP_DOWN, OVERCURRENT_TRIP)] = FAULT_TERMINAL
    delta[(RAMP_DOWN, E_STOP)] = FAULT_TERMINAL

    # 13. ISOLATING (Contactors opening; residual discharge)
    delta[(ISOLATING, CONTACTORS_OPEN)] = UNLOCKED
    delta[(ISOLATING, UNLOCK_OK)] = UNLOCKED
    delta[(ISOLATING, UNLOCK_REQ)] = ISOLATING
    delta[(ISOLATING, UNPLUG)] = UNPLUGGED
    delta[(ISOLATING, E_STOP)] = FAULT_TERMINAL

    # 14. UNLOCKED (Lock retracted; safe for operator extraction)
    delta[(UNLOCKED, UNPLUG)] = UNPLUGGED
    delta[(UNLOCKED, LOCK_OK)] = EV_CONNECTED
    delta[(UNLOCKED, PLUG_IN)] = CABLE_DETECTED

    # 15. UNPLUGGED (Cable holstered; awaiting settlement)
    delta[(UNPLUGGED, METER_FINAL)] = BILLING_PENDING
    delta[(UNPLUGGED, PAY_OK)] = COMPLETED

    # 16. BILLING_PENDING (Tariff calculation; invoice gateway)
    delta[(BILLING_PENDING, PAY_OK)] = COMPLETED
    delta[(BILLING_PENDING, PAY_FAIL)] = BILLING_PENDING  # Retry hold

    # 17. COMPLETED (Accepting state F_S)
    delta[(COMPLETED, SESSION_CLOSE)] = COMPLETED
    delta[(COMPLETED, RESET_CMD)] = IDLE

    # 18. FAULT_TERMINAL (Intentional trap / dead state)
    # Zero outgoing transitions by formal definition: delta(FAULT_TERMINAL, a) = bot

    return delta


def build_canonical_session_dfa() -> DFA:
    """Instantiate the 5-tuple canonical session DFA M_S."""
    transitions = build_canonical_transitions()
    return DFA(
        states=STATES,
        alphabet=ALPHABET,
        transitions=transitions,
        start_state=START_STATE,
        accepting_states=ACCEPTING_STATES,
    )


_CANONICAL_DFA_INSTANCE: Optional[DFA] = None


def get_canonical_dfa() -> DFA:
    """Return the cached canonical DFA singleton."""
    global _CANONICAL_DFA_INSTANCE
    if _CANONICAL_DFA_INSTANCE is None:
        _CANONICAL_DFA_INSTANCE = build_canonical_session_dfa()
    return _CANONICAL_DFA_INSTANCE


def verify_canonical_structure(dfa: Optional[DFA] = None) -> Tuple[bool, Set[str], Set[str]]:
    """Verify structural reachability of M_S:

    1. Zero unreachable states from IDLE (unreachable_states == set()).
    2. FAULT_TERMINAL is the unique dead-end trap state (trap_states == {FAULT_TERMINAL}).

    Returns:
        (is_sound, unreachables, traps)
    """
    target_dfa = dfa or get_canonical_dfa()
    unreachables = unreachable_states(target_dfa)
    traps = trap_states(target_dfa)

    is_sound = (len(unreachables) == 0) and (traps == {FAULT_TERMINAL})
    return is_sound, unreachables, traps
