import { supabase } from '@/lib/supabase'

const TABLE = 'docentes'

export async function getDocentes() {
  const { data, error } = await supabase
    .from(TABLE)
    .select('*')
    .order('nombre')
  if (error) throw error
  return data
}

export async function getDocenteById(id) {
  const { data, error } = await supabase
    .from(TABLE)
    .select('*')
    .eq('id', id)
    .single()
  if (error) throw error
  return data
}

export async function createDocente(docente) {
  const { data, error } = await supabase
    .from(TABLE)
    .insert(docente)
    .select()
    .single()
  if (error) throw error
  return data
}

export async function updateDocente(id, changes) {
  const { data, error } = await supabase
    .from(TABLE)
    .update(changes)
    .eq('id', id)
    .select()
    .single()
  if (error) throw error
  return data
}

export async function deleteDocente(id) {
  const { error } = await supabase
    .from(TABLE)
    .delete()
    .eq('id', id)
  if (error) throw error
}
