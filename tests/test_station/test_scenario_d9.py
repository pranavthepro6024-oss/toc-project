from afco.station.scenario_d9 import run_scenario_d9


def test_d9_runs_with_three_connectors_and_power_cap():
    result = run_scenario_d9(explore_limit=1000)
    assert result.is_safe
    assert result.state.resource.occupied_connectors == 3
    assert result.state.resource.power_kw == 150
    assert result.metrics.symmetry_reduced_state_count <= result.metrics.naive_state_count
