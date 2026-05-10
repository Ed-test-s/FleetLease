<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 py-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ isEdit ? 'Редактировать объявление' : 'Новое объявление' }}</h1>

    <form @submit.prevent="handleSubmit" class="card p-6 space-y-5">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="sm:col-span-2">
          <label class="label">Наименование</label>
          <input v-model="form.name" class="input-field" required placeholder="MAN TGS 33.430 6x4 BB-WW" />
        </div>

        <div>
          <label class="label">Марка</label>
          <SearchableSelect v-model="form.brand" :options="brandOptions" placeholder="Выберите марку"
                            :allow-empty="false" @update:model-value="onBrandChange" />
          <div v-if="!brandExists && form.brand" class="mt-1">
            <button type="button" @click="addNewBrand" class="text-xs text-primary-500 hover:underline">
              + Добавить марку «{{ newBrandInput }}» в базу
            </button>
          </div>
        </div>

        <div>
          <label class="label">Модель</label>
          <SearchableSelect v-model="form.model" :options="modelOptions" placeholder="Выберите модель"
                            :allow-empty="false" />
          <div class="mt-1 flex gap-2 items-center">
            <input v-model="newModelInput" class="input-field py-1 text-xs flex-1" placeholder="Новая модель" />
            <button type="button" @click="addNewModel" class="btn-secondary btn-sm text-xs" :disabled="!newModelInput">+</button>
          </div>
        </div>

        <div>
          <label class="label">Раздел / Тип ТС</label>
          <select v-model="form.vehicle_type" class="input-field" required>
            <option value="">Выберите</option>
            <option>Грузовой транспорт</option>
            <option>Тягач</option>
            <option>Самосвал</option>
            <option>Фургон</option>
            <option>Прицеп</option>
            <option>Полуприцеп</option>
            <option>Спецтехника</option>
            <option>Коммерческий транспорт</option>
          </select>
        </div>
        <div>
          <label class="label">Состояние</label>
          <select v-model="form.condition" class="input-field" required>
            <option value="new">Новый</option>
            <option value="used">С пробегом</option>
          </select>
        </div>
        <div>
          <label class="label">Цена (BYN)</label>
          <input v-model.number="form.price" type="number" class="input-field" step="0.01" required />
        </div>
        <div>
          <label class="label">Количество</label>
          <input v-model.number="form.count" type="number" class="input-field" min="0" step="1" />
        </div>
        <div>
          <label class="label">Код предложения</label>
          <input v-model="form.product_code" class="input-field" />
        </div>
        <div>
          <label class="label">Год выпуска</label>
          <input v-model.number="form.release_year" type="number" class="input-field" />
        </div>
        <div>
          <label class="label">Пробег, км</label>
          <input v-model.number="form.mileage" type="number" class="input-field" />
        </div>
        <div>
          <label class="label">VIN (17 символов)</label>
          <input v-model="form.vin" class="input-field" maxlength="17" />
        </div>

        <div>
          <label class="label">Цвет кузова</label>
          <SearchableSelect v-model="form.colour" :options="colourOptions" placeholder="Выберите цвет" />
        </div>

        <div>
          <label class="label">Область</label>
          <SearchableSelect v-model="form.region_id" :options="regionOptions" placeholder="Область" @update:model-value="onRegionChange" />
        </div>
        <div>
          <label class="label">Город</label>
          <SearchableSelect v-model="form.city_id" :options="cityOptions" placeholder="Город" />
        </div>

        <div>
          <label class="label">Тип двигателя</label>
          <select v-model="form.fuel_type" class="input-field">
            <option value="">—</option>
            <option>Дизельный</option>
            <option>Бензиновый</option>
            <option>Электро</option>
            <option>Гибрид</option>
          </select>
        </div>
        <div>
          <label class="label">Объём двигателя (л)</label>
          <input v-model.number="form.engine_capacity" type="number" step="0.1" class="input-field" />
        </div>
        <div>
          <label class="label">Мощность (л.с.)</label>
          <input v-model.number="form.hp" type="number" class="input-field" />
        </div>
        <div>
          <label class="label">Трансмиссия</label>
          <select v-model="form.transmission" class="input-field">
            <option value="">—</option>
            <option>Механическая</option>
            <option>Автоматическая</option>
            <option>Роботизированная</option>
          </select>
        </div>
        <div>
          <label class="label">Тип привода</label>
          <select v-model="form.drive_type" class="input-field">
            <option value="">—</option>
            <option>Задний</option>
            <option>Передний</option>
            <option>Постоянный полный</option>
            <option>Подключаемый полный</option>
          </select>
        </div>
      </div>

      <div>
        <label class="label">Комплектация</label>
        <textarea v-model="form.extras" class="input-field" rows="3"></textarea>
      </div>
      <div>
        <label class="label">Описание</label>
        <textarea v-model="form.description" class="input-field" rows="4"></textarea>
      </div>

      <div class="flex items-center gap-2">
        <input v-model="form.is_visible" :disabled="isOutOfStock" type="checkbox" id="visible" class="rounded border-gray-300 text-primary-500 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed" />
        <label for="visible" class="text-sm text-gray-700">Объявление активно (видно всем)</label>
      </div>
      <p v-if="isOutOfStock" class="text-xs text-gray-500">
        Укажите количество больше 0, чтобы включить объявление.
      </p>

      <div class="border-t border-surface-200 pt-4">
        <label class="label">Фотографии</label>
        <template v-if="isEdit">
          <div class="flex gap-2 flex-wrap mb-3">
            <div v-for="img in currentImages" :key="img.id" class="relative w-24 h-24 rounded-lg overflow-hidden border border-surface-200">
              <img :src="img.image_url" class="w-full h-full object-cover" />
              <button type="button" @click="removeImage(img.id)" class="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center">&times;</button>
            </div>
          </div>
          <input type="file" accept="image/*" @change="uploadImage" class="text-sm" />
        </template>
        <template v-else>
          <div class="flex gap-2 flex-wrap mb-3">
            <div v-for="(p, idx) in pendingPreviews" :key="idx" class="relative w-24 h-24 rounded-lg overflow-hidden border border-surface-200">
              <img :src="p" class="w-full h-full object-cover" alt="" />
              <button type="button" @click="removePending(idx)" class="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center">&times;</button>
            </div>
          </div>
          <input type="file" accept="image/*" multiple @change="onPickImages" class="text-sm" />
          <p class="text-xs text-gray-500 mt-1">Можно выбрать несколько файлов — они будут загружены сразу после создания объявления.</p>
        </template>
      </div>

      <div class="flex gap-3">
        <router-link to="/my-vehicles" class="btn-secondary flex-1">Отмена</router-link>
        <button type="submit" :disabled="submitting" class="btn-primary flex-1">
          {{ submitting ? 'Сохранение...' : (isEdit ? 'Сохранить' : 'Создать') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { vehiclesApi } from '@/api/vehicles'
import { referencesApi } from '@/api/references'
import { useNotificationsStore } from '@/stores/notifications'
import SearchableSelect from '@/components/common/SearchableSelect.vue'

const route = useRoute()
const router = useRouter()
const notifStore = useNotificationsStore()

const isEdit = computed(() => !!route.params.id)
const submitting = ref(false)
const currentImages = ref([])
const pendingFiles = ref([])
const pendingPreviews = ref([])

const brands = ref([])
const colours = ref([])
const regions = ref([])
const newModelInput = ref('')
const newBrandInput = ref('')

const form = ref({
  name: '', brand: null, model: null, vehicle_type: '', condition: 'new',
  price: null, count: 1, product_code: '', release_year: null,
  mileage: null, vin: '', colour: null, region_id: null, city_id: null,
  location: '', fuel_type: '', engine_capacity: null, hp: null,
  transmission: '', drive_type: '', extras: '', description: '', is_visible: true,
})
const isOutOfStock = computed(() => normalizeCount(form.value.count) <= 0)

const brandOptions = computed(() => brands.value.map(b => ({ value: b.name, label: b.name })))
const brandExists = computed(() => brands.value.some(b => b.name === form.value.brand))

const modelOptions = computed(() => {
  const selected = brands.value.find(b => b.name === form.value.brand)
  if (!selected) return []
  return selected.models.map(m => ({ value: m.name, label: m.name }))
})

const colourOptions = computed(() => colours.value.map(c => ({ value: c.name, label: c.name })))
const regionOptions = computed(() => regions.value.map(r => ({ value: r.id, label: r.name })))
const cityOptions = computed(() => {
  const sel = regions.value.find(r => r.id === form.value.region_id)
  if (!sel) return []
  return sel.cities.map(c => ({ value: c.id, label: c.name }))
})

function onBrandChange() { form.value.model = null }
function onRegionChange() { form.value.city_id = null }

function normalizeCount(value) {
  const num = Number(value)
  if (!Number.isFinite(num)) return 0
  return Math.max(0, Math.trunc(num))
}

watch(
  () => form.value.count,
  (val) => {
    const normalized = normalizeCount(val)
    if (val !== normalized) {
      form.value.count = normalized
      return
    }
    if (normalized <= 0 && form.value.is_visible) {
      form.value.is_visible = false
    }
  },
  { immediate: true }
)

async function addNewBrand() {
  if (!newBrandInput.value) return
  try {
    await referencesApi.createBrand(newBrandInput.value)
    const { data } = await referencesApi.getBrands()
    brands.value = data
    form.value.brand = newBrandInput.value
    newBrandInput.value = ''
    notifStore.showToast('Марка добавлена', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  }
}

async function addNewModel() {
  const brand = brands.value.find(b => b.name === form.value.brand)
  if (!brand || !newModelInput.value) return
  try {
    await referencesApi.createModel(brand.id, newModelInput.value)
    const { data } = await referencesApi.getBrands()
    brands.value = data
    form.value.model = newModelInput.value
    newModelInput.value = ''
    notifStore.showToast('Модель добавлена', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  }
}

onMounted(async () => {
  const [bRes, cRes, rRes] = await Promise.all([
    referencesApi.getBrands(),
    referencesApi.getColours(),
    referencesApi.getRegions(),
  ])
  brands.value = bRes.data
  colours.value = cRes.data
  regions.value = rRes.data

  if (isEdit.value) {
    const { data } = await vehiclesApi.get(route.params.id)
    const keys = Object.keys(form.value)
    keys.forEach(k => { if (data[k] !== undefined) form.value[k] = data[k] })
    currentImages.value = data.images || []
  }
})

async function handleSubmit() {
  submitting.value = true
  try {
    form.value.count = normalizeCount(form.value.count)
    if (form.value.count <= 0 && form.value.is_visible) {
      notifStore.showToast('Нельзя включить объявление при нулевом количестве техники', 'error')
      return
    }
    const payload = { ...form.value }
    if (isEdit.value) {
      await vehiclesApi.update(route.params.id, payload)
      notifStore.showToast('Объявление обновлено', 'success')
    } else {
      const { data } = await vehiclesApi.create(payload)
      for (const file of pendingFiles.value) {
        await vehiclesApi.uploadImage(data.id, file)
      }
      pendingPreviews.value.forEach((url) => URL.revokeObjectURL(url))
      pendingFiles.value = []
      pendingPreviews.value = []
      notifStore.showToast('Объявление создано', 'success')
      router.push('/my-vehicles')
      return
    }
    router.push('/my-vehicles')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  } finally {
    submitting.value = false
  }
}

function onPickImages(e) {
  const files = Array.from(e.target.files || [])
  for (const file of files) {
    pendingFiles.value.push(file)
    pendingPreviews.value.push(URL.createObjectURL(file))
  }
  e.target.value = ''
}

function removePending(idx) {
  URL.revokeObjectURL(pendingPreviews.value[idx])
  pendingFiles.value.splice(idx, 1)
  pendingPreviews.value.splice(idx, 1)
}

async function uploadImage(e) {
  const file = e.target.files[0]
  if (!file) return
  const { data } = await vehiclesApi.uploadImage(route.params.id, file)
  currentImages.value = data.images
  notifStore.showToast('Фото загружено', 'success')
}

async function removeImage(imageId) {
  await vehiclesApi.deleteImage(route.params.id, imageId)
  currentImages.value = currentImages.value.filter(i => i.id !== imageId)
}
</script>
