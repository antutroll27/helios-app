<script setup lang="ts">
import { computed } from 'vue'
import { useExerciseTiming } from '../../composables/lab/useExerciseTiming'
import type { Chronotype } from '../../composables/lab/useExerciseTiming'
import LabCard from './LabCard.vue'
import LabEvidenceBlock from './LabEvidenceBlock.vue'

const { hour, chronotype, result } = useExerciseTiming()

const CHRONOTYPES: { id: Chronotype; label: string }[] = [
  { id: 'early', label: 'Early' },
  { id: 'mid',   label: 'Mid'   },
  { id: 'late',  label: 'Late'  },
]

function formatHour(h: number): string {
  return `${h.toString().padStart(2, '0')}:00`
}

// Dynamic evidence effect string — computed so reactivity is explicit
const effectLabel = computed(() =>
  `${result.value.label} (${chronotype.value} chronotype, ${formatHour(hour.value)})`
)
</script>

<template>
  <LabCard
    accent="#9B8BFA"
    label="EXERCISE TIMING"
    title="Phase Shift"
    citation="Youngstedt 2019 · J Physiology · Thomas 2020 · Sato 2019"
    :hasOutput="true"
  >
    <!-- ── Inputs ── -->
    <template #inputs>
      <div class="et-inputs">

        <!-- Time slider -->
        <div class="et-row">
          <label class="et-label" for="et-hour">
            <span class="et-name">Exercise time</span>
            <span class="et-value">{{ formatHour(hour) }}</span>
          </label>
          <input
            id="et-hour"
            v-model.number="hour"
            type="range"
            min="5"
            max="23"
            step="1"
            class="et-slider"
            aria-label="Exercise hour"
          />
        </div>

        <!-- Chronotype toggle -->
        <div class="et-row">
          <span class="et-name">Chronotype</span>
          <div
            class="et-toggle-group"
            role="group"
            aria-label="Chronotype"
          >
            <button
              v-for="ct in CHRONOTYPES"
              :key="ct.id"
              class="et-toggle-btn"
              :class="{ 'et-toggle-btn--active': chronotype === ct.id }"
              :aria-pressed="chronotype === ct.id"
              @click="chronotype = ct.id"
            >
              {{ ct.label }}
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- ── Output ── -->
    <template #output>
      <div class="et-output">

        <!-- Phase shift label -->
        <div class="et-shift-row">
          <span class="et-shift-key">Phase shift</span>
          <span class="et-shift-val">{{ result.label }}</span>
        </div>

        <!-- Morning metabolic bonus badge -->
        <div v-if="result.morningMetabolicBonus" class="et-bonus-badge">
          Morning metabolic bonus &#10003;
        </div>

        <!-- Guidance note -->
        <p class="et-note">
          Best for late chronotypes: exercise before 10AM shifts circadian phase by up to 1.5&times; the baseline
        </p>
      </div>
    </template>

    <!-- ── Evidence ── -->
    <template #evidence>
      <LabEvidenceBlock
        :effect="effectLabel"
        population="Human PRC exercise studies (Youngstedt 2019), Thomas 2020 n=51"
        caveat="Chronotype and training status change the magnitude of the shift"
      />
    </template>
  </LabCard>
</template>

<style scoped>
/* ── Inputs ── */
.et-inputs {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 0.2rem;
}

.et-row {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.et-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.et-name {
  font-size: var(--font-size-xs3);
  color: var(--text-secondary);
  font-family: 'Geist Mono', monospace;
  letter-spacing: var(--tracking-fine);
  text-transform: uppercase;
}

.et-value {
  font-size: var(--font-size-xs5);
  color: var(--text-primary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* Slider */
.et-slider {
  width: 100%;
  height: 3px;
  appearance: none;
  background: rgba(255, 246, 233, 0.12);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
  accent-color: #9B8BFA;
}

.et-slider::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #9B8BFA;
  cursor: pointer;
  box-shadow: 0 0 4px rgba(155, 139, 250, 0.5);
}

.et-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #9B8BFA;
  border: none;
  cursor: pointer;
}

/* Chronotype toggle */
.et-toggle-group {
  display: flex;
  gap: 0.3rem;
  margin-top: 0.15rem;
}

.et-toggle-btn {
  flex: 1;
  padding: 0.25rem 0.4rem;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-xs3);
  letter-spacing: var(--tracking-fine);
  text-transform: uppercase;
  color: var(--text-muted);
  background: rgba(255, 246, 233, 0.05);
  border: 1px solid rgba(255, 246, 233, 0.1);
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.et-toggle-btn--active {
  color: #9B8BFA;
  background: rgba(155, 139, 250, 0.12);
  border-color: rgba(155, 139, 250, 0.4);
}

.et-toggle-btn:hover:not(.et-toggle-btn--active) {
  background: rgba(255, 246, 233, 0.08);
  color: var(--text-secondary);
}

/* ── Output ── */
.et-output {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.et-shift-row {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}

.et-shift-key {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-label);
  color: var(--text-muted);
  text-transform: uppercase;
}

.et-shift-val {
  font-size: 1.4rem;
  font-weight: 800;
  color: #9B8BFA;
  font-variant-numeric: tabular-nums;
  line-height: 1.15;
  letter-spacing: -0.03em;
}

/* Morning metabolic bonus badge */
.et-bonus-badge {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-fine);
  text-transform: uppercase;
  color: #00D4AA;
  background: rgba(0, 212, 170, 0.1);
  border: 1px solid rgba(0, 212, 170, 0.3);
  border-radius: 4px;
  padding: 0.2rem 0.45rem;
  align-self: flex-start;
  white-space: nowrap;
}

/* Guidance note */
.et-note {
  font-size: var(--font-size-xs3);
  color: rgba(155, 139, 250, 0.7);
  background: rgba(155, 139, 250, 0.07);
  border-left: 2px solid rgba(155, 139, 250, 0.35);
  padding: 0.3rem 0.5rem;
  border-radius: 0 3px 3px 0;
  line-height: 1.4;
  margin: 0;
}
</style>
