import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from pyomo.environ import value

from model_milp import build_model, solve_model

app = FastAPI(
    title="TFG Tribunal Assignment API",
    description="MILP-based API to schedule TFG tribunal assignments.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SolveRequest(BaseModel):
    """
    All list/dict keys that are tuples in the Pyomo model are encoded as
    comma-separated strings: e.g. {"D1,S1": 1} instead of {("D1","S1"): 1}.
    """
    T: List[str] = Field(..., description="TFG identifiers")
    D: List[str] = Field(..., description="Teacher (docente) identifiers")
    S: List[str] = Field(..., description="Time-slot identifiers")
    A: List[str] = Field(..., description="Room (aula) identifiers")
    R: List[str] = Field(..., description="Tribunal identifiers")
    avail: Dict[str, int] = Field(
        ..., description="Teacher availability per slot. Key: 'D,S', value: 0/1"
    )
    inc: Dict[str, int] = Field(
        ..., description="Teacher-TFG incompatibility. Key: 'D,T', value: 0/1 (1=incompatible)"
    )
    lang_ok: Dict[str, int] = Field(
        ..., description="Language compatibility. Key: 'D,T', value: 0/1"
    )
    room_avail: Dict[str, int] = Field(
        ..., description="Room availability. Key: 'S,A,T', value: 0/1"
    )
    tribunal_size: int = Field(3, description="Number of evaluators per tribunal")
    load_min: Dict[str, int] = Field(
        ..., description="Minimum load per teacher. Key: teacher id"
    )
    load_max: Dict[str, int] = Field(
        ..., description="Maximum load per teacher. Key: teacher id"
    )


class TFGAssignment(BaseModel):
    tfg: str
    slot: str
    room: str
    evaluators: List[str]


class SolveResponse(BaseModel):
    status: str
    termination: str
    lmax: Optional[float] = None
    lmin: Optional[float] = None
    gap: Optional[float] = None
    assignments: List[TFGAssignment] = []


def _parse_flat_keys(flat: Dict[str, int], arity: int) -> Dict[tuple, int]:
    """Convert 'K1,K2,...' string keys back to tuples."""
    result = {}
    for key, val in flat.items():
        parts = key.split(",", arity - 1)
        if len(parts) != arity:
            raise ValueError(f"Expected {arity}-part key, got: '{key}'")
        result[tuple(parts)] = val
    return result


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest):
    try:
        data = {
            "T": req.T,
            "D": req.D,
            "S": req.S,
            "A": req.A,
            "R": req.R,
            "avail": _parse_flat_keys(req.avail, 2),
            "inc": _parse_flat_keys(req.inc, 2),
            "lang_ok": _parse_flat_keys(req.lang_ok, 2),
            "room_avail": _parse_flat_keys(req.room_avail, 3),
            "tribunal_size": req.tribunal_size,
            "load_min": req.load_min,
            "load_max": req.load_max,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        model = build_model(data)
        result = solve_model(model)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    status = str(result.solver.status)
    termination = str(result.solver.termination_condition)

    if termination.lower() not in ("optimal", "feasible"):
        return SolveResponse(status=status, termination=termination)

    assignments = []
    for t in model.T:
        for s in model.S:
            for a in model.A:
                if value(model.y[t, s, a]) > 0.5:
                    evaluators = [d for d in model.D if value(model.x[d, t, s, a]) > 0.5]
                    assignments.append(TFGAssignment(tfg=t, slot=s, room=a, evaluators=evaluators))

    lmax_val = value(model.Lmax)
    lmin_val = value(model.Lmin)

    return SolveResponse(
        status=status,
        termination=termination,
        lmax=lmax_val,
        lmin=lmin_val,
        gap=lmax_val - lmin_val,
        assignments=assignments,
    )
