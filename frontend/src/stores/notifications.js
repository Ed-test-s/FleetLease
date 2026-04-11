import { defineStore } from 'pinia'
import { ref } from 'vue'
import { notificationsApi } from '@/api/notifications'

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref([])
  const unreadCount = ref(0)
  const toasts = ref([])

  async function fetchNotifications() {
    const { data } = await notificationsApi.list({ limit: 30 })
    notifications.value = data
  }

  async function fetchUnreadCount() {
    const { data } = await notificationsApi.unreadCount()
    unreadCount.value = data.count
  }

  async function markRead(id) {
    await notificationsApi.markRead(id)
    const n = notifications.value.find((n) => n.id === id)
    if (n) n.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  async function markAllRead() {
    await notificationsApi.markAllRead()
    notifications.value.forEach((n) => (n.is_read = true))
    unreadCount.value = 0
  }

  function showToast(message, type = 'info') {
    const id = Date.now()
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, 4000)
  }

  return { notifications, unreadCount, toasts, fetchNotifications, fetchUnreadCount, markRead, markAllRead, showToast }
})
