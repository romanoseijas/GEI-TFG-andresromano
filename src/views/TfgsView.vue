<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useTfgsStore } from '@/stores/tfgs'
import { useDocentesStore } from '@/stores/docentes'

const store = useTfgsStore()
const docentesStore = useDocentesStore()
const dialog = ref(false)
const editMode = ref(false)
const editId = ref(null)
const form = ref({ titulo: '', estudiante: '', tutor_id: null, mencion: '', idioma: 'Castellano', titulacion: '' })

const idiomas = ['Castellano', 'Inglés']
const menciones = ['Ingeniería del Software', 'Computación', 'Sistemas de Información', 'Tecnologías de la Información']

const tutoresDisponibles = computed(() =>
  form.value.idioma === 'Inglés'
    ? docentesStore.docentes.filter((d) => d.acepta_ingles)
    : docentesStore.docentes
)

// If the TFG is switched to English and the current tutor doesn't accept English TFGs, clear the selection
watch(
  () => form.value.idioma,
  (idioma) => {
    if (idioma !== 'Inglés') return
    const tutorValido = tutoresDisponibles.value.some((d) => d.id === form.value.tutor_id)
    if (!tutorValido) form.value.tutor_id = null
  }
)

onMounted(() => {
  store.fetchTfgs()
  docentesStore.fetchDocentes()
})

function openNew() {
  editMode.value = false
  form.value = { titulo: '', estudiante: '', tutor_id: null, mencion: '', idioma: 'Castellano', titulacion: '' }
  dialog.value = true
}

function openEdit(tfg) {
  editMode.value = true
  editId.value = tfg.id
  const tutorValido =
    tfg.idioma !== 'Inglés' || docentesStore.docentes.some((d) => d.id === tfg.tutor_id && d.acepta_ingles)
  form.value = {
    titulo: tfg.titulo,
    estudiante: tfg.estudiante,
    tutor_id: tutorValido ? tfg.tutor_id : null,
    mencion: tfg.mencion,
    idioma: tfg.idioma,
    titulacion: tfg.titulacion,
  }
  dialog.value = true
}

async function save() {
  if (editMode.value) {
    await store.editTfg(editId.value, form.value)
  } else {
    await store.addTfg(form.value)
  }
  dialog.value = false
}

async function remove(id) {
  if (confirm('¿Eliminar este TFG?')) {
    await store.removeTfg(id)
  }
}
</script>

<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h1 class="text-h4">TFGs</h1>
      <v-spacer />
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openNew">Nuevo</v-btn>
    </div>

    <v-alert v-if="store.error" type="error" variant="tonal" class="mb-4">{{ store.error }}</v-alert>

    <v-card>
      <v-data-table
        :items="store.tfgs"
        :headers="[
          { title: 'Título', key: 'titulo' },
          { title: 'Estudiante', key: 'estudiante' },
          { title: 'Tutor', key: 'docentes.nombre' },
          { title: 'Mención', key: 'mencion' },
          { title: 'Idioma', key: 'idioma' },
          { title: '', key: 'actions', sortable: false },
        ]"
        :loading="store.loading"
        items-per-page="10"
      >
        <template #item.idioma="{ item }">
          <v-chip size="small" :color="item.idioma === 'Inglés' ? 'info' : 'default'" variant="tonal">
            {{ item.idioma }}
          </v-chip>
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
    <v-dialog v-model="dialog" max-width="600">
      <v-card>
        <v-card-title>{{ editMode ? 'Editar' : 'Nuevo' }} TFG</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.titulo" label="Título" variant="outlined" class="mb-2" />
          <v-text-field v-model="form.estudiante" label="Estudiante" variant="outlined" class="mb-2" />
          <v-select
            v-model="form.tutor_id"
            :items="tutoresDisponibles"
            item-title="nombre"
            item-value="id"
            label="Tutor/a"
            :hint="form.idioma === 'Inglés' ? 'Solo se muestran los docentes que aceptan tribunales en inglés' : ''"
            persistent-hint
            variant="outlined"
            class="mb-2"
          />
          <v-select v-model="form.mencion" :items="menciones" label="Mención" variant="outlined" class="mb-2" />
          <v-select v-model="form.idioma" :items="idiomas" label="Idioma" variant="outlined" class="mb-2" />
          <v-text-field v-model="form.titulacion" label="Titulación" variant="outlined" />
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
