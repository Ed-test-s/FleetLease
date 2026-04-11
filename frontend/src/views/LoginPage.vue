<template>
  <div class="min-h-[80vh] flex items-center justify-center px-4 py-12">
    <div class="card p-8 w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900">Вход в систему</h1>
        <p class="text-sm text-gray-500 mt-2">Войдите по логину, номеру телефона или email</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-5">
        <div>
          <label class="label">Логин / Телефон / Email</label>
          <input v-model="form.identifier" type="text" class="input-field" placeholder="Введите логин, телефон или email" required />
        </div>

        <div>
          <label class="label">Пароль</label>
          <input v-model="form.password" type="password" class="input-field" placeholder="Введите пароль" required />
        </div>

        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

        <button type="submit" :disabled="loading" class="btn-primary w-full">
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>

      <p class="text-center text-sm text-gray-500 mt-6">
        Нет аккаунта?
        <router-link to="/register" class="text-primary-500 font-medium hover:underline">Зарегистрироваться</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { formatApiError } from '@/utils/apiError'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = ref({ identifier: '', password: '' })
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(form.value.identifier, form.value.password)
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    error.value = formatApiError(e, 'Ошибка авторизации')
  } finally {
    loading.value = false
  }
}
</script>
