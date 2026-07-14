<script setup>
import { ref, onMounted } from 'vue'
import { useDocentesStore } from '@/stores/docentes'

const store = useDocentesStore()
const dialog = ref(false)
const accountDialog = ref(false)
const editMode = ref(false)
const form = ref({ nombre: '', email: '', departamento: '', categoria: '', antiguedad: null, acepta_ingles: false })
const accountForm = ref({ email: '', password: '' })
const accountDocente = ref(null)
const accountLoading = ref(false)
const accountError = ref(null)
const deleteAccountLoading = ref(null)
const removeLoading = ref(null)
const editId = ref(null)

const confirmDialog = ref(false)
const confirmTitle = ref('')
const confirmText = ref('')
const confirmAction = ref(null)

const snackbar = ref(false)
const snackbarText = ref('')

function notifyError(message) {
  snackbarText.value = message
  snackbar.value = true
}

function askConfirm(title, text, action) {
  confirmTitle.value = title
  confirmText.value = text
  confirmAction.value = action
  confirmDialog.value = true
}

async function onConfirm() {
  const action = confirmAction.value
  confirmDialog.value = false
  confirmAction.value = null
  if (action) await action()
}

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

function openCreateAccount(docente) {
  accountDocente.value = docente
  accountForm.value = { email: docente.email || '', password: '' }
  accountError.value = null
  accountDialog.value = true
}

async function createAccount() {
  accountLoading.value = true
  accountError.value = null
  try {
    await store.createAccount(
      accountDocente.value.id,
      accountForm.value.email,
      accountForm.value.password,
      accountDocente.value.nombre
    )
    accountDialog.value = false
  } catch (e) {
    accountError.value = e.message
  } finally {
    accountLoading.value = false
  }
}

async function save() {
  if (editMode.value) {
    await store.editDocente(editId.value, form.value)
  } else {
    await store.addDocente(form.value)
  }
  dialog.value = false
}

function remove(id) {
  askConfirm(
    'Eliminar docente',
    '¿Eliminar este docente? Si tiene una cuenta de acceso, también se eliminará de la autenticación.',
    async () => {
      removeLoading.value = id
      try {
        await store.removeDocente(id)
      } catch (e) {
        notifyError('Error al eliminar docente: ' + e.message)
      } finally {
        removeLoading.value = null
      }
    }
  )
}

function deleteAccount(docente) {
  askConfirm(
    'Eliminar cuenta',
    `¿Eliminar la cuenta de acceso de ${docente.nombre}? El registro del docente se mantendrá.`,
    async () => {
      deleteAccountLoading.value = docente.id
      try {
        await store.deleteAccount(docente.id)
      } catch (e) {
        notifyError('Error al eliminar cuenta: ' + e.message)
      } finally {
        deleteAccountLoading.value = null
      }
    }
  )
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
          <v-btn
            v-if="!item.user_id"
            icon
            variant="text"
            size="small"
            color="info"
            title="Crear cuenta"
            @click="openCreateAccount(item)"
          >
            <v-icon size="small">mdi-account-plus</v-icon>
          </v-btn>
          <v-btn
            v-else
            icon
            variant="text"
            size="small"
            color="success"
            title="Eliminar cuenta"
            :loading="deleteAccountLoading === item.id"
            @click="deleteAccount(item)"
          >
            <v-icon size="small">mdi-account-remove</v-icon>
          </v-btn>
          <v-btn icon variant="text" size="small" color="error" :loading="removeLoading === item.id" @click="remove(item.id)">
            <v-icon size="small">mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog Docente -->
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

    <!-- Dialog Crear Cuenta -->
    <v-dialog v-model="accountDialog" max-width="450">
      <v-card>
        <v-card-title>Crear cuenta para {{ accountDocente?.nombre }}</v-card-title>
        <v-card-text>
          <v-alert v-if="accountError" type="error" variant="tonal" class="mb-3">{{ accountError }}</v-alert>
          <v-text-field v-model="accountForm.email" label="Email" variant="outlined" class="mb-2" />
          <v-text-field v-model="accountForm.password" label="Contraseña" type="password" variant="outlined" class="mb-2" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="accountDialog = false">Cancelar</v-btn>
          <v-btn color="primary" :loading="accountLoading" @click="createAccount">Crear cuenta</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog Confirmación -->
    <v-dialog v-model="confirmDialog" max-width="420">
      <v-card>
        <v-card-title>{{ confirmTitle }}</v-card-title>
        <v-card-text>{{ confirmText }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="confirmDialog = false">Cancelar</v-btn>
          <v-btn color="error" @click="onConfirm">Eliminar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" color="error" timeout="5000">
      {{ snackbarText }}
      <template #actions>
        <v-btn variant="text" @click="snackbar = false">Cerrar</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>
