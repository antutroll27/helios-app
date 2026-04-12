<script setup lang="ts">
import { computed, ref } from 'vue'

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

const CX   = 100
const CY   = 100
const R    = 84
const CIRC = 2 * Math.PI * R

// Convert angle (0=midnight, clockwise) to SVG x,y
function angleToXY(deg: number, r: number) {
  const rad = ((deg - 90) * Math.PI) / 180
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) }
}

// Arc stroke-dash for circle-based arcs
function arcDash(angleStart: number, angleEnd: number) {
  const delta   = ((angleEnd - angleStart + 360) % 360)
  const dashLen = (delta / 360) * CIRC
  const offset  = CIRC - (angleStart / 360) * CIRC + CIRC * 0.25
  return {
    strokeDasharray:  `${dashLen.toFixed(1)} ${(CIRC - dashLen).toFixed(1)}`,
    strokeDashoffset: offset.toFixed(1),
  }
}

// Convert angle back to "HH:MM" string
function angleToTime(deg: number): string {
  const wrapped = ((deg % 360) + 360) % 360
  const totalMin = Math.round((wrapped / 360) * 1440)
  const h = Math.floor(totalMin / 60) % 24
  const m = totalMin % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

// Arc span in hours (for display)
function arcSpanH(start: number, end: number): string {
  const delta = ((end - start + 360) % 360)
  const h = delta / 15
  return `${h.toFixed(0)}h`
}

const sleepArc  = computed(() => props.data ? arcDash(props.data.sleepWindowStart, props.data.sleepWindowEnd) : null)
const peakArc   = computed(() => props.data ? arcDash(props.data.peakAlertStart,  props.data.peakAlertEnd)   : null)
const dlmoDot   = computed(() => props.data ? angleToXY(props.data.dlmoAngle, R)      : null)
const solarDot  = computed(() => props.data ? angleToXY(props.data.solarNoonAngle, R) : null)
const nowNeedle = computed(() => angleToXY(props.nowAngle, 68))

// Current time text for needle label
const nowTime = computed(() => {
  const totalMin = Math.round((props.nowAngle / 360) * 1440)
  const h = Math.floor(totalMin / 60) % 24
  const m = totalMin % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
})

// Computed time strings for the info strip
const sleepOnset  = computed(() => props.data ? angleToTime(props.data.sleepWindowStart) : null)
const wakeTime    = computed(() => props.data ? angleToTime(props.data.sleepWindowEnd)   : null)
const dlmoTime    = computed(() => props.data ? angleToTime(props.data.dlmoAngle)        : null)
const peakDuration = computed(() => props.data ? arcSpanH(props.data.peakAlertStart, props.data.peakAlertEnd) : null)
const sleepDuration = computed(() => props.data ? arcSpanH(props.data.sleepWindowStart, props.data.sleepWindowEnd) : null)

// Hover state for dial info tooltip
const hoveredArc = ref<'sleep' | 'peak' | null>(null)

const hourLabels = [
  { label: '00', ...angleToXY(0,   R + 14) },
  { label: '06', ...angleToXY(90,  R + 14) },
  { label: '12', ...angleToXY(180, R + 14) },
  { label: '18', ...angleToXY(270, R + 14) },
]
</script>

<template>
  <div class="body-clock-dial bento-card">
    <!-- Header -->
    <div class="body-clock-dial__header">
      <div>
        <div class="body-clock-dial__title">BODY CLOCK</div>
        <div class="body-clock-dial__sub">24h circadian phase · now {{ nowTime }}</div>
      </div>
    </div>

    <!-- SVG dial -->
    <div class="body-clock-dial__svg-wrap">
      <svg viewBox="0 0 200 200" class="body-clock-dial__svg"
        aria-label="24-hour body clock dial">

        <!-- Track ring -->
        <circle :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="rgba(255,246,233,0.05)" stroke-width="16" />

        <!-- Sleep window arc (violet) — hover lifts opacity -->
        <circle v-if="sleepArc" :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="#9B8BFA" stroke-width="16"
          :opacity="hoveredArc === 'sleep' ? 0.75 : 0.45"
          :stroke-dasharray="sleepArc.strokeDasharray"
          :stroke-dashoffset="sleepArc.strokeDashoffset"
          stroke-linecap="round"
          class="dial-arc"
          @mouseenter="hoveredArc = 'sleep'"
          @mouseleave="hoveredArc = null">
          <title>Sleep: {{ sleepOnset }} → {{ wakeTime }}</title>
        </circle>

        <!-- Peak alertness arc (teal) -->
        <circle v-if="peakArc" :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="#00D4AA" stroke-width="8"
          :opacity="hoveredArc === 'peak' ? 0.7 : 0.4"
          :stroke-dasharray="peakArc.strokeDasharray"
          :stroke-dashoffset="peakArc.strokeDashoffset"
          stroke-linecap="round"
          class="dial-arc"
          @mouseenter="hoveredArc = 'peak'"
          @mouseleave="hoveredArc = null">
          <title>Peak alertness: {{ peakDuration }}</title>
        </circle>

        <!-- Solar noon dot -->
        <circle v-if="solarDot"
          :cx="solarDot.x" :cy="solarDot.y" r="4.5"
          fill="#FFBD76" opacity="0.55">
          <title>Solar noon</title>
        </circle>

        <!-- DLMO dot — larger with label -->
        <circle v-if="dlmoDot"
          :cx="dlmoDot.x" :cy="dlmoDot.y" r="5.5"
          fill="#9B8BFA" stroke="rgba(10,23,29,0.8)" stroke-width="2"
          class="dial-dot">
          <title>DLMO {{ dlmoTime }}</title>
        </circle>

        <!-- Hour labels -->
        <text v-for="h in hourLabels" :key="h.label"
          :x="h.x" :y="h.y"
          text-anchor="middle" dominant-baseline="middle"
          fill="rgba(255,246,233,0.25)"
          font-size="8"
          font-family="'Geist Mono', monospace">
          {{ h.label }}
        </text>

        <!-- Now needle -->
        <line :x1="CX" :y1="CY" :x2="nowNeedle.x" :y2="nowNeedle.y"
          stroke="rgba(255,246,233,0.9)" stroke-width="1.5" stroke-linecap="round" />

        <!-- Centre dot -->
        <circle :cx="CX" :cy="CY" r="4" fill="#FFF6E9" opacity="0.9" />

        <!-- Hover arc tooltip — rendered as SVG foreignObject isn't reliable, use CSS below -->

        <!-- Empty state -->
        <text v-if="!data"
          x="100" y="108"
          text-anchor="middle" fill="rgba(255,246,233,0.18)"
          font-size="11" font-family="'Geist Mono', monospace">
          No data yet
        </text>
      </svg>

      <!-- Arc hover tooltip (CSS positioned within svg-wrap) -->
      <div v-if="hoveredArc === 'sleep' && data" class="dial-arc-tip dial-arc-tip--sleep">
        <span class="dial-arc-tip__icon">💤</span>
        <span class="dial-arc-tip__label">Sleep window</span>
        <span class="dial-arc-tip__val">{{ sleepOnset }} → {{ wakeTime }}</span>
        <span class="dial-arc-tip__dur">{{ sleepDuration }}</span>
      </div>

      <div v-if="hoveredArc === 'peak' && data" class="dial-arc-tip dial-arc-tip--peak">
        <span class="dial-arc-tip__icon">⚡</span>
        <span class="dial-arc-tip__label">Peak alertness</span>
        <span class="dial-arc-tip__dur">{{ peakDuration }} window</span>
      </div>
    </div>

    <!-- Time info strip -->
    <div v-if="data" class="dial-strip">
      <div class="dial-strip__item">
        <span class="dial-strip__dot" style="background:#9B8BFA"></span>
        <span class="dial-strip__key">Sleep</span>
        <span class="dial-strip__val">{{ sleepOnset }}–{{ wakeTime }}</span>
      </div>
      <div class="dial-strip__item">
        <span class="dial-strip__dot" style="background:#00D4AA"></span>
        <span class="dial-strip__key">Peak</span>
        <span class="dial-strip__val">{{ peakDuration }}</span>
      </div>
      <div class="dial-strip__item">
        <span class="dial-strip__dot" style="background:#9B8BFA;border-radius:50%"></span>
        <span class="dial-strip__key">DLMO</span>
        <span class="dial-strip__val">{{ dlmoTime }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.body-clock-dial {
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.body-clock-dial__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.body-clock-dial__title {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.body-clock-dial__sub {
  font-size: 0.45rem;
  color: var(--text-muted);
  margin-top: 0.1rem;
}

.body-clock-dial__svg-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.body-clock-dial__svg {
  width: 100%;
  max-width: 200px;
  height: auto;
}

/* Arc animation on mount */
.dial-arc {
  transition: opacity 0.2s ease;
}

.dial-dot {
  cursor: default;
}

/* Arc hover tooltip */
.dial-arc-tip {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(10,23,29,0.92);
  border: 1px solid rgba(255,246,233,0.1);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  pointer-events: none;
  text-align: center;
  min-width: 90px;
}

.dial-arc-tip--sleep { border-color: rgba(155,139,250,0.25); }
.dial-arc-tip--peak  { border-color: rgba(0,212,170,0.25); }

.dial-arc-tip__icon  { font-size: 1rem; }
.dial-arc-tip__label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.42rem;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  text-transform: uppercase;
}
.dial-arc-tip__val {
  font-family: 'Geist Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  color: #FFF6E9;
}
.dial-arc-tip__dur {
  font-size: 0.42rem;
  color: var(--text-muted);
}

/* Time strip at bottom */
.dial-strip {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  padding-top: 0.35rem;
  border-top: 1px solid rgba(255,246,233,0.06);
}

.dial-strip__item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex: 1;
}

.dial-strip__dot {
  width: 6px;
  height: 6px;
  border-radius: 2px;
  flex-shrink: 0;
}

.dial-strip__key {
  font-family: 'Geist Mono', monospace;
  font-size: 0.42rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.dial-strip__val {
  font-family: 'Geist Mono', monospace;
  font-size: 0.48rem;
  font-weight: 600;
  color: rgba(255,246,233,0.75);
}
</style>
