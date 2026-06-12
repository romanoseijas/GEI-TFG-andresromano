import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/',
      component: () => import('@/layouts/DefaultLayout.vue'),
      children: [
        { path: '', redirect: '/dashboard' },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'docentes',
          name: 'docentes',
          component: () => import('@/views/DocentesView.vue'),
        },
        {
          path: 'periodos',
          name: 'periodos',
          component: () => import('@/views/PeriodosView.vue'),
        },
        {
          path: 'disponibilidad',
          name: 'disponibilidad',
          component: () => import('@/views/DisponibilidadView.vue'),
        },
        {
          path: 'tfgs',
          name: 'tfgs',
          component: () => import('@/views/TfgsView.vue'),
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Wait for initial auth check
  if (auth.loading) await auth.init()

  if (to.name !== 'login' && !auth.isAuthenticated) return '/login'
  if (to.name === 'login' && auth.isAuthenticated) return '/dashboard'
})

export default router
