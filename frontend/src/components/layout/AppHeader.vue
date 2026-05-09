<template>
  <header class="bg-white border-b border-surface-200 sticky top-0 z-50">
    <div class="max-w-screen-2xl mx-auto px-4 sm:px-6">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-2.5">
          <div class="w-9 h-9 bg-primary-500 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 17h8M8 17v-4m8 4v-4m-8 0h8m-8 0V9m8 4V9M4 21h16a1 1 0 001-1V8l-3-4H6L3 8v12a1 1 0 001 1z" />
            </svg>
          </div>
          <span class="text-xl font-bold text-primary-500">FleetLease</span>
        </router-link>

        <!-- Navigation -->
        <nav class="hidden md:flex items-center gap-1">
          <router-link to="/" class="nav-link">Каталог</router-link>
          <router-link to="/suppliers" class="nav-link">Поставщики</router-link>
          <router-link to="/lessors" class="nav-link">Лизингодатели</router-link>

          <template v-if="auth.isAuthenticated">
            <router-link v-if="auth.userRole === 'supplier'" to="/my-vehicles" class="nav-link">
              Мои объявления
            </router-link>
            <router-link to="/requests" class="nav-link">Заявки</router-link>
            <router-link to="/contracts" class="nav-link">Договоры</router-link>
            <router-link to="/chats" class="nav-link">Чаты</router-link>
          </template>
        </nav>

        <!-- Right section -->
        <div class="flex items-center gap-3">
          <CurrencyRatesBar />
          <template v-if="auth.isAuthenticated">
            <!-- Notifications -->
            <router-link to="/notifications" class="relative p-2 text-gray-500 hover:text-primary-500 transition-colors">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
              </svg>
              <span v-if="notifStore.unreadCount > 0"
                    class="absolute -top-0.5 -right-0.5 w-4.5 h-4.5 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                {{ notifStore.unreadCount > 9 ? '9+' : notifStore.unreadCount }}
              </span>
            </router-link>

            <!-- User menu -->
            <div class="relative" ref="menuRef">
              <button @click="showMenu = !showMenu"
                      class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-surface-100 transition-colors">
                <div class="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-semibold overflow-hidden flex-shrink-0">
                  <img v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" class="w-full h-full object-cover" alt="" />
                  <span v-else>{{ auth.userName?.charAt(0)?.toUpperCase() || 'U' }}</span>
                </div>
                <span class="hidden sm:block text-sm font-medium text-gray-700 max-w-[140px] truncate">
                  {{ auth.userName }}
                </span>
                <svg class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              <div v-if="showMenu" class="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border border-surface-200 py-1.5 z-50">
                <router-link to="/profile" class="menu-item" @click="showMenu = false">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0" />
                  </svg>
                  Мой профиль
                </router-link>
                <router-link v-if="auth.userRole === 'client'" to="/favorites" class="menu-item" @click="showMenu = false">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
                  </svg>
                  Избранное
                </router-link>
                <router-link v-if="auth.userRole === 'admin'" to="/admin" class="menu-item" @click="showMenu = false">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Админ-панель
                </router-link>
                <hr class="my-1.5 border-surface-200" />
                <button @click="handleLogout" class="menu-item w-full text-red-600 hover:bg-red-50">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                  </svg>
                  Выйти
                </button>
              </div>
            </div>
          </template>

          <template v-else>
            <router-link to="/login" class="btn-secondary btn-sm">Войти</router-link>
            <router-link to="/register" class="btn-primary btn-sm">Регистрация</router-link>
          </template>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import CurrencyRatesBar from '@/components/layout/CurrencyRatesBar.vue'

const auth = useAuthStore()
const notifStore = useNotificationsStore()
const router = useRouter()
const showMenu = ref(false)
const menuRef = ref(null)

let pollInterval = null

onMounted(() => {
  if (auth.isAuthenticated) {
    notifStore.fetchUnreadCount()
    pollInterval = setInterval(() => notifStore.fetchUnreadCount(), 30000)
  }
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  clearInterval(pollInterval)
  document.removeEventListener('click', handleClickOutside)
})

function handleClickOutside(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) {
    showMenu.value = false
  }
}

function handleLogout() {
  auth.logout()
  showMenu.value = false
  router.push('/login')
}
</script>

<style scoped>
.nav-link {
  @apply px-3 py-2 text-sm font-medium text-gray-600 rounded-lg hover:text-primary-500 hover:bg-primary-50 transition-colors whitespace-nowrap;
}
.router-link-active.nav-link {
  @apply text-primary-500 bg-primary-50;
}
.menu-item {
  @apply flex items-center gap-2.5 px-4 py-2 text-sm text-gray-700 hover:bg-surface-100 transition-colors;
}
</style>
