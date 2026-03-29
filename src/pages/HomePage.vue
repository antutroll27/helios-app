<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { Watch, Activity, Smartphone } from 'lucide-vue-next'
import HeliosGlobe from '@/components/HeliosGlobe.vue'
import SpaceWeatherGauge from '@/components/SpaceWeatherGauge.vue'
import SocialJetLagScore from '@/components/SocialJetLagScore.vue'
import EnvironmentBadge from '@/components/EnvironmentBadge.vue'
import ProtocolTimeline from '@/components/ProtocolTimeline.vue'
import ChatInterface from '@/components/ChatInterface.vue'
import OnboardingModal from '@/components/OnboardingModal.vue'

const user = useUserStore()

const wearables = [
  { name: 'Garmin', icon: Watch, color: '#00B4D8' },
  { name: 'Fitbit / Google', icon: Activity, color: '#00D4AA' },
  { name: 'Samsung Health', icon: Smartphone, color: '#A78BFA' },
  { name: 'Oura Ring', icon: Watch, color: '#FFBD76' },
  { name: 'BCI — Brain-Computer Interface', icon: Activity, color: '#FF6B6B' },
]
</script>

<template>
  <div class="min-h-screen relative">
    <!-- Onboarding -->
    <OnboardingModal v-if="!user.hasCompletedOnboarding" />

    <!-- Globe Section — full bleed -->
    <section class="relative w-full h-[60vh] min-h-[400px] overflow-hidden pt-14">
      <HeliosGlobe />
      <div class="absolute bottom-0 left-0 right-0 h-[100px] bg-linear-to-b from-transparent to-(--bg-primary) pointer-events-none z-2" />
    </section>

    <!-- Everything below globe is centered with max-width -->
    <div class="max-w-[960px] mx-auto px-6 max-[640px]:px-4">

      <!-- Live Data — 3-card grid -->
      <section class="-mt-2">
        <div class="grid grid-cols-3 gap-2.5 max-[640px]:grid-cols-1">
          <div class="bg-(--bg-card) border border-(--border-subtle) rounded-md p-5">
            <SpaceWeatherGauge />
          </div>
          <div class="bg-(--bg-card) border border-(--border-subtle) rounded-md p-5">
            <SocialJetLagScore />
          </div>
          <div class="bg-(--bg-card) border border-(--border-subtle) rounded-md p-5">
            <EnvironmentBadge />
          </div>
        </div>
      </section>

      <!-- Protocol Timeline -->
      <section class="pt-8">
        <ProtocolTimeline />
      </section>

      <!-- Wearable Integrations -->
      <section class="pt-8">
        <div class="flex justify-between items-center mb-[0.35rem]">
          <span class="font-mono text-[0.55rem] text-(--text-muted) tracking-widest">SECTION / 02</span>
          <span class="font-mono text-[0.55rem] text-(--text-muted)">5 DEVICES</span>
        </div>
        <h2 class="font-display text-2xl font-extrabold tracking-[0.08em] uppercase text-(--text-primary) mb-[0.2rem]">WEARABLE INTEGRATIONS</h2>
        <p class="font-mono text-[0.7rem] text-(--text-muted) mb-3">Close the feedback loop — measure your biology, not just predict it</p>
        <div class="h-px bg-linear-to-r from-(--text-muted) to-transparent opacity-20 mb-4" />

        <div class="grid grid-cols-4 gap-2 max-[640px]:grid-cols-2 stagger-children">
          <div
            v-for="w in wearables"
            :key="w.name"
            class="flex flex-col items-center gap-2 py-4 px-2 text-center bg-(--bg-card) border border-(--border-subtle) rounded-md transition-[border-color] duration-200 hover:border-(--border-card)"
          >
            <component :is="w.icon" :size="18" :color="w.color" :stroke-width="1.5" />
            <span class="font-display text-[0.75rem] font-semibold text-(--text-primary)">
              {{ w.name }}
            </span>
            <span
              class="font-mono text-[0.5rem] tracking-widest py-[0.15rem] px-1.5 rounded-[3px]"
              :style="{
                background: `${w.color}12`,
                color: w.color,
                border: `1px solid ${w.color}25`,
              }"
            >COMING SOON</span>
          </div>
        </div>

        <p class="font-mono text-[0.6rem] text-(--text-muted) mt-3 text-center opacity-60">
          HRV · Deep Sleep · REM · Skin Temperature · Resting Heart Rate
        </p>
      </section>

      <!-- Attribution -->
      <div class="pt-8 pb-2">
        <p class="font-mono text-[0.6rem] text-(--text-muted) text-center">
          Powered by NASA APIs · NOAA SWPC · Open-Meteo
        </p>
        <p class="font-mono text-[0.5rem] text-(--text-muted) text-center mt-[0.2rem] opacity-50">
          Data provided by NASA. Not affiliated with or endorsed by NASA.
        </p>
      </div>

      <!-- Chat Interface -->
      <section class="py-4 pb-6">
        <ChatInterface />
      </section>
    </div>
  </div>
</template>
