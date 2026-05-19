<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api/client'
import type { DagData, DagNode } from '@/types/index'
import LoadingState from '@/components/common/LoadingState.vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([GraphChart, TooltipComponent, LegendComponent, CanvasRenderer])

const loading = ref(true)
const error = ref('')
const dagData = ref<DagData | null>(null)
const selectedNode = ref<DagNode | null>(null)

/* Color palettes */
const directionColors: Record<string, string> = {}
const palette = ['#CC8B3A', '#6B8E6B', '#8B6B8E', '#6B7E8E', '#8E7B6B', '#6B8E8B', '#8E6B6B']
let colorIdx = 0
function dirColor(dir: string): string {
  if (!directionColors[dir]) {
    directionColors[dir] = palette[colorIdx % palette.length]
    colorIdx++
  }
  return directionColors[dir]
}

const statusColors: Record<string, string> = {
  pending: '#c4bdb5',
  in_progress: '#CC8B3A',
  completed: '#2d6a4f',
  blocked: '#a4262c',
  ready: '#7e9ec7',
  invalid: '#d28a93',
  failed: '#9c6b38',
}

const chartOption = computed(() => {
  if (!dagData.value) return {}
  const { nodes, edges } = dagData.value

  const graphNodes = nodes.map((n) => ({
    id: n.id,
    name: n.label,
    symbolSize: n.type === 'module' ? 36 : 20,
    category: n.type === 'module' ? 0 : 1,
    itemStyle: {
      color: n.type === 'module' ? dirColor(n.direction) : (statusColors[n.status ?? 'pending'] ?? '#ccc'),
      borderColor: '#fff',
      borderWidth: 2,
    },
    label: {
      show: n.type === 'module',
      fontSize: 11,
      color: 'var(--text-primary, #2C1810)',
    },
    value: n.progress,
    _raw: n,
  }))

  const graphLinks = edges.map((e) => ({
    source: e.source,
    target: e.target,
    lineStyle: {
      type: e.type === 'hard' ? 'solid' as const : ('dashed' as const),
      color: e.type === 'hard' ? '#CC8B3A' : '#c4bdb5',
      width: e.type === 'hard' ? 2 : 1,
      curveness: 0.2,
    },
  }))

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: '#fffaf5',
      borderColor: '#e8e0d6',
      textStyle: { color: '#2C1810', fontSize: 12 },
      formatter: (params: { data?: { _raw?: DagNode; name?: string } }) => {
        const n = params.data?._raw
        if (!n) return params.data?.name ?? ''
        const lines = [`<b>${n.label}</b>`, `类型: ${n.type === 'module' ? '模块' : '工作项'}`, `方向: ${n.direction}`]
        if (n.progress != null) lines.push(`进度: ${Math.round(n.progress)}%`)
        if (n.status) lines.push(`状态: ${n.status}`)
        return lines.join('<br/>')
      },
    },
    legend: {
      data: ['模块', '工作项'],
      top: 10,
      textStyle: { color: '#6b5b4e' },
    },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      force: { repulsion: 200, edgeLength: [80, 160], gravity: 0.1 },
      categories: [
        { name: '模块' },
        { name: '工作项' },
      ],
      data: graphNodes,
      links: graphLinks,
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [0, 8],
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 3 },
      },
    }],
  }
})

function onChartClick(params: unknown) {
  const data =
    params && typeof params === 'object' && 'data' in params
      ? (params as { data?: unknown }).data
      : undefined

  const raw =
    data && typeof data === 'object' && '_raw' in data
      ? (data as { _raw?: unknown })._raw
      : undefined

  if (raw && typeof raw === 'object' && 'id' in raw && 'label' in raw) {
    selectedNode.value = raw as DagNode
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    dagData.value = await api.getDag()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
defineExpose({ reload: load })
</script>

<template>
  <div class="dag-chart">
    <LoadingState v-if="loading" />
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else>
      <div class="chart-container">
        <v-chart
          :option="chartOption"
          autoresize
          class="echart"
          @click="onChartClick"
        />
      </div>

      <!-- Detail panel -->
      <div v-if="selectedNode" class="detail-sidebar">
        <div class="detail-header">
          <h4 class="detail-title">{{ selectedNode.label }}</h4>
          <button class="close-btn" @click="selectedNode = null">&times;</button>
        </div>
        <div class="detail-body">
          <div class="detail-row"><span class="dl">类型</span><span>{{ selectedNode.type === 'module' ? '模块' : '任务' }}</span></div>
          <div class="detail-row"><span class="dl">方向</span><span>{{ selectedNode.direction }}</span></div>
          <div v-if="selectedNode.module" class="detail-row"><span class="dl">模块</span><span>{{ selectedNode.module }}</span></div>
          <div class="detail-row"><span class="dl">进度</span><span>{{ Math.round(selectedNode.progress) }}%</span></div>
          <div v-if="selectedNode.status" class="detail-row"><span class="dl">状态</span><span>{{ selectedNode.status }}</span></div>
          <div v-if="selectedNode.work_item_count != null" class="detail-row"><span class="dl">任务数</span><span>{{ selectedNode.work_item_count }}</span></div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dag-chart {
  padding: 24px;
  display: flex;
  gap: 16px;
  height: calc(100vh - 56px - 48px);
  min-height: 500px;
}

.error-msg {
  color: #a4262c;
  text-align: center;
  padding: 40px;
  width: 100%;
}

.chart-container {
  flex: 1;
  background: var(--bg-card, #ffffff);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(44, 24, 16, 0.06);
  overflow: hidden;
}

.echart {
  width: 100%;
  height: 100%;
}

/* ── Detail sidebar ─── */
.detail-sidebar {
  width: 260px;
  flex-shrink: 0;
  background: var(--bg-card, #ffffff);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(44, 24, 16, 0.06);
  padding: 16px;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
}

.detail-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #2C1810);
  word-break: break-word;
}

.close-btn {
  border: none;
  background: none;
  font-size: 20px;
  color: var(--text-secondary, #6b5b4e);
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.dl {
  color: var(--text-secondary, #6b5b4e);
}
</style>
