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
const R    = 80
const CIRC = 2 * Math.PI * R

function angleToXY(deg: number, r: number) {
  const rad = ((deg - 90) * Math.PI) / 180
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) }
}

function arcDash(angleStart: number, angleEnd: number) {
  const delta   = ((angleEnd - angleStart + 360) % 360)
  const dashLen = (delta / 360) * CIRC
  const offset  = CIRC - (angleStart / 360) * CIRC + CIRC * 0.25
  return {
    strokeDasharray:  `${dashLen.toFixed(1)} ${(CIRC - dashLen).toFixed(1)}`,
    strokeDashoffset: offset.toFixed(1),
  }
}

function angleToTime(deg: number): string {
  const wrapped = ((deg % 360) + 360) % 360
  const totalMin = Math.round((wrapped / 360) * 1440)
  const h = Math.floor(totalMin / 60) % 24
  const m = totalMin % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

// Is nowAngle inside an arc?
function isInArc(angle: number, start: number, end: number): boolean {
  const delta = ((end - start + 360) % 360)
  const pos   = ((angle - start + 360) % 360)
  return pos <= delta
}

// Hours remaining until an arc endpoint
function hoursUntil(fromAngle: number, toAngle: number): number {
  return ((toAngle - fromAngle + 360) % 360) / 15
}

const sleepArc  = computed(() => props.data ? arcDash(props.data.sleepWindowStart, props.data.sleepWindowEnd) : null)
const peakArc   = computed(() => props.data ? arcDash(props.data.peakAlertStart,  props.data.peakAlertEnd)   : null)
const dlmoDot   = computed(() => props.data ? angleToXY(props.data.dlmoAngle, R) : null)
const nowNeedle = computed(() => angleToXY(props.nowAngle, 64))
const nowTip    = computed(() => angleToXY(props.nowAngle, 70))

const nowTime = computed(() => {
  const totalMin = Math.round((props.nowAngle / 360) * 1440)
  const h = Math.floor(totalMin / 60) % 24
  const m = totalMin % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
})

// "Right now" phase — the key normie feature
const currentPhase = computed(() => {
  if (!props.data) return null

  if (isInArc(props.nowAngle, props.data.sleepWindowStart, props.data.sleepWindowEnd)) {
    const h = hoursUntil(props.nowAngle, props.data.sleepWindowEnd)
    return {
      emoji:   '🛌',
      heading: 'Sleep time',
      detail:  `Wake up in ${h.toFixed(0)}h`,
      color:   '#9B8BFA',
    }
  }

  if (isInArc(props.nowAngle, props.data.peakAlertStart, props.data.peakAlertEnd)) {
    const h = hoursUntil(props.nowAngle, props.data.peakAlertEnd)
    return {
      emoji:   '🧠',
      heading: 'Peak focus time',
      detail:  `${h.toFixed(0)}h of focus left today`,
      color:   '#00D4AA',
    }
  }

  // Check if wind-down window (within 2h of dlmo)
  const hToDlmo = hoursUntil(props.nowAngle, props.data.dlmoAngle)
  if (hToDlmo <= 2) {
    return {
      emoji:   '🕯️',
      heading: 'Wind-down time',
      detail:  `Dim your lights, slow down`,
      color:   '#9B8BFA',
    }
  }

  // General recovery / build-up
  const hToSleep = hoursUntil(props.nowAngle, props.data.sleepWindowStart)
  return {
    emoji:   '☀️',
    heading: 'Daytime phase',
    detail:  `Bedtime in ${hToSleep.toFixed(0)}h`,
    color:   'rgba(255,246,233,0.55)',
  }
})

// Plain English time strings for the strip
const bedtime       = computed(() => props.data ? angleToTime(props.data.sleepWindowStart) : '--:--')
const wakeTime      = computed(() => props.data ? angleToTime(props.data.sleepWindowEnd)   : '--:--')
const windDownTime  = computed(() => props.data ? angleToTime(props.data.dlmoAngle)        : '--:--')

const hoveredArc = ref<'sleep' | 'peak' | null>(null)

// Human-readable clock labels (AM/PM style)
const hourLabels = [
  { label: 'MID',  ...angleToXY(0,   R + 16) },
  { label: '6AM',  ...angleToXY(90,  R + 16) },
  { label: 'NOON', ...angleToXY(180, R + 16) },
  { label: '6PM',  ...angleToXY(270, R + 16) },
]
</script>

<template>
  <div class="dial-card bento-card">

    <!-- Header: plain title + current time -->
    <div class="dial-card__header">
      <div class="dial-card__title">YOUR SLEEP SCHEDULE</div>
      <div class="dial-card__now-badge">
        <span class="dial-card__now-dot"></span>
        {{ nowTime }}
      </div>
    </div>

    <!-- SVG dial -->
    <div class="dial-card__svg-wrap">
      <svg viewBox="0 0 200 200" class="dial-card__svg"
        aria-label="24-hour sleep schedule dial">

        <!-- Track ring -->
        <circle :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="rgba(255,246,233,0.05)" stroke-width="18" />

        <!-- Sleep window arc — hoverable -->
        <circle v-if="sleepArc" :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="#9B8BFA" stroke-width="18"
          :opacity="hoveredArc === 'sleep' ? 0.7 : 0.45"
          :stroke-dasharray="sleepArc.strokeDasharray"
          :stroke-dashoffset="sleepArc.strokeDashoffset"
          stroke-linecap="round"
          class="dial-arc"
          @mouseenter="hoveredArc = 'sleep'"
          @mouseleave="hoveredArc = null" />

        <!-- Peak focus arc — thinner inner ring -->
        <circle v-if="peakArc" :cx="CX" :cy="CY" :r="R"
          fill="none" stroke="#00D4AA" stroke-width="7"
          :opacity="hoveredArc === 'peak' ? 0.75 : 0.45"
          :stroke-dasharray="peakArc.strokeDasharray"
          :stroke-dashoffset="peakArc.strokeDashoffset"
          stroke-linecap="round"
          class="dial-arc"
          @mouseenter="hoveredArc = 'peak'"
          @mouseleave="hoveredArc = null" />

        <!-- Wind-down marker dot (formerly "DLMO") -->
        <circle v-if="dlmoDot"
          :cx="dlmoDot.x" :cy="dlmoDot.y" r="5"
          fill="#9B8BFA" stroke="rgba(10,23,29,0.85)" stroke-width="2">
          <title>Dim your lights at {{ windDownTime }}</title>
        </circle>
        <!-- Candle emoji near DLMO dot — signals "dim the lights" -->
        <text v-if="dlmoDot"
          :x="angleToXY(data!.dlmoAngle, R - 18).x"
          :y="angleToXY(data!.dlmoAngle, R - 18).y"
          text-anchor="middle" dominant-baseline="middle"
          font-size="9">🕯️</text>

        <!-- Hour labels — human readable -->
        <text v-for="h in hourLabels" :key="h.label"
          :x="h.x" :y="h.y"
          text-anchor="middle" dominant-baseline="middle"
          fill="rgba(255,246,233,0.22)"
          font-size="7"
          font-family="'Geist Mono', monospace">
          {{ h.label }}
        </text>

        <!-- Now needle -->
        <line :x1="CX" :y1="CY" :x2="nowNeedle.x" :y2="nowNeedle.y"
          stroke="rgba(255,246,233,0.9)" stroke-width="2" stroke-linecap="round" />
        <!-- Needle tip glow -->
        <circle :cx="nowTip.x" :cy="nowTip.y" r="2.5"
          fill="#FFF6E9" opacity="0.8" />

        <!-- Centre hub -->
        <circle :cx="CX" :cy="CY" r="4.5" fill="#FFF6E9" opacity="0.9" />

        <!-- Empty state -->
        <text v-if="!data" x="100" y="108"
          text-anchor="middle" fill="rgba(255,246,233,0.2)"
          font-size="9" font-family="'Geist Mono', monospace">
          Need more sleep data
        </text>
      </svg>

      <!-- Arc hover overlay — center of dial -->
      <Transition name="tip-fade">
        <div v-if="hoveredArc === 'sleep' && data" class="dial-overlay">
          <span class="dial-overlay__emoji">🛌</span>
          <div class="dial-overlay__heading">Sleep window</div>
          <div class="dial-overlay__time">{{ bedtime }} → {{ wakeTime }}</div>
          <div class="dial-overlay__hint">Your average sleep time<br>based on 30 nights</div>
        </div>
        <div v-else-if="hoveredArc === 'peak' && data" class="dial-overlay">
          <span class="dial-overlay__emoji">🧠</span>
          <div class="dial-overlay__heading">Focus window</div>
          <div class="dial-overlay__hint">Your brain is most alert<br>during the teal arc</div>
        </div>
      </Transition>
    </div>

    <!-- "Right now" status — the most important normie feature -->
    <div v-if="currentPhase && data" class="dial-phase"
      :style="{ borderColor: currentPhase.color + '33', background: currentPhase.color + '0d' }">
      <span class="dial-phase__emoji">{{ currentPhase.emoji }}</span>
      <div class="dial-phase__text">
        <span class="dial-phase__heading" :style="{ color: currentPhase.color }">
          {{ currentPhase.heading }}
        </span>
        <span class="dial-phase__detail">{{ currentPhase.detail }}</span>
      </div>
    </div>

    <!-- Plain-English time strip -->
    <div v-if="data" class="dial-strip">
      <div class="dial-strip__item">
        <div class="dial-strip__icon" style="background:rgba(155,139,250,0.15);color:#9B8BFA">🛌</div>
        <div>
          <div class="dial-strip__key">Bedtime</div>
          <div class="dial-strip__val">{{ bedtime }}</div>
        </div>
      </div>
      <div class="dial-strip__item">
        <div class="dial-strip__icon" style="background:rgba(255,189,118,0.12);color:#FFBD76">🌅</div>
        <div>
          <div class="dial-strip__key">Wake up</div>
          <div class="dial-strip__val">{{ wakeTime }}</div>
        </div>
      </div>
      <div class="dial-strip__item">
        <div class="dial-strip__icon" style="background:rgba(155,139,250,0.12);color:#9B8BFA">🕯️</div>
        <div>
          <div class="dial-strip__key">Dim lights</div>
          <div class="dial-strip__val">{{ windDownTime }}</div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.dial-card {
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

/* Header */
.dial-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dial-card__title {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.dial-card__now-badge {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-family: 'Geist Mono', monospace;
  font-size: 0.55rem;
  font-weight: 600;
  color: rgba(255,246,233,0.7);
  background: rgba(255,246,233,0.06);
  border-radius: 20px;
  padding: 0.2rem 0.5rem;
}

.dial-card__now-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #FFF6E9;
  opacity: 0.8;
  animation: now-pulse 2s ease-in-out infinite;
}

@keyframes now-pulse {
  0%, 100% { opacity: 0.8; transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.7); }
}

/* SVG */
.dial-card__svg-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dial-card__svg {
  width: 100%;
  max-width: 210px;
  height: auto;
}

.dial-arc {
  cursor: pointer;
  transition: opacity 0.15s ease;
}

/* Center overlay on arc hover */
.dial-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(7,17,26,0.93);
  border: 1px solid rgba(255,246,233,0.1);
  border-radius: 10px;
  padding: 0.6rem 0.9rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  pointer-events: none;
  text-align: center;
  min-width: 100px;
}

.dial-overlay__emoji { font-size: 1.1rem; margin-bottom: 0.1rem; }

.dial-overlay__heading {
  font-size: 0.55rem;
  font-weight: 700;
  color: rgba(255,246,233,0.9);
}

.dial-overlay__time {
  font-family: 'Geist Mono', monospace;
  font-size: 0.7rem;
  font-weight: 700;
  color: #FFF6E9;
  letter-spacing: -0.01em;
}

.dial-overlay__hint {
  font-size: 0.42rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin-top: 0.1rem;
}

/* Transition */
.tip-fade-enter-active, .tip-fade-leave-active { transition: opacity 0.15s ease; }
.tip-fade-enter-from, .tip-fade-leave-to       { opacity: 0; }

/* "Right now" phase bar */
.dial-phase {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.7rem;
  border-radius: 8px;
  border: 1px solid;
}

.dial-phase__emoji { font-size: 1.1rem; flex-shrink: 0; }

.dial-phase__text {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.dial-phase__heading {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.dial-phase__detail {
  font-size: 0.48rem;
  color: var(--text-muted);
}

/* Plain-English strip */
.dial-strip {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255,246,233,0.06);
}

.dial-strip__item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex: 1;
}

.dial-strip__icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  flex-shrink: 0;
}

.dial-strip__key {
  font-size: 0.42rem;
  color: var(--text-muted);
  line-height: 1.2;
}

.dial-strip__val {
  font-family: 'Geist Mono', monospace;
  font-size: 0.6rem;
  font-weight: 700;
  color: rgba(255,246,233,0.85);
  line-height: 1.2;
}
</style>
