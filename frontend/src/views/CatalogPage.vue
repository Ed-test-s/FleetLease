<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Каталог техники</h1>
        <p class="text-sm text-gray-500 mt-1">Грузовые автомобили, тягачи, спецтехника</p>
      </div>
      <div class="flex items-center gap-3">
        <!-- Search -->
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input v-model="filters.search" @input="debouncedFetch" type="text" class="input-field pl-10 w-64"
                 placeholder="Поиск по названию..." />
        </div>
        <!-- Sort -->
        <select v-model="filters.sort_by" @change="fetchVehicles" class="input-field w-auto">
          <option value="newest">Сначала новые</option>
          <option value="oldest">Сначала старые</option>
          <option value="price_desc">Сначала дороже</option>
          <option value="price_asc">Сначала дешевле</option>
          <option value="mileage_asc">Меньший пробег</option>
          <option value="year_desc">Новее по году</option>
          <option value="year_asc">Старее по году</option>
        </select>
      </div>
    </div>

    <div class="flex gap-6">
      <!-- Sidebar Filters -->
      <aside class="hidden lg:block w-72 flex-shrink-0">
        <div class="card p-5 sticky top-20 space-y-5">
          <h3 class="text-sm font-semibold text-gray-800">Фильтры</h3>

          <div>
            <label class="label">Тип ТС</label>
            <select v-model="filters.vehicle_type" @change="fetchVehicles" class="input-field">
              <option value="">Все</option>
              <option v-for="t in vehicleTypes" :key="t">{{ t }}</option>
            </select>
          </div>

          <div>
            <label class="label">Марка</label>
            <input v-model="filters.brand" @input="debouncedFetch" type="text" class="input-field" placeholder="Например, MAN" />
          </div>

          <div>
            <label class="label">Модель</label>
            <input v-model="filters.model" @input="debouncedFetch" type="text" class="input-field" placeholder="Модель" />
          </div>

          <div>
            <label class="label">Состояние</label>
            <select v-model="filters.condition" @change="fetchVehicles" class="input-field">
              <option value="">Любое</option>
              <option value="new">Новый</option>
              <option value="used">С пробегом</option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="label">Цена от</label>
              <input v-model.number="filters.price_min" @input="debouncedFetch" type="number" class="input-field" placeholder="0" />
            </div>
            <div>
              <label class="label">Цена до</label>
              <input v-model.number="filters.price_max" @input="debouncedFetch" type="number" class="input-field" placeholder="∞" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="label">Год от</label>
              <input v-model.number="filters.year_min" @input="debouncedFetch" type="number" class="input-field" placeholder="2000" />
            </div>
            <div>
              <label class="label">Год до</label>
              <input v-model.number="filters.year_max" @input="debouncedFetch" type="number" class="input-field" placeholder="2026" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="label">Пробег от</label>
              <input v-model.number="filters.mileage_min" @input="debouncedFetch" type="number" class="input-field" placeholder="0" />
            </div>
            <div>
              <label class="label">Пробег до</label>
              <input v-model.number="filters.mileage_max" @input="debouncedFetch" type="number" class="input-field" placeholder="∞" />
            </div>
          </div>

          <div>
            <label class="label">Тип двигателя</label>
            <select v-model="filters.fuel_type" @change="fetchVehicles" class="input-field">
              <option value="">Все</option>
              <option>Дизельный</option>
              <option>Бензиновый</option>
              <option>Электро</option>
              <option>Гибрид</option>
            </select>
          </div>

          <div>
            <label class="label">Тип привода</label>
            <select v-model="filters.drive_type" @change="fetchVehicles" class="input-field">
              <option value="">Все</option>
              <option>Задний</option>
              <option>Передний</option>
              <option>Постоянный полный</option>
              <option>Подключаемый полный</option>
            </select>
          </div>

          <div>
            <label class="label">Цвет</label>
            <input v-model="filters.colour" @input="debouncedFetch" type="text" class="input-field" placeholder="Цвет кузова" />
          </div>

          <div>
            <label class="label">Город / Местоположение</label>
            <input v-model="filters.location" @input="debouncedFetch" type="text" class="input-field" placeholder="Минск" />
          </div>

          <div class="flex items-center gap-2">
            <input v-model="filters.in_stock" @change="fetchVehicles" type="checkbox" id="in_stock" class="rounded border-gray-300 text-primary-500 focus:ring-primary-500" />
            <label for="in_stock" class="text-sm text-gray-700">В наличии</label>
          </div>

          <button @click="resetFilters" class="btn-secondary w-full btn-sm">Сбросить фильтры</button>
        </div>
      </aside>

      <!-- Grid -->
      <div class="flex-1">
        <LoadingSpinner v-if="loading" />
        <div v-else-if="vehicles.length === 0" class="text-center py-16">
          <svg class="mx-auto w-16 h-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-gray-500">Техника не найдена</p>
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          <router-link v-for="v in vehicles" :key="v.id" :to="`/vehicles/${v.id}`"
                       class="card overflow-hidden hover:shadow-md transition-shadow group">
            <div class="aspect-[16/10] bg-surface-100 overflow-hidden">
              <img v-if="v.images?.length" :src="v.images[0].image_url" :alt="v.name"
                   class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
              <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5" />
                </svg>
              </div>
            </div>
            <div class="p-4">
              <h3 class="font-semibold text-gray-900 truncate">{{ v.name }}</h3>
              <p class="text-xs text-gray-500 mt-0.5">{{ v.brand }} {{ v.model }} · {{ v.release_year || '—' }}</p>
              <div class="flex items-center justify-between mt-3">
                <span class="text-lg font-bold text-primary-500">{{ formatPrice(v.price) }}</span>
                <span class="text-xs text-gray-400">{{ v.location || '' }}</span>
              </div>
              <div class="flex items-center gap-3 mt-2 text-xs text-gray-500">
                <span v-if="v.mileage != null">{{ formatMileage(v.mileage) }}</span>
                <span v-if="v.fuel_type">{{ v.fuel_type }}</span>
                <span :class="v.condition === 'new' ? 'text-green-600' : 'text-gray-500'">
                  {{ v.condition === 'new' ? 'Новый' : 'С пробегом' }}
                </span>
              </div>
            </div>
          </router-link>
        </div>

        <!-- Load more -->
        <div v-if="vehicles.length >= limit" class="text-center mt-6">
          <button @click="loadMore" class="btn-secondary">Загрузить ещё</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { vehiclesApi } from '@/api/vehicles'
import { formatPrice, formatMileage } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const vehicles = ref([])
const loading = ref(true)
const limit = 20
let skip = 0
let debounceTimer = null

const vehicleTypes = ['Грузовой транспорт', 'Тягач', 'Самосвал', 'Фургон', 'Прицеп', 'Полуприцеп', 'Спецтехника', 'Коммерческий транспорт']

const filters = ref({
  search: '', brand: '', model: '', vehicle_type: '', condition: '',
  price_min: null, price_max: null, year_min: null, year_max: null,
  mileage_min: null, mileage_max: null, fuel_type: '', drive_type: '',
  colour: '', location: '', in_stock: false, sort_by: 'newest',
})

onMounted(() => fetchVehicles())

function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchVehicles, 400)
}

async function fetchVehicles() {
  loading.value = true
  skip = 0
  try {
    const params = { skip: 0, limit }
    for (const [k, v] of Object.entries(filters.value)) {
      if (v !== '' && v !== null && v !== false) params[k] = v
    }
    const { data } = await vehiclesApi.list(params)
    vehicles.value = data
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  skip += limit
  const params = { skip, limit }
  for (const [k, v] of Object.entries(filters.value)) {
    if (v !== '' && v !== null && v !== false) params[k] = v
  }
  const { data } = await vehiclesApi.list(params)
  vehicles.value.push(...data)
}

function resetFilters() {
  filters.value = {
    search: '', brand: '', model: '', vehicle_type: '', condition: '',
    price_min: null, price_max: null, year_min: null, year_max: null,
    mileage_min: null, mileage_max: null, fuel_type: '', drive_type: '',
    colour: '', location: '', in_stock: false, sort_by: 'newest',
  }
  fetchVehicles()
}
</script>
