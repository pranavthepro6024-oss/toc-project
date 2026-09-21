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
    assert not result.is_safe; assert result.final_states["v1"] == "IDLE"; assert result.events[0].state_before == result.events[0].state_after
def test_fuzz_soundness_checkpoint():
    result = fuzz_soundness(trials=100_000, seed=17); assert result["sound"] is True; assert result["trials"] == 100_000
def test_dashboard_api_can_schedule_and_run():
    client = TestClient(create_app()); assert client.get("/").status_code == 200
    client.post("/api/events", json={"session_id": "v1", "symbol": "reserve_req", "at": 1}); response = client.post("/api/run")
    assert response.status_code == 200; assert response.json()["states"]["v1"] == "RESERVED"; assert client.get("/api/events").json()[0]["accepted"] is True
