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
  const rhr = biometrics.restingHRSeries
  return {
    ...theme,
    grid: { ...theme.grid, top: 24 },
    xAxis: {
      ...(Array.isArray(theme.xAxis) ? theme.xAxis[0] : theme.xAxis),
      data: rhr.dates
    },
    yAxis: {
      ...(Array.isArray(theme.yAxis) ? theme.yAxis[0] : theme.yAxis),
      name: 'bpm',
      nameTextStyle: { color: 'rgba(255, 246, 233, 0.35)', fontSize: 8 },
      min: 45,
      max: 75
    },
    series: [
      {
        name: 'Resting HR',
        type: 'line',
        data: rhr.values,
        connectNulls: false,
        smooth: 0.4,
        symbol: 'circle',
        symbolSize: 4,
        itemStyle: { color: '#FFBD76' },
        lineStyle: { color: '#FFBD76', width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(255, 189, 118, 0.2)' },
              { offset: 1, color: 'rgba(255, 189, 118, 0.02)' }
            ]
          }
        }
      }
    ]
  }
})
</script>

<template>
  <div class="resting-hr-chart">
    <header class="resting-hr-chart__header">
      <p class="resting-hr-chart__eyebrow font-mono text-xs5 tracking-label">RESTING HR</p>
      <p class="resting-hr-chart__sub font-mono text-xs5">Beats per minute</p>
    </header>
    <div class="resting-hr-chart__canvas">
      <VChart :option="option" autoresize />
    </div>
  </div>
</template>

<style scoped>
.resting-hr-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
  height: 100%;
}

.resting-hr-chart__header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.resting-hr-chart__eyebrow {
  margin: 0;
  color: var(--text-primary);
  letter-spacing: 0.15em;
}

.resting-hr-chart__sub {
  margin: 0;
  color: var(--text-muted);
}

.resting-hr-chart__canvas {
  height: 200px;
}
</style>
