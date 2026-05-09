<template>
  <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Мои объявления</h1>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- Add new card -->
      <router-link to="/my-vehicles/new"
                   class="card border-2 border-dashed border-surface-300 hover:border-primary-400 flex flex-col items-center justify-center py-12 transition-colors group">
        <svg class="w-12 h-12 text-gray-300 group-hover:text-primary-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        <span class="text-sm text-gray-400 group-hover:text-primary-500 mt-2">Добавить объявление</span>
      </router-link>

      <div v-for="v in vehicles" :key="v.id" class="card overflow-hidden relative">
        <router-link
          :to="`/vehicles/${v.id}`"
          class="group block text-left hover:opacity-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 focus-visible:ring-offset-2 rounded-[inherit]"
        >
          <div class="aspect-[16/10] bg-surface-100">
            <img v-if="v.images?.length" :src="v.images[0].image_url" :alt="v.name" class="w-full h-full object-cover" />
          </div>
          <div class="p-4">
            <h3 class="font-semibold text-gray-900 truncate group-hover:text-primary-600 transition-colors">{{ v.name }}</h3>
            <p class="text-sm font-bold text-primary-500 mt-1">{{ formatPrice(v.price) }}</p>
            <div class="flex items-center justify-between mt-2 text-xs text-gray-500">
              <span>{{ v.count }} шт.</span>
              <span :class="v.is_visible ? 'text-green-600' : 'text-red-500'">
                {{ v.is_visible ? 'Активно' : 'Скрыто' }}
              </span>
            </div>
          </div>
        </router-link>
        <div class="absolute top-2 right-2 z-10 flex gap-1" @click.stop>
          <router-link :to="`/my-vehicles/${v.id}/edit`" class="p-1.5 bg-white/90 rounded-lg hover:bg-white shadow-sm" title="Редактировать">
            <svg class="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
          </router-link>
          <button type="button" @click="deleteVehicle(v.id)" class="p-1.5 bg-white/90 rounded-lg hover:bg-white shadow-sm" title="Удалить">
            <svg class="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { vehiclesApi } from '@/api/vehicles'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { formatPrice } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const auth = useAuthStore()
const notifStore = useNotificationsStore()
const vehicles = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await vehiclesApi.list({ supplier_id: auth.user.id, limit: 100 })
    vehicles.value = data
  } finally {
    loading.value = false
  }
})

async function deleteVehicle(id) {
  if (!confirm('Удалить это объявление?')) return
  await vehiclesApi.delete(id)
  vehicles.value = vehicles.value.filter(v => v.id !== id)
  notifStore.showToast('Объявление удалено', 'success')
}
</script>
