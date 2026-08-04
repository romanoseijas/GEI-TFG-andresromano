import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from data_input import build_input_data
from model_milp import solve_balanced, extract_solution, is_solved

app = FastAPI(
    title="TFG Tribunal Assignment API",
    description="MILP-based API to schedule TFG tribunal assignments.",
    version="2.0.0",
)

ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("SOLVER_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Entrada: entidades tal y como salen de Supabase
# --------------------------------------------------------------------------- #

class Periodo(BaseModel):
    id: Optional[str] = None
    nombre: Optional[str] = None
    fecha_inicio: str = Field(..., description="YYYY-MM-DD")
    fecha_fin: str = Field(..., description="YYYY-MM-DD")
    hora_inicio_dia: str = Field("09:00", description="Inicio de la ventana diaria, HH:MM")
    hora_fin_dia: str = Field("14:00", description="Fin de la ventana diaria, HH:MM")
    duracion_defensa: int = Field(30, gt=0, description="Minutos por defensa")
    num_miembros: int = Field(3, gt=0, description="Tamano del tribunal (k)")
    num_aulas: int = Field(3, gt=0, description="Aulas simultaneas disponibles")
    max_tribunales: Optional[int] = Field(None, description="Maximo de tribunales por docente")


class Docente(BaseModel):
    id: str
    nombre: Optional[str] = None
    acepta_ingles: bool = False
    activo: bool = True


class Tfg(BaseModel):
    id: str
    titulo: Optional[str] = None
    estudiante: Optional[str] = None
    tutor_id: Optional[str] = None
    idioma: str = "Castellano"


class DisponibilidadSlot(BaseModel):
    docente_id: str
    fecha: str = Field(..., description="YYYY-MM-DD")
    hora_inicio: str = Field(..., description="HH:MM")


class SolveRequest(BaseModel):
    periodo: Periodo
    docentes: List[Docente]
    tfgs: List[Tfg]
    disponibilidad: List[DisponibilidadSlot] = []
    time_limit: Optional[int] = Field(60, description="Limite de tiempo del solver en segundos")


# --------------------------------------------------------------------------- #
# Salida
# --------------------------------------------------------------------------- #

class Evaluador(BaseModel):
    docente_id: str
    nombre: str


class Asignacion(BaseModel):
    tfg_id: str
    titulo: str
    estudiante: str
    idioma: str
    tutor_id: Optional[str] = None
    tutor_nombre: Optional[str] = None
    fecha: str
    dia_semana: str
    hora_inicio: str
    hora_fin: str
    aula: str
    tribunal: List[Evaluador]


class Carga(BaseModel):
    docente_id: str
    nombre: str
    num_tribunales: int


class SolveResponse(BaseModel):
    status: str
    termination: str
    resuelto: bool
    num_slots: int = 0
    num_aulas: int = 0
    tribunal_size: int = 0
    lmax: Optional[float] = None
    lmin: Optional[float] = None
    gap: Optional[float] = None
    asignaciones: List[Asignacion] = []
    cargas: List[Carga] = []
    avisos: List[str] = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest):
    payload = req.model_dump()

    try:
        data = build_input_data(payload)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        model, result, banda = solve_balanced(
            data.as_model_data(), time_limit=req.time_limit
        )
    except ValueError as exc:
        # Infactibilidad detectable al construir el modelo: devolvemos el motivo
        # junto con los avisos del prevuelo para que el admin pueda corregirlo.
        raise HTTPException(
            status_code=422,
            detail={"error": str(exc), "avisos": data.avisos},
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    status = str(result.solver.status)
    termination = str(result.solver.termination_condition)
    base = SolveResponse(
        status=status,
        termination=termination,
        resuelto=False,
        num_slots=len(data.S),
        num_aulas=data.num_aulas,
        tribunal_size=data.tribunal_size,
        avisos=list(data.avisos),
    )

    if not is_solved(result):
        base.avisos.append(
            "El solver no encontro ninguna planificacion factible. Revisa los "
            "avisos anteriores: normalmente falta disponibilidad o hay mas TFGs "
            "que huecos configurados."
        )
        return base

    asignaciones = []
    cargas = {d: 0 for d in data.D}
    for tfg_id, sid, aula, evaluadores in extract_solution(model):
        slot = data.slots_by_id[sid]
        meta = data.tfg_meta[tfg_id]
        for d in evaluadores:
            cargas[d] += 1
        asignaciones.append(
            Asignacion(
                tfg_id=tfg_id,
                titulo=meta["titulo"],
                estudiante=meta["estudiante"],
                idioma=meta["idioma"],
                tutor_id=meta["tutor_id"],
                tutor_nombre=meta["tutor_nombre"],
                fecha=slot.fecha.isoformat(),
                dia_semana=slot.dia_semana,
                hora_inicio=slot.hora_inicio,
                hora_fin=slot.hora_fin,
                aula=aula,
                tribunal=[
                    Evaluador(docente_id=d, nombre=data.docente_nombre[d])
                    for d in evaluadores
                ],
            )
        )

    asignaciones.sort(key=lambda a: (a.fecha, a.hora_inicio, a.aula))

    activos = [n for n in cargas.values() if n > 0]
    base.resuelto = True
    base.lmax = float(max(activos)) if activos else 0.0
    base.lmin = float(min(activos)) if activos else 0.0
    base.gap = base.lmax - base.lmin
    base.asignaciones = asignaciones
    base.cargas = sorted(
        (
            Carga(docente_id=d, nombre=data.docente_nombre[d], num_tribunales=n)
            for d, n in cargas.items()
        ),
        key=lambda c: (-c.num_tribunales, c.nombre),
    )

    if len(asignaciones) < len(data.T):
        base.avisos.append(
            f"Solo se han podido programar {len(asignaciones)} de {len(data.T)} TFGs."
        )
    return base
