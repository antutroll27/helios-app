<script setup lang="ts">
import { ref, computed } from 'vue'
import { buildSparkline, buildSparklinePoints } from '@/composables/useSparkline'

const props = defineProps<{
  score: number | null
  series: { date: string; value: number | null }[]
}>()

const SPARK_W = 200
const SPARK_H = 56

const values = computed(() => props.series.map(s => s.value))
const dates  = computed(() => props.series.map(s => s.date))

const sparkPaths  = computed(() => buildSparkline(values.value, SPARK_W, SPARK_H))
const sparkPoints = computed(() => buildSparklinePoints(values.value, dates.value, SPARK_W, SPARK_H))

const scoreColor = computed(() => {
  if (props.score === null) return 'var(--text-muted)'
  if (props.score >= 70) return '#00D4AA'
  if (props.score >= 40) return '#FFBD76'
  return '#FF4444'
})

const scoreLabel = computed(() => {
  if (props.score === null) return null
  if (props.score >= 85) return 'Excellent'
  if (props.score >= 70) return 'Good'
  if (props.score >= 40) return 'Fair'
  return 'Poor'
})

const scoreSub = computed(() => {
  if (props.score === null) return 'Needs 7+ nights to calculate'
  if (props.score >= 70) return 'Sleep timing is highly consistent'
  if (props.score >= 40) return 'Some variability in sleep timing'
  return 'Irregular sleep schedule detected'
})

const hasData = computed(() => props.score !== null)

// Hover interaction
const hoverIdx = ref<number | null>(null)

const hoverPoint = computed(() => {
  if (hoverIdx.value === null) return null
  return sparkPoints.value[hoverIdx.value] ?? null
})

// Tooltip left position as % of SVG width (clamped so it doesn't overflow)
const tooltipLeft = computed(() => {
  if (!hoverPoint.value) return '0%'
  const pct = (hoverPoint.value.x / SPARK_W) * 100
  return `${Math.min(Math.max(pct, 10), 75)}%`
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
  <div class="sri-card bento-card">
    <!-- Header -->
    <div class="sri-card__header">
      <span class="sri-card__label">SLEEP REGULARITY</span>
      <span v-if="scoreLabel" class="sri-card__badge"
        :style="{ color: scoreColor, borderColor: scoreColor + '44' }">
        {{ scoreLabel }}
      </span>
    </div>

    <!-- Score -->
    <div class="sri-card__score-row">
      <span class="sri-card__number" :style="{ color: scoreColor }">{{ score ?? '—' }}</span>
      <span class="sri-card__denom">/100</span>
    </div>

    <!-- Progress track -->
    <div class="sri-card__track">
      <div class="sri-card__track-fill"
        :style="{ width: hasData ? `${score}%` : '0%', background: scoreColor }" />
    </div>

    <!-- Description -->
    <div class="sri-card__sub">{{ scoreSub }}</div>

    <!-- Interactive sparkline -->
    <div v-if="hasData" class="sri-card__spark-zone">
      <!-- Hover tooltip -->
      <div v-if="hoverPoint?.y !== null && hoverPoint !== null"
        class="sri-card__tooltip"
        :style="{ left: tooltipLeft }">
        <span class="sri-card__tooltip-date">{{ hoverPoint.date }}</span>
        <span class="sri-card__tooltip-val" :style="{ color: scoreColor }">
          {{ hoverPoint.value ?? '—' }}
        </span>
      </div>

      <svg
        :viewBox="`0 0 ${SPARK_W} ${SPARK_H}`"
        class="sri-card__spark"
        preserveAspectRatio="none"
        aria-label="SRI 30-day trend"
        @mousemove="onMove"
        @mouseleave="onLeave"
      >
        <!-- Filled area -->
        <path :d="sparkPaths.fill" :fill="scoreColor" opacity="0.08" />
        <!-- Line -->
        <path :d="sparkPaths.line" fill="none" :stroke="scoreColor"
          stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
        <!-- Hover elements -->
        <template v-if="hoverPoint !== null && hoverPoint.y !== null">
          <line
            :x1="hoverPoint.x" y1="0"
            :x2="hoverPoint.x" :y2="SPARK_H"
            stroke="rgba(255,246,233,0.15)" stroke-width="1" />
          <circle
            :cx="hoverPoint.x" :cy="hoverPoint.y" r="3.5"
            :fill="scoreColor" stroke="var(--bg-card)" stroke-width="1.5" />
        </template>
      </svg>

      <!-- Axis labels -->
      <div class="sri-card__axis">
        <span>{{ series[0]?.date ?? '' }}</span>
        <span>30-day trend</span>
        <span>today</span>
      </div>
    </div>

    <div v-if="!hasData" class="sri-card__empty">
      <span class="sri-card__empty-icon">📊</span>
      Track 7+ nights to unlock
    </div>

    <div class="sri-card__citation">Windred et al. 2024 · proxy formula</div>
  </div>
</template>

<style scoped>
.sri-card {
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.sri-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sri-card__label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.sri-card__badge {
  font-family: 'Geist Mono', monospace;
  font-size: 0.45rem;
  letter-spacing: 0.08em;
  font-weight: 700;
  text-transform: uppercase;
  border: 1px solid;
  border-radius: 4px;
  padding: 0.1rem 0.35rem;
}

.sri-card__score-row {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
  margin-top: 0.1rem;
}

.sri-card__number {
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
  transition: color 0.3s ease;
}

.sri-card__denom {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-weight: 500;
}

/* Progress track */
.sri-card__track {
  height: 3px;
  background: rgba(255,246,233,0.06);
  border-radius: 2px;
  overflow: hidden;
  margin: 0.1rem 0;
}

.sri-card__track-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.sri-card__sub {
  font-size: 0.48rem;
  color: var(--text-muted);
  line-height: 1.4;
}

/* Sparkline zone */
.sri-card__spark-zone {
  position: relative;
  margin-top: 0.25rem;
}

.sri-card__spark {
  width: 100%;
  height: 56px;
  display: block;
  cursor: crosshair;
}

.sri-card__tooltip {
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

.sri-card__tooltip-date {
  font-family: 'Geist Mono', monospace;
  font-size: 0.4rem;
  color: var(--text-muted);
}

.sri-card__tooltip-val {
  font-family: 'Geist Mono', monospace;
  font-size: 0.6rem;
  font-weight: 700;
}

.sri-card__axis {
  display: flex;
  justify-content: space-between;
  font-size: 0.38rem;
  color: rgba(255,246,233,0.2);
  font-family: 'Geist Mono', monospace;
  margin-top: 0.1rem;
}

.sri-card__empty {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.5rem;
  color: var(--text-muted);
  padding: 0.75rem 0;
}

.sri-card__empty-icon {
  font-size: 0.8rem;
}

.sri-card__citation {
  font-size: 0.42rem;
  color: rgba(255,246,233,0.2);
  font-style: italic;
  margin-top: 0.1rem;
}
</style>
