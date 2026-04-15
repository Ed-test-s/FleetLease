<template>
  <div class="min-h-[80vh] flex items-center justify-center px-4 py-12">
    <div class="card p-8 w-full max-w-2xl">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900">Регистрация</h1>
        <p class="text-sm text-gray-500 mt-2">Создайте аккаунт в системе FleetLease</p>
      </div>

      <form @submit.prevent="handleRegister" class="space-y-6" novalidate>
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
            <input v-model="form.login" @blur="touched.login = true" type="text" required
                   :class="['input-field', fieldError('login') ? 'border-red-500 ring-1 ring-red-500' : '']"
                   placeholder="Только латиница и _" />
            <p v-if="fieldError('login')" class="text-xs text-red-500 mt-1">{{ fieldError('login') }}</p>
          </div>
          <div>
            <label class="label">Пароль</label>
            <input v-model="form.password" @blur="touched.password = true" type="password" required
                   :class="['input-field', fieldError('password') ? 'border-red-500 ring-1 ring-red-500' : '']"
                   placeholder="Не менее 6 символов" />
            <p v-if="fieldError('password')" class="text-xs text-red-500 mt-1">{{ fieldError('password') }}</p>
          </div>
        </div>

        <!-- Contacts -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="label">Номер телефона</label>
            <input v-model="phone" @blur="touched.phone = true" type="tel"
                   :class="['input-field', fieldError('phone') ? 'border-red-500 ring-1 ring-red-500' : '']"
                   placeholder="+375 (XX) XXX-XX-XX" />
            <p v-if="fieldError('phone')" class="text-xs text-red-500 mt-1">{{ fieldError('phone') }}</p>
          </div>
          <div>
            <label class="label">Email</label>
            <input v-model="email" @blur="touched.email = true" type="email"
                   :class="['input-field', fieldError('email') ? 'border-red-500 ring-1 ring-red-500' : '']"
                   placeholder="example@mail.com" />
            <p v-if="fieldError('email')" class="text-xs text-red-500 mt-1">{{ fieldError('email') }}</p>
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
            <div class="sm:col-span-2">
              <label class="label">Адрес прописки</label>
              <input
                v-model="individual.registration_address"
                @blur="touched.registration_address = true"
                type="text"
                :class="['input-field', fieldError('registration_address') ? 'border-red-500 ring-1 ring-red-500' : '']"
                placeholder="г. Минск, пр. Дзержинского, д. 127, кв. 123"
              />
              <p v-if="fieldError('registration_address')" class="text-xs text-red-500 mt-1">{{ fieldError('registration_address') }}</p>
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
              <input v-model="entrepreneur.full_name" type="text" class="input-field" placeholder="Кушнарев Дмитрий Васильевич" required />
            </div>
            <div>
              <label class="label">УНП</label>
              <input v-model="entrepreneur.unp" @blur="touched.unp_ie = true" type="text"
                     :class="['input-field', fieldError('unp_ie') ? 'border-red-500 ring-1 ring-red-500' : '']"
                     placeholder="9 цифр" maxlength="9" />
              <p v-if="fieldError('unp_ie')" class="text-xs text-red-500 mt-1">{{ fieldError('unp_ie') }}</p>
            </div>
            <div class="sm:col-span-2">
              <label class="label">Юридический адрес</label>
              <input v-model="entrepreneur.legal_address" type="text" class="input-field" placeholder="г. Минск, пр. Дзержинского, д. 127, кв. 123" />
            </div>
            <div class="sm:col-span-2">
              <label class="label">Почтовый адрес</label>
              <input v-model="entrepreneur.postal_address" type="text" class="input-field" placeholder="г. Минск, пр. Дзержинского, д. 127, кв. 123" />
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
              <select v-model="company.legal_form" class="input-field">
                <option value="">Выберите</option>
                <option v-for="f in legalForms" :key="f">{{ f }}</option>
              </select>
            </div>
            <div>
              <label class="label">УНП</label>
              <input v-model="company.unp" @blur="touched.unp_co = true" type="text"
                     :class="['input-field', fieldError('unp_co') ? 'border-red-500 ring-1 ring-red-500' : '']"
                     placeholder="9 цифр" maxlength="9" />
              <p v-if="fieldError('unp_co')" class="text-xs text-red-500 mt-1">{{ fieldError('unp_co') }}</p>
            </div>
            <div>
              <label class="label">ОКПО</label>
              <input v-model="company.okpo" @blur="touched.okpo = true" type="text"
                     :class="['input-field', fieldError('okpo') ? 'border-red-500 ring-1 ring-red-500' : '']"
                     placeholder="12 цифр" maxlength="12" />
              <p v-if="fieldError('okpo')" class="text-xs text-red-500 mt-1">{{ fieldError('okpo') }}</p>
            </div>
            <div class="sm:col-span-2">
              <label class="label">Юридический адрес</label>
              <input v-model="company.legal_address" type="text" class="input-field" placeholder="г. Минск, пр. Дзержинского, д. 127, кв. 123" />
            </div>
            <div class="sm:col-span-2">
              <label class="label">Почтовый адрес</label>
              <input v-model="company.postal_address" type="text" class="input-field" placeholder="г. Минск, пр. Дзержинского, д. 127, кв. 123" />
            </div>
            <div class="sm:col-span-2">
              <label class="label">ФИО директора</label>
              <input v-model="company.director_name" type="text" class="input-field" />
            </div>
          </div>
        </template>

        <p v-if="error" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">{{ error }}</p>

        <button type="submit" :disabled="loading || hasErrors" class="btn-primary w-full">
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
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { formatApiError } from '@/utils/apiError'

const auth = useAuthStore()
const router = useRouter()

const legalForms = ['ООО', 'ОДО', 'ОАО', 'ЗАО', 'ПК', 'УП']

const form = ref({ login: '', password: '', role: '', user_type: '' })
const phone = ref('')
const email = ref('')
const individual = ref({
  full_name: '',
  registration_address: '',
  passport_id: '',
  passport_number: '',
  issued_by: '',
  issue_date: null,
  expiry_date: null,
})
const entrepreneur = ref({ full_name: '', unp: '', legal_address: '', postal_address: '' })
const company = ref({ company_name: '', legal_form: '', unp: '', okpo: '', legal_address: '', postal_address: '', director_name: '' })
const error = ref('')
const loading = ref(false)
const touched = ref({})

watch(() => form.value.role, (val) => {
  if (val === 'lease_manager') form.value.user_type = 'company'
})

const validators = {
  login: () => {
    if (!form.value.login) return null
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(form.value.login)) return 'Только латинские буквы, цифры и _'
    if (form.value.login.length < 3) return 'Минимум 3 символа'
    return null
  },
  password: () => {
    if (!form.value.password) return null
    if (form.value.password.length < 6) return 'Минимум 6 символов'
    return null
  },
  phone: () => {
    if (!phone.value) return null
    const cleaned = phone.value.replace(/[\s\-\(\)]/g, '')
    if (!/^\+375(25|29|33|44)\d{7}$/.test(cleaned)) return 'Формат: +375 (XX) XXX-XX-XX'
    return null
  },
  email: () => {
    if (!email.value) return null
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) return 'Некорректный email'
    return null
  },
  unp_ie: () => {
    if (!entrepreneur.value.unp) return null
    if (!/^\d{9}$/.test(entrepreneur.value.unp)) return 'УНП: строго 9 цифр'
    return null
  },
  unp_co: () => {
    if (!company.value.unp) return null
    if (!/^\d{9}$/.test(company.value.unp)) return 'УНП: строго 9 цифр'
    return null
  },
  okpo: () => {
    if (!company.value.okpo) return null
    if (!/^\d{12}$/.test(company.value.okpo)) return 'ОКПО: строго 12 цифр'
    return null
  },
  registration_address: () => {
    if (form.value.user_type !== 'individual') return null
    if (!individual.value.registration_address?.trim()) return 'Укажите адрес прописки'
    return null
  },
}

function fieldError(field) {
  if (!touched.value[field]) return null
  return validators[field]?.() || null
}

const hasErrors = computed(() =>
  Object.keys(validators).some(k => validators[k]?.())
)

async function handleRegister() {
  Object.keys(validators).forEach(k => (touched.value[k] = true))
  if (hasErrors.value) return

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
    error.value = formatApiError(
      e,
      'Ошибка регистрации. Проверьте правильность введённых данных.'
    )
  } finally {
    loading.value = false
  }
}
</script>
