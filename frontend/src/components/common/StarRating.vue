<template>
  <div class="flex items-center gap-1">
    <template v-for="i in 5" :key="i">
      <svg @click="editable && $emit('update:modelValue', i)"
           :class="[
             'w-4 h-4 transition-colors',
             i <= displayValue ? 'text-yellow-400' : 'text-gray-300',
             editable ? 'cursor-pointer hover:text-yellow-300' : ''
           ]"
           fill="currentColor" viewBox="0 0 20 20">
        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
      </svg>
    </template>
    <span v-if="showValue && displayValue" class="text-sm font-medium text-gray-600 ml-1">
      {{ typeof displayValue === 'number' ? displayValue.toFixed(2) : displayValue }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Number, default: 0 },
  rating: { type: Number, default: null },
  editable: { type: Boolean, default: false },
  showValue: { type: Boolean, default: true },
})

defineEmits(['update:modelValue'])

const displayValue = computed(() => props.rating ?? props.modelValue)
</script>
