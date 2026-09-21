"""Automata and formal language algorithms package."""

from afco.automata.dfa import DFA, TraceResult
from afco.automata.nfa import NFA, EPSILON
from afco.automata.subset import subset_construction
from afco.automata.reachability import (
    forward_reachable,
    unreachable_states,
    backward_reachable,
    trap_states,
)
from afco.automata.minimize import minimize_dfa
from afco.automata.product import product_dfa
from afco.automata.transducer import MealyTransducer, TransductionResult
from afco.automata.render import dfa_to_dot, render_dfa_svg

__all__ = [
    "DFA",
    "TraceResult",
    "NFA",
    "EPSILON",
    "subset_construction",
    "forward_reachable",
    "unreachable_states",
    "backward_reachable",
    "trap_states",
    "minimize_dfa",
    "product_dfa",
    "MealyTransducer",
    "TransductionResult",
    "dfa_to_dot",
    "render_dfa_svg",
]
