<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const allNavItems = [
  { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/dashboard' },
  { title: 'Docentes', icon: 'mdi-account-group', to: '/docentes', adminOnly: true },
  { title: 'Periodos', icon: 'mdi-calendar-range', to: '/periodos', adminOnly: true },
  { title: 'Disponibilidad', icon: 'mdi-calendar-clock', to: '/disponibilidad' },
  { title: 'TFGs', icon: 'mdi-book-open-variant', to: '/tfgs', adminOnly: true },
]

const navItems = computed(() =>
  allNavItems.filter((item) => !item.adminOnly || auth.isAdmin)
)

async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <v-navigation-drawer app>
    <v-list-item class="pa-4" prepend-icon="mdi-school" title="TribunalUDC" subtitle="Gestión de Tribunales" />
    <v-divider />
    <v-list nav>
      <v-list-item
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :prepend-icon="item.icon"
        :title="item.title"
      />
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
    <v-toolbar-title>{{ auth.profile?.nombre || auth.user?.email }}</v-toolbar-title>
    <v-chip variant="tonal" color="primary" class="mr-4">{{ auth.profile?.rol || 'USER' }}</v-chip>
  </v-app-bar>

  <v-main>
    <v-container>
      <router-view />
    </v-container>
  </v-main>
</template>
