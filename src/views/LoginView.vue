<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.message || 'Credenciales incorrectas'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <v-container class="fill-height" fluid>
    <v-row justify="center">
      <v-col cols="12" sm="6" md="4">
        <v-card class="pa-4" elevation="4">
          <v-card-title class="text-center text-h5">TribunalUDC</v-card-title>
          <v-card-subtitle class="text-center">Gestión de Tribunales TFG</v-card-subtitle>
          <v-card-text>
            <v-alert v-if="error" type="error" variant="tonal" class="mb-4" closable>
              {{ error }}
            </v-alert>
            <v-form @submit.prevent="handleLogin">
              <v-text-field v-model="email" label="Email" type="email" variant="outlined" class="mb-2" />
              <v-text-field v-model="password" label="Contraseña" type="password" variant="outlined" class="mb-4" />
              <v-btn type="submit" color="primary" block size="large" :loading="loading">Entrar</v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
