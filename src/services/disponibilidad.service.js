import { supabase } from '@/lib/supabase'

const TABLE = 'disponibilidad'

export async function getDisponibilidadByDocente(docenteId, periodoId) {
  let query = supabase
    .from(TABLE)
    .select('*')
    .eq('docente_id', docenteId)
    .order('fecha')
    .order('hora_inicio')

  if (periodoId) {
    query = query.eq('periodo_id', periodoId)
  }

  const { data, error } = await query
  if (error) throw error
  return data
}

export async function getDisponibilidadByPeriodo(periodoId) {
  const { data, error } = await supabase
    .from(TABLE)
    .select('*, docentes(nombre)')
    .eq('periodo_id', periodoId)
    .order('fecha')
  if (error) throw error
  return data
}

// Lean projection used to build the solver payload
export async function getDisponibilidadForSolver(periodoId) {
  const { data, error } = await supabase
    .from(TABLE)
    .select('docente_id, fecha, hora_inicio')
    .eq('periodo_id', periodoId)
  if (error) throw error
  return data
}

export async function upsertDisponibilidad(slots) {
  const { data, error } = await supabase
    .from(TABLE)
    .upsert(slots, { onConflict: 'docente_id,periodo_id,fecha,hora_inicio' })
    .select()
  if (error) throw error
  return data
}

// Replaces the whole availability grid of a docente for a periodo
export async function replaceDisponibilidad(docenteId, periodoId, slots) {
  const { error: delError } = await supabase
    .from(TABLE)
    .delete()
    .eq('docente_id', docenteId)
    .eq('periodo_id', periodoId)
  if (delError) throw delError

  if (!slots.length) return []

  const { data, error } = await supabase.from(TABLE).insert(slots).select()
  if (error) throw error
  return data
}

export async function deleteDisponibilidad(id) {
  const { error } = await supabase.from(TABLE).delete().eq('id', id)
  if (error) throw error
}
