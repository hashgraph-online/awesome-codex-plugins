<script setup lang="ts">
import { onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import MainPanel from '@/components/layout/MainPanel.vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import { useDashboardStore } from '@/stores/dashboard'
import type { WorkbenchTab } from '@/types'

const store = useDashboardStore()
const route = useRoute()

let timer: number | null = null

async function syncRouteAndLoad() {
  const tab = (route.meta.tab as WorkbenchTab | undefined) ?? 'overview'
  store.setActiveTab(tab)
  await store.loadTabData(tab)
}

async function refreshAll() {
  await store.refreshForActiveTab()
}

onMounted(async () => {
  await refreshAll()
  await syncRouteAndLoad()
  timer = window.setInterval(() => {
    void refreshAll()
  }, 20000)
})

watch(
  () => route.fullPath,
  () => {
    void syncRouteAndLoad()
  },
)

onBeforeUnmount(() => {
  if (timer != null) {
    window.clearInterval(timer)
  }
})
</script>

<template>
  <div class="workbench">
    <AppHeader @refresh="refreshAll" />
    <div class="workbench__body">
      <Sidebar />
      <MainPanel />
    </div>
  </div>
</template>

<style scoped>
.workbench {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.workbench__body {
  display: flex;
  flex: 1;
  min-height: 0;
}
</style>
