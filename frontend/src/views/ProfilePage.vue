<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 py-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Мой профиль</h1>

    <LoadingSpinner v-if="!auth.user" />
    <template v-else>
      <div class="card p-6 mb-6">
        <div class="flex items-start gap-6">
          <!-- Avatar -->
          <div class="relative group">
            <div class="w-20 h-20 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-2xl font-bold overflow-hidden">
              <img v-if="auth.user.avatar_url" :src="auth.user.avatar_url" class="w-full h-full object-cover" />
              <span v-else>{{ auth.userName?.charAt(0)?.toUpperCase() }}</span>
            </div>
            <label class="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer">
              <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
              <input type="file" accept="image/*" class="hidden" @change="uploadAvatar" />
            </label>
          </div>

          <div class="flex-1">
            <h2 class="text-xl font-bold text-gray-900">{{ auth.userName }}</h2>
            <div class="flex items-center gap-3 mt-1">
              <span class="badge badge-active">{{ roleLabels[auth.user.role] }}</span>
              <span class="text-xs text-gray-500">{{ userTypeLabels[auth.user.user_type] }}</span>
            </div>
            <StarRating v-if="auth.user.rating" :rating="auth.user.rating" class="mt-2" />
            <span v-if="auth.user.reviews_count" class="text-xs text-gray-500 ml-1">
              {{ auth.user.reviews_count }} отзывов
            </span>
            <p class="text-xs text-gray-400 mt-2">{{ getRegistrationDate(auth.user.created_at) }}</p>
          </div>
        </div>
      </div>

      <!-- Registration data (read-only) -->
      <div class="card p-6 mb-6">
        <h3 class="text-sm font-semibold text-gray-800 mb-3">Регистрационные данные</h3>

        <div v-if="auth.user.user_type === 'individual'" class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <p class="text-gray-500">Адрес прописки</p>
            <p class="text-gray-900">{{ auth.user.individual?.registration_address || '—' }}</p>
          </div>
        </div>

        <div v-else-if="auth.user.user_type === 'ie'" class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <p class="text-gray-500">Почтовый адрес</p>
            <p class="text-gray-900">{{ auth.user.entrepreneur?.postal_address || '—' }}</p>
          </div>
          <div>
            <p class="text-gray-500">Юридический адрес</p>
            <p class="text-gray-900">{{ auth.user.entrepreneur?.legal_address || '—' }}</p>
          </div>
          <div>
            <p class="text-gray-500">УНП</p>
            <p class="text-gray-900">{{ auth.user.entrepreneur?.unp || '—' }}</p>
          </div>
        </div>

        <div v-else-if="auth.user.user_type === 'company'" class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <p class="text-gray-500">Название</p>
            <p class="text-gray-900">
              {{ auth.user.company?.legal_form || '' }}
              <span v-if="auth.user.company?.company_name">
                {{ auth.user.company?.legal_form ? ' ' : '' }}«{{ auth.user.company?.company_name }}»
              </span>
              <span v-else>—</span>
            </p>
          </div>
          <div>
            <p class="text-gray-500">ФИО директора</p>
            <p class="text-gray-900">{{ auth.user.company?.director_name || '—' }}</p>
          </div>
          <div>
            <p class="text-gray-500">УНП</p>
            <p class="text-gray-900">{{ auth.user.company?.unp || '—' }}</p>
          </div>
          <div>
            <p class="text-gray-500">ОКПО</p>
            <p class="text-gray-900">{{ auth.user.company?.okpo || '—' }}</p>
          </div>
          <div>
            <p class="text-gray-500">Юридический адрес</p>
            <p class="text-gray-900">{{ auth.user.company?.legal_address || '—' }}</p>
          </div>
          <div>
            <p class="text-gray-500">Почтовый адрес</p>
            <p class="text-gray-900">{{ auth.user.company?.postal_address || '—' }}</p>
          </div>
          
        </div>
      </div>

      <!-- Description edit -->
      <div class="card p-6 mb-6">
        <h3 class="text-sm font-semibold text-gray-800 mb-3">Описание</h3>
        <textarea v-model="description" class="input-field" rows="3" placeholder="Расскажите о себе или компании..."></textarea>
        <button @click="updateProfile" class="btn-primary btn-sm mt-3">Сохранить</button>
      </div>

      <!-- Contacts -->
      <div class="card p-6 mb-6">
        <h3 class="text-sm font-semibold text-gray-800 mb-3">Контакты</h3>
        <div class="space-y-2">
          <div v-for="c in auth.user.contacts" :key="c.id" class="flex items-center justify-between py-2 border-b border-surface-100 last:border-0">
            <div class="flex items-center gap-2">
              <span class="badge" :class="c.type === 'phone' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'">
                {{ c.type === 'phone' ? 'Телефон' : 'Email' }}
              </span>
              <span class="text-sm">{{ c.value }}</span>
              <span v-if="c.is_primary" class="text-[10px] text-green-600 font-medium">основной</span>
            </div>
            <button @click="deleteContact(c.id)" class="text-red-500 hover:text-red-700 text-xs">Удалить</button>
          </div>
        </div>
        <div class="flex gap-2 mt-3">
          <select v-model="newContact.type" class="input-field w-32">
            <option value="phone">Телефон</option>
            <option value="email">Email</option>
          </select>
          <input v-model="newContact.value" class="input-field flex-1" placeholder="Номер или email" />
          <button @click="addContact" class="btn-secondary btn-sm">Добавить</button>
        </div>
      </div>

      <!-- Bank accounts -->
      <div class="card p-6 mb-6">
        <h3 class="text-sm font-semibold text-gray-800 mb-3">Банковские счета</h3>
        <div class="space-y-4">
          <div v-for="ba in auth.user.bank_accounts" :key="ba.id" class="p-3 rounded-lg border border-surface-200 text-sm">
            <div class="flex justify-between items-start">
              <div class="space-y-1">
                <p><span class="text-gray-500">IBAN:</span> {{ ba.iban }}</p>
                <p><span class="text-gray-500">Банк:</span> {{ ba.bank_name }}</p>
                <p v-if="ba.bank_address"><span class="text-gray-500">Адрес:</span> {{ ba.bank_address }}</p>
                <p v-if="ba.swift"><span class="text-gray-500">SWIFT:</span> {{ ba.swift }}</p>
                <p v-if="ba.bic"><span class="text-gray-500">BIC:</span> {{ ba.bic }}</p>
              </div>
              <button @click="deleteBankAccount(ba.id)" class="text-red-500 hover:text-red-700 text-xs">Удалить</button>
            </div>
          </div>
        </div>
        <details class="mt-4">
          <summary class="text-sm text-primary-500 cursor-pointer font-medium">Добавить счёт</summary>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
            <input
              :value="newBankAccount.iban"
              class="input-field"
              placeholder="IBAN (28 символов)"
              autocomplete="off"
              spellcheck="false"
              @input="onBankCodeInput('iban', $event)"
            />
            <input
              v-model="newBankAccount.bank_name"
              class="input-field"
              placeholder='Название банка - например OAO "Белгазпромбанк"'
            />
            <input v-model="newBankAccount.bank_address" class="input-field" placeholder="Адрес банка" />
            <input
              :value="newBankAccount.swift"
              class="input-field"
              placeholder="SWIFT"
              autocomplete="off"
              spellcheck="false"
              @input="onBankCodeInput('swift', $event)"
            />
            <input
              :value="newBankAccount.bic"
              class="input-field"
              placeholder="BIC"
              autocomplete="off"
              spellcheck="false"
              @input="onBankCodeInput('bic', $event)"
            />
            <button @click="addBankAccount" class="btn-primary btn-sm">Добавить счёт</button>
          </div>
        </details>
      </div>

      <!-- Lease Terms (for lessors) -->
      <div v-if="auth.userRole === 'lease_manager'" class="card p-6 mb-6">
        <h3 class="text-sm font-semibold text-gray-800 mb-3">Условия лизинга (калькулятор)</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="label">Мин. срок (мес.)</label>
            <input v-model.number="leaseTerms.min_term_months" type="number" class="input-field" />
          </div>
          <div>
            <label class="label">Макс. срок (мес.)</label>
            <input v-model.number="leaseTerms.max_term_months" type="number" class="input-field" />
          </div>
          <div>
            <label class="label">Мин. аванс (%)</label>
            <input v-model.number="leaseTerms.min_prepayment_pct" type="number" class="input-field" />
          </div>
          <div>
            <label class="label">Макс. аванс (%)</label>
            <input v-model.number="leaseTerms.max_prepayment_pct" type="number" class="input-field" />
          </div>
          <div>
            <label class="label">Мин. стоимость техники (BYN)</label>
            <input v-model.number="leaseTerms.min_asset_price" type="number" class="input-field" />
          </div>
          <div>
            <label class="label">Макс. стоимость техники (BYN)</label>
            <input v-model.number="leaseTerms.max_asset_price" type="number" class="input-field" />
          </div>
          <div>
            <label class="label">Процентная ставка (%)</label>
            <input v-model.number="leaseTerms.interest_rate" type="number" step="0.1" class="input-field" />
          </div>
        </div>
        <button @click="saveLeaseTerms" class="btn-primary btn-sm mt-4">Сохранить условия</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { usersApi } from '@/api/users'
import { roleLabels, userTypeLabels, getRegistrationDate } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StarRating from '@/components/common/StarRating.vue'

const auth = useAuthStore()
const notifStore = useNotificationsStore()

const description = ref('')
const newContact = ref({ type: 'phone', value: '' })
const newBankAccount = ref({ iban: '', bank_name: '', bank_address: '', swift: '', bic: '' })
const leaseTerms = ref({
  min_term_months: 6, max_term_months: 84,
  min_prepayment_pct: 10, max_prepayment_pct: 49,
  min_asset_price: 5000, max_asset_price: 500000,
  interest_rate: 12,
})

onMounted(() => {
  if (auth.user) {
    description.value = auth.user.description || ''
    if (auth.user.lease_terms) {
      leaseTerms.value = { ...auth.user.lease_terms }
    }
  }
})

async function updateProfile() {
  await usersApi.updateMe({ description: description.value })
  await auth.fetchUser()
  notifStore.showToast('Профиль обновлён', 'success')
}

async function uploadAvatar(e) {
  const file = e.target.files[0]
  if (!file) return
  await usersApi.uploadAvatar(file)
  await auth.fetchUser()
  notifStore.showToast('Аватарка обновлена', 'success')
}

async function addContact() {
  if (!newContact.value.value) return
  await usersApi.addContact(newContact.value)
  await auth.fetchUser()
  newContact.value.value = ''
}

async function deleteContact(id) {
  await usersApi.deleteContact(id)
  await auth.fetchUser()
}

const bankLatinDigitsRe = /^[a-zA-Z0-9]+$/

function sanitizeBankLatinDigits(raw) {
  return String(raw ?? '').replace(/[^a-zA-Z0-9]/g, '')
}

function onBankCodeInput(field, e) {
  newBankAccount.value[field] = sanitizeBankLatinDigits(e.target.value)
}

async function addBankAccount() {
  const { iban, swift, bic } = newBankAccount.value
  for (const [label, val] of [
    ['IBAN', iban],
    ['SWIFT', swift],
    ['BIC', bic],
  ]) {
    if (val && !bankLatinDigitsRe.test(val)) {
      notifStore.showToast(
        `${label}, SWIFT, BIC: только латинские буквы и цифры, без пробелов`,
        'error',
      )
      return
    }
  }
  await usersApi.addBankAccount(newBankAccount.value)
  await auth.fetchUser()
  newBankAccount.value = { iban: '', bank_name: '', bank_address: '', swift: '', bic: '' }
}

async function deleteBankAccount(id) {
  await usersApi.deleteBankAccount(id)
  await auth.fetchUser()
}

async function saveLeaseTerms() {
  await usersApi.upsertLeaseTerms(leaseTerms.value)
  await auth.fetchUser()
  notifStore.showToast('Условия лизинга сохранены', 'success')
}
</script>
