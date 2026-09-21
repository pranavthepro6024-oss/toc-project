# AFCO — Implementation Plan

**Project:** Adaptive FSM-Based Fleet Charging Orchestrator (AFCO)  
**Course:** Theory of Computation  
**Deliverables:** Verification Kernel + Simulator + Report + Demo + Patent Claim Draft  

---

## 1. Guiding Principles

Four rules that decide every design argument later. Write them down now so you don't relitigate them at 2 a.m. in week 5:

1. **The automaton is the product.** No business rule is ever written as an `if` in application code. If a rule cannot be expressed as a transition, a forbidden state, or a property automaton, it does not go in the kernel.
2. **Kernel is verified, everything else is not.** The optimizer, the UI, and the tariff arithmetic are all untrusted. They *propose*; the kernel *disposes*.
3. **Nothing is hand-listed.** Dead states, traps, unreachable states, admissible symbol sets — all computed from $\delta$. The moment you hardcode a list of "bad states," the project degrades into a normal app.
4. **Every rejection explains itself.** A verdict without a counterexample and a repair path is a bug.

---

## 2. Scope

### In Scope
- Canonical session DFA ($M_S$), fully specified and executable (18 states, 28 symbols).
- Property automata ($P_1$–$P_5$) for safety checks + intersection-emptiness decision procedure ($L(M_S) \cap L(M_{unsafe}) = \emptyset$).
- Lazy product automaton over $N$ concurrent sessions + shared resource automaton ($R$).
- Reachability, trap detection, and Hopcroft minimization (adapted for partial transition functions).
- Adaptive recovery engine ($\rho$: nearest safe state search via cost-weighted Dijkstra over the transition graph).
- At least 3 protocol adapters (NFA $\to$ DFA $\to$ minimization $\to$ Mealy transducer).
- Bounded queue as a counter automaton; PDA for nested fleet reservation stacks.
- Heuristic queue optimizer with kernel-gated formal admission.
- Simulator with fault injection, live state visualization, and session reports.
- Comprehensive project report + patent claim draft.

### Explicitly Out of Scope
- Real charging hardware, physical electrical contactors, live OCPP TCP sockets, and live payment gateways.
- Timed automata / dense real-time clock constraints (formalized as discrete tick transitions; continuous real-time listed as future work).
- Distributed multi-site consensus / Raft protocols.
- Cryptographic authentication algorithms (authentication is treated as an abstract formal symbol `auth_ok` / `auth_fail`, not an HMAC/RSA implementation).

> [!CAUTION]
> **Protect this boundary.** The most common way this project fails is drifting into building an EV charging app with a nice state diagram attached. Keep the focus strictly on formal language theory, automata algorithms, and model checking.

---

## 3. Tech Stack & Dependencies

| Layer | Choice | Rationale |
|---|---|---|
| **Kernel** | **Python 3.11+**, pure standard library, zero heavy dependencies | Algorithms must be crystal clear and inspectable — they are the graded artifact. |
| **Data Structures** | `dataclasses`, `frozenset`, `dict`, `enum` | Subset construction requires frozensets as first-class hashable keys. |
| **Testing** | `pytest` + `hypothesis` | Property-based testing directly verifies formal language invariants. |
| **Visualization** | **Graphviz** (`dot`) | Generates state transition diagrams before/after minimization and highlights active states. |
| **UI & Simulator** | **FastAPI + Vanilla HTML5/JS/CSS** (or Streamlit) | Real-time SSE/WebSocket trace stream, connector grid, queue display. |
| **Serialization** | JSON + PyYAML | Session traces, benchmark logs, and adapter specifications. |
| **Adapter Specs** | **Declarative YAML/JSON** | Proves vendor protocol mappings are data, not code (central to the patent claim). |
| **Report & Docs** | Markdown + Graphviz SVG export | Directly builds the report figures from running code. |

### Dependencies Specification (`pyproject.toml` / `requirements.txt`)
```toml
[project]
name = "afco"
version = "0.1.0"
description = "Adaptive FSM-Based Fleet Charging Orchestrator"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0.1",
    "graphviz>=0.20.1",
    "fastapi>=0.110.0",
    "uvicorn>=0.28.0",
    "pydantic>=2.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "hypothesis>=6.98.0",
    "pytest-cov>=4.1.0",
]
```

---

## 4. Repository Layout

```
toc-project/
├── .gitignore
├── README.md
├── pyproject.toml
├── requirements.txt
├── afco/
│   ├── __init__.py
│   ├── automata/               # Pure formal language & automata algorithms
│   │   ├── __init__.py
│   │   ├── dfa.py              # DFA definition, δ, accepts(), trace(), partial δ handling
│   │   ├── nfa.py              # NFA representation, ε-closure
│   │   ├── subset.py           # Powerset / subset construction (NFA → DFA)
│   │   ├── minimize.py         # Hopcroft minimization (partition refinement)
│   │   ├── reachability.py     # Forward/backward BFS, dead states, trap detection
│   │   ├── product.py          # Synchronous & lazy product construction (M1 × M2)
│   │   └── transducer.py       # Mealy finite-state transducer (input/output mappings)
│   ├── session/                # Canonical session automaton
│   │   ├── __init__.py
│   │   ├── canonical.py        # M_S formal definition: Q, Σ, δ, q0, F
│   │   ├── alphabet.py         # 28 formal symbols and categories
│   │   └── instance.py         # Session runtime instances and event history
│   ├── station/                # Multi-session station composition
│   │   ├── __init__.py
│   │   ├── resource.py         # Shared resource automaton R (power, connectors, grid)
│   │   ├── composite.py        # Lazy product M_S^N × R with symmetry reduction
│   │   └── invariants.py       # Station invariants I1–I5 as state predicates
│   ├── verify/                 # Automata-theoretic verification layer
│   │   ├── __init__.py
│   │   ├── properties.py       # Safety properties P1–P5 encoded as forbidden DFAs
│   │   ├── checker.py          # Intersection-emptiness decision procedure (L(M) ∩ L(P) = ∅)
│   │   └── explain.py          # Counterexample extraction & shortest repair path synthesis
│   ├── recovery/               # Adaptive recovery engine
│   │   ├── __init__.py
│   │   ├── safe_states.py      # Admissible safe state set S (physical, commercial, productive)
│   │   ├── cost.py             # Domain-weighted edge cost model
│   │   └── engine.py           # ρ: Dijkstra path search + safety property re-verification
│   ├── queue/                  # Formal queue models
│   │   ├── __init__.py
│   │   ├── counter.py          # Bounded queue as a finite counter automaton (K+1 states)
│   │   ├── pda.py              # Pushdown Automaton for nested fleet hold reservations
│   │   └── pumping.py          # Programmatic Pumping Lemma adversary demo
│   ├── optimizer/              # Untrusted scheduling heuristics
│   │   ├── __init__.py
│   │   ├── heuristic.py        # Priority / power flattening scheduler (proposes only)
│   │   └── gate.py             # Kernel admission gate validating optimizer proposals
│   ├── adapters/               # Declarative protocol translation
│   │   ├── __init__.py
│   │   ├── loader.py           # YAML → NFA/DFA → Minimized Mealy transducer
│   │   ├── conformance.py      # Conformance checking: totality, range, prefix validity
│   │   ├── ocpp16.yaml         # OCPP 1.6-J adapter definition
│   │   ├── ocpp201.yaml        # OCPP 2.0.1 adapter definition
│   │   ├── chademo.yaml        # CHAdeMO adapter definition
│   │   └── malformed_test.yaml # Intentionally non-conforming adapter for D11
│   ├── sim/                    # Simulation & fault injection harness
│   │   ├── __init__.py
│   │   ├── clock.py            # Discrete event loop
│   │   ├── faults.py           # Injectors for communication, electrical, billing faults
│   │   └── scenarios.py        # Executable definitions for scenarios D1–D13
│   ├── viz/                    # Visual rendering
│   │   ├── __init__.py
│   │   └── render.py           # Graphviz dot generation, active state highlight, SVG export
│   └── ui/                     # Web dashboard
│       ├── server.py           # FastAPI backend
│       └── static/             # Frontend HTML/JS/CSS live console
├── tests/
│   ├── test_automata/          # Unit tests against textbook automata
│   ├── test_properties/        # Hypothesis property-based tests
│   ├── test_verification/      # P1–P5 emptiness checks
│   ├── test_adapters/          # Conformance & translation tests
│   └── test_scenarios/         # Regression suite for D1–D13
├── report/                     # LaTeX / Markdown report sources + auto-generated tables
└── docs/                       # Architectural diagrams and patent documentation
```

---

## 5. Step-by-Step Implementation Breakdown (Step Brokerage)

To guarantee rigorous execution and eliminate scope drift, the project is broken down into **8 self-contained, bite-sized steps**. Each step concludes with an automated verification checkpoint.

| Step # | Step Name | Key Deliverables | Verification Checkpoint | Status |
|---|---|---|---|---|
| **Step 0** | **Skeleton & Dependencies** | `pyproject.toml`, `requirements.txt`, `README.md`, package structure. | Test discovery succeeds via `pytest`. | **COMPLETED** |
| **Step 1** | **Core Automata Primitives** | `dfa.py`, `nfa.py`, `subset.py`, `reachability.py`, `minimize.py`, `product.py`, `transducer.py`, `render.py`. | 4 textbook DFAs pass; `hypothesis` confirms minimization preserves language. (12/12 tests) | **COMPLETED** |
| **Step 2** | **Session Automaton ($M_S$)** | 18 states, 28 symbols, full $\delta_S$ table, session instance tracking. | Scenarios **D1** (Happy Path) and **D2** (Billing-Skip Rejection) pass. | *Pending* |
| **Step 3** | **Verification Layer** | Safety properties $P_1$–$P_5$ as forbidden DFAs, product emptiness check, counterexample extraction. | Scenario **D3** (Unlock while charging caught via $P_2$) passes. | *Pending* |
| **Step 4** | **Station Composition** | Shared resource $R$, lazy product $M_S^N \times R$, multiset symmetry reduction, invariants $I_1$–$I_5$. | Scenario **D9** (6 bays / 3 connectors / power cap) passes without state explosion. | *Pending* |
| **Step 5** | **Recovery Engine** | Safe state set $\mathcal{S}$, domain cost model, Dijkstra shortest path $\rho$, verification gate. | Scenarios **D4**–**D8** pass; hostile bypass (D8) rejected. | *Pending* |
| **Step 6** | **Protocol Adapters** | Mealy transducers, declarative YAML parser, totality/range/prefix conformance checker. | Scenarios **D10** (Dynamic hot-load) and **D11** (Malformed YAML rejected) pass. | *Pending* |
| **Step 7** | **Queuing Automata** | Bounded counter DFA ($K+1$), Pumping Lemma adversary demo, PDA for nested holds, optimizer admission gate. | Pumping lemma game proves non-regularity; Scenario **D12** (Unsafe reorder rejected) passes. | *Pending* |
| **Step 8** | **Simulator & Live UI** | Discrete-event clock loop, FastAPI web console, live Graphviz SVG rendering, $10^5$-event fuzzing. | Scenario **D13** (Full fleet stress test) runnable from UI with zero false accepts. | *Pending* |

---

## 5.1 Phased Build Plan & Algorithmic Details

### Phase 0 — Mathematical Foundations (Week 1 / Steps 0 & 1)
**Goal:** Pure automata algorithms library, fully tested against standard theory benchmarks before any charging logic is introduced.

- [ ] Implement `DFA` class: states $Q$, alphabet $\Sigma$, transition table $\delta: Q \times \Sigma \to Q$, initial state $q_0$, accepting states $F$.
- [ ] Implement `accepts(word)` and `trace(word)`:
  - `trace()` must return the full sequence of visited states and, upon rejection, the exact failure index $i$, the rejected symbol $w[i]$, and the set of admissible symbols $\text{Admissible}(q) = \{a \in \Sigma \mid \delta(q, a) \text{ is defined}\}$.
- [ ] Implement `NFA` with $\epsilon$-transitions and $\epsilon$-closure computation.
- [ ] Implement Subset Construction (powerset determinization) with canonical frozenset state naming for traceability.
- [ ] Implement Forward Reachability from $q_0$ (unreachable state detection) and Backward Reachability from $F$ (trap / dead-end state detection).
- [ ] Implement Hopcroft Minimization ($O(|\Sigma| \cdot |Q| \log |Q|)$ partition refinement).

> [!IMPORTANT]
> **Hopcroft with Partial Transition Functions:**
> AFCO's primary rejection mechanism is the *undefined transition* (partial $\delta$). Standard Hopcroft assumes a total transition function. To minimize a partial DFA without losing rejection semantics:
> 1. Complete $\delta$ with a dedicated non-accepting sink state $q_{sink}$ before partitioning.
> 2. Execute standard Hopcroft partition refinement.
> 3. Prune the block containing $q_{sink}$ and all transitions targeting it from the resulting quotient automaton.

- [ ] Implement Graphviz exporter generating clean `.dot` and `.svg` diagrams.

**Exit Criterion (M1):** The library correctly reproduces minimized states for 4 textbook DFAs from Hopcroft, Motwani & Ullman (e.g., matching $(a|b)^*abb$, mod-3 binary counters, and known equivalent state pairs).

---

### Phase 1 — The Session Automaton (Week 2)
**Goal:** Encode and formally validate the 18-state canonical session automaton $M_S$.

- [ ] Encode $M_S$ based on the formal state taxonomy (see [Section 14](#14-canonical-session-automaton-m_s-specification)): 18 states, 28 symbols, and the complete transition table.
- [ ] Verify structural soundness:
  - Assert zero unreachable states from `IDLE`.
  - Assert that the backward reachability check finds `FAULT_TERMINAL` as the only dead-end trap state.
- [ ] Implement dynamic admissibility query: $\text{admissible}(q) = \{a \in \Sigma \mid \delta(q, a) \ne \bot\}$ computed strictly from $\delta$.
- [ ] Compute the minimal DFA for $M_S$ via Hopcroft; document the Myhill–Nerode equivalence classes explaining any collapsed states.
- [ ] Implement Scenario **D1** (Canonical Happy Path) and Scenario **D2** (Billing-Skip Rejection).

**Exit Criterion (M2):** Running D2 on the input word with an unbilled premature departure outputs the failure index, admissible symbols at the point of rejection, and the synthesized repair sequence without raising unhandled exceptions.

---

### Phase 2 — Verification Layer & Model Checking (Week 3)
**Goal:** Automata-theoretic safety verification via language intersection emptiness.

- [ ] Encode safety properties $P_1$–$P_5$ as property DFAs $M_{U,1}$–$M_{U,5}$ that accept *forbidden* sequences (see [Section 13](#13-formal-safety-properties-p1p5--station-invariants-i1i5)).
- [ ] Implement the Synchronous Product Construction $M_S \times M_{U,k}$ with accepting states $F_{prod} = F_S \times F_{U,k}$.
- [ ] Implement Intersection-Emptiness Decision Procedure:
  $$\mathcal{L}(M_S) \cap \mathcal{L}(M_{U,k}) = \emptyset \iff \text{Reach}(F_{prod}) = \emptyset$$
- [ ] Implement Counterexample Extraction: BFS parent pointer traceback yielding the shortest sequence that triggers the safety violation.
- [ ] Implement Repair Path Synthesis: BFS from the current rejecting state $q_{curr}$ to the nearest safe accepting state in $F_S$.
- [ ] Standardize the verification verdict output format (see [Section 16](#16-verification-verdict-data-structure)).
- [ ] Implement Scenario **D3** (Unlock While Charging).

**Exit Criterion (M3):** Scenario D3 is rejected by the intersection-emptiness check against property $P_2$, producing a formal counterexample trace and distinguishing this model-checking rejection from a simple missing transition.

---

### Phase 3 — Station Composition & Symmetry Reduction (Week 4)
**Goal:** Compose concurrent charging sessions with shared station physical constraints without combinatorial state explosion.

- [ ] Encode the Shared Resource Automaton $R$: tracks available connectors, active power draw tiers, and utility grid constraints.
- [ ] Implement the **Lazy Product Automaton** for $N$ sessions: $M_{comp} = M_{S,1} \times \dots \times M_{S,N} \times R$.
  - States are materialized strictly on-demand during successor generation.
- [ ] Implement Symmetry Reduction:
  - Treat identical session states as an unordered multiset.
  - State equivalence hash: `(tuple(sorted(s.state for s in sessions)), r_state)`.
- [ ] Encode Station Invariants $I_1$–$I_5$ as composite state predicates (see [Section 13](#13-formal-safety-properties-p1p5--station-invariants-i1i5)).
- [ ] Implement state space instrumentation: log naive state count vs symmetry-reduced count vs actually explored states.
- [ ] Implement Scenario **D9** (Station Concurrency: 6 vehicles, 3 connectors, power cap).

**Exit Criterion (M4):** Scenario D9 successfully manages 6 concurrent sessions across 3 connectors with 0 invariant breaches (no double connector assignment, aggregate power never exceeds $P_{grid}$), generating the state-space reduction comparison table.

---

### Phase 4 — Adaptive Recovery Engine (Week 5)
**Goal:** Compute optimal, verified repair transitions from any fault state back to safe operation.

- [ ] Formalize the Safe State Set $\mathcal{S} \subset Q_S$ satisfying:
  1. *Physical Safety:* Contactors open, voltage isolated.
  2. *Commercial Safety:* Unbilled meter recorded or payment guaranteed.
  3. *Productive Safety:* Vehicle able to resume charging or cleanly unlatch.
- [ ] Implement the Evidence Model: tuple representing physical sensors (meter delta, cable interlock, link integrity, payment status).
- [ ] Implement Domain-Weighted Cost Function $C(e)$ over transition edges (penalizing unbilled energy risk, slot blockage, and contactor wear).
- [ ] Implement Recovery Function $\rho(q, \text{evidence})$:
  - Executes Dijkstra's algorithm over the session transition graph to find the minimum-cost path to the nearest safe state $s^* \in \mathcal{S}$.
- [ ] **Mandatory Verification Gate:** Before any recovery path is executed, the entire candidate sequence is verified against $P_1$–$P_5$.
- [ ] Build the Fault Injection Harness for scenarios **D4**, **D5**, **D6**, **D7**, and **D8**.

**Exit Criterion (M5):** Scenarios D4–D8 execute successfully. Scenario D8 demonstrates that if the cheapest path to `COMPLETED` bypasses `pay_ok`, the recovery verification gate rejects the recovery plan and routes to `BILLING_PENDING`.

---

### Phase 5 — Protocol Adapters & Transducers (Week 6)
**Goal:** Normalize proprietary charger protocols into canonical session symbols using declarative Mealy machines.

- [ ] Specify the Declarative Adapter Schema in YAML (vendor states, vendor events, output emission $\lambda(q, e) \in \Sigma_S \cup \{\epsilon\}$).
- [ ] Build the Loader & Transducer Pipeline:
  $$\text{YAML Specification} \longrightarrow \text{Transducer} \longrightarrow \text{Minimized Mealy Machine}$$
- [ ] Implement Formal Conformance Checking:
  - *Totality of $\lambda$:* All admissible vendor transitions map to valid output symbols.
  - *Range Validity:* $\text{Range}(\lambda) \subseteq \Sigma_S \cup \{\epsilon\}$.
  - *Prefix Language Containment:* Output sequences conform to valid session prefixes: $\mathcal{L}_{emitted} \subseteq \text{Prefixes}(\mathcal{L}(M_S))$.
  - *No New Traps:* Vendor model introduces no unreachable or non-recovering dead states.
- [ ] Write adapters: `ocpp16.yaml`, `ocpp201.yaml`, `chademo.yaml`.
- [ ] Create `malformed_test.yaml` containing a deliberately non-conforming transition.
- [ ] Implement Scenarios **D10** (Dynamic Runtime Adapter Loading) and **D11** (Malformed Adapter Rejection).

**Exit Criterion (M6):** D10 hot-loads a new adapter file at runtime with zero Python modifications; D11 detects conformance failure and refuses to load the malformed adapter, citing the exact failing invariant.

---

### Phase 6 — Queue Automata & Optimizer Admission (Week 7)
**Goal:** Formalize queuing mechanisms and enforce the separation principle on untrusted schedulers.

- [ ] Implement Bounded Queue as a Finite Counter Automaton (depth $K$, exactly $K+1$ states tracking occupancy).
- [ ] Build the **Pumping Lemma Adversary Demo**:
  - Algorithmically prove the unbounded FIFO queue language $\mathcal{L} = \{enq^n deq^n \mid n \ge 0\}$ is non-regular by demonstrating that for any pumping length $p$, the pumped string violates queue balance.
  - Prove that bounding capacity to $K$ restores regularity.
- [ ] Implement a Pushdown Automaton (PDA) with stack transitions to manage nested fleet reservation holds.
- [ ] Implement Heuristic Queue Optimizer (greedy priority, arrival time, peak-power smoothing).
- [ ] Build the **Kernel Admission Gate**:
  - The optimizer proposes queue reorderings.
  - The kernel checks: (a) composite reachability, (b) invariant satisfaction, (c) starvation freedom ($I_5$).
- [ ] Implement Scenario **D12** (Unsafe Optimizer Proposal Rejection).

**Exit Criterion (M7):** When the optimizer proposes an aggressive schedule that breaches the station peak power ceiling, the kernel rejects it with a counterexample and enforces a safe fallback schedule.

---

### Phase 7 — Simulator & Live Visualization (Week 8)
**Goal:** Interactive real-time testbed demonstrating full system orchestration.

- [ ] Build Discrete Event Simulation Loop (`sim/clock.py`).
- [ ] Develop Web Console (FastAPI + HTML5 Canvas / SVG):
  - Station grid displaying bay status, current kW, active state.
  - Live session trace log detailing every accepted/rejected transition.
  - Graphviz SVG diagram of $M_S$ highlighting the active state in real time.
- [ ] Implement interactive fault-injection triggers (cable pull, grid trip, payment drop).
- [ ] Automated verification report generator producing PDF/HTML certificates.
- [ ] Implement Scenario **D13** (Full Fleet Simulation Stress Test).

**Exit Criterion (M8):** All scenarios D1–D13 can be selected, executed, and inspected live through the web dashboard without terminal intervention.

---

### Phase 8 — Synthesis, Report & Patent Draft (Weeks 9–10)
**Goal:** Academic deliverable and patent application package.

- [ ] Automatically regenerate all report figures and data tables directly from benchmark test runs.
- [ ] Populate §14.4 Performance Metrics:
  - State space sizes: raw product vs symmetry-reduced.
  - Recovery execution latency (target $< 2$ ms).
  - Soundness fuzzing results: 100,000 randomized events $\to$ exactly 0 false accepts.
- [ ] Implement baseline benchmark: compare AFCO against a standard industry timeout-and-reboot CPMS policy.
- [ ] Audit Patent Claims: Ensure every independent claim maps directly to a concrete Python module and an automated passing test.
- [ ] Finalize Demo Script and rehearse execution.

**Exit Criterion (M9):** Submission-ready academic paper and fully substantiated patent draft with code verification.

---

## 6. Milestones & Proven Principles

| Milestone | Target | Focus | What it Formally Proves |
|---|---|---|---|
| **M1** | Week 1 | Automata Library | Core language algorithms (DFA, NFA, Hopcroft, BFS) are textbook-correct. |
| **M2** | Week 2 | Session DFA ($M_S$) | Rejection via undefined transition yields exact failure index and repair path. |
| **M3** | Week 3 | Model Checker | Safety properties enforced via intersection emptiness ($L(M_S) \cap L(M_U) = \emptyset$). |
| **M4** | Week 4 | Station Product | Lazy composition with symmetry reduction prevents combinatorial state explosion. |
| **M5** | Week 5 | Recovery Engine | Dijkstra-based recovery $\rho$ is formally verified against $P_1$–$P_5$ before execution. |
| **M6** | Week 6 | Protocol Transducers | Protocol adapters are pure declarative data; conformance is formally verified. |
| **M7** | Week 7 | Admission Gate | Untrusted heuristic schedulers cannot breach safety invariants. |
| **M8** | Week 8 | Integrated Demo | All 13 scenarios (D1–D13) execute cleanly through the interactive UI. |
| **M9** | Week 10 | Final Submission | Complete formal report, benchmark suite, and audited patent claims. |

---

## 7. Testing Strategy

| Level | Target | Tooling | Assertion / Invariant |
|---|---|---|---|
| **Unit** | Automata algorithms | `pytest` | Validated against known textbook DFAs / NFAs. |
| **Property** | DFA execution | `hypothesis` | For all words $w$, `accepts(w)` $\iff$ `trace(w)` terminates in $F$. |
| **Invariant** | Hopcroft minimization | `hypothesis` | Minimization preserves exact language recognition: $\mathcal{L}(M) = \mathcal{L}(\text{Min}(M))$. |
| **Invariant** | Subset construction | `hypothesis` | Powerset DFA accepts the exact language of the source NFA: $\mathcal{L}(N) = \mathcal{L}(\text{Det}(N))$. |
| **Soundness** | Safety verification | `hypothesis` fuzzing | Over $10^5$ random event streams, no sequence intersecting $\mathcal{L}(M_{unsafe})$ is ever accepted. |
| **Scenario** | Regression D1–D13 | `pytest` | All 13 operational and fault scenarios pass deterministically. |
| **Exhaustive** | Fault recovery | Fuzz harness | For every state $q \in Q_S$ and every fault $f$, $\rho(q, f)$ terminates in $\mathcal{S}$ or detects terminal failure. |

---

## 8. Risk Register & Mitigations

| Risk | Severity | Mitigation Strategy |
|---|---|---|
| **Combinatorial State Explosion** in station product | High | Implement lazy successor generation and symmetry reduction (multiset of session states) from day one. Cap simulator demo at 8 bays. |
| **Arbitrary Recovery Cost Weights** | High | Ground weights in physical and economic metrics: ₹ unbilled energy risk, minutes delayed, contactor wear cycles. |
| **Adapters Becoming Executable Code** | High | Enforce strict YAML-only loading. Add an automated test verifying no adapter file imports Python code. |
| **Project Drifting into Generic Web App** | High | Strictly enforce Guiding Principle 1. Build the frontend last (Phase 7). Grade is based on the kernel. |
| **Hopcroft Failure on Partial DFAs** | Medium | Complete partial DFAs with a temporary non-accepting sink state prior to minimization, then strip it post-minimization. |
| **Transducer Determinization Pitfalls** | Medium | Require vendor input alphabets to be deterministic; disallow non-deterministic multi-token output rules in adapters. |
| **Patent Claims Exceeding Code Capabilities** | Medium | Conduct bi-weekly claim audits against unit tests. Delete any claim not directly demonstrated by code. |

---

## 9. Patent Track (Parallel Execution)

| Week | Patent Deliverable | Objective |
|---|---|---|
| **Week 2** | Prior-Art Matrix | Audit existing CPMS patents, OCPP compliance tools, and workflow model checkers. |
| **Week 4** | Technical Invention Disclosure | Formulate novel claims: runtime automata model-checking gating actuation in EV charging. |
| **Week 6** | Claim-to-Code Mapping | Bind each patent claim directly to specific classes, methods, and test fixtures. |
| **Week 8** | Independent Claim Audit | Verify that Claims 1, 2, and 5 are fully reproducible from running code. |
| **Week 10** | Final Patent Application Draft | Finalize claims, detailed specification, and algorithmic flowcharts. |

---

## 10. Weekly Checklist Template

```markdown
### Week __ Checklist

**Current Phase:** Phase __
**Target Milestone:** M__

**Completed this week:**
- [ ] 
- [ ] 

**Scenarios currently passing:** D__ D__ D__

**Verification metrics generated:**
- [ ] Graphviz state diagrams exported
- [ ] State space measurements logged
- [ ] Hypothesis fuzzing test passes (0 false accepts)

**Scope Audit:**
- Did any application-level `if` statement bypass the kernel? [No / Yes - Refactored]
- Are all protocol adapters pure declarative YAML? [Yes / No]

**Blockers & Resolutions:**
- 
```

---

## 11. Definition of Done

The project is complete if and only if:

1. All **13 demonstration scenarios (D1–D13)** execute reliably via both the automated test suite and the interactive UI.
2. Every table, state count, and diagram in the report is programmatically generated from the codebase.
3. Adding a new charger protocol requires solely dropping in one YAML file with zero modifications to the Python kernel.
4. Randomized fuzzing across $10^5$ event sequences produces exactly zero safety invariant violations (zero false accepts).
5. Every rejection in the execution trace includes the failure step, the admissible alphabet, and a synthesized repair path.
6. Every independent claim in the patent draft links to a concrete automated test.
7. An independent reviewer can read the formal specification in [Section 14](#14-canonical-session-automaton-m_s-specification) and reconstruct $M_S$ identically.

---

## 12. Demonstration & Verification Scenario Catalog (D1–D13)

| ID | Name | Sequence / Trigger | Expected Verdict | Theory Demonstrated |
|---|---|---|---|---|
| **D1** | Canonical Happy Path | `reserve` $\to$ `auth_req` $\to$ `auth_ok` $\to$ `plug_in` $\to$ `lock_ok` $\to$ `ev_ready` $\to$ `precharge_ok` $\to$ `power_start` $\to$ `power_ramp_down` $\to$ `power_stop` $\to$ `unplug` $\to$ `meter_final` $\to$ `pay_ok` $\to$ `session_close` | **ACCEPT** | Regular word acceptance: $w \in \mathcal{L}(M_S)$. Final state $q \in F_S$. |
| **D2** | Billing-Skip Rejection | User disconnects and attempts departure after `power_stop` without `pay_ok`. | **REJECT** (Step 9) | Rejection by undefined transition; outputs failure step, admissible set, and shortest repair path to `COMPLETED`. |
| **D3** | Live Disconnect Attempt | `unlock_req` emitted while session is in `CHARGING` ($I > 0$). | **REJECT** (Model Check) | Rejection by safety property $P_2$ intersection emptiness ($L(M_S) \cap L(P_2) \ne \emptyset$). |
| **D4** | Telemetry Drop Recovery | Heartbeat / meter link lost during `CHARGING`; meter delta verified upon reconnect. | **RECOVER** | Adaptive recovery $\rho$ via Dijkstra to safe state `CHARGING_RESUMED` without resetting session. |
| **D5** | Emergency Contactor Trip | `e_stop` signal asserted during active power flow. | **ISOLATE** | Immediate transition to `FAULT_TERMINAL`; physical safety isolation enforced. |
| **D6** | Payment Gateway Timeout | `pay_fail` returned during session settlement. | **HOLD** | Commercial safe state: retains cable lock / billing retry loop; prevents premature transition to `IDLE`. |
| **D7** | Grid Curtailment Throttling | Utility grid curtailment drops site power allocation to 0 kW. | **THROTTLE** | Dynamic transition to `PAUSED_DISPATCH`; session remains valid while power flow pauses. |
| **D8** | Hostile Bypass Attempt | Malicious event injection attempts recovery to `COMPLETED` skipping payment. | **BLOCKED** | Recovery verification gate re-evaluates $\rho(q)$ against $P_3$, rejecting the candidate recovery plan. |
| **D9** | Station Multi-Bay Contention | 6 vehicles request charging on a 3-bay station with a 150 kW aggregate cap. | **ORCHESTRATE** | Lazy product automaton $M_S^6 \times R$; symmetry reduction prevents state explosion; invariants $I_1$–$I_3$ hold. |
| **D10** | Dynamic Adapter Hot-Load | Drop new `vendor_x.yaml` into adapters directory at runtime. | **SUCCESS** | Mealy transducer normalizes vendor dialect into $\Sigma_S$; zero kernel recompilation. |
| **D11** | Malformed Adapter Rejection | Load `broken.yaml` with missing transitions and non-deterministic mappings. | **REJECT** (Load Time) | Conformance decision procedure verifies totality, range validity, and trap freedom. |
| **D12** | Unsafe Optimizer Rejection | Untrusted optimizer proposes reordering that would overload substation feeder. | **DISPOSE** | Kernel admission gate rejects proposal using invariant $I_2$; enforces safe priority order. |
| **D13** | Full Fleet Stress Test | 50 concurrent randomized session lifecycles with continuous fault injection. | **100% SOUND** | System soundness: zero false accepts, zero safety invariant violations, live UI rendering. |

---

## 13. Formal Safety Properties ($P_1$–$P_5$) & Station Invariants ($I_1$–$I_5$)

### Safety Properties ($P_1$–$P_5$)
Properties are encoded as minimal DFAs $M_{U,k}$ accepting the *forbidden* language $\mathcal{L}(M_{U,k})$. Safety holds if and only if $\mathcal{L}(M_S) \cap \mathcal{L}(M_{U,k}) = \emptyset$.

- **$P_1$ (No Unmetered Energy Transfer):** Contactors must never close and power must never flow unless an active session authorization token is registered.
  $$\Sigma^* \cdot \text{power\_start} \cdot (\Sigma \setminus \{\text{auth\_ok}\})^* \cdot \text{power\_active}$$
- **$P_2$ (Mechanical Interlock Integrity / No Live Disconnect):** The connector lock must never be disengaged while current is flowing ($I > 0$).
  $$\Sigma^* \cdot \text{power\_active} \cdot (\Sigma \setminus \{\text{power\_stop}, \text{isolate}\})^* \cdot \text{unlock\_ok}$$
- **$P_3$ (No Unsettled Departure):** A session must never transition to `COMPLETED` or release the vehicle without payment confirmation or authorized billing hold.
  $$\Sigma^* \cdot \text{power\_stop} \cdot (\Sigma \setminus \{\text{pay\_ok}, \text{billing\_waived}\})^* \cdot \text{session\_close}$$
- **$P_4$ (Power Envelope Non-Exceedance):** Aggregate power assigned to concurrent sessions must not exceed site feed limit:
  $$\sum_{i=1}^N P(s_i) \le P_{station\_max}$$
- **$P_5$ (Emergency Isolation Latency):** Upon receipt of an emergency stop (`e_stop`) or ground fault interrupt, the contactors must open within the immediate next transition.

### Station Invariants ($I_1$–$I_5$)
Composite state predicates evaluated on the product automaton $M_S^N \times R$:

- **$I_1$ (Connector Exclusivity):** Each connector $c \in C$ is assigned to at most one active session:
  $$\forall s_a, s_b \in S, \quad s_a \ne s_b \implies \text{Connector}(s_a) \cap \text{Connector}(s_b) = \emptyset$$
- **$I_2$ (Aggregate Power Ceiling):** Total instantaneous power draw does not exceed available grid capacity $P_{grid}(R)$:
  $$\sum_{s \in S} \text{Draw}(s) \le P_{grid}(R)$$
- **$I_3$ (Fault Isolation Independence):** An electrical fault on bay $k$ forces bay $k$ to isolate without perturbing healthy sessions on bay $j \ne k$.
- **$I_4$ (Grid Curtailment Compliance):** When $R$ receives an external curtailment event, total station dispatch drops within a bounded number of discrete clock ticks.
- **$I_5$ (Starvation Freedom):** For any waiting session $s_{wait}$ in the queue, the number of subsequent session admissions prior to $s_{wait}$ is strictly bounded by queue capacity $K$.

---

## 14. Canonical Session Automaton ($M_S$) Specification

### State Taxonomy ($Q_S$, $|Q| = 18$)

| State Name | Classification | Description |
|---|---|---|
| `IDLE` | Quiescent ($q_0$) | Connector in holster; ready for reservation or plug-in. |
| `RESERVED` | Allocated | Booked by fleet operator; awaiting vehicle arrival. |
| `AUTH_PENDING` | Handshake | Vehicle detected; validating fleet credential. |
| `AUTHORIZED` | Handshake | Credential accepted; awaiting physical cable connection. |
| `CABLE_DETECTED` | Physical Coupling | Cable inserted; pilot signal detected. |
| `EV_CONNECTED` | Physical Coupling | Connector locked mechanically; isolation test running. |
| `PRECHARGE` | Power Prep | Contactor closed; DC bus pre-charging to match battery voltage. |
| `CHARGING` | Active Energy | Full power flow; continuous telemetry and metering. |
| `PAUSED_DISPATCH`| Throttled | Energy transfer paused due to grid curtailment or power cap. |
| `SUSPENDED_EV` | Suspended | Energy transfer suspended by EV battery management system. |
| `SUSPENDED_EVSE`| Suspended | Energy transfer suspended by station control policy. |
| `RAMP_DOWN` | Termination | Current ramping down gracefully to zero. |
| `ISOLATING` | Termination | Contactors opened; residual voltage discharging. |
| `UNLOCKED` | Physical Decoupling | Connector lock retracted; safe for operator extraction. |
| `UNPLUGGED` | Physical Decoupling | Cable returned to holster; awaiting billing resolution. |
| `BILLING_PENDING`| Settlement | Calculating final kWh; submitting invoice to fleet gateway. |
| `COMPLETED` | Accepting ($F$) | Payment verified; invoice closed; session finalized. |
| `FAULT_TERMINAL` | Trap / Dead State | Physical/electrical safety interlock tripped; requires operator reset. |

### Formal Alphabet ($\Sigma_S$, $|\Sigma| = 28$)

- **Physical & Hardware Events (8):** `plug_in`, `unplug`, `lock_ok`, `lock_fail`, `unlock_req`, `unlock_ok`, `cable_fault`, `pilot_lost`.
- **Power & Contactor Events (6):** `precharge_ok`, `power_start`, `power_ramp_down`, `power_stop`, `contactors_open`, `overcurrent_trip`.
- **Authorization & Commercial Events (6):** `reserve_req`, `auth_req`, `auth_ok`, `auth_fail`, `pay_ok`, `pay_fail`.
- **Telemetry & Management Events (5):** `meter_tick`, `meter_final`, `ev_ready`, `ev_stop`, `grid_curtail`.
- **Administrative & Emergency Events (3):** `e_stop`, `reset_cmd`, `session_close`.

---

## 15. Protocol Adapter Specification & YAML Schema

Adapters translate vendor-specific message sets into canonical symbols $\Sigma_S$ via a Mealy transducer.

```yaml
adapter:
  vendor: "OCPP-1.6J"
  version: "1.0"
  initial_state: "Available"

states:
  - "Available"
  - "Preparing"
  - "Charging"
  - "SuspendedEV"
  - "SuspendedEVSE"
  - "Finishing"
  - "Faulted"

transitions:
  - from: "Available"
    event: "Authorize(idTag)"
    to: "Preparing"
    emit: "auth_req"

  - from: "Preparing"
    event: "StatusNotification(Preparing, CablePlugin)"
    to: "Preparing"
    emit: "plug_in"

  - from: "Preparing"
    event: "StartTransaction(ok)"
    to: "Charging"
    emit: "power_start"

  - from: "Charging"
    event: "MeterValues(kWh)"
    to: "Charging"
    emit: "meter_tick"

  - from: "Charging"
    event: "StopTransaction(Remote)"
    to: "Finishing"
    emit: "power_ramp_down"

  - from: "Finishing"
    event: "StatusNotification(Available)"
    to: "Available"
    emit: "session_close"

conformance:
  deterministic: true
  total_output_mapping: true
  allowed_output_alphabet: "canonical_sigma"
```

### Formal Conformance Rules
1. **Totality:** For every defined vendor transition $\delta_V(q, e)$, an output emission $\lambda_V(q, e) \in \Sigma_S \cup \{\epsilon\}$ must be specified.
2. **Range Soundness:** $\forall (q, e) \in Q_V \times \Sigma_V, \quad \lambda_V(q, e) \in \Sigma_S \cup \{\epsilon\}$.
3. **Prefix Preservation:** For any accepted vendor event sequence $w_V \in \mathcal{L}(M_V)$, the emitted canonical sequence $\lambda^*(w_V)$ must be a valid prefix of $\mathcal{L}(M_S)$.
4. **Trap Freedom:** No vendor transition sequence may reach a state from which an accepting canonical termination cannot be reached.

---

## 16. Verification Verdict & Explainability Data Structure

Every verification operation yields a structured, explainable verdict:

```python
from dataclasses import dataclass
from typing import List, Optional, Set

@dataclass(frozen=True)
class VerificationVerdict:
    is_safe: bool
    failure_index: Optional[int] = None
    rejected_symbol: Optional[str] = None
    violated_property: Optional[str] = None
    admissible_symbols: Optional[Set[str]] = None
    counterexample: Optional[List[str]] = None
    repair_path: Optional[List[str]] = None

    def format_report(self) -> str:
        """Renders standard human-readable explanation matching report §13."""
        if self.is_safe:
            return "VERDICT: ACCEPT — Trace is formally safe and admits valid completion."
        return (
            f"VERDICT: REJECT\n"
            f"  - Failure Position   : Step {self.failure_index}\n"
            f"  - Rejected Symbol    : '{self.rejected_symbol}'\n"
            f"  - Violated Invariant : {self.violated_property}\n"
            f"  - Admissible Symbols : {sorted(list(self.admissible_symbols or []))}\n"
            f"  - Counterexample     : {' -> '.join(self.counterexample or [])}\n"
            f"  - Synthesized Repair : {' -> '.join(self.repair_path or [])}"
        )
```
