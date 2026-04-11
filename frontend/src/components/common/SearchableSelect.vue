<template>
  <div class="relative" ref="wrapper">
    <div @click="open = !open" class="input-field cursor-pointer flex items-center justify-between pr-2"
         :class="{ 'ring-2 ring-primary-500 border-primary-500': open }">
      <span :class="modelValue ? 'text-gray-800' : 'text-gray-400'" class="truncate">
        {{ displayLabel || placeholder }}
      </span>
      <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </div>

    <div v-if="open" class="absolute z-50 mt-1 w-full bg-white border border-surface-200 rounded-lg shadow-lg max-h-60 flex flex-col">
      <div class="p-2 border-b border-surface-100">
        <input ref="searchInput" v-model="searchQuery" type="text" class="input-field py-1.5 text-sm"
               :placeholder="searchPlaceholder" @click.stop />
      </div>
      <ul class="overflow-y-auto flex-1 py-1">
        <li v-if="allowEmpty" @click="select(null)"
            class="px-3 py-2 text-sm text-gray-400 hover:bg-surface-50 cursor-pointer">
          {{ emptyLabel }}
        </li>
        <li v-for="opt in filteredOptions" :key="opt.value" @click="select(opt.value)"
            :class="['px-3 py-2 text-sm cursor-pointer transition-colors',
                      opt.value === modelValue ? 'bg-primary-50 text-primary-600 font-medium' : 'text-gray-700 hover:bg-surface-50']">
          {{ opt.label }}
        </li>
        <li v-if="filteredOptions.length === 0" class="px-3 py-2 text-sm text-gray-400 text-center">
          Ничего не найдено
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number, null], default: null },
  options: { type: Array, required: true }, // [{ value, label }]
  placeholder: { type: String, default: 'Выберите...' },
  searchPlaceholder: { type: String, default: 'Поиск...' },
  allowEmpty: { type: Boolean, default: true },
  emptyLabel: { type: String, default: 'Все' },
})

const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const searchQuery = ref('')
const wrapper = ref(null)
const searchInput = ref(null)

const displayLabel = computed(() => {
  const opt = props.options.find(o => o.value === props.modelValue)
  return opt ? opt.label : ''
})

const filteredOptions = computed(() => {
  const q = searchQuery.value.toLowerCase()
  if (!q) return props.options
  return props.options.filter(o => o.label.toLowerCase().includes(q))
})

function select(val) {
  emit('update:modelValue', val)
  open.value = false
  searchQuery.value = ''
}

function handleClickOutside(e) {
  if (wrapper.value && !wrapper.value.contains(e.target)) {
    open.value = false
    searchQuery.value = ''
  }
}

watch(open, async (val) => {
  if (val) {
    await nextTick()
    searchInput.value?.focus()
  }
})

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>
