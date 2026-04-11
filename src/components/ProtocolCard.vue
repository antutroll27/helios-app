<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title: string
  time: Date
  endTime?: Date
  icon: string
  citation: string
  subtitle: string
  status: 'upcoming' | 'active' | 'passed'
}>()

// Swiss palette — distinct hues, same saturation family
const cardThemes: Record<string, string> = {
  Sunrise:   '#FFBD76',  // nectarine — brand anchor
  Sun:       '#E8C547',  // warm yellow
  Brain:     '#9B8BFA',  // soft violet
  Coffee:    '#F08060',  // terracotta
  Moon:      '#5BBFD6',  // steel teal
  BedDouble: '#8899CC',  // slate blue
}

const theme = computed(() => cardThemes[props.icon] ?? '#FFBD76')
const isPassed = computed(() => props.status === 'passed')
const isActive = computed(() => props.status === 'active')

// Split time string for mixed-scale display
const timeParts = computed(() => {
  try {
    const d = props.time instanceof Date ? props.time : new Date(props.time)
    const str = isNaN(d.getTime())
      ? String(props.time)
      : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    const [h, m] = str.split(':')
    return { h: h ?? str, m: m ?? '' }
  } catch {
    return { h: String(props.time), m: '' }
  }
})

// Per-card reference durations for proportional bar fill
const windowRefMs: Record<string, number> = {
  Sunrise:   7_200_000,   // 2 hr → 30 min wake window = 25%
  Sun:       3_600_000,   // 1 hr → 10-20 min light = 17-33%
  Brain:     21_600_000,  // 6 hr → 3 hr focus = 50%
  Moon:      10_800_000,  // 3 hr → 90-120 min wind-down = 50-67%
}

// Bar fill % (0 if no endTime)
const barPct = computed(() => {
  if (!props.endTime) return 0
  const ms = props.endTime.getTime() - props.time.getTime()
  const ref = windowRefMs[props.icon] ?? 28_800_000
  return Math.min(Math.max((ms / ref) * 100, 5), 100)
})

const hasBar = computed(() => !!props.endTime)

// Tick strip: 24 ticks, N filled per card type
const tickFillMap: Record<string, number> = {
  Coffee:    4,   // ≈ 4-hr pre-bed restriction
  BedDouble: 8,   // 8 hr target sleep
}
const tickFilled = computed(() => tickFillMap[props.icon] ?? 0)
const ticks = Array.from({ length: 24 }, (_, i) => i)
</script>

<template>
  <div
    class="card"
    :class="{ 'card--passed': isPassed, 'card--active': isActive }"
    :style="{ '--accent': theme }"
  >
    <!-- Header: dot + label + status -->
    <div class="card-header">
      <div class="card-label-group">
        <span class="card-dot" />
        <span class="card-label font-mono">{{ title }}</span>
      </div>
      <span
        class="card-status font-mono"
        :class="{ 'card-status--active': isActive }"
      >
        {{ isActive ? '● ACTIVE' : isPassed ? '· PASSED' : '· UPCOMING' }}
      </span>
    </div>

    <!-- Hero: mixed-scale time -->
    <div class="card-time-wrap">
      <span class="t-h font-mono">{{ timeParts.h }}</span>
      <span class="t-sep font-mono">:</span>
      <span class="t-m font-mono">{{ timeParts.m }}</span>
    </div>

    <!-- Hairline -->
    <div class="card-rule" />

    <!-- Data strip: real bar or tick strip -->
    <div class="card-strip">
      <!-- Real window bar -->
      <div v-if="hasBar" class="bar-track">
        <div
          class="bar-fill"
          :class="{ 'bar-fill--active': isActive }"
          :style="{ width: barPct + '%' }"
        />
      </div>

      <!-- Tick strip fallback -->
      <div v-else class="tick-row">
        <span
          v-for="i in ticks"
          :key="i"
          class="tick"
          :class="{ 'tick--filled': i < tickFilled }"
        />
      </div>
    </div>

    <!-- Description -->
    <p class="card-desc">{{ subtitle }}</p>

    <!-- Citation -->
    <p class="card-cite font-mono">/ {{ citation }}</p>
  </div>
</template>

<style scoped>
.card {
  display: flex;
  flex-direction: column;
  padding: 0.875rem 0.875rem 0.75rem 1.125rem;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  transition: border-color 0.2s ease;
  position: relative;
  overflow: hidden;
  gap: 0;
}

/* Left accent bar */
.card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--accent);
}

.card:hover {
  border-color: var(--glass-border);
}

.card--passed {
  opacity: 0.3;
}

/* ── Header ─────────────────────────────────── */

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.card-label-group {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.card-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
}

.card-label {
  font-size: 0.45rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.card-status {
  font-size: 0.4rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.card-status--active {
  color: var(--accent);
}

/* ── Time hero ──────────────────────────────── */

.card-time-wrap {
  display: flex;
  align-items: baseline;
  gap: 0;
  margin-bottom: 0.75rem;
  line-height: 1;
}

.t-h,
.t-m {
  font-size: 2.25rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}

.t-sep {
  font-size: 2.25rem;
  font-weight: 300;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  opacity: 0.25;
  margin: 0 0.5px;
}

/* ── Hairline ───────────────────────────────── */

.card-rule {
  height: 1px;
  background: var(--border-subtle);
  margin-bottom: 0.5rem;
}

/* ── Data strip ─────────────────────────────── */

.card-strip {
  margin-bottom: 0.625rem;
}

/* Window bar */
.bar-track {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: var(--border-subtle);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 2px;
  background: var(--accent);
  transition: width 0.4s ease;
}

.bar-fill--active {
  animation: pulse-bar 2.5s ease-in-out infinite;
}

/* Tick strip */
.tick-row {
  display: flex;
  align-items: center;
  gap: 3px;
  flex-wrap: nowrap;
}

.tick {
  width: 3px;
  height: 6px;
  border-radius: 1px;
  background: var(--border-subtle);
  flex-shrink: 0;
}

.tick--filled {
  background: var(--accent);
}

/* ── Description ────────────────────────────── */

.card-desc {
  font-family: var(--font-body);
  font-size: 0.65rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 0.5rem;
  flex: 1;
}

/* ── Citation ───────────────────────────────── */

.card-cite {
  font-size: 0.45rem;
  color: var(--text-muted);
  opacity: 0.5;
}
</style>
