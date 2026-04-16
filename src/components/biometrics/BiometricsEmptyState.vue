<script setup lang="ts">
import { Activity } from 'lucide-vue-next'
import { useBiometricsStore } from '@/stores/biometrics'

const emit = defineEmits<{ (e: 'upload-click'): void }>()
const biometrics = useBiometricsStore()

function loadDemo() {
  biometrics.loadMockData()
}
</script>

<template>
  <div class="empty-state">
    <Activity :size="40" class="empty-state__icon" />
    <h2 class="empty-state__title">No biometric data yet</h2>
    <p class="empty-state__body text-xs5">
      Load demo data to explore your circadian patterns, or upload a wearable export.
    </p>
    <div class="empty-state__actions">
      <button class="empty-state__btn empty-state__btn--primary font-mono text-xs4 tracking-label" @click="loadDemo">
        LOAD DEMO DATA
      </button>
      <button class="empty-state__btn empty-state__btn--ghost font-mono text-xs4 tracking-label" @click="emit('upload-click')">
        UPLOAD EXPORT
      </button>
    </div>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 260px;
  gap: 0.75rem;
  text-align: center;
  padding: 2rem 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 1rem;
}

.empty-state__icon {
  color: var(--text-muted);
  opacity: 0.4;
  flex-shrink: 0;
}

.empty-state__title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-display);
  letter-spacing: -0.01em;
}

.empty-state__body {
  margin: 0;
  color: var(--text-muted);
  max-width: 320px;
  line-height: 1.6;
}

.empty-state__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 0.25rem;
}

.empty-state__btn {
  padding: 0.3rem 0.875rem;
  border-radius: 2rem;
  cursor: pointer;
  font-weight: 600;
  letter-spacing: 0.15em;
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
}

.empty-state__btn--primary {
  background: rgba(0, 212, 170, 0.08);
  border: 1px solid rgba(0, 212, 170, 0.45);
  color: #00D4AA;
}

.empty-state__btn--primary:hover {
  background: rgba(0, 212, 170, 0.16);
  border-color: #00D4AA;
}

.empty-state__btn--ghost {
  background: transparent;
  border: 1px solid var(--border-card);
  color: var(--text-muted);
}

.empty-state__btn--ghost:hover {
  border-color: rgba(148, 163, 184, 0.4);
  color: var(--text-primary);
  background: transparent;
}
</style>
