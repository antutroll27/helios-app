<script setup lang="ts">
import { computed } from 'vue'

interface DialData {
  sleepWindowStart: number
  sleepWindowEnd:   number
  peakAlertStart:   number
  peakAlertEnd:     number
  dlmoAngle:        number
  solarNoonAngle:   number
}

const props = defineProps<{
  data: DialData | null
  nowAngle: number
}>()

const CX = 100
const CY = 100
const R  = 88
const CIRC = 2 * Math.PI * R  // ≈ 552.9

// Convert degrees (0=midnight, clockwise) to SVG (x, y) at given radius
function angleToXY(deg: number, r: number) {
  const rad = ((deg - 90) * Math.PI) / 180
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) }
}

// stroke-dasharray / stroke-dashoffset for an arc from angleStart to angleEnd
function arcDash(angleStart: number, angleEnd: number) {
  const delta   = ((angleEnd - angleStart + 360) % 360)
  const dashLen = (delta / 360) * CIRC
  const offset  = CIRC - (angleStart / 360) * CIRC + CIRC * 0.25
  return {
    strokeDasharray:  `${dashLen} ${CIRC - dashLen}`,
    strokeDashoffset: offset,
  }
}

const sleepArc    = computed(() => props.data ? arcDash(props.data.sleepWindowStart, props.data.sleepWindowEnd) : null)
const peakArc     = computed(() => props.data ? arcDash(props.data.peakAlertStart,  props.data.peakAlertEnd)   : null)
const dlmoDot     = computed(() => props.data ? angleToXY(props.data.dlmoAngle, R)     : null)
const solarDot    = computed(() => props.data ? angleToXY(props.data.solarNoonAngle, R) : null)
const nowNeedle   = computed(() => angleToXY(props.nowAngle, 72))

// Hour labels at 00/06/12/18
const hourLabels = [
  { label: '00', ...angleToXY(0,   R + 12) },
  { label: '06', ...angleToXY(90,  R + 12) },
  { label: '12', ...angleToXY(180, R + 12) },
  { label: '18', ...angleToXY(270, R + 12) },
]
</script>

<template>
  <div class="body-clock-dial bento-card">
    <div class="body-clock-dial__header">
      <span class="body-clock-dial__label">BODY CLOCK</span>
      <span class="body-clock-dial__sub">24h circadian phase</span>
    </div>

    <div class="body-clock-dial__svg-wrap">
      <svg viewBox="0 0 200 200" class="body-clock-dial__svg" aria-label="24-hour body clock dial">

        <!-- Track ring -->
        <circle :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="rgba(255,246,233,0.06)" stroke-width="14" />

        <!-- Sleep window arc (violet) -->
        <circle v-if="sleepArc" :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="#9B8BFA" stroke-width="14" opacity="0.5"
          :stroke-dasharray="sleepArc.strokeDasharray"
          :stroke-dashoffset="sleepArc.strokeDashoffset"
          stroke-linecap="round">
          <title>Sleep window</title>
        </circle>

        <!-- Peak alertness arc (teal, thinner) -->
        <circle v-if="peakArc" :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="#00D4AA" stroke-width="8" opacity="0.45"
          :stroke-dasharray="peakArc.strokeDasharray"
          :stroke-dashoffset="peakArc.strokeDashoffset"
          stroke-linecap="round">
          <title>Peak alertness window</title>
        </circle>

        <!-- Solar noon dot -->
        <circle v-if="solarDot"
          :cx="solarDot.x" :cy="solarDot.y" r="4"
          fill="#FFBD76" opacity="0.5">
          <title>Solar noon</title>
        </circle>

        <!-- DLMO dot -->
        <circle v-if="dlmoDot"
          :cx="dlmoDot.x" :cy="dlmoDot.y" r="5"
          fill="#9B8BFA" stroke="#FFF6E9" stroke-width="1.5">
          <title>DLMO (melatonin onset)</title>
        </circle>

        <!-- Hour labels -->
        <text v-for="h in hourLabels" :key="h.label"
          :x="h.x" :y="h.y"
          text-anchor="middle" dominant-baseline="middle"
          fill="rgba(255,246,233,0.3)"
          font-size="9"
          font-family="'Geist Mono', monospace">
          {{ h.label }}
        </text>

        <!-- Now needle -->
        <line :x1="CX" :y1="CY" :x2="nowNeedle.x" :y2="nowNeedle.y"
          stroke="rgba(255,246,233,0.85)" stroke-width="1.5" stroke-linecap="round" />

        <!-- Centre dot -->
        <circle :cx="CX" :cy="CY" r="3.5" fill="#FFF6E9" />

        <!-- Empty state -->
        <text v-if="!data"
          x="100" y="105"
          text-anchor="middle" fill="rgba(255,246,233,0.2)"
          font-size="18" font-family="'Geist Mono', monospace">
          –
        </text>
      </svg>
    </div>

    <!-- Legend -->
    <div v-if="data" class="body-clock-dial__legend">
      <span class="legend-item legend-item--violet">Sleep</span>
      <span class="legend-item legend-item--teal">Peak</span>
      <span class="legend-item legend-item--nectarine">Solar noon</span>
    </div>
  </div>
</template>

<style scoped>
.body-clock-dial {
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.body-clock-dial__header {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.body-clock-dial__label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.body-clock-dial__sub {
  font-size: 0.5rem;
  color: var(--text-muted);
}

.body-clock-dial__svg-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
}

.body-clock-dial__svg {
  width: 100%;
  max-width: 180px;
  height: auto;
}

.body-clock-dial__legend {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
}

.legend-item {
  font-family: 'Geist Mono', monospace;
  font-size: 0.45rem;
  letter-spacing: 0.05em;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.legend-item::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 3px;
  border-radius: 2px;
}

.legend-item--violet::before  { background: #9B8BFA; }
.legend-item--teal::before    { background: #00D4AA; }
.legend-item--nectarine::before { background: #FFBD76; }
</style>
