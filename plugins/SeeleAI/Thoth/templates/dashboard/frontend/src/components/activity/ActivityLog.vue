<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api/client'
import type { ActivityEvent } from '@/types/index'
import LoadingState from '@/components/common/LoadingState.vue'

const loading = ref(true)
const error = ref('')
const events = ref<ActivityEvent[]>([])

const verdictConfig: Record<string, { label: string; color: string; icon: string }> = {
  confirmed:  { label: '确认', color: '#2d6a4f', icon: 'M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z' },
  rejected:   { label: '否决', color: '#a4262c', icon: 'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z' },
  inconclusive: { label: '未定', color: '#CC8B3A', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z' },
}

function getVerdictInfo(verdict: string) {
  return verdictConfig[verdict] ?? { label: verdict, color: '#6b5b4e', icon: '' }
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    events.value = await api.getActivity()
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
  <div class="activity-log">
    <LoadingState v-if="loading" />
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <div v-else-if="!events.length" class="empty-hint">暂无活动记录</div>
    <div v-else class="timeline">
      <div v-for="ev in events" :key="ev.id" class="timeline-item">
        <div class="timeline-line">
          <div
            class="timeline-dot"
            :style="{ backgroundColor: getVerdictInfo(ev.verdict).color }"
          >
            <svg v-if="getVerdictInfo(ev.verdict).icon" viewBox="0 0 24 24" width="12" height="12">
              <path :d="getVerdictInfo(ev.verdict).icon" fill="#fff" />
            </svg>
          </div>
        </div>
        <div class="timeline-content">
          <div class="event-header">
            <span
              class="verdict-badge"
              :style="{
                backgroundColor: getVerdictInfo(ev.verdict).color + '18',
                color: getVerdictInfo(ev.verdict).color,
              }"
            >
              {{ getVerdictInfo(ev.verdict).label }}
            </span>
            <span class="event-time">{{ formatTime(ev.created_at) }}</span>
          </div>
          <div class="event-title">{{ ev.work_title }}</div>
          <div class="event-meta">
            <span class="meta-tag">{{ ev.direction }}</span>
            <span class="meta-tag">{{ ev.module }}</span>
            <span class="meta-id">{{ ev.work_id }}</span>
          </div>
          <div v-if="ev.conclusion_text" class="event-conclusion">
            {{ ev.conclusion_text }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.activity-log {
  padding: 24px;
  max-width: 800px;
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

/* ── Timeline ─── */
.timeline {
  display: flex;
  flex-direction: column;
}

.timeline-item {
  display: flex;
  gap: 16px;
  position: relative;
}

.timeline-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
}

.timeline-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 1;
}

/* Vertical connector line */
.timeline-item:not(:last-child) .timeline-line::after {
  content: '';
  width: 2px;
  flex: 1;
  background: var(--bg-secondary, #f0ebe4);
  margin-top: 4px;
}

.timeline-content {
  flex: 1;
  background: var(--bg-card, #ffffff);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(44, 24, 16, 0.06);
  padding: 14px 18px;
  margin-bottom: 12px;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.verdict-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 999px;
}

.event-time {
  font-size: 12px;
  color: var(--text-secondary, #6b5b4e);
}

.event-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #2C1810);
  margin-bottom: 6px;
}

.event-meta {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.meta-tag {
  font-size: 11px;
  padding: 1px 8px;
  background: var(--bg-secondary, #f0ebe4);
  border-radius: 4px;
  color: var(--text-secondary, #6b5b4e);
}

.meta-id {
  font-size: 11px;
  color: var(--accent, #CC8B3A);
  font-family: monospace;
  font-weight: 600;
}

.event-conclusion {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary, #6b5b4e);
  line-height: 1.5;
  border-left: 3px solid var(--bg-secondary, #f0ebe4);
  padding-left: 10px;
}
</style>
