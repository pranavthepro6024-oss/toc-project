"""Formal conformance checks for declarative protocol adapters."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

from afco.automata.transducer import MealyTransducer
from afco.session.alphabet import ALPHABET, ACCEPTING_STATES
from afco.session.canonical import get_canonical_dfa


@dataclass(frozen=True)
class ConformanceReport:
    is_conforming: bool
    errors: tuple[str, ...] = ()
    checked_transitions: int = 0

    @property
    def valid(self) -> bool:
        return self.is_conforming

    def __bool__(self) -> bool:
        return self.is_conforming


def _reachable(machine: MealyTransducer) -> set[object]:
    seen = {machine.start_state}
    todo = [machine.start_state]
    while todo:
        state = todo.pop()
        for (source, _), target in machine.transitions.items():
            if source == state and target not in seen:
                seen.add(target)
                todo.append(target)
    return seen


def check_conformance(machine: MealyTransducer) -> ConformanceReport:
    """Check total output mapping, output range, valid prefixes and trap freedom.

    Totality is defined over every transition declared by the vendor: each
    declared edge must have an explicit ``emit`` entry (``null`` means epsilon).
    Prefix and trap checks explore the finite product of vendor and canonical
    states, so cyclic vendor protocols terminate deterministically.
    """
    errors: list[str] = []
    canonical = get_canonical_dfa()
    for key in machine.transitions:
        if key not in machine.emissions:
            errors.append(f"missing emission for transition {key!r}")
        output = machine.emissions.get(key)
        if output is not None and output not in ALPHABET:
            errors.append(f"output {output!r} is outside canonical alphabet")
    if machine.start_state not in machine.states:
        errors.append("initial state is not declared")

    # Product exploration validates every reachable emitted canonical prefix.
    # None emissions preserve the canonical state.
    queue = deque([(machine.start_state, canonical.start_state)])
    seen = set(queue)
    while queue:
        vendor_state, canonical_state = queue.popleft()
        for (source, event), target in machine.transitions.items():
            if source != vendor_state:
                continue
            output = machine.emissions.get((source, event))
            next_canonical = canonical_state if output is None else canonical.step(canonical_state, output)
            if next_canonical is None:
                errors.append(f"output prefix becomes invalid: {source!r} + {event!r} -> {output!r}")
                continue
            pair = (target, next_canonical)
            if pair not in seen:
                seen.add(pair)
                queue.append(pair)

    # A reachable vendor state must not be a dead end with respect to canonical
    # completion. This is deliberately structural and does not require every
    # vendor state to be accepting.
    reverse = {state: set() for state in canonical.states}
    for (source, symbol), target in canonical.transitions.items():
        reverse[target].add(source)
    co_reachable = set(ACCEPTING_STATES)
    todo = list(co_reachable)
    while todo:
        state = todo.pop()
        for previous in reverse[state]:
            if previous not in co_reachable:
                co_reachable.add(previous)
                todo.append(previous)
    for vendor_state, canonical_state in seen:
        if canonical_state not in co_reachable:
            errors.append(f"trap freedom violated at vendor={vendor_state!r}, canonical={canonical_state!r}")

    return ConformanceReport(not errors, tuple(dict.fromkeys(errors)), len(machine.transitions))


validate_adapter = check_conformance
