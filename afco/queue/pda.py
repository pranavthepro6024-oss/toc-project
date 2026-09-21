"""A small nondeterministic PDA for nested fleet reservation holds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class StackTransition:
    state: str
    symbol: str
    stack_top: str
    next_state: str
    replacement: tuple[str, ...]


class PushdownAutomaton:
    """Recognizes properly nested ``hold``/``release`` reservation events."""

    def __init__(self, hold_symbol: str = "hold", release_symbol: str = "release", stack_marker: str = "H") -> None:
        self.hold_symbol, self.release_symbol, self.stack_marker = hold_symbol, release_symbol, stack_marker
        self.start_state = "q"

    def step(self, stack: tuple[str, ...], symbol: str) -> tuple[str, ...] | None:
        if symbol == self.hold_symbol:
            return stack + (self.stack_marker,)
        if symbol == self.release_symbol:
            return stack[:-1] if stack and stack[-1] == self.stack_marker else None
        raise ValueError(f"unknown PDA input: {symbol}")

    transition = step

    def run(self, word: Iterable[str]) -> tuple[bool, tuple[str, ...], int | None]:
        stack: tuple[str, ...] = ()
        for index, symbol in enumerate(word):
            stack = self.step(stack, symbol)
            if stack is None:
                return False, (), index
        return not stack, stack, None

    def accepts(self, word: Iterable[str]) -> bool:
        return self.run(word)[0]

    def transitions(self, state: str = "q") -> tuple[StackTransition, ...]:
        return (
            StackTransition(state, self.hold_symbol, "any", state, (self.stack_marker, "any")),
            StackTransition(state, self.release_symbol, self.stack_marker, state, ()),
        )


PDA = PushdownAutomaton
