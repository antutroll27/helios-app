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
  if (s <= 4) return 'Storm active - start wind-down earlier'
  return 'Major storm - expect disrupted sleep'
})
</script>

<template>
  <div class="sw telemetry-module" style="--telemetry-glow: rgba(0, 212, 170, 0.08);">
    <div class="sw__header telemetry-module__header">
      <span class="telemetry-module__label font-mono">GEOMAGNETIC</span>
      <span class="telemetry-module__chip font-mono">LIVE</span>
    </div>

    <div class="sw__body telemetry-module__body">
      <div class="telemetry-module__signal" :style="{ color: scoreColor }">
        <component :is="scoreIcon" :size="16" :color="scoreColor" :stroke-width="2.1" />
        <span class="telemetry-module__status font-display">{{ sw.disruptionLabel }}</span>
      </div>

      <p class="telemetry-module__message">{{ friendlyMessage }}</p>

      <dl class="sw__metrics telemetry-module__metrics font-mono">
        <div class="telemetry-module__metric">
          <dt class="telemetry-module__metric-label">Kp</dt>
          <dd class="telemetry-module__metric-value">{{ sw.kpIndex.toFixed(1) }}</dd>
        </div>
        <div class="telemetry-module__metric">
          <dt class="telemetry-module__metric-label">Wind</dt>
          <dd class="telemetry-module__metric-value">{{ sw.solarWindSpeed }} km/s</dd>
        </div>
      </dl>
    </div>
  </div>
</template>
