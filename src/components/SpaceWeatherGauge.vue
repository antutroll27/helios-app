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
  <div class="flex flex-col items-center text-center gap-2.5 py-1">
    <span class="font-mono text-[0.7rem] font-semibold tracking-[0.15em] text-(--text-muted)">GEOMAGNETIC</span>

    <div class="flex flex-col items-center gap-1.5">
      <div class="w-[52px] h-[52px] rounded-full flex items-center justify-center shrink-0" :style="{ background: scoreColor }">
        <component :is="scoreIcon" :size="18" color="#0A171D" :stroke-width="2.5" />
      </div>
      <div class="flex flex-col items-center gap-[0.1rem]">
        <span class="font-display text-[0.9rem] font-bold tracking-[0.08em] uppercase" :style="{ color: scoreColor }">{{ sw.disruptionLabel }}</span>
        <span class="text-[0.7rem] text-(--text-secondary) leading-[1.3]">{{ friendlyMessage }}</span>
      </div>
    </div>

    <div class="font-mono flex items-center gap-[0.3rem] text-[0.7rem] text-(--text-muted) tracking-[0.05em]">
      <span class="text-[0.5rem] pulse-live" :style="{ color: scoreColor }">●</span>
      <span>Kp {{ sw.kpIndex.toFixed(1) }} · Wind {{ sw.solarWindSpeed }}km/s</span>
    </div>
  </div>
</template>
