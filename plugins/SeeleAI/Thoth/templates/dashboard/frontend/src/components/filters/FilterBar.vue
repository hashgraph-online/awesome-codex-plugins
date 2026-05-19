<script setup lang="ts">
import { computed } from 'vue'
import { locale } from '@/locales'
import { useDashboardStore } from '@/stores/dashboard'

defineProps<{
  directions: Array<{ id: string; label: string }>
}>()

const store = useDashboardStore()

const statusOptions = computed(() => [
  { value: '', label: locale.filters.allStatus },
  { value: 'ready', label: locale.status.ready },
  { value: 'completed', label: locale.status.completed },
  { value: 'blocked', label: locale.status.blocked },
  { value: 'failed', label: locale.status.failed },
  { value: 'invalid', label: locale.status.invalid },
])

function clearFilters() {
  store.filters.status = ''
  store.filters.direction = ''
  store.filters.module = ''
  store.filters.search = ''
}
</script>

<template>
  <div class="filters">
    <input
      v-model="store.filters.search"
      class="filters__search"
      :placeholder="locale.filters.search"
    />
    <div class="filters__grid">
      <select v-model="store.filters.status">
        <option v-for="option in statusOptions" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
      <select v-model="store.filters.direction">
        <option value="">{{ locale.filters.allDirection }}</option>
        <option v-for="direction in directions" :key="direction.id" :value="direction.id">
          {{ direction.label }}
        </option>
      </select>
      <select v-model="store.filters.module">
        <option value="">{{ locale.filters.allModule }}</option>
        <option v-for="module in store.modules" :key="module.id" :value="module.id">
          {{ module.id }} · {{ module.name }}
        </option>
      </select>
    </div>
    <button class="filters__clear" @click="clearFilters">
      {{ locale.filters.clear }}
    </button>
  </div>
</template>

<style scoped>
.filters {
  padding: 10px 12px 14px;
  border-bottom: 1px solid var(--border-light);
}

.filters__search {
  width: 100%;
  margin-bottom: 8px;
}

.filters__grid {
  display: grid;
  gap: 6px;
}

.filters__clear {
  margin-top: 8px;
  color: var(--accent-primary);
  font-weight: 600;
}
</style>
