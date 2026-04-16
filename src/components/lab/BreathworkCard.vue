<script setup lang="ts">
import { useBreathwork, TECHNIQUES } from '../../composables/lab/useBreathwork'
import type { Technique } from '../../composables/lab/useBreathwork'
import { buildEvidenceProfile } from '@/lib/evidence'
import LabCard from './LabCard.vue'
import LabEvidenceBlock from './LabEvidenceBlock.vue'

const { technique, durationMin, result } = useBreathwork()

const DURATIONS = [5, 10, 20, 30] as const

const techniqueKeys = Object.keys(TECHNIQUES) as Technique[]

const evidenceProfile = buildEvidenceProfile({
  evidenceTier: 'B',
  effectSummary: 'Controlled breathing sessions can raise rMSSD in adult lab studies.',
  populationSummary: 'Adult lab and meta-analytic breathing studies.',
  mainCaveat: 'Acute response varies by technique, session length, and individual responsiveness.',
  uncertaintyFactors: ['technique', 'session duration', 'baseline state'],
  claimBoundary: 'Session-level HRV guidance for adults, not a personal biometric prediction.',
})
</script>

<template>
  <LabCard
    accent="#00D4AA"
    label="BREATHWORK"
    title="HRV Session"
    citation="Laborde 2022 · NBR Meta-analysis · Van Diest 2014"
    :hasOutput="true"
  >
    <template #inputs>
      <div class="bw-inputs">

        <!-- Technique selector -->
        <div class="bw-group-label">Technique</div>
        <div class="bw-pills" role="group" aria-label="Breathing technique">
          <button
            v-for="key in techniqueKeys"
            :key="key"
            class="bw-pill"
            :class="{ 'bw-pill--active': technique === key }"
            :aria-pressed="technique === key"
            @click="technique = key"
          >
            {{ TECHNIQUES[key].label }}
          </button>
        </div>

        <!-- Duration selector -->
        <div class="bw-group-label">Duration</div>
        <div class="bw-pills" role="group" aria-label="Session duration">
          <button
            v-for="d in DURATIONS"
            :key="d"
            class="bw-pill"
            :class="{ 'bw-pill--active': durationMin === d }"
            :aria-pressed="durationMin === d"
            @click="durationMin = d"
          >
            {{ d }} min
          </button>
        </div>

      </div>
    </template>

    <template #output>
      <div class="bw-output">
        <div class="bw-output-grid">
          <div class="bw-output-cell">
            <span class="bw-output-key">rMSSD boost</span>
            <span class="bw-output-val bw-output-val--calm">+{{ result.rmssdBoost }} ms</span>
          </div>
          <div class="bw-output-cell">
            <span class="bw-output-key">Residual</span>
            <span class="bw-output-val">~{{ result.residualHours }}h HRV elevation</span>
          </div>
          <div class="bw-output-cell">
            <span class="bw-output-key">BPM target</span>
            <span class="bw-output-val">{{ result.bpm }} breaths/min</span>
          </div>
        </div>
      </div>
    </template>

    <template #evidence>
      <LabEvidenceBlock :profile="evidenceProfile" />
    </template>
  </LabCard>
</template>

<style scoped>
.bw-inputs {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-top: 0.2rem;
}

.bw-group-label {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  color: var(--text-secondary);
  letter-spacing: var(--tracking-fine);
  text-transform: uppercase;
  margin-top: 0.2rem;
}

.bw-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.bw-pill {
  padding: 0.2rem 0.55rem;
  border-radius: 4px;
  border: 1px solid rgba(0, 212, 170, 0.2);
  background: transparent;
  color: var(--text-muted);
  font-size: var(--font-size-xs3);
  font-family: 'Geist Mono', monospace;
  letter-spacing: var(--tracking-fine);
  text-transform: uppercase;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  white-space: nowrap;
}

.bw-pill:hover:not(.bw-pill--active) {
  background: rgba(0, 212, 170, 0.08);
  border-color: rgba(0, 212, 170, 0.35);
  color: var(--text-secondary);
}

.bw-pill--active {
  background: rgba(0, 212, 170, 0.15);
  border-color: rgba(0, 212, 170, 0.55);
  color: var(--card-accent);
}

/* Output */
.bw-output {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bw-output-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.35rem 0.5rem;
}

.bw-output-cell {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.bw-output-key {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-label);
  color: var(--text-muted);
  text-transform: uppercase;
}

.bw-output-val {
  font-size: var(--font-size-xs5);
  color: var(--text-primary);
  font-weight: 500;
  line-height: 1.3;
}

.bw-output-val--calm {
  color: #00D4AA;
  font-weight: 700;
}
</style>
