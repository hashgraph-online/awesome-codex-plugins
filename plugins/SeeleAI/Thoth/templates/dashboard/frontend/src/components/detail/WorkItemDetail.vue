<script setup lang="ts">
import { computed } from 'vue'
import { locale } from '@/locales'
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const task = computed(() => store.selectedWorkItem!)

const verdictLabel = computed(() => {
  const result = task.value.work_result
  if (result?.usable === true && result?.meets_goal === true) return 'meets_goal'
  if (result?.updated_at) return 'recorded'
  if (typeof task.value.verdict === 'string' && task.value.verdict) return task.value.verdict
  return ''
})

const conclusion = computed(
  () => task.value.work_result?.conclusion || task.value.work_result?.current_summary || '',
)

function renderJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2)
}
</script>

<template>
  <section class="task-detail">
    <article class="card task-detail__hero">
      <div class="task-detail__row">
        <span class="task-detail__id">{{ task.id }}</span>
        <span class="pill" :class="`badge-${task.computed_status}`">{{ task.computed_status }}</span>
        <span v-if="task.type" class="task-detail__type">{{ task.type }}</span>
      </div>
      <h2>{{ task.title }}</h2>
      <div class="task-detail__meta">
        <span>module: {{ task.module }}</span>
        <span>direction: {{ task.direction }}</span>
        <span>created: {{ task.created_at || task.generated_at || '—' }}</span>
        <span>progress: {{ Math.round(task.computed_progress) }}%</span>
      </div>
    </article>

    <article class="card task-detail__section">
      <h3>{{ locale.detail.basic }}</h3>
      <dl class="task-detail__kv">
        <dt>work_id</dt><dd>{{ task.id }}</dd>
        <dt>title</dt><dd>{{ task.title }}</dd>
        <dt>direction</dt><dd>{{ task.direction }}</dd>
        <dt>module</dt><dd>{{ task.module }}</dd>
        <dt>type</dt><dd>{{ task.type || '—' }}</dd>
        <dt>created</dt><dd>{{ task.created_at || '—' }}</dd>
        <dt>generated</dt><dd>{{ task.generated_at || '—' }}</dd>
      </dl>
    </article>

    <article
      v-if="task.goal_statement || task.decision_ids?.length || task.candidate_method_id"
      class="card task-detail__section"
    >
      <h3>{{ locale.detail.goal }}</h3>
      <dl class="task-detail__kv">
        <dt>goal_statement</dt><dd>{{ task.goal_statement || '—' }}</dd>
        <dt>decision_ids</dt><dd>{{ task.decision_ids?.join(', ') || '—' }}</dd>
        <dt>candidate_method_id</dt><dd>{{ task.candidate_method_id || '—' }}</dd>
      </dl>
    </article>

    <article v-if="task.ready_state || task.blocking_reason" class="card task-detail__section">
      <h3>{{ locale.detail.readiness }}</h3>
      <dl class="task-detail__kv">
        <dt>ready_state</dt><dd>{{ task.ready_state || '—' }}</dd>
        <dt>blocking_reason</dt><dd>{{ task.blocking_reason || '—' }}</dd>
      </dl>
    </article>

    <article v-if="task.implementation_recipe?.length" class="card task-detail__section">
      <h3>{{ locale.detail.recipe }}</h3>
      <ul class="task-detail__list">
        <li v-for="step in task.implementation_recipe" :key="step">{{ step }}</li>
      </ul>
    </article>

    <article v-if="task.eval_entrypoint" class="card task-detail__section">
      <h3>{{ locale.detail.eval }}</h3>
      <pre>{{ renderJson(task.eval_entrypoint) }}</pre>
    </article>

    <article v-if="task.failure_classes?.length" class="card task-detail__section">
      <h3>{{ locale.detail.failure }}</h3>
      <ul class="task-detail__list">
        <li v-for="item in task.failure_classes" :key="item">{{ item }}</li>
      </ul>
    </article>

    <article
      v-if="conclusion || task.work_result?.evidence_paths?.length || verdictLabel"
      class="card task-detail__section"
    >
      <h3>{{ locale.detail.verdict }}</h3>
      <dl class="task-detail__kv">
        <dt>verdict</dt><dd>{{ verdictLabel || '—' }}</dd>
        <dt>source</dt><dd>{{ task.work_result?.source || '—' }}</dd>
        <dt>updated_at</dt><dd>{{ task.work_result?.updated_at || '—' }}</dd>
      </dl>
      <p class="task-detail__text">{{ conclusion || locale.detail.noConclusion }}</p>
      <ul v-if="task.work_result?.evidence_paths?.length" class="task-detail__list">
        <li v-for="path in task.work_result.evidence_paths" :key="path">{{ path }}</li>
      </ul>
    </article>

    <article
      v-if="task.active_run || (task.run_count ?? 0) > 0"
      class="card task-detail__section"
    >
      <h3>{{ locale.detail.runtime }}</h3>
      <dl class="task-detail__kv">
        <dt>run_count</dt><dd>{{ task.run_count ?? 0 }}</dd>
        <dt>active_run</dt><dd>{{ task.active_run?.run_id || '—' }}</dd>
        <dt>host</dt><dd>{{ task.active_run?.host || '—' }}</dd>
        <dt>phase</dt><dd>{{ task.active_run?.phase || task.active_run?.status || '—' }}</dd>
      </dl>
    </article>
  </section>
</template>

<style scoped>
.task-detail {
  display: grid;
  gap: 14px;
}

.task-detail__hero,
.task-detail__section {
  padding: 18px;
}

.task-detail__row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.task-detail__id {
  font-family: var(--font-mono);
  color: var(--accent-primary);
}

.task-detail__type {
  color: var(--text-muted);
}

.task-detail__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
  color: var(--text-secondary);
}

.task-detail__kv {
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr);
  gap: 8px 12px;
}

.task-detail__kv dt {
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.task-detail__list {
  padding-left: 18px;
}

.task-detail__text,
pre {
  margin-top: 12px;
  white-space: pre-wrap;
  overflow-x: auto;
}
</style>
