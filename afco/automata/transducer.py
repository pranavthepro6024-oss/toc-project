"""Mealy Finite-State Transducer implementation.

Used by protocol adapters to translate vendor-specific message sequences
into canonical session symbols (Sigma_S).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class TransductionResult:
    """Result of running an input word through a Mealy Transducer."""
    success: bool
    output_word: List[Any]
    state_path: List[Any]
    failure_index: Optional[int] = None
    rejected_input: Optional[Any] = None
    terminal_state: Optional[Any] = None


@dataclass(frozen=True)
class MealyTransducer:
    """A Mealy Machine Transducer (Q, Sigma_in, Sigma_out, delta, lambda, q0).

    Attributes:
        states: Set of states Q.
        input_alphabet: Input symbol alphabet Sigma_in.
        output_alphabet: Output symbol alphabet Sigma_out.
        transitions: State transitions delta: Q x Sigma_in -> Q.
        emissions: Output emissions lambda: Q x Sigma_in -> Sigma_out U {None}.
        start_state: Initial state q0.
    """
    states: FrozenSet[Any]
    input_alphabet: FrozenSet[Any]
    output_alphabet: FrozenSet[Any]
    transitions: Dict[Tuple[Any, Any], Any]
    emissions: Dict[Tuple[Any, Any], Optional[Any]]
    start_state: Any

    def __post_init__(self) -> None:
        """Validate transducer invariants."""
        if self.start_state not in self.states:
            raise ValueError(f"Start state '{self.start_state}' not in states Q.")
        for (q, a), tgt in self.transitions.items():
            if q not in self.states:
                raise ValueError(f"Transition source '{q}' not in Q.")
            if a not in self.input_alphabet:
                raise ValueError(f"Input symbol '{a}' not in Sigma_in.")
            if tgt not in self.states:
                raise ValueError(f"Transition target '{tgt}' not in Q.")
        for (q, a), out in self.emissions.items():
            if (q, a) not in self.transitions:
                raise ValueError(f"Emission defined for non-existent transition {(q, a)}.")
            if out is not None and out not in self.output_alphabet:
                raise ValueError(f"Output symbol '{out}' not in Sigma_out.")

    def step(self, state: Any, input_symbol: Any) -> Tuple[Optional[Any], Optional[Any]]:
        """Compute (delta(state, input_symbol), lambda(state, input_symbol))."""
        next_state = self.transitions.get((state, input_symbol))
        if next_state is None:
            return None, None
        emission = self.emissions.get((state, input_symbol))
        return next_state, emission

    def transduce(self, input_word: Iterable[Any]) -> TransductionResult:
        """Process an input sequence and emit translated canonical symbols."""
        current = self.start_state
        state_path = [current]
        output_word: List[Any] = []

        for idx, sym in enumerate(input_word):
            next_state, emission = self.step(current, sym)
            if next_state is None:
                return TransductionResult(
                    success=False,
                    output_word=output_word,
                    state_path=state_path,
                    failure_index=idx,
                    rejected_input=sym,
                    terminal_state=current,
                )
            if emission is not None:
                output_word.append(emission)
            current = next_state
            state_path.append(current)

        return TransductionResult(
            success=True,
            output_word=output_word,
            state_path=state_path,
            failure_index=None,
            rejected_input=None,
            terminal_state=current,
        )
