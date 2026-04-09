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
  <div class="env">
    <div class="env__header">
      <span class="env__label font-mono">ENVIRONMENT</span>
      <span class="env__stamp font-mono">LOCAL</span>
    </div>

    <div class="env__grid">
      <div class="env__item">
        <span class="env__k font-mono">UV</span>
        <span class="env__val font-mono" :style="{ color: uvColor }">{{ env.uvIndexNow }}</span>
      </div>
      <div class="env__item">
        <span class="env__k font-mono">TEMP</span>
        <span class="env__val font-mono">{{ Math.round(env.temperatureNow) }}&deg;</span>
      </div>
      <div class="env__item">
        <span class="env__k font-mono">AQI</span>
        <span class="env__val font-mono" :style="{ color: aqiColor }">{{ env.aqiLevel }}</span>
      </div>
      <div class="env__item">
        <span class="env__k font-mono">HUMID</span>
        <span class="env__val font-mono">{{ env.humidity }}%</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.env {
  display: grid;
  gap: 0.75rem;
  padding: 0.95rem 0.95rem 1rem;
  border-radius: 1.15rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background:
    linear-gradient(180deg, rgba(7, 14, 27, 0.9), rgba(7, 14, 27, 0.74)),
    radial-gradient(circle at bottom left, rgba(94, 234, 212, 0.08), transparent 48%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 18px 40px rgba(2, 8, 20, 0.22);
}

.env__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.env__label,
.env__stamp {
  font-size: 0.58rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.78);
}

.env__stamp {
  padding: 0.3rem 0.55rem;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(4, 10, 21, 0.7);
}

.env__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.env__item {
  display: grid;
  gap: 0.18rem;
  padding: 0.58rem 0.65rem;
  border-radius: 0.9rem;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(3, 10, 22, 0.42);
}

.env__k {
  font-size: 0.5rem;
  letter-spacing: 0.16em;
  color: rgba(148, 163, 184, 0.72);
}

.env__val {
  font-size: 0.8rem;
  line-height: 1;
  font-weight: 700;
  color: rgba(226, 232, 240, 0.96);
}

@media (max-width: 480px) {
  .env__grid {
    grid-template-columns: 1fr;
  }
}
</style>
