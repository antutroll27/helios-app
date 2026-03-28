<script setup lang="ts">
import { computed } from 'vue'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'
import { Shield, Zap, AlertTriangle } from 'lucide-vue-next'

const sw = useSpaceWeatherStore()

const scoreColor = computed(() => {
  const s = sw.disruptionScore
  if (s <= 1) return '#00D4AA'
  if (s <= 2) return '#FFBD76'
  if (s <= 4) return '#F97316'
  return '#FF4444'
})

const scoreIcon = computed(() => {
  if (sw.disruptionScore <= 1) return Shield
  if (sw.disruptionScore <= 3) return Zap
  return AlertTriangle
})

const friendlyMessage = computed(() => {
  const s = sw.disruptionScore
  if (s <= 1) return 'Great night for sleep'
  if (s === 2) return 'Minor activity detected'
  if (s <= 4) return 'Storm active — start wind-down earlier'
  return 'Major storm — expect disrupted sleep'
})
</script>

<template>
  <div class="sw">
    <span class="sw-label font-mono">GEOMAGNETIC</span>

    <div class="sw-main">
      <div class="sw-circle" :style="{ background: scoreColor }">
        <component :is="scoreIcon" :size="18" color="#0A171D" :stroke-width="2.5" />
      </div>
      <div class="sw-info">
        <span class="sw-status font-display" :style="{ color: scoreColor }">{{ sw.disruptionLabel }}</span>
        <span class="sw-msg">{{ friendlyMessage }}</span>
      </div>
    </div>

    <div class="sw-live font-mono">
      <span class="sw-dot pulse-live" :style="{ color: scoreColor }">●</span>
      <span>Kp {{ sw.kpIndex.toFixed(1) }} · Wind {{ sw.solarWindSpeed }}km/s</span>
    </div>
  </div>
</template>

<style scoped>
.sw { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 0.6rem; padding: 0.25rem 0; }
.sw-label { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.15em; color: var(--text-muted); }
.sw-main { display: flex; flex-direction: column; align-items: center; gap: 0.4rem; }
.sw-circle {
  width: 52px; height: 52px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.sw-info { display: flex; flex-direction: column; align-items: center; gap: 0.1rem; }
.sw-status { font-size: 0.9rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
.sw-msg { font-size: 0.7rem; color: var(--text-secondary); line-height: 1.3; }
.sw-live {
  display: flex; align-items: center; gap: 0.3rem;
  font-size: 0.7rem; color: var(--text-muted); letter-spacing: 0.05em;
}
.sw-dot { font-size: 0.5rem; }
</style>
