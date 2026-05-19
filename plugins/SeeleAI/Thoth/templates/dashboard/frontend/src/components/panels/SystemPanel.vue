<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { locale } from '@/locales'
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()

const system = computed(() => store.systemStatus as Record<string, unknown> | null)

function pretty(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2)
}

onMounted(() => {
  void store.fetchSystemStatus()
})
</script>

<template>
  <section class="system">
    <article class="card system__panel">
      <h2>{{ locale.system.title }}</h2>
      <div class="system__chips">
        <span class="pill" :class="`badge-${store.overviewSummary?.healthy ? 'completed' : 'blocked'}`">
          {{ locale.system.healthy }}: {{ store.overviewSummary?.healthy ? 'OK' : 'CHECK' }}
        </span>
        <span class="pill badge-ready">
          work_items: {{ system?.work_item_count || 0 }}
        </span>
        <span class="pill badge-pending">
          modules: {{ system?.module_count || 0 }}
        </span>
      </div>
    </article>

    <div class="system__grid">
      <article class="card system__panel">
        <h3>{{ locale.system.runtime }}</h3>
        <pre>{{ pretty((system?.runtime as unknown) || store.overviewSummary?.runtime) }}</pre>
      </article>
      <article class="card system__panel">
        <h3>{{ locale.system.compiler }}</h3>
        <pre>{{ pretty(system?.compiler || store.overviewSummary?.compiler_summary) }}</pre>
      </article>
      <article class="card system__panel">
        <h3>{{ locale.system.cache }}</h3>
        <pre>{{ pretty(system?.cache_info) }}</pre>
      </article>
    </div>
  </section>
</template>

<style scoped>
.system {
  display: grid;
  gap: 14px;
}

.system__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.system__panel {
  padding: 18px;
}

.system__chips {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

pre {
  margin-top: 12px;
  white-space: pre-wrap;
  overflow-x: auto;
}

@media (max-width: 1080px) {
  .system__grid {
    grid-template-columns: 1fr;
  }
}
</style>
