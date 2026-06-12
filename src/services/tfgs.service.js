import { supabase } from '@/lib/supabase'

const TABLE = 'tfgs'

export async function getTfgs() {
  const { data, error } = await supabase
    .from(TABLE)
    .select('*, docentes!tfgs_tutor_id_fkey(nombre)')
    .order('titulo')
  if (error) throw error
  return data
}

export async function getTfgById(id) {
  const { data, error } = await supabase
    .from(TABLE)
    .select('*, docentes!tfgs_tutor_id_fkey(nombre)')
    .eq('id', id)
    .single()
  if (error) throw error
  return data
}

export async function createTfg(tfg) {
  const { data, error } = await supabase
    .from(TABLE)
    .insert(tfg)
    .select()
    .single()
  if (error) throw error
  return data
}

export async function updateTfg(id, changes) {
  const { data, error } = await supabase
    .from(TABLE)
    .update(changes)
    .eq('id', id)
    .select()
    .single()
  if (error) throw error
  return data
}

export async function deleteTfg(id) {
  const { error } = await supabase
    .from(TABLE)
    .delete()
    .eq('id', id)
  if (error) throw error
}
