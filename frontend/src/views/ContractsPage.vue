<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Мои договоры</h1>
      <select v-model="statusFilter" @change="fetchContracts" class="input-field w-auto">
        <option value="">Все статусы</option>
        <option value="draft">Черновик</option>
        <option value="active">Активен</option>
        <option value="completed">Завершён</option>
        <option value="terminated">Расторгнут</option>
      </select>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else-if="contracts.length === 0" class="text-center py-16 text-gray-500">Договоров пока нет</div>
    <div v-else class="space-y-3">
      <router-link v-for="c in contracts" :key="c.id" :to="`/contracts/${c.id}`"
                   class="card p-5 flex items-center justify-between hover:shadow-md transition-shadow">
        <div>
          <div class="flex items-center gap-3">
            <h3 class="font-semibold text-gray-900">{{ c.contract_number }}</h3>
            <StatusBadge :status="c.status" />
          </div>
          <div class="text-sm text-gray-500 mt-1">
            <p>Сумма: {{ formatPrice(c.total_amount) }} · Аванс: {{ formatPrice(c.prepayment) }} · Ставка: {{ c.interest_rate }}%</p>
            <p class="text-xs text-gray-400">{{ formatDate(c.start_date) }} — {{ formatDate(c.end_date) }}</p>
          </div>
        </div>
        <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { leasingApi } from '@/api/leasing'
import { formatPrice, formatDate } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const contracts = ref([])
const loading = ref(true)
const statusFilter = ref('')

onMounted(() => fetchContracts())

async function fetchContracts() {
  loading.value = true
  try {
    const params = { limit: 50 }
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await leasingApi.listContracts(params)
    contracts.value = data
  } finally {
    loading.value = false
  }
}
</script>
