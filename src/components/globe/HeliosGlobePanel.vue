<script setup lang="ts">
import { computed } from 'vue'
import GlobeHealthStrip from './GlobeHealthStrip.vue'
import GlobeOrbitalContext from './GlobeOrbitalContext.vue'
import GlobeProtocolCountdown from './GlobeProtocolCountdown.vue'
import GlobeStatStrip from './GlobeStatStrip.vue'
import HeliosCobeGlobe from './HeliosCobeGlobe.vue'
import { useCobeGlobeData } from '@/composables/useCobeGlobeData'

const {
  currentSnapshot,
  localSolar,
  comparisons,
  selectedComparison,
  selectedDestinationId,
  orbitalContext,
  selectDestination,
  clearDestination,
} = useCobeGlobeData()

const headerStatus = computed(() => {
  if (!selectedComparison.value) {
    return `${currentSnapshot.value.label} | ${localSolar.value.phase}`
  }
  return `${currentSnapshot.value.label} to ${selectedComparison.value.label}`
})

const timingLabel = computed(() => {
  const comparison = selectedComparison.value
  if (!comparison) {
    return `Sunrise ${localSolar.value.sunriseLabel} | Sunset ${localSolar.value.sunsetLabel}`
  }
  const sunriseDelta = formatSignedMinutes(comparison.sunriseDeltaMinutes)
  const sunsetDelta = formatSignedMinutes(comparison.sunsetDeltaMinutes)
  return `Sunrise ${sunriseDelta} | Sunset ${sunsetDelta}`
})

function formatSignedMinutes(value: number) {
  if (value === 0) return 'aligned'
  const direction = value > 0 ? '+' : '-'
  return `${direction}${Math.abs(value)}m`
}

function handleDestSelect(id: string | null) {
  if (id === null) {
    clearDestination()
  } else {
    selectDestination(id)
  }
}
</script>

<template>
  <section class="globe-panel" aria-label="HELIOS COBE globe panel">
    <div class="globe-panel__hero">
      <div class="globe-panel__backdrop" aria-hidden="true" />

      <div class="globe-panel__overlay globe-panel__overlay--intro">
        <section class="globe-panel__intro-slab" aria-label="Orbital intro panel">
          <header class="globe-panel__header">
            <p class="globe-panel__eyebrow">HELIOS / COBE</p>
            <h2 class="globe-panel__title">Orbital View</h2>
            <p class="globe-panel__status">{{ headerStatus }}</p>
          </header>

          <GlobeOrbitalContext
            :context="orbitalContext"
            :current="currentSnapshot"
            :solar="localSolar"
            :route-label="selectedComparison?.label"
          />
        </section>
      </div>

      <div class="globe-panel__overlay globe-panel__overlay--countdown">
        <GlobeProtocolCountdown
          :selected-comparison="selectedComparison"
          :comparisons="comparisons"
          @select-destination="handleDestSelect"
        />
      </div>

      <div class="globe-panel__stage">
        <HeliosCobeGlobe
          class="globe-panel__globe"
          :current="currentSnapshot"
          :comparisons="comparisons"
          :selected-destination-id="selectedDestinationId"
        />
      </div>

      <div class="globe-panel__overlay globe-panel__overlay--health">
        <GlobeHealthStrip />
      </div>

      <div class="globe-panel__overlay globe-panel__overlay--stats">
        <GlobeStatStrip
          :anchor-label="currentSnapshot.label"
          :destination-label="selectedComparison?.label ?? 'Baseline view'"
          :timing-label="timingLabel"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
.globe-panel {
  display: grid;
  width: 100%;
  color: rgba(241, 245, 249, 0.96);
}

.globe-panel__header {
  display: grid;
  gap: 0.32rem;
}

.globe-panel__eyebrow {
  margin: 0;
  font-size: 0.64rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.78);
  white-space: nowrap;
  font-weight: 600;
}

.globe-panel__title {
  margin: 0;
  font-size: clamp(0.98rem, 1.2vw, 1.1rem);
  line-height: 1.1;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(241, 245, 249, 0.92);
  font-weight: 600;
}

.globe-panel__status {
  margin: 0;
  padding-top: 0.42rem;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  color: rgba(226, 232, 240, 0.7);
  font-size: 0.62rem;
  letter-spacing: 0.14em;
  line-height: 1.2;
  text-transform: uppercase;
}

.globe-panel__status::before {
  content: 'ROUTE / ';
  color: rgba(148, 163, 184, 0.82);
}

.globe-panel__hero {
  position: relative;
  min-height: clamp(46rem, 88vh, 62rem);
  overflow: hidden;
  border-radius: 2rem;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background:
    radial-gradient(circle at 50% 44%, rgba(73, 193, 255, 0.09), transparent 24%),
    radial-gradient(circle at 48% 58%, rgba(10, 132, 255, 0.06), transparent 30%),
    radial-gradient(circle at 18% 18%, rgba(0, 212, 170, 0.05), transparent 20%),
    radial-gradient(circle at 84% 24%, rgba(56, 189, 248, 0.05), transparent 18%),
    linear-gradient(180deg, rgba(5, 10, 22, 0.94), rgba(2, 6, 18, 0.98));
  box-shadow:
    0 28px 72px rgba(2, 8, 20, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.globe-panel__backdrop {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 50% 42%, rgba(6, 13, 28, 0), rgba(2, 6, 18, 0.2) 58%, rgba(2, 6, 18, 0.76) 100%),
    radial-gradient(circle at 50% 30%, rgba(111, 216, 255, 0.08), transparent 18%),
    radial-gradient(circle at 44% 22%, rgba(16, 185, 129, 0.04), transparent 16%),
    radial-gradient(circle at 31% 18%, rgba(255, 255, 255, 0.82) 0 0.09rem, transparent 0.11rem),
    radial-gradient(circle at 41% 27%, rgba(255, 255, 255, 0.58) 0 0.06rem, transparent 0.08rem),
    radial-gradient(circle at 49% 17%, rgba(148, 223, 255, 0.74) 0 0.08rem, transparent 0.1rem),
    radial-gradient(circle at 57% 21%, rgba(255, 255, 255, 0.64) 0 0.07rem, transparent 0.09rem),
    radial-gradient(circle at 65% 29%, rgba(111, 216, 255, 0.7) 0 0.07rem, transparent 0.09rem),
    radial-gradient(circle at 74% 22%, rgba(255, 255, 255, 0.6) 0 0.07rem, transparent 0.09rem),
    radial-gradient(circle at 79% 33%, rgba(177, 232, 255, 0.62) 0 0.06rem, transparent 0.08rem),
    radial-gradient(circle at 24% 40%, rgba(255, 255, 255, 0.42) 0 0.05rem, transparent 0.07rem),
    radial-gradient(circle at 36% 48%, rgba(167, 231, 255, 0.48) 0 0.06rem, transparent 0.08rem),
    radial-gradient(circle at 61% 39%, rgba(255, 255, 255, 0.4) 0 0.05rem, transparent 0.07rem),
    radial-gradient(circle at 72% 46%, rgba(167, 231, 255, 0.44) 0 0.06rem, transparent 0.08rem),
    radial-gradient(circle at 84% 18%, rgba(73, 193, 255, 0.05), transparent 13%),
    radial-gradient(circle at 16% 24%, rgba(32, 196, 255, 0.05), transparent 14%);
  pointer-events: none;
  opacity: 0.9;
}

.globe-panel__stage {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: clamp(3.8rem, 6vw, 4.8rem) clamp(1rem, 3vw, 2rem) clamp(7rem, 11vw, 8.5rem);
}

.globe-panel__globe {
  width: min(78vw, 63rem);
  max-width: 100%;
  transform: translateY(-0.5rem);
}

.globe-panel__overlay {
  position: absolute;
  z-index: 1;
}

.globe-panel__overlay--intro {
  top: 1.25rem;
  left: 1.25rem;
  width: min(16rem, 28vw);
}

.globe-panel__overlay--countdown {
  top: 1.25rem;
  right: 1.25rem;
  width: min(15rem, 24vw);
}

.globe-panel__intro-slab {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.globe-panel__overlay--health {
  left: 1.25rem;
  top: 52%;
  width: min(18rem, 28vw);
  z-index: 2;
}

.globe-panel__overlay--stats {
  left: 50%;
  right: auto;
  bottom: 1.2rem;
  width: min(42rem, calc(100% - 2.4rem));
  transform: translateX(-50%);
}

@media (max-width: 1100px) {
  .globe-panel__hero {
    min-height: clamp(44rem, 110vw, 58rem);
  }

  .globe-panel__stage {
    padding: clamp(3.8rem, 8vw, 4.8rem) 0.85rem clamp(5rem, 10vw, 7rem);
  }

  .globe-panel__overlay--intro {
    top: 1rem;
    left: 1rem;
    width: min(14rem, calc(100% - 5.4rem));
  }

  .globe-panel__overlay--countdown {
    top: auto;
    right: 0.9rem;
    bottom: 5.5rem;
    transform: none;
    width: min(13.6rem, 22vw);
  }

  .globe-panel__overlay--stats {
    bottom: 0.9rem;
    width: min(38rem, calc(100% - 1.8rem));
  }

  .globe-panel__globe {
    width: min(100%, 50rem);
    transform: translateY(-0.5rem);
  }
}

@media (max-width: 720px) {
  .globe-panel__hero {
    border-radius: 1.45rem;
    min-height: clamp(44rem, 180vw, 56rem);
  }

  .globe-panel__header {
    gap: 0.28rem;
  }

  .globe-panel__title {
    font-size: 0.82rem;
    letter-spacing: 0.16em;
  }

  .globe-panel__status {
    padding-top: 0.36rem;
    font-size: 0.6rem;
    letter-spacing: 0.09em;
  }

  .globe-panel__stage {
    padding: 4.5rem 0.4rem 5.5rem;
  }

  .globe-panel__globe {
    width: min(110vw, 32.5rem);
    margin-left: -6vw;
    transform: translateY(-0.5rem);
  }

  .globe-panel__overlay--intro {
    top: 0.75rem;
    left: 0.75rem;
    width: min(13rem, calc(100% - 5.5rem));
  }

  .globe-panel__overlay--countdown {
    top: 0.75rem;
    right: 0.75rem;
    bottom: auto;
    transform: none;
    width: min(13rem, 40vw);
  }

  .globe-panel__overlay--stats {
    left: 50%;
    right: auto;
    bottom: 0.75rem;
    width: min(31rem, calc(100% - 1.5rem));
    transform: translateX(-50%);
  }
}

@media (max-width: 600px) {
  .globe-panel__overlay--intro {
    top: 0.75rem;
    left: 0.75rem;
    right: 0.75rem;
    width: auto;
  }

  .globe-panel__stage {
    padding-top: 5.5rem;
  }
}
</style>
