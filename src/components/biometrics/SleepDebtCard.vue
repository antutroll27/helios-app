<script setup lang="ts">
import { computed } from 'vue'
import { buildSparkline } from '@/composables/useSparkline'

const props = defineProps<{
  debtMin: number
  series: { date: string; value: number }[]
}>()

// Accent colour based on deficit threshold
const accent = computed(() => {
  if (props.debtMin > 0)    return '#00D4AA'   // surplus — Calm
  if (props.debtMin > -60)  return '#FFBD76'   // minor deficit — Nectarine
  return '#FF4444'                              // major deficit (≥60 min) — Storm
})

const displayValue = computed(() => {
  const abs = Math.abs(props.debtMin)
  const h = Math.floor(abs / 60)
  const m = abs % 60
  const sign = props.debtMin >= 0 ? '+' : '−'
  return h > 0 ? `${sign}${h}h ${m}m` : `${sign}${m} min`
})

// Zero-line position in the 28px viewBox
const SPARK_H = 28
const values  = computed(() => props.series.map(s => s.value))
// buildSparkline returns { line: string; fill: string } — use .line for <path d="...">
const sparklinePath = computed(() => buildSparkline(values.value, 160, SPARK_H).line)

// Compute zero-line Y position based on value range
const zeroY = computed(() => {
  const vals = values.value
  if (!vals.length) return SPARK_H / 2
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const range = max - min
  if (range === 0) return SPARK_H / 2
  return SPARK_H - ((0 - min) / range) * SPARK_H
})
</script>

<template>
  <div class="debt-card bento-card">
    <div class="debt-card__label">SLEEP DEBT · 14-DAY</div>

    <div class="debt-card__value" :style="{ color: accent }">
      {{ displayValue }}
    </div>

    <svg class="debt-card__spark"
      viewBox="0 0 160 28"
      preserveAspectRatio="none"
      aria-hidden="true">
      <!-- Zero line -->
      <line x1="0" :y1="zeroY" x2="160" :y2="zeroY"
        stroke="rgba(255,246,233,0.1)" stroke-width="0.5" stroke-dasharray="3 3" />
      <!-- Debt sparkline -->
      <path
        :d="sparklinePath"
        fill="none"
        :stroke="accent"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        opacity="0.75"
      />
    </svg>
  </div>
</template>

<style scoped>
.debt-card {
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.debt-card__label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.debt-card__value {
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1;
  margin: 0.2rem 0;
}

.debt-card__spark {
  width: 100%;
  height: 28px;
  display: block;
  margin-top: 0.2rem;
}
</style>
