<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { api } from '@/api/client'
import type { WorkItem, WorkItemFilters } from '@/types/index'
import ProgressBar from '@/components/common/ProgressBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingState from '@/components/common/LoadingState.vue'

const loading = ref(true)
const error = ref('')
const work_items = ref<WorkItem[]>([])
const total = ref(0)
const expandedId = ref<string | null>(null)

/* Filters */
const filterDirection = ref('')
const filterStatus = ref<string>('')
const filterModule = ref('')
const page = ref(0)
const pageSize = 20

const filters = (): WorkItemFilters => ({
  direction: filterDirection.value || undefined,
  status: (filterStatus.value as WorkItemFilters['status']) || undefined,
  module: filterModule.value || undefined,
  limit: pageSize,
  offset: page.value * pageSize,
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getWorkItems(filters())
    work_items.value = res.work_items
    total.value = res.total
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

function resetFilters() {
  filterDirection.value = ''
  filterStatus.value = ''
  filterModule.value = ''
  page.value = 0
}

const totalPages = () => Math.ceil(total.value / pageSize)

watch([filterDirection, filterStatus, filterModule], () => {
  page.value = 0
  load()
})
watch(page, load)

onMounted(load)
defineExpose({ reload: load })

const phaseLabels: Record<string, string> = {
  survey: '调研',
  method_design: '方法设计',
  experiment: '实验',
  conclusion: '结论',
}
</script>

<template>
  <div class="task-board">
    <!-- Filter bar -->
    <div class="filter-bar">
      <input
        v-model="filterDirection"
        class="filter-input"
        placeholder="方向 (direction)"
      />
      <select v-model="filterStatus" class="filter-select">
        <option value="">全部状态</option>
        <option value="pending">待开始</option>
        <option value="in_progress">进行中</option>
        <option value="completed">已完成</option>
        <option value="blocked">已阻塞</option>
        <option value="ready">可执行</option>
        <option value="invalid">无效</option>
        <option value="failed">失败</option>
      </select>
      <input
        v-model="filterModule"
        class="filter-input"
        placeholder="模块 (module)"
      />
      <button class="btn-secondary" @click="resetFilters">重置</button>
      <span class="result-count">共 {{ total }} 条</span>
    </div>

    <LoadingState v-if="loading" />
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else>
      <div v-if="!work_items.length" class="empty-hint">无匹配工作项</div>

      <div class="task-list">
        <div
          v-for="task in work_items"
          :key="task.id"
          class="task-card"
          :class="{ expanded: expandedId === task.id }"
          @click="toggleExpand(task.id)"
        >
          <!-- Summary row -->
          <div class="task-summary">
            <span class="task-id">{{ task.id }}</span>
            <span class="task-title">{{ task.title }}</span>
            <span class="task-direction-badge">{{ task.direction }}</span>
            <StatusBadge :status="task.computed_status" />
            <div class="task-progress">
              <ProgressBar :value="task.computed_progress" :height="6" />
            </div>
            <span class="task-module">{{ task.module }}</span>
          </div>

          <!-- Expanded detail -->
          <div v-if="expandedId === task.id" class="task-detail" @click.stop>
            <div v-if="task.hypothesis || task.goal_statement" class="detail-section">
              <strong>{{ task.hypothesis ? '假设' : '目标' }}：</strong>{{ task.hypothesis ?? task.goal_statement }}
            </div>

            <div v-if="task.phases" class="detail-section">
              <strong>阶段：</strong>
              <div class="phases-grid">
                <div
                  v-for="(phase, pname) in task.phases"
                  :key="pname"
                  class="phase-item"
                >
                  <span class="phase-name">{{ phaseLabels[pname] ?? pname }}</span>
                  <StatusBadge :status="phase?.status || 'pending'" />
                </div>
              </div>
            </div>

            <div v-if="task.deliverables?.length" class="detail-section">
              <strong>产物：</strong>
              <ul class="deliverable-list">
                <li v-for="(d, i) in task.deliverables" :key="i">
                  <code>{{ d.path }}</code> — {{ d.description }}
                </li>
              </ul>
            </div>

            <div v-if="task.depends_on?.length" class="detail-section">
              <strong>依赖：</strong>
              <span v-for="dep in task.depends_on" :key="dep.work_id" class="dep-chip">
                {{ dep.work_id }} ({{ dep.type }})
              </span>
            </div>

            <div v-if="task.ready_state" class="detail-section">
              <strong>工作项状态：</strong>{{ task.ready_state }}
              <span v-if="task.blocking_reason"> - {{ task.blocking_reason }}</span>
            </div>

            <div v-if="task.candidate_method_id" class="detail-section">
              <strong>冻结方法：</strong><code>{{ task.candidate_method_id }}</code>
            </div>

            <div v-if="task.implementation_recipe?.length" class="detail-section">
              <strong>执行配方：</strong>
              <ul class="deliverable-list">
                <li v-for="(step, i) in task.implementation_recipe" :key="i">{{ step }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages() > 1" class="pagination">
        <button :disabled="page === 0" class="btn-page" @click="page--">上一页</button>
        <span class="page-info">{{ page + 1 }} / {{ totalPages() }}</span>
        <button :disabled="page >= totalPages() - 1" class="btn-page" @click="page++">下一页</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.task-board {
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
  padding: 40px;
}

/* ── Filter bar ─── */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.filter-input,
.filter-select {
  padding: 7px 12px;
  border: 1px solid var(--border, #e8e0d6);
  border-radius: 8px;
  font-size: 13px;
  background: var(--bg-card, #ffffff);
  color: var(--text-primary, #2C1810);
  outline: none;
  transition: border-color 0.15s;
}
.filter-input:focus,
.filter-select:focus {
  border-color: var(--accent, #CC8B3A);
}

.btn-secondary {
  padding: 7px 14px;
  border: 1px solid var(--border, #e8e0d6);
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary, #6b5b4e);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-secondary:hover {
  background: var(--bg-secondary, #f0ebe4);
}

.result-count {
  margin-left: auto;
  font-size: 13px;
  color: var(--text-secondary, #6b5b4e);
}

/* ── WorkItem list ─── */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-card {
  background: var(--bg-card, #ffffff);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(44, 24, 16, 0.06);
  cursor: pointer;
  transition: box-shadow 0.15s;
  overflow: hidden;
}
.task-card:hover {
  box-shadow: 0 2px 8px rgba(44, 24, 16, 0.1);
}

.task-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
}

.task-id {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent, #CC8B3A);
  font-family: monospace;
  flex-shrink: 0;
}

.task-title {
  font-size: 14px;
  color: var(--text-primary, #2C1810);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-direction-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(204, 139, 58, 0.12);
  color: var(--accent, #CC8B3A);
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.task-progress {
  width: 120px;
  flex-shrink: 0;
}

.task-module {
  font-size: 12px;
  color: var(--text-secondary, #6b5b4e);
  flex-shrink: 0;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Expanded detail ─── */
.task-detail {
  padding: 0 18px 16px;
  border-top: 1px solid var(--border, #e8e0d6);
  cursor: default;
}

.detail-section {
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-primary, #2C1810);
  line-height: 1.6;
}

.phases-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}

.phase-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.phase-name {
  font-size: 13px;
  color: var(--text-secondary, #6b5b4e);
}

.deliverable-list {
  margin: 6px 0 0 16px;
  padding: 0;
  font-size: 13px;
}
.deliverable-list code {
  font-size: 12px;
  background: var(--bg-secondary, #f0ebe4);
  padding: 1px 5px;
  border-radius: 4px;
}

.dep-chip {
  display: inline-block;
  margin: 4px 6px 0 0;
  padding: 2px 8px;
  font-size: 12px;
  background: var(--bg-secondary, #f0ebe4);
  border-radius: 6px;
  font-family: monospace;
}

/* ── Pagination ─── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
}

.btn-page {
  padding: 6px 14px;
  border: 1px solid var(--border, #e8e0d6);
  border-radius: 8px;
  background: var(--bg-card, #ffffff);
  color: var(--text-primary, #2C1810);
  font-size: 13px;
  cursor: pointer;
}
.btn-page:disabled {
  opacity: 0.4;
  cursor: default;
}

.page-info {
  font-size: 13px;
  color: var(--text-secondary, #6b5b4e);
}
</style>
