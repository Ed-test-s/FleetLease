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
import { leasingApi } from '@/api/leasing'
import { useNotificationsStore } from '@/stores/notifications'
import { formatDateTime } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const notifStore = useNotificationsStore()
const router = useRouter()
const loading = ref(true)

function detectRequestFocusKind(notification) {
  const title = String(notification.title || '').toLowerCase()
  const text = String(notification.text || '').toLowerCase()
  const combined = `${title} ${text}`
  if (combined.includes('заявка на покупку')) return 'purchase'
  if (combined.includes('заявка на лизинг') || combined.includes('лизинг')) return 'lease'
  return null
}

function extractPurchaseContractNumber(text) {
  if (!text) return null
  const match = String(text).match(/договор\s+купли-продажи\s+#([A-Za-z0-9-]+)/i)
  return match ? match[1] : null
}

async function openPurchaseContractFromNotification(notification) {
  const contractNumber = extractPurchaseContractNumber(notification.text)
  if (!contractNumber) return false

  try {
    const { data } = await leasingApi.listContracts({ limit: 100, contract_type: 'purchase_sale' })
    const match = Array.isArray(data)
      ? data.find((contract) => contract.contract_number === contractNumber)
      : null
    if (match?.id) {
      await router.push(`/contracts/${match.id}`)
      return true
    }
  } catch {
    // Fallback below handles navigation when lookup fails.
  }

  await router.push('/contracts')
  return true
}

async function openNotification(notification) {
  if (!notification.is_read) {
    await notifStore.markRead(notification.id)
  }

  if (!notification.type || !notification.entity_id) return

  if (notification.type === 'request_status_changed') {
    const openedPurchaseContract = await openPurchaseContractFromNotification(notification)
    if (openedPurchaseContract) return

    const focusRequestKind = detectRequestFocusKind(notification)
    const query = { focusRequestId: String(notification.entity_id) }
    if (focusRequestKind) query.focusRequestKind = focusRequestKind
    await router.push({ path: '/requests', query })
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
