<script setup>
import { ref, onMounted } from 'vue'
import { useDocentesStore } from '@/stores/docentes'

const store = useDocentesStore()
const dialog = ref(false)
const editMode = ref(false)
const form = ref({ nombre: '', email: '', departamento: '', categoria: '', antiguedad: null, acepta_ingles: false })
const editId = ref(null)

onMounted(() => store.fetchDocentes())

function openNew() {
  editMode.value = false
  form.value = { nombre: '', email: '', departamento: '', categoria: '', antiguedad: null, acepta_ingles: false }
  dialog.value = true
}

function openEdit(docente) {
  editMode.value = true
  editId.value = docente.id
  form.value = { ...docente }
  dialog.value = true
}

async function save() {
  if (editMode.value) {
    await store.editDocente(editId.value, form.value)
  } else {
    await store.addDocente(form.value)
  }
  dialog.value = false
}

async function remove(id) {
  if (confirm('¿Eliminar este docente?')) {
    await store.removeDocente(id)
  }
}
</script>

<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">Docentes</h1>
      <v-spacer />
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openNew">Nuevo</v-btn>
    </div>

    <v-alert v-if="store.error" type="error" variant="tonal" class="mb-4">{{ store.error }}</v-alert>

    <v-card>
      <v-data-table
        :items="store.docentes"
        :headers="[
          { title: 'Nombre', key: 'nombre' },
          { title: 'Email', key: 'email' },
          { title: 'Departamento', key: 'departamento' },
          { title: 'Categoría', key: 'categoria' },
          { title: 'Antigüedad', key: 'antiguedad', align: 'center' },
          { title: 'Inglés', key: 'acepta_ingles', align: 'center' },
          { title: '', key: 'actions', sortable: false },
        ]"
        :loading="store.loading"
        items-per-page="10"
      >
        <template #item.acepta_ingles="{ item }">
          <v-icon :color="item.acepta_ingles ? 'success' : 'grey'" size="small">
            {{ item.acepta_ingles ? 'mdi-check' : 'mdi-close' }}
          </v-icon>
        </template>
        <template #item.antiguedad="{ item }">
          {{ item.antiguedad }} años
        </template>
        <template #item.actions="{ item }">
          <v-btn icon variant="text" size="small" @click="openEdit(item)">
            <v-icon size="small">mdi-pencil</v-icon>
          </v-btn>
          <v-btn icon variant="text" size="small" color="error" @click="remove(item.id)">
            <v-icon size="small">mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog -->
    <v-dialog v-model="dialog" max-width="500">
      <v-card>
        <v-card-title>{{ editMode ? 'Editar' : 'Nuevo' }} Docente</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.nombre" label="Nombre" variant="outlined" class="mb-2" />
          <v-text-field v-model="form.email" label="Email" variant="outlined" class="mb-2" />
          <v-text-field v-model="form.departamento" label="Departamento" variant="outlined" class="mb-2" />
          <v-text-field v-model="form.categoria" label="Categoría" variant="outlined" class="mb-2" />
          <v-text-field v-model.number="form.antiguedad" label="Antigüedad (años)" type="number" variant="outlined" class="mb-2" />
          <v-switch v-model="form.acepta_ingles" label="Acepta tribunales en inglés" color="primary" />
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
