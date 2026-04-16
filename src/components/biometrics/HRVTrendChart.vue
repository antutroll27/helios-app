<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import { useBiometricsStore } from '@/stores/biometrics'
import type { EChartsOption } from 'echarts'

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent])

const biometrics = useBiometricsStore()

const option = computed<EChartsOption>(() => {
  const hrv = biometrics.hrvSeries
  const kp  = biometrics.kpOverlaySeries
  return {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 600,
    grid: { left: 44, right: 44, top: 20, bottom: 32 },
    tooltip: {
      backgroundColor: '#07111a',
      borderColor: 'rgba(255, 246, 233, 0.18)',
      borderWidth: 1,
      textStyle: {
        color: 'rgba(255, 246, 233, 0.9)',
        fontFamily: "'Geist Mono', 'JetBrains Mono', monospace",
        fontSize: 11
      },
      trigger: 'axis',
      axisPointer: {
        type: 'line',
        lineStyle: { color: 'rgba(148, 163, 184, 0.3)', type: 'dashed' }
      }
    },
    legend: {
      data: ['HRV (rMSSD)', 'Kp Index'],
      top: 0,
      right: 20,
      textStyle: { color: 'rgba(255, 246, 233, 0.55)', fontSize: 9, fontFamily: "'Geist Mono', monospace" },
      itemWidth: 12,
      itemHeight: 8
    },
    xAxis: {
      type: 'category',
      data: hrv.dates,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { color: 'rgba(255,246,233,0.35)', fontSize: 9, fontFamily: "'Geist Mono', monospace" }
    },
    yAxis: [
      {
        type: 'value',
        name: 'ms',
        nameTextStyle: { color: 'rgba(255,246,233,0.35)', fontSize: 8 },
        min: 20,
        max: 70,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { color: 'rgba(255,246,233,0.35)', fontSize: 9, fontFamily: "'Geist Mono', monospace" }
      },
      {
        type: 'value',
        name: 'Kp',
        nameTextStyle: { color: 'rgba(255,246,233,0.35)', fontSize: 8 },
        min: 0,
        max: 9,
        position: 'right',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { color: 'rgba(255,246,233,0.35)', fontSize: 9, fontFamily: "'Geist Mono', monospace" }
      }
    ],
    series: [
      {
        name: 'HRV (rMSSD)',
        type: 'line',
        yAxisIndex: 0,
        data: hrv.values,
        connectNulls: false,
        smooth: 0.4,
        symbol: 'circle',
        symbolSize: 5,
        itemStyle: { color: '#00D4AA' },
        lineStyle: { color: '#00D4AA', width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0, 212, 170, 0.22)' },
              { offset: 1, color: 'rgba(0, 212, 170, 0.02)' }
            ]
          }
        }
      },
      {
        name: 'Kp Index',
        type: 'bar',
        yAxisIndex: 1,
        data: kp.kp,
        barMaxWidth: 12,
        itemStyle: {
          color: 'rgba(255, 68, 68, 0.38)',
          borderRadius: [2, 2, 0, 0]
        },
        emphasis: { itemStyle: { color: 'rgba(255, 68, 68, 0.6)' } }
      }
    ]
  }
})
</script>

<template>
  <div class="hrv-chart">
    <header class="hrv-chart__header">
      <p class="hrv-chart__eyebrow font-mono text-xs5 tracking-label">HRV TREND</p>
      <p class="hrv-chart__sub font-mono text-xs5">rMSSD · Space weather overlay</p>
    </header>
    <div class="hrv-chart__canvas">
      <VChart :option="option" autoresize />
    </div>
  </div>
</template>

<style scoped>
.hrv-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
  height: 100%;
}

.hrv-chart__header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.hrv-chart__eyebrow {
  margin: 0;
  color: var(--text-primary);
  letter-spacing: 0.15em;
}

.hrv-chart__sub {
  margin: 0;
  color: var(--text-muted);
}

.hrv-chart__canvas {
  height: 200px;
}
</style>
