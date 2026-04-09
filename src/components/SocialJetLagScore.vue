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
  <div class="sjl">
    <div class="sjl__header">
      <span class="sjl__label font-mono">{{ copy.label }}</span>
      <span class="sjl__status font-mono" :style="{ color }">{{ status }}</span>
    </div>

    <div class="sjl__body">
      <div class="sjl__readout">
        <span class="sjl__num font-mono" :style="{ color }">{{ minutes }}</span>
        <span class="sjl__unit font-mono">MIN</span>
      </div>
      <p class="sjl__desc">{{ copy.description }}</p>
    </div>
  </div>
</template>

<style scoped>
.sjl {
  display: grid;
  gap: 0.75rem;
  padding: 0.95rem 0.95rem 1rem;
  border-radius: 1.15rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background:
    linear-gradient(180deg, rgba(7, 14, 27, 0.9), rgba(7, 14, 27, 0.74)),
    radial-gradient(circle at top right, rgba(255, 189, 118, 0.08), transparent 48%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 18px 40px rgba(2, 8, 20, 0.22);
}

.sjl__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.sjl__label,
.sjl__status {
  font-size: 0.58rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.sjl__label {
  color: rgba(148, 163, 184, 0.78);
}

.sjl__body {
  display: grid;
  gap: 0.7rem;
}

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
  margin: 0;
  max-width: 14rem;
  font-size: 0.72rem;
  line-height: 1.35;
  color: rgba(226, 232, 240, 0.72);
}
</style>
