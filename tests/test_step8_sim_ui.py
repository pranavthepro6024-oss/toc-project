from fastapi.testclient import TestClient
from afco.sim.clock import DiscreteEventClock
from afco.sim.simulator import FleetSimulator, fuzz_soundness
from afco.ui.app import create_app

def test_clock_is_deterministic_and_orders_equal_timestamps():
    clock = DiscreteEventClock(); seen = []
    clock.schedule(2, lambda: seen.append("second")); clock.schedule(1, lambda: seen.append("first")); clock.schedule(1, lambda: seen.append("same-time"))
    assert clock.run() == 3; assert seen == ["first", "same-time", "second"]; assert clock.now == 2
def test_simulator_rejection_is_side_effect_free():
    sim = FleetSimulator(); sim.schedule("v1", "power_start", 0); result = sim.run()
    assert result.is_safe; assert result.rejected_events == 1; assert not result.events[0].accepted; assert result.final_states["v1"] == "IDLE"; assert result.events[0].state_before == result.events[0].state_after
def test_fuzz_soundness_checkpoint():
    result = fuzz_soundness(trials=100_000, seed=17); assert result["sound"] is True; assert result["trials"] == 100_000
def test_dashboard_api_can_schedule_and_run():
    client = TestClient(create_app()); assert client.get("/").status_code == 200
    client.post("/api/events", json={"session_id": "v1", "symbol": "reserve_req", "at": 1}); response = client.post("/api/run")
    assert response.status_code == 200; assert response.json()["states"]["v1"] == "RESERVED"; assert client.get("/api/events").json()[0]["accepted"] is True


def test_dashboard_scenarios_and_fault_injection():
    client = TestClient(create_app())
    scenarios = client.get("/api/scenarios").json()
    assert len(scenarios) == 13
    for sc in scenarios:
        res = client.post(f"/api/scenarios/{sc['id']}")
        assert res.status_code == 200
        assert "verdict" in res.json()

    fault_res = client.post("/api/faults/inject", json={"session_id": "f1", "fault_type": "e_stop"})
    assert fault_res.status_code == 200
    assert fault_res.json()["is_safe"] is True

    graph_res = client.get("/api/graph.svg?active_state=CHARGING")
    assert graph_res.status_code == 200
    assert "svg" in graph_res.headers.get("content-type", "")

    # Test /api/graph/data
    graph_data_res = client.get("/api/graph/data")
    assert graph_data_res.status_code == 200
    gdata = graph_data_res.json()
    assert len(gdata["states"]) == 18
    assert gdata["start_state"] == "IDLE"
    assert "COMPLETED" in gdata["accepting_states"]

    # Test /api/demo/action JSON body acceptance (no 422 Unprocessable Entity)
    action_res = client.post("/api/demo/action", json={"session_id": "v1", "action": "reserve"})
    assert action_res.status_code == 200
    assert action_res.json()["accepted"] is True
    assert action_res.json()["state_after"] == "RESERVED"

    # Test undefined transition rejection with repair synthesis
    illegal_res = client.post("/api/demo/action", json={"session_id": "v1", "action": "pay"})
    assert illegal_res.status_code == 200
    assert illegal_res.json()["accepted"] is False
    assert illegal_res.json()["state_before"] == illegal_res.json()["state_after"]


def test_all_scenarios_return_canonical_final_states():
    client = TestClient(create_app())
    expected_states = {
        "D1": "COMPLETED",
        "D2": "ISOLATING",
        "D3": "CHARGING",
        "D4": "SUSPENDED_EV",
        "D5": "FAULT_TERMINAL",
        "D6": "BILLING_PENDING",
        "D7": "PAUSED_DISPATCH",
        "D8": "UNPLUGGED",
        "D9": "CHARGING",
        "D10": "COMPLETED",
        "D11": "IDLE",
        "D12": "CHARGING",
        "D13": "COMPLETED",
    }
    for sc_id, expected_st in expected_states.items():
        res = client.post(f"/api/scenarios/{sc_id}")
        assert res.status_code == 200, f"Scenario {sc_id} failed with {res.status_code}"
        data = res.json()
        assert "final_state" in data, f"Scenario {sc_id} missing final_state"
        assert data["final_state"] == expected_st, f"Scenario {sc_id} final_state {data['final_state']} != {expected_st}"


def test_scenario_execution_recovers_from_prior_fault():
    """Verify that running scenarios works cleanly even after a bay is in FAULT_TERMINAL or COMPLETED."""
    client = TestClient(create_app())
    # Cause fault on Bay 1
    fault_res = client.post("/api/demo/action", json={"session_id": "v1", "action": "e_stop"})
    assert fault_res.json()["state_after"] == "FAULT_TERMINAL"

    # Now run scenarios in arbitrary sequence after the fault
    sequence = ["D1", "D5", "D2", "D3", "D11", "D8", "D13"]
    for sc_id in sequence:
        res = client.post(f"/api/scenarios/{sc_id}")
        assert res.status_code == 200
        data = res.json()
        assert "final_state" in data
        assert data["final_state"] is not None


def test_bay_recycling_and_manual_reset():
    """Verify that bay actions can be reset or auto-recycled from FAULT_TERMINAL and COMPLETED."""
    client = TestClient(create_app())

    # Trip to FAULT_TERMINAL
    client.post("/api/demo/action", json={"session_id": "v1", "action": "e_stop"})
    bays = client.get("/api/bays").json()
    v1_state = next(b["state"] for b in bays if b["session_id"] == "v1")
    assert v1_state == "FAULT_TERMINAL"

    # 1. Manual reset
    reset_res = client.post("/api/demo/action", json={"session_id": "v1", "action": "reset"})
    assert reset_res.status_code == 200
    assert reset_res.json()["state_after"] == "IDLE"

    # Trip again to FAULT_TERMINAL
    client.post("/api/demo/action", json={"session_id": "v1", "action": "e_stop"})

    # 2. Auto-recycle on new reservation
    reserve_res = client.post("/api/demo/action", json={"session_id": "v1", "action": "reserve"})
    assert reserve_res.status_code == 200
    assert reserve_res.json()["accepted"] is True
    assert reserve_res.json()["state_after"] == "RESERVED"


def test_clock_reset_and_zero_timestamp_scheduling():
    """Verify that sim.reset() resets clock to 0.0 and allows zero-timestamp event scheduling."""
    sim = FleetSimulator()
    sim.schedule("v1", "reserve_req", 5.0)
    sim.run()
    assert sim.clock.now == 5.0

    sim.reset()
    assert sim.clock.now == 0.0

    # Scheduling at 0.0 must succeed without ValueError
    sim.schedule("v1", "reserve_req", 0.0)
    res = sim.run()
    assert res.is_safe
    assert res.accepted_events == 1

