<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
    <LoadingSpinner v-if="loading" />
    <template v-else-if="user">
      <!-- Profile Card -->
      <div class="card p-6 mb-6">
        <div class="flex items-start gap-6">
          <div class="w-20 h-20 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-2xl font-bold overflow-hidden flex-shrink-0">
            <img v-if="user.avatar_url" :src="user.avatar_url" class="w-full h-full object-cover" />
            <span v-else>{{ displayName?.charAt(0)?.toUpperCase() }}</span>
          </div>
          <div class="flex-1">
            <h1 class="text-xl font-bold text-gray-900">{{ displayName }}</h1>
            <div class="flex items-center gap-3 mt-1">
              <span class="badge badge-active">{{ roleLabels[user.role] }}</span>
              <span class="text-xs text-gray-500">{{ userTypeLabels[user.user_type] }}</span>
            </div>
            <div class="flex items-center gap-2 mt-2">
              <StarRating v-if="user.rating" :rating="user.rating" />
              <router-link v-if="user.reviews_count" :to="'#reviews'" class="text-xs text-primary-500 hover:underline">
                {{ user.reviews_count }} отзывов
              </router-link>
            </div>
            <p class="text-xs text-gray-400 mt-2">{{ getRegistrationDate(user.created_at) }}</p>
            <p v-if="user.description" class="text-sm text-gray-600 mt-3">{{ user.description }}</p>
          </div>
        </div>

        <!-- Contact info (public) -->
        <div v-if="user.contacts?.length" class="mt-4 flex flex-wrap gap-4 text-sm">
          <div v-for="c in user.contacts" :key="c.id" class="flex items-center gap-1.5 text-gray-600">
            <svg v-if="c.type === 'phone'" class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
            <svg v-else class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
            {{ c.value }}
          </div>
        </div>
      </div>

      <!-- Leasing Calculator (for lessors) -->
      <div v-if="user.role === 'lease_manager' && user.lease_terms" class="card p-6 mb-6">
        <h3 class="text-lg font-bold text-gray-900 mb-4">Калькулятор лизинга</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-5">
            <div>
              <label class="label">Стоимость имущества (BYN): <span class="font-bold text-primary-500">{{ formatPrice(calc.asset_price) }}</span></label>
              <input v-model.number="calc.asset_price" type="range"
                     :min="user.lease_terms.min_asset_price" :max="user.lease_terms.max_asset_price" step="1000"
                     class="w-full accent-primary-500" />
            </div>
            <div>
              <label class="label">
                Аванс: <span class="font-bold text-primary-500">{{ formatPrice(calc.prepayment) }}</span>
                <span class="text-gray-400 ml-1">({{ prepaymentPct.toFixed(1) }}%)</span>
              </label>
              <input v-model.number="calc.prepayment" type="range"
                     :min="calc.asset_price * user.lease_terms.min_prepayment_pct / 100"
                     :max="calc.asset_price * user.lease_terms.max_prepayment_pct / 100" step="500"
                     class="w-full accent-primary-500" />
            </div>
            <div>
              <label class="label">Срок лизинга: <span class="font-bold text-primary-500">{{ calc.term_months }} мес.</span></label>
              <input v-model.number="calc.term_months" type="range"
                     :min="user.lease_terms.min_term_months" :max="user.lease_terms.max_term_months"
                     class="w-full accent-primary-500" />
            </div>
          </div>
          <div class="bg-surface-50 rounded-xl p-6 flex flex-col justify-center">
            <div class="space-y-4">
              <div>
                <p class="text-sm text-gray-500">Ежемесячный платёж</p>
                <p class="text-2xl font-bold text-primary-500">{{ calcResult ? formatPrice(calcResult.monthly_payment) : '—' }}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">Сумма договора</p>
                <p class="text-lg font-semibold text-gray-900">{{ calcResult ? formatPrice(calcResult.total_amount) : '—' }}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">Переплата</p>
                <p class="text-lg font-semibold text-gray-600">{{ calcResult ? formatPrice(calcResult.overpayment) : '—' }}</p>
              </div>
            </div>
          </div>
        </div>
        <!-- General conditions -->
        <div class="mt-4 p-4 bg-surface-50 rounded-lg text-sm text-gray-600 grid grid-cols-2 md:grid-cols-4 gap-3">
          <div><span class="text-gray-400 block">Мин. срок</span>{{ user.lease_terms.min_term_months }} мес.</div>
          <div><span class="text-gray-400 block">Макс. срок</span>{{ user.lease_terms.max_term_months }} мес.</div>
          <div><span class="text-gray-400 block">Мин. аванс</span>{{ user.lease_terms.min_prepayment_pct }}%</div>
          <div><span class="text-gray-400 block">Макс. аванс</span>{{ user.lease_terms.max_prepayment_pct }}%</div>
        </div>
      </div>

      <!-- Supplier's Vehicles -->
      <div v-if="user.role === 'supplier'" class="mb-6">
        <h3 class="text-lg font-bold text-gray-900 mb-4">Каталог техники</h3>
        <div v-if="vehicles.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <router-link v-for="v in vehicles" :key="v.id" :to="`/vehicles/${v.id}`" class="card overflow-hidden hover:shadow-md transition-shadow">
            <div class="aspect-[16/10] bg-surface-100">
              <img v-if="v.images?.length" :src="v.images[0].image_url" class="w-full h-full object-cover" />
            </div>
            <div class="p-4">
              <h4 class="font-semibold text-gray-900 truncate">{{ v.name }}</h4>
              <p class="text-sm text-primary-500 font-bold mt-1">{{ formatPrice(v.price) }}</p>
            </div>
          </router-link>
        </div>
        <p v-else class="text-gray-500 text-sm">У поставщика пока нет объявлений.</p>
      </div>

      <!-- Reviews Section -->
      <div id="reviews" class="card p-6">
        <h3 class="text-lg font-bold text-gray-900 mb-4">Отзывы</h3>
        <div v-if="reviews.length" class="space-y-4">
          <div v-for="r in reviews" :key="r.id" class="p-4 border border-surface-200 rounded-lg">
            <div class="flex items-center justify-between">
              <StarRating :rating="r.rating" :show-value="false" />
              <span class="text-xs text-gray-400">{{ formatDate(r.created_at) }}</span>
            </div>
            <p v-if="r.comment" class="text-sm text-gray-600 mt-2">{{ r.comment }}</p>
          </div>
        </div>
        <p v-else class="text-sm text-gray-500">Отзывов пока нет.</p>

        <!-- Leave review -->
        <div v-if="auth.isAuthenticated && auth.user?.id !== user.id" class="mt-6 border-t border-surface-200 pt-4">
          <h4 class="text-sm font-semibold text-gray-800 mb-3">Оставить отзыв</h4>
          <StarRating v-model="reviewForm.rating" :editable="true" :show-value="false" class="mb-3" />
          <textarea v-model="reviewForm.comment" class="input-field" rows="2" placeholder="Ваш отзыв..."></textarea>
          <button @click="submitReview" class="btn-primary btn-sm mt-3">Отправить отзыв</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usersApi } from '@/api/users'
import { vehiclesApi } from '@/api/vehicles'
import { reviewsApi } from '@/api/reviews'
import { leasingApi } from '@/api/leasing'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { formatPrice, formatDate, roleLabels, userTypeLabels, getRegistrationDate } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StarRating from '@/components/common/StarRating.vue'

const route = useRoute()
const auth = useAuthStore()
const notifStore = useNotificationsStore()

const user = ref(null)
const loading = ref(true)
const vehicles = ref([])
const reviews = ref([])
const reviewForm = ref({ rating: 5, comment: '' })

const calc = ref({ asset_price: 50000, prepayment: 10000, term_months: 24 })
const calcResult = ref(null)

const displayName = computed(() => {
  if (!user.value) return ''
  if (user.value.individual) return user.value.individual.full_name
  if (user.value.entrepreneur) return user.value.entrepreneur.full_name
  if (user.value.company) {
    const form = user.value.company.legal_form || ''
    return `${form} «${user.value.company.company_name}»`
  }
  return user.value.login
})

const prepaymentPct = computed(() => {
  if (!calc.value.asset_price) return 0
  return (calc.value.prepayment / calc.value.asset_price) * 100
})

onMounted(() => loadUser())

watch(() => route.params.id, () => loadUser())

watch(calc, async () => {
  if (user.value?.role === 'lease_manager' && user.value.lease_terms) {
    try {
      const { data } = await leasingApi.calculate({
        asset_price: calc.value.asset_price,
        prepayment: calc.value.prepayment,
        term_months: calc.value.term_months,
        interest_rate: user.value.lease_terms.interest_rate,
      })
      calcResult.value = data
    } catch { /* ignore calc errors */ }
  }
}, { deep: true, immediate: false })

async function loadUser() {
  loading.value = true
  try {
    const { data } = await usersApi.getUser(route.params.id)
    user.value = data

    if (data.role === 'supplier') {
      const vRes = await vehiclesApi.list({ supplier_id: data.id, limit: 50 })
      vehicles.value = vRes.data
    }

    const rRes = await reviewsApi.getForUser(data.id)
    reviews.value = rRes.data

    if (data.role === 'lease_manager' && data.lease_terms) {
      calc.value.asset_price = (data.lease_terms.min_asset_price + data.lease_terms.max_asset_price) / 2
      calc.value.prepayment = calc.value.asset_price * data.lease_terms.min_prepayment_pct / 100
      calc.value.term_months = Math.round((data.lease_terms.min_term_months + data.lease_terms.max_term_months) / 2)
      const { data: cRes } = await leasingApi.calculate({
        asset_price: calc.value.asset_price,
        prepayment: calc.value.prepayment,
        term_months: calc.value.term_months,
        interest_rate: data.lease_terms.interest_rate,
      })
      calcResult.value = cRes
    }
  } finally {
    loading.value = false
  }
}

async function submitReview() {
  try {
    await reviewsApi.create({ target_id: user.value.id, ...reviewForm.value })
    const rRes = await reviewsApi.getForUser(user.value.id)
    reviews.value = rRes.data
    notifStore.showToast('Отзыв отправлен', 'success')
    reviewForm.value = { rating: 5, comment: '' }
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  }
}
</script>
