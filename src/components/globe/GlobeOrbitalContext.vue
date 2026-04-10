<script setup lang="ts">
import { computed } from 'vue'

interface OrbitalContext {
  label: string
  summary: string
}

interface CurrentAnchor {
  label: string
}

interface SolarAnchor {
  phase: string
  elevationDeg: number
}

interface Props {
  context: OrbitalContext
  current: CurrentAnchor
  solar: SolarAnchor
}

const props = defineProps<Props>()

// Solar elevation as % of zenith (90°), clamped 0–100
const elevationPct = computed(() => {
  if (props.solar.elevationDeg <= 0) return 0
  return Math.min((props.solar.elevationDeg / 90) * 100, 100)
})

const isBelowHorizon = computed(() => props.solar.elevationDeg < 0)
</script>

<template>
  <section class="orbital-card" aria-label="Orbital context HUD">

    <!-- Header: label + rule + mode tag -->
    <div class="orbital-header">
      <span class="orbital-label font-mono">ORBITAL VIEW</span>
      <div class="orbital-rule" />
      <span class="orbital-mode font-mono">{{ context.label }}</span>
    </div>

    <!-- Location title -->
    <h3 class="orbital-title">{{ current.label }}</h3>

    <!-- Facts — instrument readout, hairlines only -->
    <div class="orbital-facts">
      <div class="orbital-fact">
        <span class="orbital-fact-label font-mono">SOLAR PHASE</span>
        <span class="orbital-fact-value font-mono">{{ solar.phase }}</span>
      </div>
      <div class="orbital-fact-divider" />
      <div class="orbital-fact">
        <span class="orbital-fact-label font-mono">ELEVATION</span>
        <span
          class="orbital-fact-value font-mono"
          :class="{ 'orbital-fact-value--dim': isBelowHorizon }"
        >
          {{ solar.elevationDeg.toFixed(1) }}&deg;
        </span>
      </div>
    </div>

    <!-- Elevation progress bar — solar arc tracker -->
    <div class="orbital-elev-track" :aria-label="`Solar elevation: ${solar.elevationDeg.toFixed(1)}°`">
      <div
        class="orbital-elev-fill"
        :style="{ width: elevationPct + '%', opacity: isBelowHorizon ? 0.25 : 1 }"
      />
    </div>

    <!-- Summary -->
    <p class="orbital-summary">{{ context.summary }}</p>

  </section>
</template>

<style scoped>
.orbital-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  color: rgba(241, 245, 249, 0.92);
  border-left: 2px solid rgba(255, 189, 118, 0.4);
  padding-left: 0.75rem;
}

/* ── Header ──────────────────────────────────────── */

.orbital-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.orbital-label {
  font-size: 0.42rem;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.6);
  flex-shrink: 0;
}

.orbital-rule {
  flex: 1;
  height: 1px;
  background: rgba(148, 163, 184, 0.18);
}

.orbital-mode {
  font-size: 0.4rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(255, 189, 118, 0.85);
  flex-shrink: 0;
}

/* ── Title ────────────────────────────────────────── */

.orbital-title {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: rgba(241, 245, 249, 0.95);
  line-height: 1.1;
}

/* ── Facts — no boxes, just hairlines ─────────────── */

.orbital-facts {
  display: flex;
  align-items: stretch;
  border-top: 1px solid rgba(148, 163, 184, 0.14);
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
  padding: 0.5rem 0;
}

.orbital-fact {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.18rem;
}

.orbital-fact-divider {
  width: 1px;
  background: rgba(148, 163, 184, 0.14);
  margin: 0 0.75rem;
  flex-shrink: 0;
}

.orbital-fact-label {
  font-size: 0.4rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.55);
}

.orbital-fact-value {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: rgba(241, 245, 249, 0.95);
  transition: color 0.3s ease;
}

.orbital-fact-value--dim {
  color: rgba(148, 163, 184, 0.55);
}

/* ── Elevation bar — solar arc tracker ────────────── */

.orbital-elev-track {
  width: 100%;
  height: 3px;
  border-radius: 1.5px;
  background: rgba(148, 163, 184, 0.1);
  overflow: hidden;
}

.orbital-elev-fill {
  height: 100%;
  border-radius: 1.5px;
  background: linear-gradient(90deg, rgba(255, 189, 118, 0.35), rgba(255, 189, 118, 0.9));
  transition: width 1.2s ease, opacity 0.6s ease;
}

/* ── Summary ──────────────────────────────────────── */

.orbital-summary {
  margin: 0;
  font-size: 0.65rem;
  line-height: 1.4;
  color: rgba(226, 232, 240, 0.55);
}

@media (max-width: 640px) {
  .orbital-facts {
    flex-direction: column;
    gap: 0.375rem;
    border-bottom: none;
  }

  .orbital-fact-divider {
    display: none;
  }
}

@media (max-width: 600px) {
  .orbital-card {
    gap: 0.35rem;
  }

  .orbital-summary {
    display: none;
  }
}
</style>
