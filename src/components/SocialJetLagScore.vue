<script setup lang="ts">
import { computed } from 'vue'
import { getAlignmentMetricCopy } from '@/lib/circadianTruth'
import { useProtocolStore } from '@/stores/protocol'

const protocol = useProtocolStore()
const copy = getAlignmentMetricCopy()

const minutes = computed(() => Math.min(protocol.solarAlignmentGapMinutes, 360))

const color = computed(() => {
  if (minutes.value < 30) return '#00D4AA'
  if (minutes.value <= 90) return '#FFBD76'
  return '#FF4444'
})

const status = computed(() => {
  if (minutes.value < 30) return 'Aligned'
  if (minutes.value <= 90) return 'Moderate'
  return 'Misaligned'
})
</script>

<template>
  <div class="sjl telemetry-module" style="--telemetry-glow: rgba(255, 189, 118, 0.08);">
    <div class="sjl__header telemetry-module__header">
      <span class="telemetry-module__label font-mono">{{ copy.label }}</span>
      <span class="telemetry-module__chip font-mono" :style="{ color }">{{ status }}</span>
    </div>

    <div class="sjl__body telemetry-module__body">
      <div class="sjl__readout telemetry-module__metric" :style="{ borderColor: `${color}3D`, background: `${color}12` }">
        <span class="sjl__num font-mono" :style="{ color }">{{ minutes }}</span>
        <span class="sjl__unit font-mono">MIN</span>
      </div>
      <p class="sjl__desc telemetry-module__message">{{ copy.description }}</p>
    </div>
  </div>
</template>

<style scoped>
.sjl__readout {
  display: inline-flex;
  align-items: baseline;
  gap: 0.35rem;
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(255, 189, 118, 0.24);
  background: rgba(19, 10, 8, 0.42);
}

.sjl__num {
  font-size: 1.6rem;
  line-height: 1;
  font-weight: 800;
}

.sjl__unit {
  font-size: 0.52rem;
  letter-spacing: 0.16em;
  color: rgba(148, 163, 184, 0.74);
}

.sjl__desc {
  max-width: 14rem;
}
</style>
