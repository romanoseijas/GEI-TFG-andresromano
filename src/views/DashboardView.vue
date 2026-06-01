<script setup>
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div>
    <h1 class="text-h4 mb-4">Dashboard</h1>
    <p class="text-body-1 mb-6">Bienvenido, {{ auth.user?.nombre }}</p>

    <v-row>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4">
          <v-icon color="primary" class="mb-2">mdi-account-group</v-icon>
          <p class="text-h5 font-weight-bold">12</p>
          <p class="text-caption text-medium-emphasis">Docentes</p>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4">
          <v-icon color="success" class="mb-2">mdi-book-open-variant</v-icon>
          <p class="text-h5 font-weight-bold">6</p>
          <p class="text-caption text-medium-emphasis">TFGs</p>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4">
          <v-icon color="warning" class="mb-2">mdi-gavel</v-icon>
          <p class="text-h5 font-weight-bold">3</p>
          <p class="text-caption text-medium-emphasis">Tribunales</p>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4">
          <v-icon color="info" class="mb-2">mdi-calendar-range</v-icon>
          <p class="text-h5 font-weight-bold">1</p>
          <p class="text-caption text-medium-emphasis">Periodo activo</p>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
