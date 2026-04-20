<template>
  <div class="max-w-screen-2xl mx-auto px-4 sm:px-6 py-6">
    <LoadingSpinner v-if="loading" />
    <template v-else-if="vehicle">
      <div class="mb-4">
        <router-link to="/" class="text-sm text-primary-500 hover:underline">&larr; Назад к каталогу</router-link>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <!-- Images -->
        <div class="lg:col-span-3">
          <div class="card overflow-hidden">
            <div class="aspect-[16/10] bg-surface-100">
              <img v-if="vehicle.images?.length" :src="vehicle.images[selectedImage].image_url" :alt="vehicle.name"
                   class="w-full h-full object-cover" />
              <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                <svg class="w-20 h-20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5" />
                </svg>
              </div>
            </div>
            <div v-if="vehicle.images?.length > 1" class="flex gap-2 p-3 overflow-x-auto">
              <button v-for="(img, i) in vehicle.images" :key="img.id" @click="selectedImage = i"
                      :class="['w-16 h-16 rounded-lg overflow-hidden border-2 flex-shrink-0 transition-colors',
                               i === selectedImage ? 'border-primary-500' : 'border-transparent']">
                <img :src="img.image_url" class="w-full h-full object-cover" />
              </button>
            </div>
          </div>
        </div>

        <!-- Info -->
        <div class="lg:col-span-2 space-y-4">
          <div class="card p-6">
            <h1 class="text-xl font-bold text-gray-900">{{ vehicle.name }}</h1>
            <p class="text-sm text-gray-500 mt-1">{{ vehicle.brand }} {{ vehicle.model }}</p>
            <div class="text-2xl font-bold text-primary-500 mt-4">{{ formatPrice(vehicle.price) }}</div>
            <div v-if="priceUsd != null" class="text-sm text-gray-500 mt-1">{{ formatUsdAmount(priceUsd) }}</div>
            <div class="flex items-center gap-2 mt-2 text-sm text-gray-500">
              <span :class="vehicle.condition === 'new' ? 'text-green-600 font-medium' : ''">
                {{ vehicle.condition === 'new' ? 'Новый' : 'С пробегом' }}
              </span>
              <span>&middot;</span>
              <span>{{ vehicle.count > 0 ? `В наличии: ${vehicle.count} шт.` : 'Нет в наличии' }}</span>
            </div>

            <button v-if="auth.isAuthenticated && auth.userRole === 'client'"
                    type="button"
                    @click="openLeaseRequestFlow" class="btn-primary w-full mt-6">
              Подать заявку на лизинг
            </button>
            <button v-else-if="auth.isAuthenticated && auth.userRole === 'lease_manager'"
                    type="button"
                    @click="openPurchaseFlow" class="btn-primary w-full mt-6">
              Заявка на покупку
            </button>
            <router-link v-else-if="!auth.isAuthenticated" to="/login" class="btn-primary w-full mt-6 text-center">
              Войдите для подачи заявки
            </router-link>
          </div>

          <!-- Supplier info -->
          <router-link
            :to="`/users/${vehicle.seller?.id ?? vehicle.supplier_id}`"
            class="card p-4 flex items-center gap-3 hover:bg-surface-50 transition-colors"
          >
            <div class="w-10 h-10 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-semibold flex-shrink-0 overflow-hidden">
              <img v-if="vehicle.seller?.avatar_url" :src="vehicle.seller.avatar_url" class="w-full h-full object-cover" alt="" />
              <span v-else>{{ sellerInitial }}</span>
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-gray-900 truncate">{{ sellerDisplayName }}</p>
              <p class="text-xs text-gray-500 truncate">Профиль поставщика</p>
            </div>
            <svg class="w-4 h-4 text-gray-400 ml-auto flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>

          <!-- Specs -->
          <div class="card p-6">
            <h3 class="text-sm font-semibold text-gray-800 mb-4">Характеристики</h3>
            <div class="space-y-2.5">
              <div v-if="hasSpec(vehicle.vehicle_type)" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">Тип ТС</span><span class="font-medium text-gray-800 text-right">{{ vehicle.vehicle_type }}</span>
              </div>
              <div v-if="hasSpec(vehicle.release_year)" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">Год выпуска</span><span class="font-medium text-gray-800 text-right">{{ vehicle.release_year }}</span>
              </div>
              <div v-if="vehicle.mileage != null" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">Пробег</span><span class="font-medium text-gray-800 text-right">{{ formatMileage(vehicle.mileage) }}</span>
              </div>
              <div v-if="hasSpec(vehicle.vin)" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">VIN</span><span class="font-medium text-gray-800 text-right break-all">{{ vehicle.vin }}</span>
              </div>
              <div v-if="hasSpec(vehicle.colour)" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">Цвет</span><span class="font-medium text-gray-800 text-right">{{ vehicle.colour }}</span>
              </div>
              <div v-if="hasSpec(vehicle.location)" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">Местоположение</span><span class="font-medium text-gray-800 text-right">{{ vehicle.location }}</span>
              </div>
              <div v-if="hasSpec(vehicle.fuel_type)" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">Тип двигателя</span><span class="font-medium text-gray-800 text-right">{{ vehicle.fuel_type }}</span>
              </div>
              <div v-if="vehicle.engine_capacity != null" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">Объём двигателя</span><span class="font-medium text-gray-800 text-right">{{ vehicle.engine_capacity }} л</span>
              </div>
              <div v-if="vehicle.hp != null" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">Мощность</span><span class="font-medium text-gray-800 text-right">{{ vehicle.hp }} л.с.</span>
              </div>
              <div v-if="hasSpec(vehicle.transmission)" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">Трансмиссия</span><span class="font-medium text-gray-800 text-right">{{ vehicle.transmission }}</span>
              </div>
              <div v-if="hasSpec(vehicle.drive_type)" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">Привод</span><span class="font-medium text-gray-800 text-right">{{ vehicle.drive_type }}</span>
              </div>
              <div v-if="hasSpec(vehicle.product_code)" class="flex justify-between text-sm gap-4">
                <span class="text-gray-500">Код предложения</span><span class="font-medium text-gray-800 text-right">{{ vehicle.product_code }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Description -->
      <div v-if="vehicle.description || vehicle.extras" class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <div v-if="vehicle.description" class="card p-6">
          <h3 class="text-sm font-semibold text-gray-800 mb-3">Описание</h3>
          <p class="text-sm text-gray-600 whitespace-pre-line">{{ vehicle.description }}</p>
        </div>
        <div v-if="vehicle.extras" class="card p-6">
          <h3 class="text-sm font-semibold text-gray-800 mb-3">Комплектация</h3>
          <p class="text-sm text-gray-600 whitespace-pre-line">{{ vehicle.extras }}</p>
        </div>
      </div>

      <!-- Lessor Selection Modal -->
      <div v-if="showLessorModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showLessorModal = false">
        <div class="bg-white rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col m-4">
          <div class="flex items-center justify-between p-6 border-b border-surface-200">
            <h2 class="text-lg font-bold text-gray-900">Выберите лизингодателя</h2>
            <button @click="showLessorModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          <div class="p-4 border-b border-surface-200">
            <input v-model="lessorSearch" type="text" class="input-field" placeholder="Поиск по названию организации..." />
          </div>
          <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <LoadingSpinner v-if="lessorsLoading" />
            <div
              v-for="l in filteredLessors"
              :key="l.id"
              :class="[
                'flex items-center justify-between p-4 rounded-lg border transition-colors',
                lessorEligible(l)
                  ? 'border-surface-200 hover:border-primary-300'
                  : 'border-gray-100 bg-gray-50 opacity-70 cursor-not-allowed',
              ]"
            >
              <div class="min-w-0 pr-2">
                <p class="font-medium text-gray-900">
                  {{ l.company?.legal_form }} «{{ l.company?.company_name }}»
                </p>
                <div v-if="l.lease_terms" class="text-xs text-gray-500 mt-1 flex flex-wrap gap-x-3 gap-y-1">
                  <span>Стоимость техники: {{ formatPrice(l.lease_terms.min_asset_price) }} — {{ formatPrice(l.lease_terms.max_asset_price) }}</span>
                  <span>Срок: {{ l.lease_terms.min_term_months }}–{{ l.lease_terms.max_term_months }} мес.</span>
                  <span>Аванс: {{ l.lease_terms.min_prepayment_pct }}–{{ l.lease_terms.max_prepayment_pct }}%</span>
                  <span>Ставка: {{ l.lease_terms.interest_rate }}%</span>
                </div>
                <p v-else class="text-xs text-amber-700 mt-1">Условия не указаны</p>
                <p v-if="l.lease_terms && !lessorEligible(l)" class="text-xs text-red-600 mt-1">
                  Стоимость объявления вне диапазона этой компании
                </p>
                <StarRating v-if="l.rating" :rating="l.rating" class="mt-1" />
              </div>
              <button
                type="button"
                :disabled="!lessorEligible(l)"
                class="btn-primary btn-sm flex-shrink-0 disabled:opacity-40 disabled:pointer-events-none"
                @click="selectLessor(l)"
              >
                Оставить заявку
              </button>
            </div>
            <p v-if="!lessorsLoading && filteredLessors.length === 0" class="text-center text-gray-500 py-8">Лизингодатели не найдены</p>
          </div>
        </div>
      </div>

      <!-- Request Form Modal -->
      <div v-if="showRequestModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showRequestModal = false">
        <div class="bg-white rounded-2xl w-full max-w-md m-4 p-6">
          <h2 class="text-lg font-bold text-gray-900 mb-4">Заявка на лизинг</h2>
          <p class="text-sm text-gray-500 mb-4">
            Лизингодатель: <span class="font-medium text-gray-800">{{ selectedLessor?.company?.company_name }}</span>
          </p>
          <form @submit.prevent="submitRequest" class="space-y-4">
            <div>
              <label class="label">Предмет лизинга</label>
              <input type="text" class="input-field bg-surface-50" :value="vehicle.name" disabled />
            </div>
            <div>
              <label class="label">Срок лизинга (месяцев)</label>
              <input
                v-model.number="requestForm.lease_term"
                type="number"
                class="input-field"
                :min="requestTermMin"
                :max="requestTermMax"
                required
              />
              <p v-if="selectedLessor?.lease_terms" class="text-xs text-gray-400 mt-1">
                Допустимо: {{ requestTermMin }}–{{ requestTermMax }} мес.
              </p>
            </div>
            <div>
              <label class="label">Первоначальный взнос (BYN)</label>
              <input
                v-model.number="requestForm.prepayment"
                type="number"
                class="input-field"
                step="0.01"
                :min="requestPrepaymentMin"
                :max="requestPrepaymentMax"
                required
              />
              <p v-if="selectedLessor?.lease_terms && vehicle" class="text-xs text-gray-400 mt-1">
                Допустимо: {{ formatPrice(requestPrepaymentMin) }} — {{ formatPrice(requestPrepaymentMax) }}
              </p>
            </div>
            <div>
              <label class="label">Комментарий</label>
              <textarea v-model="requestForm.comment" class="input-field" rows="3" placeholder="Дополнительная информация..."></textarea>
            </div>
            <div class="flex gap-3">
              <button type="button" @click="showRequestModal = false" class="btn-secondary flex-1">Отмена</button>
              <button type="submit" :disabled="requestLoading" class="btn-primary flex-1">
                {{ requestLoading ? 'Отправка...' : 'Отправить заявку' }}
              </button>
            </div>
          </form>
        </div>
      </div>
      <!-- Purchase Request Modal (for lease_manager) -->
      <div v-if="showPurchaseModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showPurchaseModal = false">
        <div class="bg-white rounded-2xl w-full max-w-md m-4 p-6">
          <h2 class="text-lg font-bold text-gray-900 mb-4">Заявка на покупку техники</h2>
          <p class="text-sm text-gray-500 mb-4">Техника: <span class="font-medium text-gray-800">{{ vehicle.name }}</span></p>
          <form @submit.prevent="submitPurchaseRequest" class="space-y-4">
            <div>
              <label class="label">Связанная заявка на лизинг (ID)</label>
              <select v-model.number="purchaseForm.lease_request_id" class="input-field" required>
                <option value="" disabled>Выберите заявку</option>
                <option v-for="lr in myLeaseRequests" :key="lr.id" :value="lr.id">
                  Заявка #{{ lr.id }} — {{ lr.vehicle_name || `Объявление #${lr.vehicle_id}` }}
                </option>
              </select>
              <p class="text-xs text-gray-400 mt-1">Выберите заявку лизингополучателя, в рамках которой покупается техника</p>
            </div>
            <div>
              <label class="label">Количество (шт.)</label>
              <input v-model.number="purchaseForm.quantity" type="number" class="input-field" min="1" required />
            </div>
            <div class="flex gap-3">
              <button type="button" @click="showPurchaseModal = false" class="btn-secondary flex-1">Отмена</button>
              <button type="submit" :disabled="purchaseLoading" class="btn-primary flex-1">
                {{ purchaseLoading ? 'Отправка...' : 'Отправить заявку' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { vehiclesApi } from '@/api/vehicles'
import { usersApi } from '@/api/users'
import { leasingApi } from '@/api/leasing'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { formatPrice, formatUsdAmount, formatMileage } from '@/utils/format'
import { hasBankRequisites } from '@/utils/banking'
import { exchangeRatesApi } from '@/api/exchangeRates'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StarRating from '@/components/common/StarRating.vue'

function hasSpec(v) {
  if (v === null || v === undefined) return false
  if (typeof v === 'string') return v.trim() !== ''
  return true
}

const route = useRoute()
const auth = useAuthStore()
const notifStore = useNotificationsStore()

const vehicle = ref(null)
const loading = ref(true)
const selectedImage = ref(0)
const usdRateBynPerUnit = ref(null)

const showLessorModal = ref(false)
const showRequestModal = ref(false)
const lessors = ref([])
const lessorsLoading = ref(false)
const lessorSearch = ref('')
const selectedLessor = ref(null)
const requestForm = ref({ lease_term: 24, prepayment: 0, comment: '' })
const requestLoading = ref(false)

const showPurchaseModal = ref(false)
const purchaseForm = ref({ lease_request_id: '', quantity: 1 })
const purchaseLoading = ref(false)
const myLeaseRequests = ref([])

const priceUsd = computed(() => {
  const price = vehicle.value?.price
  const rate = usdRateBynPerUnit.value
  if (price == null || rate == null || rate <= 0) return null
  return price / rate
})

const sellerDisplayName = computed(() => {
  const s = vehicle.value?.seller
  if (s?.display_name) return s.display_name
  return 'Поставщик'
})

const sellerInitial = computed(() => sellerDisplayName.value?.charAt(0)?.toUpperCase() || '?')

const filteredLessors = computed(() => {
  const s = lessorSearch.value.toLowerCase()
  if (!s) return lessors.value
  return lessors.value.filter(l =>
    l.company?.company_name?.toLowerCase().includes(s) ||
    l.login?.toLowerCase().includes(s)
  )
})

const requestTermMin = computed(() => selectedLessor.value?.lease_terms?.min_term_months ?? 6)
const requestTermMax = computed(() => selectedLessor.value?.lease_terms?.max_term_months ?? 84)
const requestPrepaymentMin = computed(() => {
  const lt = selectedLessor.value?.lease_terms
  const price = vehicle.value?.price
  if (!lt || price == null) return 0
  return Math.round((price * lt.min_prepayment_pct) / 100 * 100) / 100
})
const requestPrepaymentMax = computed(() => {
  const lt = selectedLessor.value?.lease_terms
  const price = vehicle.value?.price
  if (!lt || price == null) return 0
  return Math.round((price * lt.max_prepayment_pct) / 100 * 100) / 100
})

function lessorEligible(l) {
  const lt = l.lease_terms
  const price = vehicle.value?.price
  if (price == null) return false
  if (!lt) return true
  return price >= lt.min_asset_price && price <= lt.max_asset_price
}

function initRequestForm() {
  const l = selectedLessor.value
  const lt = l?.lease_terms
  const price = vehicle.value?.price ?? 0
  if (!lt || !price) {
    requestForm.value = { lease_term: 24, prepayment: 0, comment: '' }
    return
  }
  let term = Math.round((lt.min_term_months + lt.max_term_months) / 2)
  term = Math.min(lt.max_term_months, Math.max(lt.min_term_months, term))
  const midPct = (lt.min_prepayment_pct + lt.max_prepayment_pct) / 2
  let prep = (price * midPct) / 100
  const pMin = (price * lt.min_prepayment_pct) / 100
  const pMax = (price * lt.max_prepayment_pct) / 100
  prep = Math.min(pMax, Math.max(pMin, prep))
  requestForm.value = {
    lease_term: term,
    prepayment: Math.round(prep * 100) / 100,
    comment: '',
  }
}

onMounted(async () => {
  try {
    const [vehicleRes, ratesRes] = await Promise.allSettled([
      vehiclesApi.get(route.params.id),
      exchangeRatesApi.get(),
    ])
    if (vehicleRes.status === 'fulfilled') {
      vehicle.value = vehicleRes.value.data
    }
    if (ratesRes.status === 'fulfilled') {
      const list = ratesRes.value.data?.currencies || []
      const usd = list.find((c) => c.code === 'USD')
      if (usd?.rate_byn_per_unit > 0) {
        usdRateBynPerUnit.value = usd.rate_byn_per_unit
      }
    }
  } finally {
    loading.value = false
  }
})

watch(showPurchaseModal, async (val) => {
  if (val && myLeaseRequests.value.length === 0) {
    try {
      const { data } = await leasingApi.listRequests({ status: 'in_review', limit: 100 })
      myLeaseRequests.value = data
    } catch {}
  }
})

watch(showLessorModal, async (val) => {
  if (val && lessors.value.length === 0) {
    lessorsLoading.value = true
    try {
      const { data } = await usersApi.listUsers({ role: 'lease_manager', limit: 100 })
      lessors.value = data
    } finally {
      lessorsLoading.value = false
    }
  }
})

const bankRequiredMsg =
  'Укажите в профиле хотя бы один банковский счёт: IBAN, название и адрес отделения банка, BIC или SWIFT.'

function openLeaseRequestFlow() {
  if (!hasBankRequisites(auth.user)) {
    notifStore.showToast(bankRequiredMsg, 'error')
    return
  }
  showLessorModal.value = true
}

function openPurchaseFlow() {
  if (!hasBankRequisites(auth.user)) {
    notifStore.showToast(bankRequiredMsg, 'error')
    return
  }
  showPurchaseModal.value = true
}

function selectLessor(l) {
  if (!lessorEligible(l)) return
  if (!hasBankRequisites(auth.user)) {
    notifStore.showToast(bankRequiredMsg, 'error')
    return
  }
  selectedLessor.value = l
  initRequestForm()
  showLessorModal.value = false
  showRequestModal.value = true
}

async function submitPurchaseRequest() {
  if (!hasBankRequisites(auth.user)) {
    notifStore.showToast(bankRequiredMsg, 'error')
    return
  }
  purchaseLoading.value = true
  try {
    await leasingApi.createSupplierRequest({
      lease_request_id: purchaseForm.value.lease_request_id,
      vehicle_id: vehicle.value.id,
      quantity: purchaseForm.value.quantity,
    })
    showPurchaseModal.value = false
    notifStore.showToast('Заявка на покупку отправлена поставщику!', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  } finally {
    purchaseLoading.value = false
  }
}

async function submitRequest() {
  if (!hasBankRequisites(auth.user)) {
    notifStore.showToast(bankRequiredMsg, 'error')
    return
  }
  const lt = selectedLessor.value?.lease_terms
  const price = vehicle.value?.price
  if (lt && price != null) {
    const t = requestForm.value.lease_term
    if (t < lt.min_term_months || t > lt.max_term_months) {
      notifStore.showToast('Укажите срок лизинга в допустимом диапазоне', 'error')
      return
    }
    const prep = requestForm.value.prepayment
    if (prep < requestPrepaymentMin.value - 0.01 || prep > requestPrepaymentMax.value + 0.01) {
      notifStore.showToast('Укажите первоначальный взнос в допустимом диапазоне', 'error')
      return
    }
  }
  requestLoading.value = true
  try {
    await leasingApi.createRequest({
      lease_company_id: selectedLessor.value.id,
      vehicle_id: vehicle.value.id,
      lease_term: requestForm.value.lease_term,
      prepayment: requestForm.value.prepayment,
      comment: requestForm.value.comment,
    })
    showRequestModal.value = false
    notifStore.showToast('Заявка успешно отправлена!', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  } finally {
    requestLoading.value = false
  }
}
</script>
