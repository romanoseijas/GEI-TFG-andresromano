import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authService from '@/services/auth.service'
import { getDocenteByUserId } from '@/services/docentes.service'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const profile = ref(null)
  const docente = ref(null)
  const loading = ref(true)

  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => profile.value?.rol === 'ADMIN')
  const isDocente = computed(() => profile.value?.rol === 'DOCENTE')
  const docenteId = computed(() => docente.value?.id)

  async function init() {
    try {
      const session = await authService.getSession()
      if (session?.user) {
        user.value = session.user
        profile.value = await authService.getProfile(session.user.id)
        if (profile.value?.rol === 'DOCENTE') {
          try {
            docente.value = await getDocenteByUserId(session.user.id)
          } catch (e) {
            // Docente record may not exist yet
            console.warn('No docente record linked:', e.message)
          }
        }
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
    if (profile.value?.rol === 'DOCENTE') {
      try {
        docente.value = await getDocenteByUserId(authUser.id)
      } catch (e) {
        console.warn('No docente record linked:', e.message)
      }
    }
  }

  async function logout() {
    await authService.signOut()
    user.value = null
    profile.value = null
    docente.value = null
  }

  // Listen for auth changes (token refresh, etc.)
  authService.onAuthChange((event, session) => {
    if (event === 'SIGNED_OUT') {
      user.value = null
      profile.value = null
      docente.value = null
    }
  })

  return {
    user,
    profile,
    docente,
    loading,
    isAuthenticated,
    isAdmin,
    isDocente,
    docenteId,
    init,
    login,
    logout,
  }
})
