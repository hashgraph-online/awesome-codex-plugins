<script setup lang="ts">
import { ref } from 'vue'
import type { TreeModule } from '@/types'
import WorkItemNode from './WorkItemNode.vue'
import { useDashboardStore } from '@/stores/dashboard'

const props = defineProps<{ module: TreeModule }>()
const store = useDashboardStore()
const open = ref(false)
</script>

<template>
  <div class="module">
    <div class="module__header">
      <button class="module__toggle" @click="open = !open">
        <span class="module__arrow" :class="{ 'module__arrow--open': open }">▸</span>
      </button>
      <button class="module__info" @click="store.selectModule(props.module.id)">
        <span class="module__id">{{ props.module.id }}</span>
        <span class="module__name">{{ props.module.name }}</span>
      </button>
      <span class="module__meta">{{ props.module.work_item_count }}</span>
    </div>
    <div v-show="open" class="module__work_items">
      <WorkItemNode v-for="task in props.module.work_items" :key="task.id" :task="task" />
    </div>
  </div>
</template>

<style scoped>
.module {
  margin: 2px 0;
}

.module__header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.module__toggle {
  width: 22px;
}

.module__arrow {
  display: inline-block;
  transition: transform 0.2s ease;
}

.module__arrow--open {
  transform: rotate(90deg);
}

.module__info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  padding: 6px 8px;
  border-radius: var(--radius-xs);
  text-align: left;
}

.module__info:hover {
  background: rgba(255, 255, 255, 0.6);
}

.module__id {
  font-family: var(--font-mono);
  color: var(--accent-primary);
  font-size: 0.74rem;
}

.module__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.module__meta {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.module__work_items {
  padding-left: 18px;
}
</style>
