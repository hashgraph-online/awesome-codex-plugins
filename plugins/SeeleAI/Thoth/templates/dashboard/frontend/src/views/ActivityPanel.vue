<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api/client'
import type { ActivityEvent } from '@/types'

const events = ref<ActivityEvent[]>([])
const loading = ref(true)
const error = ref('')
const limit = ref(50)

onMounted(async () => {
  await loadActivity()
})

async function loadActivity() {
  loading.value = true
  error.value = ''
  try {
    events.value = await api.getActivity(limit.value)
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
}

function formatTime(ts: string): string {
  return new Date(ts).toLocaleString('zh-CN')
}

function verdictClass(verdict: string | null): string {
  if (!verdict) return ''
  return 'verdict-' + verdict
}
</script>

<template>
  <div class="panel">
    <h2 class="panel-title">活动</h2>

    <div v-if="loading" class="loading-state">Loading...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>

    <template v-else>
      <div class="event-count">{{ events.length }} events</div>

      <div class="event-list">
        <div v-for="ev in events" :key="ev.id" class="card event-card">
          <div class="ev-header">
            <span class="ev-task-title">{{ ev.work_title }}</span>
            <span v-if="ev.verdict" class="ev-verdict" :class="verdictClass(ev.verdict)">
              {{ ev.verdict }}
            </span>
          </div>
          <div class="ev-meta">
            <span>{{ ev.module }}</span>
            <span>{{ ev.direction }}</span>
            <span class="ev-time">{{ formatTime(ev.created_at) }}</span>
          </div>
          <p v-if="ev.conclusion_text" class="ev-conclusion">{{ ev.conclusion_text }}</p>
        </div>
      </div>

      <div v-if="events.length === 0" class="empty-state">No activity events yet.</div>
    </template>
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

.event-count {
  font-size: 14px;
  opacity: 0.6;
  margin-bottom: 12px;
}

.card {
  background: var(--color-card-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 10px;
  box-shadow: 0 1px 3px var(--color-card-shadow);
}

.ev-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.ev-task-title {
  font-weight: 600;
  font-size: 15px;
}

.ev-verdict {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 10px;
  border-radius: 12px;
}

.verdict-confirmed {
  background: #D4EDDA;
  color: #155724;
}

.verdict-rejected {
  background: #F8D7DA;
  color: #721C24;
}

.verdict-partial {
  background: #FFF3CD;
  color: #856404;
}

.ev-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  opacity: 0.7;
  margin-bottom: 6px;
}

.ev-time {
  margin-left: auto;
}

.ev-conclusion {
  font-size: 14px;
  line-height: 1.5;
  margin-top: 6px;
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
}
</style>
