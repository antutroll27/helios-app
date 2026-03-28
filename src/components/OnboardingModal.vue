<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { PROVIDERS } from '@/composables/useAI'
import { Sunrise, Sun, Moon, Sparkles } from 'lucide-vue-next'

const user = useUserStore()

const step = ref(1)

// Step 1 — AI Provider
const selectedProvider = ref<string>('openai')
const apiKeyInput = ref('')

// Step 2 — Sleep Time
const sleepTime = ref('23:00')

// Step 3 — Chronotype
const selectedChronotype = ref<'early' | 'intermediate' | 'late'>('intermediate')

const currentProviderPlaceholder = computed(() => {
  const p = PROVIDERS.find((pr) => pr.id === selectedProvider.value)
  return p ? p.placeholder : '...'
})

const chronotypes = [
  { id: 'early' as const, label: 'Early Bird', desc: 'Rise with the sun', icon: Sunrise },
  { id: 'intermediate' as const, label: 'Intermediate', desc: 'Balanced rhythm', icon: Sun },
  { id: 'late' as const, label: 'Night Owl', desc: 'Peak after dark', icon: Moon },
]

const providerDescriptions: Record<string, string> = {
  openai: 'GPT-4o — fast, versatile',
  claude: 'Claude Sonnet — nuanced, thoughtful',
  kimi: 'Kimi 2.5 — Moonshot AI',
  glm: 'GLM-4 Flash — fast inference',
}

function nextStep() {
  if (step.value < 3) {
    step.value++
  }
}

function prevStep() {
  if (step.value > 1) {
    step.value--
  }
}

function skipAI() {
  step.value = 2
}

function launch() {
  user.completeOnboarding(sleepTime.value, selectedChronotype.value)
  if (apiKeyInput.value.trim()) {
    user.setProvider(
      selectedProvider.value as 'openai' | 'claude' | 'kimi' | 'glm',
      apiKeyInput.value.trim()
    )
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="onboarding-backdrop">
      <div class="onboarding-card">
        <!-- Logo -->
        <div class="onboarding-logo">
          <div class="logo-glow" />
          <h1 class="font-display tracking-label logo-text">HELIOS</h1>
          <p class="tagline">Your body runs on the Sun.</p>
        </div>

        <!-- Step indicators -->
        <div class="step-dots">
          <span
            v-for="s in 3"
            :key="s"
            class="step-dot"
            :class="{ 'step-dot--active': s === step, 'step-dot--done': s < step }"
          />
        </div>

        <!-- ────────── STEP 1: AI Provider ────────── -->
        <div v-if="step === 1" class="step-content animate-fade-in-up">
          <h2 class="step-header">Choose your AI engine</h2>

          <div class="provider-grid">
            <button
              v-for="p in PROVIDERS"
              :key="p.id"
              class="provider-card"
              :class="{ 'provider-card--selected': selectedProvider === p.id }"
              @click="selectedProvider = p.id"
            >
              <span class="provider-name font-display">{{ p.name }}</span>
              <span class="provider-desc">{{ providerDescriptions[p.id] }}</span>
            </button>
          </div>

          <div class="api-key-section">
            <label class="api-key-label font-mono">API KEY</label>
            <input
              v-model="apiKeyInput"
              type="password"
              class="api-key-input font-mono"
              :placeholder="currentProviderPlaceholder"
              autocomplete="off"
            />
          </div>

          <div class="step-actions">
            <button class="skip-link" @click="skipAI">Skip for now</button>
            <button class="next-btn" @click="nextStep">
              Continue
            </button>
          </div>
        </div>

        <!-- ────────── STEP 2: Sleep Time ────────── -->
        <div v-if="step === 2" class="step-content animate-fade-in-up">
          <h2 class="step-header">When do you usually fall asleep?</h2>

          <div class="time-input-wrap">
            <input
              v-model="sleepTime"
              type="time"
              class="time-input font-mono"
            />
          </div>

          <div class="step-actions">
            <button class="back-link" @click="prevStep">Back</button>
            <button class="next-btn" @click="nextStep">
              Continue
            </button>
          </div>
        </div>

        <!-- ────────── STEP 3: Chronotype ────────── -->
        <div v-if="step === 3" class="step-content animate-fade-in-up">
          <h2 class="step-header">Your chronotype</h2>

          <div class="chrono-grid">
            <button
              v-for="c in chronotypes"
              :key="c.id"
              class="chrono-card"
              :class="{ 'chrono-card--selected': selectedChronotype === c.id }"
              @click="selectedChronotype = c.id"
            >
              <component :is="c.icon" :size="24" class="chrono-icon" />
              <span class="chrono-label font-display">{{ c.label }}</span>
              <span class="chrono-desc">{{ c.desc }}</span>
            </button>
          </div>

          <div class="step-actions">
            <button class="back-link" @click="prevStep">Back</button>
            <button class="launch-btn font-display tracking-label" @click="launch">
              <Sparkles :size="16" />
              Launch HELIOS
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* ── Backdrop ───────────────────────────────────────── */

.onboarding-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(10, 23, 29, 0.92);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
}

/* ── Card ───────────────────────────────────────────── */

.onboarding-card {
  width: 100%;
  max-width: 28rem;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 1.25rem;
  padding: 2rem 1.5rem;
  position: relative;
  overflow: hidden;
}

/* Ambient glow at top */
.onboarding-card::before {
  content: '';
  position: absolute;
  top: -40%;
  left: 50%;
  transform: translateX(-50%);
  width: 200%;
  height: 200px;
  background: radial-gradient(ellipse, rgba(255, 189, 118, 0.06) 0%, transparent 70%);
  pointer-events: none;
}

/* ── Logo ───────────────────────────────────────────── */

.onboarding-logo {
  text-align: center;
  margin-bottom: 1.5rem;
  position: relative;
}

.logo-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 189, 118, 0.12), transparent 70%);
  filter: blur(20px);
  pointer-events: none;
}

.logo-text {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  position: relative;
}

.tagline {
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-style: italic;
  color: var(--text-secondary);
  margin-top: 0.375rem;
}

/* ── Step dots ──────────────────────────────────────── */

.step-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.step-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--border-subtle);
  transition: all 0.3s ease;
}
.step-dot--active {
  background: #FFBD76;
  box-shadow: 0 0 8px rgba(255, 189, 118, 0.4);
  transform: scale(1.2);
}
.step-dot--done {
  background: #00D4AA;
}

/* ── Step content ───────────────────────────────────── */

.step-content {
  position: relative;
}

.step-header {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: 1.25rem;
}

/* ── Provider grid ──────────────────────────────────── */

.provider-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.625rem;
  margin-bottom: 1.25rem;
}

.provider-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.25rem;
  padding: 0.875rem;
  border-radius: 0.75rem;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface, var(--bg-primary));
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}
.provider-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--glass-border);
}
.provider-card--selected {
  border-color: #FFBD76 !important;
  background: rgba(255, 189, 118, 0.06);
  box-shadow: 0 0 0 1px rgba(255, 189, 118, 0.2);
}

.provider-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
}

.provider-desc {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-family: var(--font-body);
  line-height: 1.4;
}

/* ── API key ────────────────────────────────────────── */

.api-key-section {
  margin-bottom: 1.25rem;
}

.api-key-label {
  display: block;
  font-size: 0.55rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.api-key-input {
  width: 100%;
  padding: 0.625rem 0.875rem;
  border-radius: 0.625rem;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 0.78rem;
  outline: none;
  transition: border-color 0.2s;
}
.api-key-input:focus {
  border-color: #FFBD76;
  box-shadow: 0 0 0 2px rgba(255, 189, 118, 0.15);
}
.api-key-input::placeholder {
  color: var(--text-muted);
}

/* ── Time input ─────────────────────────────────────── */

.time-input-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
}

.time-input {
  font-size: 2.5rem;
  font-weight: 600;
  text-align: center;
  padding: 1rem 1.5rem;
  border-radius: 1rem;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.2s;
  color-scheme: dark;
}
.time-input:focus {
  border-color: #FFBD76;
  box-shadow: 0 0 0 2px rgba(255, 189, 118, 0.15);
}

/* ── Chronotype grid ────────────────────────────────── */

.chrono-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.625rem;
  margin-bottom: 1.5rem;
}

.chrono-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.375rem;
  padding: 1.25rem 0.5rem;
  border-radius: 0.75rem;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface, var(--bg-primary));
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}
.chrono-card:hover {
  background: var(--bg-card-hover);
}
.chrono-card--selected {
  border-color: #FFBD76 !important;
  background: rgba(255, 189, 118, 0.06);
  box-shadow: 0 0 0 1px rgba(255, 189, 118, 0.2);
}

.chrono-icon {
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}
.chrono-card--selected .chrono-icon {
  color: #FFBD76;
}

.chrono-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-primary);
}

.chrono-desc {
  font-size: 0.6rem;
  color: var(--text-muted);
  font-family: var(--font-body);
}

/* ── Actions ────────────────────────────────────────── */

.step-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.skip-link,
.back-link {
  border: none;
  background: none;
  color: var(--text-muted);
  font-family: var(--font-body);
  font-size: 0.78rem;
  cursor: pointer;
  padding: 0.375rem 0;
  transition: color 0.2s;
}
.skip-link:hover,
.back-link:hover {
  color: var(--text-secondary);
}

.next-btn {
  padding: 0.625rem 1.5rem;
  border-radius: 0.625rem;
  border: 1px solid var(--border-subtle);
  background: var(--bg-card-hover);
  color: var(--text-primary);
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.next-btn:hover {
  background: var(--glass-border);
  border-color: var(--glass-border);
}

.launch-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.75rem;
  border-radius: 0.75rem;
  border: none;
  background: #FFBD76;
  color: #0A171D;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s ease;
}
.launch-btn:hover {
  background: #FFD4A0;
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(255, 189, 118, 0.3);
}
</style>
