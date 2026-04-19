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
        <div v-for="r in requests" :key="r.id" class="card p-5">
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
        <div v-for="sr in supplierRequests" :key="sr.id" class="card p-5">
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
import { ref, computed, onMounted, watch } from 'vue'
import { leasingApi } from '@/api/leasing'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { formatPrice, formatDateTime } from '@/utils/format'
import { hasBankRequisites } from '@/utils/banking'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const auth = useAuthStore()
const notifStore = useNotificationsStore()

const requests = ref([])
const supplierRequests = ref([])
const loading = ref(true)
const statusFilter = ref('')
const tab = ref('lease')

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

onMounted(() => fetchData())
watch(tab, () => fetchData())

async function fetchData() {
  loading.value = true
  try {
    const params = { limit: 50 }
    if (statusFilter.value) params.status = statusFilter.value

    if (showLeaseRequests.value) {
      const { data } = await leasingApi.listRequests(params)
      requests.value = data
    }
    if (showSupplierRequests.value) {
      const { data } = await leasingApi.listSupplierRequests(params)
      supplierRequests.value = data
    }
  } finally {
    loading.value = false
  }
}

async function updateLeaseStatus(id, status) {
  await leasingApi.updateRequestStatus(id, status)
  notifStore.showToast('Статус обновлён', 'success')
  fetchData()
}

const bankRequiredMsg =
  'Укажите в профиле полные банковские реквизиты (IBAN, банк, адрес отделения, BIC или SWIFT).'

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
