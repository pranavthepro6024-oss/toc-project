# AFCO — Step-by-Step Build Roadmap

This document outlines the step-by-step development sequence for the **Adaptive FSM-Based Fleet Charging Orchestrator (AFCO)**. Each step is self-contained and terminates in a verification checkpoint.

---

## Progress Overview

- [x] **Step 0: Skeleton & Dependencies**
- [x] **Step 1: Core Automata Primitives (DFA, NFA, Hopcroft, BFS)**
- [x] **Step 2: Canonical Session Automaton ($M_S$, 18 States, 28 Symbols)**
- [ ] **Step 3: Formal Verification Layer (Properties $P_1$–$P_5$ & Model Checking)**
- [x] **Step 4: Shared Station Resource & Lazy Product Composition**
- [ ] **Step 5: Adaptive Recovery Engine (Dijkstra + Safe State $\mathcal{S}$)**
- [x] **Step 6: Declarative Protocol Adapters (Mealy Transducers & YAML)**
- [x] **Step 7: Queuing Automata (Counter, PDA, Pumping Lemma Demo)**
- [x] **Step 8: Simulation Engine, Live UI & Soundness Fuzzing**
- [x] **Step 9: Synthesis, Reproducible Report & Patent Audit**

---

### Step 0: Project Setup & Tooling Skeleton
- [x] Create `pyproject.toml` and `requirements.txt`
- [x] Setup package structure `afco/` and test suite `tests/`
- [x] Verify test runner discovery with `pytest`
- **Checkpoint 0:** `pytest` runs and discovers test environment cleanly. (PASSED)

---

### Step 1: Core Automata Primitives (`afco/automata/`)
- [x] `dfa.py`: 5-tuple DFA, `accepts()`, explainable `trace()` with failure index and admissible symbols
- [x] `nfa.py`: NFA with $\epsilon$-transitions and $\epsilon$-closure
- [x] `subset.py`: Powerset construction (NFA $\to$ DFA) with frozenset state labels
- [x] `reachability.py`: Forward BFS (unreachability) and backward BFS (trap detection)
- [x] `minimize.py`: Hopcroft minimization adapted for partial transition functions
- [x] `render.py`: Graphviz `.dot` and `.svg` export
- **Checkpoint 1:** 4 textbook DFAs pass; `hypothesis` test confirms minimization preserves language recognition. (PASSED - 12/12 tests)

---

### Step 2: Canonical Session Automaton ($M_S$) (`afco/session/`)
- [x] `alphabet.py`: 28 formal symbols and 18 lifecycle states ($Q_S$)
- [x] `canonical.py`: Complete transition table $\delta_S$
- [x] Verify structural reachability (0 unreachables, `FAULT_TERMINAL` as only trap)
- [x] `instance.py`: Session runtime instance and history tracking
- [x] Implement Scenarios **D1** (Happy Path) and **D2** (Billing-Skip Rejection)
- **Checkpoint 2:** D1 accepts; D2 rejects with exact failure index, admissible symbols, and repair path. (PASSED - 13/13 tests)

---

### Step 3: Verification Layer & Model Checking (`afco/verify/`)
- [ ] `properties.py`: Encode safety properties $P_1$–$P_5$ as forbidden DFAs
- [ ] `checker.py`: Synchronous product $M_S \times M_U$ & intersection-emptiness check
- [ ] `explain.py`: Shortest counterexample witness extraction & repair path synthesis
- [ ] Implement Scenario **D3** (Mechanical interlock violation rejected by $P_2$)
- **Checkpoint 3:** D3 is caught by model-checking emptiness test with counterexample.

---

### Step 4: Shared Station Resource & Lazy Composition (`afco/station/`)
- [x] `resource.py`: Shared resource automaton $R$ (connectors, kW tiers, grid mode)
- [x] `composite.py`: Lazy product $M_S^N \times R$ with on-demand successor generation
- [x] Symmetry reduction using multiset state hashing (`Counter` / sorted state tuples)
- [ ] `invariants.py`: Invariants $I_1$–$I_5$ as composite state predicates
- [x] Implement Scenario **D9** (6 vehicles, 3 connectors, 150 kW limit)
- **Checkpoint 4:** D9 runs without state explosion; state space reduction metrics logged. (PASSED)

---

### Step 5: Adaptive Recovery Engine (`afco/recovery/`)
- [ ] `safe_states.py`: Admissible safe state set $\mathcal{S} \subset Q_S$
- [ ] `cost.py`: Domain-weighted transition edge cost model
- [ ] `engine.py`: Dijkstra recovery search $\rho(q, \text{evidence}) \to s^* \in \mathcal{S}$
- [ ] Verification gate: candidate recovery path verified against $P_1$–$P_5$
- [ ] Implement Scenarios **D4**, **D5**, **D6**, **D7**, and **D8** (unbilled bypass rejected)
- **Checkpoint 5:** Regression suite for D4–D8 passes.

---

### Step 6: Protocol Adapters & Transducers (`afco/adapters/`)
- [ ] `transducer.py`: Mealy finite-state transducer data model
- [ ] `loader.py`: YAML parser converting vendor specs into Mealy machines
- [ ] `conformance.py`: Verify totality, range soundness, prefix containment, and trap freedom
- [ ] Author `ocpp16.yaml`, `ocpp201.yaml`, `chademo.yaml`, and `malformed_test.yaml`
- [ ] Implement Scenarios **D10** (Dynamic hot-load) and **D11** (Malformed adapter rejected)
- **Checkpoint 6:** D10 translates runtime events without code changes; D11 refuses broken adapter.

---

### Step 7: Queue Automata & Optimizer Gate (`afco/queue/`, `afco/optimizer/`)
- [ ] `counter.py`: Bounded queue counter automaton ($K+1$ states)
- [ ] `pumping.py`: Programmatic Pumping Lemma adversary demo proving unbounded queue non-regular
- [ ] `pda.py`: Pushdown Automaton for nested fleet hold reservations
- [ ] `heuristic.py` & `gate.py`: Untrusted optimizer proposal gated by kernel invariants
- [ ] Implement Scenario **D12** (Unsafe schedule rejected, safe schedule admitted)
- **Checkpoint 7:** Pumping lemma proof passes; D12 rejects unsafe proposals with counterexample.

---

### Step 8: Simulator, Live UI & Soundness Fuzzing (`afco/sim/`, `afco/ui/`)
- [ ] `clock.py`: Discrete event loop
- [ ] `ui/`: FastAPI backend + live web dashboard (connector grid, trace log, Graphviz active state SVG)
- [ ] Soundness fuzzing test ($10^5$ randomized events $\to$ 0 false accepts)
- [ ] Implement Scenario **D13** (Full fleet stress test executable via UI)
- [ ] Automated generation of report metrics, tables, and figures
- **Checkpoint 8:** Web dashboard runs D1–D13 live; fuzz test confirms 100% soundness.
---

### Step 9: Synthesis, Reproducible Report & Patent Audit (`afco/report/`)
- [x] `generate.py`: execute D3, D9, D13, and soundness fuzzing to produce a machine-readable evidence bundle
- [x] Generate Markdown metrics and a deterministic timeout-and-reboot baseline comparison
- [x] Audit independent patent claims against concrete modules and automated tests
- [x] Add CLI output options for JSON and Markdown artifacts
- **Checkpoint 9:** The report generator runs from the repository, emits zero-false-accept evidence, and fails if claim evidence paths are missing. (PASSED)
