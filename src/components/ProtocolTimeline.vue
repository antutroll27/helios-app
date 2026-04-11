<script setup lang="ts">
import { computed } from 'vue'
import { useProtocolStore } from '@/stores/protocol'
import { useSolarStore } from '@/stores/solar'
import type { ProtocolItem } from '@/stores/protocol'
import ProtocolCard from './ProtocolCard.vue'

const protocol = useProtocolStore()
const solar = useSolarStore()

const protocolItems = computed<ProtocolItem[]>(() => {
  const p = protocol.dailyProtocol
  return [
    p.wakeWindow,
    p.morningLight,
    p.peakFocus,
    p.caffeineCutoff,
    p.windDown,
    p.sleepWindow
  ]
})

function getStatus(time: Date, endTime?: Date): 'upcoming' | 'active' | 'passed' {
  const now = solar.now.getTime()
  const t = time.getTime()
  if (endTime) {
    const e = endTime.getTime()
    if (now > e) return 'passed'
    if (now >= t) return 'active'
    return 'upcoming'
  }
  // moment-based fallback: 60-min lookahead
  if (t < now) return 'passed'
  if ((t - now) / 60_000 <= 60) return 'active'
  return 'upcoming'
}
</script>

<template>
  <div>
    <!-- Section header — editorial style -->
    <div class="timeline-header">
      <div class="timeline-header-top">
        <span class="font-mono" style="font-size: 0.55rem; color: var(--text-muted); letter-spacing: 0.1em;">SECTION / 01</span>
        <span class="font-mono" style="font-size: 0.55rem; color: var(--text-muted);">6 ITEMS</span>
      </div>
      <h2 class="timeline-title font-display">YOUR PROTOCOL</h2>
      <p class="timeline-subtitle font-mono">Based on live solar position + NOAA space weather data</p>
      <div class="timeline-rule" />
    </div>

    <!-- 3-column grid -->
    <div class="protocol-grid stagger-children">
      <ProtocolCard
        v-for="item in protocolItems"
        :key="item.key"
        :title="item.title"
        :time="item.time"
        :end-time="item.endTime"
        :icon="item.icon"
        :citation="item.citation"
        :subtitle="item.subtitle"
        :status="getStatus(item.time, item.endTime)"
        :viz-data="item.vizData"
      />
    </div>
  </div>
</template>

<style scoped>
.timeline-header {
  margin-bottom: 1.5rem;
}

.timeline-header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.35rem;
}

.timeline-title {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-primary);
  margin-bottom: 0.2rem;
}

.timeline-subtitle {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.timeline-rule {
  height: 1px;
  background: linear-gradient(to right, var(--text-muted), transparent);
  opacity: 0.3;
}

.protocol-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

@media (max-width: 900px) {
  .protocol-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 500px) {
  .protocol-grid {
    grid-template-columns: 1fr;
  }
}
</style>
