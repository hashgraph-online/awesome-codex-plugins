<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api/client'
import type { TimelineItem } from '@/types/index'
import LoadingState from '@/components/common/LoadingState.vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CustomChart } from 'echarts/charts'
import {
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([CustomChart, TooltipComponent, GridComponent, DataZoomComponent, CanvasRenderer])

const loading = ref(true)
const error = ref('')
const items = ref<TimelineItem[]>([])

const statusColors: Record<string, string> = {
  pending: '#c4bdb5',
  in_progress: '#CC8B3A',
  completed: '#2d6a4f',
  blocked: '#a4262c',
}

const chartOption = computed(() => {
  if (!items.value.length) return {}

  /* Group by direction then sort */
  const dirGroups: Record<string, TimelineItem[]> = {}
  for (const item of items.value) {
    const dir = item.direction || 'unknown'
    if (!dirGroups[dir]) dirGroups[dir] = []
    dirGroups[dir].push(item)
  }

  const yLabels: string[] = []
  const data: Array<{ value: [number, number, number, string]; itemStyle: { color: string } }> = []
  let rowIdx = 0

  const now = Date.now()
  let minTime = now
  let maxTime = now

  for (const dir of Object.keys(dirGroups).sort()) {
    for (const item of dirGroups[dir]) {
      const startMs = item.start_date ? new Date(item.start_date).getTime() : now
      const endMs = item.end_date
        ? new Date(item.end_date).getTime()
        : (item.estimated_hours
          ? startMs + item.estimated_hours * 3600 * 1000
          : startMs + 7 * 86400 * 1000)

      minTime = Math.min(minTime, startMs)
      maxTime = Math.max(maxTime, endMs)

      yLabels.push(`[${dir}] ${item.title}`)
      data.push({
        value: [rowIdx, startMs, endMs, item.id],
        itemStyle: { color: statusColors[item.status] ?? '#ccc' },
      })
      rowIdx++
    }
  }

  return {
    tooltip: {
      backgroundColor: '#fffaf5',
      borderColor: '#e8e0d6',
      textStyle: { color: '#2C1810', fontSize: 12 },
      formatter: (params: { value?: [number, number, number, string] }) => {
        if (!params.value) return ''
        const [idx, s, e, id] = params.value
        const label = yLabels[idx] ?? id
        const start = new Date(s).toLocaleDateString('zh-CN')
        const end = new Date(e).toLocaleDateString('zh-CN')
        return `<b>${label}</b><br/>ID: ${id}<br/>${start} ~ ${end}`
      },
    },
    grid: { left: 220, right: 40, top: 20, bottom: 60 },
    xAxis: {
      type: 'time',
      min: minTime - 86400000,
      max: maxTime + 86400000,
      axisLine: { lineStyle: { color: '#e8e0d6' } },
      axisLabel: { color: '#6b5b4e', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f0ebe4' } },
    },
    yAxis: {
      type: 'category',
      data: yLabels,
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#2C1810',
        fontSize: 11,
        width: 200,
        overflow: 'truncate',
      },
    },
    dataZoom: [
      { type: 'slider', xAxisIndex: 0, bottom: 10, height: 20, borderColor: '#e8e0d6', fillerColor: 'rgba(204,139,58,0.15)' },
    ],
    series: [{
      type: 'custom',
      renderItem: (
        _params: unknown,
        apiObj: {
          value: (idx: number) => number
          coord: (pair: [number, number]) => [number, number]
          size: (pair: [number, number]) => [number, number]
          style: () => Record<string, unknown>
        },
      ) => {
        const categoryIndex = apiObj.value(0) as number
        const start = apiObj.coord([apiObj.value(1) as number, categoryIndex])
        const end = apiObj.coord([apiObj.value(2) as number, categoryIndex])
        const barHeight = Math.max(apiObj.size([0, 1])[1] * 0.6, 8)
        return {
          type: 'rect',
          shape: {
            x: start[0],
            y: start[1] - barHeight / 2,
            width: Math.max(end[0] - start[0], 4),
            height: barHeight,
            r: 4,
          },
          style: apiObj.style(),
        }
      },
      encode: { x: [1, 2], y: 0 },
      data,
    }],
  }
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await api.getTimeline()
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
  <div class="timeline-chart">
    <LoadingState v-if="loading" />
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <div v-else-if="!items.length" class="empty-hint">暂无时间线数据</div>
    <div v-else class="chart-container">
      <v-chart :option="chartOption" autoresize class="echart" />
    </div>
  </div>
</template>

<style scoped>
.timeline-chart {
  padding: 24px;
  height: calc(100vh - 56px - 48px);
  min-height: 500px;
}

.error-msg {
  color: #a4262c;
  text-align: center;
  padding: 40px;
}
.empty-hint {
  color: var(--text-secondary, #6b5b4e);
  text-align: center;
  padding: 60px 0;
  font-size: 14px;
}

.chart-container {
  width: 100%;
  height: 100%;
  background: var(--bg-card, #ffffff);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(44, 24, 16, 0.06);
  overflow: hidden;
}

.echart {
  width: 100%;
  height: 100%;
}
</style>
