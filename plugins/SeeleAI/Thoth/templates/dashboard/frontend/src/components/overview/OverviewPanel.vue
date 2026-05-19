<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api/client'
import type { ProgressData, WorkItem } from '@/types/index'
import ProgressBar from '@/components/common/ProgressBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingState from '@/components/common/LoadingState.vue'

const loading = ref(true)
const error = ref('')
const progress = ref<ProgressData | null>(null)
const decisionTasks = ref<WorkItem[]>([])

const overallPct = computed(() => progress.value?.overall_progress ?? 0)
const counts = computed(() => progress.value?.status_counts ?? { total: 0, pending: 0, in_progress: 0, completed: 0, blocked: 0 })
const estDays = computed(() => progress.value?.estimation?.estimated_days_remaining)

/* SVG progress ring helpers */
const ringRadius = 54
const ringCircumference = 2 * Math.PI * ringRadius
const ringOffset = computed(() => ringCircumference * (1 - overallPct.value / 100))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [p, blockedRes] = await Promise.all([
      api.getProgress(),
      api.getWorkItems({ status: 'blocked' }),
    ])
    progress.value = p
    decisionTasks.value = blockedRes.work_items
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
  <div class="overview-panel">
    <LoadingState v-if="loading" />
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else>
      <!-- Big number cards -->
      <div class="stat-grid">
        <!-- Progress ring card -->
        <div class="stat-card ring-card">
          <svg class="progress-ring" width="130" height="130" viewBox="0 0 130 130">
            <circle
              class="ring-bg"
              cx="65" cy="65" :r="ringRadius"
              fill="none" stroke="var(--bg-secondary, #f0ebe4)" stroke-width="10"
            />
            <circle
              class="ring-fill"
              cx="65" cy="65" :r="ringRadius"
              fill="none" stroke="var(--accent, #CC8B3A)" stroke-width="10"
              stroke-linecap="round"
              :stroke-dasharray="ringCircumference"
              :stroke-dashoffset="ringOffset"
              transform="rotate(-90 65 65)"
            />
          </svg>
          <div class="ring-label">
            <span class="ring-pct">{{ Math.round(overallPct) }}<small>%</small></span>
            <span class="ring-sub">总体进度</span>
          </div>
        </div>

        <div class="stat-card">
          <span class="stat-number">{{ counts.completed }}<small> / {{ counts.total }}</small></span>
          <span class="stat-title">任务完成</span>
        </div>

        <div class="stat-card">
          <span class="stat-number accent">{{ counts.in_progress }}</span>
          <span class="stat-title">进行中</span>
        </div>

        <div class="stat-card">
          <span class="stat-number danger">{{ counts.blocked }}</span>
          <span class="stat-title">已阻塞</span>
        </div>

        <div class="stat-card">
          <span class="stat-number">{{ estDays != null ? `~${estDays}` : '--' }}</span>
          <span class="stat-title">预计剩余天数</span>
        </div>
      </div>

      <!-- Direction progress -->
      <div v-if="progress?.by_direction" class="section">
        <h3 class="section-title">研究方向进度</h3>
        <div class="direction-list">
          <div
            v-for="(pct, dir) in progress.by_direction"
            :key="dir"
            class="direction-row"
          >
            <span class="dir-name">{{ dir }}</span>
            <ProgressBar :value="pct" />
          </div>
        </div>
      </div>

      <!-- Decision queue -->
      <div class="section">
        <h3 class="section-title">
          决策队列
          <span v-if="decisionTasks.length" class="badge">{{ decisionTasks.length }}</span>
        </h3>
        <div v-if="!decisionTasks.length" class="empty-hint">暂无需要人工决策的任务</div>
        <div v-else class="decision-list">
          <div v-for="task in decisionTasks" :key="task.id" class="decision-item">
            <div class="decision-header">
              <span class="task-id">{{ task.id }}</span>
              <StatusBadge :status="task.computed_status" />
            </div>
            <span class="task-title">{{ task.title }}</span>
            <ProgressBar :value="task.computed_progress" :height="6" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.overview-panel {
  padding: 24px;
  max-width: 1200px;
}

.error-msg {
  color: #a4262c;
  text-align: center;
  padding: 40px;
}

/* ── Stat Grid ─── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--bg-card, #ffffff);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(44, 24, 16, 0.06);
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.ring-card {
  position: relative;
  grid-row: span 1;
  justify-content: center;
}

.progress-ring {
  display: block;
}

.ring-fill {
  transition: stroke-dashoffset 0.6s ease;
}

.ring-label {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.ring-pct {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary, #2C1810);
}
.ring-pct small {
  font-size: 16px;
  font-weight: 500;
}

.ring-sub {
  font-size: 12px;
  color: var(--text-secondary, #6b5b4e);
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary, #2C1810);
  line-height: 1.1;
}
.stat-number small {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-secondary, #6b5b4e);
}
.stat-number.accent { color: var(--accent, #CC8B3A); }
.stat-number.danger { color: #a4262c; }

.stat-title {
  font-size: 13px;
  color: var(--text-secondary, #6b5b4e);
}

/* ── Sections ─── */
.section {
  margin-bottom: 28px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #2C1810);
  margin: 0 0 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.badge {
  background: var(--accent, #CC8B3A);
  color: #fff;
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 999px;
  font-weight: 600;
}

/* Direction progress */
.direction-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: var(--bg-card, #ffffff);
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 1px 4px rgba(44, 24, 16, 0.06);
}

.direction-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.dir-name {
  width: 140px;
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary, #2C1810);
}

/* Decision queue */
.empty-hint {
  color: var(--text-secondary, #6b5b4e);
  font-size: 13px;
  padding: 12px 0;
}

.decision-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.decision-item {
  background: var(--bg-card, #ffffff);
  border-radius: 12px;
  padding: 14px 18px;
  box-shadow: 0 1px 4px rgba(44, 24, 16, 0.06);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.decision-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-id {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent, #CC8B3A);
  font-family: monospace;
}

.task-title {
  font-size: 14px;
  color: var(--text-primary, #2C1810);
}
</style>
