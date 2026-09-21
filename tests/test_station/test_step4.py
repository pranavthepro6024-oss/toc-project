from afco.session.alphabet import CABLE_DETECTED, CHARGING, IDLE, PLUG_IN, POWER_START, POWER_STOP, LOCK_OK, EV_READY
from afco.station import LazyStationProduct, ResourceConfig, ResourceEvent, ResourceState, SharedResourceAutomaton, GridMode, check_invariants


def test_resource_enforces_connector_and_power_limits():
    r = SharedResourceAutomaton(ResourceConfig(connectors=1, power_limit_kw=50, power_tiers=(0, 50)))
    s = r.step(r.start_state, ResourceEvent.CONNECT)
    assert s and r.step(s, ResourceEvent.CONNECT) is None
    charging = r.step(s, ResourceEvent.POWER_START, 50)
    assert charging and r.step(charging, ResourceEvent.POWER_START, 50) is None


def test_resource_grid_modes_are_explicit():
    r = SharedResourceAutomaton(ResourceConfig(connectors=1, power_limit_kw=100, power_tiers=(0, 50, 100), curtailed_power_limit_kw=50))
    s = r.step(r.start_state, "connect")
    s = r.step(s, "power_start", 50)
    assert r.step(s, "grid_curtail") == ResourceState(1, 50, GridMode.CURTAILED)
    assert r.step(s, "power_start", 50) is None


def test_product_uses_sorted_multiset_state_and_lazy_successors():
    product = LazyStationProduct(2, SharedResourceAutomaton(ResourceConfig(connectors=1, power_limit_kw=50, power_tiers=(0, 50))))
    first = product.successors(product.initial_state)
    assert first
    assert all(t.target.session_states == tuple(sorted(t.target.session_states)) for t in first)
    assert product.metrics is None


def test_d9_six_sessions_three_connectors_and_power_cap():
    product = LazyStationProduct(6, SharedResourceAutomaton(ResourceConfig(connectors=3, power_limit_kw=150, power_tiers=(0, 50, 100, 150))))
    state = product.initial_state
    # Three sessions reach the physical cable state; the fourth is rejected.
    for _ in range(3):
        state = product.transition_state(state, "IDLE", "reserve_req")
        state = product.transition_state(state, "RESERVED", "auth_req")
        state = product.transition_state(state, "AUTH_PENDING", "auth_ok")
        state = product.transition_state(state, "AUTHORIZED", "plug_in")
        assert state is not None
        state = product.transition_state(state, "CABLE_DETECTED", "lock_ok")
        assert state is not None
        state = product.transition_state(state, "EV_CONNECTED", "ev_ready")
        assert state is not None
    assert product.transition_state(state, "IDLE", "reserve_req") is not None
    # Connector allocation prevents the fourth physical connection.
    fourth = product.transition_state(state, "RESERVED", "auth_req")
    fourth = product.transition_state(fourth, "AUTH_PENDING", "auth_ok")
    fourth = product.transition_state(fourth, "AUTHORIZED", "plug_in")
    assert fourth is None
    metrics = product.explore(max_states=5000)
    assert metrics.symmetry_reduced_state_count <= metrics.naive_state_count
    assert all(result.holds for result in check_invariants(state, product.resource.config))
