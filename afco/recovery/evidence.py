"""Sensor and gateway evidence consumed by the recovery policy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
    """Immutable evidence snapshot attached to a recovery request."""

    meter_delta: float = 0.0
    cable_interlock: bool = False
    link_integrity: bool = True
    payment_status: str = "unknown"

    @property
    def meter_verified(self) -> bool:
        return self.meter_delta <= 0.0

    @property
    def payment_guaranteed(self) -> bool:
        return self.payment_status in {"paid", "guaranteed", "waived"}
