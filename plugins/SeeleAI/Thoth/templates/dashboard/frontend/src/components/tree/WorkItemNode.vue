<script setup lang="ts">
import type { TreeWorkItem } from '@/types'
import { useDashboardStore } from '@/stores/dashboard'

const props = defineProps<{ task: TreeWorkItem }>()
const store = useDashboardStore()

function selectWorkItem() {
  void store.selectWorkItem(props.task.id)
}
</script>

<template>
  <button class="task" :class="{ 'task--selected': store.selectedWorkItem?.id === task.id }" @click="selectWorkItem">
    <span class="task__status" :class="`badge-${task.status}`" />
    <span class="task__id">{{ task.id }}</span>
    <span class="task__title">{{ task.title }}</span>
  </button>
</template>

<style scoped>
.task {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 8px;
  border-radius: var(--radius-xs);
  text-align: left;
}

.task:hover,
.task--selected {
  background: rgba(255, 255, 255, 0.72);
}

.task__status {
  width: 9px;
  height: 9px;
  border-radius: 999px;
}

.task__id {
  font-family: var(--font-mono);
  color: var(--text-muted);
  font-size: 0.7rem;
}

.task__title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
