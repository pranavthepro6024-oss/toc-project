"""Executable specifications for Scenarios D1 (Happy Path) and D2 (Billing-Skip Rejection).

Demonstrates regular word acceptance (D1) and explainable rejection via undefined
transitions with failure index, admissible alphabet, and repair path synthesis (D2).
"""

from __future__ import annotations
from typing import List, Tuple

from afco.session.alphabet import (
    AUTH_OK,
    AUTH_REQ,
    EV_READY,
    LOCK_OK,
    METER_FINAL,
    PAY_OK,
    PLUG_IN,
    POWER_RAMP_DOWN,
    POWER_START,
    POWER_STOP,
    PRECHARGE_OK,
    RESERVE_REQ,
    SESSION_CLOSE,
    UNPLUG,
)
from afco.session.instance import SessionInstance, VerificationVerdict


# D1: Canonical Happy Path word
D1_CANONICAL_TRACE: List[str] = [
    RESERVE_REQ,       # 0: IDLE -> RESERVED
    AUTH_REQ,          # 1: RESERVED -> AUTH_PENDING
    AUTH_OK,           # 2: AUTH_PENDING -> AUTHORIZED
    PLUG_IN,           # 3: AUTHORIZED -> CABLE_DETECTED
    LOCK_OK,           # 4: CABLE_DETECTED -> EV_CONNECTED
    EV_READY,          # 5: EV_CONNECTED -> PRECHARGE
    PRECHARGE_OK,      # 6: PRECHARGE -> PRECHARGE
    POWER_START,       # 7: PRECHARGE -> CHARGING
    POWER_RAMP_DOWN,   # 8: CHARGING -> RAMP_DOWN
    POWER_STOP,        # 9: RAMP_DOWN -> ISOLATING
    UNPLUG,            # 10: ISOLATING -> UNPLUGGED
    METER_FINAL,       # 11: UNPLUGGED -> BILLING_PENDING
    PAY_OK,            # 12: BILLING_PENDING -> COMPLETED
    SESSION_CLOSE,     # 13: COMPLETED -> COMPLETED
]

# D2: Direct-auth path attempting departure after power_stop without pay_ok (Rejects at Step 9)
D2_BILLING_SKIP_DIRECT_AUTH: List[str] = [
    AUTH_REQ,          # 0: IDLE -> AUTH_PENDING
    AUTH_OK,           # 1: AUTH_PENDING -> AUTHORIZED
    PLUG_IN,           # 2: AUTHORIZED -> CABLE_DETECTED
    LOCK_OK,           # 3: CABLE_DETECTED -> EV_CONNECTED
    EV_READY,          # 4: EV_CONNECTED -> PRECHARGE
    PRECHARGE_OK,      # 5: PRECHARGE -> PRECHARGE
    POWER_START,       # 6: PRECHARGE -> CHARGING
    POWER_RAMP_DOWN,   # 7: CHARGING -> RAMP_DOWN
    POWER_STOP,        # 8: RAMP_DOWN -> ISOLATING
    SESSION_CLOSE,     # 9: ISOLATING -> REJECT (session_close invalid without pay_ok!)
]

# D2 alternative: reserved path attempting departure after power_stop
D2_BILLING_SKIP_RESERVED: List[str] = [
    RESERVE_REQ,       # 0: IDLE -> RESERVED
    AUTH_REQ,          # 1: RESERVED -> AUTH_PENDING
    AUTH_OK,           # 2: AUTH_PENDING -> AUTHORIZED
    PLUG_IN,           # 3: AUTHORIZED -> CABLE_DETECTED
    LOCK_OK,           # 4: CABLE_DETECTED -> EV_CONNECTED
    EV_READY,          # 5: EV_CONNECTED -> PRECHARGE
    PRECHARGE_OK,      # 6: PRECHARGE -> PRECHARGE
    POWER_START,       # 7: PRECHARGE -> CHARGING
    POWER_RAMP_DOWN,   # 8: CHARGING -> RAMP_DOWN
    POWER_STOP,        # 9: RAMP_DOWN -> ISOLATING
    SESSION_CLOSE,     # 10: ISOLATING -> REJECT
]


def run_scenario_d1(trace: List[str] = D1_CANONICAL_TRACE) -> Tuple[SessionInstance, VerificationVerdict]:
    """Execute Scenario D1 (Canonical Happy Path).

    Asserts that the word is accepted and terminates in an accepting state.
    """
    session = SessionInstance(session_id="D1-HAPPY-PATH")
    for sym in trace:
        success = session.step(sym)
        if not success:
            break

    verdict = session.evaluate_trace(trace)
    return session, verdict


def run_scenario_d2(trace: List[str] = D2_BILLING_SKIP_DIRECT_AUTH) -> Tuple[SessionInstance, VerificationVerdict]:
    """Execute Scenario D2 (Billing-Skip Rejection).

    Asserts that premature departure without settlement is rejected by an
    undefined transition, extracting failure index, admissible symbols, and repair path.
    """
    session = SessionInstance(session_id="D2-BILLING-SKIP")
    for sym in trace:
        success = session.step(sym)
        if not success:
            break

    verdict = session.evaluate_trace(trace)
    return session, verdict
