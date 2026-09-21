"""Definition of states in which a failed session can safely pause."""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Optional

from afco.session.alphabet import (
    BILLING_PENDING, CHARGING, COMPLETED, FAULT_TERMINAL, IDLE,
    ISOLATING, PAUSED_DISPATCH, RAMP_DOWN, SUSPENDED_EV, SUSPENDED_EVSE,
    UNLOCKED, UNPLUGGED,
)


@dataclass(frozen=True)
class SafeStatePolicy:
    """Evidence constraints used to refine the state-level safe set.

    ``meter_verified`` means that all delivered energy has been accounted for;
    ``payment_guaranteed`` permits completion without another payment event.
    The defaults are conservative and therefore suitable for an untrusted
    recovery request.
    """

    meter_verified: bool = False
    cable_interlock: bool = False
    link_integrity: bool = True
    payment_guaranteed: bool = False


_BASE_SAFE: FrozenSet[str] = frozenset({
    IDLE, PAUSED_DISPATCH, SUSPENDED_EV, SUSPENDED_EVSE, RAMP_DOWN,
    ISOLATING, UNLOCKED, UNPLUGGED, BILLING_PENDING, COMPLETED,
})


def safe_states(policy: Optional[SafeStatePolicy] = None) -> FrozenSet[str]:
    """Return the admissible safe state set ``S`` for the supplied evidence."""
    policy = policy or SafeStatePolicy()
    states = set(_BASE_SAFE)
    # Active transfer is safe only if telemetry is available and metering is
    # already reconciled.  A disconnected link must never be treated as safe.
    if policy.link_integrity and policy.meter_verified:
        states.add(CHARGING)
    if not policy.link_integrity:
        states.discard(PAUSED_DISPATCH)
        states.discard(SUSPENDED_EV)
        states.discard(SUSPENDED_EVSE)
    # FAULT_TERMINAL is intentionally never safe: it has no outgoing edges.
    states.discard(FAULT_TERMINAL)
    return frozenset(states)
