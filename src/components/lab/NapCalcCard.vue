<script setup lang="ts">
import { useNapCalc } from '../../composables/lab/useNapCalc'
import type { EvidenceProfile } from '@/lib/evidence'
import LabCard from './LabCard.vue'
import LabEvidenceBlock from './LabEvidenceBlock.vue'

const { hoursAwake, sleepDebtMin, result } = useNapCalc()

function boostLabel(minutes: number): string {
  return `~${Math.round(minutes / 60)}h`
}

const evidenceProfile = {
  evidenceTier: 'B',
  effectSummary: 'Short daytime naps improve alertness in controlled studies.',
  populationSummary: 'NASA and controlled nap studies in adults.',
  mainCaveat: 'Late naps can impair night sleep efficiency and timing still matters.',
  uncertaintyFactors: ['nap timing', 'sleep debt', 'individual sensitivity'],
  claimBoundary: 'Daytime nap timing guidance for alertness, not a personal performance prediction.',
} satisfies EvidenceProfile
</script>

<template>
  <LabCard
    accent="#00D4AA"
    label="NAP CALCULATOR"
    title="Nap Timing"
    citation="Rosekind 1995 · NASA · Dutheil 2021"
    :hasOutput="true"
  >
    <template #inputs>
      <div class="nap-inputs">
        <div class="nap-slider-row">
          <label class="nap-slider-label" for="nap-hours-awake">
            <span class="nap-slider-name">Hours awake</span>
            <span class="nap-slider-value">{{ hoursAwake }}h</span>
          </label>
          <input
            id="nap-hours-awake"
            v-model.number="hoursAwake"
            type="range"
            min="0"
            max="16"
            step="1"
            class="nap-slider"
          />
        </div>
        <div class="nap-slider-row">
          <label class="nap-slider-label" for="nap-sleep-debt">
            <span class="nap-slider-name">Sleep debt</span>
            <span class="nap-slider-value">{{ sleepDebtMin }} min</span>
          </label>
          <input
            id="nap-sleep-debt"
            v-model.number="sleepDebtMin"
            type="range"
            min="0"
            max="120"
            step="15"
            class="nap-slider"
          />
        </div>
      </div>
    </template>

    <template #output>
      <div class="nap-output">
        <div class="nap-output-grid">
          <div class="nap-output-cell">
            <span class="nap-output-key">Nap</span>
            <span class="nap-output-val nap-output-val--accent">{{ result.durationLabel }}</span>
          </div>
          <div class="nap-output-cell">
            <span class="nap-output-key">Take at</span>
            <span class="nap-output-val">{{ result.idealStart }}</span>
          </div>
          <div class="nap-output-cell">
            <span class="nap-output-key">Alert boost</span>
            <span class="nap-output-val">{{ boostLabel(result.boostMinutes) }}</span>
          </div>
          <div class="nap-output-cell">
            <span class="nap-output-key">Night sleep</span>
            <span class="nap-output-val" :class="result.nightPenalty > 0 ? 'nap-output-val--warn' : 'nap-output-val--ok'">
              <template v-if="result.nightPenalty === 0">&#10003; No impact</template>
              <template v-else>&#9888; &minus;{{ result.nightPenalty }}% efficiency</template>
            </span>
          </div>
        </div>
        <div v-if="result.coffeeNap" class="nap-coffee-hint">
          <span class="nap-coffee-icon">&#128161;</span>
          Drink coffee right before lying down &mdash; it peaks as you wake
        </div>
      </div>
    </template>

    <template #evidence>
      <LabEvidenceBlock :profile="evidenceProfile" />
    </template>
  </LabCard>
</template>

<style scoped>
.nap-inputs {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 0.2rem;
}

.nap-slider-row {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.nap-slider-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.nap-slider-name {
  font-size: var(--font-size-xs3);
  color: var(--text-secondary);
  font-family: 'Geist Mono', monospace;
  letter-spacing: var(--tracking-fine);
  text-transform: uppercase;
}

.nap-slider-value {
  font-size: var(--font-size-xs5);
  color: var(--text-primary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.nap-slider {
  width: 100%;
  height: 3px;
  appearance: none;
  background: rgba(255, 246, 233, 0.12);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
  accent-color: #00D4AA;
}

.nap-slider::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #00D4AA;
  cursor: pointer;
  box-shadow: 0 0 4px rgba(0, 212, 170, 0.5);
}

.nap-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #00D4AA;
  border: none;
  cursor: pointer;
}

.nap-output {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nap-output-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.35rem 0.5rem;
}

.nap-output-cell {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.nap-output-key {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-label);
  color: var(--text-muted);
  text-transform: uppercase;
}

.nap-output-val {
  font-size: var(--font-size-xs5);
  color: var(--text-primary);
  font-weight: 500;
  line-height: 1.3;
}

.nap-output-val--accent {
  color: #00D4AA;
  font-weight: 600;
}

.nap-output-val--ok {
  color: #00D4AA;
}

.nap-output-val--warn {
  color: #FFBD76;
}

.nap-coffee-hint {
  font-size: var(--font-size-xs3);
  color: rgba(255, 189, 118, 0.85);
  background: rgba(255, 189, 118, 0.07);
  border-left: 2px solid rgba(255, 189, 118, 0.35);
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
  line-height: 1.4;
}

.nap-coffee-icon {
  margin-right: 0.2rem;
}
</style>
