"""Intersection-Emptiness Decision Procedure and Safety Checker.

Core theorem (from §13):
    L(M_S) ∩ L(M_{U,k}) = ∅  ↔  Reach(F_prod) = ∅

where F_prod = F_S × F_{U,k} in the synchronous product M_S × M_{U,k}.

The checker:
1. Builds the product DFA via `product_dfa(m_s, m_unsafe, mode="intersection")`.
2. Tests emptiness by checking whether the product DFA has any reachable
   accepting state (using forward_reachable from reachability.py).
3. If the intersection is non-empty, extracts the shortest counterexample
   trace via BFS parent-pointer traceback (explain.py).
4. Synthesizes the shortest repair path from the violation state back to
   the nearest safe M_S accepting state.
5. Returns a structured VerificationVerdict (§16).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

from afco.automata.dfa import DFA
from afco.automata.product import product_dfa
from afco.automata.reachability import forward_reachable
from afco.session.instance import VerificationVerdict, find_shortest_repair_path
from afco.verify.explain import extract_counterexample
from afco.verify.properties import ALL_PROPERTY_BUILDERS


# ---------------------------------------------------------------------------
# Per-property safety report
# ---------------------------------------------------------------------------

@dataclass
class SafetyReport:
    """Aggregated safety report across all properties P1–P5.

    Attributes:
        verdicts: Mapping from property name → VerificationVerdict.
        is_globally_safe: True iff every property check passes.
    """
    verdicts: Dict[str, VerificationVerdict]
    is_globally_safe: bool

    def format_report(self) -> str:
        """Render a human-readable multi-property safety summary."""
        lines = ["=" * 60, "AFCO MULTI-PROPERTY SAFETY REPORT", "=" * 60]
        for prop_name, verdict in self.verdicts.items():
            status = "✓ SAFE" if verdict.is_safe else "✗ VIOLATION"
            lines.append(f"\n[{prop_name}]  {status}")
            if not verdict.is_safe:
                lines.append(verdict.format_report())
        lines.append("\n" + "=" * 60)
        if self.is_globally_safe:
            lines.append("OVERALL: SAFE — all properties verified.")
        else:
            failed = [p for p, v in self.verdicts.items() if not v.is_safe]
            lines.append(f"OVERALL: UNSAFE — violated properties: {failed}")
        lines.append("=" * 60)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core intersection-emptiness check
# ---------------------------------------------------------------------------

def check_safety(
    session_dfa: DFA,
    property_dfa: DFA,
    property_name: str = "Unknown",
) -> VerificationVerdict:
    """Check whether L(session_dfa) ∩ L(property_dfa) = ∅.

    Implements the automata-theoretic model checking decision procedure:

        Safe ↔ Reach(F_prod) = ∅

    where F_prod = F_S × F_{U,k} in the synchronous product.

    Args:
        session_dfa: The canonical session DFA M_S.
        property_dfa: The forbidden-language DFA M_{U,k} for a single property.
        property_name: Label used in the verdict (e.g. "P2_NoLiveDisconnect").

    Returns:
        VerificationVerdict with is_safe=True if the intersection is empty,
        otherwise containing the shortest counterexample and a repair path.
    """
    # Step 1: Build synchronous product M_S × M_{U,k}
    # Accepting states = F_S × F_{U,k}  (intersection semantics)
    prod = product_dfa(session_dfa, property_dfa, mode="intersection")

    # Step 2: Decide emptiness — is any accepting state reachable?
    reachable = forward_reachable(prod)
    reachable_accepting = prod.accepting_states & reachable

    if not reachable_accepting:
        # Property holds — language intersection is empty
        return VerificationVerdict(
            is_safe=True,
            violated_property=None,
            counterexample=None,
            repair_path=[],
        )

    # Step 3: Property violated — extract shortest counterexample via BFS
    counterexample = extract_counterexample(prod)

    # Step 4: Determine the session state after replaying the counterexample
    # (used to synthesize the repair path in M_S)
    session_state_at_violation = _replay_to_session_state(
        session_dfa, counterexample or []
    )

    # Step 5: Synthesize repair path from the violating session state
    repair_path = find_shortest_repair_path(session_dfa, session_state_at_violation)

    return VerificationVerdict(
        is_safe=False,
        failure_index=len(counterexample) if counterexample is not None else None,
        rejected_symbol=counterexample[-1] if counterexample else None,
        violated_property=property_name,
        admissible_symbols=session_dfa.admissible_symbols(session_state_at_violation),
        counterexample=counterexample,
        repair_path=repair_path,
    )


def check_all_properties(session_dfa: DFA) -> SafetyReport:
    """Run the intersection-emptiness check against all properties P1–P5.

    Args:
        session_dfa: The canonical session DFA M_S.

    Returns:
        A SafetyReport aggregating individual VerificationVerdicts.
    """
    verdicts: Dict[str, VerificationVerdict] = {}

    for prop_name, builder in ALL_PROPERTY_BUILDERS.items():
        prop_dfa = builder()
        verdict = check_safety(session_dfa, prop_dfa, property_name=prop_name)
        verdicts[prop_name] = verdict

    is_globally_safe = all(v.is_safe for v in verdicts.values())
    return SafetyReport(verdicts=verdicts, is_globally_safe=is_globally_safe)


# ---------------------------------------------------------------------------
# Helper: replay counterexample through M_S to find session state
# ---------------------------------------------------------------------------

def _replay_to_session_state(dfa: DFA, word: List[str]) -> object:
    """Walk the session DFA along `word` and return the terminal state.

    If a transition is undefined mid-word (partial δ), returns the state
    at the point of failure.
    """
    current = dfa.start_state
    for sym in word:
        nxt = dfa.step(current, sym)
        if nxt is None:
            break
        current = nxt
    return current
