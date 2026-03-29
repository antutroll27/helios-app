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
  <div class="flex flex-col items-center gap-2 text-center py-1">
    <span class="font-mono text-[0.7rem] font-semibold tracking-[0.15em] text-(--text-muted)">SOCIAL JET LAG</span>

    <div class="flex justify-center">
      <div class="w-20 h-20 rounded-full border-3 border-solid bg-(--bg-primary) flex flex-col items-center justify-center" :style="{ borderColor: color }">
        <span class="font-mono text-2xl font-extrabold leading-none" :style="{ color }">{{ minutes }}</span>
        <span class="font-mono text-[0.45rem] tracking-widest text-(--text-muted)">MIN</span>
      </div>
    </div>

    <span class="font-display text-[0.7rem] font-bold tracking-widest uppercase" :style="{ color }">{{ status }}</span>
    <span class="text-[0.7rem] text-(--text-muted) leading-[1.35] max-w-45">Delta between solar midnight and your sleep midpoint</span>
  </div>
</template>

<style scoped>
:root.light .sjl-circle { background: #0A171D; }
</style>
