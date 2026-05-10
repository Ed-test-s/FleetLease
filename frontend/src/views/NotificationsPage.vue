<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 py-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Уведомления</h1>
      <button v-if="notifStore.notifications.some(n => !n.is_read)" @click="notifStore.markAllRead"
              class="btn-secondary btn-sm">
        Отметить все как прочитанные
      </button>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else-if="notifStore.notifications.length === 0" class="text-center py-16 text-gray-500">
      Уведомлений пока нет
    </div>
    <div v-else class="space-y-2">
      <div v-for="n in notifStore.notifications" :key="n.id"
           @click="openNotification(n)"
           :class="['card p-4 cursor-pointer transition-colors', n.is_read ? 'bg-white' : 'bg-primary-50 border-primary-200']">
        <div class="flex items-start justify-between">
          <div>
            <h3 :class="['text-sm font-medium', n.is_read ? 'text-gray-700' : 'text-gray-900']">{{ n.title }}</h3>
            <p class="text-xs text-gray-500 mt-0.5">{{ n.text }}</p>
          </div>
          <span class="text-[10px] text-gray-400 flex-shrink-0 ml-4">{{ formatDateTime(n.created_at) }}</span>
        </div>
        <div v-if="!n.is_read" class="w-2 h-2 rounded-full bg-primary-500 absolute top-4 left-2"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationsStore } from '@/stores/notifications'
import { formatDateTime } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const notifStore = useNotificationsStore()
const router = useRouter()
const loading = ref(true)

async function openNotification(notification) {
  if (!notification.is_read) {
    await notifStore.markRead(notification.id)
  }

  if (!notification.type || !notification.entity_id) return

  if (notification.type === 'request_status_changed') {
    await router.push({ path: '/requests', query: { focusRequestId: String(notification.entity_id) } })
    return
  }
  if (notification.type === 'contract_status_changed') {
    await router.push(`/contracts/${notification.entity_id}`)
    return
  }
  if (notification.type === 'chat_new_message') {
    await router.push(`/chats/${notification.entity_id}`)
  }
}

onMounted(async () => {
  await notifStore.fetchNotifications()
  loading.value = false
})
</script>
