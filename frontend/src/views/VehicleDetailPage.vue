<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-6">
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
            <div class="flex items-center gap-2 mt-2 text-sm text-gray-500">
              <span :class="vehicle.condition === 'new' ? 'text-green-600 font-medium' : ''">
                {{ vehicle.condition === 'new' ? 'Новый' : 'С пробегом' }}
              </span>
              <span>&middot;</span>
              <span>{{ vehicle.count > 0 ? `В наличии: ${vehicle.count} шт.` : 'Нет в наличии' }}</span>
            </div>

            <button v-if="auth.isAuthenticated && auth.userRole === 'client'"
                    @click="showLessorModal = true" class="btn-primary w-full mt-6">
              Подать заявку на лизинг
            </button>
            <router-link v-else-if="!auth.isAuthenticated" to="/login" class="btn-primary w-full mt-6 text-center">
              Войдите для подачи заявки
            </router-link>
          </div>

          <!-- Supplier info -->
          <router-link :to="`/users/${vehicle.supplier_id}`" class="card p-4 flex items-center gap-3 hover:bg-surface-50 transition-colors">
            <div class="w-10 h-10 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-semibold flex-shrink-0">
              П
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-gray-900">Продавец</p>
              <p class="text-xs text-gray-500 truncate">Перейти в профиль поставщика</p>
            </div>
            <svg class="w-4 h-4 text-gray-400 ml-auto flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>

          <!-- Specs -->
          <div class="card p-6">
            <h3 class="text-sm font-semibold text-gray-800 mb-4">Характеристики</h3>
            <div class="space-y-2.5">
              <SpecRow label="Тип ТС" :value="vehicle.vehicle_type" />
              <SpecRow label="Год выпуска" :value="vehicle.release_year" />
              <SpecRow label="Пробег" :value="vehicle.mileage != null ? formatMileage(vehicle.mileage) : null" />
              <SpecRow label="VIN" :value="vehicle.vin" />
              <SpecRow label="Цвет" :value="vehicle.colour" />
              <SpecRow label="Местоположение" :value="vehicle.location" />
              <SpecRow label="Тип двигателя" :value="vehicle.fuel_type" />
              <SpecRow label="Объём двигателя" :value="vehicle.engine_capacity ? `${vehicle.engine_capacity} л` : null" />
              <SpecRow label="Мощность" :value="vehicle.hp ? `${vehicle.hp} л.с.` : null" />
              <SpecRow label="Трансмиссия" :value="vehicle.transmission" />
              <SpecRow label="Привод" :value="vehicle.drive_type" />
              <SpecRow label="Код предложения" :value="vehicle.product_code" />
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
            <div v-for="l in filteredLessors" :key="l.id" class="flex items-center justify-between p-4 rounded-lg border border-surface-200 hover:border-primary-300 transition-colors">
              <div>
                <p class="font-medium text-gray-900">
                  {{ l.company?.legal_form }} «{{ l.company?.company_name }}»
                </p>
                <div v-if="l.lease_terms" class="text-xs text-gray-500 mt-1 space-x-3">
                  <span>Срок: {{ l.lease_terms.min_term_months }}–{{ l.lease_terms.max_term_months }} мес.</span>
                  <span>Аванс: {{ l.lease_terms.min_prepayment_pct }}–{{ l.lease_terms.max_prepayment_pct }}%</span>
                  <span>Ставка: {{ l.lease_terms.interest_rate }}%</span>
                </div>
                <StarRating v-if="l.rating" :rating="l.rating" class="mt-1" />
              </div>
              <button @click="selectLessor(l)" class="btn-primary btn-sm flex-shrink-0">Оставить заявку</button>
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
              <input v-model.number="requestForm.lease_term" type="number" class="input-field" :min="selectedLessor?.lease_terms?.min_term_months || 6" :max="selectedLessor?.lease_terms?.max_term_months || 84" required />
            </div>
            <div>
              <label class="label">Первоначальный взнос (BYN)</label>
              <input v-model.number="requestForm.prepayment" type="number" class="input-field" step="0.01" required />
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
import { formatPrice, formatMileage } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StarRating from '@/components/common/StarRating.vue'

const SpecRow = { props: ['label', 'value'], template: `<div v-if="value" class="flex justify-between text-sm"><span class="text-gray-500">{{ label }}</span><span class="font-medium text-gray-800">{{ value }}</span></div>` }

const route = useRoute()
const auth = useAuthStore()
const notifStore = useNotificationsStore()

const vehicle = ref(null)
const loading = ref(true)
const selectedImage = ref(0)

const showLessorModal = ref(false)
const showRequestModal = ref(false)
const lessors = ref([])
const lessorsLoading = ref(false)
const lessorSearch = ref('')
const selectedLessor = ref(null)
const requestForm = ref({ lease_term: 24, prepayment: 0, comment: '' })
const requestLoading = ref(false)

const filteredLessors = computed(() => {
  const s = lessorSearch.value.toLowerCase()
  if (!s) return lessors.value
  return lessors.value.filter(l =>
    l.company?.company_name?.toLowerCase().includes(s) ||
    l.login?.toLowerCase().includes(s)
  )
})

onMounted(async () => {
  try {
    const { data } = await vehiclesApi.get(route.params.id)
    vehicle.value = data
  } finally {
    loading.value = false
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

function selectLessor(l) {
  selectedLessor.value = l
  showLessorModal.value = false
  showRequestModal.value = true
}

async function submitRequest() {
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
