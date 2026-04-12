<script setup lang="ts">
import { computed } from 'vue'
import { buildSparkline } from '@/composables/useSparkline'

const props = defineProps<{
  score: number | null
  series: { date: string; value: number | null }[]
}>()

// buildSparkline returns { line: string; fill: string } — SVG path strings
const sparklinePath = computed(() => {
  const values = props.series.map(s => s.value)
  return buildSparkline(values, 160, 28).line
})

const hasEnoughData = computed(() => props.score !== null)
</script>

<template>
  <div class="sri-card bento-card">
    <div class="sri-card__label">SLEEP REGULARITY INDEX</div>

    <div class="sri-card__score">
      <span class="sri-card__number">{{ score ?? '--' }}</span>
      <span class="sri-card__denom">/ 100</span>
    </div>

    <svg v-if="hasEnoughData"
      class="sri-card__spark"
      viewBox="0 0 160 28"
      preserveAspectRatio="none"
      aria-hidden="true">
      <path
        :d="sparklinePath"
        fill="none"
        stroke="#00D4AA"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        opacity="0.8"
      />
    </svg>

    <div v-if="!hasEnoughData" class="sri-card__empty">Need 7+ nights</div>

    <div class="sri-card__citation">adapted · Windred et al. 2024</div>
  </div>
</template>

<style scoped>
.sri-card {
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.sri-card__label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.1em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.sri-card__score {
  display: flex;
  align-items: baseline;
  gap: 0.2rem;
  margin: 0.2rem 0;
}

.sri-card__number {
  font-size: 1.6rem;
  font-weight: 800;
  color: #00D4AA;
  letter-spacing: -0.02em;
  line-height: 1;
}

.sri-card__denom {
  font-size: 0.5rem;
  color: var(--text-muted);
}

.sri-card__spark {
  width: 100%;
  height: 28px;
  display: block;
  margin-top: 0.2rem;
}

.sri-card__empty {
  font-size: 0.5rem;
  color: var(--text-muted);
  font-style: italic;
}

.sri-card__citation {
  font-size: 0.45rem;
  color: var(--text-muted);
  font-style: italic;
  margin-top: 0.1rem;
}
</style>
