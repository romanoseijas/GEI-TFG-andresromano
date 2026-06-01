import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.rol === 'ADMIN')

  function login(email, password) {
    if (email === 'admin@udc.es' && password === '1234') {
      user.value = { email, nombre: 'Admin UDC', rol: 'ADMIN' }
    } else if (email === 'docente@udc.es' && password === '1234') {
      user.value = { email, nombre: 'Andrés Romano', rol: 'DOCENTE' }
    } else {
      return false
    }
    localStorage.setItem('user', JSON.stringify(user.value))
    return true
  }

  function logout() {
    user.value = null
    localStorage.removeItem('user')
  }

  return { user, isAuthenticated, isAdmin, login, logout }
})
