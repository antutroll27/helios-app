<script setup lang="ts">
defineProps<{
  label: string       // e.g. "NAP CALCULATOR"
  title: string       // e.g. "Nap Timing"
  accent: string      // hex color
  citation: string    // e.g. "Rosekind 1995 · NASA"
  hasOutput: boolean
}>()
</script>

<template>
  <div class="lab-card bento-card" :style="{ '--card-accent': accent }">
    <div class="lab-card__header">
      <div class="lab-card__label">{{ label }}</div>
      <h2 class="lab-card__title">{{ title }}</h2>
    </div>
    <slot name="inputs" />
    <div v-if="hasOutput" class="lab-card__divider" />
    <slot v-if="hasOutput" name="output" />
    <slot v-if="hasOutput" name="evidence" />
    <div class="lab-card__citation">{{ citation }}</div>
  </div>
</template>

<style scoped>
.lab-card {
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.lab-card__label {
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-label);
  color: var(--card-accent);
  font-weight: 700;
  text-transform: uppercase;
}
.lab-card__title {
  font-size: var(--font-size-md2);
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 0.1rem;
}
.lab-card__divider {
  height: 1px;
  background: rgba(255,246,233,0.06);
  margin: 0.25rem 0;
}
.lab-card__citation {
  font-size: var(--font-size-4xs);
  color: rgba(255,246,233,0.2);
  font-style: italic;
  margin-top: auto;
  padding-top: 0.4rem;
}
</style>
