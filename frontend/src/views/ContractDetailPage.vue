<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
    <router-link to="/contracts" class="text-sm text-primary-500 hover:underline mb-4 inline-block">&larr; Все договоры</router-link>

    <LoadingSpinner v-if="loading" />
    <template v-else-if="contract">
      <!-- Contract info -->
      <div class="card p-6 mb-6">
        <div class="flex items-start justify-between">
          <div>
            <h1 class="text-xl font-bold text-gray-900">Договор {{ contract.contract_number }}</h1>
            <StatusBadge :status="contract.status" class="mt-2" />
          </div>
          <div v-if="auth.userRole === 'lease_manager'" class="flex gap-2">
            <button v-if="contract.status === 'draft'" @click="updateStatus('active')" class="btn-success btn-sm">Активировать</button>
            <button v-if="contract.status === 'active'" @click="updateStatus('completed')" class="btn-secondary btn-sm">Завершить</button>
            <button v-if="contract.status === 'active'" @click="generateSchedule" class="btn-primary btn-sm">Сформировать график</button>
          </div>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 text-sm">
          <div><span class="text-gray-400 block">Общая сумма</span><span class="font-semibold">{{ formatPrice(contract.total_amount) }}</span></div>
          <div><span class="text-gray-400 block">Аванс</span><span class="font-semibold">{{ formatPrice(contract.prepayment) }}</span></div>
          <div><span class="text-gray-400 block">Ставка</span><span class="font-semibold">{{ contract.interest_rate }}%</span></div>
          <div><span class="text-gray-400 block">Период</span><span class="font-semibold">{{ formatDate(contract.start_date) }} — {{ formatDate(contract.end_date) }}</span></div>
        </div>
      </div>

      <!-- Payment schedule -->
      <div class="card p-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">График платежей</h2>
        <div v-if="schedule.length === 0" class="text-center text-gray-500 py-8">
          <p>График ещё не сформирован.</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-surface-200 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th class="pb-3 pr-4">№</th>
                <th class="pb-3 pr-4">Дата</th>
                <th class="pb-3 pr-4">Платёж</th>
                <th class="pb-3 pr-4">Тело долга</th>
                <th class="pb-3 pr-4">Проценты</th>
                <th class="pb-3 pr-4">НДС</th>
                <th class="pb-3 pr-4">Остаток</th>
                <th class="pb-3 pr-4">Статус</th>
                <th class="pb-3"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(s, i) in schedule" :key="s.id" class="border-b border-surface-100">
                <td class="py-3 pr-4 text-gray-400">{{ i + 1 }}</td>
                <td class="py-3 pr-4">{{ formatDate(s.payment_date) }}</td>
                <td class="py-3 pr-4 font-medium">{{ formatPrice(s.total_amount) }}</td>
                <td class="py-3 pr-4">{{ formatPrice(s.principal_amount) }}</td>
                <td class="py-3 pr-4">{{ formatPrice(s.interest_amount) }}</td>
                <td class="py-3 pr-4">{{ formatPrice(s.vat_amount) }}</td>
                <td class="py-3 pr-4">{{ formatPrice(s.remaining_debt) }}</td>
                <td class="py-3 pr-4"><StatusBadge :status="s.status" /></td>
                <td class="py-3">
                  <button v-if="s.status === 'pending' && auth.userRole === 'client'"
                          @click="makePayment(s)" class="btn-primary btn-sm">
                    Оплатить
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { leasingApi } from '@/api/leasing'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { formatPrice, formatDate } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const route = useRoute()
const auth = useAuthStore()
const notifStore = useNotificationsStore()

const contract = ref(null)
const schedule = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [cRes, sRes] = await Promise.all([
      leasingApi.getContract(route.params.id),
      leasingApi.getSchedule(route.params.id),
    ])
    contract.value = cRes.data
    schedule.value = sRes.data
  } finally {
    loading.value = false
  }
})

async function updateStatus(status) {
  await leasingApi.updateContractStatus(route.params.id, status)
  contract.value.status = status
  notifStore.showToast('Статус обновлён', 'success')
}

async function generateSchedule() {
  const { data } = await leasingApi.generateSchedule(route.params.id)
  schedule.value = data
  notifStore.showToast('График сформирован', 'success')
}

async function makePayment(s) {
  await leasingApi.makePayment({
    contract_id: contract.value.id,
    payment_schedule_id: s.id,
    amount: s.total_amount,
  })
  s.status = 'paid'
  notifStore.showToast('Платёж выполнен', 'success')
}
</script>
