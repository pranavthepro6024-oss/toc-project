"""Kernel admission gate for untrusted schedule proposals (Scenario D12)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .heuristic import ScheduleItem, ScheduleProposal


@dataclass(frozen=True)
class AdmissionVerdict:
    admitted: bool
    schedule: tuple[ScheduleItem, ...]
    reason: str = ""
    counterexample: tuple[str, ...] = ()

    @property
    def accepted(self) -> bool:
        return self.admitted


class KernelAdmissionGate:
    def __init__(self, power_limit_kw: int = 150, queue_capacity: int | None = None) -> None:
        if power_limit_kw < 0:
            raise ValueError("power_limit_kw must be non-negative")
        self.power_limit_kw = power_limit_kw
        self.queue_capacity = queue_capacity

    def admit(self, proposal: ScheduleProposal | Iterable[ScheduleItem], *, fallback: Iterable[ScheduleItem] = ()) -> AdmissionVerdict:
        items = tuple(proposal.items if isinstance(proposal, ScheduleProposal) else proposal)
        if any(item.power_kw < 0 for item in items):
            return AdmissionVerdict(False, tuple(fallback), "negative power request", ("negative_power",))
        total = sum(item.power_kw for item in items)
        if total > self.power_limit_kw:
            return AdmissionVerdict(False, tuple(fallback), "I2 aggregate power ceiling exceeded",
                                    tuple([*(item.session_id for item in items), f"total={total}", f"limit={self.power_limit_kw}"]))
        if self.queue_capacity is not None and len(items) > self.queue_capacity:
            return AdmissionVerdict(False, tuple(fallback), "queue capacity exceeded", (f"length={len(items)}",))
        return AdmissionVerdict(True, items, "admitted")

    verify = admit


@dataclass(frozen=True)
class D12Result:
    unsafe: AdmissionVerdict
    safe: AdmissionVerdict

    @property
    def is_safe(self) -> bool:
        return not self.unsafe.admitted and self.safe.admitted


def run_scenario_d12() -> D12Result:
    original = tuple((ScheduleItem("ev-1", 50, 3), ScheduleItem("ev-2", 50, 2), ScheduleItem("ev-3", 50, 1)))
    unsafe = ScheduleProposal(original + (ScheduleItem("ev-4", 50, 0),), "aggressive-reorder")
    gate = KernelAdmissionGate(power_limit_kw=150, queue_capacity=4)
    return D12Result(gate.admit(unsafe, fallback=original), gate.admit(original))


AdmissionGate = KernelAdmissionGate
