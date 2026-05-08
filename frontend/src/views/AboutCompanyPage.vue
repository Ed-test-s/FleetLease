<template>
  <div class="min-h-[80vh] px-4 py-12">
    <div v-if="loading" class="py-16">
      <LoadingSpinner />
    </div>
    <div v-else-if="error" class="card p-8 max-w-2xl mx-auto text-center text-red-600">
      {{ error }}
    </div>
    <div v-else class="max-w-4xl mx-auto space-y-12">
      <section class="card overflow-hidden">
        <div class="grid md:grid-cols-2 gap-0">
          <div class="p-8 md:p-10 flex flex-col justify-center">
            <h1 class="text-3xl font-bold text-gray-900 mb-4">{{ content.hero.title }}</h1>
            <p class="text-gray-600 leading-relaxed whitespace-pre-wrap">{{ content.hero.subtitle }}</p>
          </div>
          <div v-if="content.hero.image_url" class="min-h-[220px] md:min-h-full bg-surface-100">
            <img
              :src="content.hero.image_url"
              alt=""
              class="w-full h-full object-cover min-h-[220px] md:min-h-[320px]"
            />
          </div>
          <div
            v-else
            class="hidden md:flex min-h-[320px] bg-gradient-to-br from-primary-100 to-surface-100 items-center justify-center text-primary-400"
          >
            <svg class="w-24 h-24 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
        </div>
      </section>

      <section
        v-for="(block, idx) in content.blocks"
        :key="idx"
        class="card p-8 md:p-10"
      >
        <div
          class="flex flex-col gap-6"
          :class="block.image_url ? 'md:flex-row md:items-start md:gap-10' : ''"
        >
          <div v-if="block.image_url" class="shrink-0 md:w-2/5">
            <img :src="block.image_url" alt="" class="rounded-xl w-full object-cover max-h-72 shadow-sm border border-surface-200" />
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-xl font-semibold text-gray-900 mb-3">{{ block.title }}</h2>
            <p class="text-gray-700 leading-relaxed whitespace-pre-wrap">{{ block.body }}</p>
          </div>
        </div>
      </section>

      <p class="text-center pb-8">
        <router-link to="/" class="text-primary-500 font-medium hover:underline text-sm">На главную</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { siteApi } from '@/api/site'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const loading = ref(true)
const error = ref('')
const content = ref({
  hero: { title: '', subtitle: '', image_url: null },
  blocks: [],
})

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await siteApi.getAbout()
    content.value = data
  } catch {
    error.value = 'Не удалось загрузить страницу. Попробуйте позже.'
  } finally {
    loading.value = false
  }
})
</script>
