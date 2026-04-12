<script setup lang="ts">
const supplements = [
  {
    name: 'Melatonin',
    dose: '0.5–1 mg',
    timing: '60–90 min before bed',
    effect: '-7 min sleep latency',
    caveat: 'Best for circadian misalignment (jet lag, shift work). Higher doses cause receptor desensitisation — more is not better.',
    grade: 'B',
    citation: 'Fatemeh 2022, k=23 RCTs',
  },
  {
    name: 'Mg Glycinate',
    dose: '225–400 mg',
    timing: '30–60 min before bed',
    effect: '-17 min latency, +16 min TST',
    caveat: 'Studies mostly in elderly adults with insomnia. Effect in healthy young adults is likely much smaller.',
    grade: 'C',
    citation: 'Mah 2021, BMC meta-analysis',
  },
  {
    name: 'Glycine',
    dose: '3 g',
    timing: '30 min before bed',
    effect: '-10 min latency, -0.1–0.2°C core temp',
    caveat: 'Mechanism is well-understood (peripheral vasodilation lowers core temp). Fewest side effects of the three.',
    grade: 'B',
    citation: 'Bannai 2012',
  },
] as const

const GRADE_COLOR: Record<string, string> = {
  A: '#00D4AA',
  B: '#9B8BFA',
  C: '#FFBD76',
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
        v-for="s in supplements"
        :key="s.name"
        class="sg-sub"
        :style="{ '--grade-color': GRADE_COLOR[s.grade] }"
      >
        <!-- Grade badge -->
        <div class="sg-grade-badge">GRADE {{ s.grade }}</div>

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

        <!-- Caveat — always visible -->
        <p class="sg-caveat">{{ s.caveat }}</p>

        <!-- Citation -->
        <div class="sg-citation">{{ s.citation }}</div>
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

/* Caveat — always visible, amber tint */
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
</style>
