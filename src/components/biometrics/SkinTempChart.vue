<script setup lang="ts">
import { computed } from 'vue'
import { useBiometricsStore } from '@/stores/biometrics'

const biometrics = useBiometricsStore()
const VB_W = 400
const VB_H = 80
const MID  = VB_H / 2

const bars = computed(() => {
  const { values: deltas } = biometrics.skinTempSeries
  const maxAbs = Math.max(...deltas.map(d => Math.abs(d ?? 0)), 0.5)
  const n = deltas.length
  const colW = VB_W / n
  const barW = Math.max(4, colW * 0.55)

  return deltas.map((delta, i) => {
    if (delta == null) return null
    const h = (Math.abs(delta) / maxAbs) * (MID - 4)
    const positive = delta >= 0
    return {
      x: colW * i + (colW - barW) / 2,
      barW,
      y: positive ? MID - h : MID,
      h,
      positive
    }
  })
})
</script>

<template>
  <div class="skin-temp">
    <header class="skin-temp__header">
      <p class="font-mono text-xs5 tracking-label skin-temp__eyebrow">SKIN TEMP Δ</p>
      <p class="font-mono text-xs5 skin-temp__sub">°C from baseline</p>
    </header>
    <svg :viewBox="`0 0 ${VB_W} ${VB_H}`" preserveAspectRatio="none" class="skin-temp__svg">
      <line :x1="0" :y1="MID" :x2="VB_W" :y2="MID"
            stroke="rgba(255,246,233,0.15)" stroke-width="0.5" stroke-dasharray="3 3"/>
      <g v-for="(bar, i) in bars" :key="i">
        <rect v-if="bar"
              :x="bar.x" :y="bar.y" :width="bar.barW" :height="Math.max(bar.h, 1)"
              :fill="bar.positive ? 'rgba(255,68,68,0.65)' : 'rgba(0,212,170,0.65)'"
              :rx="2"/>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.skin-temp { display: flex; flex-direction: column; gap: 0.625rem; height: 100%; }
.skin-temp__header { display: flex; align-items: center; gap: 0.625rem; flex-shrink: 0; }
.skin-temp__eyebrow { margin: 0; color: var(--text-primary); }
.skin-temp__sub { margin: 0; color: var(--text-muted); }
.skin-temp__svg { width: 100%; flex: 1; min-height: 60px; height: 0; display: block; }
</style>
