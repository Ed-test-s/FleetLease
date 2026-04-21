<template>
  <div class="min-h-[80vh] flex items-center justify-center px-4 py-12">
    <div class="card p-8 w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900">Восстановление доступа</h1>
        <p class="text-sm text-gray-500 mt-2">
          Укажите email, привязанный к аккаунту. Мы отправим на него временный пароль.
        </p>
      </div>

      <form v-if="!sent" @submit.prevent="handleSubmit" class="space-y-5">
        <div>
          <label class="label">Email</label>
          <input
            v-model="email"
            type="email"
            class="input-field"
            placeholder="example@mail.com"
            required
            autocomplete="email"
          />
        </div>

        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

        <button type="submit" :disabled="loading" class="btn-primary w-full">
          {{ loading ? 'Отправка...' : 'Отправить письмо' }}
        </button>
      </form>

      <div v-else class="space-y-4 text-center">
        <p class="text-sm text-gray-700">
          Если для этого адреса есть учётная запись, на указанный email отправлено письмо с временным паролем.
          Войдите с ним и смените пароль в разделе «Мой профиль».
        </p>
        <router-link to="/login" class="btn-primary inline-block w-full text-center">Перейти ко входу</router-link>
      </div>

      <p class="text-center text-sm text-gray-500 mt-6">
        <router-link to="/login" class="text-primary-500 font-medium hover:underline">Назад к входу</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { authApi } from '@/api/auth'
import { formatApiError } from '@/utils/apiError'

const email = ref('')
const error = ref('')
const loading = ref(false)
const sent = ref(false)

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await authApi.forgotPassword(email.value.trim())
    sent.value = true
  } catch (e) {
    error.value = formatApiError(e, 'Не удалось отправить запрос')
  } finally {
    loading.value = false
  }
}
</script>
