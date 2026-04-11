<script setup lang="ts">
import { computed } from 'vue'
import type { GlobeComparison } from '@/composables/useCobeGlobeData'

type ComparisonItem = Pick<
  GlobeComparison,
  'id' | 'label' | 'timezoneDeltaHours' | 'travelReadiness'
>

interface Props {
  comparisons: ComparisonItem[]
  selectedDestinationId: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (event: 'select-destination', destinationId: string): void
}>()

const displayedComparisons = computed(() => {
  const selected = props.comparisons.find((comparison) => comparison.id === props.selectedDestinationId)
  const rest = props.comparisons.filter((comparison) => comparison.id !== selected?.id)
  const comparisons: ComparisonItem[] = []

  if (selected) {
    comparisons.push(selected)
  }

  comparisons.push(...rest)

  return comparisons.slice(0, 3)
})

function formatSignedHours(value: number) {
  const absolute = Math.abs(value).toFixed(1)
  return value > 0 ? `+${absolute}h` : value < 0 ? `-${absolute}h` : '0h'
}

function handleSelect(destinationId: string) {
  emit('select-destination', destinationId)
}
</script>

<template>
  <section class="comparison-rail" aria-label="Destination comparison HUD">
    <div class="comparison-rail__heading">
      <p class="comparison-rail__eyebrow">Destinations</p>
      <h3 class="comparison-rail__title">Choose a city</h3>
    </div>

    <div v-if="displayedComparisons.length" class="comparison-rail__list">
      <button
        v-for="comparison in displayedComparisons"
        :key="comparison.id"
        type="button"
        class="comparison-rail__item"
        :class="{ 'comparison-rail__item--active': comparison.id === props.selectedDestinationId }"
        :aria-pressed="comparison.id === props.selectedDestinationId"
        @click="handleSelect(comparison.id)"
      >
        <div class="comparison-rail__row">
          <strong class="comparison-rail__label">{{ comparison.label }}</strong>
          <span class="comparison-rail__delta">{{ formatSignedHours(comparison.timezoneDeltaHours) }}</span>
        </div>

        <p class="comparison-rail__status">{{ comparison.travelReadiness }}</p>

        <span v-if="comparison.id === props.selectedDestinationId" class="comparison-rail__selected">
          Active
        </span>
      </button>
    </div>

    <div v-else class="comparison-rail__empty">
      No destination comparisons are available yet.
    </div>
  </section>
</template>

<style scoped>
.comparison-rail {
  display: flex;
  flex-direction: column;
  gap: 0.72rem;
  padding: 0.82rem 0.82rem 0.86rem;
  max-width: 14.25rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 1.15rem;
  background:
    linear-gradient(180deg, rgba(7, 14, 27, 0.9), rgba(7, 14, 27, 0.72)),
    radial-gradient(circle at top right, rgba(94, 234, 212, 0.08), transparent 46%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 20px 42px rgba(2, 8, 20, 0.22);
  color: rgba(241, 245, 249, 0.92);
}

.comparison-rail__heading {
  display: grid;
  gap: 0.16rem;
}

.comparison-rail__eyebrow {
  margin: 0;
  font-size: 0.62rem;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.78);
}

.comparison-rail__title {
  margin: 0;
  font-size: 0.86rem;
  line-height: 1.12;
  letter-spacing: -0.01em;
}

.comparison-rail__list {
  display: grid;
  gap: 0.42rem;
}

.comparison-rail__item {
  appearance: none;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 0.95rem;
  padding: 0.66rem 0.68rem;
  background: rgba(4, 10, 21, 0.56);
  color: inherit;
  text-align: left;
  display: grid;
  gap: 0.34rem;
  cursor: pointer;
  transition:
    transform 140ms ease,
    border-color 140ms ease,
    background-color 140ms ease,
    box-shadow 140ms ease,
    opacity 140ms ease;
}

.comparison-rail__item:hover {
  transform: translateY(-1px);
  border-color: rgba(94, 234, 212, 0.32);
  background: rgba(5, 14, 28, 0.68);
}

.comparison-rail__item:focus-visible {
  outline: 2px solid rgba(94, 234, 212, 0.92);
  outline-offset: 2px;
  border-color: rgba(94, 234, 212, 0.62);
}

.comparison-rail__item--active {
  border-color: rgba(0, 212, 170, 0.52);
  background:
    linear-gradient(180deg, rgba(4, 10, 21, 0.82), rgba(4, 10, 21, 0.64)),
    linear-gradient(90deg, rgba(0, 212, 170, 0.08), transparent 48%);
  box-shadow:
    inset 0 0 0 1px rgba(0, 212, 170, 0.08),
    0 16px 28px rgba(0, 212, 170, 0.08);
}

.comparison-rail__row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.38rem;
}

.comparison-rail__label {
  min-width: 0;
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.comparison-rail__delta {
  flex: none;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: rgba(94, 234, 212, 0.96);
}

.comparison-rail__status {
  margin: 0;
  font-size: 0.66rem;
  line-height: 1.3;
  color: rgba(241, 245, 249, 0.82);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.comparison-rail__selected {
  display: inline-flex;
  align-items: center;
  justify-self: start;
  padding: 0.16rem 0.4rem;
  border-radius: 999px;
  background: rgba(0, 212, 170, 0.12);
  border: 1px solid rgba(0, 212, 170, 0.22);
  color: rgba(160, 255, 231, 0.92);
  font-size: 0.58rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.comparison-rail__empty {
  padding: 0.7rem 0.8rem;
  border-radius: 0.85rem;
  background: rgba(3, 10, 22, 0.45);
  color: rgba(148, 163, 184, 0.88);
  font-size: 0.78rem;
}

@media (max-width: 960px) {
  .comparison-rail {
    max-width: none;
    padding: 0.8rem;
  }
}
</style>
