<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import DagChart from '@/components/charts/DagChart.vue'
import GanttChart from '@/components/charts/GanttChart.vue'
import ModuleDetail from '@/components/detail/ModuleDetail.vue'
import WorkItemDetail from '@/components/detail/WorkItemDetail.vue'
import ActivityPanel from '@/components/panels/ActivityPanel.vue'
import CockpitPanel from '@/components/panels/CockpitPanel.vue'
import SystemPanel from '@/components/panels/SystemPanel.vue'
import TodoPanel from '@/components/todo/TodoPanel.vue'
import { locale } from '@/locales'
import { useDashboardStore } from '@/stores/dashboard'
import type { WorkbenchTab } from '@/types'

const router = useRouter()
const store = useDashboardStore()

const tabs = computed<Array<{ key: WorkbenchTab; label: string }>>(() => [
  { key: 'overview', label: locale.tabs.overview },
  { key: 'detail', label: locale.tabs.detail },
  { key: 'dag', label: locale.tabs.dag },
  { key: 'gantt', label: locale.tabs.gantt },
  { key: 'todo', label: locale.tabs.todo },
  { key: 'activity', label: locale.tabs.activity },
  { key: 'system', label: locale.tabs.system },
])

const tabRoute: Record<WorkbenchTab, string> = {
  overview: '/overview',
  detail: '/work-items',
  dag: '/dag',
  gantt: '/timeline',
  todo: '/todo',
  activity: '/activity',
  system: '/system',
}

function activateTab(tab: WorkbenchTab) {
  store.setActiveTab(tab)
  router.push(tabRoute[tab])
}
</script>

<template>
  <main class="main-panel">
    <div class="main-panel__tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="main-panel__tab"
        :class="{ 'main-panel__tab--active': tab.key === store.activeTab }"
        @click="activateTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="main-panel__content">
      <Transition name="fade" mode="out-in">
        <CockpitPanel v-if="store.activeTab === 'overview'" key="overview" />
        <WorkItemDetail
          v-else-if="store.activeTab === 'detail' && store.selectedWorkItem"
          :key="store.selectedWorkItem.id"
        />
        <ModuleDetail
          v-else-if="store.activeTab === 'detail' && store.selectedModule"
          :key="store.selectedModule.id"
        />
        <div v-else-if="store.activeTab === 'detail'" key="empty-detail" class="main-panel__placeholder card">
          {{ locale.detail.empty }}
        </div>
        <DagChart v-else-if="store.activeTab === 'dag'" key="dag" />
        <GanttChart v-else-if="store.activeTab === 'gantt'" key="gantt" />
        <TodoPanel v-else-if="store.activeTab === 'todo'" key="todo" />
        <ActivityPanel v-else-if="store.activeTab === 'activity'" key="activity" />
        <SystemPanel v-else key="system" />
      </Transition>
    </div>
  </main>
</template>

<style scoped>
.main-panel {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
}

.main-panel__tabs {
  display: flex;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-light);
  background: rgba(255, 253, 248, 0.86);
  overflow-x: auto;
}

.main-panel__tab {
  padding: 8px 14px;
  border-radius: 999px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.main-panel__tab--active {
  background: var(--accent-light);
  color: var(--accent-primary);
  font-weight: 700;
}

.main-panel__content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px;
}

.main-panel__placeholder {
  display: grid;
  place-items: center;
  min-height: 240px;
  color: var(--text-muted);
}
</style>
