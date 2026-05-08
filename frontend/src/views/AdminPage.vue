<template>
  <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Админ-панель</h1>

    <div class="card p-4 mb-6 max-w-md">
      <h2 class="text-sm font-semibold text-gray-800 mb-3">Ставка НДС</h2>
      <p class="text-xs text-gray-500 mb-3">Используется при автоматической генерации графика платежей по договору. На сайте для посетителей не отображается.</p>
      <div class="flex flex-wrap items-end gap-3">
        <div>
          <label class="label text-xs">Процент</label>
          <input
            v-model.number="vatPercent"
            type="number"
            min="0"
            max="100"
            step="0.01"
            class="input-field w-32"
            :disabled="settingsLoading"
          />
        </div>
        <button type="button" class="btn-primary" :disabled="settingsLoading || settingsSaving" @click="saveVat">
          {{ settingsSaving ? 'Сохранение...' : 'Сохранить' }}
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-6">
      <input v-model="search" @input="debouncedFetch" type="text" class="input-field w-64" placeholder="Поиск пользователя..." />
      <select v-model="roleFilter" @change="fetchUsers" class="input-field w-auto">
        <option value="">Все роли</option>
        <option value="client">Лизингополучатель</option>
        <option value="lease_manager">Лизинговая компания</option>
        <option value="supplier">Поставщик</option>
        <option value="admin">Администратор</option>
      </select>
      <select v-model="typeFilter" @change="fetchUsers" class="input-field w-auto">
        <option value="">Все типы</option>
        <option value="individual">Физ. лицо</option>
        <option value="ie">ИП</option>
        <option value="company">Юр. лицо</option>
      </select>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-50 border-b border-surface-200 text-left text-xs text-gray-500 uppercase tracking-wide">
            <th class="px-4 py-3">ID</th>
            <th class="px-4 py-3">Логин</th>
            <th class="px-4 py-3">Имя / Компания</th>
            <th class="px-4 py-3">Роль</th>
            <th class="px-4 py-3">Тип</th>
            <th class="px-4 py-3">Статус</th>
            <th class="px-4 py-3">Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-b border-surface-100 hover:bg-surface-50">
            <td class="px-4 py-3 text-gray-400">{{ u.id }}</td>
            <td class="px-4 py-3 font-medium">{{ u.login }}</td>
            <td class="px-4 py-3">{{ getUserName(u) }}</td>
            <td class="px-4 py-3">
              <select :value="u.role" @change="changeRole(u.id, $event.target.value)" class="input-field py-1 px-2 text-xs w-auto">
                <option value="client">Клиент</option>
                <option value="lease_manager">Менеджер</option>
                <option value="supplier">Поставщик</option>
                <option value="admin">Админ</option>
              </select>
            </td>
            <td class="px-4 py-3 text-xs text-gray-500">{{ userTypeLabels[u.user_type] }}</td>
            <td class="px-4 py-3">
              <span :class="['badge', u.is_active !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
                {{ u.is_active !== false ? 'Активен' : 'Заблокирован' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <button @click="toggleActive(u.id)" :class="u.is_active !== false ? 'btn-danger btn-sm' : 'btn-success btn-sm'">
                {{ u.is_active !== false ? 'Блокировать' : 'Разблокировать' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Страница «О компании» (контент для /about) -->
    <div class="card p-6 mt-8">
      <h2 class="text-lg font-semibold text-gray-900 mb-1">Страница «О компании»</h2>
      <p class="text-xs text-gray-500 mb-6">
        Отображается всем посетителям по адресу
        <router-link to="/about" class="text-primary-500 hover:underline">/about</router-link>
        . Изображения загружаются в отдельное хранилище.
      </p>

      <LoadingSpinner v-if="aboutLoading" />
      <div v-else class="space-y-8">
        <div class="border border-surface-200 rounded-lg p-4 space-y-4">
          <h3 class="text-sm font-semibold text-gray-800">Шапка страницы</h3>
          <div>
            <label class="label text-xs">Заголовок</label>
            <input v-model="aboutForm.hero.title" type="text" class="input-field" />
          </div>
          <div>
            <label class="label text-xs">Подзаголовок</label>
            <textarea v-model="aboutForm.hero.subtitle" rows="4" class="input-field" />
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button type="button" class="btn-secondary btn-sm" :disabled="aboutUploading" @click="pickHeroAboutImage">
              {{ aboutUploading && pendingAboutUpload === 'hero' ? 'Загрузка…' : 'Загрузить изображение' }}
            </button>
            <button
              v-if="aboutForm.hero.image_url"
              type="button"
              class="text-xs text-red-600 hover:underline"
              @click="aboutForm.hero.image_url = null"
            >
              Убрать фото
            </button>
          </div>
          <div v-if="aboutForm.hero.image_url" class="rounded-lg overflow-hidden border border-surface-200 max-w-md">
            <img :src="aboutForm.hero.image_url" alt="" class="w-full max-h-48 object-cover" />
          </div>
        </div>

        <div class="space-y-4">
          <div class="flex flex-wrap justify-between items-center gap-2">
            <h3 class="text-sm font-semibold text-gray-800">Блоки контента</h3>
            <button
              type="button"
              class="btn-secondary btn-sm"
              :disabled="aboutForm.blocks.length >= 10"
              @click="addAboutBlock"
            >
              Добавить блок
            </button>
          </div>
          <p v-if="aboutForm.blocks.length === 0" class="text-sm text-gray-500">Блоков пока нет — добавьте хотя бы один.</p>
          <div
            v-for="(block, i) in aboutForm.blocks"
            :key="i"
            class="border border-surface-200 rounded-lg p-4 space-y-3"
          >
            <div class="flex justify-between items-center gap-2">
              <span class="text-xs font-medium text-gray-500">Блок {{ i + 1 }}</span>
              <button type="button" class="text-xs text-red-600 hover:underline" @click="removeAboutBlock(i)">
                Удалить блок
              </button>
            </div>
            <div>
              <label class="label text-xs">Заголовок блока</label>
              <input v-model="block.title" type="text" class="input-field" />
            </div>
            <div>
              <label class="label text-xs">Текст</label>
              <textarea v-model="block.body" rows="5" class="input-field" />
            </div>
            <div class="flex flex-wrap items-center gap-3">
              <button
                type="button"
                class="btn-secondary btn-sm"
                :disabled="aboutUploading"
                @click="pickBlockAboutImage(i)"
              >
                {{ aboutUploading && pendingAboutUpload === i ? 'Загрузка…' : 'Загрузить изображение' }}
              </button>
              <button
                v-if="block.image_url"
                type="button"
                class="text-xs text-red-600 hover:underline"
                @click="block.image_url = null"
              >
                Убрать фото
              </button>
            </div>
            <div v-if="block.image_url" class="rounded-lg overflow-hidden border border-surface-200 max-w-md">
              <img :src="block.image_url" alt="" class="w-full max-h-40 object-cover" />
            </div>
          </div>
        </div>

        <button type="button" class="btn-primary" :disabled="aboutSaving" @click="saveAboutPage">
          {{ aboutSaving ? 'Сохранение…' : 'Сохранить страницу' }}
        </button>
      </div>

      <input
        ref="aboutFileInputRef"
        type="file"
        accept="image/*"
        class="hidden"
        @change="onAboutFileSelected"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { usersApi } from '@/api/users'
import { settingsApi } from '@/api/settings'
import { siteApi } from '@/api/site'
import { useNotificationsStore } from '@/stores/notifications'
import { userTypeLabels } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const notifStore = useNotificationsStore()
const users = ref([])
const loading = ref(true)
const search = ref('')
const roleFilter = ref('')
const typeFilter = ref('')
const vatPercent = ref(20)
const settingsLoading = ref(true)
const settingsSaving = ref(false)

const aboutLoading = ref(true)
const aboutSaving = ref(false)
const aboutUploading = ref(false)
const pendingAboutUpload = ref(null)
const aboutFileInputRef = ref(null)
const aboutForm = ref({
  hero: { title: '', subtitle: '', image_url: null },
  blocks: [],
})

let debounceTimer = null

function emptyAboutForm() {
  return {
    hero: { title: '', subtitle: '', image_url: null },
    blocks: [],
  }
}

async function loadAboutAdmin() {
  aboutLoading.value = true
  try {
    const { data } = await siteApi.getAboutAdmin()
    aboutForm.value = {
      hero: {
        title: data.hero?.title ?? '',
        subtitle: data.hero?.subtitle ?? '',
        image_url: data.hero?.image_url ?? null,
      },
      blocks: (data.blocks ?? []).map((b) => ({
        title: b.title ?? '',
        body: b.body ?? '',
        image_url: b.image_url ?? null,
      })),
    }
  } catch {
    notifStore.showToast('Не удалось загрузить страницу «О компании»', 'error')
    aboutForm.value = emptyAboutForm()
  } finally {
    aboutLoading.value = false
  }
}

function normalizeAboutPayload() {
  const hero = { ...aboutForm.value.hero }
  if (!hero.image_url || !String(hero.image_url).trim()) hero.image_url = null
  const blocks = aboutForm.value.blocks.map((b) => ({
    title: b.title ?? '',
    body: b.body ?? '',
    image_url: b.image_url?.trim() ? b.image_url.trim() : null,
  }))
  return { hero, blocks }
}

async function saveAboutPage() {
  aboutSaving.value = true
  try {
    await siteApi.patchAbout(normalizeAboutPayload())
    notifStore.showToast('Страница «О компании» сохранена', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка сохранения', 'error')
  } finally {
    aboutSaving.value = false
  }
}

function addAboutBlock() {
  if (aboutForm.value.blocks.length >= 10) return
  aboutForm.value.blocks.push({ title: '', body: '', image_url: null })
}

function removeAboutBlock(i) {
  aboutForm.value.blocks.splice(i, 1)
}

function pickHeroAboutImage() {
  pendingAboutUpload.value = 'hero'
  aboutFileInputRef.value?.click()
}

function pickBlockAboutImage(i) {
  pendingAboutUpload.value = i
  aboutFileInputRef.value?.click()
}

async function onAboutFileSelected(ev) {
  const input = ev.target
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  aboutUploading.value = true
  try {
    const { data } = await siteApi.uploadAboutImage(file)
    const url = data.url
    if (pendingAboutUpload.value === 'hero') {
      aboutForm.value.hero.image_url = url
    } else if (typeof pendingAboutUpload.value === 'number') {
      const idx = pendingAboutUpload.value
      if (aboutForm.value.blocks[idx]) {
        aboutForm.value.blocks[idx].image_url = url
      }
    }
    notifStore.showToast('Изображение загружено', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка загрузки файла', 'error')
  } finally {
    aboutUploading.value = false
    pendingAboutUpload.value = null
  }
}

onMounted(async () => {
  settingsLoading.value = true
  try {
    const { data } = await settingsApi.getAdmin()
    vatPercent.value = data.vat_rate_percent
  } catch {
    notifStore.showToast('Не удалось загрузить настройки', 'error')
  } finally {
    settingsLoading.value = false
  }
  fetchUsers()
  loadAboutAdmin()
})

async function saveVat() {
  settingsSaving.value = true
  try {
    await settingsApi.patchAdmin({ vat_rate_percent: Number(vatPercent.value) })
    notifStore.showToast('Ставка НДС сохранена', 'success')
  } catch (e) {
    notifStore.showToast(e.response?.data?.detail || 'Ошибка сохранения', 'error')
  } finally {
    settingsSaving.value = false
  }
}

function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchUsers, 400)
}

async function fetchUsers() {
  loading.value = true
  try {
    const params = { limit: 100 }
    if (search.value) params.search = search.value
    if (roleFilter.value) params.role = roleFilter.value
    if (typeFilter.value) params.user_type = typeFilter.value
    const { data } = await usersApi.listUsers(params)
    users.value = data
  } finally {
    loading.value = false
  }
}

function getUserName(u) {
  if (u.individual) return u.individual.full_name
  if (u.entrepreneur) return u.entrepreneur.full_name
  if (u.company) return u.company.company_name
  return '—'
}

async function toggleActive(id) {
  await usersApi.toggleActive(id)
  fetchUsers()
  notifStore.showToast('Статус обновлён', 'success')
}

async function changeRole(id, role) {
  await usersApi.changeRole(id, role)
  fetchUsers()
  notifStore.showToast('Роль обновлена', 'success')
}
</script>
