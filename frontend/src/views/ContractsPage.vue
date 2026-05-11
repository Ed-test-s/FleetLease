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

    <!-- Tabs for lease_manager -->
    <div v-if="auth.userRole === 'lease_manager'" class="flex gap-1 mb-6 bg-surface-100 p-1 rounded-lg w-fit">
      <button @click="typeFilter = ''" :class="['px-4 py-2 text-sm rounded-md font-medium transition-colors', typeFilter === '' ? 'bg-white shadow-sm text-primary-500' : 'text-gray-500 hover:text-gray-700']">
        Все
      </button>
      <button @click="typeFilter = 'lease'" :class="['px-4 py-2 text-sm rounded-md font-medium transition-colors', typeFilter === 'lease' ? 'bg-white shadow-sm text-primary-500' : 'text-gray-500 hover:text-gray-700']">
        С лизингополучателями
      </button>
      <button @click="typeFilter = 'purchase_sale'" :class="['px-4 py-2 text-sm rounded-md font-medium transition-colors', typeFilter === 'purchase_sale' ? 'bg-white shadow-sm text-primary-500' : 'text-gray-500 hover:text-gray-700']">
        С поставщиками
      </button>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else-if="contracts.length === 0" class="text-center py-16 text-gray-500">Договоров пока нет</div>

    <!-- Лизингодатель / лизингополучатель / поставщик: группы по заявке -->
    <div v-else-if="useGroupedContracts" class="space-y-4">
      <div
        v-for="row in contractGroups"
        :key="row.key"
        :class="row.grouped ? 'rounded-xl border-2 border-primary-200/80 bg-primary-50/40 p-4 space-y-2' : ''"
      >
        <p v-if="row.showCaption && row.requestId != null" class="text-xs font-medium text-primary-700 uppercase tracking-wide">
          Сделка по заявке №{{ row.requestId }}
        </p>
        <router-link
          v-for="c in row.contracts"
          :key="c.id"
          :to="`/contracts/${c.id}`"
          class="card p-5 flex items-center justify-between hover:shadow-md transition-shadow block"
        >
          <div>
            <div class="flex items-center gap-3">
              <h3 class="font-semibold text-gray-900">{{ c.contract_number }}</h3>
              <StatusBadge :status="c.status" />
              <span class="badge text-[10px]" :class="c.contract_type === 'lease' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'">
                {{ c.contract_type === 'lease' ? 'Лизинг' : 'ДКП' }}
              </span>
            </div>
            <div class="text-sm text-gray-500 mt-1">
              <p v-if="c.vehicle_name">Техника: {{ c.vehicle_name }}</p>
              <p v-if="c.contract_type === 'lease'">Сумма: {{ formatPrice(c.total_amount, c.currency || 'BYN') }} · Аванс: {{ formatPrice(c.prepayment, c.currency || 'BYN') }} · Ставка: {{ c.interest_rate }}%</p>
              <p v-else>Сумма: {{ formatPrice(c.total_amount, c.currency || 'BYN') }}</p>
              <p v-if="c.lessee_label || c.supplier_label" class="text-xs text-gray-400 mt-0.5">
                <span v-if="c.contract_type === 'lease' && c.lessee_label">Лизингополучатель: {{ c.lessee_label }}</span>
                <span v-if="c.contract_type === 'purchase_sale' && c.supplier_label">Поставщик: {{ c.supplier_label }}</span>
              </p>
              <p v-if="c.contract_type === 'lease'" class="text-xs text-gray-400">{{ formatDate(c.start_date) }} — {{ formatDate(c.end_date) }}</p>
              <p v-else-if="c.signing_date" class="text-xs text-gray-400">Дата подписания: {{ formatDate(c.signing_date) }}</p>
            </div>
          </div>
          <svg class="w-5 h-5 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </router-link>
      </div>
    </div>

    <!-- Остальные роли: плоский список -->
    <div v-else class="space-y-3">
      <router-link v-for="c in contracts" :key="c.id" :to="`/contracts/${c.id}`"
                   class="card p-5 flex items-center justify-between hover:shadow-md transition-shadow">
        <div>
          <div class="flex items-center gap-3">
            <h3 class="font-semibold text-gray-900">{{ c.contract_number }}</h3>
            <StatusBadge :status="c.status" />
            <span class="badge text-[10px]" :class="c.contract_type === 'lease' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'">
              {{ c.contract_type === 'lease' ? 'Лизинг' : 'ДКП' }}
            </span>
          </div>
          <div class="text-sm text-gray-500 mt-1">
            <p v-if="c.vehicle_name">Техника: {{ c.vehicle_name }}</p>
            <p v-if="c.contract_type === 'lease'">Сумма: {{ formatPrice(c.total_amount, c.currency || 'BYN') }} · Аванс: {{ formatPrice(c.prepayment, c.currency || 'BYN') }} · Ставка: {{ c.interest_rate }}%</p>
            <p v-else>Сумма: {{ formatPrice(c.total_amount, c.currency || 'BYN') }}</p>
            <p v-if="c.lessee_label || c.supplier_label" class="text-xs text-gray-400 mt-0.5">
              <span v-if="c.contract_type === 'lease' && c.lessee_label">Лизингополучатель: {{ c.lessee_label }}</span>
              <span v-if="c.contract_type === 'purchase_sale' && c.supplier_label">Поставщик: {{ c.supplier_label }}</span>
            </p>
            <p v-if="c.contract_type === 'lease'" class="text-xs text-gray-400">{{ formatDate(c.start_date) }} — {{ formatDate(c.end_date) }}</p>
            <p v-else-if="c.signing_date" class="text-xs text-gray-400">Дата подписания: {{ formatDate(c.signing_date) }}</p>
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
import { ref, computed, onMounted, watch } from 'vue'
import { leasingApi } from '@/api/leasing'
import { useAuthStore } from '@/stores/auth'
import { formatPrice, formatDate } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const auth = useAuthStore()
const contracts = ref([])
const loading = ref(true)
const statusFilter = ref('')
const typeFilter = ref('')

const useGroupedContracts = computed(() =>
  ['lease_manager', 'client', 'supplier'].includes(auth.userRole),
)

function sortContractsInDeal(a, b) {
  if (a.contract_type === 'purchase_sale' && b.contract_type === 'lease') return -1
  if (a.contract_type === 'lease' && b.contract_type === 'purchase_sale') return 1
  return a.id - b.id
}

const contractGroups = computed(() => {
  const list = contracts.value
  if (!list.length) return []

  const role = auth.userRole
  const supplierFrame = role === 'supplier'

  const byReq = new Map()
  const singles = []

  for (const c of list) {
    if (c.request_id == null) {
      singles.push({
        key: `solo-${c.id}`,
        grouped: false,
        showCaption: false,
        requestId: null,
        contracts: [c],
      })
      continue
    }
    if (!byReq.has(c.request_id)) byReq.set(c.request_id, [])
    byReq.get(c.request_id).push(c)
  }

  const groups = []
  for (const [rid, arr] of byReq) {
    const sorted = [...arr].sort(sortContractsInDeal)
    const multi = sorted.length > 1
    const grouped = supplierFrame ? true : multi
    groups.push({
      key: `deal-${rid}`,
      grouped,
      showCaption: grouped,
      requestId: rid,
      contracts: sorted,
    })
  }

  const ts = (row) => {
    const t = row.contracts[0]?.created_at
    return t ? new Date(t).getTime() : 0
  }
  groups.sort((a, b) => ts(b) - ts(a))
  singles.sort((a, b) => ts(b) - ts(a))
  return [...groups, ...singles]
})

onMounted(() => fetchContracts())
watch(typeFilter, () => fetchContracts())

async function fetchContracts() {
  loading.value = true
  try {
    const params = { limit: 50 }
    if (statusFilter.value) params.status = statusFilter.value
    if (typeFilter.value) params.contract_type = typeFilter.value
    const { data } = await leasingApi.listContracts(params)
    contracts.value = data
  } finally {
    loading.value = false
  }
}
</script>
