<script setup lang="ts">
import { ref } from 'vue'
import type { TreeDirection } from '@/types'
import ModuleNode from './ModuleNode.vue'

defineProps<{ direction: TreeDirection }>()
const open = ref(true)
</script>

<template>
  <section class="direction">
    <button class="direction__header" @click="open = !open">
      <span class="direction__arrow" :class="{ 'direction__arrow--open': open }">▸</span>
      <span class="direction__label">{{ direction.label }}</span>
      <span class="direction__meta">{{ Math.round(direction.progress) }}%</span>
    </button>
    <div v-show="open" class="direction__modules">
      <ModuleNode v-for="module in direction.modules" :key="module.id" :module="module" />
    </div>
  </section>
</template>

<style scoped>
.direction {
  margin-bottom: 6px;
}

.direction__header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  text-align: left;
}

.direction__header:hover {
  background: rgba(255, 255, 255, 0.55);
}

.direction__arrow {
  transition: transform 0.2s ease;
}

.direction__arrow--open {
  transform: rotate(90deg);
}

.direction__label {
  flex: 1;
  font-weight: 700;
}

.direction__meta {
  color: var(--accent-primary);
  font-size: 0.78rem;
}

.direction__modules {
  padding-left: 12px;
}
</style>
