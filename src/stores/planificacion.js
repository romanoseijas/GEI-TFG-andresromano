import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as solverService from '@/services/solver.service'
import { getPeriodoById } from '@/services/periodos.service'
import { getDocentes } from '@/services/docentes.service'
import { getTfgs } from '@/services/tfgs.service'
import { getDisponibilidadForSolver } from '@/services/disponibilidad.service'

export const usePlanificacionStore = defineStore('planificacion', () => {
  const result = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const periodo = ref(null)

  const asignaciones = computed(() => result.value?.asignaciones || [])
  const cargas = computed(() => result.value?.cargas || [])
  const avisos = computed(() => result.value?.avisos || [])

  /** Assignments grouped by date, then sorted by time and room. */
  const porDia = computed(() => {
    const groups = new Map()
    for (const a of asignaciones.value) {
      if (!groups.has(a.fecha)) groups.set(a.fecha, [])
      groups.get(a.fecha).push(a)
    }
    return [...groups.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([fecha, items]) => ({
        fecha,
        diaSemana: items[0]?.dia_semana || '',
        items: items.sort(
          (x, y) => x.hora_inicio.localeCompare(y.hora_inicio) || x.aula.localeCompare(y.aula),
        ),
      }))
  })

  async function generar(periodoId, { timeLimit = 60 } = {}) {
    loading.value = true
    error.value = null
    result.value = null
    try {
      const [p, docentes, tfgs, disponibilidad] = await Promise.all([
        getPeriodoById(periodoId),
        getDocentes(),
        getTfgs(),
        getDisponibilidadForSolver(periodoId),
      ])
      periodo.value = p
      result.value = await solverService.solve({
        periodo: p,
        docentes,
        tfgs,
        disponibilidad,
        timeLimit,
      })
      return result.value
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  function reset() {
    result.value = null
    error.value = null
    periodo.value = null
  }

  return { result, loading, error, periodo, asignaciones, cargas, avisos, porDia, generar, reset }
})
