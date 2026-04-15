<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
    <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Лизингодатели</h1>
        <p class="text-sm text-gray-500 mt-1">Лизинговые компании на платформе</p>
      </div>
      <input v-model="search" @input="debouncedFetch" type="text" class="input-field w-full sm:w-64 flex-shrink-0" placeholder="Поиск по названию..." />
    </div>

    <div class="card p-4 mb-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <h2 class="text-sm font-semibold text-gray-800">Условия лизинга</h2>
        <button type="button" class="btn-secondary btn-sm self-start sm:self-auto" @click="resetFilters">Сбросить фильтры</button>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <p class="label mb-2">Стоимость имущества (BYN)</p>
          <div class="flex items-center gap-2">
            <input v-model="f.assetMin" type="number" min="0" step="1" class="input-field flex-1 min-w-0" placeholder="От" />
            <span class="text-gray-400 flex-shrink-0">—</span>
            <input v-model="f.assetMax" type="number" min="0" step="1" class="input-field flex-1 min-w-0" placeholder="До" />
          </div>
        </div>
        <div>
          <p class="label mb-2">Срок (мес.)</p>
          <div class="flex items-center gap-2">
            <input v-model="f.termMin" type="number" min="1" step="1" class="input-field flex-1 min-w-0" placeholder="От" />
            <span class="text-gray-400 flex-shrink-0">—</span>
            <input v-model="f.termMax" type="number" min="1" step="1" class="input-field flex-1 min-w-0" placeholder="До" />
          </div>
        </div>
        <div>
          <p class="label mb-2">Аванс (%)</p>
          <div class="flex items-center gap-2">
            <input v-model="f.prepMin" type="number" min="0" step="0.1" class="input-field flex-1 min-w-0" placeholder="От" />
            <span class="text-gray-400 flex-shrink-0">—</span>
            <input v-model="f.prepMax" type="number" min="0" step="0.1" class="input-field flex-1 min-w-0" placeholder="До" />
          </div>
        </div>
        <div>
          <p class="label mb-2">Ставка (%)</p>
          <div class="flex items-center gap-2">
            <input v-model="f.rateMin" type="number" min="0" step="0.1" class="input-field flex-1 min-w-0" placeholder="От" />
            <span class="text-gray-400 flex-shrink-0">—</span>
            <input v-model="f.rateMax" type="number" min="0" step="0.1" class="input-field flex-1 min-w-0" placeholder="До" />
          </div>
        </div>
      </div>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else class="space-y-4">
      <router-link v-for="l in filteredLessors" :key="l.id" :to="`/users/${l.id}`"
                   class="card p-5 flex items-center gap-5 hover:shadow-md transition-shadow">
        <div class="w-14 h-14 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-xl font-bold flex-shrink-0 overflow-hidden">
          <img v-if="l.avatar_url" :src="l.avatar_url" class="w-full h-full object-cover" />
          <span v-else>{{ l.company?.company_name?.charAt(0)?.toUpperCase() || 'L' }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-gray-900">{{ l.company?.legal_form }} «{{ l.company?.company_name }}»</h3>
          <div v-if="l.lease_terms" class="text-xs text-gray-500 mt-1 flex flex-wrap gap-x-4 gap-y-1">
            <span>Стоимость имущества: {{ formatPrice(l.lease_terms.min_asset_price) }} — {{ formatPrice(l.lease_terms.max_asset_price) }}</span>
            <span>Срок: {{ l.lease_terms.min_term_months }}–{{ l.lease_terms.max_term_months }} мес.</span>
            <span>Аванс: {{ l.lease_terms.min_prepayment_pct }}–{{ l.lease_terms.max_prepayment_pct }}%</span>
            <span>Ставка: {{ l.lease_terms.interest_rate }}%</span>
          </div>
          <p v-else class="text-xs text-amber-700 mt-1">Условия не указаны</p>
          <StarRating v-if="l.rating" :rating="l.rating" class="mt-1" />
        </div>
        <svg class="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </router-link>
    </div>
    <p v-if="!loading && lessors.length === 0" class="text-center text-gray-500 py-12">Лизингодатели не найдены</p>
    <p v-else-if="!loading && lessors.length > 0 && filteredLessors.length === 0" class="text-center text-gray-500 py-12">
      Нет лизингодателей, подходящих под выбранные условия.
      <button type="button" class="text-primary-600 underline ml-1" @click="resetFilters">Сбросить фильтры</button>
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usersApi } from '@/api/users'
import { formatPrice } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StarRating from '@/components/common/StarRating.vue'

const lessors = ref([])
const loading = ref(true)
const search = ref('')
let debounceTimer = null

const f = ref({
  assetMin: '',
  assetMax: '',
  termMin: '',
  termMax: '',
  prepMin: '',
  prepMax: '',
  rateMin: '',
  rateMax: '',
})

function num(v) {
  if (v === '' || v == null) return null
  const n = Number(String(v).trim())
  return Number.isFinite(n) ? n : null
}

/** Пересечение диапазона лизингодателя [lLo,lHi] с фильтром (обе границы или одна). */
function numericRangeOverlap(lLo, lHi, fMin, fMax) {
  const lo = Math.min(lLo, lHi)
  const hi = Math.max(lLo, lHi)
  if (fMin != null && fMax != null) {
    const uLo = Math.min(fMin, fMax)
    const uHi = Math.max(fMin, fMax)
    return Math.max(lo, uLo) <= Math.min(hi, uHi)
  }
  if (fMin != null) return hi >= fMin
  if (fMax != null) return lo <= fMax
  return true
}

const hasActiveFilters = computed(() => {
  const x = f.value
  return ['assetMin', 'assetMax', 'termMin', 'termMax', 'prepMin', 'prepMax', 'rateMin', 'rateMax'].some(
    (k) => num(x[k]) != null
  )
})

const filteredLessors = computed(() => {
  const list = lessors.value
  if (!hasActiveFilters.value) return list

  const assetMin = num(f.value.assetMin)
  const assetMax = num(f.value.assetMax)
  const termMin = num(f.value.termMin)
  const termMax = num(f.value.termMax)
  const prepMin = num(f.value.prepMin)
  const prepMax = num(f.value.prepMax)
  const rateMin = num(f.value.rateMin)
  const rateMax = num(f.value.rateMax)

  return list.filter((l) => {
    const lt = l.lease_terms
    if (!lt) return false

    if (!numericRangeOverlap(lt.min_asset_price, lt.max_asset_price, assetMin, assetMax)) return false
    if (!numericRangeOverlap(lt.min_term_months, lt.max_term_months, termMin, termMax)) return false
    if (!numericRangeOverlap(lt.min_prepayment_pct, lt.max_prepayment_pct, prepMin, prepMax)) return false

    const rate = lt.interest_rate
    if (rateMin != null && rate < rateMin) return false
    if (rateMax != null && rate > rateMax) return false

    return true
  })
})

onMounted(() => fetchLessors())

function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchLessors, 400)
}

function resetFilters() {
  f.value = {
    assetMin: '',
    assetMax: '',
    termMin: '',
    termMax: '',
    prepMin: '',
    prepMax: '',
    rateMin: '',
    rateMax: '',
  }
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
