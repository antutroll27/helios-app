<script setup lang="ts">
import { useAlcoholImpact } from '../../composables/lab/useAlcoholImpact'
import type { EvidenceProfile } from '@/lib/evidence'
import LabCard from './LabCard.vue'
import LabEvidenceBlock from './LabEvidenceBlock.vue'

const { drinks, weightKg, sex, sleepHour, hoursSinceDrinking, result } = useAlcoholImpact()

// Format hour value 20–26 → display string (24=0:00, 25=1:00, 26=2:00)
function formatHour(h: number): string {
  const display = h >= 24 ? h - 24 : h
  return `${display}:00`
}

// Format a fractional hour as HH:MM for the cutoff output
function formatCutoff(h: number): string {
  const totalMin = Math.round(h * 60)
  const hrs = Math.floor(totalMin / 60) % 24
  const mins = totalMin % 60
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`
}

const evidenceProfile = {
  evidenceTier: 'B',
  effectSummary: 'Evening drinking is associated with next-morning HRV and sleep disruption.',
  populationSummary: 'Free-living adult nights in a large observational sample.',
  mainCaveat: 'Response varies substantially by body size, sex, tolerance, and meal timing.',
  uncertaintyFactors: ['body size', 'sex', 'tolerance', 'meal timing'],
  claimBoundary: 'Sleep-disruption estimate for drinking nights, not a personal BAC model.',
} satisfies EvidenceProfile

function evidenceEffect(): string {
  const drinks_val = drinks.value
  if (drinks_val === 0) return 'No HRV impact (0 drinks)'
  if (drinks_val <= 2) return 'HRV next morning: -9.3% (1–2 drinks)'
  if (drinks_val <= 4) return 'HRV next morning: -24% (3–4 drinks)'
  return 'HRV next morning: -39.2% (5+ drinks)'
}
</script>

<template>
  <LabCard
    accent="#9B8BFA"
    label="ALCOHOL IMPACT"
    title="Sleep Disruption"
    citation="Pietilä 2018 · JMIR · n=4,098"
    :hasOutput="true"
  >
    <template #inputs>
      <div class="alc-inputs">

        <!-- Drinks stepper -->
        <div class="alc-row">
          <div class="alc-label">
            <span class="alc-name" id="alc-drinks-label">Drinks tonight</span>
            <span class="alc-value">{{ drinks }}</span>
          </div>
          <div class="alc-stepper" role="group" aria-labelledby="alc-drinks-label">
            <button
              class="alc-step-btn"
              :disabled="drinks <= 0"
              @click="drinks = Math.max(0, drinks - 1)"
              aria-label="Decrease drinks"
            >&#8722;</button>
            <span class="alc-step-count" aria-hidden="true">{{ drinks }}</span>
            <button
              class="alc-step-btn"
              :disabled="drinks >= 8"
              @click="drinks = Math.min(8, drinks + 1)"
              aria-label="Increase drinks"
            >&#43;</button>
          </div>
        </div>

        <!-- Weight slider -->
        <div class="alc-row">
          <label class="alc-label" for="alc-weight">
            <span class="alc-name">Body weight</span>
            <span class="alc-value">{{ weightKg }} kg</span>
          </label>
          <input
            id="alc-weight"
            v-model.number="weightKg"
            type="range"
            min="40"
            max="120"
            step="5"
            class="alc-slider"
          />
        </div>

        <!-- Sex toggle -->
        <div class="alc-row">
          <span class="alc-name">Biological sex</span>
          <div class="alc-toggle" role="group" aria-label="Biological sex">
            <button
              class="alc-toggle-btn"
              :class="{ 'alc-toggle-btn--active': sex === 'male' }"
              :aria-pressed="sex === 'male'"
              @click="sex = 'male'"
            >Male</button>
            <button
              class="alc-toggle-btn"
              :class="{ 'alc-toggle-btn--active': sex === 'female' }"
              :aria-pressed="sex === 'female'"
              @click="sex = 'female'"
            >Female</button>
          </div>
        </div>

        <!-- Sleep time slider -->
        <div class="alc-row">
          <label class="alc-label" for="alc-sleep">
            <span class="alc-name">Sleep time</span>
            <span class="alc-value">{{ formatHour(sleepHour) }}</span>
          </label>
          <input
            id="alc-sleep"
            v-model.number="sleepHour"
            type="range"
            min="20"
            max="26"
            step="1"
            class="alc-slider"
          />
        </div>

        <!-- Hours since last drink -->
        <div class="alc-row">
          <label class="alc-label" for="alc-hours">
            <span class="alc-name">Since last drink</span>
            <span class="alc-value">{{ hoursSinceDrinking }}h</span>
          </label>
          <input
            id="alc-hours"
            v-model.number="hoursSinceDrinking"
            type="range"
            min="0"
            max="8"
            step="0.5"
            class="alc-slider"
          />
        </div>
      </div>
    </template>

    <template #output>
      <!-- Zero-drink state -->
      <div v-if="drinks === 0" class="alc-no-impact">
        <span class="alc-no-impact__icon">&#10003;</span>
        No impact tonight
      </div>

      <!-- Active output -->
      <div v-else class="alc-output">
        <div class="alc-output-grid">
          <div class="alc-output-cell">
            <span class="alc-output-key">HRV drop</span>
            <span class="alc-output-val alc-output-val--storm">{{ result.hrvDropPct }}%</span>
          </div>
          <div class="alc-output-cell">
            <span class="alc-output-key">REM lost</span>
            <span class="alc-output-val">~{{ result.remLossMin }} min</span>
          </div>
          <div class="alc-output-cell">
            <span class="alc-output-key">BAC now</span>
            <span class="alc-output-val" :class="result.bac >= 0.05 ? 'alc-output-val--storm' : 'alc-output-val--muted'">
              {{ result.bac.toFixed(3) }}%
              <span v-if="result.bac >= 0.05" class="alc-output-sub">&ge;0.05 impairs sleep</span>
            </span>
          </div>
          <div class="alc-output-cell">
            <span class="alc-output-key">Clears in</span>
            <span class="alc-output-val" :class="result.hoursToClear > 0 ? 'alc-output-val--warn' : 'alc-output-val--ok'">
              <template v-if="result.hoursToClear === 0">Cleared</template>
              <template v-else>{{ result.hoursToClear.toFixed(1) }}h</template>
            </span>
          </div>
        </div>
        <div class="alc-cutoff-hint">
          <span class="alc-cutoff-icon">&#128344;</span>
          Drink before {{ formatCutoff(result.cutoffHour) }} for minimal sleep impact
        </div>
      </div>
    </template>

    <template #evidence>
      <LabEvidenceBlock :profile="evidenceProfile" />
    </template>
  </LabCard>
</template>

<style scoped>
.alc-inputs {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 0.2rem;
}

.alc-row {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.alc-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.alc-name {
  font-size: var(--font-size-xs3);
  color: var(--text-secondary);
  font-family: 'Geist Mono', monospace;
  letter-spacing: var(--tracking-fine);
  text-transform: uppercase;
}

.alc-value {
  font-size: var(--font-size-xs5);
  color: var(--text-primary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* Slider */
.alc-slider {
  width: 100%;
  height: 3px;
  appearance: none;
  background: rgba(255, 246, 233, 0.12);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
  accent-color: #9B8BFA;
}

.alc-slider::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #9B8BFA;
  cursor: pointer;
  box-shadow: 0 0 4px rgba(155, 139, 250, 0.5);
}

.alc-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #9B8BFA;
  border: none;
  cursor: pointer;
}

/* Drinks stepper */
.alc-stepper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.alc-step-btn {
  width: 22px;
  height: 22px;
  border-radius: 4px;
  border: 1px solid rgba(155, 139, 250, 0.35);
  background: rgba(155, 139, 250, 0.08);
  color: #9B8BFA;
  font-size: var(--font-size-xs5);
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.alc-step-btn:hover:not(:disabled) {
  background: rgba(155, 139, 250, 0.2);
}

.alc-step-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.alc-step-count {
  font-size: var(--font-size-md2);
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
  min-width: 20px;
  text-align: center;
}

/* Sex toggle */
.alc-toggle {
  display: flex;
  gap: 0.3rem;
  margin-top: 0.2rem;
}

.alc-toggle-btn {
  flex: 1;
  padding: 0.2rem 0;
  border-radius: 4px;
  border: 1px solid rgba(155, 139, 250, 0.25);
  background: transparent;
  color: var(--text-muted);
  font-size: var(--font-size-xs3);
  font-family: 'Geist Mono', monospace;
  letter-spacing: var(--tracking-fine);
  text-transform: uppercase;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.alc-toggle-btn--active {
  background: rgba(155, 139, 250, 0.18);
  border-color: rgba(155, 139, 250, 0.6);
  color: #9B8BFA;
}

/* Zero-drink state */
.alc-no-impact {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: var(--font-size-xs5);
  color: #00D4AA;
  font-weight: 600;
  padding: 0.3rem 0;
}

.alc-no-impact__icon {
  font-size: var(--font-size-md2);
}

/* Output grid */
.alc-output {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.alc-output-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.35rem 0.5rem;
}

.alc-output-cell {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.alc-output-key {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-label);
  color: var(--text-muted);
  text-transform: uppercase;
}

.alc-output-val {
  font-size: var(--font-size-xs5);
  color: var(--text-primary);
  font-weight: 500;
  line-height: 1.3;
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}

.alc-output-val--storm {
  color: #FF4444;
  font-weight: 600;
}

.alc-output-val--warn {
  color: #FFBD76;
  font-weight: 500;
}

.alc-output-val--ok {
  color: #00D4AA;
  font-weight: 500;
}

.alc-output-val--muted {
  color: var(--text-secondary);
}

.alc-output-sub {
  font-size: var(--font-size-3xs);
  color: rgba(255, 68, 68, 0.75);
  font-weight: 400;
}

/* Cutoff hint */
.alc-cutoff-hint {
  font-size: var(--font-size-xs3);
  color: rgba(155, 139, 250, 0.85);
  background: rgba(155, 139, 250, 0.07);
  border-left: 2px solid rgba(155, 139, 250, 0.35);
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
  line-height: 1.4;
}

.alc-cutoff-icon {
  margin-right: 0.2rem;
}
</style>
