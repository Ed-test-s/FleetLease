<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Лизингодатели</h1>
        <p class="text-sm text-gray-500 mt-1">Лизинговые компании на платформе</p>
      </div>
      <input v-model="search" @input="debouncedFetch" type="text" class="input-field w-64" placeholder="Поиск по названию..." />
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else class="space-y-4">
      <router-link v-for="l in lessors" :key="l.id" :to="`/users/${l.id}`"
                   class="card p-5 flex items-center gap-5 hover:shadow-md transition-shadow">
        <div class="w-14 h-14 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-xl font-bold flex-shrink-0 overflow-hidden">
          <img v-if="l.avatar_url" :src="l.avatar_url" class="w-full h-full object-cover" />
          <span v-else>{{ l.company?.company_name?.charAt(0)?.toUpperCase() || 'L' }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-gray-900">{{ l.company?.legal_form }} «{{ l.company?.company_name }}»</h3>
          <div v-if="l.lease_terms" class="text-xs text-gray-500 mt-1 flex flex-wrap gap-x-4 gap-y-1">
            <span>Срок: {{ l.lease_terms.min_term_months }}–{{ l.lease_terms.max_term_months }} мес.</span>
            <span>Аванс: {{ l.lease_terms.min_prepayment_pct }}–{{ l.lease_terms.max_prepayment_pct }}%</span>
            <span>Ставка: {{ l.lease_terms.interest_rate }}%</span>
          </div>
          <StarRating v-if="l.rating" :rating="l.rating" class="mt-1" />
        </div>
        <svg class="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </router-link>
    </div>
    <p v-if="!loading && lessors.length === 0" class="text-center text-gray-500 py-12">Лизингодатели не найдены</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { usersApi } from '@/api/users'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StarRating from '@/components/common/StarRating.vue'

const lessors = ref([])
const loading = ref(true)
const search = ref('')
let debounceTimer = null

onMounted(() => fetchLessors())

function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchLessors, 400)
}

async function fetchLessors() {
  loading.value = true
  try {
    const params = { role: 'lease_manager', limit: 100 }
    if (search.value) params.search = search.value
    const { data } = await usersApi.listUsers(params)
    lessors.value = data
  } finally {
    loading.value = false
  }
}
</script>
