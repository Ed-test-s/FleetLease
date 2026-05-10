<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Заявки</h1>
      <select v-model="statusFilter" @change="fetchData" class="input-field w-auto">
        <option value="">Все статусы</option>
        <option value="new">Новые</option>
        <option value="in_review">В работе</option>
        <option value="approved">Одобренные</option>
        <option value="rejected">Отклонённые</option>
      </select>
    </div>

    <!-- Tabs for lease_manager -->
    <div v-if="auth.userRole === 'lease_manager'" class="flex gap-1 mb-6 bg-surface-100 p-1 rounded-lg w-fit">
      <button @click="tab = 'lease'" :class="['px-4 py-2 text-sm rounded-md font-medium transition-colors', tab === 'lease' ? 'bg-white shadow-sm text-primary-500' : 'text-gray-500 hover:text-gray-700']">
        От лизингополучателей
      </button>
      <button @click="tab = 'purchase'" :class="['px-4 py-2 text-sm rounded-md font-medium transition-colors', tab === 'purchase' ? 'bg-white shadow-sm text-primary-500' : 'text-gray-500 hover:text-gray-700']">
        Поставщикам
      </button>
    </div>

    <LoadingSpinner v-if="loading" />

    <!-- Lease Requests (client, lease_manager tab=lease) -->
    <template v-if="!loading && showLeaseRequests">
      <div v-if="requests.length === 0" class="text-center py-16 text-gray-500">Заявок пока нет</div>
      <div v-else class="space-y-3">
        <div
          v-for="r in requests"
          :key="r.id"
          :id="`lease-request-${r.id}`"
          :class="[
            'card p-5 transition-all',
            highlightedLeaseRequestId === r.id ? 'ring-2 ring-primary-400 bg-primary-50' : '',
          ]"
        >
          <div class="flex items-start justify-between">
            <div>
              <div class="flex items-center gap-3">
                <h3 class="font-semibold text-gray-900">Заявка #{{ r.id }}</h3>
                <StatusBadge :status="r.status" />
              </div>
              <div class="text-sm text-gray-500 mt-1 space-y-0.5">
                <p>
                  Техника:
                  <router-link :to="`/vehicles/${r.vehicle_id}`" class="text-primary-500 hover:underline">
                    {{ r.vehicle_name || `Объявление #${r.vehicle_id}` }}
                  </router-link>
                </p>
                <p v-if="(auth.userRole === 'lease_manager' || auth.userRole === 'admin') && r.client_label">
                  Лизингополучатель:
                  <router-link :to="`/users/${r.user_id}`" class="text-primary-500 hover:underline">{{ r.client_label }}</router-link>
                </p>
                <p v-if="auth.userRole === 'client' && r.lease_company_label">
                  Лизинговая компания:
                  <router-link :to="`/users/${r.lease_company_id}`" class="text-primary-500 hover:underline">{{ r.lease_company_label }}</router-link>
                </p>
                <p>Срок: {{ r.lease_term }} мес. · Аванс: {{ formatPrice(r.prepayment) }}</p>
                <p v-if="r.comment" class="text-gray-400 italic">{{ r.comment }}</p>
                <p class="text-xs text-gray-400">{{ formatDateTime(r.created_at) }}</p>
              </div>
            </div>

            <!-- Manager actions -->
            <div v-if="auth.userRole === 'lease_manager' && r.status === 'new'" class="flex gap-2">
              <button @click="updateLeaseStatus(r.id, 'in_review')" class="btn-secondary btn-sm">В работу</button>
              <button @click="updateLeaseStatus(r.id, 'rejected')" class="btn-danger btn-sm">Отклонить</button>
            </div>
            <div v-if="auth.userRole === 'lease_manager' && r.status === 'in_review'" class="flex gap-2">
              <button @click="approveRequest(r)" class="btn-success btn-sm">Одобрить</button>
              <button @click="updateLeaseStatus(r.id, 'rejected')" class="btn-danger btn-sm">Отклонить</button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Supplier Requests (supplier, lease_manager tab=purchase) -->
    <template v-if="!loading && showSupplierRequests">
      <div v-if="supplierRequests.length === 0" class="text-center py-16 text-gray-500">Заявок на покупку пока нет</div>
      <div v-else class="space-y-3">
        <div
          v-for="sr in supplierRequests"
          :key="sr.id"
          :id="`supplier-request-${sr.id}`"
          :class="[
            'card p-5 transition-all',
            highlightedSupplierRequestId === sr.id ? 'ring-2 ring-primary-400 bg-primary-50' : '',
          ]"
        >
          <div class="flex items-start justify-between">
            <div>
              <div class="flex items-center gap-3">
                <h3 class="font-semibold text-gray-900">Заявка на покупку #{{ sr.id }}</h3>
                <StatusBadge :status="sr.status" />
              </div>
              <div class="text-sm text-gray-500 mt-1 space-y-0.5">
                <p>
                  Техника:
                  <router-link :to="`/vehicles/${sr.vehicle_id}`" class="text-primary-500 hover:underline">
                    {{ sr.vehicle_name || `Объявление #${sr.vehicle_id}` }}
                  </router-link>
                </p>
                <p>Количество: {{ sr.quantity }} шт.</p>
                <p v-if="auth.userRole === 'supplier' && sr.lessor_label">
                  Лизингодатель:
                  <router-link :to="`/users/${sr.lessor_id}`" class="text-primary-500 hover:underline">{{ sr.lessor_label }}</router-link>
                </p>
                <p v-if="auth.userRole === 'lease_manager' && sr.supplier_label">
                  Поставщик:
                  <router-link :to="`/users/${sr.supplier_id}`" class="text-primary-500 hover:underline">{{ sr.supplier_label }}</router-link>
                </p>
                <p class="text-xs text-gray-400">{{ formatDateTime(sr.created_at) }}</p>
              </div>
            </div>

            <!-- Supplier actions -->
            <div v-if="auth.userRole === 'supplier' && sr.status === 'new'" class="flex gap-2">
              <button @click="updateSupplierStatus(sr.id, 'in_review')" class="btn-secondary btn-sm">В работу</button>
              <button @click="updateSupplierStatus(sr.id, 'rejected')" class="btn-danger btn-sm">Отклонить</button>
            </div>
            <div v-if="auth.userRole === 'supplier' && sr.status === 'in_review'" class="flex gap-2">
              <button @click="updateSupplierStatus(sr.id, 'approved')" class="btn-success btn-sm">Одобрить</button>
              <button @click="updateSupplierStatus(sr.id, 'rejected')" class="btn-danger btn-sm">Отклонить</button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { leasingApi } from '@/api/leasing'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { formatPrice, formatDateTime } from '@/utils/format'
import { hasBankRequisites } from '@/utils/banking'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const auth = useAuthStore()
const notifStore = useNotificationsStore()
const route = useRoute()

const requests = ref([])
const supplierRequests = ref([])
const loading = ref(true)
const statusFilter = ref('')
const tab = ref('lease')
const pendingFocusRequestId = ref(null)
const highlightedLeaseRequestId = ref(null)
const highlightedSupplierRequestId = ref(null)
let highlightTimer = null

const showLeaseRequests = computed(() => {
  if (auth.userRole === 'supplier') return false
  if (auth.userRole === 'lease_manager') return tab.value === 'lease'
  return true
})

const showSupplierRequests = computed(() => {
  if (auth.userRole === 'supplier') return true
  if (auth.userRole === 'lease_manager') return tab.value === 'purchase'
  return false
})

watch(tab, () => fetchData())
watch(
  () => route.query.focusRequestId,
  (value) => {
    pendingFocusRequestId.value = parseFocusRequestId(value)
    fetchData()
  },
  { immediate: true },
)

function parseFocusRequestId(value) {
  const raw = Array.isArray(value) ? value[0] : value
  const parsed = Number(raw)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
}

function applyHighlight(leaseRequestId, supplierRequestId) {
  highlightedLeaseRequestId.value = leaseRequestId
  highlightedSupplierRequestId.value = supplierRequestId
  if (highlightTimer) clearTimeout(highlightTimer)
  highlightTimer = setTimeout(() => {
    highlightedLeaseRequestId.value = null
    highlightedSupplierRequestId.value = null
  }, 2500)
}

async function focusRequestIfNeeded() {
  const requestId = pendingFocusRequestId.value
  if (!requestId) return

  const leaseMatch = requests.value.some((r) => r.id === requestId)
  const supplierMatch = supplierRequests.value.some((sr) => sr.id === requestId)

  if (auth.userRole === 'lease_manager') {
    if (leaseMatch && tab.value !== 'lease') {
      tab.value = 'lease'
      return
    }
    if (supplierMatch && tab.value !== 'purchase') {
      tab.value = 'purchase'
      return
    }
  }

  const targetElementId = leaseMatch
    ? `lease-request-${requestId}`
    : supplierMatch
      ? `supplier-request-${requestId}`
      : null
  if (!targetElementId) return

  const cardElement = document.getElementById(targetElementId)
  if (!cardElement) return

  cardElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
  applyHighlight(leaseMatch ? requestId : null, supplierMatch ? requestId : null)
  pendingFocusRequestId.value = null
}

async function fetchData() {
  loading.value = true
  try {
    const hasFocusRequest = Boolean(pendingFocusRequestId.value)
    const shouldLoadBothForFocus = auth.userRole === 'lease_manager' && hasFocusRequest
    const params = { limit: 50 }
    if (statusFilter.value && !hasFocusRequest) params.status = statusFilter.value

    if (showLeaseRequests.value || shouldLoadBothForFocus) {
      const { data } = await leasingApi.listRequests(params)
      requests.value = data
    } else {
      requests.value = []
    }
    if (showSupplierRequests.value || shouldLoadBothForFocus) {
      const { data } = await leasingApi.listSupplierRequests(params)
      supplierRequests.value = data
    } else {
      supplierRequests.value = []
    }
  } finally {
    loading.value = false
    await nextTick()
    await focusRequestIfNeeded()
  }
}

async function updateLeaseStatus(id, status) {
  await leasingApi.updateRequestStatus(id, status)
  notifStore.showToast('Статус обновлён', 'success')
  fetchData()
}

const bankRequiredMsg =
  'Укажите в профиле полные банковские реквизиты (IBAN, банк, адрес отделения, SWIFT).'

async function approveRequest(r) {
  if (!hasBankRequisites(auth.user)) {
    notifStore.showToast(bankRequiredMsg, 'error')
    return
  }
  await leasingApi.updateRequestStatus(r.id, 'approved')
  notifStore.showToast('Заявка одобрена, договор лизинга создан', 'success')
  fetchData()
}

async function updateSupplierStatus(id, status) {
  if (status === 'approved' && !hasBankRequisites(auth.user)) {
    notifStore.showToast(bankRequiredMsg, 'error')
    return
  }
  await leasingApi.updateSupplierRequestStatus(id, status)
  if (status === 'approved') {
    notifStore.showToast('Заявка на покупку одобрена, ДКП создан', 'success')
  } else {
    notifStore.showToast('Статус обновлён', 'success')
  }
  fetchData()
}
</script>
