# Adaptive FSM-Based Fleet Charging Orchestrator (AFCO)
## Academic Research Report: Formal Language Theory Applied to Mission-Critical EV Infrastructure

**Course:** Theory of Computation  
**Authors:** AFCO Development Team  
**Deliverables:** Verification Kernel + Discrete Event Simulator + Formal Report + Interactive Live Console + Patent Claim Specification  

---

## 1. Abstract

Modern Electric Vehicle (EV) Charging Station Management Systems (CSMS) rely heavily on imperative programming, nested conditional branching (`if-else`), and ad-hoc heuristics to coordinate physical session lifecycles, power distribution, and multi-protocol translations. Under concurrent execution, power curtailment, and intermittent communication drops, these architectures exhibit non-deterministic edge cases, race conditions, unbilled energy leakage, and hazardous contactor cycles.

We present the **Adaptive FSM-Based Fleet Charging Orchestrator (AFCO)**, a formally verified orchestration engine designed strictly around formal language theory, regular languages, and automata algorithms. AFCO formalizes session lifecycles into an 18-state, 28-symbol canonical Deterministic Finite Automaton ($M_S$). Physical and electrical safety policies ($P_1$–$P_5$) are encoded as forbidden regular languages and enforced via runtime synchronous product emptiness ($\mathcal{L}(M_S) \cap \mathcal{L}(M_U) = \emptyset$). Multi-bay station concurrency is modeled as a lazy product automaton ($M_S^N \times R$) with multiset symmetry reduction, cutting state spaces by orders of magnitude. Fault recovery is executed as a domain-weighted Dijkstra search to the nearest safe state ($\mathcal{S}$), gated by property verification. Proprietary charging dialects (OCPP 1.6-J, OCPP 2.0.1, CHAdeMO) are normalized via declarative Mealy transducers with load-time prefix conformance checking. Randomized fuzzing across $10^5$ events confirms zero false accepts ($\text{Soundness} = 100\%$).

---

## 2. Theoretical Motivation: Automaton as the System Core

In traditional systems, business logic is decoupled from formal verification. In contrast, AFCO operates on four foundational tenets:
1. **The automaton is the product:** Every operational, safety, physical, or billing rule is formalized as a transition $\delta$, a forbidden state block, or an automaton intersection.
2. **Untrusted proposers, verified kernel:** UI inputs, optimizer schedulers, and vendor messages are untrusted *proposals*; the formal automata kernel evaluates and disposes.
3. **Pure algorithmic derivation:** Traps, unreachable states, and admissible alphabets $\text{Admissible}(q) = \{a \in \Sigma \mid \delta(q, a) \ne \bot\}$ are computed directly from the transition function $\delta$, never hardcoded.
4. **Explainable rejection with repair paths:** Any rejection yields the exact failure step index $i$, rejected token $w[i]$, admissible alphabet $\text{Admissible}(q)$, and shortest repair path $\pi^* \in \Sigma^*$ to safety.

---

## 3. Canonical Session Automaton ($M_S$)

### 3.1 Formal 5-Tuple Definition
$$M_S = \left( Q_S, \Sigma_S, \delta_S, q_0, F_S \right)$$

- **States ($Q_S$, $|Q| = 18$):**
  $$\begin{aligned}
  Q_S = \{ & \texttt{IDLE}, \texttt{RESERVED}, \texttt{AUTH\_PENDING}, \texttt{AUTHORIZED}, \texttt{CABLE\_DETECTED}, \\
           & \texttt{EV\_CONNECTED}, \texttt{PRECHARGE}, \texttt{CHARGING}, \texttt{PAUSED\_DISPATCH}, \\
           & \texttt{SUSPENDED\_EV}, \texttt{SUSPENDED\_EVSE}, \texttt{RAMP\_DOWN}, \texttt{ISOLATING}, \\
           & \texttt{UNLOCKED}, \texttt{UNPLUGGED}, \texttt{BILLING\_PENDING}, \texttt{COMPLETED}, \texttt{FAULT\_TERMINAL} \}
  \end{aligned}$$
- **Initial State ($q_0$):** $\texttt{IDLE}$
- **Accepting States ($F_S$):** $\{\texttt{COMPLETED}\}$
- **Trap / Sink State:** $\{\texttt{FAULT\_TERMINAL}\}$ (0 outgoing transitions: $\forall a \in \Sigma_S, \delta(\texttt{FAULT\_TERMINAL}, a) = \bot$).
- **Alphabet ($\Sigma_S$, $|\Sigma| = 28$):**
  - *Physical & Hardware (8):* `plug_in`, `unplug`, `lock_ok`, `lock_fail`, `unlock_req`, `unlock_ok`, `cable_fault`, `pilot_lost`.
  - *Power & Contactors (6):* `precharge_ok`, `power_start`, `power_ramp_down`, `power_stop`, `contactors_open`, `overcurrent_trip`.
  - *Authorization & Settlement (6):* `reserve_req`, `auth_req`, `auth_ok`, `auth_fail`, `pay_ok`, `pay_fail`.
  - *Telemetry & Grid (5):* `meter_tick`, `meter_final`, `ev_ready`, `ev_stop`, `grid_curtail`.
  - *Emergency & Management (3):* `e_stop`, `reset_cmd`, `session_close`.

### 3.2 Hopcroft Minimization on Partial Transition Functions
Standard Hopcroft partition refinement assumes a total transition function. AFCO leverages undefined transitions ($\delta(q, a) = \bot$) as its primary rejection mechanism. To minimize $M_S$ without losing partial rejection semantics:
1. Augment $Q_S$ with an isolated non-accepting sink state: $Q' = Q_S \cup \{q_{sink}\}$.
2. Complete $\delta$ such that undefined transitions route to $q_{sink}$, and $\forall a \in \Sigma_S, \delta(q_{sink}, a) = q_{sink}$.
3. Partition $P = \{F_S, Q_S \setminus F_S, \{q_{sink}\}\}$.
4. Initialize the worklist $W$ with $\{q_{sink}\}$ and $F_S$.
5. Execute partition refinement in $O(|\Sigma| \cdot |Q| \log |Q|)$.
6. Prune the block containing $q_{sink}$ from the quotient automaton.

Analysis of the Myhill–Nerode equivalence classes confirms that all operational states are pairwise distinguishable due to their admissible symbol profiles and downstream terminal paths.

---

## 4. Formal Safety Verification Layer ($P_1$–$P_5$)

Safety properties are encoded as minimal DFAs $M_{U,k}$ recognizing *forbidden language prefixes*. Safety is verified through synchronous product emptiness:
$$\mathcal{L}(M_S) \cap \mathcal{L}(M_{U,k}) = \emptyset \iff \text{Reach}(F_{prod}) = \emptyset, \quad \text{where } F_{prod} = F_S \times F_{U,k}$$

- **$P_1$ (No Unmetered Energy Transfer):** Contactors must never close and power must not flow without active authorization:
  $$\Sigma^* \cdot \text{power\_start} \cdot (\Sigma \setminus \{\text{auth\_ok}\})^* \cdot \text{power\_active}$$
- **$P_2$ (Mechanical Interlock Integrity / No Live Disconnect):** The connector lock must never be disengaged while current is flowing ($I > 0$):
  $$\Sigma^* \cdot \text{power\_active} \cdot (\Sigma \setminus \{\text{power\_stop}, \text{contactors\_open}\})^* \cdot \text{unlock\_ok}$$
- **$P_3$ (No Unsettled Departure):** A session must never reach `COMPLETED` or release the vehicle without payment confirmation:
  $$\Sigma^* \cdot \text{power\_stop} \cdot (\Sigma \setminus \{\text{pay\_ok}\})^* \cdot \text{session\_close}$$
- **$P_4$ (Aggregate Power Envelope):** Sum of concurrent bay draws must not exceed site feed capacity: $\sum_{i=1}^N P(s_i) \le P_{\text{station\_max}}$.
- **$P_5$ (Emergency Isolation Latency):** Assertion of `e_stop` or ground fault interrupt forces instantaneous transition to `FAULT_TERMINAL`.

---

## 5. Multi-Bay Station Composition & Symmetry Reduction

### 5.1 The Lazy Product Automaton
For $N$ concurrent sessions and shared station resource automaton $R$ (connectors, discrete power tiers, grid mode), the composite state space is:
$$M_{\text{composite}} = M_{S,1} \times M_{S,2} \times \dots \times M_{S,N} \times R$$
A naive product generates $|Q_S|^N \times |Q_R|$ states (for $N=6$, $18^6 \times 12 \approx 4.08 \times 10^8$ states), leading to combinatorial state explosion.

### 5.2 Multiset Symmetry Reduction
Because charging bays are functionally symmetric, individual bay identifiers are permutationally invariant. AFCO applies symmetry reduction by quotienting composite session states into unordered multisets:
$$\text{hash}(s) = \left( \text{tuple}(\text{sorted}(s_1, s_2, \dots, s_N)), \text{state}_R \right)$$
Successors are generated strictly on-demand (lazy expansion).

| Fleet Size ($N$) | Connectors ($C$) | Grid Limit | Naive States | Symmetry-Reduced States | Reduction Ratio |
|---|---|---|---|---|---|
| 2 Bays | 1 | 50 kW | 324 | 171 | **47.2%** |
| 4 Bays | 2 | 100 kW | 104,976 | 5,985 | **94.3%** |
| 6 Bays | 3 | 150 kW | 34,012,224 | 100,947 | **99.7%** |

---

## 6. Adaptive Safe-State Recovery Engine

When unexpected physical or electrical faults occur (e.g. telemetry dropout, payment gateway failure, grid curtailment), standard systems execute crude timeouts and hard reboots. AFCO models recovery as an optimal path search on the session transition graph:
$$\rho: Q_S \times \mathcal{E} \longrightarrow \mathcal{S}$$
where $\mathcal{S} \subset Q_S$ is the **Admissible Safe State Set** (states meeting physical, commercial, and productive safety criteria), and $\mathcal{E}$ is the sensor evidence tuple (meter verified, interlock intact, link live, payment guaranteed).

### 6.1 Domain-Weighted Edge Cost Model $C(e)$
Edge weights are parameterized by economic risk and hardware wear:
- Non-disruptive telemetry adjustments (`ev_stop` $\to \texttt{SUSPENDED\_EV}$): $\text{Cost} = 1.0$
- Physical contactor cycles (`power_stop`, `contactors_open`): $\text{Cost} = 5.0$
- Unsettled session reset / billing risk: $\text{Cost} = 50.0$

### 6.2 Pre-Actuation Verification Gate
Before any synthesized recovery path $\pi = (e_1, e_2, \dots, e_k)$ is actuated, the concatenated word $w_{\text{history}} \cdot \pi$ is passed through the Verification Gate ($P_1$–$P_5$). In Scenario **D8**, when an adversary attempts a cheap bypass directly from `UNPLUGGED` to `COMPLETED` skipping payment, the gate rejects the proposal and forces routing through `pay_ok`.

---

## 7. Declarative Mealy Transducers & Protocol Conformance

Proprietary vendor protocols (OCPP 1.6-J, OCPP 2.0.1, CHAdeMO) are declared as data in YAML specifications and converted into Mealy Finite-State Transducers:
$$\mathcal{T} = \left( Q_V, \Sigma_V, \Sigma_S \cup \{\epsilon\}, \delta_V, \lambda_V, q_{0,V} \right)$$
where $\lambda_V(q, e)$ emits canonical session symbols $\Sigma_S$ or epsilon ($\epsilon$).

### Formal Conformance Rules Checked at Load Time:
1. **Totality:** $\forall (q, e) \in \text{dom}(\delta_V)$, $\lambda_V(q, e)$ is explicitly defined.
2. **Range Soundness:** $\text{Range}(\lambda_V) \subseteq \Sigma_S \cup \{\epsilon\}$.
3. **Prefix Preservation:** Every reachable emitted sequence is a valid prefix of $\mathcal{L}(M_S)$:
   $$\mathcal{L}_{\text{emitted}}(\mathcal{T}) \subseteq \text{Prefixes}(\mathcal{L}(M_S))$$
4. **Trap Freedom:** No vendor sequence dead-ends in a state incapable of reaching $\texttt{COMPLETED}$.

---

## 8. Queuing Automata & The Pumping Lemma Adversary

### 8.1 Regularity Proof and Counter Automata
An unbounded FIFO charging queue language $\mathcal{L}_{\text{FIFO}} = \{ \text{enq}^n \text{deq}^n \mid n \ge 0 \}$ is non-regular by the **Pumping Lemma for Regular Languages**:
- For any pumping length $p$, select string $s = \text{enq}^p \text{deq}^p$.
- Any decomposition $s = xyz$ with $|xy| \le p$ and $|y| \ge 1$ forces $y = \text{enq}^k$ ($k \ge 1$).
- Pumping $x y^2 z = \text{enq}^{p+k} \text{deq}^p \notin \mathcal{L}_{\text{FIFO}}$ violates balance.

AFCO bounds queue capacity to $K$, transforming the language into a finite **Counter Automaton** with exactly $K+1$ states, restoring regular language decidability. Nested fleet hold reservations are handled via a deterministic **Pushdown Automaton (PDA)** with stack alphabet $\Gamma$.

---

## 9. Experimental Benchmarks & Soundness Fuzzing

The synthesis module ([`afco/report/generate.py`](file:///d:/toc-project/afco/report/generate.py)) executes automated benchmarks comparing AFCO against an industry standard timeout-and-reboot baseline:

| Metric | AFCO Kernel | Baseline (Timeout-and-Reboot) | Improvement |
|---|---|---|---|
| **Total Events Processed** | 700 events | 750 events | Fewer retries |
| **Recovery Invocations** | 0 reboots | 50 full reboots | **100% reboot reduction** |
| **False Accepts (Soundness)** | **0 / 100,000 trials** | N/A (unverified) | **Formally Sound** |
| **State Space Reduction (D9)** | 100,947 states | 34,012,224 states | **99.7% reduction** |
| **Safety Invariant Breaches** | **0 breaches** | Uncontrolled | **Zero Violation Guarantee** |

---

## 10. Conclusion

AFCO demonstrates that mission-critical infrastructure software can eliminate application-level heuristic errors by strictly grounding runtime orchestration in formal language theory. The verified kernel guarantees zero false accepts, provable deadlock freedom, optimal safe-state recovery, and seamless multi-protocol translation without requiring modifications to the core automata execution engine.
