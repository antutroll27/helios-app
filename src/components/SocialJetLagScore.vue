<script setup lang="ts">
import { computed } from 'vue'
import { useProtocolStore } from '@/stores/protocol'

const protocol = useProtocolStore()

const minutes = computed(() => Math.min(protocol.socialJetLagMinutes, 360))

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
    <span class="sjl-label font-mono">SOCIAL JET LAG</span>

    <div class="sjl-main">
      <div class="sjl-circle" :style="{ borderColor: color }">
        <span class="sjl-num font-mono" :style="{ color }">{{ minutes }}</span>
        <span class="sjl-unit font-mono">MIN</span>
      </div>
    </div>

    <span class="sjl-status font-display" :style="{ color }">{{ status }}</span>
    <span class="sjl-desc">Delta between solar midnight and your sleep midpoint</span>
  </div>
</template>

<style scoped>
.sjl { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; text-align: center; padding: 0.25rem 0; }
.sjl-label { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.15em; color: var(--text-muted); }
.sjl-main { display: flex; justify-content: center; }
.sjl-circle {
  width: 80px; height: 80px; border-radius: 50%;
  border: 3px solid; background: var(--bg-primary);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
:root.light .sjl-circle { background: #0A171D; }
.sjl-num { font-size: 1.5rem; font-weight: 800; line-height: 1; }
.sjl-unit { font-size: 0.45rem; letter-spacing: 0.1em; color: var(--text-muted); }
.sjl-status { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }
.sjl-desc { font-size: 0.7rem; color: var(--text-muted); line-height: 1.35; max-width: 180px; }
</style>
