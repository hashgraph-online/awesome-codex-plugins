<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api/client'
import type { DagData, DagNode, DagEdge } from '@/types'

const dagData = ref<DagData | null>(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    dagData.value = await api.getDag()
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
})

function nodeColor(node: DagNode): string {
  switch (node.status) {
    case 'completed': return '#8BA870'
    case 'in_progress': return '#CC8B3A'
    case 'blocked': return '#c0392b'
    case 'pending': return '#E8DED4'
    default: return '#E8DED4'
  }
}

function edgeTargetLabel(edge: DagEdge, nodes: DagNode[]): string {
  const target = nodes.find(n => n.id === edge.target)
  return target?.label ?? edge.target
}

function edgeStyle(edge: DagEdge): string {
  return edge.type === 'soft' ? 'dashed' : 'solid'
}
</script>

<template>
  <div class="panel">
    <h2 class="panel-title">依赖图</h2>

    <div v-if="loading" class="loading-state">Loading...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>

    <template v-else-if="dagData">
      <div class="dag-stats card">
        <span>{{ dagData.nodes.length }} nodes</span>
        <span>{{ dagData.edges.length }} edges</span>
      </div>

      <div class="dag-container">
        <div class="dag-nodes">
          <div
            v-for="node in dagData.nodes"
            :key="node.id"
            class="dag-node card"
            :style="{ borderLeftColor: nodeColor(node) }"
          >
            <div class="node-header">
              <span class="node-label">{{ node.label }}</span>
              <span class="node-type">{{ node.type }}</span>
            </div>
            <div class="node-meta">
              <span v-if="node.status" class="node-status">{{ node.status }}</span>
              <span class="node-direction">{{ node.direction }}</span>
              <span class="node-progress">{{ node.progress.toFixed(0) }}%</span>
              <span v-if="node.work_item_count !== undefined" class="node-work_items">{{ node.work_item_count }} work_items</span>
            </div>
            <!-- Edges from this node -->
            <div
              v-if="dagData.edges.filter(e => e.source === node.id).length > 0"
              class="node-edges"
            >
              <span class="edge-arrow">&#x2192;</span>
              <span
                v-for="edge in dagData.edges.filter(e => e.source === node.id)"
                :key="edge.target"
                class="edge-target"
                :style="{ borderStyle: edgeStyle(edge) }"
              >
                {{ edgeTargetLabel(edge, dagData.nodes) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.panel {
  max-width: 1200px;
}

.panel-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
}

.loading-state,
.error-state {
  padding: 32px;
  text-align: center;
}

.error-state {
  color: #c0392b;
}

.card {
  background: var(--color-card-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 1px 3px var(--color-card-shadow);
}

.dag-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-accent);
}

.dag-container {
  overflow-x: auto;
}

.dag-nodes {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}

.dag-node {
  border-left: 4px solid var(--color-border);
}

.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.node-label {
  font-weight: 600;
  font-size: 14px;
}

.node-type {
  font-size: 11px;
  text-transform: uppercase;
  opacity: 0.5;
  font-weight: 600;
}

.node-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  opacity: 0.7;
}

.node-edges {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 13px;
}

.edge-arrow {
  color: var(--color-accent);
  font-weight: 700;
}

.edge-target {
  background: var(--color-bg);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  border: 1px solid var(--color-border);
}
</style>
