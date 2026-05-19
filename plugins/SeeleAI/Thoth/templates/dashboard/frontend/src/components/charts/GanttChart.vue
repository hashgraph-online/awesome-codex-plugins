<script setup lang="ts">
import { onMounted, ref, shallowRef, watch } from 'vue'
import * as echarts from 'echarts'
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const chartRef = ref<HTMLDivElement | null>(null)
const chart = shallowRef<echarts.ECharts | null>(null)

const statusColors: Record<string, string> = {
  blocked: '#c97761',
  completed: '#7f9a5b',
  failed: '#9c6b38',
  invalid: '#d28a93',
  ready: '#7e9ec7',
}

function buildOptions() {
  const rows = store.gantt
  if (!rows.length) return null
  const yData = rows.map((row) => row.id)
  const now = new Date()
  const starts = rows
    .filter((row) => row.start_date)
    .map((row) => new Date(row.start_date as string).getTime())
  const minDate = starts.length ? new Date(Math.min(...starts)) : now
  const maxDate = new Date(now.getTime() + 45 * 86400000)

  const barData = rows.map((row, index) => {
    const start = row.start_date ? new Date(row.start_date) : now
    const estimatedHours = row.estimated_hours > 0 ? row.estimated_hours : 24
    const computedEnd = new Date(start.getTime() + estimatedHours * 3600000)
    const end = row.end_date ? new Date(row.end_date) : computedEnd
    return {
      name: row.title,
      value: [index, start.getTime(), end.getTime(), row.progress, row.status, row.dependencies.join(', ')],
      itemStyle: {
        color: statusColors[row.status] || '#bf7c2b',
        opacity: row.start_date ? 1 : 0.35,
        borderRadius: 5,
      },
    }
  })

  return {
    tooltip: {
      trigger: 'item' as const,
      formatter: (params: { name: string; value: [number, number, number, number, string, string] }) => {
        const value = params.value
        const start = new Date(value[1]).toLocaleDateString()
        const end = new Date(value[2]).toLocaleDateString()
        return [
          `<b>${params.name}</b>`,
          `${start} -> ${end}`,
          `progress: ${Math.round(value[3])}%`,
          `status: ${value[4]}`,
          `deps: ${value[5] || 'none'}`,
        ].join('<br/>')
      },
    },
    grid: { left: 160, right: 24, top: 18, bottom: 36 },
    xAxis: {
      type: 'time' as const,
      min: minDate.getTime(),
      max: maxDate.getTime(),
      axisLabel: { color: '#624b3b' },
      splitLine: { lineStyle: { color: '#eadbc8' } },
    },
    yAxis: {
      type: 'category' as const,
      data: yData,
      inverse: true,
      axisLabel: {
        color: '#2f2118',
        width: 140,
        overflow: 'truncate' as const,
      },
    },
    series: [
      {
        type: 'custom',
        renderItem: (_params: unknown, api: any) => {
          const categoryIndex = api.value(0)
          const start = api.coord([api.value(1), categoryIndex])
          const end = api.coord([api.value(2), categoryIndex])
          return {
            type: 'rect',
            shape: {
              x: start[0],
              y: start[1] - 8,
              width: Math.max(end[0] - start[0], 5),
              height: 16,
              r: 5,
            },
            style: api.style(),
          }
        },
        encode: { x: [1, 2], y: 0 },
        data: barData,
      },
    ],
  }
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart.value) {
    chart.value = echarts.init(chartRef.value)
  }
  const options = buildOptions()
  if (options) {
    chart.value.setOption(options, true)
  }
}

onMounted(async () => {
  if (!store.gantt.length) {
    await store.fetchGantt()
  }
  renderChart()
  window.addEventListener('resize', () => chart.value?.resize())
})

watch(
  () => store.gantt,
  () => renderChart(),
  { deep: true },
)
</script>

<template>
  <section class="card gantt">
    <div ref="chartRef" class="gantt__canvas" />
  </section>
</template>

<style scoped>
.gantt {
  padding: 12px;
  min-height: 620px;
}

.gantt__canvas {
  min-height: 580px;
}
</style>
