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
          <input v-model="form.brand" class="input-field" required placeholder="MAN" />
        </div>
        <div>
          <label class="label">Модель</label>
          <input v-model="form.model" class="input-field" required placeholder="TGS 33.430" />
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
          <input v-model.number="form.count" type="number" class="input-field" min="0" />
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
          <input v-model="form.colour" class="input-field" />
        </div>
        <div>
          <label class="label">Местоположение</label>
          <input v-model="form.location" class="input-field" placeholder="г. Минск" />
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
          <input v-model="form.transmission" class="input-field" placeholder="6МКПП" />
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
        <input v-model="form.is_visible" type="checkbox" id="visible" class="rounded border-gray-300 text-primary-500 focus:ring-primary-500" />
        <label for="visible" class="text-sm text-gray-700">Объявление активно (видно всем)</label>
      </div>

      <!-- Images upload (for edit mode) -->
      <div v-if="isEdit" class="border-t border-surface-200 pt-4">
        <label class="label">Фотографии</label>
        <div class="flex gap-2 flex-wrap mb-3">
          <div v-for="img in currentImages" :key="img.id" class="relative w-24 h-24 rounded-lg overflow-hidden border border-surface-200">
            <img :src="img.image_url" class="w-full h-full object-cover" />
            <button @click="removeImage(img.id)" class="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center">&times;</button>
          </div>
        </div>
        <input type="file" accept="image/*" @change="uploadImage" class="text-sm" />
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { vehiclesApi } from '@/api/vehicles'
import { useNotificationsStore } from '@/stores/notifications'

const route = useRoute()
const router = useRouter()
const notifStore = useNotificationsStore()

const isEdit = computed(() => !!route.params.id)
const submitting = ref(false)
const currentImages = ref([])

const form = ref({
  name: '', brand: '', model: '', vehicle_type: '', condition: 'new',
  price: null, count: 1, product_code: '', release_year: null,
  mileage: null, vin: '', colour: '', location: '', fuel_type: '',
  engine_capacity: null, hp: null, transmission: '', drive_type: '',
  extras: '', description: '', is_visible: true,
})

onMounted(async () => {
  if (isEdit.value) {
    const { data } = await vehiclesApi.get(route.params.id)
    Object.keys(form.value).forEach(k => { if (data[k] !== undefined) form.value[k] = data[k] })
    currentImages.value = data.images || []
  }
})

async function handleSubmit() {
  submitting.value = true
  try {
    if (isEdit.value) {
      await vehiclesApi.update(route.params.id, form.value)
      notifStore.showToast('Объявление обновлено', 'success')
    } else {
      const { data } = await vehiclesApi.create(form.value)
      notifStore.showToast('Объявление создано', 'success')
      router.push(`/my-vehicles/${data.id}/edit`)
      return
    }
    router.push('/my-vehicles')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка', 'error')
  } finally {
    submitting.value = false
  }
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
