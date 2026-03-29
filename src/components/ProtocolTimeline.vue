<script setup lang="ts">
import { computed } from 'vue'
import { useProtocolStore } from '@/stores/protocol'
import type { ProtocolItem } from '@/stores/protocol'
import ProtocolCard from './ProtocolCard.vue'

const protocol = useProtocolStore()

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

function getStatus(time: Date): 'upcoming' | 'active' | 'passed' {
  const now = Date.now()
  const t = time.getTime()
  const diffMs = t - now
  const diffMin = diffMs / 60_000

  if (diffMs < 0) return 'passed'
  if (diffMin <= 60) return 'active'
  return 'upcoming'
}
</script>

<template>
  <div>
    <!-- Section header — editorial style -->
    <div class="mb-5">
      <div class="flex justify-between items-center mb-[0.35rem]">
        <span class="font-mono text-[0.55rem] text-(--text-muted) tracking-widest">SECTION / 01</span>
        <span class="font-mono text-[0.55rem] text-(--text-muted)">6 ITEMS</span>
      </div>
      <h2 class="font-display text-2xl font-extrabold tracking-[0.08em] uppercase text-(--text-primary) mb-[0.2rem]">YOUR PROTOCOL</h2>
      <p class="font-mono text-[0.7rem] text-(--text-muted) mb-3">Based on live solar position + NOAA space weather data</p>
      <div class="h-px bg-linear-to-r from-(--text-muted) to-transparent opacity-30" />
    </div>

    <!-- 3-column grid -->
    <div class="grid grid-cols-3 gap-2.5 max-[900px]:grid-cols-2 max-[500px]:grid-cols-1 stagger-children">
      <ProtocolCard
        v-for="item in protocolItems"
        :key="item.key"
        :title="item.title"
        :time="item.time"
        :icon="item.icon"
        :citation="item.citation"
        :subtitle="item.subtitle"
        :status="getStatus(item.time)"
      />
    </div>
  </div>
</template>
