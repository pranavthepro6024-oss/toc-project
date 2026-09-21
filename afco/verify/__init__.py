"""Verification Layer — Automata-theoretic safety verification for AFCO.

Provides:
- Safety properties P1–P5 encoded as forbidden DFAs (M_{U,k}).
- Intersection-emptiness decision procedure: L(M_S) ∩ L(M_{U,k}) = ∅.
- Counterexample extraction via BFS parent-pointer traceback.
- Repair path synthesis from current state to nearest safe state.
- Standardized VerificationVerdict with full explainability.
"""

from afco.verify.properties import (
    build_property_p1,
    build_property_p2,
    build_property_p3,
    build_property_p4_placeholder,
    build_property_p5,
    ALL_PROPERTY_BUILDERS,
)
from afco.verify.checker import (
    check_safety,
    check_all_properties,
    SafetyReport,
)
from afco.verify.explain import (
    extract_counterexample,
    synthesize_repair_path,
)

__all__ = [
    # Property builders
    "build_property_p1",
    "build_property_p2",
    "build_property_p3",
    "build_property_p4_placeholder",
    "build_property_p5",
    "ALL_PROPERTY_BUILDERS",
    # Checker
    "check_safety",
    "check_all_properties",
    "SafetyReport",
    # Explainability
    "extract_counterexample",
    "synthesize_repair_path",
]
