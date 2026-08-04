"""Puente de datos entre Supabase y el modelo MILP.

El frontend envia las entidades en crudo (periodo, docentes, tfgs, disponibilidad)
tal y como salen de las tablas de Supabase. Aqui se derivan los conjuntos y
parametros que necesita el modelo:

  T  -> TFGs a programar
  D  -> docentes activos
  S  -> slots (fecha + hora) generados a partir de la configuracion del periodo
  A  -> aulas A1..An (homogeneas, num_aulas del periodo)

Todos los indices se calculan a partir de la entrada; no hay tamanos fijos.
Las estructuras de compatibilidad se construyen de forma dispersa: solo se
almacenan los pares realmente permitidos, para que el modelo escale.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Set, Tuple

# La rejilla que pinta el frontend en "Mi Disponibilidad" usa bloques de 30 min.
# Un slot de defensa puede durar mas (p.ej. 45 min) y por tanto solapar varios
# bloques: el docente solo esta disponible si tiene marcados TODOS los bloques.
AVAILABILITY_BLOCK_MINUTES = 30

WEEKDAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


# --------------------------------------------------------------------------- #
# Utilidades de fecha/hora
# --------------------------------------------------------------------------- #

def _parse_date(raw) -> date:
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    # Acepta '2026-06-01' y '2026-06-01T00:00:00Z'
    return date.fromisoformat(str(raw).strip()[:10])


def _parse_time(raw) -> time:
    if isinstance(raw, time):
        return raw
    parts = str(raw).strip().split(":")
    if len(parts) < 2:
        raise ValueError(f"Hora no valida: '{raw}' (formato esperado HH:MM)")
    return time(int(parts[0]), int(parts[1]))


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _hhmm(total_minutes: int) -> str:
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


# --------------------------------------------------------------------------- #
# Slots
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Slot:
    """Un hueco concreto de defensa. `sid` es el identificador usado en el MILP."""

    sid: str
    fecha: date
    inicio_min: int
    fin_min: int

    @property
    def hora_inicio(self) -> str:
        return _hhmm(self.inicio_min)

    @property
    def hora_fin(self) -> str:
        return _hhmm(self.fin_min)

    @property
    def dia_semana(self) -> str:
        return WEEKDAY_NAMES[self.fecha.weekday()]

    def blocks(self) -> List[Tuple[date, str]]:
        """Bloques de la rejilla de disponibilidad que cubre este slot."""
        out = []
        cursor = self.inicio_min - (self.inicio_min % AVAILABILITY_BLOCK_MINUTES)
        while cursor < self.fin_min:
            out.append((self.fecha, _hhmm(cursor)))
            cursor += AVAILABILITY_BLOCK_MINUTES
        return out


def generate_slots(periodo: dict) -> List[Slot]:
    """Genera la rejilla de slots del periodo: dias laborables x ventana diaria."""
    inicio = _parse_date(periodo["fecha_inicio"])
    fin = _parse_date(periodo["fecha_fin"])
    if fin < inicio:
        raise ValueError("La fecha de fin del periodo es anterior a la de inicio")

    dur = int(periodo.get("duracion_defensa") or 30)
    if dur <= 0:
        raise ValueError("La duracion de la defensa debe ser mayor que 0 minutos")

    dia_ini = _minutes(_parse_time(periodo.get("hora_inicio_dia") or "09:00"))
    dia_fin = _minutes(_parse_time(periodo.get("hora_fin_dia") or "14:00"))
    if dia_fin <= dia_ini:
        raise ValueError("La hora de fin diaria debe ser posterior a la de inicio")

    slots: List[Slot] = []
    dia = inicio
    while dia <= fin:
        if dia.weekday() < 5:  # solo lunes-viernes
            cursor = dia_ini
            while cursor + dur <= dia_fin:
                slots.append(
                    Slot(
                        sid=f"{dia.isoformat()}T{_hhmm(cursor)}",
                        fecha=dia,
                        inicio_min=cursor,
                        fin_min=cursor + dur,
                    )
                )
                cursor += dur
        dia += timedelta(days=1)

    if not slots:
        raise ValueError(
            "El periodo no genera ningun slot: revisa las fechas (debe incluir "
            "algun dia laborable) y la ventana horaria diaria"
        )
    return slots


# --------------------------------------------------------------------------- #
# Construccion de la entrada del modelo
# --------------------------------------------------------------------------- #

@dataclass
class ScheduleInput:
    """Datos ya normalizados y listos para `build_model`."""

    T: List[str]
    D: List[str]
    S: List[str]
    A: List[str]
    slots: List[Slot]
    slots_by_id: Dict[str, Slot]
    tribunal_size: int
    load_min: Dict[str, int]
    load_max: Dict[str, int]
    # Pares (docente, tfg) permitidos: el docente no es tutor y el idioma encaja
    eligible: Set[Tuple[str, str]]
    # Slots en los que cada docente esta disponible
    avail_slots: Dict[str, Set[str]]
    num_aulas: int
    # Metadatos para poder devolver nombres legibles en la respuesta
    docente_nombre: Dict[str, str] = field(default_factory=dict)
    tfg_meta: Dict[str, dict] = field(default_factory=dict)
    avisos: List[str] = field(default_factory=list)

    def as_model_data(self) -> dict:
        return {
            "T": self.T,
            "D": self.D,
            "S": self.S,
            "A": self.A,
            "tribunal_size": self.tribunal_size,
            "load_min": self.load_min,
            "load_max": self.load_max,
            "eligible": self.eligible,
            "avail_slots": self.avail_slots,
            "num_aulas": self.num_aulas,
        }


def build_input_data(payload: dict) -> ScheduleInput:
    """Convierte el payload crudo de Supabase en la entrada del MILP."""
    periodo = payload["periodo"]
    docentes = payload.get("docentes") or []
    tfgs = payload.get("tfgs") or []
    disponibilidad = payload.get("disponibilidad") or []

    avisos: List[str] = []

    # --- Docentes (solo activos) -------------------------------------------
    docentes_activos = [d for d in docentes if d.get("activo", True)]
    if not docentes_activos:
        raise ValueError("No hay docentes activos para formar tribunales")

    D = [str(d["id"]) for d in docentes_activos]
    docente_nombre = {str(d["id"]): d.get("nombre") or str(d["id"]) for d in docentes_activos}
    acepta_ingles = {str(d["id"]): bool(d.get("acepta_ingles")) for d in docentes_activos}
    docentes_set = set(D)

    # --- TFGs ---------------------------------------------------------------
    if not tfgs:
        raise ValueError("No hay TFGs que programar en este periodo")

    T = [str(t["id"]) for t in tfgs]
    tfg_meta = {
        str(t["id"]): {
            "titulo": t.get("titulo") or "",
            "estudiante": t.get("estudiante") or "",
            "idioma": t.get("idioma") or "Castellano",
            "tutor_id": str(t["tutor_id"]) if t.get("tutor_id") else None,
            "tutor_nombre": docente_nombre.get(str(t.get("tutor_id"))),
        }
        for t in tfgs
    }

    # --- Slots y aulas ------------------------------------------------------
    slots = generate_slots(periodo)
    S = [s.sid for s in slots]
    slots_by_id = {s.sid: s for s in slots}

    num_aulas = int(periodo.get("num_aulas") or 1)
    if num_aulas < 1:
        raise ValueError("El periodo debe tener al menos un aula")
    A = [f"A{i}" for i in range(1, num_aulas + 1)]

    k = int(periodo.get("num_miembros") or 3)
    if k < 1:
        raise ValueError("El tribunal debe tener al menos un miembro")
    if k > len(D):
        raise ValueError(
            f"El tribunal requiere {k} miembros pero solo hay {len(D)} docentes activos"
        )

    # --- Disponibilidad: bloques marcados -> slots completos ----------------
    marcados: Dict[str, Set[Tuple[date, str]]] = {d: set() for d in D}
    for row in disponibilidad:
        did = str(row.get("docente_id"))
        if did not in docentes_set:
            continue
        try:
            fecha = _parse_date(row["fecha"])
            hora = _hhmm(_minutes(_parse_time(row["hora_inicio"])))
        except (KeyError, TypeError, ValueError):
            continue
        marcados[did].add((fecha, hora))

    avail_slots: Dict[str, Set[str]] = {}
    for d in D:
        libres = marcados[d]
        avail_slots[d] = {s.sid for s in slots if all(b in libres for b in s.blocks())}

    sin_disponibilidad = [docente_nombre[d] for d in D if not avail_slots[d]]
    if sin_disponibilidad:
        avisos.append(
            f"{len(sin_disponibilidad)} docente(s) sin disponibilidad en el periodo, "
            f"no podran formar parte de ningun tribunal: "
            f"{', '.join(sin_disponibilidad[:5])}"
            + (" ..." if len(sin_disponibilidad) > 5 else "")
        )

    # --- Elegibilidad docente-TFG (tutor + idioma) --------------------------
    eligible: Set[Tuple[str, str]] = set()
    for t in T:
        meta = tfg_meta[t]
        en_ingles = str(meta["idioma"]).strip().lower() in ("inglés", "ingles", "english")
        for d in D:
            if meta["tutor_id"] == d:
                continue  # el tutor no evalua su propio TFG
            if en_ingles and not acepta_ingles[d]:
                continue  # compatibilidad de idioma
            eligible.add((d, t))

    # --- Cargas -------------------------------------------------------------
    max_trib = periodo.get("max_tribunales")
    load_max_default = len(T) if max_trib in (None, "") else int(max_trib)
    load_min = {d: 0 for d in D}
    load_max = {d: load_max_default for d in D}

    data = ScheduleInput(
        T=T,
        D=D,
        S=S,
        A=A,
        slots=slots,
        slots_by_id=slots_by_id,
        tribunal_size=k,
        load_min=load_min,
        load_max=load_max,
        eligible=eligible,
        avail_slots=avail_slots,
        num_aulas=num_aulas,
        docente_nombre=docente_nombre,
        tfg_meta=tfg_meta,
        avisos=avisos,
    )
    data.avisos.extend(preflight_checks(data))
    return data


def preflight_checks(data: ScheduleInput) -> List[str]:
    """Detecta causas obvias de infactibilidad antes de lanzar el solver.

    Un MILP infactible solo devuelve 'infeasible', asi que estos avisos son la
    unica forma de explicarle al usuario que le falta por configurar.
    """
    avisos: List[str] = []
    k = data.tribunal_size

    capacidad = len(data.S) * data.num_aulas
    if capacidad < len(data.T):
        avisos.append(
            f"Capacidad insuficiente: {len(data.T)} TFGs para {capacidad} huecos "
            f"({len(data.S)} slots x {data.num_aulas} aulas). Amplia el periodo, "
            f"anade aulas o reduce la duracion de la defensa."
        )

    for t in data.T:
        elegibles = [d for d in data.D if (d, t) in data.eligible]
        titulo = data.tfg_meta[t]["titulo"] or t
        if len(elegibles) < k:
            avisos.append(
                f"'{titulo}': solo {len(elegibles)} docente(s) elegibles y el "
                f"tribunal necesita {k} (revisa tutor e idioma)."
            )
            continue
        if not any(
            sum(1 for d in elegibles if s in data.avail_slots[d]) >= k for s in data.S
        ):
            avisos.append(
                f"'{titulo}': no hay ningun slot con {k} docentes elegibles "
                f"disponibles a la vez."
            )

    plazas = sum(data.load_max[d] for d in data.D)
    if plazas < len(data.T) * k:
        avisos.append(
            f"El limite de tribunales por docente es demasiado bajo: se necesitan "
            f"{len(data.T) * k} plazas de evaluador y solo hay {plazas}."
        )

    return avisos


# --------------------------------------------------------------------------- #
# Datos de ejemplo para ejecutar el modelo desde la CLI (main.py)
# --------------------------------------------------------------------------- #

def demo_payload() -> dict:
    """Payload sintetico con la misma forma que envia el frontend."""
    docentes = [
        {"id": f"D{i}", "nombre": f"Docente {i}", "acepta_ingles": i % 2 == 0, "activo": True}
        for i in range(1, 11)
    ]
    tfgs = [
        {
            "id": f"T{i}",
            "titulo": f"TFG {i}",
            "estudiante": f"Estudiante {i}",
            "tutor_id": f"D{i}",
            "idioma": "Inglés" if i % 4 == 0 else "Castellano",
        }
        for i in range(1, 11)
    ]
    periodo = {
        "fecha_inicio": "2026-06-01",
        "fecha_fin": "2026-06-02",
        "hora_inicio_dia": "09:00",
        "hora_fin_dia": "13:00",
        "duracion_defensa": 30,
        "num_miembros": 3,
        "num_aulas": 2,
        "max_tribunales": 5,
    }
    disponibilidad = [
        {"docente_id": d["id"], "fecha": fecha, "hora_inicio": hora}
        for d in docentes
        for fecha in ("2026-06-01", "2026-06-02")
        for hora in ("09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30")
    ]
    return {
        "periodo": periodo,
        "docentes": docentes,
        "tfgs": tfgs,
        "disponibilidad": disponibilidad,
    }
