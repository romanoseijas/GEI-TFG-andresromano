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
  duracion_defensa: 30,
  estado: 'BORRADOR',
  num_miembros: 3,
  max_tribunales: 5,
})

const estados = ['BORRADOR', 'ABIERTO', 'CERRADO', 'GENERADO', 'PUBLICADO']
const estadoColor = { BORRADOR: 'grey', ABIERTO: 'success', CERRADO: 'warning', GENERADO: 'info', PUBLICADO: 'primary' }

onMounted(() => store.fetchPeriodos())

function openNew() {
  editMode.value = false
  form.value = { nombre: '', fecha_inicio: '', fecha_fin: '', duracion_defensa: 30, estado: 'BORRADOR', num_miembros: 3, max_tribunales: 5 }
  dialog.value = true
}

function openEdit(periodo) {
  editMode.value = true
  editId.value = periodo.id
  form.value = { ...periodo }
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
            <p><strong>Duración defensa:</strong> {{ p.duracion_defensa }} min</p>
            <p><strong>Miembros tribunal:</strong> {{ p.num_miembros }}</p>
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
          <v-text-field v-model="form.fecha_inicio" label="Fecha inicio" type="date" variant="outlined" class="mb-2" />
          <v-text-field v-model="form.fecha_fin" label="Fecha fin" type="date" variant="outlined" class="mb-2" />
          <v-text-field v-model.number="form.duracion_defensa" label="Duración defensa (min)" type="number" variant="outlined" class="mb-2" />
          <v-text-field v-model.number="form.num_miembros" label="Nº miembros tribunal" type="number" variant="outlined" class="mb-2" />
          <v-text-field v-model.number="form.max_tribunales" label="Máx. tribunales por docente" type="number" variant="outlined" class="mb-2" />
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
