"""D13: deterministic full-fleet stress scenario."""
from __future__ import annotations
from dataclasses import dataclass
from .simulator import FleetSimulator, SimulationResult
from afco.session.scenarios import D1_CANONICAL_TRACE

@dataclass(frozen=True)
class D13Result:
    simulation: SimulationResult
    fleet_size: int
    @property
    def is_safe(self) -> bool:
        return self.simulation.is_safe and self.simulation.rejected_events == 0

def run_scenario_d13(*, fleet_size: int = 24) -> D13Result:
    """Run canonical happy paths for a concurrent fleet through the event loop."""
    if fleet_size < 1: raise ValueError("fleet_size must be positive")
    simulator = FleetSimulator()
    for vehicle in range(fleet_size):
        session_id = f"D13-{vehicle:03d}"
        for offset, symbol in enumerate(D1_CANONICAL_TRACE):
            simulator.schedule(session_id, symbol, float(offset) + vehicle * 0.001)
    return D13Result(simulator.run(), fleet_size)
