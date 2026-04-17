<template>
  <div class="relative" ref="rootRef">
    <button
      type="button"
      class="rates-btn"
      :aria-expanded="open"
      aria-haspopup="true"
      @click.stop="open = !open"
    >
      Курс валют
      <svg class="w-4 h-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <div
      v-if="open"
      class="absolute right-0 mt-2 w-[min(18rem,calc(100vw-2rem))] rounded-xl border border-surface-200 bg-white py-3 px-3 shadow-lg z-[60]"
      role="dialog"
      aria-label="Официальные курсы НБ РБ"
      @click.stop
    >
      <p v-if="rateDate" class="text-[11px] text-gray-500 mb-2">На дату: {{ rateDate }}</p>

      <table v-if="foreignRows.length" class="w-full text-xs text-left">
        <thead>
          <tr class="text-gray-500 border-b border-surface-100">
            <th class="pb-2 pr-2 font-medium w-8" />
            <th class="pb-2 pr-2 font-medium">Валюта</th>
            <th class="pb-2 font-medium text-right tabular-nums">BYN за 1 ед.</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in foreignRows" :key="c.code" class="border-b border-surface-50 last:border-0">
            <td class="py-2 pr-2 align-middle w-11" aria-hidden="true">
              <span
                v-if="flagIconSuffix(c.code)"
                class="text-[1.125rem] leading-none inline-flex align-middle rounded-sm overflow-hidden shadow-sm ring-1 ring-black/10"
              >
                <span :class="['fi', `fi-${flagIconSuffix(c.code)}`]" />
              </span>
              <span v-else class="text-sm">{{ c.flag }}</span>
            </td>
            <td class="py-2 pr-2 align-middle font-medium text-gray-800">{{ c.code }}</td>
            <td class="py-2 align-middle text-right tabular-nums text-gray-900">{{ formatRate(c) }}</td>
          </tr>
        </tbody>
      </table>

      <p v-else-if="!loading" class="text-xs text-gray-500 py-2">Не удалось загрузить курсы</p>
      <p v-else class="text-xs text-gray-500 py-2">Загрузка…</p>

      <p class="text-[11px] text-gray-500 mt-3 leading-snug">
        Значение для USD и EUR — сколько белорусских рублей стоит один доллар или один евро по официальному курсу НБ РБ.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { exchangeRatesApi } from '@/api/exchangeRates'

const rootRef = ref(null)
const open = ref(false)
const loading = ref(true)
const rateDate = ref('')
const currencies = ref([])

const foreignRows = computed(() => (currencies.value || []).filter((c) => c.code !== 'BYN'))

/** Коды flag-icons: https://github.com/lipis/flag-icons */
const CURRENCY_TO_FLAG_SUFFIX = {
  USD: 'us',
  EUR: 'eu',
  BYN: 'by',
}

function flagIconSuffix(code) {
  return CURRENCY_TO_FLAG_SUFFIX[code] ?? null
}

function formatRate(c) {
  const v = c.rate_byn_per_unit
  if (v == null) return '—'
  return v.toLocaleString('ru-BY', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
}

async function loadRates() {
  loading.value = true
  try {
    const { data } = await exchangeRatesApi.get()
    currencies.value = data.currencies || []
    if (data.rate_date) {
      const d = new Date(data.rate_date)
      rateDate.value = Number.isNaN(d.getTime())
        ? data.rate_date
        : d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
    }
  } catch {
    currencies.value = []
    rateDate.value = ''
  } finally {
    loading.value = false
  }
}

function onDocClick(e) {
  if (!open.value) return
  const el = rootRef.value
  if (el && !el.contains(e.target)) {
    open.value = false
  }
}

onMounted(() => {
  loadRates()
  document.addEventListener('click', onDocClick)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
})

watch(open, (v) => {
  if (v && !currencies.value.length && !loading.value) {
    loadRates()
  }
})
</script>

<style scoped>
.rates-btn {
  @apply inline-flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-600 rounded-lg;
  @apply hover:text-primary-500 hover:bg-primary-50 transition-colors;
}
</style>
