import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as disponibilidadService from '@/services/disponibilidad.service'

export const useDisponibilidadStore = defineStore('disponibilidad', () => {
  const slots = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchByDocente(docenteId, periodoId) {
    loading.value = true
    error.value = null
    try {
      slots.value = await disponibilidadService.getDisponibilidadByDocente(docenteId, periodoId)
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchByPeriodo(periodoId) {
    loading.value = true
    error.value = null
    try {
      slots.value = await disponibilidadService.getDisponibilidadByPeriodo(periodoId)
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function saveSlots(newSlots) {
    const saved = await disponibilidadService.upsertDisponibilidad(newSlots)
    slots.value = saved
    return saved
  }

  async function removeSlot(id) {
    await disponibilidadService.deleteDisponibilidad(id)
    slots.value = slots.value.filter((s) => s.id !== id)
  }

  return { slots, loading, error, fetchByDocente, fetchByPeriodo, saveSlots, removeSlot }
})
