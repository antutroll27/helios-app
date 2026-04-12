<script setup lang="ts">
import { useSupplementGuide } from '../../composables/lab/useSupplementGuide'

const { rankedSupplements, hasPersonalization } = useSupplementGuide()

const GRADE_COLOR: Record<string, string> = {
  'A+': '#00D4AA',
  A:    '#9B8BFA',
  B:    '#FFBD76',
}

function opacityForScore(score: number): number {
  if (score >= 2) return 1
  if (score === 1) return 0.85
  return 0.65
}
</script>

<template>
  <div class="sg-card bento-card">

    <!-- Header -->
    <div class="sg-header">
      <div class="sg-label">SUPPLEMENTS</div>
      <h2 class="sg-title">Sleep Stack</h2>
    </div>

    <!-- Sub-card grid -->
    <div class="sg-grid">
      <div
        v-for="s in rankedSupplements"
        :key="s.key"
        class="sg-sub"
        :style="{
          '--grade-color': GRADE_COLOR[s.grade],
          opacity: hasPersonalization ? opacityForScore(s.score) : 1,
        }"
      >
        <!-- Grade badge + Recommended badge -->
        <div class="sg-badge-row">
          <div class="sg-grade-badge">GRADE {{ s.grade }}</div>
          <div v-if="hasPersonalization && s.isTopPick" class="sg-recommended-badge">
            Recommended ✓
          </div>
        </div>

        <!-- Name -->
        <div class="sg-name">{{ s.name }}</div>

        <!-- Dose + timing -->
        <div class="sg-dose-row">
          <span class="sg-dose">{{ s.dose }}</span>
          <span class="sg-sep">·</span>
          <span class="sg-timing">{{ s.timing }}</span>
        </div>

        <!-- Effect -->
        <div class="sg-effect">{{ s.effect }}</div>

        <!-- Caveat -->
        <p class="sg-caveat">{{ s.caveat }}</p>

        <!-- Citation -->
        <div class="sg-citation">{{ s.citation }}</div>

        <!-- Personalized note (only when biometrics are available) -->
        <div
          v-if="hasPersonalization"
          class="sg-note"
          :class="s.score >= 1 ? 'sg-note--triggered' : 'sg-note--fallback'"
        >
          {{ s.note }}
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.sg-card {
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  grid-column: 1 / -1;
}

/* ── Header ── */
.sg-header {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.sg-label {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-label);
  color: #FFBD76;
  font-weight: 700;
  text-transform: uppercase;
}

.sg-title {
  font-size: var(--font-size-md2);
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 0.1rem;
}

/* ── Sub-card grid ── */
.sg-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.6rem;
}

@media (max-width: 580px) {
  .sg-grid {
    grid-template-columns: 1fr;
  }
}

/* ── Individual sub-card ── */
.sg-sub {
  background: rgba(255, 246, 233, 0.03);
  border: 1px solid rgba(255, 246, 233, 0.08);
  border-radius: 0.6rem;
  padding: 0.75rem 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  transition: opacity 0.2s;
}

/* Badge row */
.sg-badge-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

/* Grade badge */
.sg-grade-badge {
  display: inline-flex;
  align-self: flex-start;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-4xs);
  letter-spacing: var(--tracking-label);
  font-weight: 700;
  text-transform: uppercase;
  color: #0A171D;
  background: var(--grade-color);
  border-radius: 3px;
  padding: 0.15rem 0.4rem;
}

/* Recommended badge */
.sg-recommended-badge {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-fine);
  text-transform: uppercase;
  color: #00D4AA;
  background: rgba(0, 212, 170, 0.1);
  border: 1px solid rgba(0, 212, 170, 0.3);
  border-radius: 4px;
  padding: 0.2rem 0.45rem;
  white-space: nowrap;
}

/* Name */
.sg-name {
  font-size: var(--font-size-xs5);
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 0.1rem;
}

/* Dose + timing */
.sg-dose-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  color: var(--text-muted);
  letter-spacing: var(--tracking-fine);
}

.sg-sep {
  opacity: 0.4;
}

/* Effect */
.sg-effect {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: var(--tracking-fine);
}

/* Caveat */
.sg-caveat {
  font-size: var(--font-size-xs3);
  font-style: italic;
  color: rgba(255, 189, 118, 0.75);
  background: rgba(255, 189, 118, 0.06);
  border-left: 2px solid rgba(255, 189, 118, 0.3);
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
  line-height: 1.45;
  margin: 0.1rem 0 0;
}

/* Citation */
.sg-citation {
  font-size: var(--font-size-4xs);
  color: rgba(255, 246, 233, 0.2);
  font-style: italic;
  margin-top: auto;
  padding-top: 0.2rem;
}

/* Personalized note */
.sg-note {
  font-size: var(--font-size-xs3);
  line-height: 1.4;
  border-left: 2px solid;
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
  margin-top: 0.1rem;
}

.sg-note--triggered {
  color: #00D4AA;
  background: rgba(0, 212, 170, 0.07);
  border-left-color: rgba(0, 212, 170, 0.35);
}

.sg-note--fallback {
  color: rgba(255, 246, 233, 0.35);
  background: none;
  border-left-color: rgba(255, 246, 233, 0.1);
}
</style>
