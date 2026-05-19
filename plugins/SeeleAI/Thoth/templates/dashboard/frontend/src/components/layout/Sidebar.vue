<script setup lang="ts">
import { computed } from 'vue'
import FilterBar from '@/components/filters/FilterBar.vue'
import DirectionNode from '@/components/tree/DirectionNode.vue'
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()

const directions = computed(
  () => store.config?.research?.directions?.map((item) => ({
    id: item.id,
    label: item.label_zh || item.label_en || item.id,
  })) ?? [],
)
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar__label">Workbench Tree</div>
    <FilterBar :directions="directions" />
    <div class="sidebar__tree">
      <DirectionNode
        v-for="direction in store.filteredTree"
        :key="direction.direction"
        :direction="direction"
      />
      <div v-if="store.filteredTree.length === 0" class="sidebar__empty">
        No matching work_items
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 340px;
  min-width: 290px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-light);
  background: var(--bg-sidebar);
}

.sidebar__label {
  padding: 12px 16px 6px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  text-transform: uppercase;
}

.sidebar__tree {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 6px 8px 16px;
}

.sidebar__empty {
  padding: 32px 16px;
  text-align: center;
  color: var(--text-muted);
}

@media (max-width: 960px) {
  .sidebar {
    display: none;
  }
}
</style>
