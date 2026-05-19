<script setup lang="ts">
import { onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()

onMounted(() => {
  if (!store.activity.length) {
    void store.fetchActivity()
  }
})
</script>

<template>
  <section class="activity">
    <article class="card activity__panel">
      <h2>Activity</h2>
      <div class="activity__list">
        <div v-for="event in store.activity" :key="event.id" class="activity__item">
          <div class="activity__top">
            <strong>{{ event.work_id }} · {{ event.work_title }}</strong>
            <span>{{ event.verdict }}</span>
          </div>
          <p>{{ event.conclusion_text || 'No conclusion text' }}</p>
          <small>{{ event.module }} · {{ event.direction }} · {{ event.created_at }}</small>
        </div>
        <p v-if="!store.activity.length">No activity events.</p>
      </div>
    </article>
  </section>
</template>

<style scoped>
.activity__panel {
  padding: 18px;
}

.activity__list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.activity__item {
  padding: 12px;
  border-radius: var(--radius-sm);
  background: rgba(243, 236, 223, 0.55);
}

.activity__top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.activity__item p {
  margin-top: 8px;
}

.activity__item small {
  display: block;
  margin-top: 8px;
  color: var(--text-muted);
}
</style>
