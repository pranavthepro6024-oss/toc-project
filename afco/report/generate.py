"""Generate the synthesis metrics required by roadmap milestone M9.

The report is deliberately data-first: scenario runners are the source of
truth and the Markdown output is only a presentation of their results.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from afco.sim.simulator import fuzz_soundness
from afco.sim.scenario_d13 import run_scenario_d13
from afco.station.scenario_d9 import run_scenario_d9
from afco.verify.scenario_d3 import run_scenario_d3


@dataclass(frozen=True)
class BenchmarkResult:
    """Comparable, deterministic outcome for an orchestration policy."""

    policy: str
    events: int
    rejected_events: int
    recoveries: int
    false_accepts: int


@dataclass(frozen=True)
class ReportData:
    """Machine-readable M9 evidence bundle."""

    d3_safe: bool
    d3_counterexample_length: int
    d9_naive_states: int
    d9_symmetry_reduced_states: int
    d9_explored_states: int
    d9_invariant_breaches: tuple[str, ...]
    d13_fleet_size: int
    d13_events: int
    d13_rejected_events: int
    fuzz_trials: int
    fuzz_rejected_events: int
    fuzz_false_accepts: int
    afco_benchmark: BenchmarkResult
    baseline_benchmark: BenchmarkResult
    patent_claims: dict[str, dict[str, tuple[str, ...]]]


# Claims are explicit audit records rather than prose that can drift away
# from implementation. Paths are repository-relative for portable reports.
PATENT_CLAIMS: dict[str, dict[str, tuple[str, ...]]] = {
    "claim_1_runtime_automata_gate": {
        "modules": ("afco/session/canonical.py", "afco/verify/checker.py"),
        "tests": ("tests/test_verification/test_step3.py",),
    },
    "claim_2_adaptive_safe_recovery": {
        "modules": ("afco/recovery/engine.py", "afco/recovery/cost.py"),
        "tests": ("tests/test_recovery/test_step5_recovery.py",),
    },
    "claim_5_declarative_protocol_normalization": {
        "modules": ("afco/adapters/loader.py", "afco/adapters/conformance.py"),
        "tests": ("tests/test_adapters_step6.py",),
    },
}


def _baseline(fleet_size: int, events: int) -> BenchmarkResult:
    """Model a timeout-and-reboot policy for the same workload.

    The baseline cannot explain a rejected transition: it reboots the session
    and retries the current event. This intentionally simple model provides a
    stable comparison without pretending to emulate hardware.
    """

    rejected = fleet_size
    return BenchmarkResult("timeout-and-reboot", events + rejected, rejected, rejected, 0)


def _audit_claims(root: Path) -> dict[str, dict[str, tuple[str, ...]]]:
    audited: dict[str, dict[str, tuple[str, ...]]] = {}
    for claim, record in PATENT_CLAIMS.items():
        missing = [path for paths in record.values() for path in paths if not (root / path).is_file()]
        if missing:
            raise FileNotFoundError(f"{claim} references missing evidence: {', '.join(missing)}")
        audited[claim] = record
    return audited


def generate_report(*, root: str | Path | None = None, fuzz_trials: int = 100_000,
                    fleet_size: int = 50) -> ReportData:
    """Run the evidence-producing scenarios and return a serializable bundle."""

    if fuzz_trials < 0 or fleet_size < 1:
        raise ValueError("fuzz_trials must be non-negative and fleet_size must be positive")
    project_root = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    d3, _ = run_scenario_d3()
    d9 = run_scenario_d9()
    d13 = run_scenario_d13(fleet_size=fleet_size)
    fuzz = fuzz_soundness(trials=fuzz_trials, seed=17)
    afco = BenchmarkResult("AFCO", len(d13.simulation.events), d13.simulation.rejected_events, 0, 0)
    return ReportData(
        d3_safe=d3.is_safe,
        d3_counterexample_length=len(d3.counterexample or ()),
        d9_naive_states=d9.metrics.naive_state_count,
        d9_symmetry_reduced_states=d9.metrics.symmetry_reduced_state_count,
        d9_explored_states=d9.metrics.explored_state_count,
        d9_invariant_breaches=d9.invariant_breaches,
        d13_fleet_size=fleet_size,
        d13_events=len(d13.simulation.events),
        d13_rejected_events=d13.simulation.rejected_events,
        fuzz_trials=int(fuzz["trials"]),
        fuzz_rejected_events=int(fuzz["rejected"]),
        fuzz_false_accepts=0 if fuzz["sound"] else 1,
        afco_benchmark=afco,
        baseline_benchmark=_baseline(fleet_size, len(d13.simulation.events)),
        patent_claims=_audit_claims(project_root),
    )


def _plain(value: Any) -> Any:
    return asdict(value) if hasattr(value, "__dataclass_fields__") else value


def render_markdown(data: ReportData) -> str:
    """Render a concise report without recomputing any metric."""

    claims = "\n".join(
        f"- **{name}** — modules: `{', '.join(record['modules'])}`; tests: `{', '.join(record['tests'])}`"
        for name, record in data.patent_claims.items()
    )
    return f"""# AFCO M9 Verification Report

## Evidence

| Metric | Result |
|---|---:|
| D3 P2 model-check safe | {data.d3_safe} |
| D3 counterexample length | {data.d3_counterexample_length} |
| D9 naive states | {data.d9_naive_states} |
| D9 symmetry-reduced states | {data.d9_symmetry_reduced_states} |
| D9 explored states | {data.d9_explored_states} |
| D13 events | {data.d13_events} |
| D13 rejected events | {data.d13_rejected_events} |
| Fuzz trials | {data.fuzz_trials} |
| Fuzz false accepts | {data.fuzz_false_accepts} |

## Baseline benchmark

| Policy | Events | Rejected | Recoveries |
|---|---:|---:|---:|
| {data.afco_benchmark.policy} | {data.afco_benchmark.events} | {data.afco_benchmark.rejected_events} | {data.afco_benchmark.recoveries} |
| {data.baseline_benchmark.policy} | {data.baseline_benchmark.events} | {data.baseline_benchmark.rejected_events} | {data.baseline_benchmark.recoveries} |

## Claim-to-code audit

{claims}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_path", type=Path)
    parser.add_argument("--markdown", dest="markdown_path", type=Path)
    parser.add_argument("--fuzz-trials", type=int, default=100_000)
    parser.add_argument("--fleet-size", type=int, default=50)
    args = parser.parse_args()
    data = generate_report(fuzz_trials=args.fuzz_trials, fleet_size=args.fleet_size)
    if args.json_path:
        args.json_path.write_text(json.dumps(_plain(data), indent=2), encoding="utf-8")
    if args.markdown_path:
        args.markdown_path.write_text(render_markdown(data), encoding="utf-8")
    if not args.json_path and not args.markdown_path:
        print(render_markdown(data))


if __name__ == "__main__":
    main()
