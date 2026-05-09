<template>
  <div class="max-w-screen-2xl mx-auto px-4 sm:px-6 py-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Избранное</h1>
        <p class="text-sm text-gray-500 mt-1">Техника, которую вы добавили в избранное</p>
      </div>
    </div>

    <LoadingSpinner v-if="loading" />

    <div v-else-if="favorites.length === 0" class="text-center py-20">
      <svg class="mx-auto w-16 h-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
      </svg>
      <p class="text-gray-500 mb-4">У вас пока нет избранной техники</p>
      <router-link to="/" class="btn-primary">Перейти в каталог</router-link>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="f in favorites" :key="f.id" class="card overflow-hidden hover:shadow-md transition-shadow group">
        <router-link :to="`/vehicles/${f.vehicle_id}`" class="block">
          <div class="aspect-[16/10] bg-surface-100 overflow-hidden relative">
            <img v-if="f.vehicle_images?.length" :src="f.vehicle_images[0].image_url" :alt="f.vehicle_name"
                 class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
              <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5" />
              </svg>
            </div>
          </div>
        </router-link>
        <div class="p-4">
          <router-link :to="`/vehicles/${f.vehicle_id}`" class="block">
            <h3 class="font-semibold text-gray-900 truncate">{{ f.vehicle_name }}</h3>
            <p class="text-xs text-gray-500 mt-0.5">{{ f.vehicle_brand }} {{ f.vehicle_model }} · {{ f.vehicle_release_year || '—' }}</p>
            <div class="flex items-center justify-between mt-3">
              <span class="text-lg font-bold text-primary-500">{{ formatPrice(f.vehicle_price) }}</span>
              <span class="text-xs text-gray-400">{{ f.vehicle_location || '' }}</span>
            </div>
            <div class="flex items-center gap-3 mt-2 text-xs text-gray-500">
              <span v-if="f.vehicle_mileage != null">{{ formatMileage(f.vehicle_mileage) }}</span>
              <span v-if="f.vehicle_fuel_type">{{ f.vehicle_fuel_type }}</span>
              <span :class="f.vehicle_condition === 'new' ? 'text-green-600' : 'text-gray-500'">
                {{ f.vehicle_condition === 'new' ? 'Новый' : 'С пробегом' }}
              </span>
            </div>
          </router-link>
          <button @click="removeFavorite(f)"
                  class="mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 transition-colors">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Удалить из избранного
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { favoritesApi } from '@/api/favorites'
import { useFavoritesStore } from '@/stores/favorites'
import { formatPrice, formatMileage } from '@/utils/format'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const favStore = useFavoritesStore()
const favorites = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await favoritesApi.list()
    favorites.value = data
  } finally {
    loading.value = false
  }
})

async function removeFavorite(f) {
  await favStore.toggle(f.vehicle_id)
  favorites.value = favorites.value.filter(item => item.id !== f.id)
}
</script>
