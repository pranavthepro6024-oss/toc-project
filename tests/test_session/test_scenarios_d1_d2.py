"""Regression and verification tests for Scenarios D1 (Happy Path) and D2 (Billing-Skip Rejection)."""

from afco.session.alphabet import COMPLETED
from afco.session.scenarios import (
    run_scenario_d1,
    run_scenario_d2,
    D1_CANONICAL_TRACE,
    D2_BILLING_SKIP_DIRECT_AUTH,
    D2_BILLING_SKIP_RESERVED,
)


def test_scenario_d1_happy_path_acceptance():
    """Checkpoint 2: Scenario D1 accepts cleanly ending in COMPLETED."""
    session, verdict = run_scenario_d1()

    # Formally accepted
    assert verdict.is_safe is True
    assert session.current_state == COMPLETED
    assert session.is_accepted() is True
    assert verdict.failure_index is None
    assert verdict.rejected_symbol is None

    # Explanation report formatting
    report = verdict.format_report()
    assert "VERDICT: ACCEPT" in report


def test_scenario_d2_billing_skip_rejection_direct_auth():
    """Checkpoint 2: Scenario D2 rejects at Step 9 with explainable diagnostics."""
    session, verdict = run_scenario_d2(D2_BILLING_SKIP_DIRECT_AUTH)

    # Formally rejected at step 9
    assert verdict.is_safe is False
    assert verdict.failure_index == 9
    assert verdict.rejected_symbol == "session_close"
    assert verdict.violated_property == "PartialDeltaUndefined"

    # Admissible symbols from ISOLATING are reported
    assert verdict.admissible_symbols is not None
    assert "contactors_open" in verdict.admissible_symbols
    assert "unplug" in verdict.admissible_symbols

    # Synthesized repair path exists and reaches COMPLETED
    assert verdict.repair_path is not None
    assert len(verdict.repair_path) > 0

    curr = session.current_state
    for sym in verdict.repair_path:
        curr = session.dfa.step(curr, sym)
    assert curr == COMPLETED

    # Explanation report formatting
    report = verdict.format_report()
    assert "VERDICT: REJECT" in report
    assert "Step 9" in report
    assert "session_close" in report
    assert "Synthesized Repair" in report


def test_scenario_d2_billing_skip_rejection_reserved():
    """Scenario D2 variant with reservation rejects at Step 10."""
    session, verdict = run_scenario_d2(D2_BILLING_SKIP_RESERVED)

    assert verdict.is_safe is False
    assert verdict.failure_index == 10
    assert verdict.rejected_symbol == "session_close"
    assert verdict.repair_path is not None

    curr = session.current_state
    for sym in verdict.repair_path:
        curr = session.dfa.step(curr, sym)
    assert curr == COMPLETED
