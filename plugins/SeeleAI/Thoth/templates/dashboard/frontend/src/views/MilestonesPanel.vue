<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api/client'
import type { Milestone } from '@/types'

const milestones = ref<Milestone[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    milestones.value = await api.getMilestones()
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="panel">
    <h2 class="panel-title">里程碑</h2>

    <div v-if="loading" class="loading-state">Loading...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>

    <div v-else class="milestone-grid">
      <div v-for="ms in milestones" :key="ms.id" class="card milestone-card">
        <div class="ms-header">
          <span class="ms-id">{{ ms.id }}</span>
          <span class="ms-task-count">{{ ms.work_item_count }} work_items</span>
        </div>
        <h4 class="ms-name">{{ ms.name }}</h4>
        <p class="ms-desc">{{ ms.description }}</p>
        <div class="progress-bar-wrapper">
          <div class="progress-bar" :style="{ width: ms.progress + '%' }">
            {{ ms.progress.toFixed(0) }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  max-width: 960px;
}

.panel-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
}

.loading-state,
.error-state {
  padding: 32px;
  text-align: center;
}

.error-state {
  color: #c0392b;
}

.card {
  background: var(--color-card-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px var(--color-card-shadow);
}

.milestone-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.ms-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ms-id {
  font-size: 12px;
  font-family: monospace;
  opacity: 0.6;
}

.ms-task-count {
  font-size: 13px;
  color: var(--color-accent);
  font-weight: 600;
}

.ms-name {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 6px;
}

.ms-desc {
  font-size: 14px;
  opacity: 0.75;
  margin-bottom: 12px;
  line-height: 1.5;
}

.progress-bar-wrapper {
  background: var(--color-border);
  border-radius: 6px;
  height: 22px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: var(--color-accent);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  min-width: fit-content;
  padding: 0 8px;
  transition: width 0.4s ease;
}
</style>
