"""Unit tests for SessionInstance runtime and repair synthesis."""

from afco.session.alphabet import (
    AUTH_OK,
    AUTH_REQ,
    BILLING_PENDING,
    COMPLETED,
    E_STOP,
    FAULT_TERMINAL,
    IDLE,
    METER_TICK,
    PAY_OK,
    PLUG_IN,
    POWER_START,
    UNPLUGGED,
)
from afco.session.canonical import get_canonical_dfa
from afco.session.instance import SessionInstance, find_shortest_repair_path


def test_session_instance_lifecycle():
    """Verify session initialization and step-by-step state advancement."""
    sess = SessionInstance(session_id="test-001")
    assert sess.current_state == IDLE
    assert sess.is_accepted() is False
    assert sess.is_trap() is False

    # Valid step
    ok = sess.step(AUTH_REQ)
    assert ok is True
    assert sess.current_state == "AUTH_PENDING"
    assert len(sess.history) == 1
    assert sess.history[0] == (IDLE, AUTH_REQ, "AUTH_PENDING")

    # Invalid step (power_start invalid in AUTH_PENDING)
    ok = sess.step(POWER_START)
    assert ok is False
    assert sess.current_state == "AUTH_PENDING"  # State preserved
    assert sess.last_verdict is not None
    assert sess.last_verdict.is_safe is False
    assert sess.last_verdict.failure_index == 1
    assert sess.last_verdict.rejected_symbol == POWER_START


def test_meter_kwh_tracking():
    """Verify that meter ticks accumulate energy in SessionInstance."""
    sess = SessionInstance()
    # Transition to CHARGING
    for sym in ["auth_req", "auth_ok", "plug_in", "lock_ok", "ev_ready", "precharge_ok", "power_start"]:
        assert sess.step(sym) is True
    assert sess.current_state == "CHARGING"

    assert sess.meter_kwh == 0.0
    sess.step(METER_TICK)
    sess.step(METER_TICK)
    assert sess.meter_kwh == 0.50


def test_repair_path_synthesis():
    """Verify that BFS repair path synthesis discovers shortest path to COMPLETED."""
    dfa = get_canonical_dfa()

    # From BILLING_PENDING, shortest repair is ['pay_ok']
    repair_billing = find_shortest_repair_path(dfa, BILLING_PENDING)
    assert repair_billing == [PAY_OK]

    # From UNPLUGGED, shortest repair is ['meter_final', 'pay_ok'] or ['pay_ok']
    repair_unplugged = find_shortest_repair_path(dfa, UNPLUGGED)
    assert repair_unplugged is not None
    # Tracing the repair must reach COMPLETED
    curr = UNPLUGGED
    for sym in repair_unplugged:
        curr = dfa.step(curr, sym)
    assert curr == COMPLETED

    # From COMPLETED, repair is []
    assert find_shortest_repair_path(dfa, COMPLETED) == []

    # From FAULT_TERMINAL, repair is None (trap state)
    assert find_shortest_repair_path(dfa, FAULT_TERMINAL) is None


def test_trap_detection():
    """Verify that entering FAULT_TERMINAL marks session as trapped."""
    sess = SessionInstance()
    sess.step("auth_req")
    sess.step("auth_ok")
    sess.step("plug_in")
    sess.step("lock_ok")
    # E_STOP in EV_CONNECTED
    sess.step(E_STOP)
    assert sess.current_state == FAULT_TERMINAL
    assert sess.is_trap() is True
    assert sess.synthesize_repair_path() is None
