<template>
  <div class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
    <transition-group name="toast">
      <div v-for="toast in notifStore.toasts" :key="toast.id"
           :class="[
             'px-4 py-3 rounded-lg shadow-lg text-sm font-medium max-w-sm',
             toast.type === 'success' ? 'bg-green-600 text-white' :
             toast.type === 'error' ? 'bg-red-600 text-white' :
             'bg-primary-500 text-white'
           ]">
        {{ toast.message }}
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useNotificationsStore } from '@/stores/notifications'
const notifStore = useNotificationsStore()
</script>

<style scoped>
.toast-enter-active { animation: slideIn 0.3s ease; }
.toast-leave-active { animation: slideOut 0.3s ease; }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } }
@keyframes slideOut { to { transform: translateX(100%); opacity: 0; } }
</style>
