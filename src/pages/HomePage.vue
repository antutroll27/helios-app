<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import { Activity, Smartphone, Watch } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { useHomeDeferredSections } from '@/composables/useHomeDeferredSections'
import EnvironmentBadge from '@/components/EnvironmentBadge.vue'
import OnboardingModal from '@/components/OnboardingModal.vue'
import ProtocolTimeline from '@/components/ProtocolTimeline.vue'
import SocialJetLagScore from '@/components/SocialJetLagScore.vue'
import SpaceWeatherGauge from '@/components/SpaceWeatherGauge.vue'
import HomeChatPlaceholder from '@/components/home/HomeChatPlaceholder.vue'
import HomeGlobePlaceholder from '@/components/home/HomeGlobePlaceholder.vue'

const HeliosGlobePanel = defineAsyncComponent({
  loader: () => import('@/components/globe/HeliosGlobePanel.vue'),
  loadingComponent: HomeGlobePlaceholder,
  delay: 0,
})

const ChatInterface = defineAsyncComponent({
  loader: () => import('@/components/ChatInterface.vue'),
  loadingComponent: HomeChatPlaceholder,
  delay: 0,
})

const user = useUserStore()
const { chatSectionRef, showGlobe, showChat } = useHomeDeferredSections()

const wearables = [
  { name: 'Garmin', icon: Watch, color: '#00B4D8' },
  { name: 'Fitbit / Google', icon: Activity, color: '#00D4AA' },
  { name: 'Samsung Health', icon: Smartphone, color: '#A78BFA' },
  { name: 'Oura Ring', icon: Watch, color: '#FFBD76' },
  { name: 'BCI — Brain-Computer Interface', icon: Activity, color: '#FF6B6B' },
]
</script>

<template>
  <div class="home-page">
    <OnboardingModal v-if="!user.hasCompletedOnboarding" />

    <section class="globe-section">
      <HomeGlobePlaceholder v-if="!showGlobe" />
      <HeliosGlobePanel v-else />
      <div class="globe-fade" />
    </section>

    <div class="content-container">
      <section class="data-section">
        <div class="data-grid">
          <SpaceWeatherGauge />
          <SocialJetLagScore />
          <EnvironmentBadge />
        </div>
      </section>

      <section class="protocol-section">
        <ProtocolTimeline />
      </section>

      <section class="integrations-section">
        <div class="section-meta">
          <span class="font-mono" style="font-size: 0.55rem; color: var(--text-muted); letter-spacing: 0.1em;">SECTION / 02</span>
          <span class="font-mono" style="font-size: 0.55rem; color: var(--text-muted);">5 DEVICES</span>
        </div>
        <h2 class="font-display section-heading">WEARABLE INTEGRATIONS</h2>
        <p class="font-mono section-sub">Close the feedback loop — measure your biology, not just predict it</p>
        <div class="section-rule" />

        <div class="integrations-grid stagger-children">
          <div
            v-for="w in wearables"
            :key="w.name"
            class="integration-card"
          >
            <component :is="w.icon" :size="18" :color="w.color" :stroke-width="1.5" />
            <span class="font-display" style="font-size: 0.75rem; font-weight: 600; color: var(--text-primary);">
              {{ w.name }}
            </span>
            <span
              class="font-mono"
              :style="{
                fontSize: '0.5rem',
                letterSpacing: '0.1em',
                padding: '0.15rem 0.4rem',
                borderRadius: '3px',
                background: `${w.color}12`,
                color: w.color,
                border: `1px solid ${w.color}25`,
              }"
            >COMING SOON</span>
          </div>
        </div>

        <p class="font-mono" style="font-size: 0.6rem; color: var(--text-muted); margin-top: 0.75rem; text-align: center; opacity: 0.6;">
          HRV · Deep Sleep · REM · Skin Temperature · Resting Heart Rate
        </p>
      </section>

      <div class="attribution">
        <p class="font-mono" style="font-size: 0.6rem; color: var(--text-muted); text-align: center;">
          Powered by NASA APIs · NOAA SWPC · Open-Meteo
        </p>
        <p class="font-mono" style="font-size: 0.5rem; color: var(--text-muted); text-align: center; margin-top: 0.2rem; opacity: 0.5;">
          Data provided by NASA. Not affiliated with or endorsed by NASA.
        </p>
      </div>

      <section ref="chatSectionRef" class="chat-section">
        <HomeChatPlaceholder v-if="!showChat" />
        <ChatInterface v-else />
      </section>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  position: relative;
}

.globe-section {
  position: relative;
  width: 100%;
  height: 60vh;
  min-height: 400px;
  overflow: hidden;
  padding-top: 3.5rem;
}

.globe-fade {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 100px;
  background: linear-gradient(to bottom, transparent, var(--bg-primary));
  pointer-events: none;
  z-index: 2;
}

.content-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.data-section {
  margin-top: 0.5rem;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.85rem;
}

@media (max-width: 640px) {
  .data-grid {
    grid-template-columns: 1fr;
  }
}

.protocol-section {
  padding-top: 2.5rem;
}

.integrations-section {
  padding-top: 2.5rem;
}

.section-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.35rem;
}

.section-heading {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-primary);
  margin-bottom: 0.2rem;
}

.section-sub {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.section-rule {
  height: 1px;
  background: linear-gradient(to right, var(--text-muted), transparent);
  opacity: 0.2;
  margin-bottom: 1.25rem;
}

.integrations-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.6rem;
}

@media (max-width: 640px) {
  .integrations-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.integration-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 0.5rem;
  text-align: center;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  transition: border-color 0.2s;
}

.integration-card:hover {
  border-color: var(--border-card);
}

.attribution {
  padding: 2rem 0 0.5rem;
}

.chat-section {
  padding: 1rem 0 1.5rem;
}

@media (max-width: 640px) {
  .data-row {
    grid-template-columns: 1fr;
  }

  .content-container {
    padding: 0 1rem;
  }
}
</style>
