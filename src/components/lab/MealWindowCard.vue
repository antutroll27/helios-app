<script setup lang="ts">
import { useMealWindow } from '../../composables/lab/useMealWindow'
import LabCard from './LabCard.vue'
import LabEvidenceBlock from './LabEvidenceBlock.vue'

const { firstMealHour, lastMealHour, sleepHour, result } = useMealWindow()

// Format a decimal hour as HH:MM (handles overflow 24=0:00, 25=1:00, 26=2:00)
function formatHour(h: number): string {
  const totalMin = Math.round(h * 60)
  const hrs = Math.floor(totalMin / 60) % 24
  const mins = totalMin % 60
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`
}

// Format decimal hours as "Xh" or "X.Xh"
function formatWindow(h: number): string {
  return Number.isInteger(h) ? `${h}h` : `${h.toFixed(1)}h`
}
</script>

<template>
  <LabCard
    accent="#FFBD76"
    label="MEAL WINDOW"
    title="TRF Score"
    citation="Sutton 2018 · Cell Metabolism · Manoogian 2022"
    :hasOutput="true"
  >
    <template #inputs>
      <div class="mw-inputs">

        <!-- First meal slider -->
        <div class="mw-row">
          <label class="mw-label" for="mw-first">
            <span class="mw-name">First meal</span>
            <span class="mw-value">{{ formatHour(firstMealHour) }}</span>
          </label>
          <input
            id="mw-first"
            v-model.number="firstMealHour"
            type="range"
            min="5"
            max="14"
            step="0.5"
            class="mw-slider"
            aria-label="First meal time"
          />
        </div>

        <!-- Last meal slider -->
        <div class="mw-row">
          <label class="mw-label" for="mw-last">
            <span class="mw-name">Last meal</span>
            <span class="mw-value">{{ formatHour(lastMealHour) }}</span>
          </label>
          <input
            id="mw-last"
            v-model.number="lastMealHour"
            type="range"
            min="12"
            max="22"
            step="0.5"
            class="mw-slider"
            aria-label="Last meal time"
          />
        </div>

        <!-- Sleep time slider (24=0:00, 25=1:00, 26=2:00) -->
        <div class="mw-row">
          <label class="mw-label" for="mw-sleep">
            <span class="mw-name">Sleep time</span>
            <span class="mw-value">{{ formatHour(sleepHour) }}</span>
          </label>
          <input
            id="mw-sleep"
            v-model.number="sleepHour"
            type="range"
            min="20"
            max="26"
            step="0.5"
            class="mw-slider"
            aria-label="Sleep time"
          />
        </div>
      </div>
    </template>

    <template #output>
      <!-- Invalid state: error banner -->
      <div v-if="!result.valid" class="mw-error" role="alert">
        <span class="mw-error__icon">&#9888;</span>
        {{ result.error }}
      </div>

      <!-- Valid state: score output -->
      <div v-else class="mw-output">
        <div class="mw-score-row">
          <div class="mw-score-block">
            <span class="mw-score-key">TRF Score</span>
            <span class="mw-score-val">{{ result.score }}<span class="mw-score-denom">/100</span></span>
          </div>
          <div v-if="result.earlyTRF" class="mw-badge-early">
            Early TRF &#10003;
          </div>
        </div>

        <div class="mw-stats-grid">
          <div class="mw-stat-cell">
            <span class="mw-stat-key">Eating window</span>
            <span class="mw-stat-val">{{ formatWindow(result.windowHours) }}</span>
          </div>
          <div class="mw-stat-cell">
            <span class="mw-stat-key">Before sleep</span>
            <span class="mw-stat-val">{{ formatWindow(result.hoursBeforeSleep) }}</span>
          </div>
        </div>

        <div v-if="result.glucoseBenefit" class="mw-glucose-note">
          <span class="mw-glucose-icon">&#128200;</span>
          {{ result.glucoseBenefit }}
        </div>
      </div>
    </template>

    <template #evidence>
      <LabEvidenceBlock
        effect="≤10h window: +10–15% glucose tolerance, -11/10 mmHg BP"
        population="Sutton 2018 (Cell Metabolism), Manoogian 2022 n=400,000 UK Biobank"
        caveat="Benefits strongest in metabolically at-risk populations. Meal composition matters too."
      />
    </template>
  </LabCard>
</template>

<style scoped>
.mw-inputs {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 0.2rem;
}

.mw-row {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.mw-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.mw-name {
  font-size: var(--font-size-xs3);
  color: var(--text-secondary);
  font-family: 'Geist Mono', monospace;
  letter-spacing: var(--tracking-fine);
  text-transform: uppercase;
}

.mw-value {
  font-size: var(--font-size-xs5);
  color: var(--text-primary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* Slider */
.mw-slider {
  width: 100%;
  height: 3px;
  appearance: none;
  background: rgba(255, 246, 233, 0.12);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
  accent-color: #FFBD76;
}

.mw-slider::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #FFBD76;
  cursor: pointer;
  box-shadow: 0 0 4px rgba(255, 189, 118, 0.5);
}

.mw-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #FFBD76;
  border: none;
  cursor: pointer;
}

/* Error banner */
.mw-error {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  font-size: var(--font-size-xs3);
  color: #FF4444;
  background: rgba(255, 68, 68, 0.08);
  border-left: 2px solid rgba(255, 68, 68, 0.45);
  padding: 0.35rem 0.5rem;
  border-radius: 0 3px 3px 0;
  line-height: 1.4;
}

.mw-error__icon {
  flex-shrink: 0;
  font-size: var(--font-size-xs5);
}

/* Output */
.mw-output {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.mw-score-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.mw-score-block {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}

.mw-score-key {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-label);
  color: var(--text-muted);
  text-transform: uppercase;
}

.mw-score-val {
  font-size: 1.5rem;
  font-weight: 800;
  color: #FFBD76;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
  letter-spacing: -0.03em;
}

.mw-score-denom {
  font-size: var(--font-size-xs5);
  font-weight: 500;
  color: rgba(255, 189, 118, 0.5);
  letter-spacing: 0;
}

/* Early TRF badge */
.mw-badge-early {
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

/* Stats grid */
.mw-stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.35rem 0.5rem;
}

.mw-stat-cell {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.mw-stat-key {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-label);
  color: var(--text-muted);
  text-transform: uppercase;
}

.mw-stat-val {
  font-size: var(--font-size-xs5);
  color: var(--text-primary);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

/* Glucose benefit note */
.mw-glucose-note {
  font-size: var(--font-size-xs3);
  color: rgba(0, 212, 170, 0.85);
  background: rgba(0, 212, 170, 0.07);
  border-left: 2px solid rgba(0, 212, 170, 0.35);
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
  line-height: 1.4;
}

.mw-glucose-icon {
  margin-right: 0.2rem;
}
</style>
