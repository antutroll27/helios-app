<script setup lang="ts">
interface Props {
  label: string
  value: string
  unit: string
  accent: string
}
defineProps<Props>()
</script>

<template>
  <div class="metric-tile bento-card">
    <p class="metric-tile__label font-mono text-xs5 tracking-label">{{ label }}</p>
    <div class="metric-tile__body">
      <span class="metric-tile__value font-display">{{ value }}</span>
      <span class="metric-tile__unit font-mono text-xs5" :style="{ color: accent }">{{ unit }}</span>
    </div>
  </div>
</template>

<style scoped>
.metric-tile {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 100px;
}
.metric-tile__label {
  margin: 0;
  color: var(--text-muted);
}
.metric-tile__body {
  display: flex;
  align-items: baseline;
  gap: 0.375rem;
  margin-top: auto;
}
.metric-tile__value {
  font-size: 2.2rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.025em;
}
.metric-tile__unit {
  font-weight: 500;
  opacity: 0.9;
}
</style>
