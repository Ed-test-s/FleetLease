<template>
  <span :class="['badge', `badge-${status}`]">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { statusLabels } from '@/utils/format'

const props = defineProps({ status: { type: String, required: true } })
const label = computed(() => statusLabels[props.status] || props.status)
</script>
