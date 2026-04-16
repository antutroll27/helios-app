<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { SUPPLEMENT_GOALS, type SupplementGoal } from '../../composables/lab/supplementCatalog'
import { useSupplementGuide } from '../../composables/lab/useSupplementGuide'

const selectedGoal = shallowRef<SupplementGoal>('sleep_onset')
const { rankedSupplements, hasPersonalization, usesBiometrics, usesTravelContext } = useSupplementGuide(selectedGoal)

const goalLabel = computed(
  () => SUPPLEMENT_GOALS.find((goal) => goal.key === selectedGoal.value)?.label ?? 'Sleep onset',
)

const personalizationCopy = computed(() => {
  if (usesBiometrics.value && usesTravelContext.value) {
    return 'Personalized with biometrics and travel state.'
  }
  if (usesBiometrics.value) {
    return 'Personalized with biometrics.'
  }
  if (usesTravelContext.value) {
    return 'Personalized with travel state.'
  }
  return 'Using the current wellness context.'
})
</script>

<template>
  <div class="sg-card bento-card">
    <div class="sg-header">
      <div class="sg-label">SUPPLEMENTS</div>
      <h2 class="sg-title">Goal-based guide</h2>
      <p class="sg-disclaimer">
        General wellness guidance only, not medical advice. If you are pregnant, take prescription medication, or have a medical condition, consult a clinician before using supplements.
      </p>
    </div>

    <div class="sg-goals" role="group" aria-label="Supplement goal selector">
      <button
        v-for="goal in SUPPLEMENT_GOALS"
        :key="goal.key"
        type="button"
        class="sg-goal"
        :class="{ 'sg-goal--active': selectedGoal === goal.key }"
        :aria-pressed="selectedGoal === goal.key"
        @click="selectedGoal = goal.key"
      >
        <span class="sg-goal__label">{{ goal.label }}</span>
        <span class="sg-goal__desc">{{ goal.description }}</span>
      </button>
    </div>

    <div class="sg-current">
      Showing guidance for <strong>{{ goalLabel }}</strong>.
      {{ hasPersonalization ? personalizationCopy : 'Using the current wellness context.' }}
    </div>

    <div class="sg-grid">
      <article
        v-for="supplement in rankedSupplements"
        :key="supplement.key"
        class="sg-sub"
        :class="{ 'sg-sub--top': supplement.isTopPick }"
      >
        <div class="sg-badge-row">
          <div class="sg-tier-badge">TIER {{ supplement.evidenceTier }}</div>
          <div v-if="supplement.isTopPick" class="sg-recommended-badge">
            Top pick
          </div>
        </div>

        <div class="sg-name">{{ supplement.name }}</div>

        <div class="sg-dose-row">
          <span class="sg-dose">{{ supplement.dose }}</span>
          <span class="sg-sep">&middot;</span>
          <span class="sg-timing">{{ supplement.timing }}</span>
        </div>

        <div class="sg-effect">{{ supplement.effect }}</div>
        <div class="sg-population">{{ supplement.population }}</div>

        <p class="sg-caveat">{{ supplement.caveat }}</p>
        <ul class="sg-contraindications">
          <li
            v-for="contraindication in supplement.contraindications"
            :key="contraindication"
          >
            {{ contraindication }}
          </li>
        </ul>
        <p class="sg-clinician">{{ supplement.clinicianDisclaimer }}</p>

        <div class="sg-note">
          <span class="sg-note__score">Score {{ supplement.score }}/5</span>
          <span>{{ supplement.note }}</span>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.sg-card {
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  grid-column: 1 / -1;
}

.sg-header {
  display: flex;
  flex-direction: column;
  gap: 0.22rem;
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
}

.sg-disclaimer {
  font-size: var(--font-size-xs3);
  line-height: 1.45;
  color: rgba(255, 246, 233, 0.72);
  background: rgba(255, 189, 118, 0.08);
  border-left: 2px solid rgba(255, 189, 118, 0.35);
  padding: 0.45rem 0.6rem;
  border-radius: 0 3px 3px 0;
  margin: 0.15rem 0 0;
}

.sg-goals {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.45rem;
}

@media (max-width: 720px) {
  .sg-goals {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.sg-goal {
  text-align: left;
  border-radius: 0.65rem;
  border: 1px solid rgba(255, 246, 233, 0.12);
  background: rgba(255, 246, 233, 0.03);
  padding: 0.55rem 0.6rem;
  color: var(--text-muted);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, transform 0.15s;
}

.sg-goal:hover {
  transform: translateY(-1px);
  border-color: rgba(255, 189, 118, 0.24);
}

.sg-goal--active {
  background: rgba(255, 189, 118, 0.12);
  border-color: rgba(255, 189, 118, 0.45);
  color: var(--text-primary);
}

.sg-goal__label {
  display: block;
  font-size: var(--font-size-xs3);
  font-family: 'Geist Mono', monospace;
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  font-weight: 700;
}

.sg-goal__desc {
  display: block;
  margin-top: 0.2rem;
  font-size: var(--font-size-4xs);
  line-height: 1.35;
}

.sg-current {
  font-size: var(--font-size-xs3);
  color: rgba(255, 246, 233, 0.75);
  background: rgba(155, 139, 250, 0.06);
  border-left: 2px solid rgba(155, 139, 250, 0.32);
  padding: 0.4rem 0.55rem;
  border-radius: 0 3px 3px 0;
}

.sg-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
}

@media (max-width: 680px) {
  .sg-grid {
    grid-template-columns: 1fr;
  }
}

.sg-sub {
  background: rgba(255, 246, 233, 0.03);
  border: 1px solid rgba(255, 246, 233, 0.08);
  border-radius: 0.75rem;
  padding: 0.8rem 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.sg-sub--top {
  border-color: rgba(0, 212, 170, 0.3);
  background: rgba(0, 212, 170, 0.05);
}

.sg-badge-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.sg-tier-badge,
.sg-recommended-badge {
  display: inline-flex;
  align-self: flex-start;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-4xs);
  letter-spacing: var(--tracking-label);
  font-weight: 700;
  text-transform: uppercase;
  border-radius: 3px;
  padding: 0.16rem 0.4rem;
}

.sg-tier-badge {
  color: #0A171D;
  background: #FFBD76;
}

.sg-recommended-badge {
  color: #00D4AA;
  background: rgba(0, 212, 170, 0.1);
  border: 1px solid rgba(0, 212, 170, 0.3);
}

.sg-name {
  font-size: var(--font-size-xs5);
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 0.08rem;
}

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

.sg-effect {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: var(--tracking-fine);
  line-height: 1.35;
}

.sg-population {
  font-size: var(--font-size-xs3);
  color: rgba(255, 246, 233, 0.82);
  line-height: 1.45;
}

.sg-caveat,
.sg-contraindications,
.sg-clinician {
  font-size: var(--font-size-xs3);
  line-height: 1.45;
  margin: 0;
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
}

.sg-caveat {
  font-style: italic;
  color: rgba(255, 189, 118, 0.8);
  background: rgba(255, 189, 118, 0.06);
  border-left: 2px solid rgba(255, 189, 118, 0.3);
}

.sg-contraindications {
  color: rgba(255, 246, 233, 0.78);
  background: rgba(255, 246, 233, 0.04);
  border-left: 2px solid rgba(255, 246, 233, 0.12);
  list-style: none;
}

.sg-contraindications li + li {
  margin-top: 0.2rem;
}

.sg-clinician {
  color: rgba(0, 212, 170, 0.82);
  background: rgba(0, 212, 170, 0.06);
  border-left: 2px solid rgba(0, 212, 170, 0.22);
}

.sg-note {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  font-size: var(--font-size-xs3);
  line-height: 1.4;
  border-left: 2px solid rgba(255, 246, 233, 0.12);
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
  color: rgba(255, 246, 233, 0.86);
  background: rgba(255, 246, 233, 0.02);
}

.sg-note__score {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-4xs);
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  color: rgba(255, 246, 233, 0.45);
}
</style>
