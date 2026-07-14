import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as tfgsService from '@/services/tfgs.service'

export const useTfgsStore = defineStore('tfgs', () => {
  const tfgs = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchTfgs() {
    loading.value = true
    error.value = null
    try {
      tfgs.value = await tfgsService.getTfgs()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function addTfg(tfg) {
    await tfgsService.createTfg(tfg)
    await fetchTfgs()
  }

  async function editTfg(id, changes) {
    await tfgsService.updateTfg(id, changes)
    await fetchTfgs()
  }

  async function removeTfg(id) {
    await tfgsService.deleteTfg(id)
    tfgs.value = tfgs.value.filter((t) => t.id !== id)
  }

  return { tfgs, loading, error, fetchTfgs, addTfg, editTfg, removeTfg }
})
