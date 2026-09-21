"""Strict YAML-to-Mealy adapter loader.

Adapter files are data only: no Python callbacks or executable mappings are
accepted.  The resulting object can be used directly by the runtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from afco.automata.transducer import MealyTransducer
from afco.adapters.conformance import ConformanceReport, check_conformance


class AdapterLoadError(ValueError):
    """Raised when an adapter is malformed or fails formal conformance."""


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdapterLoadError(f"{name} must be a mapping")
    return value


def _build(data: Mapping[str, Any], *, validate: bool = True) -> MealyTransducer:
    adapter = _require_mapping(data.get("adapter"), "adapter")
    states_raw = data.get("states")
    transitions_raw = data.get("transitions")
    if not isinstance(states_raw, list) or not states_raw or not all(isinstance(s, str) for s in states_raw):
        raise AdapterLoadError("states must be a non-empty list of strings")
    if len(set(states_raw)) != len(states_raw):
        raise AdapterLoadError("states contains duplicates")
    if not isinstance(transitions_raw, list):
        raise AdapterLoadError("transitions must be a list")

    start = adapter.get("initial_state")
    if not isinstance(start, str):
        raise AdapterLoadError("adapter.initial_state is required")
    inputs = set()
    outputs = set()
    transitions = {}
    emissions = {}
    for index, row in enumerate(transitions_raw):
        item = _require_mapping(row, f"transitions[{index}]")
        required = ("from", "event", "to", "emit")
        missing = [key for key in required if key not in item]
        if missing:
            raise AdapterLoadError(f"transitions[{index}] missing {', '.join(missing)}")
        source, event, target, emit = (item[key] for key in required)
        if not all(isinstance(x, str) for x in (source, event, target)):
            raise AdapterLoadError(f"transitions[{index}] from/event/to must be strings")
        if emit is not None and not isinstance(emit, str):
            raise AdapterLoadError(f"transitions[{index}].emit must be a string or null")
        key = (source, event)
        if key in transitions:
            raise AdapterLoadError(f"duplicate transition for state/event {key!r}")
        inputs.add(event)
        if emit is not None:
            outputs.add(emit)
        transitions[key] = target
        emissions[key] = emit

    try:
        machine = MealyTransducer(
            states=frozenset(states_raw),
            input_alphabet=frozenset(inputs),
            output_alphabet=frozenset(outputs),
            transitions=transitions,
            emissions=emissions,
            start_state=start,
        )
    except ValueError as exc:
        raise AdapterLoadError(str(exc)) from exc
    if validate:
        report = check_conformance(machine)
        if not report.is_conforming:
            raise AdapterLoadError("adapter failed conformance: " + "; ".join(report.errors))
    return machine


def load_adapter_text(text: str, *, validate: bool = True) -> MealyTransducer:
    """Parse one adapter from YAML text."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise AdapterLoadError(f"invalid YAML: {exc}") from exc
    return _build(_require_mapping(data, "document"), validate=validate)


def load_adapter(path: str | Path, *, validate: bool = True) -> MealyTransducer:
    """Hot-load and validate an adapter from a YAML file."""
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise AdapterLoadError(f"cannot read adapter {source}: {exc}") from exc
    return load_adapter_text(text, validate=validate)


def load_adapter_with_report(path: str | Path) -> tuple[MealyTransducer | None, ConformanceReport]:
    """Convenience API for callers that want a verdict instead of an exception."""
    try:
        machine = load_adapter(path)
    except AdapterLoadError as exc:
        return None, ConformanceReport(False, (str(exc),))
    return machine, check_conformance(machine)
