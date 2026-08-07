<script setup>
import { ref, onMounted } from 'vue'
import { usePeriodosStore } from '@/stores/periodos'

const store = usePeriodosStore()
const dialog = ref(false)
const editMode = ref(false)
const editId = ref(null)
const form = ref({
  nombre: '',
  fecha_inicio: '',
  fecha_fin: '',
  hora_inicio_dia: '09:00',
  hora_fin_dia: '14:00',
  duracion_defensa: 30,
  estado: 'BORRADOR',
  num_miembros: 3,
  num_aulas: 3,
  max_tribunales: 5,
})

const emptyForm = () => ({
  nombre: '',
  fecha_inicio: '',
  fecha_fin: '',
  hora_inicio_dia: '09:00',
  hora_fin_dia: '14:00',
  duracion_defensa: 30,
  estado: 'BORRADOR',
  num_miembros: 3,
  num_aulas: 3,
  max_tribunales: 5,
})

const estados = ['BORRADOR', 'ABIERTO', 'CERRADO', 'GENERADO', 'PUBLICADO']
const estadoColor = { BORRADOR: 'grey', ABIERTO: 'success', CERRADO: 'warning', GENERADO: 'info', PUBLICADO: 'primary' }

onMounted(() => store.fetchPeriodos())

function openNew() {
  editMode.value = false
  form.value = emptyForm()
  dialog.value = true
}

function openEdit(periodo) {
  editMode.value = true
  editId.value = periodo.id
  form.value = { ...emptyForm(), ...periodo }
  dialog.value = true
}

async function save() {
  if (editMode.value) {
    await store.editPeriodo(editId.value, form.value)
  } else {
    await store.addPeriodo(form.value)
  }
  dialog.value = false
}

async function remove(id) {
  if (confirm('¿Eliminar este periodo?')) {
    await store.removePeriodo(id)
  }
}
</script>

<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Periodos de Defensa</h1>
      <v-spacer />
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openNew">Nuevo</v-btn>
    </div>

    <v-alert v-if="store.error" type="error" variant="tonal" class="mb-4">{{ store.error }}</v-alert>

    <v-row>
      <v-col v-for="p in store.periodos" :key="p.id" cols="12" md="6" lg="4">
        <v-card class="h-100">
          <v-card-title class="d-flex align-center">
            {{ p.nombre }}
            <v-spacer />
            <v-chip :color="estadoColor[p.estado]" size="small" variant="tonal">{{ p.estado }}</v-chip>
          </v-card-title>
          <v-card-text>
            <p><strong>Inicio:</strong> {{ p.fecha_inicio }}</p>
            <p><strong>Fin:</strong> {{ p.fecha_fin }}</p>
            <p><strong>Horario diario:</strong> {{ p.hora_inicio_dia }} - {{ p.hora_fin_dia }}</p>
            <p><strong>Duración defensa:</strong> {{ p.duracion_defensa }} min</p>
            <p><strong>Miembros tribunal:</strong> {{ p.num_miembros }}</p>
            <p><strong>Aulas simultáneas:</strong> {{ p.num_aulas }}</p>
            <p><strong>Máx. tribunales/docente:</strong> {{ p.max_tribunales }}</p>
          </v-card-text>
          <v-card-actions>
            <v-btn size="small" @click="openEdit(p)">Editar</v-btn>
            <v-btn size="small" color="error" @click="remove(p.id)">Eliminar</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-progress-linear v-if="store.loading" indeterminate class="mt-4" />

    <!-- Dialog -->
    <v-dialog v-model="dialog" max-width="500">
      <v-card>
        <v-card-title>{{ editMode ? 'Editar' : 'Nuevo' }} Periodo</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.nombre" label="Nombre" variant="outlined" class="mb-2" />
          <v-row density="comfortable">
            <v-col cols="6">
              <v-text-field v-model="form.fecha_inicio" label="Fecha inicio" type="date" variant="outlined"
                class="mb-2" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model="form.fecha_fin" label="Fecha fin" type="date" variant="outlined" class="mb-2" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model="form.hora_inicio_dia" label="Hora inicio (diaria)" type="time" variant="outlined"
                class="mb-2" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model="form.hora_fin_dia" label="Hora fin (diaria)" type="time" variant="outlined"
                class="mb-2" />
            </v-col>
          </v-row>
          <v-text-field v-model.number="form.duracion_defensa" label="Duración defensa (min)" type="number"
            variant="outlined" class="mb-2" hint="Define el paso de la rejilla de horarios" persistent-hint />
          <v-text-field v-model.number="form.num_miembros" label="Nº miembros tribunal" type="number" variant="outlined"
            class="mb-2" />
          <v-text-field v-model.number="form.num_aulas" label="Nº de aulas simultáneas" type="number" variant="outlined"
            class="mb-2" hint="Defensas que pueden celebrarse a la vez" persistent-hint />
          <v-text-field v-model.number="form.max_tribunales" label="Máx. tribunales por docente" type="number"
            variant="outlined" class="mb-2" />
          <v-select v-model="form.estado" :items="estados" label="Estado" variant="outlined" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="dialog = false">Cancelar</v-btn>
          <v-btn color="primary" @click="save">Guardar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
