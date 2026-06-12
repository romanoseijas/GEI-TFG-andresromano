import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authService from '@/services/auth.service'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const profile = ref(null)
  const loading = ref(true)

  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => profile.value?.rol === 'ADMIN')

  async function init() {
    try {
      const session = await authService.getSession()
      if (session?.user) {
        user.value = session.user
        profile.value = await authService.getProfile(session.user.id)
      }
    } catch (e) {
      console.error('Error initializing auth:', e)
    } finally {
      loading.value = false
    }
  }

  async function login(email, password) {
    const { user: authUser } = await authService.signIn(email, password)
    user.value = authUser
    profile.value = await authService.getProfile(authUser.id)
  }

  async function logout() {
    await authService.signOut()
    user.value = null
    profile.value = null
  }

  // Listen for auth changes (token refresh, etc.)
  authService.onAuthChange((event, session) => {
    if (event === 'SIGNED_OUT') {
      user.value = null
      profile.value = null
    }
  })

  return { user, profile, loading, isAuthenticated, isAdmin, init, login, logout }
})
