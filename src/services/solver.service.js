// Client for the Python MILP solver (backend/src/api.py).
// The API receives the raw Supabase entities and derives slots, aulas and
// compatibility matrices itself, so we only forward what the tables contain.
const SOLVER_URL = (import.meta.env.VITE_SOLVER_URL || 'http://localhost:8000').replace(/\/$/, '')

export async function health() {
  const res = await fetch(`${SOLVER_URL}/health`)
  if (!res.ok) throw new Error(`El solver respondió ${res.status}`)
  return res.json()
}

export async function solve({ periodo, docentes, tfgs, disponibilidad, timeLimit = 60 }) {
  const body = {
    periodo: {
      id: periodo.id,
      nombre: periodo.nombre,
      fecha_inicio: periodo.fecha_inicio,
      fecha_fin: periodo.fecha_fin,
      hora_inicio_dia: periodo.hora_inicio_dia || '09:00',
      hora_fin_dia: periodo.hora_fin_dia || '14:00',
      duracion_defensa: periodo.duracion_defensa ?? 30,
      num_miembros: periodo.num_miembros ?? 3,
      num_aulas: periodo.num_aulas ?? 3,
      max_tribunales: periodo.max_tribunales ?? null,
    },
    docentes: docentes.map((d) => ({
      id: d.id,
      nombre: d.nombre,
      acepta_ingles: !!d.acepta_ingles,
      activo: d.activo !== false,
    })),
    tfgs: tfgs.map((t) => ({
      id: t.id,
      titulo: t.titulo,
      estudiante: t.estudiante,
      tutor_id: t.tutor_id,
      idioma: t.idioma || 'Castellano',
    })),
    disponibilidad: disponibilidad.map((s) => ({
      docente_id: s.docente_id,
      fecha: String(s.fecha).slice(0, 10),
      hora_inicio: String(s.hora_inicio).slice(0, 5),
    })),
    time_limit: timeLimit,
  }

  let res
  try {
    res = await fetch(`${SOLVER_URL}/solve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new Error(
      `No se pudo contactar con el solver en ${SOLVER_URL}. ` +
        'Arráncalo con: cd backend && uvicorn src.api:app --reload',
    )
  }

  const payload = await res.json().catch(() => null)
  if (!res.ok) {
    throw new Error(formatError(payload, res.status))
  }
  return payload
}

function formatError(payload, status) {
  const detail = payload?.detail
  if (typeof detail === 'string') return detail
  if (detail?.error) {
    return [detail.error, ...(detail.avisos || [])].join('\n')
  }
  if (Array.isArray(detail)) {
    return detail.map((d) => `${(d.loc || []).join('.')}: ${d.msg}`).join('\n')
  }
  return `El solver devolvió un error ${status}`
}
