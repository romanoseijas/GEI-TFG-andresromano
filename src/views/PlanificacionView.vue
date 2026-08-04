<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePlanificacionStore } from '@/stores/planificacion'
import { usePeriodosStore } from '@/stores/periodos'
import { useTfgsStore } from '@/stores/tfgs'
import { defenseSlots } from '@/lib/schedule'

const store = usePlanificacionStore()
const periodosStore = usePeriodosStore()
const tfgsStore = useTfgsStore()

const selectedPeriodo = ref(null)

const periodo = computed(() =>
  periodosStore.periodos.find((p) => p.id === selectedPeriodo.value)
)

// Same slot grid the backend will generate, so the admin can sanity-check capacity
const capacidad = computed(() => {
  if (!periodo.value) return null
  const slots = defenseSlots(periodo.value)
  return {
    slots: slots.length,
    aulas: periodo.value.num_aulas ?? 0,
    huecos: slots.length * (periodo.value.num_aulas ?? 0),
    tfgs: tfgsStore.tfgs.length,
  }
})

onMounted(async () => {
  await Promise.all([periodosStore.fetchPeriodos(), tfgsStore.fetchTfgs()])
  const abierto = periodosStore.periodos.find((p) => ['ABIERTO', 'CERRADO'].includes(p.estado))
  selectedPeriodo.value = (abierto || periodosStore.periodos[0])?.id ?? null
})

async function generar() {
  if (!selectedPeriodo.value) return
  try {
    await store.generar(selectedPeriodo.value)
  } catch {
    // el mensaje ya queda en store.error
  }
}
</script>

<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Planificación</h1>
      <v-spacer />
      <v-btn
        color="primary"
        prepend-icon="mdi-cog-play"
        :loading="store.loading"
        :disabled="!selectedPeriodo"
        @click="generar"
      >
        Generar planificación
      </v-btn>
    </div>

    <v-select
      v-model="selectedPeriodo"
      :items="periodosStore.periodos"
      item-title="nombre"
      item-value="id"
      label="Periodo"
      variant="outlined"
      density="comfortable"
      style="max-width: 400px"
    />

    <v-row v-if="capacidad" class="mb-2">
      <v-col cols="6" md="3">
        <v-card class="pa-3"><p class="text-h6">{{ capacidad.tfgs }}</p><p class="text-caption text-medium-emphasis">TFGs a programar</p></v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card class="pa-3"><p class="text-h6">{{ capacidad.slots }}</p><p class="text-caption text-medium-emphasis">Slots de {{ periodo.duracion_defensa }} min</p></v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card class="pa-3"><p class="text-h6">{{ capacidad.aulas }}</p><p class="text-caption text-medium-emphasis">Aulas simultáneas</p></v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card class="pa-3" :color="capacidad.huecos < capacidad.tfgs ? 'error' : undefined" :variant="capacidad.huecos < capacidad.tfgs ? 'tonal' : 'elevated'">
          <p class="text-h6">{{ capacidad.huecos }}</p>
          <p class="text-caption text-medium-emphasis">Huecos disponibles</p>
        </v-card>
      </v-col>
    </v-row>

    <v-alert v-if="store.error" type="error" variant="tonal" class="mb-4" style="white-space: pre-line">
      {{ store.error }}
    </v-alert>

    <v-alert
      v-for="(aviso, i) in store.avisos"
      :key="i"
      type="warning"
      variant="tonal"
      density="compact"
      class="mb-2"
    >
      {{ aviso }}
    </v-alert>

    <v-progress-linear v-if="store.loading" indeterminate class="mb-4" />

    <template v-if="store.result?.resuelto">
      <v-alert type="success" variant="tonal" class="mb-4">
        {{ store.asignaciones.length }} defensas programadas ·
        tribunales de {{ store.result.tribunal_size }} miembros ·
        carga por docente entre {{ store.result.lmin }} y {{ store.result.lmax }}
        (diferencia {{ store.result.gap }})
      </v-alert>

      <v-card v-for="dia in store.porDia" :key="dia.fecha" class="mb-4">
        <v-card-title class="text-subtitle-1">
          {{ dia.diaSemana }} {{ dia.fecha }}
          <v-chip size="x-small" variant="tonal" class="ml-2">{{ dia.items.length }} defensas</v-chip>
        </v-card-title>
        <v-table density="compact">
          <thead>
            <tr>
              <th style="width: 110px">Hora</th>
              <th style="width: 80px">Aula</th>
              <th>TFG</th>
              <th>Estudiante</th>
              <th>Tutor/a</th>
              <th>Tribunal</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in dia.items" :key="a.tfg_id">
              <td class="text-no-wrap">{{ a.hora_inicio }}–{{ a.hora_fin }}</td>
              <td>{{ a.aula }}</td>
              <td>
                {{ a.titulo }}
                <v-chip v-if="a.idioma === 'Inglés'" size="x-small" color="info" variant="tonal" class="ml-1">EN</v-chip>
              </td>
              <td>{{ a.estudiante }}</td>
              <td class="text-medium-emphasis">{{ a.tutor_nombre || '—' }}</td>
              <td>
                <v-chip
                  v-for="e in a.tribunal"
                  :key="e.docente_id"
                  size="x-small"
                  variant="tonal"
                  class="mr-1 mb-1"
                >
                  {{ e.nombre }}
                </v-chip>
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card>

      <v-card class="mb-4">
        <v-card-title class="text-subtitle-1">Carga por docente</v-card-title>
        <v-table density="compact">
          <thead>
            <tr><th>Docente</th><th style="width: 140px">Tribunales</th></tr>
          </thead>
          <tbody>
            <tr v-for="c in store.cargas" :key="c.docente_id">
              <td>{{ c.nombre }}</td>
              <td>{{ c.num_tribunales }}</td>
            </tr>
          </tbody>
        </v-table>
      </v-card>
    </template>

    <v-alert
      v-else-if="store.result && !store.result.resuelto"
      type="error"
      variant="tonal"
    >
      No se ha encontrado ninguna planificación factible
      ({{ store.result.termination }}).
    </v-alert>
  </div>
</template>
