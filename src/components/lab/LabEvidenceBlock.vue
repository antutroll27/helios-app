<script setup lang="ts">
import { computed } from 'vue'
import type { EvidenceProfile } from '@/lib/evidence'

const props = defineProps<{
  profile?: EvidenceProfile
  effect?: string
  population?: string
  caveat?: string
}>()

const legacyProfile = computed<EvidenceProfile | null>(() => {
  if (props.profile) return props.profile
  if (props.effect && props.population && props.caveat) {
    return {
      evidenceTier: 'B',
      effectSummary: props.effect,
      populationSummary: props.population,
      mainCaveat: props.caveat,
      uncertaintyFactors: [],
      claimBoundary: '',
    }
  }
  return null
})
</script>

<template>
  <div class="lab-evidence">
    <template v-if="props.profile">
      <div class="lab-evidence__row">
        <span class="lab-evidence__key">Tier</span>
        <span class="lab-evidence__val">Tier {{ props.profile.evidenceTier }}</span>
      </div>
      <div class="lab-evidence__row">
        <span class="lab-evidence__key">Effect</span>
        <span class="lab-evidence__val">{{ props.profile.effectSummary }}</span>
      </div>
      <div class="lab-evidence__row">
        <span class="lab-evidence__key">Population</span>
        <span class="lab-evidence__val">{{ props.profile.populationSummary }}</span>
      </div>
      <div class="lab-evidence__row lab-evidence__row--caveat">
        <span class="lab-evidence__key">Caveat</span>
        <span class="lab-evidence__val">{{ props.profile.mainCaveat }}</span>
      </div>
      <div class="lab-evidence__row">
        <span class="lab-evidence__key">Boundary</span>
        <span class="lab-evidence__val">{{ props.profile.claimBoundary }}</span>
      </div>
    </template>
    <template v-else-if="legacyProfile">
      <div class="lab-evidence__row">
        <span class="lab-evidence__key">Effect</span>
        <span class="lab-evidence__val">{{ legacyProfile.effectSummary }}</span>
      </div>
      <div class="lab-evidence__row">
        <span class="lab-evidence__key">Population</span>
        <span class="lab-evidence__val">{{ legacyProfile.populationSummary }}</span>
      </div>
      <div class="lab-evidence__row lab-evidence__row--caveat">
        <span class="lab-evidence__key">Caveat</span>
        <span class="lab-evidence__val">{{ legacyProfile.mainCaveat }}</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.lab-evidence {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  margin-top: 0.2rem;
}
.lab-evidence__row {
  display: flex;
  gap: 0.4rem;
  align-items: baseline;
  font-size: var(--font-size-3xs);
  line-height: 1.5;
}
.lab-evidence__key {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-4xs);
  letter-spacing: var(--tracking-fine);
  color: var(--text-muted);
  text-transform: uppercase;
  flex-shrink: 0;
  width: 56px;
}
.lab-evidence__val {
  color: rgba(255,246,233,0.65);
}
.lab-evidence__row--caveat .lab-evidence__val {
  color: rgba(255,189,118,0.7);
  font-style: italic;
}
</style>
