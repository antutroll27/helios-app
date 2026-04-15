<script setup lang="ts">
import { computed } from 'vue'
import { useBiometricsStore } from '@/stores/biometrics'

const biometrics = useBiometricsStore()
const adherence = computed(() => biometrics.protocolAdherence)
const svgHeight = computed(() => adherence.value.length * 28)

function accentForPct(pct: number): string {
  if (pct >= 80) return '#00D4AA'
  if (pct >= 55) return '#FFBD76'
  return '#FF4444'
}
</script>

<template>
  <div class="adherence-timeline">
    <header class="adherence-timeline__header">
      <p class="adherence-timeline__eyebrow font-mono text-xs5 tracking-label">PROTOCOL ADHERENCE</p>
      <p class="adherence-timeline__sub font-mono text-xs5">Sleep &amp; wake timing vs target</p>
    </header>
    <div class="adherence-timeline__scroll">
      <svg
        class="adherence-timeline__svg"
        :viewBox="`0 0 500 ${svgHeight}`"
        preserveAspectRatio="xMinYMid meet"
        aria-label="Protocol adherence timeline"
      >
        <g v-for="(day, i) in adherence" :key="day.date">
          <!-- Date label -->
          <text :x="0" :y="i * 28 + 17" class="adherence-timeline__date">
            {{ day.date.slice(5) }}
          </text>
          <!-- Track background -->
          <rect :x="45" :y="i * 28 + 10" :width="340" :height="8" rx="4" class="adherence-timeline__track" />
          <!-- Fill bar -->
          <rect
            :x="45"
            :y="i * 28 + 10"
            :width="340 * (day.adherence_pct / 100)"
            :height="8"
            rx="4"
            :fill="accentForPct(day.adherence_pct)"
            :opacity="0.8"
          />
          <!-- Target marker (center dot) -->
          <circle :cx="215" :cy="i * 28 + 14" r="3" class="adherence-timeline__target" />
          <!-- Delta label: show delta_sleep_min if non-zero -->
          <text
            v-if="Math.abs(day.sleep_delta_min) > 5"
            :x="395"
            :y="i * 28 + 17"
            class="adherence-timeline__delta"
            :fill="accentForPct(day.adherence_pct)"
          >{{ day.sleep_delta_min > 0 ? '+' : '' }}{{ day.sleep_delta_min }}m</text>
          <!-- Adherence % on far right -->
          <text :x="498" :y="i * 28 + 17" class="adherence-timeline__pct" text-anchor="end">
            {{ day.adherence_pct }}%
          </text>
        </g>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.adherence-timeline {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
  height: 100%;
}

.adherence-timeline__header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  flex-shrink: 0;
}

.adherence-timeline__eyebrow {
  margin: 0;
  color: var(--text-primary);
  letter-spacing: 0.15em;
}

.adherence-timeline__sub {
  margin: 0;
  color: var(--text-muted);
}

.adherence-timeline__scroll {
  overflow-x: hidden;
  overflow-y: auto;
  flex: 1;
}

.adherence-timeline__svg {
  width: 100%;
  height: auto;
  display: block;
}

.adherence-timeline__date {
  font-size: 11px;
  fill: rgba(255, 246, 233, 0.4);
  font-family: 'Geist Mono', 'JetBrains Mono', monospace;
}

.adherence-timeline__track {
  fill: rgba(148, 163, 184, 0.08);
}

.adherence-timeline__target {
  fill: rgba(255, 246, 233, 0.3);
}

.adherence-timeline__delta {
  font-size: 11px;
  font-family: 'Geist Mono', 'JetBrains Mono', monospace;
}

.adherence-timeline__pct {
  font-size: 11px;
  fill: rgba(255, 246, 233, 0.5);
  font-family: 'Geist Mono', 'JetBrains Mono', monospace;
}
</style>
