# AFCO M9 Verification Report

## Evidence

| Metric | Result |
|---|---:|
| D3 P2 model-check safe | True |
| D3 counterexample length | 0 |
| D9 naive states | 1632586752 |
| D9 symmetry-reduced states | 5002 |
| D9 explored states | 5002 |
| D13 events | 700 |
| D13 rejected events | 0 |
| Fuzz trials | 100000 |
| Fuzz false accepts | 0 |

## Baseline benchmark

| Policy | Events | Rejected | Recoveries |
|---|---:|---:|---:|
| AFCO | 700 | 0 | 0 |
| timeout-and-reboot | 750 | 50 | 50 |

## Claim-to-code audit

- **claim_1_runtime_automata_gate** — modules: `afco/session/canonical.py, afco/verify/checker.py`; tests: `tests/test_verification/test_step3.py`
- **claim_2_adaptive_safe_recovery** — modules: `afco/recovery/engine.py, afco/recovery/cost.py`; tests: `tests/test_recovery/test_step5_recovery.py`
- **claim_5_declarative_protocol_normalization** — modules: `afco/adapters/loader.py, afco/adapters/conformance.py`; tests: `tests/test_adapters_step6.py`
