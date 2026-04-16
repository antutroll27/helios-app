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


const chronotypes = [
  { id: 'early' as const, label: 'Early Bird', icon: Sunrise },
  { id: 'intermediate' as const, label: 'Intermediate', icon: Sun },
  { id: 'late' as const, label: 'Night Owl', icon: Moon },
]

const apiKeyNote = 'Optional. Stored in memory only for this session.'

const currentPlaceholder = computed(() => {
  const p = PROVIDERS.find((pr: { id: string; placeholder: string }) => pr.id === selectedProvider.value)
  return p ? p.placeholder : '...'
})

// ── Save handlers ────────────────────────────────────

function selectProvider(id: string) {
  selectedProvider.value = id as typeof user.provider
  user.setProvider(
    selectedProvider.value as 'openai' | 'claude' | 'gemini' | 'grok' | 'perplexity' | 'kimi' | 'glm',
    apiKeyInput.value.trim() || undefined
  )
}

function saveApiKey() {
  user.setProvider(
    selectedProvider.value as 'openai' | 'claude' | 'gemini' | 'grok' | 'perplexity' | 'kimi' | 'glm',
    apiKeyInput.value.trim()
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

    <!-- ── Header ─────────────────────────────────── -->
    <div class="settings-header">
      <button class="back-btn" @click="router.push('/')">
        <ArrowLeft :size="16" />
      </button>
      <div class="header-center">
        <span class="header-eyebrow font-mono">HELIOS</span>
        <h1 class="header-title font-mono">SETTINGS</h1>
      </div>
      <div style="width: 36px;" />
    </div>

    <div class="settings-body">

      <!-- ── AI Provider ──────────────────────────── -->
      <section class="settings-card">
        <div class="card-header">
          <div class="card-header-left">
            <Bot :size="13" class="card-icon" />
            <span class="card-label font-mono">AI ENGINE</span>
          </div>
          <div class="card-rule" />
          <span class="card-tag font-mono">SELECT</span>
        </div>

        <div class="provider-grid">
          <button
            v-for="(p, i) in PROVIDERS"
            :key="p.id"
            class="provider-btn"
            :class="{ 'provider-btn--active': selectedProvider === p.id }"
            @click="selectProvider(p.id)"
          >
            <span class="provider-index font-mono">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="provider-name font-mono">{{ p.name }}</span>
            <span v-if="selectedProvider === p.id" class="provider-dot" />
          </button>
        </div>

        <div class="field-group">
          <div class="field-header">
            <label class="field-label font-mono">API KEY</label>
            <div class="field-rule" />
          </div>
          <p class="field-note font-mono">{{ apiKeyNote }}</p>
          <div class="api-key-wrap">
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
                :size="14"
                class="eye-icon"
              />
            </button>
          </div>
        </div>
      </section>

      <!-- ── Sleep Preferences ───────────────────── -->
      <section class="settings-card">
        <div class="card-header">
          <div class="card-header-left">
            <BedDouble :size="13" class="card-icon" />
            <span class="card-label font-mono">SLEEP PROFILE</span>
          </div>
          <div class="card-rule" />
          <span class="card-tag font-mono">CONFIGURE</span>
        </div>

        <div class="sleep-display">
          <div class="sleep-label-row">
            <span class="field-label font-mono">SLEEP TARGET</span>
          </div>
          <div class="sleep-time-row">
            <input
              v-model="sleepTime"
              type="time"
              class="time-input font-mono"
              @change="saveSleepTime"
            />
          </div>
        </div>

        <div class="field-divider" />

        <div class="field-group">
          <div class="field-header">
            <label class="field-label font-mono">CHRONOTYPE</label>
            <div class="field-rule" />
          </div>
          <div class="chrono-grid">
            <button
              v-for="c in chronotypes"
              :key="c.id"
              class="chrono-btn"
              :class="{ 'chrono-btn--active': selectedChronotype === c.id }"
              @click="selectChronotype(c.id)"
            >
              <component :is="c.icon" :size="18" class="chrono-icon" />
              <span class="chrono-label font-mono">{{ c.label.toUpperCase() }}</span>
            </button>
          </div>
        </div>
      </section>

      <!-- ── Location ────────────────────────────── -->
      <section class="settings-card">
        <div class="card-header">
          <div class="card-header-left">
            <MapPin :size="13" class="card-icon" />
            <span class="card-label font-mono">LOCATION</span>
          </div>
          <div class="card-rule" />
          <span class="card-tag font-mono">GPS</span>
        </div>

        <div class="location-row">
          <div class="location-data">
            <span class="location-name">{{ geo.locationName }}</span>
            <span class="location-coords font-mono">
              {{ geo.lat.toFixed(4) }}°  {{ geo.lng.toFixed(4) }}°
            </span>
          </div>
          <button
            class="refresh-btn"
            :disabled="isRefreshingLocation"
            @click="refreshLocation"
          >
            <RefreshCw
              :size="12"
              :class="{ 'spin-anim': isRefreshingLocation }"
            />
            <span class="font-mono">REFRESH</span>
          </button>
        </div>

        <p v-if="geo.error" class="location-error font-mono">{{ geo.error }}</p>
      </section>

      <!-- ── About ───────────────────────────────── -->
      <section class="settings-card settings-card--about">
        <div class="card-header">
          <div class="card-header-left">
            <Info :size="13" class="card-icon" />
            <span class="card-label font-mono">SYSTEM</span>
          </div>
          <div class="card-rule" />
          <span class="card-tag font-mono">v0.1.0</span>
        </div>

        <div class="about-grid">
          <div class="about-row">
            <span class="about-key font-mono">DATA</span>
            <span class="about-val">NASA Open APIs · NOAA SWPC</span>
          </div>
          <div class="about-row">
            <span class="about-key font-mono">ENV</span>
            <span class="about-val">Open-Meteo · AQICN</span>
          </div>
          <div class="about-row">
            <span class="about-key font-mono">ENGINE</span>
            <span class="about-val">Peer-reviewed circadian science</span>
          </div>
        </div>

        <div class="about-disclaimer font-mono">
          Not affiliated with or endorsed by NASA. Data sourced from NASA public APIs.
        </div>
      </section>

    </div>
  </div>
</template>

<style scoped>
/* ── Page ─────────────────────────────────────────── */

.settings-page {
  min-height: 100vh;
  padding-top: 3.5rem;
  background: var(--bg-primary);
}

/* ── Header ─────────────────────────────────────────── */

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.25rem 0.75rem;
}

.back-btn {
  width: 36px;
  height: 36px;
  border-radius: 0.5rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(148, 163, 184, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}
.back-btn:hover {
  border-color: rgba(255, 189, 118, 0.3);
  color: #FFBD76;
  background: rgba(255, 189, 118, 0.06);
}

.header-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.1rem;
}

.header-eyebrow {
  font-size: 0.42rem;
  font-weight: 600;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: rgba(255, 189, 118, 0.6);
}

.header-title {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-primary);
  margin: 0;
}

/* ── Body ───────────────────────────────────────────── */

.settings-body {
  padding: 0.75rem 1.25rem 3rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 680px;
  margin: 0 auto;
}

/* ── Card ───────────────────────────────────────────── */

.settings-card {
  padding: 1rem 1.125rem 1.125rem;
  border-radius: 1.125rem;
  border: 1px solid rgba(148, 163, 184, 0.1);
  background:
    linear-gradient(160deg, rgba(148, 163, 184, 0.04), rgba(148, 163, 184, 0.01)),
    var(--bg-card);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.03) inset,
    0 8px 24px rgba(0, 0, 0, 0.18);
  position: relative;
  overflow: hidden;
}

.settings-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 1rem;
  right: 1rem;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 189, 118, 0.18), transparent);
  pointer-events: none;
}

.settings-card--about {
  border-color: rgba(148, 163, 184, 0.07);
}

/* ── Card header ────────────────────────────────────── */

.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-shrink: 0;
}

.card-icon {
  color: rgba(148, 163, 184, 0.5);
}

.card-label {
  font-size: 0.48rem;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.65);
}

.card-rule {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.18), transparent);
}

.card-tag {
  font-size: 0.4rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255, 189, 118, 0.5);
  flex-shrink: 0;
}

/* ── Provider grid ──────────────────────────────────── */

.provider-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.4rem;
  margin-bottom: 1rem;
}

.provider-btn {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.2rem;
  padding: 0.55rem 0.6rem 0.5rem;
  border-radius: 0.6rem;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(148, 163, 184, 0.04);
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
  overflow: hidden;
}

.provider-btn::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(circle at top left, rgba(255, 189, 118, 0.07), transparent 60%);
  opacity: 0;
  transition: opacity 0.2s;
}

.provider-btn:hover::after {
  opacity: 1;
}

.provider-btn:hover {
  border-color: rgba(148, 163, 184, 0.22);
  background: rgba(148, 163, 184, 0.07);
}

.provider-btn--active {
  border-color: rgba(255, 189, 118, 0.4) !important;
  background: rgba(255, 189, 118, 0.07) !important;
  box-shadow:
    0 0 0 1px rgba(255, 189, 118, 0.12),
    inset 0 1px 0 rgba(255, 189, 118, 0.1);
}

.provider-btn--active::after {
  opacity: 1 !important;
}

.provider-index {
  font-size: 0.38rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: rgba(148, 163, 184, 0.38);
  transition: color 0.15s;
}

.provider-btn--active .provider-index {
  color: rgba(255, 189, 118, 0.5);
}

.provider-name {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--text-secondary);
  transition: color 0.15s;
}

.provider-btn--active .provider-name {
  color: #FFBD76;
}

.provider-dot {
  position: absolute;
  top: 0.45rem;
  right: 0.5rem;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 189, 118, 0.8);
}

/* ── Field group ────────────────────────────────────── */

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.field-note {
  font-size: 0.4rem;
  line-height: 1.4;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.42);
  margin: 0 0 0.4rem;
}

.field-label {
  font-size: 0.42rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.5);
  flex-shrink: 0;
}

.field-rule {
  flex: 1;
  height: 1px;
  background: rgba(148, 163, 184, 0.1);
}

/* ── API Key input ──────────────────────────────────── */

.api-key-wrap {
  display: flex;
  align-items: center;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 0.6rem;
  background: rgba(148, 163, 184, 0.04);
  overflow: hidden;
  transition: border-color 0.2s;
}

.api-key-wrap:focus-within {
  border-color: rgba(255, 189, 118, 0.35);
  box-shadow: 0 0 0 2px rgba(255, 189, 118, 0.06);
}

.field-input {
  flex: 1;
  padding: 0.55rem 0.75rem;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 0.72rem;
  letter-spacing: 0.02em;
}

.field-input::placeholder {
  color: rgba(148, 163, 184, 0.3);
}

.eye-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.55rem 0.7rem;
  display: flex;
  align-items: center;
  border-left: 1px solid rgba(148, 163, 184, 0.08);
  transition: opacity 0.2s;
}

.eye-icon {
  color: rgba(148, 163, 184, 0.4);
}

.eye-btn:hover .eye-icon {
  color: rgba(148, 163, 184, 0.7);
}

/* ── Sleep ──────────────────────────────────────────── */

.sleep-display {
  margin-bottom: 0.75rem;
}

.sleep-label-row {
  margin-bottom: 0.5rem;
}

.sleep-time-row {
  display: flex;
  align-items: center;
}

.time-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(148, 163, 184, 0.04);
  color: var(--text-primary);
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  outline: none;
  transition: border-color 0.2s;
  color-scheme: dark;
}

.time-input:focus {
  border-color: rgba(255, 189, 118, 0.35);
  box-shadow: 0 0 0 2px rgba(255, 189, 118, 0.06);
}

:global(:root.light) .time-input {
  color-scheme: light;
}

.field-divider {
  height: 1px;
  background: rgba(148, 163, 184, 0.08);
  margin: 0.875rem 0;
}

/* ── Chronotype ─────────────────────────────────────── */

.chrono-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.4rem;
}

.chrono-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  padding: 0.875rem 0.5rem;
  border-radius: 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(148, 163, 184, 0.04);
  cursor: pointer;
  transition: all 0.18s ease;
}

.chrono-btn:hover {
  border-color: rgba(148, 163, 184, 0.22);
  background: rgba(148, 163, 184, 0.07);
}

.chrono-btn--active {
  border-color: rgba(255, 189, 118, 0.4) !important;
  background: rgba(255, 189, 118, 0.07) !important;
  box-shadow: 0 0 0 1px rgba(255, 189, 118, 0.1);
}

.chrono-icon {
  color: rgba(148, 163, 184, 0.45);
  transition: color 0.15s;
}

.chrono-btn--active .chrono-icon {
  color: #FFBD76;
}

.chrono-label {
  font-size: 0.44rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: rgba(148, 163, 184, 0.55);
  text-transform: uppercase;
  transition: color 0.15s;
}

.chrono-btn--active .chrono-label {
  color: rgba(255, 189, 118, 0.85);
}

/* ── Location ───────────────────────────────────────── */

.location-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.location-data {
  display: flex;
  flex-direction: column;
  gap: 0.22rem;
  min-width: 0;
}

.location-name {
  font-family: var(--font-body);
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.location-coords {
  font-size: 0.48rem;
  color: rgba(148, 163, 184, 0.5);
  letter-spacing: 0.1em;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.45rem 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(148, 163, 184, 0.04);
  color: rgba(148, 163, 184, 0.6);
  font-size: 0.42rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.refresh-btn:hover:not(:disabled) {
  border-color: rgba(255, 189, 118, 0.3);
  color: #FFBD76;
  background: rgba(255, 189, 118, 0.06);
}

.refresh-btn:disabled {
  opacity: 0.4;
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
  margin-top: 0.625rem;
  font-size: 0.5rem;
  color: #FF4444;
  letter-spacing: 0.05em;
}

/* ── About ──────────────────────────────────────────── */

.about-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-bottom: 0.875rem;
}

.about-row {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  padding: 0.45rem 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.06);
}

.about-row:last-child {
  border-bottom: none;
}

.about-key {
  font-size: 0.4rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(255, 189, 118, 0.45);
  width: 3.5rem;
  flex-shrink: 0;
}

.about-val {
  font-family: var(--font-body);
  font-size: 0.7rem;
  color: rgba(148, 163, 184, 0.55);
  line-height: 1.4;
}

.about-disclaimer {
  font-size: 0.42rem;
  letter-spacing: 0.04em;
  line-height: 1.6;
  color: rgba(148, 163, 184, 0.3);
  border-top: 1px solid rgba(148, 163, 184, 0.07);
  padding-top: 0.75rem;
}

/* ── Responsive ─────────────────────────────────────── */

@media (max-width: 480px) {
  .provider-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .settings-body {
    padding: 0.75rem 1rem 3rem;
  }
}
</style>
