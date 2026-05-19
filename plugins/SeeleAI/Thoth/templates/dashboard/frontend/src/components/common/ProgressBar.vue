<script setup lang="ts">
const props = withDefaults(defineProps<{
  value: number
  color?: string
  height?: number
}>(), {
  color: 'var(--accent-primary)',
  height: 8,
})

const clampedValue = computed(() => Math.max(0, Math.min(100, props.value)))

import { computed } from 'vue'
</script>

<template>
  <div class="progress-bar-wrapper">
    <div
      class="progress-bar-track"
      :style="{ height: `${height}px` }"
    >
      <div
        class="progress-bar-fill"
        :style="{
          width: `${clampedValue}%`,
          backgroundColor: color,
          height: `${height}px`,
        }"
      />
    </div>
    <span class="progress-bar-label">{{ Math.round(clampedValue) }}%</span>
  </div>
</template>

<style scoped>
.progress-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.progress-bar-track {
  flex: 1;
  background: var(--bg-hover, #f0ebe4);
  border-radius: 999px;
  overflow: hidden;
}

.progress-bar-fill {
  border-radius: 999px;
  transition: width 0.4s ease;
}

.progress-bar-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, #6b5b4e);
  min-width: 36px;
  text-align: right;
}
</style>
