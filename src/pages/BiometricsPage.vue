<script setup lang="ts">
import { onMounted } from 'vue'
import { useBiometricsStore } from '@/stores/biometrics'
import BiometricsHeader from '@/components/biometrics/BiometricsHeader.vue'
import HRVHeroCell from '@/components/biometrics/HRVHeroCell.vue'
import SleepScoreHeroCell from '@/components/biometrics/SleepScoreHeroCell.vue'
import MetricSummaryTile from '@/components/biometrics/MetricSummaryTile.vue'
import HRVTrendChart from '@/components/biometrics/HRVTrendChart.vue'
import SleepArchitectureChart from '@/components/biometrics/SleepArchitectureChart.vue'
import SkinTempChart from '@/components/biometrics/SkinTempChart.vue'
import ProtocolAdherenceTimeline from '@/components/biometrics/ProtocolAdherenceTimeline.vue'
import CircadianInsightsPanel from '@/components/biometrics/CircadianInsightsPanel.vue'
import WearableUploadZone from '@/components/biometrics/WearableUploadZone.vue'
import BiometricsEmptyState from '@/components/biometrics/BiometricsEmptyState.vue'
import ProtocolIntelligenceSection from '@/components/biometrics/ProtocolIntelligenceSection.vue'

const biometrics = useBiometricsStore()
onMounted(() => biometrics.loadMockData())
function triggerFileInput() { document.getElementById('wearable-file-input')?.click() }
</script>

<template>
  <div class="bio-page">
    <div class="bio-container">
      <BiometricsHeader @upload-click="triggerFileInput" />

      <template v-if="biometrics.logs.length > 0">
        <div class="bento mt-4">
          <HRVHeroCell class="bento__hrv-hero" />
          <SleepScoreHeroCell class="bento__sleep-hero" />

          <MetricSummaryTile
            class="bento__resting"
            label="RESTING HR"
            :value="biometrics.avgRestingHR != null ? String(biometrics.avgRestingHR) : '—'"
            unit="bpm"
            accent="#FFBD76"
          />
          <MetricSummaryTile
            class="bento__total-sleep"
            label="TOTAL SLEEP"
            :value="biometrics.avgTotalSleepH != null ? String(biometrics.avgTotalSleepH) : '—'"
            unit="hrs"
            accent="#38BDF8"
          />

          <div class="bento__trend bento-card">
            <HRVTrendChart />
          </div>

          <div class="bento__arch bento-card">
            <SleepArchitectureChart />
          </div>

          <div class="bento__protocol bento-card">
            <ProtocolAdherenceTimeline />
          </div>

          <div class="bento__skin bento-card">
            <SkinTempChart />
          </div>

          <div class="bento__insights bento-card">
            <CircadianInsightsPanel />
          </div>

          <WearableUploadZone class="bento__upload" />
        </div>
        <ProtocolIntelligenceSection />
      </template>

      <BiometricsEmptyState v-else class="mt-4" @upload-click="triggerFileInput" />
    </div>
  </div>
</template>

<style scoped>
.bio-page {
  min-height: 100vh;
  background: var(--bg-primary);
  padding-top: 3.5rem;
}
.bio-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 1.5rem 1.5rem 3rem;
}
.bento {
  display: grid;
  grid-template-columns: 1fr 1fr 0.65fr;
  grid-template-rows: auto auto auto 260px auto;
  grid-template-areas:
    "hrv-hero  sleep-hero  resting"
    "hrv-hero  sleep-hero  total-sleep"
    "trend     trend       trend"
    "arch      protocol    protocol"
    "skin      insights    upload";
  gap: 0.75rem;
}
.bento__hrv-hero    { grid-area: hrv-hero; }
.bento__sleep-hero  { grid-area: sleep-hero; }
.bento__resting     { grid-area: resting; }
.bento__total-sleep { grid-area: total-sleep; }
.bento__trend       { grid-area: trend; }
.bento__arch        { grid-area: arch; }
.bento__protocol    { grid-area: protocol; }
.bento__skin        { grid-area: skin; }
.bento__insights    { grid-area: insights; }
.bento__upload      { grid-area: upload; }

@media (max-width: 640px) {
  .bento {
    grid-template-columns: 1fr 1fr;
    grid-template-areas:
      "hrv-hero    sleep-hero"
      "resting     total-sleep"
      "trend       trend"
      "arch        skin"
      "protocol    protocol"
      "insights    insights"
      "upload      upload";
  }
}
</style>
