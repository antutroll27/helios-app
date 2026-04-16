<script setup lang="ts">
import { computed, ref } from 'vue'
import { useBiometricsStore } from '@/stores/biometrics'
import { buildSparkline, buildSparklinePoints } from '@/composables/useSparkline'

const biometrics = useBiometricsStore()

const VB_W = 440
const VB_H = 52

const displayValue = computed(() =>
  biometrics.avgSleepScore != null ? String(biometrics.avgSleepScore) : '—'
)

const spark = computed(() =>
  buildSparkline(biometrics.sleepScoreSeries.values, VB_W, VB_H)
)

const points = computed(() =>
  buildSparklinePoints(biometrics.sleepScoreSeries.values, biometrics.sleepScoreSeries.dates, VB_W, VB_H)
)

// ── Hover state ──────────────────────────────────────────────
const hoverIdx = ref<number | null>(null)

const hoverPoint = computed(() => {
  if (hoverIdx.value == null) return null
  const p = points.value[hoverIdx.value]
  return p?.y != null ? p : null
})

function onMouseMove(e: MouseEvent) {
  const svg = e.currentTarget as SVGSVGElement
  const rect = svg.getBoundingClientRect()
  const relX = ((e.clientX - rect.left) / rect.width) * VB_W

  let bestIdx: number | null = null
  let bestDist = Infinity
  points.value.forEach(p => {
    if (p.value == null) return
    const d = Math.abs(p.x - relX)
    if (d < bestDist) { bestDist = d; bestIdx = p.index }
  })
  hoverIdx.value = bestIdx
}

function onMouseLeave() {
  hoverIdx.value = null
}
</script>

<template>
  <div class="sleep-hero bento-card">
    <div class="sleep-hero__top">
      <span class="sleep-hero__label font-mono text-xs5 tracking-label">SLEEP SCORE</span>
    </div>

    <div class="sleep-hero__center">
      <!-- Show hovered value when interacting, else avg -->
      <span class="sleep-hero__value font-display">
        {{ hoverPoint ? String(Math.round(hoverPoint.value!)) : displayValue }}
      </span>
      <div class="sleep-hero__meta">
        <span class="sleep-hero__unit font-mono text-xs5">/100</span>
        <span class="sleep-hero__avg font-mono text-xs5">
          {{ hoverPoint ? hoverPoint.date : `${biometrics.dateRange}d avg` }}
        </span>
      </div>
    </div>

    <div class="sleep-hero__spark-wrap">
      <svg
        :viewBox="`0 0 ${VB_W} ${VB_H}`"
        preserveAspectRatio="none"
        class="sleep-hero__svg"
        @mousemove="onMouseMove"
        @mouseleave="onMouseLeave"
      >
        <defs>
          <linearGradient id="sleep-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#0A171D" stop-opacity="0.18"/>
            <stop offset="100%" stop-color="#0A171D" stop-opacity="0"/>
          </linearGradient>
        </defs>

        <!-- Sparkline fill + line -->
        <path v-if="spark.fill" :d="spark.fill" fill="url(#sleep-grad)"/>
        <path v-if="spark.line" :d="spark.line" fill="none" stroke="#0A171D" stroke-width="1.5"
              stroke-linejoin="round" stroke-linecap="round" stroke-opacity="0.5"/>

        <!-- Hover: needle + dot -->
        <template v-if="hoverPoint">
          <line
            :x1="hoverPoint.x" :y1="2"
            :x2="hoverPoint.x" :y2="VB_H - 2"
            stroke="#0A171D" stroke-width="0.75"
            stroke-opacity="0.45" stroke-dasharray="2 2"
          />
          <circle
            :cx="hoverPoint.x ?? undefined" :cy="hoverPoint.y ?? undefined"
            r="3" fill="#0A171D" opacity="0.75"
          />
        </template>

        <!-- Transparent hit area -->
        <rect
          x="0" y="0" :width="VB_W" :height="VB_H"
          fill="transparent" style="cursor: crosshair"
          @mousemove="onMouseMove" @mouseleave="onMouseLeave"
        />
      </svg>
    </div>
  </div>
</template>

<style scoped>
.sleep-hero {
  display: flex;
  flex-direction: column;
  background: #9B8BFA !important;
  border: none !important;
  min-height: 230px;
}
.sleep-hero__top { margin-bottom: 0.25rem; }
.sleep-hero__label { color: rgba(10,23,29,0.6); }
.sleep-hero__center {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.25rem;
}
.sleep-hero__value {
  font-size: 3.75rem;
  font-weight: 700;
  color: #0A171D;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.03em;
}
.sleep-hero__meta {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}
.sleep-hero__unit { color: rgba(10,23,29,0.75); }
.sleep-hero__avg  { color: rgba(10,23,29,0.5); }
.sleep-hero__spark-wrap {
  margin-top: auto;
  height: 52px;
}
.sleep-hero__svg {
  width: 100%;
  height: 52px;
  display: block;
}
</style>
