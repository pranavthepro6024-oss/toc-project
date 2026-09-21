"""Domain-weighted edge costs for recovery search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from afco.session.alphabet import (
    CONTACTORS_OPEN, METER_FINAL, PAY_FAIL, PAY_OK, POWER_RAMP_DOWN,
    POWER_STOP, RESET_CMD, UNLOCK_OK, UNLOCK_REQ,
)


@dataclass(frozen=True)
class RecoveryCost:
    """Evidence-dependent penalties used by :class:`TransitionCostModel`."""

    unbilled_energy_risk: float = 25.0
    slot_blockage: float = 5.0
    contactor_wear: float = 2.0
    communication: float = 1.0


class TransitionCostModel:
    """Positive edge-cost model; callers may override symbol costs."""

    def __init__(self, costs: RecoveryCost | None = None,
                 overrides: Mapping[str, float] | None = None) -> None:
        self.costs = costs or RecoveryCost()
        self.overrides = dict(overrides or {})

    def __call__(self, from_state: str, symbol: str, to_state: str) -> float:
        if symbol in self.overrides:
            value = self.overrides[symbol]
        elif symbol == RESET_CMD:
            value = self.costs.slot_blockage
        elif symbol in {POWER_STOP, POWER_RAMP_DOWN, CONTACTORS_OPEN}:
            value = self.costs.contactor_wear
        elif symbol in {UNLOCK_REQ, UNLOCK_OK}:
            value = self.costs.contactor_wear
        elif symbol in {PAY_FAIL, PAY_OK, METER_FINAL}:
            value = self.costs.communication
        else:
            value = 1.0
        return max(float(value), 0.000001)
