<script setup lang="ts">
import { computed } from 'vue'
import { useEnvironmentStore } from '@/stores/environment'
import { useProtocolStore } from '@/stores/protocol'
import { useSolarStore } from '@/stores/solar'
import { useSpaceWeatherStore } from '@/stores/spaceWeather'

const solar = useSolarStore()
const protocol = useProtocolStore()
const spaceWeather = useSpaceWeatherStore()
const environment = useEnvironmentStore()

// NOW — current energy phase based on circadian position
const energyPhase = computed(() => {
  const now = solar.now.getTime()
  const wake = protocol.wakeWindowTime.getTime()
  const focusStart = protocol.peakFocusStart.getTime()
  const focusEnd = protocol.peakFocusEnd.getTime()
  const windDown = protocol.windDownStart.getTime()
  const sleep = protocol.sleepTime.getTime()

  if (now < wake)                    return { label: 'Resting',   sub: 'Before wake',   color: '#8899CC' }
  if (now < wake + 7_200_000)        return { label: 'Rising',    sub: 'Cortisol peak',  color: '#FFBD76' }
  if (now < focusStart)              return { label: 'Building',  sub: 'Pre-focus',      color: '#E8C547' }
  if (now < focusEnd)                return { label: 'Peak',      sub: 'Deep work',      color: '#00D4AA' }
  if (now < windDown)                return { label: 'Sustain',   sub: 'Afternoon',      color: '#9B8BFA' }
  if (now < sleep)                   return { label: 'Wind-Down', sub: 'Dim screens',    color: '#5BBFD6' }
  return                                    { label: 'Rest',      sub: 'Sleep window',   color: '#8899CC' }
})

// TONIGHT — sleep quality forecast translated from Kp disruption score
const sleepForecast = computed(() => {
  const score = spaceWeather.disruptionScore
  const kp = `Kp ${spaceWeather.kpIndex.toFixed(1)}`
  if (score < 1) return { label: 'Optimal',   sub: kp, color: '#00D4AA' }
  if (score < 2) return { label: 'Good',      sub: kp, color: '#00D4AA' }
  if (score < 3) return { label: 'Moderate',  sub: kp, color: '#E8C547' }
  return               { label: 'Disrupted',  sub: kp, color: '#FF4444' }
})

// OUTDOOR — UV index with plain label
const uvStatus = computed(() => {
  const uv = environment.uvIndexNow
  if (uv <= 2)  return { label: 'Low',       sub: `UV ${uv}`, color: '#00D4AA' }
  if (uv <= 5)  return { label: 'Moderate',  sub: `UV ${uv}`, color: '#E8C547' }
  if (uv <= 7)  return { label: 'High',      sub: `UV ${uv}`, color: '#FFBD76' }
  if (uv <= 10) return { label: 'Very High', sub: `UV ${uv}`, color: '#FF4444' }
  return              { label: 'Extreme',    sub: `UV ${uv}`, color: '#FF4444' }
})
</script>

<template>
  <div class="hs-card">
    <!-- NOW -->
    <div class="hs-cell">
      <span class="hs-label">NOW</span>
      <span class="hs-value" :style="{ color: energyPhase.color }">{{ energyPhase.label }}</span>
      <span class="hs-sub">{{ energyPhase.sub }}</span>
    </div>

    <div class="hs-divider" />

    <!-- TONIGHT -->
    <div class="hs-cell">
      <span class="hs-label">TONIGHT</span>
      <span class="hs-value" :style="{ color: sleepForecast.color }">{{ sleepForecast.label }}</span>
      <span class="hs-sub">{{ sleepForecast.sub }}</span>
    </div>

    <div class="hs-divider" />

    <!-- OUTDOOR -->
    <div class="hs-cell">
      <span class="hs-label">OUTDOOR</span>
      <span class="hs-value" :style="{ color: uvStatus.color }">{{ uvStatus.label }}</span>
      <span class="hs-sub">{{ uvStatus.sub }}</span>
    </div>
  </div>
</template>

<style scoped>
.hs-card {
  display: flex;
  align-items: stretch;
  background: color-mix(in srgb, #00D4AA 22%, #07111a);
  border: 1px solid rgba(0, 212, 170, 0.28);
  border-radius: 0.875rem;
  padding: 0.65rem 0.8rem;
  gap: 0;
}

.hs-cell {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.18rem;
  padding: 0 0.5rem;
}

.hs-cell:first-child {
  padding-left: 0;
}

.hs-cell:last-child {
  padding-right: 0;
}

.hs-divider {
  width: 1px;
  background: rgba(0, 212, 170, 0.12);
  align-self: stretch;
  flex-shrink: 0;
}

.hs-label {
  font-family: var(--font-mono);
  font-size: 0.38rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(0, 212, 170, 0.52);
}

.hs-value {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  line-height: 1.1;
}

.hs-sub {
  font-family: var(--font-mono);
  font-size: 0.36rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: rgba(255, 245, 225, 0.38);
  text-transform: uppercase;
}
</style>
