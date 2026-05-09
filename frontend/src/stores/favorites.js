import { defineStore } from 'pinia'
import { ref } from 'vue'
import { favoritesApi } from '@/api/favorites'

export const useFavoritesStore = defineStore('favorites', () => {
  const ids = ref(new Set())

  function isFavorited(vehicleId) {
    return ids.value.has(vehicleId)
  }

  async function fetchIds() {
    try {
      const { data } = await favoritesApi.ids()
      ids.value = new Set(data)
    } catch {
      ids.value = new Set()
    }
  }

  async function toggle(vehicleId) {
    if (ids.value.has(vehicleId)) {
      ids.value.delete(vehicleId)
      ids.value = new Set(ids.value)
      try {
        await favoritesApi.remove(vehicleId)
      } catch {
        ids.value.add(vehicleId)
        ids.value = new Set(ids.value)
      }
    } else {
      ids.value.add(vehicleId)
      ids.value = new Set(ids.value)
      try {
        await favoritesApi.add(vehicleId)
      } catch {
        ids.value.delete(vehicleId)
        ids.value = new Set(ids.value)
      }
    }
  }

  function clear() {
    ids.value = new Set()
  }

  return { ids, isFavorited, fetchIds, toggle, clear }
})
