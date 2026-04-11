<script setup lang="ts">
import { computed } from 'vue'
import type { GlobeComparison } from '@/composables/useCobeGlobeData'
import { useProtocolStore } from '@/stores/protocol'
import { useSolarStore } from '@/stores/solar'

interface Props {
  selectedComparison?: GlobeComparison | null
  comparisons: GlobeComparison[]
}

const props = defineProps<Props>()
const emit = defineEmits<{ 'select-destination': [id: string | null] }>()

const protocol = useProtocolStore()
const solar = useSolarStore()

// Convert DailyProtocol keyed object to sorted array — .find()/.filter() require an array
const protocolItems = computed(() =>
  Object.values(protocol.dailyProtocol).sort((a, b) => a.time.getTime() - b.time.getTime())
)

// First upcoming protocol event
const nextEvent = computed(() => {
  const now = solar.now.getTime()
  return protocolItems.value.find(item => item.time.getTime() > now) ?? null
})

// Next 2 events after nextEvent (shown in queue)
const eventQueue = computed(() => {
  if (!nextEvent.value) return []
  const now = solar.now.getTime()
  return protocolItems.value
    .filter(item => item.time.getTime() > now && item !== nextEvent.value)
    .slice(0, 2)
})

// Minutes until next event, floored, minimum 0
const countdownMinutes = computed(() => {
  if (!nextEvent.value) return 0
  return Math.max(0, Math.floor((nextEvent.value.time.getTime() - solar.now.getTime()) / 60000))
})

// Split into value + unit for mixed-weight typography
const countdownDisplay = computed(() => {
  const m = countdownMinutes.value
  if (m < 60) return { value: String(m), unit: 'min' }
  const h = Math.floor(m / 60)
  const rem = m % 60
  return { value: `${h}h`, unit: rem > 0 ? `${rem}m` : '' }
})

// Percentage of current inter-event window elapsed, drives bar fill
const progressPct = computed(() => {
  if (!nextEvent.value) return 100
  const now = solar.now.getTime()
  const allTimes = protocolItems.value.map(i => i.time.getTime()).sort((a, b) => a - b)
  const nextT = nextEvent.value.time.getTime()
  const prevTimes = allTimes.filter(t => t <= now)
  const prevT = prevTimes.length > 0 ? prevTimes[prevTimes.length - 1] : allTimes[0]
  const window = nextT - prevT
  if (window <= 0) return 0
  return Math.min(100, Math.round(((now - prevT) / window) * 100))
})

// Hours elapsed since wake — drives nap window logic
const hoursAwake = computed(() => {
  const wakeMs = protocol.wakeWindowTime.getTime()
  const nowMs = solar.now.getTime()
  return Math.max(0, (nowMs - wakeMs) / 3600000)
})

// Nap window: 6–9 h after wake AND between 12:00–15:00 local time
const napWindowOpen = computed(() => {
  const h = solar.now.getHours()
  return hoursAwake.value >= 6 && hoursAwake.value <= 9 && h >= 12 && h < 15
})

// Format timezone delta with sign (e.g. "+5.5h" or "-3h")
const tzDeltaLabel = computed(() => {
  const delta = props.selectedComparison?.timezoneDeltaHours ?? 0
  const sign = delta >= 0 ? '+' : ''
  return `${sign}${delta}h`
})

// Queue item countdown label (hours+minutes until that event)
function queueMinLabel(item: { time: Date }): string {
  const m = Math.max(0, Math.floor((item.time.getTime() - solar.now.getTime()) / 60000))
  if (m < 60) return `${m}m`
  const h = Math.floor(m / 60)
  const rem = m % 60
  return rem > 0 ? `${h}h ${rem}m` : `${h}h`
}

// Derive solar phase from elevation — GlobeComparison has no destinationSolarPhase field
const destSolarPhase = computed(() => {
  const deg = props.selectedComparison?.destinationElevationDeg ?? 0
  if (deg > 20) return 'Day — High Sun'
  if (deg > 6) return 'Day — Low Angle'
  if (deg > 0) return 'Civil Twilight'
  return 'Night'
})
</script>

<template>
  <div class="pcd-card">

    <!-- ── COMPARISON MODE ──────────────────────────────────────── -->
    <template v-if="props.selectedComparison">
      <div class="pcd-row pcd-row--space">
        <span class="pcd-chip">DESTINATION</span>
        <span class="pcd-active-pill">● ACTIVE</span>
      </div>

      <div class="pcd-city-row">
        <span class="pcd-city-name">{{ props.selectedComparison.label }}</span>
        <span class="pcd-tz-delta">{{ tzDeltaLabel }}</span>
      </div>

      <div class="pcd-hairline" />

      <p class="pcd-solar-phase">{{ destSolarPhase }}</p>
      <p class="pcd-travel-readiness">{{ props.selectedComparison.travelReadiness }}</p>

      <button
        class="pcd-dismiss"
        type="button"
        aria-label="Return to countdown"
        @click="emit('select-destination', null)"
      >✕</button>
    </template>

    <!-- ── COUNTDOWN MODE (default) ────────────────────────────── -->
    <template v-else>
      <div class="pcd-row pcd-row--space">
        <span class="pcd-chip">NEXT EVENT</span>
        <span class="pcd-live">
          <span class="pcd-live-dot" aria-hidden="true" />
          LIVE
        </span>
      </div>

      <template v-if="nextEvent">
        <p class="pcd-coming-up">Coming up</p>
        <p class="pcd-event-name">{{ nextEvent.title }}</p>

        <div class="pcd-hero">
          <span class="cd-num">{{ countdownDisplay.value }}</span>
          <span class="cd-unit">{{ countdownDisplay.unit }}</span>
        </div>

        <!-- Progress bar -->
        <div class="pcd-bar-track">
          <div class="pcd-bar-fill" :style="{ width: progressPct + '%' }" />
        </div>
      </template>
      <p v-else class="pcd-event-name">All events passed</p>

      <div class="pcd-hairline" />

      <!-- Event queue -->
      <div v-if="eventQueue.length" class="pcd-queue">
        <div v-for="item in eventQueue" :key="item.key" class="pcd-queue-row">
          <span class="pcd-queue-name">{{ item.title }}</span>
          <span class="pcd-queue-time">{{ queueMinLabel(item) }}</span>
        </div>
      </div>

      <!-- Nap badge (conditional) -->
      <div v-if="napWindowOpen" class="pcd-nap-badge">
        <span class="pcd-nap-dot" aria-hidden="true" />
        Nap Window Open · 20 min
      </div>

      <div class="pcd-hairline" />

      <!-- Destination chips -->
      <div class="pcd-chips">
        <button
          v-for="comp in props.comparisons"
          :key="comp.id"
          class="pcd-dest-chip"
          type="button"
          @click="emit('select-destination', comp.id)"
        >
          {{ comp.label }}
        </button>
      </div>
    </template>

  </div>
</template>

<style scoped>
/* Card shell */
.pcd-card {
  position: relative;
  background: color-mix(in srgb, #9B8BFA 18%, #07111a);
  border-radius: 1rem;
  padding: 1rem 1rem 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Header row */
.pcd-row {
  display: flex;
  align-items: center;
  margin-bottom: 0.52rem;
}
.pcd-row--space {
  justify-content: space-between;
}

/* Label chip */
.pcd-chip {
  font-family: var(--font-mono);
  font-size: 0.46rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(200, 190, 250, 0.62);
}

/* Live indicator */
.pcd-live {
  display: flex;
  align-items: center;
  gap: 0.28rem;
  font-family: var(--font-mono);
  font-size: 0.42rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: #00D4AA;
}
.pcd-live-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #00D4AA;
  box-shadow: 0 0 5px #00D4AA;
  flex-shrink: 0;
}

/* Active pill (comparison mode) */
.pcd-active-pill {
  font-family: var(--font-mono);
  font-size: 0.4rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #00D4AA;
  background: rgba(0, 212, 170, 0.12);
  border: 1px solid rgba(0, 212, 170, 0.22);
  border-radius: 20px;
  padding: 0.18rem 0.4rem;
}

/* Sub-label above event name */
.pcd-coming-up {
  margin: 0 0 0.1rem;
  font-family: var(--font-mono);
  font-size: 0.42rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: rgba(200, 190, 250, 0.45);
  text-transform: uppercase;
}

/* Event name */
.pcd-event-name {
  margin: 0 0 0.3rem;
  font-size: 1.02rem;
  font-weight: 700;
  color: rgba(255, 245, 225, 0.95);
  line-height: 1.15;
}

/* Hero countdown */
.pcd-hero {
  display: flex;
  align-items: flex-end;
  gap: 0.22rem;
  margin-bottom: 0.48rem;
  line-height: 1;
}
.cd-num {
  font-family: var(--font-mono);
  font-size: 2.4rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: rgba(255, 245, 225, 0.97);
}
.cd-unit {
  font-family: var(--font-mono);
  font-size: 0.88rem;
  font-weight: 600;
  color: rgba(200, 190, 250, 0.55);
  padding-bottom: 0.2rem;
}

/* Progress bar */
.pcd-bar-track {
  height: 4px;
  border-radius: 2px;
  background: rgba(155, 139, 250, 0.1);
  margin-bottom: 0.58rem;
  overflow: hidden;
}
.pcd-bar-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, rgba(155, 139, 250, 0.4), #9B8BFA);
  transition: width 1.2s ease;
}

/* Hairline */
.pcd-hairline {
  height: 1px;
  background: rgba(155, 139, 250, 0.12);
  margin-bottom: 0.52rem;
}

/* Event queue */
.pcd-queue {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.48rem;
}
.pcd-queue-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.pcd-queue-name {
  font-family: var(--font-mono);
  font-size: 0.55rem;
  font-weight: 600;
  color: rgba(255, 245, 225, 0.68);
}
.pcd-queue-time {
  font-family: var(--font-mono);
  font-size: 0.52rem;
  font-weight: 600;
  color: rgba(200, 190, 250, 0.48);
}

/* Nap badge */
.pcd-nap-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
  background: rgba(0, 212, 170, 0.1);
  border: 1px solid rgba(0, 212, 170, 0.22);
  color: #00D4AA;
  font-family: var(--font-mono);
  font-size: 0.42rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  border-radius: 20px;
  padding: 0.2rem 0.46rem;
  margin-bottom: 0.48rem;
  align-self: flex-start;
}
.pcd-nap-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #00D4AA;
  flex-shrink: 0;
}

/* Destination chips */
.pcd-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}
.pcd-dest-chip {
  font-family: var(--font-mono);
  font-size: 0.38rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 0.16rem 0.38rem;
  border-radius: 20px;
  background: rgba(155, 139, 250, 0.1);
  border: 1px solid rgba(155, 139, 250, 0.18);
  color: rgba(200, 190, 250, 0.65);
  cursor: pointer;
  appearance: none;
  transition: background 0.15s, border-color 0.15s;
}
.pcd-dest-chip:hover {
  background: rgba(155, 139, 250, 0.18);
  border-color: rgba(155, 139, 250, 0.32);
}

/* ── Comparison mode ──────────────────────────────────────────── */
.pcd-city-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.42rem;
}
.pcd-city-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: rgba(255, 245, 225, 0.95);
}
.pcd-tz-delta {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 700;
  color: #FFBD76;
}
.pcd-solar-phase {
  margin: 0 0 0.2rem;
  font-family: var(--font-mono);
  font-size: 0.52rem;
  font-weight: 600;
  color: rgba(200, 190, 250, 0.72);
  letter-spacing: 0.06em;
}
.pcd-travel-readiness {
  margin: 0;
  font-size: 0.46rem;
  color: rgba(200, 190, 250, 0.5);
  line-height: 1.4;
  font-family: var(--font-mono);
}
.pcd-dismiss {
  position: absolute;
  top: 0.6rem;
  right: 0.7rem;
  font-size: 0.65rem;
  color: rgba(200, 190, 250, 0.4);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.1rem 0.2rem;
  line-height: 1;
  appearance: none;
}
.pcd-dismiss:hover {
  color: rgba(200, 190, 250, 0.75);
}
</style>
