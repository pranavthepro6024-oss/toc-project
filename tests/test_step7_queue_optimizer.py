from afco.queue import BoundedQueueCounter, prove_unbounded_non_regular, PushdownAutomaton
from afco.optimizer import KernelAdmissionGate, ScheduleItem, ScheduleProposal, run_scenario_d12


def test_bounded_counter_has_k_plus_one_states_and_rejects_overflow_underflow():
    counter = BoundedQueueCounter(2)
    assert counter.state_count == 3
    assert counter.accepts(["enq", "enq", "deq"])
    assert not counter.accepts(["enq", "enq", "enq"])
    assert not counter.accepts(["deq"])


def test_pumping_adversary_separates_unbounded_queue_language():
    result = prove_unbounded_non_regular(5)
    assert result.proves_non_regular
    assert not result.balance_preserved


def test_pda_accepts_nested_holds_only():
    pda = PushdownAutomaton()
    assert pda.accepts(["hold", "hold", "release", "release"])
    assert not pda.accepts(["hold", "release", "release"])
    assert not pda.accepts(["hold"])


def test_d12_rejects_unsafe_schedule_and_keeps_safe_fallback():
    result = run_scenario_d12()
    assert result.is_safe
    assert result.unsafe.counterexample
    assert result.unsafe.schedule == result.safe.schedule


def test_gate_rejects_power_overrun_with_invariant_counterexample():
    gate = KernelAdmissionGate(power_limit_kw=100)
    proposal = ScheduleProposal((ScheduleItem("a", 75), ScheduleItem("b", 75)))
    verdict = gate.admit(proposal)
    assert not verdict.admitted
    assert "I2" in verdict.reason
