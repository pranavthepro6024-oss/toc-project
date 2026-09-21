"""JSON/HTML console for running and inspecting AFCO simulations."""
from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from afco.automata.render import dfa_to_dot
from afco.session.canonical import get_canonical_dfa
from afco.sim.simulator import FleetSimulator
from afco.sim.scenario_d13 import run_scenario_d13

class EventRequest(BaseModel):
    session_id: str = Field(min_length=1); symbol: str; at: float = Field(default=0.0, ge=0.0)

def create_app(simulator: FleetSimulator | None = None) -> FastAPI:
    sim = simulator or FleetSimulator(); application = FastAPI(title="AFCO Live Console", version="0.1.0")
    @application.get("/", response_class=HTMLResponse)
    def dashboard() -> str: return Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    @application.get("/api/state")
    def state() -> dict: return {"clock": sim.clock.now, "sessions": {k: v.current_state for k, v in sim.sessions.items()}, "events": len(sim.events), "pending": sim.clock.pending}
    @application.get("/api/events")
    def events() -> list[dict]: return [event.__dict__ for event in sim.events]
    @application.post("/api/events")
    def add_event(request: EventRequest) -> dict:
        try: sim.schedule(request.session_id, request.symbol, request.at)
        except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"scheduled": True, "session_id": request.session_id, "symbol": request.symbol, "at": request.at}
    @application.post("/api/run")
    def run(max_events: int | None = None) -> dict:
        try: result = sim.run(max_events=max_events)
        except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"safe": result.is_safe, "accepted": result.accepted_events, "rejected": result.rejected_events, "states": result.final_states}
    @application.post("/api/scenarios/d13")
    def scenario_d13(fleet_size: int = 24) -> dict:
        try: result = run_scenario_d13(fleet_size=fleet_size)
        except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"safe": result.is_safe, "fleet_size": result.fleet_size, "accepted": result.simulation.accepted_events, "rejected": result.simulation.rejected_events, "states": result.simulation.final_states}
    @application.get("/api/graph.svg")
    def graph() -> Response:
        dot = dfa_to_dot(get_canonical_dfa(), graph_name="AFCO_Session")
        try:
            import graphviz
            rendered = graphviz.Source(dot).pipe(format="svg")
            return Response(rendered, media_type="image/svg+xml")
        except Exception:
            return Response(dot, media_type="text/vnd.graphviz")
    return application

app = create_app()
