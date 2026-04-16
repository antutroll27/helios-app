<script setup lang="ts">
defineProps<{
  label: string
  value: string
  subtext: string
  accent: string
}>()
</script>

<template>
  <div class="phase-a-tile bento-card" :style="{ '--tile-accent': accent }">
    <div class="phase-a-tile__label">{{ label }}</div>
    <div class="phase-a-tile__value">{{ value }}</div>
    <div class="phase-a-tile__sub">{{ subtext }}</div>
  </div>
</template>

<style scoped>
.phase-a-tile {
  padding: 1rem 1.1rem;
  border-left: 2.5px solid var(--tile-accent);
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.phase-a-tile__label {
  font-family: 'Geist Mono', monospace;
  font-size: 0.5rem;           /* text-xs2 */
  letter-spacing: 0.1em;
  color: var(--tile-accent);
  font-weight: 700;
  text-transform: uppercase;
}

.phase-a-tile__value {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  line-height: 1;
  margin: 0.15rem 0;
}

.phase-a-tile__sub {
  font-size: 0.5rem;            /* text-xs2 */
  color: var(--text-muted);
  line-height: 1.4;
}
</style>
