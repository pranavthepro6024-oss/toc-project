from afco.sim.scenario_d13 import run_scenario_d13

def test_d13_full_fleet_stress_scenario():
    result = run_scenario_d13(fleet_size=8)
    assert result.is_safe
    assert result.simulation.rejected_events == 0
    assert all(state == "COMPLETED" for state in result.simulation.final_states.values())
