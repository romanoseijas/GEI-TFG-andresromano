import { supabase } from '@/lib/supabase'

const TABLE = 'docentes'

export async function getDocentes() {
  const { data, error } = await supabase.from(TABLE).select('*').order('nombre')
  if (error) throw error
  return data
}

export async function getDocenteByUserId(userId) {
  const { data, error } = await supabase.from(TABLE).select('*').eq('user_id', userId).single()
  if (error) throw error
  return data
}

export async function getDocenteById(id) {
  const { data, error } = await supabase.from(TABLE).select('*').eq('id', id).single()
  if (error) throw error
  return data
}

export async function createDocente(docente) {
  const { data, error } = await supabase.from(TABLE).insert(docente).select().single()
  if (error) throw error
  return data
}

export async function updateDocente(id, changes) {
  const { data, error } = await supabase.from(TABLE).update(changes).eq('id', id).select().single()
  if (error) throw error
  return data
}

export async function deleteDocente(id) {
  const { error } = await supabase.from(TABLE).delete().eq('id', id)
  if (error) throw error
}

export async function createDocenteAccount(docenteId, email, password, nombre) {
  const {
    data: { session },
  } = await supabase.auth.getSession()
  const response = await supabase.functions.invoke('create-docente-account', {
    body: { docente_id: docenteId, email, password, nombre },
  })
  if (response.error) throw new Error(response.error.message || 'Error creating account')
  if (response.data?.error) throw new Error(response.data.error)
  return response.data
}
