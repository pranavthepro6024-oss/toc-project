"""Step 5: Automated unit and regression tests for the Adaptive Recovery Engine."""

import pytest
from afco.recovery.cost import TransitionCostModel
from afco.recovery.engine import RecoveryEngine, RecoveryStatus, VerificationGate
from afco.recovery.evidence import Evidence
from afco.recovery.safe_states import SafeStatePolicy, safe_states
from afco.recovery.scenarios import (
    run_scenario_d4,
    run_scenario_d5,
    run_scenario_d6,
    run_scenario_d7,
    run_scenario_d8,
)
from afco.session.alphabet import (
    BILLING_PENDING,
    CHARGING,
    COMPLETED,
    FAULT_TERMINAL,
    IDLE,
    PAUSED_DISPATCH,
    PRECHARGE,
    SUSPENDED_EV,
    UNPLUGGED,
)


def test_safe_states_policy_filtering():
    """Verify safe states generation based on evidence policy."""
    default_states = safe_states(SafeStatePolicy())
    assert IDLE in default_states
    assert COMPLETED in default_states
    assert FAULT_TERMINAL not in default_states

    # Cable interlock allows SUSPENDED states
    interlock_states = safe_states(SafeStatePolicy(cable_interlock=True))
    assert SUSPENDED_EV in interlock_states
    assert PAUSED_DISPATCH in interlock_states


def test_cost_model_weights():
    """Verify domain-weighted edge transition costs."""
    cost_fn = TransitionCostModel()
    # Contactor / heavy transitions are penalized
    assert cost_fn(CHARGING, "power_stop", "ISOLATING") >= 1.0
    # Safe suspension transitions have lower penalties
    assert cost_fn(CHARGING, "ev_stop", SUSPENDED_EV) <= 1.0


def test_verification_gate_detects_violations():
    """Verify gate catches forbidden traces using property DFAs."""
    gate = VerificationGate()
    # Safe word
    ok, prop = gate.verify(["auth_ok", "plug_in", "lock_ok", "power_start"])
    assert ok is True
    assert prop is None

    # P2 violation: unlock while current is flowing
    bad_trace = ["auth_ok", "power_start", "unlock_ok"]
    ok, prop = gate.verify(bad_trace)
    assert ok is False
    assert prop is not None


def test_recovery_from_safe_state_is_noop():
    """If already in a safe state, recovery cost is zero and path is empty."""
    engine = RecoveryEngine()
    plan = engine.recover(IDLE)
    assert plan.status is RecoveryStatus.FOUND
    assert plan.target_state == IDLE
    assert plan.path == []
    assert plan.cost == 0.0


def test_scenario_d4_telemetry_drop():
    """Scenario D4: telemetry drop during CHARGING recovers to SUSPENDED_EV."""
    scenario = run_scenario_d4()
    assert scenario.name == "D4_TelemetryDrop"
    assert scenario.plan.status is RecoveryStatus.FOUND
    assert scenario.plan.start_state == CHARGING
    assert scenario.plan.target_state == SUSPENDED_EV
    assert scenario.plan.path == ["ev_stop"]
    assert scenario.plan.cost == 1.0


def test_scenario_d5_emergency_contactor_trip():
    """Scenario D5: FAULT_TERMINAL is a formal trap with no safe outgoing paths."""
    scenario = run_scenario_d5()
    assert scenario.name == "D5_EmergencyContactorTrip"
    assert scenario.plan.status is RecoveryStatus.NO_PATH
    assert scenario.plan.start_state == FAULT_TERMINAL
    assert scenario.plan.target_state is None
    assert scenario.plan.path == []
    assert "no verified safe state" in scenario.plan.reason


def test_scenario_d6_payment_gateway_timeout():
    """Scenario D6: payment failure holds session in BILLING_PENDING."""
    scenario = run_scenario_d6()
    assert scenario.name == "D6_PaymentGatewayTimeout"
    assert scenario.plan.status is RecoveryStatus.FOUND
    assert scenario.plan.start_state == BILLING_PENDING
    assert scenario.plan.target_state == BILLING_PENDING
    assert scenario.plan.path == []
    assert scenario.plan.cost == 0.0


def test_scenario_d7_grid_curtailment():
    """Scenario D7: grid curtailment holds in PAUSED_DISPATCH."""
    scenario = run_scenario_d7()
    assert scenario.name == "D7_GridCurtailment"
    assert scenario.plan.status is RecoveryStatus.FOUND
    assert scenario.plan.start_state == PAUSED_DISPATCH
    assert scenario.plan.target_state == PAUSED_DISPATCH
    assert scenario.plan.path == []
    assert scenario.plan.cost == 0.0


def test_scenario_d8_hostile_bypass_rejection():
    """Scenario D8: hostile bypass skipping pay_ok is rejected by P3 gate."""
    scenario = run_scenario_d8()
    assert scenario.name == "D8_HostileBypass"
    assert scenario.plan.status is RecoveryStatus.FOUND
    assert scenario.plan.target_state == COMPLETED
    # The valid path must include pay_ok, not skip to session_close directly
    assert "pay_ok" in scenario.plan.path
