<script setup lang="ts">
import { useBiometricsStore } from '@/stores/biometrics'
import type { DateRange } from '@/stores/biometrics'

const emit = defineEmits<{
  'upload-click': []
}>()

const biometrics = useBiometricsStore()

function setRange(range: DateRange) {
  biometrics.setDateRange(range)
}
</script>

<template>
  <div class="header-row">
    <!-- Left: eyebrow + title -->
    <div class="header-left">
      <p class="eyebrow text-xs5 tracking-label">HELIOS / BIOMETRICS</p>
      <h1 class="title">Sleep &amp; Recovery</h1>
    </div>

    <!-- Right: controls -->
    <div class="header-controls">
      <!-- 7d / 30d toggle -->
      <div class="range-toggle">
        <button
          class="toggle-btn"
          :class="{ active: biometrics.dateRange === 7 }"
          @click="setRange(7)"
        >
          7d
        </button>
        <button
          class="toggle-btn"
          :class="{ active: biometrics.dateRange === 30 }"
          @click="setRange(30)"
        >
          30d
        </button>
      </div>

      <!-- DEMO DATA chip — shown when source is mock -->
      <span v-if="biometrics.dataSource === 'mock'" class="demo-chip text-xs3 tracking-label">
        DEMO DATA
      </span>

      <!-- Upload Data button -->
      <button class="upload-btn text-xs5" @click="emit('upload-click')">
        Upload Data
      </button>
    </div>
  </div>
</template>

<style scoped>
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-card);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.eyebrow {
  font-family: var(--font-mono);
  color: var(--text-muted);
  margin: 0;
  letter-spacing: 0.15em;
}

.title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.02em;
  font-family: var(--font-display);
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

/* Range toggle pill */
.range-toggle {
  display: flex;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 0.5rem;
  overflow: hidden;
}

.toggle-btn {
  padding: 0.25rem 0.625rem;
  font-size: 0.6rem;
  font-weight: 600;
  font-family: var(--font-mono);
  letter-spacing: 0.08em;
  color: var(--text-muted);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.toggle-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 189, 118, 0.08);
}

.toggle-btn.active {
  background: rgba(255, 189, 118, 0.15);
  color: #FFBD76;
}

/* DEMO DATA chip */
.demo-chip {
  font-family: var(--font-mono);
  padding: 0.2rem 0.5rem;
  background: rgba(0, 212, 170, 0.08);
  border: 1px solid rgba(0, 212, 170, 0.2);
  border-radius: 0.375rem;
  color: #00D4AA;
  letter-spacing: 0.15em;
}

/* Upload button — ghost style */
.upload-btn {
  padding: 0.25rem 0.625rem;
  background: transparent;
  border: 1px solid var(--border-card);
  border-radius: 0.5rem;
  color: var(--text-muted);
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 0.6rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
}

.upload-btn:hover {
  border-color: #FFBD76;
  color: #FFBD76;
  background: rgba(255, 189, 118, 0.06);
}
</style>
