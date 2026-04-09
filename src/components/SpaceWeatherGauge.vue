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
  <div class="sw">
    <div class="sw__header">
      <span class="sw__label font-mono">GEOMAGNETIC</span>
      <span class="sw__live font-mono">LIVE</span>
    </div>

    <div class="sw__body">
      <div class="sw__signal" :style="{ color: scoreColor }">
        <component :is="scoreIcon" :size="16" :color="scoreColor" :stroke-width="2.1" />
        <span class="sw__status font-display">{{ sw.disruptionLabel }}</span>
      </div>

      <p class="sw__message">{{ friendlyMessage }}</p>

      <dl class="sw__metrics font-mono">
        <div>
          <dt>Kp</dt>
          <dd>{{ sw.kpIndex.toFixed(1) }}</dd>
        </div>
        <div>
          <dt>Wind</dt>
          <dd>{{ sw.solarWindSpeed }} km/s</dd>
        </div>
      </dl>
    </div>
  </div>
</template>

<style scoped>
.sw {
  display: grid;
  gap: 0.75rem;
  padding: 0.95rem 0.95rem 1rem;
  border-radius: 1.15rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background:
    linear-gradient(180deg, rgba(7, 14, 27, 0.9), rgba(7, 14, 27, 0.74)),
    radial-gradient(circle at top left, rgba(0, 212, 170, 0.08), transparent 48%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 18px 40px rgba(2, 8, 20, 0.22);
}

.sw__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.sw__label,
.sw__live {
  font-size: 0.58rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.78);
}

.sw__live {
  padding: 0.3rem 0.55rem;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(4, 10, 21, 0.7);
}

.sw__body {
  display: grid;
  gap: 0.7rem;
}

.sw__signal {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
}

.sw__status {
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.sw__message {
  margin: 0;
  font-size: 0.72rem;
  line-height: 1.35;
  color: rgba(226, 232, 240, 0.72);
  max-width: 14rem;
}

.sw__metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
}

.sw__metrics > div {
  display: grid;
  gap: 0.18rem;
  padding: 0.58rem 0.65rem;
  border-radius: 0.9rem;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(3, 10, 22, 0.42);
}

.sw__metrics dt {
  font-size: 0.5rem;
  letter-spacing: 0.16em;
  color: rgba(148, 163, 184, 0.72);
}

.sw__metrics dd {
  margin: 0;
  font-size: 0.72rem;
  color: rgba(226, 232, 240, 0.96);
}
</style>
