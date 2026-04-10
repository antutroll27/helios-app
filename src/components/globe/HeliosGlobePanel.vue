<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import GlobeComparisonHud from './GlobeComparisonHud.vue'
import GlobeOrbitalContext from './GlobeOrbitalContext.vue'
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

// ── Mobile rail toggle ────────────────────────────────────────────────────
const showRail = ref(false)
const isMobile = ref(false)

const handleResize = () => {
  isMobile.value = window.innerWidth <= 600
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

function toggleRail() {
  showRail.value = !showRail.value
}

function onDestinationSelect(id: string) {
  selectDestination(id)
  showRail.value = false
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

          <div class="globe-panel__intro-rule" aria-hidden="true" />

          <GlobeOrbitalContext
            :context="orbitalContext"
            :current="currentSnapshot"
            :solar="localSolar"
          />
        </section>
      </div>

      <div class="globe-panel__stage">
        <HeliosCobeGlobe
          class="globe-panel__globe"
          :current="currentSnapshot"
          :comparisons="comparisons"
          :selected-destination-id="selectedDestinationId"
        />
      </div>

      <div class="globe-panel__overlay globe-panel__overlay--rail">
        <GlobeComparisonHud
          v-show="!isMobile || showRail"
          :comparisons="comparisons"
          :selected-destination-id="selectedDestinationId"
          @select-destination="onDestinationSelect"
        />
      </div>

      <!-- Mobile-only destination pill toggle -->
      <button
        v-if="isMobile"
        class="globe-panel__dest-pill font-mono"
        type="button"
        @click="toggleRail"
      >
        <span v-if="selectedComparison" class="globe-panel__dest-pill-dot" />
        {{ selectedComparison?.label ?? 'DEST' }} ↗
      </button>

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
  min-height: clamp(34rem, 72vh, 52rem);
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
  padding: clamp(3.8rem, 6vw, 4.8rem) clamp(1rem, 3vw, 2rem) clamp(9.6rem, 14vw, 11rem);
}

.globe-panel__globe {
  width: min(78vw, 63rem);
  max-width: 100%;
  transform: translateY(-2.3rem);
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

.globe-panel__intro-slab {
  display: grid;
  gap: 0.65rem;
  padding: 0.85rem 0.85rem 0.9rem;
  border-radius: 1.2rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background:
    linear-gradient(180deg, rgba(7, 14, 27, 0.92), rgba(7, 14, 27, 0.72)),
    radial-gradient(circle at top left, rgba(99, 228, 255, 0.08), transparent 42%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 22px 46px rgba(2, 8, 20, 0.26);
  backdrop-filter: blur(18px);
}

.globe-panel__intro-rule {
  height: 1px;
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.28), transparent);
}

.globe-panel__overlay--rail {
  top: 50%;
  right: 1.25rem;
  transform: translateY(-52%);
  max-width: min(15rem, 24vw);
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
    min-height: clamp(34rem, 92vw, 48rem);
  }

  .globe-panel__stage {
    padding: clamp(3.8rem, 8vw, 4.8rem) 0.85rem clamp(9rem, 17vw, 10.4rem);
  }

  .globe-panel__overlay--intro {
    top: 1rem;
    left: 1rem;
    width: min(14rem, calc(100% - 5.4rem));
  }

  .globe-panel__overlay--rail {
    top: auto;
    right: 0.9rem;
    bottom: 6rem;
    transform: none;
    max-width: min(13.6rem, calc(100% - 1.8rem));
  }

  .globe-panel__overlay--stats {
    bottom: 0.9rem;
    width: min(38rem, calc(100% - 1.8rem));
  }

  .globe-panel__globe {
    width: min(100%, 50rem);
    transform: translateY(-1.9rem);
  }
}

@media (max-width: 720px) {
  .globe-panel__hero {
    border-radius: 1.45rem;
    min-height: clamp(34rem, 150vw, 43rem);
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

  .globe-panel__intro-slab {
    gap: 0.82rem;
    padding: 0.92rem 0.92rem 0.98rem;
    border-radius: 1.08rem;
  }

  .globe-panel__stage {
    padding: 4.5rem 0.4rem 8.9rem;
  }

  .globe-panel__globe {
    width: min(110vw, 32.5rem);
    margin-left: -6vw;
    transform: translateY(-1.15rem);
  }

  .globe-panel__overlay--intro {
    top: 0.75rem;
    left: 0.75rem;
    width: min(13rem, calc(100% - 5.5rem));
  }

  .globe-panel__overlay--rail {
    top: 4.7rem;
    right: 0.75rem;
    bottom: auto;
    left: auto;
    max-width: min(13rem, calc(100% - 5rem));
  }

  .globe-panel__overlay--stats {
    left: 50%;
    right: auto;
    bottom: 0.75rem;
    width: min(31rem, calc(100% - 1.5rem));
    transform: translateX(-50%);
  }
}

/* ── Mobile (≤ 600px) ───────────────────────────────────────────────────── */

@media (max-width: 600px) {
  /* Orbital context card — full width strip */
  .globe-panel__overlay--intro {
    top: 0.75rem;
    left: 0.75rem;
    right: 0.75rem;
    width: auto;
  }

  /* Comparison HUD — repositioned above pill when open */
  .globe-panel__overlay--rail {
    top: auto;
    bottom: 6rem;
    right: 0.75rem;
    left: auto;
    transform: none;
    max-width: min(14rem, calc(100% - 1.5rem));
    z-index: 2;
  }

  /* Globe stage — extra top padding to clear full-width intro card */
  .globe-panel__stage {
    padding-top: 5.5rem;
  }

  /* Destination pill — mobile-only floating toggle */
  .globe-panel__dest-pill {
    position: absolute;
    z-index: 3;
    bottom: 4.25rem;
    right: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.32rem 0.6rem;
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 999px;
    background: rgba(7, 14, 27, 0.82);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    color: rgba(241, 245, 249, 0.9);
    font-size: 0.55rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    cursor: pointer;
    appearance: none;
  }

  .globe-panel__dest-pill-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: rgba(255, 189, 118, 0.9);
    flex-shrink: 0;
  }
}

/* Pill is mobile-only — explicitly hidden on desktop */
@media (min-width: 601px) {
  .globe-panel__dest-pill {
    display: none;
  }
}
</style>
