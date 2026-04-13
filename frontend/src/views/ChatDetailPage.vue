<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 py-6 h-[calc(100vh-8rem)] flex flex-col">
    <div class="flex items-center gap-3 mb-4">
      <router-link to="/chats" class="text-gray-400 hover:text-primary-500 transition-colors">
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
      </router-link>
      <div v-if="chat?.partner" class="flex items-center gap-3 min-w-0 flex-1">
        <div class="w-10 h-10 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-bold flex-shrink-0 overflow-hidden">
          <img v-if="chat.partner.avatar_url" :src="chat.partner.avatar_url" class="w-full h-full object-cover" alt="" />
          <span v-else>{{ chatPartnerInitial }}</span>
        </div>
        <div class="min-w-0">
          <h1 class="text-lg font-bold text-gray-900 truncate">{{ chat.partner.display_name }}</h1>
          <p class="text-xs text-gray-500">Чат #{{ route.params.id }}</p>
        </div>
      </div>
      <h1 v-else class="text-lg font-bold text-gray-900">Чат #{{ route.params.id }}</h1>
      <span v-if="chat" class="badge text-[10px] flex-shrink-0" :class="chat.chat_type === 'request' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'">
        {{ chat?.chat_type === 'request' ? 'Заявка' : 'Поставщик' }}
      </span>

      <!-- Link to contract if exists -->
      <router-link v-if="chat?.contract_id" :to="`/contracts/${chat.contract_id}`" class="ml-auto btn-secondary btn-sm">
        Приложения к договору
      </router-link>
    </div>

    <!-- Messages -->
    <div ref="messagesContainer" class="flex-1 card overflow-y-auto p-4 space-y-3">
      <div v-for="m in messages" :key="m.id"
           :class="['max-w-[75%] p-3 rounded-xl text-sm', m.sender_id === auth.user?.id ? 'ml-auto bg-primary-500 text-white rounded-br-sm' : 'bg-surface-100 text-gray-800 rounded-bl-sm']">
        <p>{{ m.message_text }}</p>
        <a v-if="m.file_url" :href="m.file_url" target="_blank" class="underline text-xs mt-1 block opacity-80">Прикреплённый файл</a>
        <span :class="['text-[10px] block mt-1', m.sender_id === auth.user?.id ? 'text-white/60' : 'text-gray-400']">
          {{ formatDateTime(m.created_at) }}
        </span>
      </div>
    </div>

    <!-- Input -->
    <form @submit.prevent="sendMessage" class="flex gap-2 mt-3">
      <input v-model="messageText" type="text" class="input-field flex-1" placeholder="Введите сообщение..." required />
      <label class="btn-secondary cursor-pointer flex-shrink-0">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
        <input type="file" class="hidden" @change="handleFileUpload" />
      </label>
      <button type="submit" class="btn-primary flex-shrink-0">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { chatsApi } from '@/api/chats'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const auth = useAuthStore()

const chat = ref(null)
const messages = ref([])
const messageText = ref('')
const messagesContainer = ref(null)
let ws = null

const chatPartnerInitial = computed(() => {
  const n = chat.value?.partner?.display_name
  return n ? n.charAt(0).toUpperCase() : '?'
})

onMounted(async () => {
  const chatId = route.params.id
  const [chatRes, msgRes] = await Promise.all([
    chatsApi.get(chatId),
    chatsApi.getMessages(chatId, { limit: 200 }),
  ])
  chat.value = chatRes.data
  messages.value = msgRes.data
  await nextTick()
  scrollToBottom()

  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const token = localStorage.getItem('token')
  ws = new WebSocket(`${protocol}://${location.host}/api/v1/chats/${chatId}/ws?token=${token}`)
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    messages.value.push(msg)
    nextTick(() => scrollToBottom())
  }
})

onUnmounted(() => {
  ws?.close()
})

async function sendMessage() {
  if (!messageText.value.trim()) return
  const { data } = await chatsApi.sendMessage(route.params.id, { message_text: messageText.value })
  messages.value.push(data)
  messageText.value = ''
  await nextTick()
  scrollToBottom()
}

async function handleFileUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  const { data } = await chatsApi.sendMessage(route.params.id, {
    message_text: `Файл: ${file.name}`,
    file_url: URL.createObjectURL(file),
  })
  messages.value.push(data)
  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
</script>
