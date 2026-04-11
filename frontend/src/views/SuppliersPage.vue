<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Поставщики</h1>
        <p class="text-sm text-gray-500 mt-1">Все продавцы техники на платформе</p>
      </div>
      <div class="flex gap-3">
        <input v-model="search" @input="debouncedFetch" type="text" class="input-field w-64" placeholder="Поиск по названию или ФИО..." />
        <select v-model="typeFilter" @change="fetchSuppliers" class="input-field w-auto">
          <option value="">Все типы</option>
          <option value="individual">Частное лицо</option>
          <option value="company">Компания</option>
          <option value="ie">ИП</option>
        </select>
      </div>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <router-link v-for="s in suppliers" :key="s.id" :to="`/users/${s.id}`"
                   class="card p-5 hover:shadow-md transition-shadow">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-lg font-bold flex-shrink-0 overflow-hidden">
            <img v-if="s.avatar_url" :src="s.avatar_url" class="w-full h-full object-cover" />
            <span v-else>{{ getSupplierName(s)?.charAt(0)?.toUpperCase() }}</span>
          </div>
          <div class="min-w-0">
            <h3 class="font-semibold text-gray-900 truncate">{{ getSupplierName(s) }}</h3>
            <p class="text-xs text-gray-500">{{ userTypeLabels[s.user_type] }}</p>
            <StarRating v-if="s.rating" :rating="s.rating" class="mt-1" />
          </div>
        </div>
      </router-link>
    </div>
    <p v-if="!loading && suppliers.length === 0" class="text-center text-gray-500 py-12">Поставщики не найдены</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { usersApi } from '@/api/users'
import { userTypeLabels } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StarRating from '@/components/common/StarRating.vue'

const suppliers = ref([])
const loading = ref(true)
const search = ref('')
const typeFilter = ref('')
let debounceTimer = null

onMounted(() => fetchSuppliers())

function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchSuppliers, 400)
}

async function fetchSuppliers() {
  loading.value = true
  try {
    const params = { role: 'supplier', limit: 100 }
    if (search.value) params.search = search.value
    if (typeFilter.value) params.user_type = typeFilter.value
    const { data } = await usersApi.listUsers(params)
    suppliers.value = data
  } finally {
    loading.value = false
  }
}

function getSupplierName(s) {
  if (s.individual) return s.individual.full_name
  if (s.entrepreneur) return s.entrepreneur.full_name
  if (s.company) return `${s.company.legal_form || ''} «${s.company.company_name}»`
  return s.login
}
</script>
