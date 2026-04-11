<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Каталог техники</h1>
        <p class="text-sm text-gray-500 mt-1">Грузовые автомобили, тягачи, спецтехника</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input v-model="filters.search" @input="debouncedFetch" type="text" class="input-field pl-10 w-64" placeholder="Поиск по названию..." />
        </div>
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
        <div class="card p-5 sticky top-20 space-y-4 max-h-[calc(100vh-6rem)] overflow-y-auto">
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
            <SearchableSelect v-model="filters.brand" :options="brandOptions"
                              placeholder="Все марки" search-placeholder="Введите марку..." @update:model-value="onBrandChange" />
          </div>

          <div>
            <label class="label">Модель</label>
            <SearchableSelect v-model="filters.model" :options="modelOptions"
                              placeholder="Все модели" search-placeholder="Введите модель..." @update:model-value="fetchVehicles" />
          </div>

          <div>
            <label class="label">От кого предложения</label>
            <div class="space-y-1.5">
              <label class="flex items-center gap-2 text-sm text-gray-700">
                <input v-model="supplierTypes" value="individual" type="checkbox" @change="fetchVehicles"
                       class="rounded border-gray-300 text-primary-500 focus:ring-primary-500" /> Физическое лицо
              </label>
              <label class="flex items-center gap-2 text-sm text-gray-700">
                <input v-model="supplierTypes" value="ie" type="checkbox" @change="fetchVehicles"
                       class="rounded border-gray-300 text-primary-500 focus:ring-primary-500" /> ИП
              </label>
              <label class="flex items-center gap-2 text-sm text-gray-700">
                <input v-model="supplierTypes" value="company" type="checkbox" @change="fetchVehicles"
                       class="rounded border-gray-300 text-primary-500 focus:ring-primary-500" /> Юридическое лицо
              </label>
            </div>
          </div>

          <div>
            <label class="label">Состояние</label>
            <select v-model="filters.condition" @change="fetchVehicles" class="input-field">
              <option value="">Любой</option>
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
            <label class="label">Цвет кузова</label>
            <SearchableSelect v-model="filters.colour" :options="colourOptions"
                              placeholder="Все цвета" search-placeholder="Введите цвет..." @update:model-value="fetchVehicles" />
          </div>

          <div>
            <label class="label">Область</label>
            <SearchableSelect v-model="filters.region_id" :options="regionOptions"
                              placeholder="Все области" @update:model-value="onRegionChange" />
          </div>

          <div>
            <label class="label">Город</label>
            <SearchableSelect v-model="filters.city_id" :options="cityOptions"
                              placeholder="Все города" @update:model-value="fetchVehicles" />
          </div>

          <div class="flex items-center gap-2">
            <input v-model="filters.in_stock" @change="fetchVehicles" type="checkbox" id="in_stock"
                   class="rounded border-gray-300 text-primary-500 focus:ring-primary-500" />
            <label for="in_stock" class="text-sm text-gray-700">В наличии</label>
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
            <label class="label">Объём двигателя, л</label>
            <input v-model.number="filters.engine_capacity_min" @input="debouncedFetch" type="number" step="0.1"
                   class="input-field" placeholder="От" />
          </div>

          <div>
            <label class="label">Мощность, л.с.</label>
            <input v-model.number="filters.hp_min" @input="debouncedFetch" type="number"
                   class="input-field" placeholder="От" />
          </div>

          <div>
            <label class="label">Трансмиссия</label>
            <select v-model="filters.transmission" @change="fetchVehicles" class="input-field">
              <option value="">Все</option>
              <option value="Механическая">Механическая</option>
              <option value="Автоматическая">Автоматическая</option>
              <option value="Роботизированная">Роботизированная</option>
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

        <div v-if="vehicles.length >= pageLimit" class="text-center mt-6">
          <button @click="loadMore" class="btn-secondary">Загрузить ещё</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { vehiclesApi } from '@/api/vehicles'
import { referencesApi } from '@/api/references'
import { formatPrice, formatMileage } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import SearchableSelect from '@/components/common/SearchableSelect.vue'

const vehicles = ref([])
const loading = ref(true)
const pageLimit = 20
let skip = 0
let debounceTimer = null

const brands = ref([])
const colours = ref([])
const regions = ref([])
const supplierTypes = ref([])

const vehicleTypes = ['Грузовой транспорт', 'Тягач', 'Самосвал', 'Фургон', 'Прицеп', 'Полуприцеп', 'Спецтехника', 'Коммерческий транспорт']

const filters = ref({
  search: '', brand: null, model: null, vehicle_type: '', condition: '',
  price_min: null, price_max: null, year_min: null, year_max: null,
  mileage_min: null, mileage_max: null, fuel_type: '', drive_type: '',
  colour: null, region_id: null, city_id: null, in_stock: false,
  sort_by: 'newest', transmission: '',
  engine_capacity_min: null, hp_min: null,
})

const brandOptions = computed(() =>
  brands.value.map(b => ({ value: b.name, label: b.name }))
)

const modelOptions = computed(() => {
  const selected = brands.value.find(b => b.name === filters.value.brand)
  if (!selected) {
    const all = brands.value.flatMap(b => b.models.map(m => ({ value: m.name, label: m.name })))
    const unique = [...new Map(all.map(i => [i.value, i])).values()]
    return unique.sort((a, b) => a.label.localeCompare(b.label))
  }
  return selected.models.map(m => ({ value: m.name, label: m.name }))
})

const colourOptions = computed(() =>
  colours.value.map(c => ({ value: c.name, label: c.name }))
)

const regionOptions = computed(() =>
  regions.value.map(r => ({ value: r.id, label: r.name }))
)

const cityOptions = computed(() => {
  const sel = regions.value.find(r => r.id === filters.value.region_id)
  if (!sel) {
    return regions.value.flatMap(r => r.cities.map(c => ({ value: c.id, label: c.name })))
  }
  return sel.cities.map(c => ({ value: c.id, label: c.name }))
})

onMounted(async () => {
  const [bRes, cRes, rRes] = await Promise.all([
    referencesApi.getBrands(),
    referencesApi.getColours(),
    referencesApi.getRegions(),
  ])
  brands.value = bRes.data
  colours.value = cRes.data
  regions.value = rRes.data
  fetchVehicles()
})

function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchVehicles, 400)
}

function onBrandChange() {
  filters.value.model = null
  fetchVehicles()
}

function onRegionChange() {
  filters.value.city_id = null
  fetchVehicles()
}

async function fetchVehicles() {
  loading.value = true
  skip = 0
  try {
    const params = { skip: 0, limit: pageLimit }
    for (const [k, v] of Object.entries(filters.value)) {
      if (v !== '' && v !== null && v !== false) params[k] = v
    }
    if (supplierTypes.value.length) params.supplier_type = supplierTypes.value.join(',')
    const { data } = await vehiclesApi.list(params)
    vehicles.value = data
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  skip += pageLimit
  const params = { skip, limit: pageLimit }
  for (const [k, v] of Object.entries(filters.value)) {
    if (v !== '' && v !== null && v !== false) params[k] = v
  }
  if (supplierTypes.value.length) params.supplier_type = supplierTypes.value.join(',')
  const { data } = await vehiclesApi.list(params)
  vehicles.value.push(...data)
}

function resetFilters() {
  filters.value = {
    search: '', brand: null, model: null, vehicle_type: '', condition: '',
    price_min: null, price_max: null, year_min: null, year_max: null,
    mileage_min: null, mileage_max: null, fuel_type: '', drive_type: '',
    colour: null, region_id: null, city_id: null, in_stock: false,
    sort_by: 'newest', transmission: '',
    engine_capacity_min: null, hp_min: null,
  }
  supplierTypes.value = []
  fetchVehicles()
}
</script>
