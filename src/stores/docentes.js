import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as docentesService from '@/services/docentes.service'

export const useDocentesStore = defineStore('docentes', () => {
  const docentes = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchDocentes() {
    loading.value = true
    error.value = null
    try {
      docentes.value = await docentesService.getDocentes()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function addDocente(docente) {
    const created = await docentesService.createDocente(docente)
    docentes.value.push(created)
    return created
  }

  async function editDocente(id, changes) {
    const updated = await docentesService.updateDocente(id, changes)
    const idx = docentes.value.findIndex((d) => d.id === id)
    if (idx !== -1) docentes.value[idx] = updated
    return updated
  }

  async function removeDocente(id) {
    const docente = docentes.value.find((d) => d.id === id)
    if (docente?.user_id) {
      await docentesService.deleteDocenteAccount(id)
    }
    await docentesService.deleteDocente(id)
    docentes.value = docentes.value.filter((d) => d.id !== id)
  }

  async function createAccount(docenteId, email, password, nombre) {
    const result = await docentesService.createDocenteAccount(docenteId, email, password, nombre)
    // Update the local docente record with the user_id
    const idx = docentes.value.findIndex((d) => d.id === docenteId)
    if (idx !== -1) docentes.value[idx].user_id = result.user_id
    return result
  }

  async function deleteAccount(docenteId) {
    await docentesService.deleteDocenteAccount(docenteId)
    const idx = docentes.value.findIndex((d) => d.id === docenteId)
    if (idx !== -1) docentes.value[idx].user_id = null
  }

  return {
    docentes,
    loading,
    error,
    fetchDocentes,
    addDocente,
    editDocente,
    removeDocente,
    createAccount,
    deleteAccount,
  }
})
