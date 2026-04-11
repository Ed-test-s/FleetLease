<template>
  <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Админ-панель</h1>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-6">
      <input v-model="search" @input="debouncedFetch" type="text" class="input-field w-64" placeholder="Поиск пользователя..." />
      <select v-model="roleFilter" @change="fetchUsers" class="input-field w-auto">
        <option value="">Все роли</option>
        <option value="client">Лизингополучатель</option>
        <option value="lease_manager">Лизинговая компания</option>
        <option value="supplier">Поставщик</option>
        <option value="admin">Администратор</option>
      </select>
      <select v-model="typeFilter" @change="fetchUsers" class="input-field w-auto">
        <option value="">Все типы</option>
        <option value="individual">Физ. лицо</option>
        <option value="ie">ИП</option>
        <option value="company">Юр. лицо</option>
      </select>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-50 border-b border-surface-200 text-left text-xs text-gray-500 uppercase tracking-wide">
            <th class="px-4 py-3">ID</th>
            <th class="px-4 py-3">Логин</th>
            <th class="px-4 py-3">Имя / Компания</th>
            <th class="px-4 py-3">Роль</th>
            <th class="px-4 py-3">Тип</th>
            <th class="px-4 py-3">Статус</th>
            <th class="px-4 py-3">Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-b border-surface-100 hover:bg-surface-50">
            <td class="px-4 py-3 text-gray-400">{{ u.id }}</td>
            <td class="px-4 py-3 font-medium">{{ u.login }}</td>
            <td class="px-4 py-3">{{ getUserName(u) }}</td>
            <td class="px-4 py-3">
              <select :value="u.role" @change="changeRole(u.id, $event.target.value)" class="input-field py-1 px-2 text-xs w-auto">
                <option value="client">Клиент</option>
                <option value="lease_manager">Менеджер</option>
                <option value="supplier">Поставщик</option>
                <option value="admin">Админ</option>
              </select>
            </td>
            <td class="px-4 py-3 text-xs text-gray-500">{{ userTypeLabels[u.user_type] }}</td>
            <td class="px-4 py-3">
              <span :class="['badge', u.is_active !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
                {{ u.is_active !== false ? 'Активен' : 'Заблокирован' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <button @click="toggleActive(u.id)" :class="u.is_active !== false ? 'btn-danger btn-sm' : 'btn-success btn-sm'">
                {{ u.is_active !== false ? 'Блокировать' : 'Разблокировать' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { usersApi } from '@/api/users'
import { useNotificationsStore } from '@/stores/notifications'
import { userTypeLabels } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const notifStore = useNotificationsStore()
const users = ref([])
const loading = ref(true)
const search = ref('')
const roleFilter = ref('')
const typeFilter = ref('')
let debounceTimer = null

onMounted(() => fetchUsers())

function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchUsers, 400)
}

async function fetchUsers() {
  loading.value = true
  try {
    const params = { limit: 100 }
    if (search.value) params.search = search.value
    if (roleFilter.value) params.role = roleFilter.value
    if (typeFilter.value) params.user_type = typeFilter.value
    const { data } = await usersApi.listUsers(params)
    users.value = data
  } finally {
    loading.value = false
  }
}

function getUserName(u) {
  if (u.individual) return u.individual.full_name
  if (u.entrepreneur) return u.entrepreneur.full_name
  if (u.company) return u.company.company_name
  return '—'
}

async function toggleActive(id) {
  await usersApi.toggleActive(id)
  fetchUsers()
  notifStore.showToast('Статус обновлён', 'success')
}

async function changeRole(id, role) {
  await usersApi.changeRole(id, role)
  fetchUsers()
  notifStore.showToast('Роль обновлена', 'success')
}
</script>
