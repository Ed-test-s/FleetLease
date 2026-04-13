<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Чаты</h1>

    <!-- Tabs for lease manager -->
    <div v-if="auth.userRole === 'lease_manager'" class="flex gap-1 mb-6 bg-surface-100 p-1 rounded-lg w-fit">
      <button @click="tab = 'request'" :class="['px-4 py-2 text-sm rounded-md font-medium transition-colors', tab === 'request' ? 'bg-white shadow-sm text-primary-500' : 'text-gray-500 hover:text-gray-700']">
        С лизингополучателями
      </button>
      <button @click="tab = 'supplier'" :class="['px-4 py-2 text-sm rounded-md font-medium transition-colors', tab === 'supplier' ? 'bg-white shadow-sm text-primary-500' : 'text-gray-500 hover:text-gray-700']">
        С поставщиками
      </button>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else-if="filteredChats.length === 0" class="text-center py-16 text-gray-500">Чатов пока нет</div>
    <div v-else class="space-y-2">
      <router-link v-for="c in filteredChats" :key="c.id" :to="`/chats/${c.id}`"
                   class="card p-4 flex items-center gap-4 hover:shadow-md transition-shadow">
        <div class="w-10 h-10 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-bold flex-shrink-0 overflow-hidden">
          <img v-if="c.partner?.avatar_url" :src="c.partner.avatar_url" class="w-full h-full object-cover" alt="" />
          <span v-else>{{ partnerInitial(c) }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium text-gray-900 truncate">{{ c.partner?.display_name || `Чат #${c.id}` }}</span>
            <span class="badge text-[10px]" :class="c.chat_type === 'request' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'">
              {{ c.chat_type === 'request' ? 'Заявка' : 'Поставщик' }}
            </span>
          </div>
          <p v-if="c.last_message" class="text-xs text-gray-500 truncate mt-0.5">{{ c.last_message.message_text }}</p>
          <p v-else class="text-xs text-gray-400 mt-0.5">Нет сообщений</p>
        </div>
        <span v-if="c.last_message" class="text-[10px] text-gray-400 flex-shrink-0">
          {{ formatDateTime(c.last_message.created_at) }}
        </span>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { chatsApi } from '@/api/chats'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const auth = useAuthStore()
const chats = ref([])
const loading = ref(true)
const tab = ref('request')

const filteredChats = computed(() => {
  if (auth.userRole !== 'lease_manager') return chats.value
  return chats.value.filter(c => c.chat_type === tab.value)
})

onMounted(async () => {
  try {
    const { data } = await chatsApi.list()
    chats.value = data
  } finally {
    loading.value = false
  }
})

function partnerInitial(c) {
  const name = c.partner?.display_name || ''
  if (name) return name.charAt(0).toUpperCase()
  return c.chat_type === 'request' ? 'Л' : 'П'
}
</script>
