"""A deterministic discrete-event clock."""
from __future__ import annotations
from dataclasses import dataclass, field
import heapq
from itertools import count
from typing import Any, Callable, Optional

@dataclass(order=True, frozen=True)
class ClockEvent:
    time: float
    sequence: int
    callback: Callable[..., Any] = field(compare=False)
    payload: Any = field(default=None, compare=False)

class DiscreteEventClock:
    """Priority-queue event loop with a virtual (never sleeping) clock."""
    def __init__(self, start_time: float = 0.0) -> None:
        if start_time < 0: raise ValueError("start_time must be non-negative")
        self.now = float(start_time); self._sequence = count(); self._queue: list[ClockEvent] = []; self.processed = 0
    @property
    def pending(self) -> int: return len(self._queue)
    def schedule(self, delay: float, callback: Callable[..., Any], payload: Any = None) -> ClockEvent:
        if delay < 0: raise ValueError("delay must be non-negative")
        return self.schedule_at(self.now + delay, callback, payload)
    def schedule_at(self, timestamp: float, callback: Callable[..., Any], payload: Any = None) -> ClockEvent:
        if timestamp < self.now: raise ValueError("timestamp cannot be earlier than the current clock")
        event = ClockEvent(float(timestamp), next(self._sequence), callback, payload); heapq.heappush(self._queue, event); return event
    def run(self, until: Optional[float] = None, max_events: Optional[int] = None) -> int:
        if until is not None and until < self.now: raise ValueError("until cannot be earlier than the current clock")
        if max_events is not None and max_events < 0: raise ValueError("max_events must be non-negative")
        processed = 0
        while self._queue and (until is None or self._queue[0].time <= until) and (max_events is None or processed < max_events):
            event = heapq.heappop(self._queue); self.now = event.time
            if event.payload is None: event.callback()
            else: event.callback(event.payload)
            processed += 1; self.processed += 1
        if until is not None: self.now = max(self.now, float(until))
        return processed
    def clear(self) -> None: self._queue.clear()
