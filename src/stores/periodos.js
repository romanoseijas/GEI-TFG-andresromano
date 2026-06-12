import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as periodosService from '@/services/periodos.service'

export const usePeriodosStore = defineStore('periodos', () => {
  const periodos = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchPeriodos() {
    loading.value = true
    error.value = null
    try {
      periodos.value = await periodosService.getPeriodos()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function addPeriodo(periodo) {
    const created = await periodosService.createPeriodo(periodo)
    periodos.value.unshift(created)
    return created
  }

  async function editPeriodo(id, changes) {
    const updated = await periodosService.updatePeriodo(id, changes)
    const idx = periodos.value.findIndex((p) => p.id === id)
    if (idx !== -1) periodos.value[idx] = updated
    return updated
  }

  async function removePeriodo(id) {
    await periodosService.deletePeriodo(id)
    periodos.value = periodos.value.filter((p) => p.id !== id)
  }

  return { periodos, loading, error, fetchPeriodos, addPeriodo, editPeriodo, removePeriodo }
})
