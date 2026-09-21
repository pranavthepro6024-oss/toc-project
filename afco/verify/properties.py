"""Safety Properties P1–P5 encoded as forbidden DFAs (M_{U,k}).

Each property DFA accepts the *forbidden* language L(M_{U,k}).
Safety holds iff L(M_S) ∩ L(M_{U,k}) = ∅.

Property formulations (from §13 of the plan):

P1 — No Unmetered Energy Transfer:
    Σ* · power_start · (Σ \ {auth_ok})* · power_active
    [encoded as: power_start without a preceding auth_ok in the same session]
    Practical encoding: a session trace that contains power_start but was
    never preceded by auth_ok is forbidden.

P2 — Mechanical Interlock Integrity / No Live Disconnect:
    Σ* · power_active · (Σ \ {power_stop, isolate})* · unlock_ok
    [encoded as: unlock_ok emitted while in a power-active state without
    an intervening power_stop / isolating transition]

P3 — No Unsettled Departure:
    Σ* · power_stop · (Σ \ {pay_ok, billing_waived})* · session_close
    [encoded as: session_close reached after power_stop without pay_ok]

P4 — Power Envelope Non-Exceedance:
    Aggregate power property – spans the product automaton M_S^N × R.
    Encoded here as a placeholder that always reports safe (enforced at
    the station composition layer in Step 4).

P5 — Emergency Isolation Latency:
    e_stop must be followed by immediate isolation (contactors_open or
    fault-terminal transition) within one step.
    Forbidden: e_stop · (Σ \ {contactors_open, fault signals})* · any_non_isolated
"""

from __future__ import annotations
from typing import Callable, Dict, FrozenSet, List, Tuple

from afco.automata.dfa import DFA
from afco.session.alphabet import (
    ALPHABET,
    AUTH_OK,
    CONTACTORS_OPEN,
    E_STOP,
    METER_TICK,
    OVERCURRENT_TRIP,
    PAY_OK,
    PILOT_LOST,
    POWER_RAMP_DOWN,
    POWER_START,
    POWER_STOP,
    RESERVE_REQ,
    SESSION_CLOSE,
    UNLOCK_OK,
    UNLOCK_REQ,
    CABLE_FAULT,
    LOCK_OK,
    LOCK_FAIL,
    PLUG_IN,
    UNPLUG,
    UNLOCK_REQ,
    AUTH_REQ,
    AUTH_FAIL,
    PAY_FAIL,
    METER_FINAL,
    EV_READY,
    EV_STOP,
    GRID_CURTAIL,
    RESET_CMD,
    PRECHARGE_OK,
    RESERVE,
)


# ---------------------------------------------------------------------------
# P1 — No Unmetered Energy Transfer
# ---------------------------------------------------------------------------
# Forbidden: a trace that reaches power_start without auth_ok having
# been seen first.  The property DFA tracks whether auth_ok has been
# observed; if power_start arrives before auth_ok, it enters an
# accepting (forbidden) state.
#
# States:
#   q0: initial — no auth_ok seen yet
#   q1: auth_ok seen — authorized for energy transfer
#   q_bad: FORBIDDEN — power_start without prior auth_ok
#   q_sink: absorbing non-accepting sink after leaving bad branch

def build_property_p1() -> DFA:
    """P1: Forbidden DFA — power_start with no prior auth_ok.

    L(P1) = Σ* where power_start appears before any auth_ok in the prefix.
    """
    Q = frozenset({"p1_q0", "p1_auth", "p1_bad"})
    q0 = "p1_q0"
    F = frozenset({"p1_bad"})   # Reaching here is forbidden

    delta: Dict[Tuple[str, str], str] = {}

    for sym in ALPHABET:
        if sym == AUTH_OK:
            delta[("p1_q0", sym)] = "p1_auth"   # Auth seen → safe zone
            delta[("p1_auth", sym)] = "p1_auth"  # Stays authorized
            delta[("p1_bad", sym)] = "p1_bad"    # Trap: already violated
        elif sym == POWER_START:
            delta[("p1_q0", sym)] = "p1_bad"     # FORBIDDEN: power before auth
            delta[("p1_auth", sym)] = "p1_auth"  # OK: auth preceded it
            delta[("p1_bad", sym)] = "p1_bad"    # Absorbing
        else:
            delta[("p1_q0", sym)] = "p1_q0"      # Neutral
            delta[("p1_auth", sym)] = "p1_auth"  # Stay authorized
            delta[("p1_bad", sym)] = "p1_bad"    # Stay bad

    return DFA(
        states=Q,
        alphabet=ALPHABET,
        transitions=delta,
        start_state=q0,
        accepting_states=F,
    )


# ---------------------------------------------------------------------------
# P2 — Mechanical Interlock Integrity / No Live Disconnect
# ---------------------------------------------------------------------------
# Forbidden: unlock_ok (or unlock_req accepted by M_S into unlocking)
# while the session is in an active power state, without an intervening
# power_stop + contactors_open sequence.
#
# We track a boolean "power_active" flag:
#   q0: initial / not power-active
#   q1: power_start seen (power active)
#   q_bad: FORBIDDEN — unlock while power active
#
# Transitions:
#   power_start → q1 (power becomes active)
#   power_stop, contactors_open → q0  (power deactivated)
#   unlock_ok in q1 → q_bad  (FORBIDDEN)
#   unlock_ok in q0 → q0     (safe, already deactivated)

def build_property_p2() -> DFA:
    """P2: Forbidden DFA — connector unlock while power is active.

    L(P2) = traces containing unlock_ok after power_start without an
    intervening power_stop/contactors_open.
    """
    Q = frozenset({"p2_idle", "p2_powered", "p2_bad"})
    q0 = "p2_idle"
    F = frozenset({"p2_bad"})

    delta: Dict[Tuple[str, str], str] = {}

    for sym in ALPHABET:
        if sym == POWER_START:
            delta[("p2_idle", sym)] = "p2_powered"
            delta[("p2_powered", sym)] = "p2_powered"   # Stay active
            delta[("p2_bad", sym)] = "p2_bad"

        elif sym in {POWER_STOP, CONTACTORS_OPEN, POWER_RAMP_DOWN}:
            # Deactivate power
            delta[("p2_idle", sym)] = "p2_idle"
            delta[("p2_powered", sym)] = "p2_idle"      # Power deactivated
            delta[("p2_bad", sym)] = "p2_bad"

        elif sym in {UNLOCK_OK, UNLOCK_REQ}:
            delta[("p2_idle", sym)] = "p2_idle"         # Safe unlock
            delta[("p2_powered", sym)] = "p2_bad"       # FORBIDDEN
            delta[("p2_bad", sym)] = "p2_bad"

        else:
            delta[("p2_idle", sym)] = "p2_idle"
            delta[("p2_powered", sym)] = "p2_powered"
            delta[("p2_bad", sym)] = "p2_bad"

    return DFA(
        states=Q,
        alphabet=ALPHABET,
        transitions=delta,
        start_state=q0,
        accepting_states=F,
    )


# ---------------------------------------------------------------------------
# P3 — No Unsettled Departure
# ---------------------------------------------------------------------------
# Forbidden: session_close reached after power_stop without pay_ok.
#
# States:
#   q0: initial
#   q1: power_stop seen — pending settlement
#   q_bad: FORBIDDEN — session_close after power_stop without pay_ok
#   q_settled: pay_ok seen — safe to close

def build_property_p3() -> DFA:
    """P3: Forbidden DFA — session_close without prior pay_ok after power_stop.

    L(P3) = traces where session_close appears after power_stop but pay_ok
    has not been seen since power_stop.
    """
    Q = frozenset({"p3_init", "p3_post_stop", "p3_settled", "p3_bad"})
    q0 = "p3_init"
    F = frozenset({"p3_bad"})

    delta: Dict[Tuple[str, str], str] = {}

    for sym in ALPHABET:
        if sym == POWER_STOP:
            delta[("p3_init", sym)] = "p3_post_stop"
            delta[("p3_post_stop", sym)] = "p3_post_stop"  # Reset wait
            delta[("p3_settled", sym)] = "p3_post_stop"    # Re-enter wait
            delta[("p3_bad", sym)] = "p3_bad"

        elif sym == PAY_OK:
            delta[("p3_init", sym)] = "p3_init"
            delta[("p3_post_stop", sym)] = "p3_settled"    # Settlement done
            delta[("p3_settled", sym)] = "p3_settled"
            delta[("p3_bad", sym)] = "p3_bad"

        elif sym == SESSION_CLOSE:
            delta[("p3_init", sym)] = "p3_init"            # No power_stop yet — OK
            delta[("p3_post_stop", sym)] = "p3_bad"        # FORBIDDEN
            delta[("p3_settled", sym)] = "p3_settled"      # Settled — OK
            delta[("p3_bad", sym)] = "p3_bad"

        else:
            delta[("p3_init", sym)] = "p3_init"
            delta[("p3_post_stop", sym)] = "p3_post_stop"
            delta[("p3_settled", sym)] = "p3_settled"
            delta[("p3_bad", sym)] = "p3_bad"

    return DFA(
        states=Q,
        alphabet=ALPHABET,
        transitions=delta,
        start_state=q0,
        accepting_states=F,
    )


# ---------------------------------------------------------------------------
# P4 — Power Envelope Non-Exceedance (Placeholder)
# ---------------------------------------------------------------------------
# This property spans the product automaton M_S^N × R and is enforced
# fully in Step 4 (Station Composition). The single-session DFA does not
# carry aggregate power state.  Provide a trivially-safe DFA here that
# never accepts (empty forbidden language) so the checker infrastructure
# remains consistent.

def build_property_p4_placeholder() -> DFA:
    """P4 placeholder: always reports safe (empty forbidden language).

    Real enforcement is deferred to Step 4 station invariant I2.
    """
    Q = frozenset({"p4_safe"})
    delta: Dict[Tuple[str, str], str] = {}
    for sym in ALPHABET:
        delta[("p4_safe", sym)] = "p4_safe"

    return DFA(
        states=Q,
        alphabet=ALPHABET,
        transitions=delta,
        start_state="p4_safe",
        accepting_states=frozenset(),  # No accepting states → empty forbidden language
    )


# ---------------------------------------------------------------------------
# P5 — Emergency Isolation Latency
# ---------------------------------------------------------------------------
# Forbidden: e_stop is followed by any symbol that is NOT an immediate
# isolation action (contactors_open, overcurrent_trip, cable_fault, or
# pilot_lost which all lead to FAULT_TERMINAL in M_S).
#
# States:
#   q0: normal operation
#   q1: e_stop just received — next must be isolation symbol
#   q_bad: FORBIDDEN — non-isolation event after e_stop

_P5_IMMEDIATE_ISOLATION = frozenset({
    CONTACTORS_OPEN,
    OVERCURRENT_TRIP,
    CABLE_FAULT,
    PILOT_LOST,
    LOCK_FAIL,
})


def build_property_p5() -> DFA:
    """P5: Forbidden DFA — non-isolation event immediately following e_stop.

    L(P5) = traces where a non-isolation symbol immediately follows e_stop.
    """
    Q = frozenset({"p5_normal", "p5_post_estop", "p5_bad"})
    q0 = "p5_normal"
    F = frozenset({"p5_bad"})

    delta: Dict[Tuple[str, str], str] = {}

    for sym in ALPHABET:
        if sym == E_STOP:
            delta[("p5_normal", sym)] = "p5_post_estop"
            delta[("p5_post_estop", sym)] = "p5_post_estop"  # Another e_stop: still pending
            delta[("p5_bad", sym)] = "p5_bad"

        elif sym in _P5_IMMEDIATE_ISOLATION:
            delta[("p5_normal", sym)] = "p5_normal"
            delta[("p5_post_estop", sym)] = "p5_normal"   # Properly isolated → clear
            delta[("p5_bad", sym)] = "p5_bad"

        else:
            # Any other symbol after e_stop is a latency violation
            delta[("p5_normal", sym)] = "p5_normal"
            delta[("p5_post_estop", sym)] = "p5_bad"      # FORBIDDEN
            delta[("p5_bad", sym)] = "p5_bad"

    return DFA(
        states=Q,
        alphabet=ALPHABET,
        transitions=delta,
        start_state=q0,
        accepting_states=F,
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_PROPERTY_BUILDERS: Dict[str, Callable[[], DFA]] = {
    "P1_NoUnmeteredEnergy": build_property_p1,
    "P2_NoLiveDisconnect": build_property_p2,
    "P3_NoUnsettledDeparture": build_property_p3,
    "P4_PowerEnvelope": build_property_p4_placeholder,
    "P5_EmergencyLatency": build_property_p5,
}
