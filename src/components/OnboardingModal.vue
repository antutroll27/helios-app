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
      selectedProvider.value as 'openai' | 'claude' | 'gemini' | 'grok' | 'perplexity' | 'kimi' | 'glm',
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
          <svg class="logo-svg" viewBox="0 0 501 427" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="HELIOS">
            <path d="M388.793 0.819253C388.375 7.54175 388.432 14.3335 387.463 20.9755C381.374 62.7093 361.568 96.6013 328.108 122.224C302.744 141.647 273.848 152.046 241.889 153.044C223.3 153.625 204.68 153.206 186.075 153.239C185.192 153.241 184.309 153.262 183.114 153.391C182.68 154.284 182.449 155.06 182.449 155.835C182.43 184.184 182.432 212.533 182.431 240.882C181.868 240.922 181.304 240.996 180.74 240.996C160.17 241.002 139.6 241.001 119.03 240.997C118.594 240.997 118.157 240.955 117.657 240.929C117.657 238.575 117.553 236.265 117.672 233.966C119.64 196.038 133.501 163.072 159.61 135.521C184.843 108.895 215.917 93.3996 252.325 88.8483C258.871 88.03 265.528 87.891 272.138 87.8357C288.605 87.6977 305.075 87.793 321.544 87.7744C322.314 87.7735 323.472 88.2295 323.567 86.4725C323.845 85.5293 324.03 84.8033 324.03 84.0771C324.045 57.0751 324.061 30.073 324.003 3.07105C323.999 1.22588 324.54 0.773443 326.335 0.778701C347.154 0.839676 367.974 0.818589 388.793 0.819253Z" fill="currentColor"/>
            <path d="M158.201 7.5107e-05C170.241 1.37922e-07 182.091 0 193.938 0C196.08 80.3132 127.106 154.174 41 153.171C41 131.45 41 109.727 41 87.8017C70.1701 87.8017 99.2787 87.8017 128.571 87.8017C128.571 58.4865 128.571 29.3729 128.571 0.000144437C138.507 0.000144437 148.259 0.000144397 158.201 7.5107e-05Z" fill="currentColor"/>
            <path d="M464.883 153.108C464.195 153.154 463.507 153.239 462.82 153.239C435.124 153.242 407.428 153.236 379.732 153.232C379.176 153.232 378.619 153.232 377.814 153.232C377.814 167.94 377.814 182.486 377.814 197.031C377.814 211.594 377.814 226.156 377.814 240.859C355.951 240.859 334.223 240.859 312.367 240.859C312.367 238.542 312.276 236.167 312.381 233.801C315.338 166.969 362.143 109.284 426.928 92.5833C439.267 89.4025 451.802 87.7814 464.714 87.9534C464.885 109.828 464.884 131.468 464.883 153.108Z" fill="currentColor"/>
            <path d="M5.97777 404.785V352.48H12.2544V375.718H36.7633V352.48H43.04V404.785H36.7633V381.397H12.2544V404.785H5.97777ZM105.825 404.785V352.48H138.031V358.158H112.102V375.643H135.938V381.322H112.102V399.106H138.404V404.785H105.825ZM198.741 404.785V352.48H205.017V399.106H231.469V404.785H198.741ZM290.342 404.785V352.48H296.619V404.785H290.342ZM378.376 405.831C372.149 405.831 367.167 404.038 363.431 400.451C359.745 396.815 357.902 391.534 357.902 384.61V372.655C357.902 365.73 359.745 360.475 363.431 356.888C367.167 353.252 372.149 351.433 378.376 351.433C384.652 351.433 389.634 353.252 393.32 356.888C397.056 360.475 398.924 365.73 398.924 372.655V384.61C398.924 391.534 397.056 396.815 393.32 400.451C389.634 404.038 384.652 405.831 378.376 405.831ZM378.376 400.227C382.909 400.227 386.421 398.882 388.911 396.192C391.402 393.452 392.647 389.666 392.647 384.834V372.43C392.647 367.598 391.402 363.837 388.911 361.147C386.421 358.407 382.909 357.038 378.376 357.038C373.892 357.038 370.405 358.407 367.914 361.147C365.424 363.837 364.178 367.598 364.178 372.43V384.834C364.178 389.666 365.424 393.452 367.914 396.192C370.405 398.882 373.892 400.227 378.376 400.227ZM477.602 405.831C473.817 405.831 470.429 405.159 467.44 403.814C464.451 402.469 462.085 400.451 460.342 397.761C458.648 395.021 457.801 391.609 457.801 387.524V385.955H464.003V387.524C464.003 391.858 465.273 395.096 467.814 397.238C470.354 399.33 473.617 400.376 477.602 400.376C481.687 400.376 484.801 399.455 486.943 397.612C489.085 395.769 490.156 393.452 490.156 390.663C490.156 388.72 489.658 387.176 488.661 386.03C487.715 384.884 486.37 383.962 484.626 383.265C482.883 382.518 480.84 381.87 478.499 381.322L474.614 380.351C471.575 379.554 468.885 378.582 466.544 377.437C464.202 376.291 462.359 374.797 461.014 372.953C459.719 371.06 459.071 368.644 459.071 365.705C459.071 362.766 459.794 360.226 461.238 358.084C462.733 355.942 464.8 354.298 467.44 353.152C470.13 352.006 473.219 351.433 476.706 351.433C480.243 351.433 483.406 352.056 486.196 353.301C489.035 354.497 491.252 356.29 492.846 358.681C494.49 361.023 495.312 363.987 495.312 367.573V370.712H489.11V367.573C489.11 365.033 488.562 362.99 487.466 361.446C486.42 359.902 484.95 358.756 483.057 358.009C481.214 357.262 479.097 356.888 476.706 356.888C473.269 356.888 470.504 357.66 468.412 359.205C466.319 360.699 465.273 362.841 465.273 365.631C465.273 367.474 465.722 368.968 466.618 370.114C467.515 371.26 468.785 372.206 470.429 372.953C472.073 373.651 474.041 374.273 476.332 374.821L480.218 375.793C483.256 376.44 485.971 377.337 488.362 378.483C490.803 379.579 492.746 381.098 494.191 383.041C495.635 384.934 496.358 387.425 496.358 390.513C496.358 393.602 495.586 396.292 494.041 398.583C492.497 400.875 490.305 402.668 487.466 403.963C484.676 405.208 481.388 405.831 477.602 405.831Z" fill="currentColor"/>
          </svg>
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
          <div class="step-label-row">
            <span class="step-label font-mono">SELECT AI ENGINE</span>
            <div class="step-label-rule" />
          </div>

          <div class="provider-grid">
            <button
              v-for="(p, i) in PROVIDERS"
              :key="p.id"
              class="provider-card"
              :class="{ 'provider-card--selected': selectedProvider === p.id }"
              @click="selectedProvider = p.id"
            >
              <span class="provider-index font-mono">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="provider-name font-display">{{ p.name }}</span>
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
  max-width: 34rem;
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

.logo-svg {
  height: 52px;
  width: auto;
  color: var(--text-primary);
  display: block;
  margin: 0 auto;
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

/* ── Step label row (step 1) ────────────────────────── */

.step-label-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.875rem;
}

.step-label {
  font-size: 0.48rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--text-muted);
  flex-shrink: 0;
}

.step-label-rule {
  flex: 1;
  height: 1px;
  background: var(--border-subtle);
}

/* ── Provider grid ──────────────────────────────────── */

.provider-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.375rem;
  margin-bottom: 1.25rem;
}

.provider-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.375rem;
  padding: 0.625rem 0.625rem 0.625rem 0.75rem;
  border-radius: 0.25rem;
  border: 1px solid var(--border-subtle);
  background: transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
  min-height: 56px;
}
.provider-card:hover:not(.provider-card--selected) {
  border-color: var(--glass-border);
  background: var(--bg-card-hover);
}
.provider-card--selected {
  border-color: #FFBD76 !important;
  background: #FFBD76;
}
.provider-card--selected .provider-index {
  color: rgba(10, 23, 29, 0.35);
}
.provider-card--selected .provider-name {
  color: #0A171D;
}

.provider-index {
  font-size: 0.42rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.provider-name {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-primary);
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

:global(:root.light) .time-input {
  color-scheme: light;
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
