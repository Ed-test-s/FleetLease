<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
    <router-link to="/contracts" class="text-sm text-primary-500 hover:underline mb-4 inline-block">&larr; Все договоры</router-link>

    <LoadingSpinner v-if="loading" />
    <template v-else-if="contract">
      <!-- Contract info -->
      <div class="card p-6 mb-6">
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-3">
              <h1 class="text-xl font-bold text-gray-900">Договор {{ contract.contract_number }}</h1>
              <StatusBadge :status="contract.status" />
              <span class="badge text-[10px]" :class="contract.contract_type === 'lease' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'">
                {{ contract.contract_type === 'lease' ? 'Лизинг' : 'ДКП' }}
              </span>
            </div>
            <p v-if="contract.vehicle_name" class="text-sm text-gray-500 mt-1">Техника: {{ contract.vehicle_name }}</p>
          </div>
          <div v-if="auth.userRole === 'lease_manager'" class="flex gap-2">
            <button v-if="contract.status === 'draft'" @click="confirmStatusChange('active')" class="btn-success btn-sm">Активировать</button>
            <button v-if="contract.status === 'active'" @click="confirmStatusChange('completed')" class="btn-secondary btn-sm">Завершить</button>
            <button v-if="contract.status === 'active' && contract.contract_type === 'lease'" @click="confirmGenerateSchedule" class="btn-primary btn-sm">Сформировать график</button>
          </div>
        </div>

        <!-- Parties -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 text-sm">
          <div v-if="contract.lessor_label">
            <span class="text-gray-400 block">Лизингодатель</span>
            <span class="font-semibold">{{ contract.lessor_label }}</span>
          </div>
          <div v-if="contract.lessee_label">
            <span class="text-gray-400 block">Лизингополучатель</span>
            <span class="font-semibold">{{ contract.lessee_label }}</span>
          </div>
          <div v-if="contract.supplier_label">
            <span class="text-gray-400 block">Поставщик</span>
            <span class="font-semibold">{{ contract.supplier_label }}</span>
          </div>
        </div>

        <!-- Financial info -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
          <div><span class="text-gray-400 block">Общая сумма</span><span class="font-semibold">{{ formatPrice(contract.total_amount) }}</span></div>
          <div><span class="text-gray-400 block">Аванс</span><span class="font-semibold">{{ formatPrice(contract.prepayment) }}</span></div>
          <div><span class="text-gray-400 block">Ставка</span><span class="font-semibold">{{ contract.interest_rate }}%</span></div>
          <div><span class="text-gray-400 block">Кол-во техники</span><span class="font-semibold">{{ contract.quantity }} шт.</span></div>
        </div>
      </div>

      <!-- Editable contract fields -->
      <div class="card p-6 mb-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">Параметры договора</h2>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <!-- Lessor-editable fields -->
          <div>
            <label class="label">Дата подписания</label>
            <input v-if="canEditLessorFields" v-model="fields.signing_date" type="date" class="input-field" />
            <p v-else class="text-sm font-medium text-gray-800">{{ contract.signing_date || 'Не указана' }}</p>
          </div>
          <div>
            <label class="label">Город подписания</label>
            <input v-if="canEditLessorFields" v-model="fields.signing_city" type="text" class="input-field" placeholder="Минск" />
            <p v-else class="text-sm font-medium text-gray-800">{{ contract.signing_city || 'Не указан' }}</p>
          </div>
          <div>
            <label class="label">Валюта</label>
            <select v-if="canEditLessorFields" v-model="fields.currency" class="input-field">
              <option value="BYN">BYN</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="RUB">RUB</option>
            </select>
            <p v-else class="text-sm font-medium text-gray-800">{{ contract.currency || 'Не указана' }}</p>
          </div>

          <!-- Supplier-editable fields -->
          <div>
            <label class="label">Номер техпаспорта</label>
            <input v-if="canEditSupplierFields" v-model="fields.tech_passport_number" type="text" class="input-field" />
            <p v-else class="text-sm font-medium text-gray-800">{{ contract.tech_passport_number || 'Не указан' }}</p>
          </div>
          <div>
            <label class="label">Дата выдачи техпаспорта</label>
            <input v-if="canEditSupplierFields" v-model="fields.tech_passport_date" type="date" class="input-field" />
            <p v-else class="text-sm font-medium text-gray-800">{{ contract.tech_passport_date || 'Не указана' }}</p>
          </div>

          <!-- Read-only computed fields -->
          <div>
            <label class="label">НДС</label>
            <p class="text-sm font-medium text-gray-800">{{ contract.vat_rate != null ? `${contract.vat_rate}%` : 'Будет установлен при подтверждении' }}</p>
          </div>
          <div>
            <label class="label">Период</label>
            <p class="text-sm font-medium text-gray-800">{{ formatDate(contract.start_date) }} — {{ formatDate(contract.end_date) }}</p>
          </div>
        </div>

        <div v-if="canEditLessorFields || canEditSupplierFields" class="mt-4">
          <button @click="saveFields" :disabled="savingFields" class="btn-primary btn-sm">
            {{ savingFields ? 'Сохранение...' : 'Сохранить изменения' }}
          </button>
        </div>
      </div>

      <!-- Confirmation section -->
      <div class="card p-6 mb-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">Подтверждение данных сторонами</h2>

        <div v-if="contract.all_confirmed" class="flex items-center gap-2 text-green-600 mb-4">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <span class="font-medium">Все стороны подтвердили данные</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div class="flex items-center gap-2">
            <span :class="contract.lessor_confirmed ? 'text-green-600' : 'text-gray-400'">
              {{ contract.lessor_confirmed ? '&#10003;' : '&#x25CB;' }}
            </span>
            <span>Лизингодатель: {{ contract.lessor_confirmed ? 'Подтвердил' : 'Ожидает' }}</span>
          </div>
          <div v-if="contract.lessee_id" class="flex items-center gap-2">
            <span :class="contract.lessee_confirmed ? 'text-green-600' : 'text-gray-400'">
              {{ contract.lessee_confirmed ? '&#10003;' : '&#x25CB;' }}
            </span>
            <span>Лизингополучатель: {{ contract.lessee_confirmed ? 'Подтвердил' : 'Ожидает' }}</span>
          </div>
          <div v-if="contract.supplier_id" class="flex items-center gap-2">
            <span :class="contract.supplier_confirmed ? 'text-green-600' : 'text-gray-400'">
              {{ contract.supplier_confirmed ? '&#10003;' : '&#x25CB;' }}
            </span>
            <span>Поставщик: {{ contract.supplier_confirmed ? 'Подтвердил' : 'Ожидает' }}</span>
          </div>
        </div>

        <div v-if="canConfirm && !contract.all_confirmed" class="flex gap-2 mt-4">
          <button @click="doConfirm(true)" class="btn-success btn-sm">Подтвердить</button>
          <button @click="doConfirm(false)" class="btn-danger btn-sm">Отклонить</button>
        </div>
      </div>

      <!-- Documents section -->
      <div class="card p-6 mb-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">Документы</h2>

        <div v-if="!contract.all_confirmed" class="text-sm text-gray-500">
          Документы будут доступны после подтверждения всеми сторонами.
        </div>
        <template v-else>
          <div v-if="contract.psa_doc_url || contract.la_doc_url" class="space-y-2">
            <a v-if="contract.psa_doc_url" :href="contract.psa_doc_url" target="_blank" class="flex items-center gap-2 text-sm text-primary-500 hover:underline">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              Скачать договор купли-продажи (.docx)
            </a>
            <a v-if="contract.la_doc_url" :href="contract.la_doc_url" target="_blank" class="flex items-center gap-2 text-sm text-primary-500 hover:underline">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              Скачать договор лизинга (.docx)
            </a>
          </div>
          <div v-else class="flex items-center gap-3">
            <p class="text-sm text-gray-500">Документы ещё не сформированы.</p>
            <button @click="generateDocs" :disabled="generatingDocs" class="btn-primary btn-sm">
              {{ generatingDocs ? 'Генерация...' : 'Сформировать документы' }}
            </button>
          </div>
        </template>
      </div>

      <!-- Payment schedule (only for lease contracts) -->
      <div v-if="contract.contract_type === 'lease'" class="card p-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">График платежей</h2>
        <div v-if="schedule.length === 0" class="text-center text-gray-500 py-8">
          <p>График ещё не сформирован.</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-surface-200 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th class="pb-3 pr-4">No</th>
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
                          @click="confirmPayment(s)" class="btn-primary btn-sm">
                    Оплатить
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Confirmation Modal -->
      <div v-if="showConfirmModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showConfirmModal = false">
        <div class="bg-white rounded-2xl w-full max-w-sm m-4 p-6">
          <h2 class="text-lg font-bold text-gray-900 mb-3">{{ confirmModalTitle }}</h2>
          <p class="text-sm text-gray-600 mb-6">{{ confirmModalText }}</p>
          <div class="flex gap-3">
            <button @click="showConfirmModal = false" class="btn-secondary flex-1">Отмена</button>
            <button @click="executeConfirmedAction" class="btn-primary flex-1">Подтвердить</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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
const savingFields = ref(false)
const generatingDocs = ref(false)

const fields = ref({
  signing_date: '',
  signing_city: '',
  currency: 'BYN',
  tech_passport_number: '',
  tech_passport_date: '',
})

const showConfirmModal = ref(false)
const confirmModalTitle = ref('')
const confirmModalText = ref('')
let pendingAction = null

const canEditLessorFields = computed(() => {
  if (!contract.value || contract.value.all_confirmed) return false
  return auth.userRole === 'lease_manager' && contract.value.lessor_id === auth.user?.id
})

const canEditSupplierFields = computed(() => {
  if (!contract.value || contract.value.all_confirmed) return false
  return auth.userRole === 'supplier' && contract.value.supplier_id === auth.user?.id
})

const canConfirm = computed(() => {
  if (!contract.value || contract.value.all_confirmed) return false
  const uid = auth.user?.id
  if (uid === contract.value.lessor_id && !contract.value.lessor_confirmed) return true
  if (uid === contract.value.lessee_id && !contract.value.lessee_confirmed) return true
  if (uid === contract.value.supplier_id && !contract.value.supplier_confirmed) return true
  return false
})

onMounted(async () => {
  try {
    const [cRes, sRes] = await Promise.all([
      leasingApi.getContract(route.params.id),
      leasingApi.getSchedule(route.params.id),
    ])
    contract.value = cRes.data
    schedule.value = sRes.data
    syncFieldsFromContract()
  } finally {
    loading.value = false
  }
})

function syncFieldsFromContract() {
  const c = contract.value
  if (!c) return
  fields.value = {
    signing_date: c.signing_date || '',
    signing_city: c.signing_city || '',
    currency: c.currency || 'BYN',
    tech_passport_number: c.tech_passport_number || '',
    tech_passport_date: c.tech_passport_date || '',
  }
}

async function saveFields() {
  savingFields.value = true
  try {
    const payload = {}
    if (canEditLessorFields.value) {
      if (fields.value.signing_date) payload.signing_date = fields.value.signing_date
      if (fields.value.signing_city) payload.signing_city = fields.value.signing_city
      if (fields.value.currency) payload.currency = fields.value.currency
    }
    if (canEditSupplierFields.value) {
      if (fields.value.tech_passport_number) payload.tech_passport_number = fields.value.tech_passport_number
      if (fields.value.tech_passport_date) payload.tech_passport_date = fields.value.tech_passport_date
    }
    const { data } = await leasingApi.updateContractFields(route.params.id, payload)
    contract.value = data
    syncFieldsFromContract()
    notifStore.showToast('Данные сохранены', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  } finally {
    savingFields.value = false
  }
}

async function doConfirm(confirmed) {
  try {
    const { data } = await leasingApi.confirmContract(route.params.id, confirmed)
    contract.value = data
    notifStore.showToast(confirmed ? 'Данные подтверждены' : 'Данные отклонены', confirmed ? 'success' : 'warning')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  }
}

async function generateDocs() {
  generatingDocs.value = true
  try {
    const { data } = await leasingApi.generateDocuments(route.params.id)
    contract.value = data
    notifStore.showToast('Документы сформированы', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка при генерации документов', 'error')
  } finally {
    generatingDocs.value = false
  }
}

function confirmStatusChange(newStatus) {
  const labels = {
    active: { title: 'Активировать договор', text: 'Вы уверены, что хотите активировать данный договор?' },
    completed: { title: 'Завершить договор', text: 'Вы уверены, что хотите завершить данный договор?' },
  }
  confirmModalTitle.value = labels[newStatus]?.title || 'Подтверждение'
  confirmModalText.value = labels[newStatus]?.text || 'Вы уверены?'
  pendingAction = () => updateStatus(newStatus)
  showConfirmModal.value = true
}

function confirmGenerateSchedule() {
  confirmModalTitle.value = 'Сформировать график'
  confirmModalText.value = 'Сформировать график платежей для данного договора?'
  pendingAction = () => generateSchedule()
  showConfirmModal.value = true
}

function confirmPayment(s) {
  confirmModalTitle.value = 'Подтвердить оплату'
  confirmModalText.value = `Оплатить платёж на сумму ${formatPrice(s.total_amount)}?`
  pendingAction = () => makePayment(s)
  showConfirmModal.value = true
}

async function executeConfirmedAction() {
  showConfirmModal.value = false
  if (pendingAction) {
    await pendingAction()
    pendingAction = null
  }
}

async function updateStatus(status) {
  try {
    const { data } = await leasingApi.updateContractStatus(route.params.id, status)
    contract.value = data
    notifStore.showToast('Статус обновлён', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  }
}

async function generateSchedule() {
  try {
    const { data } = await leasingApi.generateSchedule(route.params.id)
    schedule.value = data
    notifStore.showToast('График сформирован', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  }
}

async function makePayment(s) {
  try {
    await leasingApi.makePayment({
      contract_id: contract.value.id,
      payment_schedule_id: s.id,
      amount: s.total_amount,
    })
    s.status = 'paid'
    notifStore.showToast('Платёж выполнен', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  }
}
</script>
