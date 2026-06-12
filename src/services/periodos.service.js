import { supabase } from '@/lib/supabase'

const TABLE = 'periodos'

export async function getPeriodos() {
  const { data, error } = await supabase
    .from(TABLE)
    .select('*')
    .order('fecha_inicio', { ascending: false })
  if (error) throw error
  return data
}

export async function getPeriodoById(id) {
  const { data, error } = await supabase
    .from(TABLE)
    .select('*')
    .eq('id', id)
    .single()
  if (error) throw error
  return data
}

export async function createPeriodo(periodo) {
  const { data, error } = await supabase
    .from(TABLE)
    .insert(periodo)
    .select()
    .single()
  if (error) throw error
  return data
}

export async function updatePeriodo(id, changes) {
  const { data, error } = await supabase
    .from(TABLE)
    .update(changes)
    .eq('id', id)
    .select()
    .single()
  if (error) throw error
  return data
}

export async function deletePeriodo(id) {
  const { error } = await supabase
    .from(TABLE)
    .delete()
    .eq('id', id)
  if (error) throw error
}
