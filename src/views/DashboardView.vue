<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useDocentesStore } from '@/stores/docentes'
import { usePeriodosStore } from '@/stores/periodos'
import { useTfgsStore } from '@/stores/tfgs'

const auth = useAuthStore()
const docentesStore = useDocentesStore()
const periodosStore = usePeriodosStore()
const tfgsStore = useTfgsStore()

onMounted(() => {
  docentesStore.fetchDocentes()
  periodosStore.fetchPeriodos()
  tfgsStore.fetchTfgs()
})
</script>

<template>
  <div>
    <h1 class="text-h4 mb-2">Dashboard</h1>
    <p class="text-body-1 mb-6 text-medium-emphasis">
      Bienvenido, {{ auth.profile?.nombre || auth.user?.email }}
    </p>

    <v-row>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4">
          <v-icon color="primary" class="mb-2">mdi-account-group</v-icon>
          <p class="text-h5 font-weight-bold">{{ docentesStore.docentes.length }}</p>
          <p class="text-caption text-medium-emphasis">Docentes</p>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4">
          <v-icon color="success" class="mb-2">mdi-book-open-variant</v-icon>
          <p class="text-h5 font-weight-bold">{{ tfgsStore.tfgs.length }}</p>
          <p class="text-caption text-medium-emphasis">TFGs</p>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4">
          <v-icon color="warning" class="mb-2">mdi-calendar-range</v-icon>
          <p class="text-h5 font-weight-bold">{{ periodosStore.periodos.length }}</p>
          <p class="text-caption text-medium-emphasis">Periodos</p>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4">
          <v-icon color="info" class="mb-2">mdi-calendar-check</v-icon>
          <p class="text-h5 font-weight-bold">
            {{ periodosStore.periodos.filter(p => p.estado === 'ABIERTO').length }}
          </p>
          <p class="text-caption text-medium-emphasis">Periodos activos</p>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent periods table -->
    <v-card class="mt-6" v-if="periodosStore.periodos.length">
      <v-card-title>Periodos recientes</v-card-title>
      <v-table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Inicio</th>
            <th>Fin</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in periodosStore.periodos.slice(0, 5)" :key="p.id">
            <td>{{ p.nombre }}</td>
            <td>{{ p.fecha_inicio }}</td>
            <td>{{ p.fecha_fin }}</td>
            <td>
              <v-chip size="small" variant="tonal" :color="p.estado === 'ABIERTO' ? 'success' : 'grey'">
                {{ p.estado }}
              </v-chip>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </div>
</template>
