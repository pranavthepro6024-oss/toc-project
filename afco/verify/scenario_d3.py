"""Scenario D3 — Live Disconnect Attempt (Model-Checking Proof via P2).

Demonstrates the intersection-emptiness model checker applied to safety
property P2 (Mechanical Interlock Integrity / No Live Disconnect).

The scenario proves, via automata-theoretic model checking, that:

    L(M_S) ∩ L(P2) = ∅

i.e., no word accepted by the canonical session automaton M_S also satisfies
the forbidden-language DFA P2 (power_start followed by unlock_ok/unlock_req
without an intervening power_stop / power_ramp_down).

This is the *formal verification result* for D3:

  - If the intersection is EMPTY → M_S is **proved safe** w.r.t. live disconnect.
    The model checker certifies that the connector lock is never released while
    current is flowing in any reachable session trace.

  - If the intersection is NON-EMPTY → the model checker extracts the shortest
    counterexample trace that witnesses the safety violation.

The M3 exit criterion is met when:
  1. `check_safety(M_S, P2)` runs without exception.
  2. A structured `VerificationVerdict` is produced with either:
     a. `is_safe=True` (the model checker formally proves P2 holds), OR
     b. `is_safe=False` with a formal counterexample trace.
  3. The verdict is clearly distinguished from a D2-style missing-transition
     rejection (`PartialDeltaUndefined`) — it is a *language-level* result.

Additionally, P1 (No Unmetered Energy Transfer) IS violated by M_S, because
M_S permits `plug_in → lock_ok → ev_ready → power_start → COMPLETED` without
a preceding `auth_ok`.  The model checker extracts this counterexample,
demonstrating the full counterexample-extraction pipeline.

Event trace for human illustration of D3 intent (operator unlock attempt
while charging — the operator sends unlock_req during CHARGING):

    ... → power_start → [CHARGING state] → unlock_req → ...

M_S correctly blocks this at the structural level (no δ(CHARGING, unlock_req)),
which is exactly why L(M_S) ∩ L(P2) = ∅.
"""

from __future__ import annotations
from typing import Optional, Tuple, List

from afco.session.alphabet import (
    AUTH_OK,
    AUTH_REQ,
    EV_READY,
    LOCK_OK,
    METER_TICK,
    PAY_OK,
    PLUG_IN,
    POWER_RAMP_DOWN,
    POWER_START,
    POWER_STOP,
    PRECHARGE_OK,
    RESERVE_REQ,
    SESSION_CLOSE,
    UNLOCK_OK,
    UNLOCK_REQ,
    UNPLUG,
    METER_FINAL,
    CONTACTORS_OPEN,
)
from afco.session.canonical import get_canonical_dfa
from afco.session.instance import VerificationVerdict
from afco.verify.checker import check_safety, check_all_properties, SafetyReport
from afco.verify.properties import build_property_p2


# ---------------------------------------------------------------------------
# D3 human-intent trace — illustrates what the operator attempted
# (the model checker will assess whether M_S permits it)
# ---------------------------------------------------------------------------
D3_OPERATOR_TRACE = [
    RESERVE_REQ,      # IDLE → RESERVED
    AUTH_REQ,         # RESERVED → AUTH_PENDING
    AUTH_OK,          # AUTH_PENDING → AUTHORIZED
    PLUG_IN,          # AUTHORIZED → CABLE_DETECTED
    LOCK_OK,          # CABLE_DETECTED → EV_CONNECTED
    EV_READY,         # EV_CONNECTED → PRECHARGE
    PRECHARGE_OK,     # PRECHARGE → PRECHARGE
    POWER_START,      # PRECHARGE → CHARGING   [power now active]
    METER_TICK,       # CHARGING → CHARGING
    UNLOCK_REQ,       # ← ATTEMPTED: unlock while power active
]


def run_scenario_d3() -> Tuple[VerificationVerdict, SafetyReport]:
    """Execute Scenario D3 — Live Disconnect Safety Verification (Model Checking).

    Uses the intersection-emptiness decision procedure to formally verify
    whether M_S permits any live-disconnect sequence:

        check_safety(M_S, P2) → VerificationVerdict

    If L(M_S) ∩ L(P2) = ∅:
        M_S is formally proved SAFE w.r.t. live disconnect.
        The verdict certifies that δ_S structurally prevents connector
        unlock while current is flowing.

    If L(M_S) ∩ L(P2) ≠ ∅:
        A counterexample trace is extracted and a repair path synthesized.

    Also runs the full P1–P5 sweep, which demonstrates:
    - P1 is VIOLATED: M_S allows power_start without auth_ok (plug-in bypass).
    - P2 is SAFE: M_S correctly prevents live disconnect.
    - P3 may be VIOLATED: M_S may allow session_close without pay_ok (via partial paths).

    Returns:
        (p2_verdict, full_report) where:
          - p2_verdict: result of targeted P2 model check (the D3 result).
          - full_report: P1–P5 sweep for report completeness.
    """
    ms = get_canonical_dfa()
    p2 = build_property_p2()

    # Targeted P2 check — the formal D3 model-checking result
    p2_verdict = check_safety(ms, p2, property_name="P2_NoLiveDisconnect")

    # Full multi-property sweep for completeness
    full_report = check_all_properties(ms)

    return p2_verdict, full_report


def run_d3_p1_demonstration() -> VerificationVerdict:
    """Demonstrate P1 counterexample extraction as part of D3.

    P1 (No Unmetered Energy Transfer) is violated by M_S because the
    plug-in path allows power_start without auth_ok:
        plug_in → lock_ok → ev_ready → power_start

    The model checker extracts the shortest such counterexample.
    """
    from afco.verify.properties import build_property_p1
    ms = get_canonical_dfa()
    p1 = build_property_p1()
    return check_safety(ms, p1, property_name="P1_NoUnmeteredEnergy")
