<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent
} from 'echarts/components'
import { useBiometricsStore } from '@/stores/biometrics'
import { useBiometricsChartTheme } from '@/composables/useBiometricsChartTheme'
import type { EChartsOption } from 'echarts'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, DataZoomComponent])


const biometrics = useBiometricsStore()
const theme = useBiometricsChartTheme()

const option = computed<EChartsOption>(() => {
  const scores = biometrics.sleepScoreSeries
  return {
    ...theme,
    grid: { ...theme.grid, top: 24 },
    xAxis: {
      ...(Array.isArray(theme.xAxis) ? theme.xAxis[0] : theme.xAxis),
      data: scores.dates
    },
    yAxis: {
      ...(Array.isArray(theme.yAxis) ? theme.yAxis[0] : theme.yAxis),
      name: 'score',
      nameTextStyle: { color: 'rgba(255, 246, 233, 0.35)', fontSize: 8 },
      min: 0,
      max: 100
    },
    series: [
      {
        name: 'Sleep Score',
        type: 'line',
        data: scores.scores,
        connectNulls: false,
        smooth: 0.3,
        symbol: 'circle',
        symbolSize: 4,
        itemStyle: { color: '#9B8BFA' },
        lineStyle: { color: '#9B8BFA', width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(155, 139, 250, 0.28)' },
              { offset: 1, color: 'rgba(155, 139, 250, 0.02)' }
            ]
          }
        }
      }
    ]
  }
})
</script>

<template>
  <div class="sleep-score-chart">
    <header class="sleep-score-chart__header">
      <p class="sleep-score-chart__eyebrow font-mono text-xs5 tracking-label">SLEEP SCORE</p>
      <p class="sleep-score-chart__sub font-mono text-xs5">0–100 scale</p>
    </header>
    <div class="sleep-score-chart__canvas">
      <VChart :option="option" autoresize />
    </div>
  </div>
</template>

<style scoped>
.sleep-score-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
  height: 100%;
}

.sleep-score-chart__header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.sleep-score-chart__eyebrow {
  margin: 0;
  color: var(--text-primary);
  letter-spacing: 0.15em;
}

.sleep-score-chart__sub {
  margin: 0;
  color: var(--text-muted);
}

.sleep-score-chart__canvas {
  height: 200px;
}
</style>
