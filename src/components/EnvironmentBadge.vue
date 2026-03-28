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
  <div class="env">
    <span class="env-label font-mono">ENVIRONMENT</span>

    <div class="env-grid">
      <div class="env-item">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="4" :stroke="uvColor" stroke-width="1.5" fill="none"/>
          <line x1="9" y1="1" x2="9" y2="4" :stroke="uvColor" stroke-width="1"/>
          <line x1="9" y1="14" x2="9" y2="17" :stroke="uvColor" stroke-width="1"/>
          <line x1="1" y1="9" x2="4" y2="9" :stroke="uvColor" stroke-width="1"/>
          <line x1="14" y1="9" x2="17" y2="9" :stroke="uvColor" stroke-width="1"/>
        </svg>
        <span class="env-val font-mono" :style="{ color: uvColor }">{{ env.uvIndexNow }}</span>
        <span class="env-k font-mono">UV</span>
      </div>

      <div class="env-item">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <rect x="7" y="2" width="4" height="12" rx="2" stroke="var(--text-muted)" stroke-width="1" fill="none"/>
          <circle cx="9" cy="14" r="2.5" stroke="var(--text-muted)" stroke-width="1" fill="none"/>
        </svg>
        <span class="env-val font-mono">{{ Math.round(env.temperatureNow) }}°</span>
        <span class="env-k font-mono">TEMP</span>
      </div>

      <div class="env-item">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 2 C9 2 4 8 4 11 C4 14 6.5 16 9 16 C11.5 16 14 14 14 11 C14 8 9 2 9 2Z" :stroke="aqiColor" stroke-width="1" fill="none"/>
        </svg>
        <span class="env-val font-mono" :style="{ color: aqiColor }">{{ env.aqiLevel }}</span>
        <span class="env-k font-mono">AQI · {{ aqiLabel }}</span>
      </div>

      <div class="env-item">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 3 L9 8 M5 12 C5 9.8 6.8 8 9 8 C11.2 8 13 9.8 13 12 C13 14.2 11.2 16 9 16 C6.8 16 5 14.2 5 12Z" stroke="var(--text-muted)" stroke-width="1" fill="none"/>
        </svg>
        <span class="env-val font-mono">{{ env.humidity }}%</span>
        <span class="env-k font-mono">HUMID</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.env { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; }
.env-label { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.15em; color: var(--text-muted); }
.env-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.4rem; width: 100%; max-width: 220px; }
.env-item {
  display: flex; flex-direction: column; align-items: center; gap: 0.15rem;
  padding: 0.4rem 0.25rem;
  border: 1px solid var(--border-subtle); border-radius: 4px;
}
.env-val { font-size: 0.85rem; font-weight: 700; color: var(--text-primary); line-height: 1; }
.env-k { font-size: 0.35rem; letter-spacing: 0.1em; color: var(--text-muted); text-align: center; }
</style>
