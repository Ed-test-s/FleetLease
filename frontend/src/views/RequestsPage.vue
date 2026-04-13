<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Заявки</h1>
      <select v-model="statusFilter" @change="fetchRequests" class="input-field w-auto">
        <option value="">Все статусы</option>
        <option value="new">Новые</option>
        <option value="in_review">В работе</option>
        <option value="approved">Одобренные</option>
        <option value="rejected">Отклонённые</option>
      </select>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else-if="requests.length === 0" class="text-center py-16 text-gray-500">Заявок пока нет</div>
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
            <button @click="updateStatus(r.id, 'in_review')" class="btn-secondary btn-sm">В работу</button>
            <button @click="updateStatus(r.id, 'rejected')" class="btn-danger btn-sm">Отклонить</button>
          </div>
          <div v-if="auth.userRole === 'lease_manager' && r.status === 'in_review'" class="flex gap-2">
            <button @click="approveRequest(r)" class="btn-success btn-sm">Одобрить</button>
            <button @click="updateStatus(r.id, 'rejected')" class="btn-danger btn-sm">Отклонить</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { leasingApi } from '@/api/leasing'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { formatPrice, formatDateTime } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const auth = useAuthStore()
const notifStore = useNotificationsStore()
const router = useRouter()

const requests = ref([])
const loading = ref(true)
const statusFilter = ref('')

onMounted(() => fetchRequests())

async function fetchRequests() {
  loading.value = true
  try {
    const params = { limit: 50 }
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await leasingApi.listRequests(params)
    requests.value = data
  } finally {
    loading.value = false
  }
}

async function updateStatus(id, status) {
  await leasingApi.updateRequestStatus(id, status)
  notifStore.showToast('Статус обновлён', 'success')
  fetchRequests()
}

async function approveRequest(r) {
  await leasingApi.updateRequestStatus(r.id, 'approved')

  const contractNumber = `FL-${Date.now().toString(36).toUpperCase()}`
  const total = r.prepayment + (r.prepayment * 0.12 * r.lease_term / 12)

  await leasingApi.createContract({
    request_id: r.id,
    lessee_id: r.user_id,
    lessor_id: r.lease_company_id,
    vehicle_id: r.vehicle_id,
    contract_number: contractNumber,
    total_amount: Math.round(total * 100) / 100,
    prepayment: r.prepayment,
    interest_rate: 12.0,
  })

  notifStore.showToast('Заявка одобрена, договор создан', 'success')
  fetchRequests()
}
</script>
