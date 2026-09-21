"""Executable D4–D8 recovery demonstrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from afco.recovery.engine import RecoveryEngine, RecoveryPlan, RecoveryStatus
from afco.session.alphabet import (
    BILLING_PENDING, CHARGING, COMPLETED, FAULT_TERMINAL, PAUSED_DISPATCH,
)


@dataclass(frozen=True)
class RecoveryScenario:
    name: str
    plan: RecoveryPlan


def run_scenario_d4() -> RecoveryScenario:
    return RecoveryScenario("D4_TelemetryDrop", RecoveryEngine().recover(CHARGING))


def run_scenario_d5() -> RecoveryScenario:
    return RecoveryScenario("D5_EmergencyContactorTrip", RecoveryEngine().recover(FAULT_TERMINAL))


def run_scenario_d6() -> RecoveryScenario:
    return RecoveryScenario("D6_PaymentGatewayTimeout", RecoveryEngine().recover(BILLING_PENDING))


def run_scenario_d7() -> RecoveryScenario:
    return RecoveryScenario("D7_GridCurtailment", RecoveryEngine().recover(PAUSED_DISPATCH))


def run_scenario_d8() -> RecoveryScenario:
    engine = RecoveryEngine()
    # A hostile proposal claims completion without settlement.  The prefix
    # contains power_stop, so P3 must reject it even though completion is a
    # superficially cheap target.
    history = ["power_stop"]
    plan = engine.recover_to_completed("UNPLUGGED", history=history)
    if engine.verify_candidate(history, ["session_close"]):
        raise AssertionError("D8 gate accepted an unsettled completion")
    return RecoveryScenario("D8_HostileBypass", plan)
