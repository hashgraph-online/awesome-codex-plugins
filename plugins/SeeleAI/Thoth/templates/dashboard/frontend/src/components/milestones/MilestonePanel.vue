<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api/client'
import type { Milestone } from '@/types/index'
import ProgressBar from '@/components/common/ProgressBar.vue'
import LoadingState from '@/components/common/LoadingState.vue'

const loading = ref(true)
const error = ref('')
const milestones = ref<Milestone[]>([])

async function load() {
  loading.value = true
  error.value = ''
  try {
    milestones.value = await api.getMilestones()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
defineExpose({ reload: load })
</script>

<template>
  <div class="milestone-panel">
    <LoadingState v-if="loading" />
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <div v-else-if="!milestones.length" class="empty-hint">暂无里程碑</div>
    <div v-else class="ms-grid">
      <div v-for="ms in milestones" :key="ms.id" class="ms-card">
        <div class="ms-header">
          <h3 class="ms-name">{{ ms.name }}</h3>
          <span class="ms-task-count">{{ ms.work_item_count }} 项任务</span>
        </div>
        <p v-if="ms.description" class="ms-desc">{{ ms.description }}</p>
        <ProgressBar :value="ms.progress" :height="8" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.milestone-panel {
  padding: 24px;
  max-width: 1200px;
}

.error-msg {
  color: #a4262c;
  text-align: center;
  padding: 40px;
}
.empty-hint {
  color: var(--text-secondary, #6b5b4e);
  text-align: center;
  padding: 60px 0;
  font-size: 14px;
}

.ms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.ms-card {
  background: var(--bg-card, #ffffff);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(44, 24, 16, 0.06);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ms-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.ms-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #2C1810);
}

.ms-task-count {
  font-size: 12px;
  color: var(--text-secondary, #6b5b4e);
  flex-shrink: 0;
  padding: 2px 8px;
  background: var(--bg-secondary, #f0ebe4);
  border-radius: 999px;
}

.ms-desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary, #6b5b4e);
  line-height: 1.5;
}
</style>
