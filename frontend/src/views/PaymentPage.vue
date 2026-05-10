<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-3xl mx-auto px-4 sm:px-6">
      <!-- Loading -->
      <LoadingSpinner v-if="loading" />

      <!-- Payment Form -->
      <div v-else-if="!processing && !success" class="space-y-6">
        <!-- Header with timer -->
        <div class="card p-5">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-xl font-bold text-gray-900">Банковский перевод</h1>
              <p class="text-sm text-gray-500 mt-1">Договор {{ paymentData.contract_number }}</p>
            </div>
            <div class="text-right">
              <p class="text-xs text-gray-500 uppercase tracking-wide">Время на оплату</p>
              <p :class="['text-lg font-mono font-bold', timerMinutes < 2 ? 'text-red-600' : 'text-gray-900']">
                {{ timerDisplay }}
              </p>
            </div>
          </div>
        </div>

        <!-- Sender / Receiver -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Sender (Lessee) -->
          <div class="card p-5">
            <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">Отправитель</h2>
            <div class="space-y-3">
              <div>
                <label class="label">IBAN</label>
                <input v-model="form.senderIban" type="text" class="input-field" placeholder="BY00XXXX0000000000000000000" />
              </div>
              <div>
                <label class="label">SWIFT / BIC</label>
                <input v-model="form.senderSwift" type="text" class="input-field" placeholder="XXXXXXXX" />
              </div>
            </div>
          </div>

          <!-- Receiver (Lessor) -->
          <div class="card p-5">
            <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">Получатель</h2>
            <div class="space-y-3">
              <div>
                <label class="label">IBAN</label>
                <input v-model="form.receiverIban" type="text" class="input-field" placeholder="BY00XXXX0000000000000000000" />
              </div>
              <div>
                <label class="label">SWIFT / BIC</label>
                <input v-model="form.receiverSwift" type="text" class="input-field" placeholder="XXXXXXXX" />
              </div>
            </div>
          </div>
        </div>

        <!-- Amount and Currency -->
        <div class="card p-5">
          <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">Сумма перевода</h2>
          <div class="grid grid-cols-3 gap-4">
            <div class="col-span-2">
              <label class="label">Сумма</label>
              <input v-model.number="form.amount" type="number" step="0.01" min="0" class="input-field" />
            </div>
            <div>
              <label class="label">Валюта</label>
              <select v-model="form.currency" class="input-field">
                <option value="BYN">BYN</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="RUB">RUB</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Comment -->
        <div class="card p-5">
          <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">Назначение платежа</h2>
          <textarea v-model="form.comment" rows="3" class="input-field resize-none"></textarea>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-between">
          <button @click="goBack" class="btn-secondary">Отмена</button>
          <button @click="submitPayment" :disabled="!isFormValid" class="btn-primary px-8 py-2.5">
            Оплатить
          </button>
        </div>
      </div>

      <!-- Processing overlay -->
      <div v-else-if="processing" class="card p-12 text-center">
        <div class="flex flex-col items-center gap-4">
          <div class="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
          <h2 class="text-lg font-semibold text-gray-900">Обработка платежа...</h2>
          <p class="text-sm text-gray-500">Пожалуйста, не закрывайте страницу</p>
        </div>
      </div>

      <!-- Success -->
      <div v-else-if="success" class="card p-12 text-center">
        <div class="flex flex-col items-center gap-4">
          <div class="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
            <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 class="text-lg font-semibold text-gray-900">Платёж успешно проведён</h2>
          <p class="text-sm text-gray-500">Транзакция № {{ transactionId }}</p>
          <p class="text-xs text-gray-400">Перенаправление...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { leasingApi } from '@/api/leasing'
import { useNotificationsStore } from '@/stores/notifications'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()
const notifStore = useNotificationsStore()

const contractId = Number(route.params.contractId)
const scheduleId = Number(route.params.scheduleId)

const loading = ref(true)
const processing = ref(false)
const success = ref(false)
const transactionId = ref('')
const paymentData = ref({})

const form = ref({
  senderIban: '',
  senderSwift: '',
  receiverIban: '',
  receiverSwift: '',
  amount: 0,
  currency: 'BYN',
  comment: '',
})

const TIMER_DURATION = 10 * 60
const timerSeconds = ref(TIMER_DURATION)
let timerInterval = null

const timerMinutes = computed(() => Math.floor(timerSeconds.value / 60))
const timerDisplay = computed(() => {
  const m = Math.floor(timerSeconds.value / 60)
  const s = timerSeconds.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const isFormValid = computed(() =>
  form.value.senderIban &&
  form.value.senderSwift &&
  form.value.receiverIban &&
  form.value.receiverSwift &&
  form.value.amount > 0
)

function startTimer() {
  timerInterval = setInterval(() => {
    timerSeconds.value--
    if (timerSeconds.value <= 0) {
      clearInterval(timerInterval)
      notifStore.showToast('Время на оплату истекло', 'error')
      router.push(`/contracts/${contractId}`)
    }
  }, 1000)
}

async function loadPaymentData() {
  try {
    const { data } = await leasingApi.preparePayment(contractId, scheduleId)
    paymentData.value = data
    form.value.senderIban = data.sender_iban || ''
    form.value.senderSwift = data.sender_swift || ''
    form.value.receiverIban = data.receiver_iban || ''
    form.value.receiverSwift = data.receiver_swift || ''
    form.value.amount = data.amount
    form.value.currency = data.currency
    form.value.comment = `Оплата лизингового платежа компании ${data.receiver_name}`
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка загрузки данных', 'error')
    router.push(`/contracts/${contractId}`)
  } finally {
    loading.value = false
  }
}

async function submitPayment() {
  processing.value = true
  clearInterval(timerInterval)
  await nextTick()
  window.scrollTo({ top: 0, behavior: 'smooth' })

  await new Promise(resolve => setTimeout(resolve, 2500))

  try {
    const { data } = await leasingApi.makePayment({
      contract_id: contractId,
      payment_schedule_id: scheduleId,
      amount: form.value.amount,
      payment_method: 'bank_transfer',
    })
    processing.value = false
    success.value = true
    transactionId.value = `TXN-${data.id}-${Date.now().toString(36).toUpperCase()}`

    setTimeout(() => {
      router.push(`/contracts/${contractId}`)
    }, 2000)
  } catch (e) {
    processing.value = false
    notifStore.showToast(e.response?.data?.detail || 'Ошибка при проведении платежа', 'error')
  }
}

function goBack() {
  router.push(`/contracts/${contractId}`)
}

onMounted(() => {
  loadPaymentData()
  startTimer()
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})
</script>
