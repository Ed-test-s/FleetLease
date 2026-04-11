<template>
  <div class="min-h-[80vh] flex items-center justify-center px-4 py-12">
    <div class="card p-8 w-full max-w-2xl">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900">Регистрация</h1>
        <p class="text-sm text-gray-500 mt-2">Создайте аккаунт в системе FleetLease</p>
      </div>

      <form @submit.prevent="handleRegister" class="space-y-6">
        <!-- Step 1: Role & Type -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="label">Роль в системе</label>
            <select v-model="form.role" class="input-field" required>
              <option value="" disabled>Выберите роль</option>
              <option value="client">Лизингополучатель</option>
              <option value="lease_manager">Лизинговая компания</option>
              <option value="supplier">Поставщик</option>
            </select>
          </div>
          <div>
            <label class="label">Тип</label>
            <select v-model="form.user_type" class="input-field" required :disabled="form.role === 'lease_manager'">
              <option value="" disabled>Выберите тип</option>
              <option value="individual">Физическое лицо</option>
              <option value="ie">ИП</option>
              <option value="company">Юридическое лицо</option>
            </select>
          </div>
        </div>

        <!-- Step 2: Credentials -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="label">Логин</label>
            <input v-model="form.login" type="text" class="input-field" placeholder="Придумайте логин" required />
          </div>
          <div>
            <label class="label">Пароль</label>
            <input v-model="form.password" type="password" class="input-field" placeholder="Не менее 6 символов" required />
          </div>
        </div>

        <!-- Contacts -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="label">Номер телефона</label>
            <input v-model="phone" type="tel" class="input-field" placeholder="+375 (XX) XXX-XX-XX" />
          </div>
          <div>
            <label class="label">Email</label>
            <input v-model="email" type="email" class="input-field" placeholder="example@mail.com" />
          </div>
        </div>

        <!-- Individual fields -->
        <template v-if="form.user_type === 'individual'">
          <h3 class="text-sm font-semibold text-gray-700 border-b border-surface-200 pb-2">Данные физического лица</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="sm:col-span-2">
              <label class="label">ФИО</label>
              <input v-model="individual.full_name" type="text" class="input-field" placeholder="Иванов Иван Иванович" required />
            </div>
            <div>
              <label class="label">Идентификационный номер паспорта</label>
              <input v-model="individual.passport_id" type="text" class="input-field" placeholder="14 символов" maxlength="14" />
            </div>
            <div>
              <label class="label">Номер паспорта</label>
              <input v-model="individual.passport_number" type="text" class="input-field" placeholder="AB1234567" maxlength="9" />
            </div>
            <div>
              <label class="label">Кем выдан</label>
              <input v-model="individual.issued_by" type="text" class="input-field" placeholder="Московское РУВД г. Минска" />
            </div>
            <div>
              <label class="label">Дата выдачи</label>
              <input v-model="individual.issue_date" type="date" class="input-field" />
            </div>
            <div>
              <label class="label">Срок действия</label>
              <input v-model="individual.expiry_date" type="date" class="input-field" />
            </div>
          </div>
        </template>

        <!-- IE fields -->
        <template v-if="form.user_type === 'ie'">
          <h3 class="text-sm font-semibold text-gray-700 border-b border-surface-200 pb-2">Данные ИП</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="sm:col-span-2">
              <label class="label">ФИО</label>
              <input v-model="entrepreneur.full_name" type="text" class="input-field" placeholder="ИП Кушнарев Дмитрий Васильевич" required />
            </div>
            <div>
              <label class="label">УНП</label>
              <input v-model="entrepreneur.unp" type="text" class="input-field" placeholder="9 цифр" maxlength="9" />
            </div>
            <div class="sm:col-span-2">
              <label class="label">Юридический адрес</label>
              <input v-model="entrepreneur.legal_address" type="text" class="input-field" />
            </div>
            <div class="sm:col-span-2">
              <label class="label">Почтовый адрес</label>
              <input v-model="entrepreneur.postal_address" type="text" class="input-field" />
            </div>
          </div>
        </template>

        <!-- Company fields -->
        <template v-if="form.user_type === 'company'">
          <h3 class="text-sm font-semibold text-gray-700 border-b border-surface-200 pb-2">Данные юридического лица</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="label">Название компании</label>
              <input v-model="company.company_name" type="text" class="input-field" placeholder="АстраЛизинг" required />
            </div>
            <div>
              <label class="label">Организационно-правовая форма</label>
              <input v-model="company.legal_form" type="text" class="input-field" placeholder="ООО" />
            </div>
            <div>
              <label class="label">УНП</label>
              <input v-model="company.unp" type="text" class="input-field" placeholder="9 цифр" maxlength="9" />
            </div>
            <div>
              <label class="label">ОКПО</label>
              <input v-model="company.okpo" type="text" class="input-field" placeholder="12 цифр" maxlength="12" />
            </div>
            <div class="sm:col-span-2">
              <label class="label">Юридический адрес</label>
              <input v-model="company.legal_address" type="text" class="input-field" />
            </div>
            <div class="sm:col-span-2">
              <label class="label">Почтовый адрес</label>
              <input v-model="company.postal_address" type="text" class="input-field" />
            </div>
            <div class="sm:col-span-2">
              <label class="label">ФИО директора</label>
              <input v-model="company.director_name" type="text" class="input-field" />
            </div>
          </div>
        </template>

        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

        <button type="submit" :disabled="loading" class="btn-primary w-full">
          {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
        </button>
      </form>

      <p class="text-center text-sm text-gray-500 mt-6">
        Уже есть аккаунт?
        <router-link to="/login" class="text-primary-500 font-medium hover:underline">Войти</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ login: '', password: '', role: '', user_type: '' })
const phone = ref('')
const email = ref('')
const individual = ref({ full_name: '', passport_id: '', passport_number: '', issued_by: '', issue_date: null, expiry_date: null })
const entrepreneur = ref({ full_name: '', unp: '', legal_address: '', postal_address: '' })
const company = ref({ company_name: '', legal_form: '', unp: '', okpo: '', legal_address: '', postal_address: '', director_name: '' })
const error = ref('')
const loading = ref(false)

watch(() => form.value.role, (val) => {
  if (val === 'lease_manager') form.value.user_type = 'company'
})

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    const data = { ...form.value, contacts: [] }
    if (phone.value) data.contacts.push({ type: 'phone', value: phone.value, is_primary: true })
    if (email.value) data.contacts.push({ type: 'email', value: email.value, is_primary: !phone.value })

    if (form.value.user_type === 'individual') data.individual = individual.value
    else if (form.value.user_type === 'ie') data.entrepreneur = entrepreneur.value
    else if (form.value.user_type === 'company') data.company = company.value

    await auth.register(data)
    await auth.login(form.value.login, form.value.password)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка регистрации'
  } finally {
    loading.value = false
  }
}
</script>
