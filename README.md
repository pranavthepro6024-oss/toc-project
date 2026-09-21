# Adaptive FSM-Based Fleet Charging Orchestrator (AFCO)

**Course:** Theory of Computation  
**Deliverables:** Verification Kernel + Simulator + Report + Demo + Patent Claim Draft  

## Overview
AFCO is a formally verified runtime orchestration system for electric vehicle fleet charging. Instead of relying on ad-hoc application heuristics and nested `if-else` business logic, AFCO encodes physical session lifecycles, grid limits, protocol translations, and safety rules strictly into formal language theory:
- **Canonical Session Automaton ($M_S$):** 18-state, 28-symbol DFA governing session lifecycles with explainable undefined transition rejections.
- **Safety Properties ($P_1$–$P_5$):** Minimal DFAs capturing forbidden language prefixes, enforced at runtime via synchronous product emptiness ($\mathcal{L}(M_S) \cap \mathcal{L}(M_U) = \emptyset$).
- **Multi-Bay Station Product:** Lazy product automaton $M_S^N \times R$ with symmetry reduction over unordered multisets.
- **Adaptive Recovery Engine:** Cost-weighted Dijkstra search to the nearest safe state ($\mathcal{S}$), gated by property verification.
- **Declarative Protocol Adapters:** Mealy transducers normalizing vendor protocols (OCPP 1.6-J, 2.0.1, CHAdeMO) via YAML declarations.
- **Queue Models:** Bounded counter automata and a formal adversary game demonstrating the Pumping Lemma for regular languages.

## Project Structure
```
afco/
  automata/     # Core language algorithms (DFA, NFA, Hopcroft, Product, Transducer)
  session/      # 18-state canonical session DFA
  station/      # Multi-bay lazy composition and symmetry reduction
  verify/       # Model checking & safety property intersection
  recovery/     # Dijkstra safe-state recovery engine
  adapters/     # Protocol normalization transducers and YAML loaders
  queue/        # Counter automaton, PDA, and Pumping Lemma proofs
  optimizer/    # Untrusted heuristic scheduler + kernel admission gate
  sim/          # Discrete-event simulation and fault injection
  ui/           # FastAPI web dashboard and live Graphviz rendering
tests/          # Unit, hypothesis property-based, and scenario regression tests
```

## Quickstart

### Installation
```bash
pip install -r requirements.txt
pip install -e .
```

### Running Tests
```bash
pytest -v
```
