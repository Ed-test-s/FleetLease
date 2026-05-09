import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import { usersApi } from '@/api/users'
import { useFavoritesStore } from '@/stores/favorites'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))

  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role)
  const userName = computed(() => {
    if (!user.value) return ''
    if (user.value.individual) return user.value.individual.full_name
    if (user.value.entrepreneur) return user.value.entrepreneur.full_name
    if (user.value.company) return user.value.company.company_name
    return user.value.login
  })

  async function login(identifier, password) {
    const { data } = await authApi.login(identifier, password)
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await fetchUser()
  }

  async function register(formData) {
    const { data } = await authApi.register(formData)
    return data
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const { data } = await usersApi.getMe()
      user.value = data
      if (data.role === 'client') {
        const favStore = useFavoritesStore()
        favStore.fetchIds()
      }
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    const favStore = useFavoritesStore()
    favStore.clear()
  }

  return { user, token, isAuthenticated, userRole, userName, login, register, fetchUser, logout }
})
