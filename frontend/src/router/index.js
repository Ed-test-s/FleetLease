import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import RequestsPage from '@/views/RequestsPage.vue'
import ContractsPage from '@/views/ContractsPage.vue'

const routes = [
  {
    path: '/',
    name: 'catalog',
    component: () => import('@/views/CatalogPage.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginPage.vue'),
    meta: { guest: true },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('@/views/ForgotPasswordPage.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterPage.vue'),
    meta: { guest: true },
  },
  {
    path: '/privacy',
    name: 'privacy-policy',
    component: () => import('@/views/PrivacyPolicyPage.vue'),
  },
  {
    path: '/terms',
    name: 'terms-of-use',
    component: () => import('@/views/TermsOfUsePage.vue'),
  },
  {
    path: '/about',
    name: 'about-company',
    component: () => import('@/views/AboutCompanyPage.vue'),
  },
  {
    path: '/vehicles/:id',
    name: 'vehicle-detail',
    component: () => import('@/views/VehicleDetailPage.vue'),
  },
  {
    path: '/favorites',
    name: 'favorites',
    component: () => import('@/views/FavoritesPage.vue'),
    meta: { auth: true, roles: ['client'] },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfilePage.vue'),
    meta: { auth: true },
  },
  {
    path: '/users/:id',
    name: 'user-profile',
    component: () => import('@/views/UserProfilePage.vue'),
  },
  {
    path: '/suppliers',
    name: 'suppliers',
    component: () => import('@/views/SuppliersPage.vue'),
  },
  {
    path: '/lessors',
    name: 'lessors',
    component: () => import('@/views/LessorsPage.vue'),
  },
  {
    path: '/my-vehicles',
    name: 'my-vehicles',
    component: () => import('@/views/MyVehiclesPage.vue'),
    meta: { auth: true, roles: ['supplier'] },
  },
  {
    path: '/my-vehicles/new',
    name: 'vehicle-create',
    component: () => import('@/views/VehicleFormPage.vue'),
    meta: { auth: true, roles: ['supplier'] },
  },
  {
    path: '/my-vehicles/:id/edit',
    name: 'vehicle-edit',
    component: () => import('@/views/VehicleFormPage.vue'),
    meta: { auth: true, roles: ['supplier'] },
  },
  {
    path: '/requests',
    name: 'requests',
    component: RequestsPage,
    meta: { auth: true },
  },
  {
    path: '/contracts',
    name: 'contracts',
    component: ContractsPage,
    meta: { auth: true },
  },
  {
    path: '/contracts/:id',
    name: 'contract-detail',
    component: () => import('@/views/ContractDetailPage.vue'),
    meta: { auth: true },
  },
  {
    path: '/payment/:contractId/:scheduleId',
    name: 'payment',
    component: () => import('@/views/PaymentPage.vue'),
    meta: { auth: true, roles: ['client'] },
  },
  {
    path: '/chats',
    name: 'chats',
    component: () => import('@/views/ChatsPage.vue'),
    meta: { auth: true },
  },
  {
    path: '/chats/:id',
    name: 'chat-detail',
    component: () => import('@/views/ChatDetailPage.vue'),
    meta: { auth: true },
  },
  {
    path: '/notifications',
    name: 'notifications',
    component: () => import('@/views/NotificationsPage.vue'),
    meta: { auth: true },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/views/AdminPage.vue'),
    meta: { auth: true, roles: ['admin'] },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  if (auth.isAuthenticated && !auth.user) {
    await auth.fetchUser()
  }

  if (to.meta.auth && !auth.isAuthenticated) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  if (to.meta.guest && auth.isAuthenticated) {
    return next({ name: 'catalog' })
  }

  if (to.meta.roles && auth.user) {
    if (!to.meta.roles.includes(auth.user.role)) {
      return next({ name: 'catalog' })
    }
  }

  next()
})

export default router
