"""Fleet simulation and soundness checks built on SessionInstance."""
from __future__ import annotations
from dataclasses import dataclass
import random
from typing import Optional
from afco.session.instance import SessionInstance
from afco.session.alphabet import ALPHABET
from .clock import DiscreteEventClock

@dataclass(frozen=True)
class SimulationEvent:
    time: float; session_id: str; symbol: str; accepted: bool; state_before: str; state_after: str
    failure_index: Optional[int] = None; error: Optional[str] = None

@dataclass(frozen=True)
class SimulationResult:
    events: tuple[SimulationEvent, ...]; accepted_events: int; rejected_events: int; final_states: dict[str, str]
    @property
    def is_safe(self) -> bool:
        return all(event.accepted or event.state_before == event.state_after for event in self.events)

class FleetSimulator:
    """Run timestamped session events while preserving rejection semantics."""
    def __init__(self, *, clock: Optional[DiscreteEventClock] = None) -> None:
        self.clock = clock or DiscreteEventClock(); self.sessions: dict[str, SessionInstance] = {}; self.events: list[SimulationEvent] = []
    def add_session(self, session_id: str, session: Optional[SessionInstance] = None) -> SessionInstance:
        if session_id in self.sessions: raise ValueError(f"session already exists: {session_id}")
        instance = session or SessionInstance(session_id=session_id); self.sessions[session_id] = instance; return instance
    def schedule(self, session_id: str, symbol: str, at: float) -> None:
        if session_id not in self.sessions: self.add_session(session_id)
        if at < self.clock.now: raise ValueError("event time cannot be earlier than the clock")
        self.clock.schedule_at(at, self._apply, (session_id, symbol))
    def _apply(self, item: tuple[str, str]) -> None:
        session_id, symbol = item; session = self.sessions[session_id]; before = session.current_state; accepted = session.step(symbol); verdict = session.last_verdict
        self.events.append(SimulationEvent(self.clock.now, session_id, symbol, accepted, before, session.current_state, None if accepted or verdict is None else verdict.failure_index, None if accepted else (verdict.violated_property if verdict else "rejected")))
    def run(self, until: Optional[float] = None, max_events: Optional[int] = None) -> SimulationResult:
        self.clock.run(until=until, max_events=max_events); accepted = sum(event.accepted for event in self.events)
        return SimulationResult(tuple(self.events), accepted, len(self.events) - accepted, {key: value.current_state for key, value in self.sessions.items()})
    def reset(self) -> None:
        self.clock.reset(); self.events.clear(); self.sessions.clear()

def fuzz_soundness(*, trials: int = 100_000, seed: int = 0) -> dict[str, int | bool]:
    """Inject random symbols and assert undefined transitions are side-effect free."""
    if trials < 0: raise ValueError("trials must be non-negative")
    rng = random.Random(seed); symbols = tuple(sorted(ALPHABET)); rejected = 0
    for index in range(trials):
        session = SessionInstance(session_id=f"fuzz-{index}"); before = session.current_state; accepted = session.step(rng.choice(symbols))
        if not accepted:
            rejected += 1
            if session.current_state != before or session.history: return {"trials": index + 1, "rejected": rejected, "sound": False}
    return {"trials": trials, "rejected": rejected, "sound": True}
