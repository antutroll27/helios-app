<script setup lang="ts">
import { useBiometricsStore } from '@/stores/biometrics'
import PhaseATile from './PhaseATile.vue'
import BodyClockDial from './BodyClockDial.vue'
import SRICard from './SRICard.vue'
import SleepDebtCard from './SleepDebtCard.vue'

const store = useBiometricsStore()
</script>

<template>
  <section class="proto-intel">
    <header class="proto-intel__header">
      <span class="proto-intel__title">PROTOCOL INTELLIGENCE</span>
      <span class="proto-intel__sub">Derived from your sleep patterns</span>
    </header>

    <!-- Phase A: 3 info tiles -->
    <div class="proto-intel__phase-a">
      <PhaseATile
        label="MELATONIN ONSET"
        :value="store.dlmoEstimate"
        subtext="dim lights 1h before"
        accent="#00D4AA"
      />
      <PhaseATile
        label="CAFFEINE CUTOFF"
        :value="store.caffeineCutoff"
        subtext="last coffee by this time"
        accent="#FFBD76"
      />
      <PhaseATile
        label="OPTIMAL NAP"
        :value="store.napWindow"
        subtext="26 min · NASA protocol"
        accent="var(--text-muted)"
      />
    </div>

    <!-- Phase B: Dial + SRI + Debt -->
    <div class="proto-intel__phase-b">
      <BodyClockDial
        :data="store.dialData"
        :now-angle="store.nowAngle"
      />
      <SRICard
        :score="store.sri"
        :series="store.sriSeries"
      />
      <SleepDebtCard
        :debt-min="store.sleepDebtMin"
        :series="store.sleepDebtSeries"
      />
    </div>
  </section>
</template>

<style scoped>
.proto-intel {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.proto-intel__header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--border-card);
}

.proto-intel__title {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;
  letter-spacing: 0.15em;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
}

.proto-intel__sub {
  font-size: 0.5rem;
  color: var(--text-muted);
}

.proto-intel__phase-a {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.proto-intel__phase-b {
  display: grid;
  grid-template-columns: 1.6fr 1fr 1fr;
  gap: 0.75rem;
  align-items: start;
}

@media (max-width: 640px) {
  .proto-intel__phase-a {
    grid-template-columns: 1fr;
  }
  .proto-intel__phase-b {
    grid-template-columns: 1fr;
  }
}
</style>
