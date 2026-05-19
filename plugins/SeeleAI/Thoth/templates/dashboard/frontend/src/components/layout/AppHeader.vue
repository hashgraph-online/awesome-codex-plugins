<script setup lang="ts">
import { computed } from 'vue'
import { locale } from '@/locales'
import { useDashboardStore } from '@/stores/dashboard'

const emit = defineEmits<{
  refresh: []
}>()

const store = useDashboardStore()

const projectName = computed(
  () => store.config?.project?.name || store.overviewSummary?.project?.name || locale.brand,
)

const freshness = computed(() => {
  if (!store.lastUpdatedAt) return '—'
  const diffSeconds = Math.max(
    0,
    Math.floor((Date.now() - new Date(store.lastUpdatedAt).getTime()) / 1000),
  )
  if (diffSeconds < 60) return `${diffSeconds}s`
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m`
  return `${Math.floor(diffSeconds / 3600)}h`
})

const headline = computed(() => store.overviewSummary?.headline)
const runtime = computed(() => store.overviewSummary?.runtime)
</script>

<template>
  <header class="header">
    <div class="header__brand">
      <div class="header__mark">TH</div>
      <div>
        <h1 class="header__title">{{ projectName }}</h1>
        <p class="header__subtitle">{{ locale.subtitle }}</p>
      </div>
    </div>

    <div class="header__stats" v-if="headline">
      <div class="header__chip">
        <span>{{ locale.header.activeRuns }}</span>
        <strong>{{ runtime?.active_run_count ?? 0 }}</strong>
      </div>
      <div class="header__chip">
        <span>{{ locale.header.staleRuns }}</span>
        <strong>{{ runtime?.stale_run_count ?? 0 }}</strong>
      </div>
      <div class="header__chip">
        <span>{{ locale.header.decisionQueue }}</span>
        <strong>{{ headline.decision_queue_count }}</strong>
      </div>
    </div>

    <div class="header__actions">
      <div class="header__freshness">
        <span>{{ locale.header.freshness }}</span>
        <strong>{{ freshness }}</strong>
      </div>
      <button class="header__button" @click="emit('refresh')">
        {{ locale.header.refresh }}
      </button>
    </div>
  </header>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 16px 22px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-header);
}

.header__brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header__mark {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: linear-gradient(145deg, #3c2a1f, #6a492e);
  color: #fff8ef;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.header__title {
  font-size: 1.2rem;
}

.header__subtitle {
  color: var(--text-muted);
  font-size: 0.82rem;
}

.header__stats {
  display: flex;
  flex: 1;
  justify-content: center;
  gap: 10px;
}

.header__chip {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid rgba(47, 33, 24, 0.08);
  border-radius: 999px;
  background: rgba(255, 253, 248, 0.75);
  color: var(--text-secondary);
}

.header__chip strong {
  color: var(--text-primary);
  font-size: 1rem;
}

.header__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header__freshness {
  text-align: right;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.header__freshness strong {
  display: block;
  color: var(--text-primary);
  font-size: 0.95rem;
}

.header__button {
  padding: 10px 14px;
  border-radius: 999px;
  background: var(--text-primary);
  color: #fff7ef;
  box-shadow: var(--shadow-soft);
}

@media (max-width: 1080px) {
  .header {
    flex-wrap: wrap;
  }

  .header__stats {
    order: 3;
    width: 100%;
    justify-content: flex-start;
    overflow-x: auto;
  }
}
</style>
