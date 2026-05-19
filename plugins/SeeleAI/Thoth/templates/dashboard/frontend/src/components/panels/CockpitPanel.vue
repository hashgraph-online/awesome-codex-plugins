<script setup lang="ts">
import { computed } from 'vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import { locale } from '@/locales'
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const summary = computed(() => store.overviewSummary)

function openTask(taskId: string) {
  void store.selectWorkItem(taskId)
}

function activityTitle(entry: string): string {
  return entry.split('\n')[0]?.replace(/^- /, '') || entry
}
</script>

<template>
  <section class="cockpit">
    <div class="cockpit__hero card">
      <div>
        <p class="cockpit__eyebrow">{{ locale.cockpit.title }}</p>
        <h2 class="cockpit__title">{{ summary?.project?.name || locale.brand }}</h2>
        <p class="cockpit__description">
          {{ summary?.project?.description || 'Strict authority driven dashboard overview.' }}
        </p>
      </div>
      <div class="cockpit__hero-progress">
        <ProgressBar :value="summary?.headline.overall_progress ?? 0" />
      </div>
    </div>

    <div class="cockpit__metrics">
      <article class="card cockpit__metric">
        <span>Total</span>
        <strong>{{ summary?.headline.total_work_items ?? 0 }}</strong>
      </article>
      <article class="card cockpit__metric">
        <span>Completed</span>
        <strong>{{ summary?.headline.completed_work_items ?? 0 }}</strong>
      </article>
      <article class="card cockpit__metric">
        <span>Blocked</span>
        <strong>{{ summary?.headline.blocked_work_items ?? 0 }}</strong>
      </article>
      <article class="card cockpit__metric">
        <span>Ready</span>
        <strong>{{ summary?.headline.ready_work_items ?? 0 }}</strong>
      </article>
    </div>

    <div class="cockpit__grid">
      <article class="card cockpit__panel">
        <h3>{{ locale.cockpit.runtime }}</h3>
        <div class="cockpit__runtime-meta">
          <span>Healthy: {{ summary?.healthy ? 'yes' : 'no' }}</span>
          <span>{{ summary?.health_message }}</span>
        </div>
        <div class="cockpit__runtime-list">
          <div
            v-for="run in summary?.runtime.active_runs ?? []"
            :key="run.run_id"
            class="cockpit__runtime-item"
          >
            <div>
              <strong>{{ run.run_id }}</strong>
              <p>{{ run.work_id || 'no work item' }} · {{ run.host || 'unknown host' }}</p>
            </div>
            <span class="pill" :class="`badge-${run.is_stale ? 'blocked' : 'ready'}`">
              {{ run.phase || run.status }}
            </span>
          </div>
          <p v-if="!(summary?.runtime.active_runs?.length)" class="cockpit__empty">
            {{ locale.cockpit.empty }}
          </p>
        </div>
      </article>

      <article class="card cockpit__panel">
        <h3>{{ locale.cockpit.milestones }}</h3>
        <div class="cockpit__list">
          <button
            v-for="milestone in summary?.milestones ?? []"
            :key="milestone.id"
            class="cockpit__list-item"
          >
            <div>
              <strong>{{ milestone.name }}</strong>
              <p>{{ milestone.work_item_count }} work_items</p>
            </div>
            <span>{{ Math.round(milestone.progress) }}%</span>
          </button>
          <p v-if="!(summary?.milestones?.length)" class="cockpit__empty">
            {{ locale.cockpit.empty }}
          </p>
        </div>
      </article>

      <article class="card cockpit__panel">
        <h3>{{ locale.cockpit.conclusions }}</h3>
        <div class="cockpit__list">
          <button
            v-for="item in summary?.recent_conclusions ?? []"
            :key="item.work_id"
            class="cockpit__list-item cockpit__list-item--stack"
            @click="openTask(item.work_id)"
          >
            <div>
              <strong>{{ item.work_id }} · {{ item.title }}</strong>
              <p>{{ item.conclusion || 'No conclusion text' }}</p>
            </div>
            <span>{{ item.source || item.status }}</span>
          </button>
          <p v-if="!(summary?.recent_conclusions?.length)" class="cockpit__empty">
            {{ locale.cockpit.empty }}
          </p>
        </div>
      </article>

      <article class="card cockpit__panel">
        <h3>{{ locale.cockpit.activity }}</h3>
        <div class="cockpit__list">
          <div
            v-for="entry in summary?.recent_activity ?? []"
            :key="entry"
            class="cockpit__list-item cockpit__list-item--stack"
          >
            <strong>{{ activityTitle(entry) }}</strong>
            <pre>{{ entry }}</pre>
          </div>
          <p v-if="!(summary?.recent_activity?.length)" class="cockpit__empty">
            {{ locale.cockpit.empty }}
          </p>
        </div>
      </article>

      <article class="card cockpit__panel">
        <h3>{{ locale.cockpit.blockers }}</h3>
        <div class="cockpit__list">
          <div
            v-for="task in store.progress?.blocked_work_items ?? []"
            :key="task.id"
            class="cockpit__list-item cockpit__list-item--stack"
          >
            <strong>{{ task.id }} · {{ task.title }}</strong>
            <p>{{ task.blocked_by.join(', ') || 'blocked' }}</p>
          </div>
          <p v-if="!(store.progress?.blocked_work_items?.length)" class="cockpit__empty">
            {{ locale.cockpit.empty }}
          </p>
        </div>
      </article>

      <article class="card cockpit__panel">
        <h3>{{ locale.cockpit.todo }}</h3>
        <div class="cockpit__list">
          <div
            v-for="entry in summary?.todo_next ?? []"
            :key="entry.id"
            class="cockpit__list-item cockpit__list-item--stack"
          >
            <strong>{{ entry.id }}</strong>
            <p>[{{ entry.status }}] {{ entry.description }}</p>
          </div>
          <p v-if="!(summary?.todo_next?.length)" class="cockpit__empty">
            {{ locale.cockpit.empty }}
          </p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.cockpit {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cockpit__hero {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.9fr);
  gap: 20px;
  padding: 20px;
}

.cockpit__eyebrow {
  color: var(--accent-primary);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.cockpit__title {
  font-size: 1.8rem;
  margin-top: 6px;
}

.cockpit__description {
  margin-top: 10px;
  color: var(--text-secondary);
  max-width: 58ch;
}

.cockpit__hero-progress {
  align-self: center;
}

.cockpit__metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.cockpit__metric {
  padding: 16px 18px;
}

.cockpit__metric span {
  color: var(--text-muted);
}

.cockpit__metric strong {
  display: block;
  margin-top: 4px;
  font-size: 1.8rem;
}

.cockpit__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.cockpit__panel {
  padding: 18px;
}

.cockpit__panel h3 {
  margin-bottom: 12px;
}

.cockpit__runtime-meta {
  display: grid;
  gap: 4px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.cockpit__runtime-list,
.cockpit__list {
  display: grid;
  gap: 10px;
}

.cockpit__runtime-item,
.cockpit__list-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: rgba(243, 236, 223, 0.55);
}

.cockpit__list-item--stack {
  text-align: left;
}

.cockpit__list-item p,
.cockpit__runtime-item p {
  color: var(--text-secondary);
}

.cockpit__list-item pre {
  white-space: pre-wrap;
  font-family: var(--font-mono);
  font-size: 0.76rem;
  color: var(--text-secondary);
}

.cockpit__empty {
  color: var(--text-muted);
}

@media (max-width: 1080px) {
  .cockpit__hero,
  .cockpit__metrics,
  .cockpit__grid {
    grid-template-columns: 1fr;
  }
}
</style>
