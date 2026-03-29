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

const aqiLabel = computed(() => {
  if (env.aqiLevel < 50) return 'Good'
  if (env.aqiLevel < 100) return 'Moderate'
  if (env.aqiLevel < 150) return 'Unhealthy'
  return 'Hazardous'
})
</script>

<template>
  <div class="flex flex-col items-center gap-2">
    <span class="font-mono text-[0.7rem] font-semibold tracking-[0.15em] text-(--text-muted)">ENVIRONMENT</span>

    <div class="grid grid-cols-2 gap-1.5 w-full max-w-55">
      <div class="flex flex-col items-center gap-[0.15rem] py-1.5 px-1 border border-(--border-subtle) rounded-sm">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="4" :stroke="uvColor" stroke-width="1.5" fill="none"/>
          <line x1="9" y1="1" x2="9" y2="4" :stroke="uvColor" stroke-width="1"/>
          <line x1="9" y1="14" x2="9" y2="17" :stroke="uvColor" stroke-width="1"/>
          <line x1="1" y1="9" x2="4" y2="9" :stroke="uvColor" stroke-width="1"/>
          <line x1="14" y1="9" x2="17" y2="9" :stroke="uvColor" stroke-width="1"/>
        </svg>
        <span class="font-mono text-[0.85rem] font-bold text-(--text-primary) leading-none" :style="{ color: uvColor }">{{ env.uvIndexNow }}</span>
        <span class="font-mono text-[0.35rem] tracking-widest text-(--text-muted) text-center">UV</span>
      </div>

      <div class="flex flex-col items-center gap-[0.15rem] py-1.5 px-1 border border-(--border-subtle) rounded-sm">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <rect x="7" y="2" width="4" height="12" rx="2" stroke="var(--text-muted)" stroke-width="1" fill="none"/>
          <circle cx="9" cy="14" r="2.5" stroke="var(--text-muted)" stroke-width="1" fill="none"/>
        </svg>
        <span class="font-mono text-[0.85rem] font-bold text-(--text-primary) leading-none">{{ Math.round(env.temperatureNow) }}°</span>
        <span class="font-mono text-[0.35rem] tracking-widest text-(--text-muted) text-center">TEMP</span>
      </div>

      <div class="flex flex-col items-center gap-[0.15rem] py-1.5 px-1 border border-(--border-subtle) rounded-sm">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 2 C9 2 4 8 4 11 C4 14 6.5 16 9 16 C11.5 16 14 14 14 11 C14 8 9 2 9 2Z" :stroke="aqiColor" stroke-width="1" fill="none"/>
        </svg>
        <span class="font-mono text-[0.85rem] font-bold text-(--text-primary) leading-none" :style="{ color: aqiColor }">{{ env.aqiLevel }}</span>
        <span class="font-mono text-[0.35rem] tracking-widest text-(--text-muted) text-center">AQI · {{ aqiLabel }}</span>
      </div>

      <div class="flex flex-col items-center gap-[0.15rem] py-1.5 px-1 border border-(--border-subtle) rounded-sm">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 3 L9 8 M5 12 C5 9.8 6.8 8 9 8 C11.2 8 13 9.8 13 12 C13 14.2 11.2 16 9 16 C6.8 16 5 14.2 5 12Z" stroke="var(--text-muted)" stroke-width="1" fill="none"/>
        </svg>
        <span class="font-mono text-[0.85rem] font-bold text-(--text-primary) leading-none">{{ env.humidity }}%</span>
        <span class="font-mono text-[0.35rem] tracking-widest text-(--text-muted) text-center">HUMID</span>
      </div>
    </div>
  </div>
</template>
