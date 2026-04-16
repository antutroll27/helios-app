import type { EChartsOption } from 'echarts'

export function useBiometricsChartTheme(): Partial<EChartsOption> {
  return {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 600,
    textStyle: {
      fontFamily: "'Geist Mono', 'JetBrains Mono', monospace",
      color: 'rgba(255, 246, 233, 0.55)',
      fontSize: 10
    },
    grid: {
      left: 52,
      right: 20,
      top: 24,
      bottom: 36,
      containLabel: false
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.12)' } },
      axisTick: { show: false },
      axisLabel: {
        color: 'rgba(255, 246, 233, 0.45)',
        fontSize: 9,
        fontFamily: "'Geist Mono', 'JetBrains Mono', monospace"
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: 'rgba(255, 246, 233, 0.45)',
        fontSize: 9,
        fontFamily: "'Geist Mono', 'JetBrains Mono', monospace"
      },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.08)', type: 'dashed' } }
    },
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
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        height: 18,
        bottom: 4,
        borderColor: 'rgba(148, 163, 184, 0.15)',
        backgroundColor: 'rgba(7, 17, 26, 0.4)',
        fillerColor: 'rgba(0, 212, 170, 0.12)',
        handleStyle: { color: '#00D4AA', borderColor: '#00D4AA' },
        textStyle: { color: 'transparent' },
        showDetail: false
      }
    ]
  }
}
