<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api/client'
import type { TimelineItem } from '@/types'

const items = ref<TimelineItem[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    items.value = await api.getTimeline()
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
})

function statusColor(status: string): string {
  switch (status) {
    case 'completed': return '#8BA870'
    case 'in_progress': return '#CC8B3A'
    case 'blocked': return '#c0392b'
    case 'pending': return '#E8DED4'
    default: return '#E8DED4'
  }
}

function formatDate(d: string | null): string {
  if (!d) return '--'
  return new Date(d).toLocaleDateString('zh-CN')
}
</script>

<template>
  <div class="panel">
    <h2 class="panel-title">时间线</h2>

    <div v-if="loading" class="loading-state">Loading...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>

    <div v-else class="timeline">
      <div v-for="item in items" :key="item.id" class="timeline-item">
        <div class="timeline-dot" :style="{ background: statusColor(item.status) }"></div>
        <div class="timeline-content card">
          <div class="tl-header">
            <span class="tl-title">{{ item.title }}</span>
            <span class="tl-status" :style="{ color: statusColor(item.status) }">{{ item.status }}</span>
          </div>
          <div class="tl-meta">
            <span>{{ item.module }}</span>
            <span>{{ item.direction }}</span>
            <span>{{ item.progress.toFixed(0) }}%</span>
          </div>
          <div class="tl-dates">
            <span>Start: {{ formatDate(item.start_date) }}</span>
            <span>End: {{ formatDate(item.end_date) }}</span>
          </div>
          <div class="tl-hours">
            <span>Est: {{ item.estimated_hours }}h</span>
            <span>Spent: {{ item.spent_hours }}h</span>
          </div>
        </div>
      </div>

      <div v-if="items.length === 0" class="empty-state">No timeline items yet.</div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  max-width: 800px;
}

.panel-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
}

.loading-state,
.error-state,
.empty-state {
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
  padding: 16px 20px;
  box-shadow: 0 1px 3px var(--color-card-shadow);
}

.timeline {
  position: relative;
  padding-left: 28px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--color-border);
}

.timeline-item {
  position: relative;
  margin-bottom: 16px;
}

.timeline-dot {
  position: absolute;
  left: -24px;
  top: 20px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--color-card-bg);
  z-index: 1;
}

.tl-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.tl-title {
  font-weight: 600;
  font-size: 15px;
}

.tl-status {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.tl-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  opacity: 0.7;
  margin-bottom: 4px;
}

.tl-dates {
  display: flex;
  gap: 16px;
  font-size: 13px;
  opacity: 0.6;
  margin-bottom: 4px;
}

.tl-hours {
  display: flex;
  gap: 16px;
  font-size: 13px;
  opacity: 0.6;
}
</style>
