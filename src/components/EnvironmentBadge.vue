<script setup lang="ts">
import { computed } from 'vue'
import { useEnvironmentStore } from '@/stores/environment'

const env = useEnvironmentStore()

const uvColor = computed(() => {
  if (env.uvIndexNow < 3) return '#00D4AA'
  if (env.uvIndexNow <= 6) return '#FFBD76'
  return '#FF4444'
})

const aqiColor = computed(() => {
  if (env.aqiLevel < 50) return '#00D4AA'
  if (env.aqiLevel < 100) return '#FFBD76'
  if (env.aqiLevel < 150) return '#F97316'
  return '#FF4444'
})
</script>

<template>
  <div class="env telemetry-module" style="--telemetry-glow: rgba(94, 234, 212, 0.08);">
    <div class="env__header telemetry-module__header">
      <span class="telemetry-module__label font-mono">ENVIRONMENT</span>
      <span class="telemetry-module__chip font-mono">LOCAL</span>
    </div>

    <div class="env__grid telemetry-module__metrics">
      <div class="env__item telemetry-module__metric">
        <span class="telemetry-module__metric-label font-mono">UV</span>
        <span class="env__val telemetry-module__metric-value font-mono" :style="{ color: uvColor }">{{ env.uvIndexNow }}</span>
      </div>
      <div class="env__item telemetry-module__metric">
        <span class="telemetry-module__metric-label font-mono">TEMP</span>
        <span class="env__val telemetry-module__metric-value font-mono">{{ Math.round(env.temperatureNow) }}&deg;</span>
      </div>
      <div class="env__item telemetry-module__metric">
        <span class="telemetry-module__metric-label font-mono">AQI</span>
        <span class="env__val telemetry-module__metric-value font-mono" :style="{ color: aqiColor }">{{ env.aqiLevel }}</span>
      </div>
      <div class="env__item telemetry-module__metric">
        <span class="telemetry-module__metric-label font-mono">HUMID</span>
        <span class="env__val telemetry-module__metric-value font-mono">{{ env.humidity }}%</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.env__grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.env__val {
  line-height: 1;
}

@media (max-width: 480px) {
  .env__grid {
    grid-template-columns: 1fr;
  }
}
</style>
