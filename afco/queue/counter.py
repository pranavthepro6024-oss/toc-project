"""A bounded FIFO queue represented as a finite counter automaton."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional


class QueueOperation(str, Enum):
    ENQUEUE = "enq"
    DEQUEUE = "deq"


@dataclass(frozen=True)
class CounterTrace:
    accepted: bool
    states: tuple[int, ...]
    failure_index: Optional[int] = None


class BoundedQueueCounter:
    """DFA with exactly ``capacity + 1`` occupancy states (0 through K)."""

    def __init__(self, capacity: int) -> None:
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 0:
            raise ValueError("capacity must be a non-negative integer")
        self.capacity = capacity
        self.states = frozenset(range(capacity + 1))
        self.start_state = 0
        self.accepting_states = self.states

    def step(self, state: int, symbol: QueueOperation | str) -> Optional[int]:
        if state not in self.states:
            raise ValueError(f"invalid occupancy state: {state}")
        symbol = QueueOperation(symbol)
        if symbol is QueueOperation.ENQUEUE:
            return state + 1 if state < self.capacity else None
        return state - 1 if state > 0 else None

    transition = step

    def trace(self, word: Iterable[QueueOperation | str]) -> CounterTrace:
        state = self.start_state
        states = [state]
        for index, symbol in enumerate(word):
            state = self.step(state, symbol)
            if state is None:
                return CounterTrace(False, tuple(states), index)
            states.append(state)
        return CounterTrace(True, tuple(states))

    def accepts(self, word: Iterable[QueueOperation | str]) -> bool:
        return self.trace(word).accepted

    def admissible_symbols(self, state: int) -> frozenset[str]:
        return frozenset(symbol.value for symbol in QueueOperation if self.step(state, symbol) is not None)

    @property
    def state_count(self) -> int:
        return len(self.states)


BoundedCounterAutomaton = BoundedQueueCounter
