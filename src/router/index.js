import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import DashboardView from '@/views/DashboardView.vue'
import DocentesView from '@/views/DocentesView.vue'
import PeriodosView from '@/views/PeriodosView.vue'
import DisponibilidadView from '@/views/DisponibilidadView.vue'
import TfgsView from '@/views/TfgsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/',
      component: DefaultLayout,
      children: [
        { path: '', redirect: '/dashboard' },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView,
        },
        {
          path: 'docentes',
          name: 'docentes',
          meta: { requiresAdmin: true },
          component: DocentesView,
        },
        {
          path: 'periodos',
          name: 'periodos',
          meta: { requiresAdmin: true },
          component: PeriodosView,
        },
        {
          path: 'disponibilidad',
          name: 'disponibilidad',
          component: DisponibilidadView,
        },
        {
          path: 'tfgs',
          name: 'tfgs',
          meta: { requiresAdmin: true },
          component: TfgsView,
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

  // Role-based access control
  if (to.meta.requiresAdmin && !auth.isAdmin) return '/disponibilidad'
})

export default router
