<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { api } from '@/api/client'
import type { RunEvent, RunSummary, WorkItem, WorkItemListResponse, WorkItemFilters, WorkItemStatus } from '@/types'

const work_items = ref<WorkItem[]>([])
const total = ref(0)
const offset = ref(0)
const limit = ref(20)
const filterDirection = ref('')
const filterStatus = ref<WorkItemStatus | ''>('')
const loading = ref(true)
const error = ref('')
const expandedId = ref<string | null>(null)
const workItemRuns = ref<Record<string, RunSummary[]>>({})
const activeRuns = ref<Record<string, RunSummary | null>>({})
const runEvents = ref<Record<string, RunEvent[]>>({})
const runEventCursor = ref<Record<string, number | null>>({})
const detailLoading = ref<Record<string, boolean>>({})
let pollHandle: number | null = null
const DEFAULT_POLL_MS = 10 * 60 * 1000
const parsedPollMs = Number(import.meta.env.VITE_THOTH_DASHBOARD_POLL_MS ?? DEFAULT_POLL_MS)
const pollMs = Number.isFinite(parsedPollMs) && parsedPollMs >= 250 ? parsedPollMs : DEFAULT_POLL_MS

async function loadWorkItems() {
  loading.value = true
  error.value = ''
  try {
    const filters: WorkItemFilters = {
      offset: offset.value,
      limit: limit.value,
    }
    if (filterDirection.value) filters.direction = filterDirection.value
    if (filterStatus.value) filters.status = filterStatus.value
    const res: WorkItemListResponse = await api.getWorkItems(filters)
    work_items.value = res.work_items
    total.value = res.total
    for (const workItem of res.work_items) {
      activeRuns.value[workItem.id] = workItem.active_run ?? null
    }
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
}

async function loadWorkItemRuntime(workId: string) {
  detailLoading.value[workId] = true
  try {
    const [activeRun, runsPayload] = await Promise.all([
      api.getWorkItemActiveRun(workId),
      api.getWorkItemRuns(workId),
    ])
    activeRuns.value[workId] = activeRun
    workItemRuns.value[workId] = runsPayload.runs

    const displayRunId = activeRun?.run_id ?? runsPayload.runs[0]?.run_id
    if (!displayRunId) {
      runEvents.value[workId] = []
      runEventCursor.value[workId] = null
      return
    }
    const eventsPayload = await api.getRunEvents(displayRunId, null, 50)
    runEvents.value[workId] = eventsPayload.events
    runEventCursor.value[workId] = eventsPayload.next_after_seq ?? null
  } catch (e) {
    error.value = String(e)
  } finally {
    detailLoading.value[workId] = false
  }
}

async function refreshExpandedWorkItemRuntime() {
  if (!expandedId.value) return
  const workId = expandedId.value
  await loadWorkItemRuntime(workId)
  const runId = activeRuns.value[workId]?.run_id
  const afterSeq = runEventCursor.value[workId]
  if (!runId || afterSeq == null) return
  const delta = await api.getRunEvents(runId, afterSeq, 100)
  if (delta.events.length) {
    runEvents.value[workId] = [...(runEvents.value[workId] ?? []), ...delta.events].slice(-200)
    runEventCursor.value[workId] = delta.next_after_seq ?? runEventCursor.value[workId]
  }
}

function prevPage() {
  if (offset.value > 0) {
    offset.value = Math.max(0, offset.value - limit.value)
    loadWorkItems()
  }
}

function nextPage() {
  if (offset.value + limit.value < total.value) {
    offset.value += limit.value
    loadWorkItems()
  }
}

function applyFilters() {
  offset.value = 0
  loadWorkItems()
}

async function toggleExpand(workId: string) {
  expandedId.value = expandedId.value === workId ? null : workId
  if (expandedId.value === workId) {
    await loadWorkItemRuntime(workId)
  }
}

function statusClass(status: string): string {
  return 'status-badge status-' + status.replace(/_/g, '-')
}

function runtimeStatusClass(status?: string | null): string {
  return 'runtime-status runtime-' + (status || 'unknown').replace(/_/g, '-')
}

function formatTime(value?: string | null): string {
  if (!value) return 'N/A'
  return new Date(value).toLocaleString('zh-CN')
}

onMounted(async () => {
  await loadWorkItems()
  pollHandle = window.setInterval(async () => {
    await loadWorkItems()
    await refreshExpandedWorkItemRuntime()
  }, pollMs)
})

onBeforeUnmount(() => {
  if (pollHandle != null) {
    window.clearInterval(pollHandle)
  }
})
</script>

<template>
  <div class="panel">
    <h2 class="panel-title">Work Items</h2>

    <div class="filters card">
      <input
        v-model="filterDirection"
        placeholder="Filter by direction..."
        class="filter-input"
        @keydown.enter="applyFilters"
      />
      <select v-model="filterStatus" class="filter-select" @change="applyFilters">
        <option value="">All statuses</option>
        <option value="pending">Pending</option>
        <option value="in_progress">In Progress</option>
        <option value="completed">Completed</option>
        <option value="blocked">Blocked</option>
      </select>
      <button class="filter-btn" @click="applyFilters">Filter</button>
    </div>

    <div v-if="loading" class="loading-state">Loading...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>

    <template v-else>
      <div class="task-count">{{ total }} work items found</div>

      <div class="task-list">
        <div v-for="task in work_items" :key="task.id" class="card task-card">
          <div class="task-header" @click="toggleExpand(task.id)">
            <span class="task-id">{{ task.id }}</span>
            <span :class="statusClass(task.computed_status)">{{ task.computed_status }}</span>
          </div>
          <h4 class="task-title">{{ task.title }}</h4>
          <div class="task-meta">
            <span>Module: {{ task.module }}</span>
            <span>Direction: {{ task.direction }}</span>
            <span>Progress: {{ task.computed_progress.toFixed(0) }}%</span>
            <span>Runs: {{ task.run_count ?? 0 }}</span>
          </div>
          <p v-if="task.hypothesis" class="task-hypothesis">{{ task.hypothesis }}</p>

          <div class="runtime-card">
            <template v-if="activeRuns[task.id]">
              <div class="runtime-head">
                <strong>Active Run</strong>
                <span :class="runtimeStatusClass(activeRuns[task.id]?.status)">
                  {{ activeRuns[task.id]?.status }}
                </span>
              </div>
              <div class="runtime-meta">
                <span>Run: {{ activeRuns[task.id]?.run_id }}</span>
                <span>Host: {{ activeRuns[task.id]?.host || 'unknown' }}</span>
                <span>Executor: {{ activeRuns[task.id]?.executor || 'unknown' }}</span>
                <span>Phase: {{ activeRuns[task.id]?.phase || 'unknown' }}</span>
                <span>Supervisor: {{ activeRuns[task.id]?.supervisor_state || 'unknown' }}</span>
                <span>Freshness: {{ activeRuns[task.id]?.is_stale ? 'stale' : 'fresh' }}</span>
                <span>Runtime Progress: {{ activeRuns[task.id]?.progress_pct.toFixed(0) }}%</span>
              </div>
              <div class="runtime-message">
                {{ activeRuns[task.id]?.latest_message || 'No recent runtime message.' }}
              </div>
            </template>
            <template v-else>
              <div class="runtime-empty">No bound runs yet.</div>
            </template>
          </div>

          <div v-if="expandedId === task.id" class="runtime-detail">
            <div v-if="detailLoading[task.id]" class="loading-state compact">Loading runtime details...</div>
            <template v-else>
              <div class="history-section">
                <h5>Run History</h5>
                <div v-if="(workItemRuns[task.id] || []).length" class="history-list">
                  <div v-for="run in workItemRuns[task.id]" :key="run.run_id" class="history-row">
                    <span>{{ run.run_id }}</span>
                    <span>{{ run.status }}</span>
                    <span>{{ run.progress_pct.toFixed(0) }}%</span>
                    <span>{{ formatTime(run.last_updated_at) }}</span>
                  </div>
                </div>
                <div v-else class="runtime-empty">No run history available.</div>
              </div>

              <div class="history-section">
                <h5>Recent Logs</h5>
                <div v-if="(runEvents[task.id] || []).length" class="log-list">
                  <div v-for="event in runEvents[task.id]" :key="`${task.id}-${event.seq}`" class="log-row">
                    <span class="log-seq">#{{ event.seq }}</span>
                    <span class="log-kind">{{ event.kind }}</span>
                    <span class="log-ts">{{ formatTime(event.ts) }}</span>
                    <span class="log-msg">{{ event.message || '(empty event)' }}</span>
                  </div>
                </div>
                <div v-else class="runtime-empty">No runtime events yet.</div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <div class="pagination">
        <button :disabled="offset === 0" @click="prevPage" class="page-btn">Previous</button>
        <span class="page-info">{{ offset + 1 }}-{{ Math.min(offset + limit, total) }} of {{ total }}</span>
        <button :disabled="offset + limit >= total" @click="nextPage" class="page-btn">Next</button>
      </div>
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
  padding: 16px 20px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px var(--color-card-shadow);
}

.filters {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-input {
  flex: 1;
  min-width: 160px;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
  background: var(--color-bg);
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
  background: var(--color-bg);
}

.filter-btn {
  padding: 8px 20px;
  background: var(--color-accent);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
}

.task-count {
  font-size: 14px;
  opacity: 0.6;
  margin-bottom: 12px;
}

.task-card {
  transition: box-shadow 0.15s;
}

.task-card:hover {
  box-shadow: 0 2px 8px var(--color-card-shadow);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  cursor: pointer;
}

.task-id {
  font-size: 12px;
  font-family: monospace;
  opacity: 0.6;
}

.status-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
  text-transform: uppercase;
}

.status-pending { background: var(--color-border); color: var(--color-text); }
.status-in-progress { background: #FFF3CD; color: #856404; }
.status-completed { background: #D4EDDA; color: #155724; }
.status-blocked { background: #F8D7DA; color: #721C24; }

.task-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.task-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  opacity: 0.7;
  flex-wrap: wrap;
}

.task-hypothesis {
  margin-top: 8px;
  font-size: 14px;
  font-style: italic;
  opacity: 0.8;
}

.runtime-card {
  margin-top: 12px;
  padding: 12px;
  border-radius: 8px;
  background: var(--color-bg);
}

.runtime-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.runtime-meta {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 13px;
  opacity: 0.76;
}

.runtime-message,
.runtime-empty {
  margin-top: 8px;
  font-size: 13px;
  opacity: 0.85;
}

.runtime-status {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.runtime-running,
.runtime-queued,
.runtime-waiting-input,
.runtime-paused {
  color: #856404;
}

.runtime-completed {
  color: #155724;
}

.runtime-failed,
.runtime-cancelled,
.runtime-stopped {
  color: #721c24;
}

.runtime-detail {
  margin-top: 12px;
  border-top: 1px solid var(--color-border);
  padding-top: 12px;
}

.history-section {
  margin-top: 10px;
}

.history-section h5 {
  margin-bottom: 8px;
  font-size: 14px;
}

.history-list,
.log-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-row,
.log-row {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 8px 10px;
  border-radius: 6px;
  background: #fff;
  font-size: 12px;
  overflow-x: auto;
}

.log-seq,
.log-kind,
.log-ts {
  white-space: nowrap;
  color: #6b5b4e;
}

.compact {
  padding: 16px 0;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
}

.page-btn {
  padding: 6px 16px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
</style>
