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
  routeLabel?: string
}

const props = defineProps<Props>()

// Solar elevation as % of zenith (90°), clamped 0–100
const elevationPct = computed(() => {
  if (props.solar.elevationDeg <= 0) return 0
  return Math.min((props.solar.elevationDeg / 90) * 100, 100)
})

const isBelowHorizon = computed(() => props.solar.elevationDeg < 0)

// Split elevation string for mixed-weight hero number
const elevStr = computed(() => props.solar.elevationDeg.toFixed(1))
const intPart = computed(() => elevStr.value.split('.')[0])
const decPart = computed(() => elevStr.value.split('.')[1] ?? '0')
</script>

<template>
  <section class="orbital-card" aria-label="Orbital context HUD">

    <!-- Top row: chip + solar phase pill -->
    <div class="card-top">
      <span class="card-chip">Solar Context</span>
      <span class="pill">
        <span class="pill-dot" aria-hidden="true" />
        {{ solar.phase }}
      </span>
    </div>

    <!-- Hero: elevation angle split into int/sep/dec/sym -->
    <div class="elev-hero" :aria-label="`Solar elevation ${solar.elevationDeg.toFixed(1)} degrees`">
      <span class="h-int">{{ intPart }}</span>
      <span class="h-sep" aria-hidden="true">.</span>
      <span class="h-dec">{{ decPart }}</span>
      <span class="h-sym" aria-hidden="true">°</span>
    </div>

    <!-- Sublabel -->
    <p class="elev-sub">Solar Elevation · {{ current.label }}</p>

    <!-- Hairline -->
    <div class="hairline" aria-hidden="true" />

    <!-- Elevation bar -->
    <div
      class="bar-track"
      :aria-label="`Solar elevation: ${solar.elevationDeg.toFixed(1)}°`"
    >
      <div
        class="bar-fill"
        :style="{ width: elevationPct + '%', opacity: isBelowHorizon ? 0.25 : 1 }"
      />
    </div>

    <!-- Stats -->
    <div class="stats">
      <div class="stat">
        <span class="stat-label">Solar Phase</span>
        <span class="stat-value">{{ solar.phase }}</span>
      </div>
      <div class="stat stat--right">
        <template v-if="props.routeLabel">
          <span class="stat-label">Route</span>
          <span class="stat-value">→ {{ props.routeLabel }}</span>
        </template>
        <template v-else>
          <span class="stat-label">Elevation</span>
          <span class="stat-value">{{ solar.elevationDeg.toFixed(1) }}°</span>
        </template>
      </div>
    </div>

    <!-- Summary -->
    <p class="orbital-summary">{{ context.summary }}</p>

  </section>
</template>

<style scoped>
/* ── Card shell ─────────────────────────────────── */
.orbital-card {
  display: flex;
  flex-direction: column;
  gap: 0;
  background: color-mix(in srgb, #FFBD76 26%, #07111a);
  border-radius: 1rem;
  padding: 0.9rem 0.9rem 0.8rem 1rem;
}

/* ── Top row ────────────────────────────────────── */
.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.6rem;
}

.card-chip {
  font-family: var(--font-mono);
  font-size: 0.41rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255, 220, 160, 0.7);
}

.pill {
  display: flex;
  align-items: center;
  gap: 0.28rem;
  padding: 0.16rem 0.42rem;
  border-radius: 20px;
  background: rgba(255, 189, 118, 0.18);
  color: #FFBD76;
  font-family: var(--font-mono);
  font-size: 0.39rem;
  font-weight: 600;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.pill-dot {
  display: inline-block;
  width: 3.5px;
  height: 3.5px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

/* ── Hero elevation number ──────────────────────── */
.elev-hero {
  display: flex;
  align-items: baseline;
  gap: 0.08rem;
  margin-bottom: 0.26rem;
}

.h-int,
.h-dec {
  font-family: var(--font-mono);
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: rgba(255, 245, 225, 0.97);
}

.h-sep {
  font-family: var(--font-mono);
  font-size: 2.2rem;
  font-weight: 300;
  opacity: 0.22;
  color: rgba(255, 245, 225, 0.97);
}

.h-sym {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255, 220, 160, 0.65);
  align-self: flex-end;
  padding-bottom: 0.2rem;
}

/* ── Sublabel ───────────────────────────────────── */
.elev-sub {
  margin: 0 0 0.62rem;
  font-family: var(--font-mono);
  font-size: 0.4rem;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 220, 160, 0.55);
}

/* ── Hairline ───────────────────────────────────── */
.hairline {
  height: 1px;
  background: rgba(255, 189, 118, 0.15);
  margin-bottom: 0.62rem;
}

/* ── Elevation bar ──────────────────────────────── */
.bar-track {
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 189, 118, 0.12);
  margin-bottom: 0.68rem;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, rgba(255, 189, 118, 0.5), #FFBD76);
  transition: width 1.2s ease, opacity 0.6s ease;
}

/* ── Stats ──────────────────────────────────────── */
.stats {
  display: flex;
  margin-bottom: 0.55rem;
}

.stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.14rem;
}

.stat--right {
  border-left: 1px solid rgba(255, 189, 118, 0.12);
  padding-left: 0.6rem;
}

.stat-label {
  font-family: var(--font-mono);
  font-size: 0.37rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(255, 220, 160, 0.52);
}

.stat-value {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: rgba(255, 245, 225, 0.92);
}

/* ── Summary ────────────────────────────────────── */
.orbital-summary {
  margin: 0;
  font-size: 0.58rem;
  line-height: 1.45;
  color: rgba(255, 220, 160, 0.38);
}

/* ── Responsive ─────────────────────────────────── */
@media (max-width: 640px) {
  .stats {
    flex-direction: column;
    gap: 0.375rem;
  }
  .stat--right {
    border-left: none;
    padding-left: 0;
  }
}

@media (max-width: 600px) {
  .orbital-summary {
    display: none;
  }
}
</style>
