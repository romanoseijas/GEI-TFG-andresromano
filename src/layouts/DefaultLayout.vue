<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <v-navigation-drawer app>
    <v-list-item class="pa-4" prepend-icon="mdi-school" title="TribunalUDC" subtitle="Gestión de Tribunales" />
    <v-divider />
    <v-list nav>
      <v-list-item to="/dashboard" prepend-icon="mdi-view-dashboard" title="Dashboard" />
    </v-list>
    <template #append>
      <div class="pa-4">
        <v-btn block variant="outlined" prepend-icon="mdi-logout" @click="logout">
          Cerrar sesión
        </v-btn>
      </div>
    </template>
  </v-navigation-drawer>

  <v-app-bar app flat border="b">
    <v-toolbar-title>{{ auth.user?.nombre }}</v-toolbar-title>
    <v-chip variant="tonal" color="primary" class="mr-4">{{ auth.user?.rol }}</v-chip>
  </v-app-bar>

  <v-main>
    <v-container>
      <router-view />
    </v-container>
  </v-main>
</template>
