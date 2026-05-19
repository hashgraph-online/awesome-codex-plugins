<script setup lang="ts">
import { ref, onMounted, computed, onBeforeUnmount } from 'vue'
import { api } from '@/api/client'
import type { ProgressData } from '@/types'

const progress = ref<ProgressData | null>(null)
const loading = ref(true)
const error = ref('')
let pollHandle: number | null = null
const DEFAULT_POLL_MS = 10 * 60 * 1000
const parsedPollMs = Number(import.meta.env.VITE_THOTH_DASHBOARD_POLL_MS ?? DEFAULT_POLL_MS)
const pollMs = Number.isFinite(parsedPollMs) && parsedPollMs >= 250 ? parsedPollMs : DEFAULT_POLL_MS

async function loadProgress() {
  try {
    progress.value = await api.getProgress()
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadProgress()
  pollHandle = window.setInterval(loadProgress, pollMs)
})

onBeforeUnmount(() => {
  if (pollHandle != null) {
    window.clearInterval(pollHandle)
  }
})

function statusLabel(key: string): string {
  const map: Record<string, string> = {
    total: 'Total',
    pending: 'Pending',
    in_progress: 'In Progress',
    completed: 'Completed',
    blocked: 'Blocked',
  }
  return map[key] ?? key
}

const directionEntries = computed(() => {
  if (!progress.value) return []
  return Object.entries(progress.value.by_direction).map(([dir, pct]) => ({
    direction: dir,
    progress: pct,
  }))
})
</script>

<template>
  <div class="panel">
    <h2 class="panel-title">总览</h2>

    <div v-if="loading" class="loading-state">Loading...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>

    <template v-else-if="progress">
      <!-- Overall progress -->
      <section class="card progress-overview">
        <h3>Overall Progress</h3>
        <div class="progress-bar-wrapper">
          <div class="progress-bar" :style="{ width: progress.overall_progress + '%' }">
            {{ progress.overall_progress.toFixed(1) }}%
          </div>
        </div>
      </section>

      <!-- Status counts -->
      <section class="card status-grid">
        <h3>WorkItem Status</h3>
        <div class="status-items">
          <div
            v-for="(count, key) in progress.status_counts"
            :key="key"
            class="status-item"
          >
            <span class="status-count">{{ count }}</span>
            <span class="status-label">{{ statusLabel(String(key)) }}</span>
          </div>
        </div>
      </section>

      <section class="card">
        <h3>Runtime Overview</h3>
        <div class="estimation-grid">
          <div class="est-item">
            <span class="est-value">{{ progress.runtime.active_run_count }}</span>
            <span class="est-label">Active Runs</span>
          </div>
          <div class="est-item">
            <span class="est-value">{{ progress.runtime.stale_run_count }}</span>
            <span class="est-label">Stale Runs</span>
          </div>
          <div class="est-item">
            <span class="est-value">{{ progress.runtime.progress_source }}</span>
            <span class="est-label">Progress Source</span>
          </div>
        </div>
        <p v-if="progress.runtime.last_runtime_update" class="est-message">
          Last runtime update: {{ progress.runtime.last_runtime_update }}
        </p>
        <div v-if="progress.runtime.active_runs.length" class="active-run-list">
          <div v-for="run in progress.runtime.active_runs" :key="run.run_id" class="active-run-row">
            <strong>{{ run.work_id }}</strong>
            <span>{{ run.host || 'unknown-host' }}</span>
            <span>{{ run.executor || 'unknown-executor' }}</span>
            <span>{{ run.status }}</span>
            <span>{{ run.supervisor_state || 'unknown-supervisor' }}</span>
            <span>{{ run.progress_pct.toFixed(0) }}%</span>
            <span>{{ run.latest_message || run.phase || 'No recent message' }}</span>
          </div>
        </div>
      </section>

      <!-- Direction breakdown -->
      <section class="card">
        <h3>By Direction</h3>
        <div class="direction-list">
          <div v-for="d in directionEntries" :key="d.direction" class="direction-row">
            <span class="direction-label">{{ d.direction }}</span>
            <div class="progress-bar-wrapper small">
              <div class="progress-bar" :style="{ width: d.progress + '%' }">
                {{ d.progress.toFixed(0) }}%
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Blocked work items -->
      <section v-if="progress.blocked_work_items.length > 0" class="card blocked-section">
        <h3>Blocked Work Items</h3>
        <ul class="blocked-list">
          <li v-for="bt in progress.blocked_work_items" :key="bt.id">
            <strong>{{ bt.title }}</strong>
            <span class="blocked-reason">Blocked by: {{ bt.blocked_by.join(', ') }}</span>
          </li>
        </ul>
      </section>

      <!-- Estimation -->
      <section v-if="progress.estimation" class="card">
        <h3>Estimation</h3>
        <div class="estimation-grid">
          <div class="est-item">
            <span class="est-value">{{ progress.estimation.completed_work_items }}/{{ progress.estimation.total_work_items }}</span>
            <span class="est-label">Work Items Completed</span>
          </div>
          <div class="est-item">
            <span class="est-value">{{ progress.estimation.elapsed_days }}d</span>
            <span class="est-label">Elapsed</span>
          </div>
          <div v-if="progress.estimation.estimated_days_remaining !== null" class="est-item">
            <span class="est-value">{{ progress.estimation.estimated_days_remaining }}d</span>
            <span class="est-label">Est. Remaining</span>
          </div>
        </div>
        <p v-if="progress.estimation.message" class="est-message">{{ progress.estimation.message }}</p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.panel {
  max-width: 960px;
}

.panel-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 20px;
}

.loading-state,
.error-state {
  padding: 32px;
  text-align: center;
  color: var(--color-accent);
}

.error-state {
  color: #c0392b;
}

.card {
  background: var(--color-card-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px var(--color-card-shadow);
}

.card h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-text);
}

/* Progress bars */
.progress-bar-wrapper {
  background: var(--color-border);
  border-radius: 6px;
  height: 28px;
  overflow: hidden;
}

.progress-bar-wrapper.small {
  height: 20px;
  flex: 1;
}

.progress-bar {
  height: 100%;
  background: var(--color-accent);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  min-width: fit-content;
  padding: 0 8px;
  transition: width 0.4s ease;
}

/* Status grid */
.status-items {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 80px;
  padding: 12px 16px;
  background: var(--color-bg);
  border-radius: 8px;
}

.status-count {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-accent);
}

.status-label {
  font-size: 12px;
  color: var(--color-text);
  opacity: 0.7;
  margin-top: 4px;
}

/* Direction list */
.direction-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.direction-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.direction-label {
  font-weight: 600;
  min-width: 140px;
}

/* Blocked */
.blocked-list {
  list-style: none;
}

.blocked-list li {
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.blocked-list li:last-child {
  border-bottom: none;
}

.blocked-reason {
  font-size: 13px;
  opacity: 0.7;
}

/* Estimation */
.estimation-grid {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.est-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 80px;
  padding: 12px 16px;
  background: var(--color-bg);
  border-radius: 8px;
}

.est-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-accent);
}

.est-label {
  font-size: 12px;
  opacity: 0.7;
  margin-top: 4px;
}

.est-message {
  margin-top: 12px;
  font-size: 14px;
  opacity: 0.8;
  font-style: italic;
}

.active-run-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.active-run-row {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) 120px 80px 2fr;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--color-bg);
  font-size: 13px;
}
</style>
