<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useGeoStore } from '@/stores/geo'
import { PROVIDERS } from '@/composables/useAI'
import {
  ArrowLeft,
  Sunrise,
  Sun,
  Moon,
  Eye,
  EyeOff,
  RefreshCw,
  MapPin,
  Bot,
  BedDouble,
  Info,
} from 'lucide-vue-next'

const router = useRouter()
const user = useUserStore()
const geo = useGeoStore()

// ── Local state mirroring store ──────────────────────
const selectedProvider = ref(user.provider)
const apiKeyInput = ref(user.apiKey)
const showApiKey = ref(false)
const sleepTime = ref(user.usualSleepTime)
const selectedChronotype = ref(user.chronotype)
const isRefreshingLocation = ref(false)

const providerDescriptions: Record<string, string> = {
  openai: 'GPT-4o',
  claude: 'Claude Sonnet',
  kimi: 'Kimi 2.5',
  glm: 'GLM-4 Flash',
}

const chronotypes = [
  { id: 'early' as const, label: 'Early Bird', icon: Sunrise },
  { id: 'intermediate' as const, label: 'Intermediate', icon: Sun },
  { id: 'late' as const, label: 'Night Owl', icon: Moon },
]

const currentPlaceholder = computed(() => {
  const p = PROVIDERS.find((pr: { id: string; placeholder: string }) => pr.id === selectedProvider.value)
  return p ? p.placeholder : '...'
})

// ── Save handlers ────────────────────────────────────

function selectProvider(id: string) {
  selectedProvider.value = id as typeof user.provider
  user.setProvider(
    selectedProvider.value as 'openai' | 'claude' | 'kimi' | 'glm',
    apiKeyInput.value
  )
}

function saveApiKey() {
  user.setProvider(
    selectedProvider.value as 'openai' | 'claude' | 'kimi' | 'glm',
    apiKeyInput.value
  )
}

function saveSleepTime() {
  user.usualSleepTime = sleepTime.value
}

function selectChronotype(id: 'early' | 'intermediate' | 'late') {
  selectedChronotype.value = id
  user.chronotype = id
}

async function refreshLocation() {
  isRefreshingLocation.value = true
  await geo.requestLocation()
  isRefreshingLocation.value = false
}
</script>

<template>
  <div class="settings-page">
    <!-- Header -->
    <div class="settings-header">
      <button class="back-btn" @click="router.push('/')">
        <ArrowLeft :size="20" style="color: var(--text-primary)" />
      </button>
      <h1 class="font-display tracking-label settings-title">SETTINGS</h1>
      <div style="width: 36px;" />
    </div>

    <div class="settings-body stagger-children">

      <!-- ── AI Provider ──────────────────────────────── -->
      <section class="bento-card settings-section">
        <div class="section-header">
          <Bot :size="16" style="color: var(--text-muted)" />
          <span class="section-label font-display tracking-label">AI PROVIDER</span>
        </div>

        <div class="provider-row">
          <button
            v-for="p in PROVIDERS"
            :key="p.id"
            class="provider-btn"
            :class="{ 'provider-btn--active': selectedProvider === p.id }"
            @click="selectProvider(p.id)"
          >
            <span class="provider-btn-name font-display">{{ p.name }}</span>
            <span class="provider-btn-desc">{{ providerDescriptions[p.id] }}</span>
          </button>
        </div>

        <div class="api-key-row">
          <label class="field-label font-mono">API KEY</label>
          <div class="api-key-input-wrap">
            <input
              v-model="apiKeyInput"
              :type="showApiKey ? 'text' : 'password'"
              class="field-input font-mono"
              :placeholder="currentPlaceholder"
              autocomplete="off"
              @blur="saveApiKey"
              @keydown.enter="saveApiKey"
            />
            <button class="eye-btn" @click="showApiKey = !showApiKey">
              <component
                :is="showApiKey ? EyeOff : Eye"
                :size="16"
                style="color: var(--text-muted)"
              />
            </button>
          </div>
        </div>
      </section>

      <!-- ── Sleep Preferences ────────────────────────── -->
      <section class="bento-card settings-section">
        <div class="section-header">
          <BedDouble :size="16" style="color: var(--text-muted)" />
          <span class="section-label font-display tracking-label">SLEEP PREFERENCES</span>
        </div>

        <div class="sleep-row">
          <label class="field-label font-mono">USUAL SLEEP TIME</label>
          <input
            v-model="sleepTime"
            type="time"
            class="time-input font-mono"
            @change="saveSleepTime"
          />
        </div>

        <div class="chrono-row">
          <label class="field-label font-mono">CHRONOTYPE</label>
          <div class="chrono-btns">
            <button
              v-for="c in chronotypes"
              :key="c.id"
              class="chrono-btn"
              :class="{ 'chrono-btn--active': selectedChronotype === c.id }"
              @click="selectChronotype(c.id)"
            >
              <component :is="c.icon" :size="16" class="chrono-btn-icon" />
              <span>{{ c.label }}</span>
            </button>
          </div>
        </div>
      </section>

      <!-- ── Location ─────────────────────────────────── -->
      <section class="bento-card settings-section">
        <div class="section-header">
          <MapPin :size="16" style="color: var(--text-muted)" />
          <span class="section-label font-display tracking-label">LOCATION</span>
        </div>

        <div class="location-info">
          <div class="location-text">
            <span class="location-name">{{ geo.locationName }}</span>
            <span class="location-coords font-mono">
              {{ geo.lat.toFixed(4) }}, {{ geo.lng.toFixed(4) }}
            </span>
          </div>
          <button
            class="refresh-btn"
            :disabled="isRefreshingLocation"
            @click="refreshLocation"
          >
            <RefreshCw
              :size="14"
              :class="{ 'spin-anim': isRefreshingLocation }"
              style="color: var(--text-primary)"
            />
            <span>Refresh</span>
          </button>
        </div>

        <p v-if="geo.error" class="location-error">{{ geo.error }}</p>
      </section>

      <!-- ── About ────────────────────────────────────── -->
      <section class="bento-card settings-section about-section">
        <div class="section-header">
          <Info :size="16" style="color: var(--text-muted)" />
          <span class="section-label font-display tracking-label">ABOUT</span>
        </div>

        <div class="about-body">
          <p class="about-version font-display">HELIOS <span class="font-mono">v0.1.0</span></p>
          <p class="about-line">Built using NASA Open Data</p>
          <p class="about-line">Space weather data from NASA DONKI</p>
          <p class="about-line">Powered by NASA APIs &middot; NOAA SWPC &middot; Open-Meteo</p>
          <div class="about-disclaimer">
            <p>This application is not affiliated with, endorsed by, or sponsored by NASA. Data is sourced from NASA's publicly available APIs.</p>
          </div>
        </div>
      </section>

    </div>
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100vh;
  padding-top: 3.5rem; /* navbar */
}

/* ── Header ─────────────────────────────────────────── */

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1rem 0.5rem;
}

.back-btn {
  width: 36px;
  height: 36px;
  border-radius: 0.625rem;
  border: 1px solid var(--border-subtle);
  background: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.back-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--glass-border);
}

.settings-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
}

/* ── Body ───────────────────────────────────────────── */

.settings-body {
  padding: 0.75rem 1rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* ── Sections ───────────────────────────────────────── */

.settings-section {
  padding: 1.125rem;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.section-label {
  font-size: 0.58rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
}

/* ── Provider selector ──────────────────────────────── */

.provider-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.provider-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.15rem;
  padding: 0.625rem 0.75rem;
  border-radius: 0.625rem;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}
.provider-btn:hover {
  background: var(--bg-card-hover);
}
.provider-btn--active {
  border-color: #FFBD76;
  background: rgba(255, 189, 118, 0.06);
  box-shadow: 0 0 0 1px rgba(255, 189, 118, 0.15);
}

.provider-btn-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-primary);
}

.provider-btn-desc {
  font-size: 0.6rem;
  color: var(--text-muted);
  font-family: var(--font-body);
}

/* ── API key ────────────────────────────────────────── */

.api-key-row {
  margin-bottom: 0;
}

.field-label {
  display: block;
  font-size: 0.52rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.375rem;
}

.api-key-input-wrap {
  display: flex;
  align-items: center;
  gap: 0;
  border: 1px solid var(--border-subtle);
  border-radius: 0.625rem;
  overflow: hidden;
  background: var(--bg-primary);
  transition: border-color 0.2s;
}
.api-key-input-wrap:focus-within {
  border-color: #FFBD76;
  box-shadow: 0 0 0 2px rgba(255, 189, 118, 0.1);
}

.field-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 0.78rem;
}
.field-input::placeholder {
  color: var(--text-muted);
}

.eye-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem 0.75rem;
  display: flex;
  align-items: center;
  transition: opacity 0.2s;
}
.eye-btn:hover {
  opacity: 0.7;
}

/* ── Sleep ──────────────────────────────────────────── */

.sleep-row {
  margin-bottom: 1rem;
}

.time-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border-radius: 0.625rem;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
  outline: none;
  transition: border-color 0.2s;
  color-scheme: dark;
}
.time-input:focus {
  border-color: #FFBD76;
  box-shadow: 0 0 0 2px rgba(255, 189, 118, 0.1);
}

.chrono-row {
  margin-bottom: 0;
}

.chrono-btns {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.chrono-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.375rem;
  padding: 0.75rem 0.375rem;
  border-radius: 0.625rem;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  cursor: pointer;
  transition: all 0.2s;
  font-family: var(--font-body);
  font-size: 0.65rem;
  font-weight: 500;
  color: var(--text-secondary);
}
.chrono-btn:hover {
  background: var(--bg-card-hover);
}
.chrono-btn--active {
  border-color: #FFBD76;
  background: rgba(255, 189, 118, 0.06);
  color: var(--text-primary);
}

.chrono-btn-icon {
  color: var(--text-muted);
}
.chrono-btn--active .chrono-btn-icon {
  color: #FFBD76;
}

/* ── Location ───────────────────────────────────────── */

.location-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.location-text {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.location-name {
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.location-coords {
  font-size: 0.65rem;
  color: var(--text-muted);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 0.72rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.refresh-btn:hover:not(:disabled) {
  background: var(--bg-card-hover);
  border-color: var(--glass-border);
}
.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spin-anim {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.location-error {
  margin-top: 0.5rem;
  font-size: 0.7rem;
  color: #FF4444;
  font-family: var(--font-body);
}

/* ── About ──────────────────────────────────────────── */

.about-section {
  border: 1px solid var(--border-card);
}

.about-body {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.about-version {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.about-line {
  font-family: var(--font-body);
  font-size: 0.72rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.about-disclaimer {
  margin-top: 0.625rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: rgba(255, 68, 68, 0.04);
  border: 1px solid rgba(255, 68, 68, 0.1);
}

.about-disclaimer p {
  font-family: var(--font-body);
  font-size: 0.65rem;
  color: var(--text-muted);
  line-height: 1.6;
  font-style: italic;
}
</style>
