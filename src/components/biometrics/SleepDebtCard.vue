<script setup lang="ts">
import { ref, computed } from 'vue'
import { buildSparkline, buildSparklinePoints } from '@/composables/useSparkline'

const props = defineProps<{
  debtMin: number
  series: { date: string; value: number }[]
}>()

const SPARK_W = 200
const SPARK_H = 56

const accent = computed(() => {
  if (props.debtMin > 0)    return '#00D4AA'
  if (props.debtMin > -60)  return '#FFBD76'
  return '#FF4444'
})

const statusLabel = computed(() => {
  if (props.debtMin > 120)  return 'Building surplus'
  if (props.debtMin > 0)    return 'On track'
  if (props.debtMin > -60)  return 'Minor deficit'
  if (props.debtMin > -240) return 'Significant debt'
  return 'Recovery needed'
})

const displayValue = computed(() => {
  const abs = Math.abs(props.debtMin)
  const h   = Math.floor(abs / 60)
  const m   = abs % 60
  const sign = props.debtMin >= 0 ? '+' : '−'
  return h > 0 ? `${sign}${h}h ${m}m` : `${sign}${m} min`
})

const values = computed(() => props.series.map(s => s.value))
const dates  = computed(() => props.series.map(s => s.date))

const sparkPaths  = computed(() => buildSparkline(values.value, SPARK_W, SPARK_H))
const sparkPoints = computed(() => buildSparklinePoints(values.value, dates.value, SPARK_W, SPARK_H))

// Zero-line Y in viewBox coordinates
const zeroY = computed(() => {
  const vals = values.value
  if (!vals.length) return SPARK_H / 2
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const range = max - min
  if (range === 0) return SPARK_H / 2
  // buildSparkline maps values to [padding, SPARK_H - padding]; match that
  const padding = 4
  const drawH   = SPARK_H - padding * 2
  return padding + drawH - ((0 - min) / range) * drawH
})

// Hover interaction
const hoverIdx = ref<number | null>(null)

const hoverPoint = computed(() => {
  if (hoverIdx.value === null) return null
  return sparkPoints.value[hoverIdx.value] ?? null
})

const tooltipLeft = computed(() => {
  if (!hoverPoint.value) return '0%'
  const pct = (hoverPoint.value.x / SPARK_W) * 100
  return `${Math.min(Math.max(pct, 10), 75)}%`
})

const hoverLabel = computed(() => {
  if (!hoverPoint.value) return ''
  const v = hoverPoint.value.value as number
  const abs = Math.abs(v)
  const h = Math.floor(abs / 60)
  const m = abs % 60
  const sign = v >= 0 ? '+' : '−'
  return h > 0 ? `${sign}${h}h ${m}m` : `${sign}${m}m`
})

function onMove(e: MouseEvent) {
  const svg = e.currentTarget as SVGSVGElement
  const rect = svg.getBoundingClientRect()
  const x = (e.clientX - rect.left) * (SPARK_W / rect.width)
  const pts = sparkPoints.value
  if (!pts.length) return
  let best = 0, minD = Infinity
  pts.forEach((pt, i) => {
    if (pt.y === null) return
    const d = Math.abs(pt.x - x)
    if (d < minD) { minD = d; best = i }
  })
  hoverIdx.value = best
}

function onLeave() { hoverIdx.value = null }
</script>

<template>
  <div class="debt-card bento-card">
    <!-- Header -->
    <div class="debt-card__header">
      <span class="debt-card__label">SLEEP DEBT · 14-DAY</span>
      <span class="debt-card__status" :style="{ color: accent }">
        {{ statusLabel }}
      </span>
    </div>

    <!-- Main value -->
    <div class="debt-card__value" :style="{ color: accent }">
      {{ displayValue }}
    </div>

    <!-- Sub context -->
    <div class="debt-card__sub">
      vs. 8h target per night
    </div>

    <!-- Interactive sparkline -->
    <div class="debt-card__spark-zone">
      <!-- Hover tooltip -->
      <div v-if="hoverPoint !== null && hoverPoint.y !== null"
        class="debt-card__tooltip"
        :style="{ left: tooltipLeft }">
        <span class="debt-card__tooltip-date">{{ hoverPoint.date }}</span>
        <span class="debt-card__tooltip-val" :style="{ color: accent }">
          {{ hoverLabel }}
        </span>
      </div>

      <svg
        :viewBox="`0 0 ${SPARK_W} ${SPARK_H}`"
        class="debt-card__spark"
        preserveAspectRatio="none"
        aria-label="14-day sleep debt trend"
        @mousemove="onMove"
        @mouseleave="onLeave"
      >
        <!-- Filled area above zero (surplus) or below zero (debt) -->
        <path :d="sparkPaths.fill" :fill="accent" opacity="0.07" />

        <!-- Zero reference line -->
        <line x1="0" :y1="zeroY" :x2="SPARK_W" :y2="zeroY"
          stroke="rgba(255,246,233,0.15)" stroke-width="0.75" stroke-dasharray="4 3" />

        <!-- Sparkline -->
        <path :d="sparkPaths.line" fill="none" :stroke="accent"
          stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />

        <!-- Hover elements -->
        <template v-if="hoverPoint !== null && hoverPoint.y !== null">
          <line
            :x1="hoverPoint.x" y1="0"
            :x2="hoverPoint.x" :y2="SPARK_H"
            stroke="rgba(255,246,233,0.15)" stroke-width="1" />
          <circle
            :cx="hoverPoint.x" :cy="hoverPoint.y" r="3.5"
            :fill="accent" stroke="var(--bg-card)" stroke-width="1.5" />
        </template>
      </svg>

      <!-- Axis labels -->
      <div class="debt-card__axis">
        <span>{{ series[0]?.date ?? '' }}</span>
        <span>14-day window</span>
        <span>today</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.debt-card {
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.debt-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.debt-card__label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.debt-card__status {
  font-family: 'Geist Mono', monospace;
  font-size: 0.45rem;
  letter-spacing: 0.05em;
  font-weight: 600;
  text-transform: uppercase;
}

.debt-card__value {
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
  margin-top: 0.1rem;
  transition: color 0.3s ease;
}

.debt-card__sub {
  font-size: 0.48rem;
  color: var(--text-muted);
}

/* Sparkline zone */
.debt-card__spark-zone {
  position: relative;
  margin-top: 0.25rem;
}

.debt-card__spark {
  width: 100%;
  height: 56px;
  display: block;
  cursor: crosshair;
}

.debt-card__tooltip {
  position: absolute;
  top: 4px;
  transform: translateX(-50%);
  background: rgba(10,23,29,0.9);
  border: 1px solid rgba(255,246,233,0.12);
  border-radius: 4px;
  padding: 0.2rem 0.4rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.05rem;
  pointer-events: none;
  z-index: 10;
  white-space: nowrap;
}

.debt-card__tooltip-date {
  font-family: 'Geist Mono', monospace;
  font-size: 0.4rem;
  color: var(--text-muted);
}

.debt-card__tooltip-val {
  font-family: 'Geist Mono', monospace;
  font-size: 0.6rem;
  font-weight: 700;
}

.debt-card__axis {
  display: flex;
  justify-content: space-between;
  font-size: 0.38rem;
  color: rgba(255,246,233,0.2);
  font-family: 'Geist Mono', monospace;
  margin-top: 0.1rem;
}
</style>
