<script setup lang="ts">
import { computed } from 'vue'
import { useBiometricsStore } from '@/stores/biometrics'

const biometrics = useBiometricsStore()

const VB_W = 500
const VB_H = 110

const bars = computed(() => {
  const { dates, deep, rem, light } = biometrics.sleepArchitectureSeries
  const totals = dates.map((_, i) => (deep[i] ?? 0) + (rem[i] ?? 0) + (light[i] ?? 0))
  const maxTotal = Math.max(...totals, 1)
  const n = dates.length
  const colW = VB_W / n
  const barW = Math.max(5, colW * 0.55)

  return dates.map((date, i) => {
    const x = colW * i + (colW - barW) / 2
    const dH = ((deep[i]  ?? 0) / maxTotal) * VB_H
    const rH = ((rem[i]   ?? 0) / maxTotal) * VB_H
    const lH = ((light[i] ?? 0) / maxTotal) * VB_H
    return {
      date, x, barW,
      deep:  { y: VB_H - dH,           h: dH },
      rem:   { y: VB_H - dH - rH,      h: rH },
      light: { y: VB_H - dH - rH - lH, h: lH }
    }
  })
})
</script>

<template>
  <div class="arch-chart">
    <header class="arch-chart__header">
      <p class="font-mono text-xs5 tracking-label arch-chart__eyebrow">SLEEP ARCHITECTURE</p>
      <div class="arch-chart__legend">
        <span class="font-mono text-xs5 arch-chart__leg-item">
          <span class="arch-chart__dot" style="background:#9B8BFA"></span>Deep
        </span>
        <span class="font-mono text-xs5 arch-chart__leg-item">
          <span class="arch-chart__dot" style="background:#00D4AA"></span>REM
        </span>
        <span class="font-mono text-xs5 arch-chart__leg-item">
          <span class="arch-chart__dot" style="background:rgba(255,246,233,0.25)"></span>Light
        </span>
      </div>
    </header>
    <svg :viewBox="`0 0 ${VB_W} ${VB_H}`" preserveAspectRatio="none" class="arch-chart__svg">
      <g v-for="bar in bars" :key="bar.date">
        <rect v-if="bar.light.h > 0" :x="bar.x" :y="bar.light.y" :width="bar.barW" :height="bar.light.h"
              fill="rgba(255,246,233,0.12)" :rx="2"/>
        <rect v-if="bar.rem.h > 0"   :x="bar.x" :y="bar.rem.y"   :width="bar.barW" :height="bar.rem.h"
              fill="#00D4AA" opacity="0.65" :rx="2"/>
        <rect v-if="bar.deep.h > 0"  :x="bar.x" :y="bar.deep.y"  :width="bar.barW" :height="bar.deep.h"
              fill="#9B8BFA" opacity="0.8" :rx="2"/>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.arch-chart { display: flex; flex-direction: column; gap: 0.625rem; height: 100%; }
.arch-chart__header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; flex-shrink: 0; }
.arch-chart__eyebrow { margin: 0; color: var(--text-primary); }
.arch-chart__legend { display: flex; gap: 0.75rem; }
.arch-chart__leg-item { color: var(--text-muted); display: flex; align-items: center; gap: 0.3rem; }
.arch-chart__dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.arch-chart__svg { width: 100%; flex: 1; min-height: 80px; height: 0; display: block; }
</style>
