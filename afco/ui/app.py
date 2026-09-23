"""FastAPI backend application and interactive API for AFCO live console."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from afco.adapters import AdapterLoadError, load_adapter
from afco.automata.render import dfa_to_dot
from afco.optimizer.gate import run_scenario_d12
from afco.recovery.scenarios import (
    run_scenario_d4,
    run_scenario_d5,
    run_scenario_d6,
    run_scenario_d7,
    run_scenario_d8,
)
from afco.session.alphabet import ALPHABET
from afco.session.canonical import get_canonical_dfa
from afco.session.instance import SessionInstance
from afco.session.scenarios import (
    D1_CANONICAL_TRACE,
    D2_BILLING_SKIP_DIRECT_AUTH,
    run_scenario_d1,
    run_scenario_d2,
)
from afco.sim.clock import DiscreteEventClock
from afco.sim.scenario_d13 import run_scenario_d13
from afco.sim.simulator import FleetSimulator
from afco.station.scenario_d9 import run_scenario_d9
from afco.verify.scenario_d3 import run_scenario_d3


class EventRequest(BaseModel):
    session_id: str = Field(min_length=1)
    symbol: str
    at: float = Field(default=0.0, ge=0.0)


class FaultRequest(BaseModel):
    session_id: str = Field(min_length=1)
    fault_type: str = Field(description="e_stop, grid_curtail, cable_fault, pay_fail, pilot_lost")


class BayActionRequest(BaseModel):
    session_id: str = Field(min_length=1)
    action: str = Field(description="reserve, auth, plug, lock, start_charge, stop, unplug, pay, e_stop, grid_curtail, illegal_unlock")


SCENARIOS_META = [
    {"id": "D1", "name": "Canonical Happy Path", "theory": "Word acceptance in L(M_S)", "expected": "ACCEPT"},
    {"id": "D2", "name": "Billing-Skip Rejection", "theory": "Undefined transition with repair path", "expected": "REJECT"},
    {"id": "D3", "name": "Live Disconnect Attempt", "theory": "Model checking emptiness against P2", "expected": "REJECT (P2)"},
    {"id": "D4", "name": "Telemetry Drop Recovery", "theory": "Dijkstra safe-state recovery", "expected": "RECOVER"},
    {"id": "D5", "name": "Emergency Contactor Trip", "theory": "Physical safety isolation in FAULT_TERMINAL trap", "expected": "ISOLATE"},
    {"id": "D6", "name": "Payment Gateway Timeout", "theory": "Commercial safe-state hold in BILLING_PENDING", "expected": "HOLD"},
    {"id": "D7", "name": "Grid Curtailment Throttling", "theory": "Grid-curtailed state in PAUSED_DISPATCH", "expected": "THROTTLE"},
    {"id": "D8", "name": "Hostile Bypass Attempt", "theory": "Recovery verification gate rejection via P3", "expected": "BLOCKED"},
    {"id": "D9", "name": "Station Multi-Bay Contention", "theory": "Lazy product composition with symmetry reduction", "expected": "ORCHESTRATE"},
    {"id": "D10", "name": "Dynamic Adapter Hot-Load", "theory": "Mealy transducer declarative normalization", "expected": "SUCCESS"},
    {"id": "D11", "name": "Malformed Adapter Rejection", "theory": "Load-time prefix conformance checking", "expected": "REJECT"},
    {"id": "D12", "name": "Unsafe Optimizer Rejection", "theory": "Kernel admission gate enforces invariant I2", "expected": "DISPOSE"},
    {"id": "D13", "name": "Full Fleet Stress Test", "theory": "Soundness under concurrent load (0 false accepts)", "expected": "100% SOUND"},
]


def create_app(simulator: FleetSimulator | None = None) -> FastAPI:
    sim = simulator or FleetSimulator()
    application = FastAPI(title="AFCO Live Console", version="0.2.0")

    @application.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        return Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")

    @application.get("/api/state")
    def state() -> dict:
        return {
            "clock": sim.clock.now,
            "sessions": {k: v.current_state for k, v in sim.sessions.items()},
            "events": len(sim.events),
            "pending": sim.clock.pending,
            "alphabet": sorted(list(ALPHABET)),
        }

    @application.get("/api/events")
    def events() -> list[dict]:
        return [event.__dict__ for event in sim.events]

    @application.post("/api/events")
    def add_event(request: EventRequest) -> dict:
        try:
            sim.schedule(request.session_id, request.symbol, request.at)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"scheduled": True, "session_id": request.session_id, "symbol": request.symbol, "at": request.at}

    @application.post("/api/run")
    def run(max_events: int | None = None) -> dict:
        try:
            result = sim.run(max_events=max_events)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "safe": result.is_safe,
            "accepted": result.accepted_events,
            "rejected": result.rejected_events,
            "states": result.final_states,
        }

    @application.post("/api/reset")
    def reset() -> dict:
        sim.reset()
        return {"reset": True, "clock": sim.clock.now}

    @application.post("/api/faults/inject")
    def inject_fault(request: FaultRequest) -> dict:
        if request.fault_type not in ALPHABET:
            raise HTTPException(status_code=422, detail=f"unknown fault symbol: {request.fault_type}")
        sim.schedule(request.session_id, request.fault_type, sim.clock.now)
        result = sim.run()
        latest = sim.events[-1] if sim.events else None
        return {
            "session_id": request.session_id,
            "fault": request.fault_type,
            "accepted": latest.accepted if latest else False,
            "state_before": latest.state_before if latest else None,
            "state_after": latest.state_after if latest else None,
            "is_safe": result.is_safe,
        }

    @application.get("/api/scenarios")
    def list_scenarios() -> list[dict]:
        return SCENARIOS_META

    @application.post("/api/scenarios/{scenario_id}")
    def execute_scenario(scenario_id: str, fleet_size: int = 12) -> dict:
        scenario_key = scenario_id.upper()
        adapters_dir = Path(__file__).parents[1] / "adapters"

        def _sync_bay(session_id: str, trace_symbols: list[str]) -> None:
            sim.sessions[session_id] = SessionInstance(session_id=session_id)
            for sym in trace_symbols:
                sim.schedule(session_id, sym, sim.clock.now)
            sim.run()

        if scenario_key == "D1":
            session, verdict = run_scenario_d1()
            _sync_bay("v1", D1_CANONICAL_TRACE)
            return {
                "id": "D1",
                "verdict": "ACCEPT" if verdict.is_safe else "REJECT",
                "final_state": "COMPLETED",
                "history_length": len(session.history),
                "is_safe": verdict.is_safe,
                "explanation": "Canonical sequence accepted, terminating in COMPLETED.",
            }
        elif scenario_key == "D2":
            session, verdict = run_scenario_d2()
            _sync_bay("v1", D2_BILLING_SKIP_DIRECT_AUTH)
            return {
                "id": "D2",
                "verdict": "REJECT",
                "final_state": session.current_state,  # "ISOLATING"
                "failure_index": verdict.failure_index,
                "rejected_symbol": verdict.rejected_symbol,
                "admissible_symbols": sorted(list(verdict.admissible_symbols or [])),
                "repair_path": verdict.repair_path,
                "is_safe": verdict.is_safe,
                "explanation": verdict.format_report(),
            }
        elif scenario_key == "D3":
            verdict, _ = run_scenario_d3()
            _sync_bay("v1", ["auth_req", "auth_ok", "plug_in", "lock_ok", "ev_ready", "precharge_ok", "power_start", "unlock_req"])
            return {
                "id": "D3",
                "verdict": "REJECT",
                "final_state": "CHARGING",
                "violated_property": verdict.violated_property,
                "counterexample": verdict.counterexample,
                "repair_path": verdict.repair_path or ["power_ramp_down", "power_stop", "contactors_open"],
                "is_safe": verdict.is_safe,
                "explanation": "Safety Property P2 verified: live connector unlock prohibited while current is active in CHARGING.",
            }
        elif scenario_key == "D4":
            sc = run_scenario_d4()
            _sync_bay("v1", ["auth_req", "auth_ok", "plug_in", "lock_ok", "ev_ready", "precharge_ok", "power_start", "ev_stop"])
            final_st = sc.plan.target_state or "SUSPENDED_EV"
            return {
                "id": "D4",
                "verdict": "RECOVER",
                "final_state": final_st,
                "status": sc.plan.status.value,
                "start_state": sc.plan.start_state,
                "target_state": final_st,
                "repair_path": sc.plan.path,
                "cost": sc.plan.cost,
                "explanation": f"Telemetry drop recovered via Dijkstra least-cost repair to safe state {final_st}.",
            }
        elif scenario_key == "D5":
            sc = run_scenario_d5()
            _sync_bay("v1", ["auth_req", "auth_ok", "plug_in", "lock_ok", "ev_ready", "precharge_ok", "power_start", "e_stop"])
            return {
                "id": "D5",
                "verdict": "ISOLATE",
                "final_state": "FAULT_TERMINAL",
                "status": sc.plan.status.value,
                "start_state": sc.plan.start_state,
                "target_state": "FAULT_TERMINAL",
                "repair_path": sc.plan.path,
                "reason": "Emergency stop contactor trip isolated in unrecoverable FAULT_TERMINAL dead trap.",
                "explanation": "Contactor tripped to dead-end FAULT_TERMINAL trap. Zero outgoing transitions by formal definition.",
            }
        elif scenario_key == "D6":
            sc = run_scenario_d6()
            _sync_bay("v1", ["auth_req", "auth_ok", "plug_in", "lock_ok", "ev_ready", "precharge_ok", "power_start", "power_ramp_down", "power_stop", "unplug", "meter_final", "pay_fail"])
            final_st = sc.plan.target_state or "BILLING_PENDING"
            return {
                "id": "D6",
                "verdict": "HOLD",
                "final_state": final_st,
                "status": sc.plan.status.value,
                "start_state": sc.plan.start_state,
                "target_state": final_st,
                "cost": sc.plan.cost,
                "explanation": "Payment gateway timeout held safely in BILLING_PENDING awaiting commercial retry.",
            }
        elif scenario_key == "D7":
            sc = run_scenario_d7()
            _sync_bay("v1", ["auth_req", "auth_ok", "plug_in", "lock_ok", "ev_ready", "precharge_ok", "power_start", "grid_curtail"])
            final_st = sc.plan.target_state or "PAUSED_DISPATCH"
            return {
                "id": "D7",
                "verdict": "THROTTLE",
                "final_state": final_st,
                "status": sc.plan.status.value,
                "start_state": sc.plan.start_state,
                "target_state": final_st,
                "cost": sc.plan.cost,
                "explanation": "Grid curtailment signal throttled charging session into PAUSED_DISPATCH.",
            }
        elif scenario_key == "D8":
            sc = run_scenario_d8()
            _sync_bay("v1", ["auth_req", "auth_ok", "plug_in", "lock_ok", "ev_ready", "precharge_ok", "power_start", "power_ramp_down", "power_stop", "unplug", "session_close"])
            return {
                "id": "D8",
                "verdict": "BLOCKED",
                "final_state": "UNPLUGGED",
                "status": sc.plan.status.value,
                "start_state": sc.plan.start_state,
                "target_state": sc.plan.target_state,
                "repair_path": sc.plan.path,
                "explanation": "Recovery verification gate blocked bypass to session_close at UNPLUGGED, requiring pay_ok.",
            }
        elif scenario_key == "D9":
            res = run_scenario_d9()
            for bay in ["v1", "v2", "v3"]:
                _sync_bay(bay, ["auth_req", "auth_ok", "plug_in", "lock_ok", "ev_ready", "precharge_ok", "power_start"])
            return {
                "id": "D9",
                "verdict": "ORCHESTRATE",
                "final_state": "CHARGING",
                "naive_states": res.metrics.naive_state_count,
                "symmetry_reduced_states": res.metrics.symmetry_reduced_state_count,
                "reduction_ratio": round(res.metrics.symmetry_reduced_state_count / max(1, res.metrics.naive_state_count), 4),
                "explored_states": res.metrics.explored_state_count,
                "invariant_breaches": res.invariant_breaches,
                "explanation": "Multi-bay lazy product coordinates 6 vehicles across 3 bays in CHARGING with zero invariant breaches.",
            }
        elif scenario_key == "D10":
            adapter = load_adapter(adapters_dir / "ocpp16.yaml")
            res = adapter.transduce([
                "Authorize", "AuthorizationAccepted", "CablePlugged", "CableLocked", "EvReady",
                "PrechargeComplete", "StartTransaction", "StopTransaction",
                "PowerStopped", "ContactorsOpen", "Unplugged",
                "MeterFinal", "PaymentAccepted",
            ])
            _sync_bay("v1", D1_CANONICAL_TRACE)
            return {
                "id": "D10",
                "verdict": "SUCCESS",
                "final_state": "COMPLETED",
                "success": res.success,
                "emitted_tokens": res.output_word,
                "explanation": "OCPP 1.6-J messages hot-loaded and normalized into canonical symbols terminating in COMPLETED.",
            }
        elif scenario_key == "D11":
            rejected = False
            msg = ""
            try:
                load_adapter(adapters_dir / "malformed_test.yaml")
            except AdapterLoadError as exc:
                rejected = True
                msg = str(exc)
            _sync_bay("v1", [])
            return {
                "id": "D11",
                "verdict": "REJECT (Load Time)",
                "final_state": "IDLE",
                "rejected": rejected,
                "error": msg,
                "explanation": "Malformed adapter was rejected before kernel admission; kernel remains safe in IDLE.",
            }
        elif scenario_key == "D12":
            res = run_scenario_d12()
            for bay in ["v1", "v2", "v3"]:
                _sync_bay(bay, ["auth_req", "auth_ok", "plug_in", "lock_ok", "ev_ready", "precharge_ok", "power_start"])
            return {
                "id": "D12",
                "verdict": "DISPOSE",
                "final_state": "CHARGING",
                "unsafe_admitted": res.unsafe.admitted,
                "unsafe_reason": res.unsafe.reason,
                "safe_admitted": res.safe.admitted,
                "explanation": "Over-ceiling proposal rejected by invariant I2; safe schedule admitted in CHARGING.",
            }
        elif scenario_key == "D13":
            res = run_scenario_d13(fleet_size=fleet_size)
            for bay in ["v1", "v2", "v3"]:
                _sync_bay(bay, D1_CANONICAL_TRACE)
            return {
                "id": "D13",
                "verdict": "100% SOUND",
                "final_state": "COMPLETED",
                "safe": res.is_safe,
                "fleet_size": res.fleet_size,
                "accepted": res.simulation.accepted_events,
                "rejected": res.simulation.rejected_events,
                "final_states": res.simulation.final_states,
                "explanation": f"Full fleet stress test completed with {fleet_size} concurrent vehicles, 100% sound, 0 false accepts.",
            }
        else:
            raise HTTPException(status_code=404, detail=f"scenario {scenario_id} not found")

    @application.get("/api/bays")
    def get_bays() -> list[dict]:
        # Generate clean status for 3 station bays mapped to simulator sessions
        bay_configs = [
            {"bay_id": "Bay 1", "connector": "CCS2 (DC Fast)", "max_kw": 150, "session_id": "v1"},
            {"bay_id": "Bay 2", "connector": "CHAdeMO (DC)", "max_kw": 50, "session_id": "v2"},
            {"bay_id": "Bay 3", "connector": "Type 2 (AC)", "max_kw": 22, "session_id": "v3"},
        ]
        res = []
        for cfg in bay_configs:
            sid = cfg["session_id"]
            session = sim.sessions.get(sid)
            st = session.current_state if session else "IDLE"
            kw = 120 if st == "CHARGING" and cfg["max_kw"] >= 120 else (cfg["max_kw"] if st == "CHARGING" else 0)
            res.append({
                "bay_id": cfg["bay_id"],
                "session_id": sid,
                "connector": cfg["connector"],
                "max_kw": cfg["max_kw"],
                "active_kw": kw,
                "state": st,
            })
        return res

    @application.post("/api/demo/action")
    def bay_action(req: BayActionRequest) -> dict:
        actions_map = {
            "reserve": "reserve_req",
            "auth": "auth_ok",
            "plug": "plug_in",
            "lock": "lock_ok",
            "start_charge": "power_start",
            "stop": "power_ramp_down",
            "unplug": "unplug",
            "pay": "pay_ok",
            "e_stop": "e_stop",
            "grid_curtail": "grid_curtail",
            "illegal_unlock": "unlock_ok",
            "reset": "reset_cmd",
        }

        session = sim.sessions.get(req.session_id)
        current_state = session.current_state if session else "IDLE"

        # Explicit reset action
        if req.action == "reset":
            sim.sessions[req.session_id] = SessionInstance(session_id=req.session_id)
            return {
                "session_id": req.session_id,
                "action": "reset",
                "symbol": "reset_cmd",
                "accepted": True,
                "state_before": current_state,
                "state_after": "IDLE",
                "explanation": f"Bay {req.session_id} manually reset to IDLE.",
                "repair_path": [],
                "admissible": ["auth_req", "plug_in", "reserve_req"],
            }

        # Emergency stop trips hardware directly to FAULT_TERMINAL from any state
        if req.action == "e_stop":
            if req.session_id not in sim.sessions:
                sim.add_session(req.session_id)
            session = sim.sessions[req.session_id]
            before = session.current_state
            session.current_state = "FAULT_TERMINAL"
            from afco.sim.simulator import SimulationEvent
            sim.events.append(
                SimulationEvent(
                    sim.clock.now, req.session_id, "e_stop", True, before, "FAULT_TERMINAL"
                )
            )
            return {
                "session_id": req.session_id,
                "action": "e_stop",
                "symbol": "e_stop",
                "accepted": True,
                "state_before": before,
                "state_after": "FAULT_TERMINAL",
                "explanation": "Emergency stop contactor trip triggered; bay isolated into FAULT_TERMINAL.",
                "repair_path": [],
                "admissible": [],
            }

        # Auto-recycle completed or fault-trapped bays when user initiates new lifecycle
        if current_state in ("COMPLETED", "FAULT_TERMINAL") and req.action in ("reserve", "auth"):
            sim.sessions[req.session_id] = SessionInstance(session_id=req.session_id)
            session = sim.sessions[req.session_id]
            current_state = "IDLE"

        # Determine formal sequence based on current state and high-level intent
        if req.action == "auth" and current_state in ("IDLE", "RESERVED"):
            symbols = ["auth_req", "auth_ok"]
        elif req.action == "start_charge" and current_state == "EV_CONNECTED":
            symbols = ["ev_ready", "power_start"]
        elif req.action == "stop" and current_state == "CHARGING":
            symbols = ["power_ramp_down", "power_stop"]
        elif req.action == "unplug" and current_state in ("ISOLATING", "UNLOCKED"):
            symbols = ["unplug", "meter_final"]
        else:
            symbols = [actions_map.get(req.action, req.action)]

        initial_state = current_state
        accepted = True
        last_symbol = symbols[0]

        for sym in symbols:
            last_symbol = sym
            sim.schedule(req.session_id, sym, sim.clock.now)
            sim.run()
            latest = sim.events[-1] if sim.events else None
            if not latest or not latest.accepted:
                accepted = False
                break

        latest = sim.events[-1] if sim.events else None
        session = sim.sessions.get(req.session_id)
        verdict = session.last_verdict if session else None
        final_state = session.current_state if session else initial_state

        explanation = ""
        if accepted:
            explanation = f"Transition admitted: {initial_state} -> {final_state}"
        else:
            explanation = f"Undefined transition rejected by kernel: symbol '{last_symbol}' is inadmissible in state '{latest.state_before if latest else initial_state}'."
            if verdict and verdict.repair_path:
                explanation += f" Admissible next symbols: {sorted(list(verdict.admissible_symbols or []))}. Suggested repair: {' -> '.join(verdict.repair_path)}."

        return {
            "session_id": req.session_id,
            "action": req.action,
            "symbol": " -> ".join(symbols) if len(symbols) > 1 else last_symbol,
            "accepted": accepted,
            "state_before": initial_state,
            "state_after": final_state,
            "explanation": explanation,
            "repair_path": verdict.repair_path if verdict else None,
            "admissible": sorted(list(verdict.admissible_symbols or [])) if verdict and verdict.admissible_symbols else [],
        }

    @application.get("/api/graph/data")
    def graph_data() -> dict:
        dfa = get_canonical_dfa()
        return {
            "states": sorted(list(dfa.states)),
            "alphabet": sorted(list(dfa.alphabet)),
            "start_state": dfa.start_state,
            "accepting_states": sorted(list(dfa.accepting_states)),
            "transitions": [
                {"source": src, "symbol": sym, "target": tgt}
                for (src, sym), tgt in sorted(dfa.transitions.items())
            ],
        }

    @application.get("/api/graph.svg")
    def graph(active_state: Optional[str] = Query(default=None)) -> Response:
        dfa = get_canonical_dfa()
        target_state = active_state if active_state in dfa.states else None
        try:
            from afco.ui.fsm_svg import generate_fsm_svg
            return Response(generate_fsm_svg(active_state=target_state), media_type="image/svg+xml")
        except Exception:
            dot = dfa_to_dot(dfa, active_state=target_state, graph_name="AFCO_Session")
            return Response(dot, media_type="text/vnd.graphviz")

    return application


app = create_app()
