<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useDisponibilidadStore } from '@/stores/disponibilidad'
import { usePeriodosStore } from '@/stores/periodos'
import { useAuthStore } from '@/stores/auth'
import { workingDays, timeBlocks } from '@/lib/schedule'

const auth = useAuthStore()
const disponibilidadStore = useDisponibilidadStore()
const periodosStore = usePeriodosStore()

const selectedPeriodo = ref(null)
const saving = ref(false)
const loading = ref(false)
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

// Set of "YYYY-MM-DD|HH:MM" keys
const selected = ref(new Set())

const periodo = computed(() =>
  periodosStore.periodos.find((p) => p.id === selectedPeriodo.value)
)
const days = computed(() =>
  workingDays(periodo.value?.fecha_inicio, periodo.value?.fecha_fin)
)
const hours = computed(() =>
  timeBlocks(periodo.value?.hora_inicio_dia, periodo.value?.hora_fin_dia)
)
const total = computed(() => selected.value.size)

const key = (fecha, hora) => `${fecha}|${hora}`

onMounted(async () => {
  await periodosStore.fetchPeriodos()
  const abierto = periodosStore.periodos.find((p) => p.estado === 'ABIERTO')
  selectedPeriodo.value = (abierto || periodosStore.periodos[0])?.id ?? null
})

watch([selectedPeriodo, () => auth.docenteId], loadGrid, { immediate: true })

async function loadGrid() {
  selected.value = new Set()
  if (!selectedPeriodo.value || !auth.docenteId) return
  loading.value = true
  try {
    await disponibilidadStore.fetchByDocente(auth.docenteId, selectedPeriodo.value)
    const next = new Set()
    for (const s of disponibilidadStore.slots) {
      next.add(key(String(s.fecha).slice(0, 10), String(s.hora_inicio).slice(0, 5)))
    }
    selected.value = next
  } finally {
    loading.value = false
  }
}

function isSelected(fecha, hora) {
  return selected.value.has(key(fecha, hora))
}

function toggle(fecha, hora) {
  const next = new Set(selected.value)
  const k = key(fecha, hora)
  next.has(k) ? next.delete(k) : next.add(k)
  selected.value = next
}

function toggleDay(fecha) {
  const next = new Set(selected.value)
  const allSet = hours.value.every((h) => next.has(key(fecha, h)))
  for (const h of hours.value) {
    allSet ? next.delete(key(fecha, h)) : next.add(key(fecha, h))
  }
  selected.value = next
}

function toggleHour(hora) {
  const next = new Set(selected.value)
  const allSet = days.value.every((d) => next.has(key(d.fecha, hora)))
  for (const d of days.value) {
    allSet ? next.delete(key(d.fecha, hora)) : next.add(key(d.fecha, hora))
  }
  selected.value = next
}

function selectAll() {
  const next = new Set()
  for (const d of days.value) for (const h of hours.value) next.add(key(d.fecha, h))
  selected.value = next
}

function clearAll() {
  selected.value = new Set()
}

function notify(text, color = 'success') {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

async function save() {
  if (!auth.docenteId) return notify('Tu usuario no está vinculado a ningún docente', 'error')
  if (!selectedPeriodo.value) return notify('Selecciona un periodo', 'error')

  saving.value = true
  try {
    const slots = [...selected.value].map((k) => {
      const [fecha, hora_inicio] = k.split('|')
      return {
        docente_id: auth.docenteId,
        periodo_id: selectedPeriodo.value,
        fecha,
        hora_inicio,
      }
    })
    await disponibilidadStore.replaceSlots(auth.docenteId, selectedPeriodo.value, slots)
    notify(`Disponibilidad guardada (${slots.length} bloques)`)
  } catch (e) {
    notify(e.message || 'No se pudo guardar la disponibilidad', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Mi Disponibilidad</h1>
      <v-spacer />
      <v-btn color="primary" prepend-icon="mdi-content-save" :loading="saving" @click="save">
        Guardar
      </v-btn>
    </div>

    <div class="d-flex align-center ga-4 mb-4 flex-wrap">
      <v-select
        v-model="selectedPeriodo"
        :items="periodosStore.periodos"
        item-title="nombre"
        item-value="id"
        label="Periodo"
        variant="outlined"
        hide-details
        density="comfortable"
        style="max-width: 360px"
      />
      <v-btn variant="text" size="small" @click="selectAll">Marcar todo</v-btn>
      <v-btn variant="text" size="small" @click="clearAll">Limpiar</v-btn>
      <v-chip variant="tonal" color="primary">{{ total }} bloques marcados</v-chip>
    </div>

    <v-alert v-if="!auth.docenteId" type="warning" variant="tonal" class="mb-4">
      Tu usuario no está vinculado a una ficha de docente, no podrás guardar disponibilidad.
    </v-alert>

    <v-alert v-else-if="!periodo" type="info" variant="tonal">
      Selecciona un periodo de defensa para marcar tu disponibilidad.
    </v-alert>

    <v-alert v-else-if="!days.length || !hours.length" type="warning" variant="tonal">
      El periodo no tiene días laborables o su ventana horaria diaria no es válida.
      Pide al administrador que revise la configuración del periodo.
    </v-alert>

    <v-card v-else>
      <v-card-subtitle class="pt-3">
        Marca los bloques de {{ hours.length ? '30' : '' }} minutos en los que puedes asistir a una
        defensa. Pulsa una fecha o una hora para marcar la fila/columna completa.
      </v-card-subtitle>
      <v-progress-linear v-if="loading" indeterminate />
      <div class="calendar-grid pa-2">
        <div class="calendar-header">
          <div class="time-col"></div>
          <div
            v-for="d in days"
            :key="d.fecha"
            class="day-col text-center pa-1 day-head"
            @click="toggleDay(d.fecha)"
          >
            <div class="text-caption font-weight-medium">{{ d.diaSemana }}</div>
            <div class="text-caption text-medium-emphasis">{{ d.fecha.slice(5) }}</div>
          </div>
        </div>
        <div class="calendar-body">
          <div v-for="hora in hours" :key="hora" class="calendar-row">
            <div class="time-col text-caption pa-1 text-center hour-head" @click="toggleHour(hora)">
              {{ hora }}
            </div>
            <div
              v-for="d in days"
              :key="d.fecha + hora"
              class="day-col slot"
              :class="{ selected: isSelected(d.fecha, hora) }"
              @click="toggle(d.fecha, hora)"
            />
          </div>
        </div>
      </div>
    </v-card>

    <v-snackbar v-model="snackbar" :color="snackbarColor" :timeout="2500">
      {{ snackbarText }}
    </v-snackbar>
  </div>
</template>

<style scoped>
.calendar-grid { overflow-x: auto; }
.calendar-header, .calendar-row { display: flex; }
.time-col { width: 64px; min-width: 64px; }
.day-col { flex: 1; min-width: 74px; }
.day-head, .hour-head { cursor: pointer; user-select: none; }
.day-head:hover, .hour-head:hover { background: #eeeeee; border-radius: 4px; }
.slot {
  height: 24px;
  margin: 1px;
  border-radius: 4px;
  background: #f0f0f0;
  cursor: pointer;
  transition: background 0.15s;
}
.slot:hover { background: #e3f2fd; }
.slot.selected { background: #4caf50; }
</style>
