<script setup lang="ts">
interface OrbitalContext {
  label: string
  summary: string
}

interface CurrentAnchor {
  label: string
  lat: number
  lng: number
  timezone: string
}

interface SolarAnchor {
  phase: string
  elevationDeg: number
  sunriseLabel: string
  sunsetLabel: string
}

interface Props {
  context: OrbitalContext
  current: CurrentAnchor
  solar: SolarAnchor
}

defineProps<Props>()
</script>

<template>
  <section class="orbital-card" aria-label="Orbital context HUD">
    <div class="orbital-card__header">
      <div class="orbital-card__meta">
        <p class="orbital-card__eyebrow">Current frame</p>
        <span class="orbital-card__badge">{{ context.label }}</span>
      </div>
      <h3 class="orbital-card__title">{{ current.label }}</h3>
    </div>

    <dl class="orbital-card__facts">
      <div class="orbital-card__fact">
        <dt>Solar phase</dt>
        <dd>{{ solar.phase }}</dd>
      </div>
      <div class="orbital-card__fact">
        <dt>Elevation</dt>
        <dd>{{ solar.elevationDeg.toFixed(1) }}&deg;</dd>
      </div>
    </dl>

    <p class="orbital-card__summary">
      {{ context.summary }}
    </p>
  </section>
</template>

<style scoped>
.orbital-card {
  display: grid;
  gap: 0.82rem;
  padding: 0;
  max-width: none;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  color: rgba(241, 245, 249, 0.92);
}

.orbital-card__header {
  display: grid;
  gap: 0.42rem;
}

.orbital-card__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
}

.orbital-card__eyebrow {
  margin: 0;
  font-size: 0.62rem;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.78);
}

.orbital-card__badge {
  display: inline-flex;
  align-items: center;
  padding: 0.22rem 0.5rem;
  border-radius: 999px;
  border: 1px solid rgba(94, 234, 212, 0.18);
  background: rgba(0, 212, 170, 0.08);
  color: rgba(160, 255, 231, 0.9);
  font-size: 0.62rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.orbital-card__title {
  margin: 0;
  font-size: 0.96rem;
  line-height: 1.15;
  letter-spacing: -0.01em;
}

.orbital-card__facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.6rem;
  margin: 0;
}

.orbital-card__fact {
  display: grid;
  gap: 0.2rem;
  padding: 0.7rem 0.75rem;
  border-radius: 0.85rem;
  background: rgba(3, 10, 22, 0.42);
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.orbital-card__fact dt {
  margin: 0;
  font-size: 0.62rem;
  line-height: 1.1;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.8);
}

.orbital-card__fact dd {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.35;
  color: rgba(241, 245, 249, 0.94);
}

.orbital-card__summary {
  margin: 0;
  max-width: 16rem;
  font-size: 0.76rem;
  line-height: 1.4;
  color: rgba(226, 232, 240, 0.68);
}

@media (max-width: 640px) {
  .orbital-card {
    max-width: none;
  }

  .orbital-card__facts {
    grid-template-columns: 1fr;
  }
}
</style>
