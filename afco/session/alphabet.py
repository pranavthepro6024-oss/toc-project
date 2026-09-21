"""Formal alphabet and state taxonomy for the Canonical Session Automaton (M_S).

Defines the 18 lifecycle states (Q_S) and 28 formal input symbols (Sigma_S)
categorized across hardware, power, authorization, telemetry, and administrative domains.
"""

from __future__ import annotations
from enum import Enum
from typing import FrozenSet


class SessionState(str, Enum):
    """The 18 lifecycle states (Q_S) of the canonical session automaton."""
    # Quiescent & Allocated
    IDLE = "IDLE"
    RESERVED = "RESERVED"

    # Handshake & Authentication
    AUTH_PENDING = "AUTH_PENDING"
    AUTHORIZED = "AUTHORIZED"

    # Physical Coupling
    CABLE_DETECTED = "CABLE_DETECTED"
    EV_CONNECTED = "EV_CONNECTED"

    # Power Preparation & Active Transfer
    PRECHARGE = "PRECHARGE"
    CHARGING = "CHARGING"

    # Throttled & Suspended Operations
    PAUSED_DISPATCH = "PAUSED_DISPATCH"
    SUSPENDED_EV = "SUSPENDED_EV"
    SUSPENDED_EVSE = "SUSPENDED_EVSE"

    # Termination & Isolation
    RAMP_DOWN = "RAMP_DOWN"
    ISOLATING = "ISOLATING"

    # Physical Decoupling
    UNLOCKED = "UNLOCKED"
    UNPLUGGED = "UNPLUGGED"

    # Settlement & Acceptance
    BILLING_PENDING = "BILLING_PENDING"
    COMPLETED = "COMPLETED"

    # Dead / Trap State
    FAULT_TERMINAL = "FAULT_TERMINAL"


class SessionSymbol(str, Enum):
    """The 28 formal input symbols (Sigma_S) of the canonical session automaton."""
    # Physical & Hardware Events (8)
    PLUG_IN = "plug_in"
    UNPLUG = "unplug"
    LOCK_OK = "lock_ok"
    LOCK_FAIL = "lock_fail"
    UNLOCK_REQ = "unlock_req"
    UNLOCK_OK = "unlock_ok"
    CABLE_FAULT = "cable_fault"
    PILOT_LOST = "pilot_lost"

    # Power & Contactor Events (6)
    PRECHARGE_OK = "precharge_ok"
    POWER_START = "power_start"
    POWER_RAMP_DOWN = "power_ramp_down"
    POWER_STOP = "power_stop"
    CONTACTORS_OPEN = "contactors_open"
    OVERCURRENT_TRIP = "overcurrent_trip"

    # Authorization & Commercial Events (6)
    RESERVE_REQ = "reserve_req"
    AUTH_REQ = "auth_req"
    AUTH_OK = "auth_ok"
    AUTH_FAIL = "auth_fail"
    PAY_OK = "pay_ok"
    PAY_FAIL = "pay_fail"

    # Telemetry & Management Events (5)
    METER_TICK = "meter_tick"
    METER_FINAL = "meter_final"
    EV_READY = "ev_ready"
    EV_STOP = "ev_stop"
    GRID_CURTAIL = "grid_curtail"

    # Administrative & Emergency Events (3)
    E_STOP = "e_stop"
    RESET_CMD = "reset_cmd"
    SESSION_CLOSE = "session_close"


# Convenient string constants matching SessionState
IDLE = SessionState.IDLE.value
RESERVED = SessionState.RESERVED.value
AUTH_PENDING = SessionState.AUTH_PENDING.value
AUTHORIZED = SessionState.AUTHORIZED.value
CABLE_DETECTED = SessionState.CABLE_DETECTED.value
EV_CONNECTED = SessionState.EV_CONNECTED.value
PRECHARGE = SessionState.PRECHARGE.value
CHARGING = SessionState.CHARGING.value
PAUSED_DISPATCH = SessionState.PAUSED_DISPATCH.value
SUSPENDED_EV = SessionState.SUSPENDED_EV.value
SUSPENDED_EVSE = SessionState.SUSPENDED_EVSE.value
RAMP_DOWN = SessionState.RAMP_DOWN.value
ISOLATING = SessionState.ISOLATING.value
UNLOCKED = SessionState.UNLOCKED.value
UNPLUGGED = SessionState.UNPLUGGED.value
BILLING_PENDING = SessionState.BILLING_PENDING.value
COMPLETED = SessionState.COMPLETED.value
FAULT_TERMINAL = SessionState.FAULT_TERMINAL.value

# Convenient string constants matching SessionSymbol
PLUG_IN = SessionSymbol.PLUG_IN.value
UNPLUG = SessionSymbol.UNPLUG.value
LOCK_OK = SessionSymbol.LOCK_OK.value
LOCK_FAIL = SessionSymbol.LOCK_FAIL.value
UNLOCK_REQ = SessionSymbol.UNLOCK_REQ.value
UNLOCK_OK = SessionSymbol.UNLOCK_OK.value
CABLE_FAULT = SessionSymbol.CABLE_FAULT.value
PILOT_LOST = SessionSymbol.PILOT_LOST.value

PRECHARGE_OK = SessionSymbol.PRECHARGE_OK.value
POWER_START = SessionSymbol.POWER_START.value
POWER_RAMP_DOWN = SessionSymbol.POWER_RAMP_DOWN.value
POWER_STOP = SessionSymbol.POWER_STOP.value
CONTACTORS_OPEN = SessionSymbol.CONTACTORS_OPEN.value
OVERCURRENT_TRIP = SessionSymbol.OVERCURRENT_TRIP.value

RESERVE_REQ = SessionSymbol.RESERVE_REQ.value
RESERVE = RESERVE_REQ  # Convenience alias for scenario word notation
AUTH_REQ = SessionSymbol.AUTH_REQ.value
AUTH_OK = SessionSymbol.AUTH_OK.value
AUTH_FAIL = SessionSymbol.AUTH_FAIL.value
PAY_OK = SessionSymbol.PAY_OK.value
PAY_FAIL = SessionSymbol.PAY_FAIL.value

METER_TICK = SessionSymbol.METER_TICK.value
METER_FINAL = SessionSymbol.METER_FINAL.value
EV_READY = SessionSymbol.EV_READY.value
EV_STOP = SessionSymbol.EV_STOP.value
GRID_CURTAIL = SessionSymbol.GRID_CURTAIL.value

E_STOP = SessionSymbol.E_STOP.value
RESET_CMD = SessionSymbol.RESET_CMD.value
SESSION_CLOSE = SessionSymbol.SESSION_CLOSE.value

# Categorized Symbol Groups
PHYSICAL_SYMBOLS: FrozenSet[str] = frozenset({
    PLUG_IN, UNPLUG, LOCK_OK, LOCK_FAIL, UNLOCK_REQ, UNLOCK_OK, CABLE_FAULT, PILOT_LOST,
})

POWER_SYMBOLS: FrozenSet[str] = frozenset({
    PRECHARGE_OK, POWER_START, POWER_RAMP_DOWN, POWER_STOP, CONTACTORS_OPEN, OVERCURRENT_TRIP,
})

AUTH_SYMBOLS: FrozenSet[str] = frozenset({
    RESERVE_REQ, AUTH_REQ, AUTH_OK, AUTH_FAIL, PAY_OK, PAY_FAIL,
})

TELEMETRY_SYMBOLS: FrozenSet[str] = frozenset({
    METER_TICK, METER_FINAL, EV_READY, EV_STOP, GRID_CURTAIL,
})

ADMIN_SYMBOLS: FrozenSet[str] = frozenset({
    E_STOP, RESET_CMD, SESSION_CLOSE,
})

# Complete Formal Alphabet Sigma_S (|Sigma| = 28)
ALPHABET: FrozenSet[str] = frozenset(
    PHYSICAL_SYMBOLS | POWER_SYMBOLS | AUTH_SYMBOLS | TELEMETRY_SYMBOLS | ADMIN_SYMBOLS
)

# Complete Formal States Q_S (|Q| = 18)
STATES: FrozenSet[str] = frozenset({
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
})

# Start and Accepting States
START_STATE: str = IDLE
ACCEPTING_STATES: FrozenSet[str] = frozenset({COMPLETED})

# Structural Invariant Assertions
assert len(STATES) == 18, f"Expected 18 states, got {len(STATES)}"
assert len(ALPHABET) == 28, f"Expected 28 symbols, got {len(ALPHABET)}"
assert len(PHYSICAL_SYMBOLS) == 8, f"Expected 8 physical symbols, got {len(PHYSICAL_SYMBOLS)}"
assert len(POWER_SYMBOLS) == 6, f"Expected 6 power symbols, got {len(POWER_SYMBOLS)}"
assert len(AUTH_SYMBOLS) == 6, f"Expected 6 auth symbols, got {len(AUTH_SYMBOLS)}"
assert len(TELEMETRY_SYMBOLS) == 5, f"Expected 5 telemetry symbols, got {len(TELEMETRY_SYMBOLS)}"
assert len(ADMIN_SYMBOLS) == 3, f"Expected 3 admin symbols, got {len(ADMIN_SYMBOLS)}"
