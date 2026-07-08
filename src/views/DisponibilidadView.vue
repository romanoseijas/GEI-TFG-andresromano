<script setup>
import { ref, onMounted, computed } from 'vue'
import { useDisponibilidadStore } from '@/stores/disponibilidad'
import { usePeriodosStore } from '@/stores/periodos'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const disponibilidadStore = useDisponibilidadStore()
const periodosStore = usePeriodosStore()

const selectedPeriodo = ref(null)
const saving = ref(false)
const snackbar = ref(false)

const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
const hours = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30']

// Local grid state (day -> set of hours)
const grid = ref({})
days.forEach((d) => (grid.value[d] = new Set()))

onMounted(async () => {
  await periodosStore.fetchPeriodos()
  const abierto = periodosStore.periodos.find((p) => p.estado === 'ABIERTO')
  if (abierto) selectedPeriodo.value = abierto.id
})

function isSelected(day, hour) {
  return grid.value[day]?.has(hour)
}

function toggle(day, hour) {
  if (grid.value[day].has(hour)) {
    grid.value[day].delete(hour)
  } else {
    grid.value[day].add(hour)
  }
}

async function save() {
  saving.value = true
  try {
    const slots = []
    for (const day of days) {
      for (const hour of grid.value[day]) {
        slots.push({
          docente_id: auth.docenteId,
          periodo_id: selectedPeriodo.value,
          dia_semana: day.toLowerCase(),
          hora_inicio: hour,
        })
      }
    }
    await disponibilidadStore.saveSlots(slots)
    snackbar.value = true
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

    <v-select
      v-model="selectedPeriodo"
      :items="periodosStore.periodos"
      item-title="nombre"
      item-value="id"
      label="Periodo"
      variant="outlined"
      class="mb-4"
      style="max-width: 400px"
    />

    <v-card>
      <div class="calendar-grid">
        <div class="calendar-header">
          <div class="time-col"></div>
          <div v-for="day in days" :key="day" class="day-col text-center font-weight-medium pa-2">
            {{ day }}
          </div>
        </div>
        <div class="calendar-body">
          <div v-for="hour in hours" :key="hour" class="calendar-row">
            <div class="time-col text-caption pa-1 text-center">{{ hour }}</div>
            <div
              v-for="day in days"
              :key="day + hour"
              class="day-col slot"
              :class="{ selected: isSelected(day, hour) }"
              @click="toggle(day, hour)"
            />
          </div>
        </div>
      </div>
    </v-card>

    <v-snackbar v-model="snackbar" color="success" :timeout="2000">
      Disponibilidad guardada
    </v-snackbar>
  </div>
</template>

<style scoped>
.calendar-grid { overflow-x: auto; }
.calendar-header, .calendar-row { display: flex; }
.time-col { width: 60px; min-width: 60px; }
.day-col { flex: 1; min-width: 80px; }
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
