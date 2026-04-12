<script setup lang="ts">
import { ref, useSlots } from 'vue'

defineProps<{
  label:     string
  title:     string
  accent:    string
  citation:  string
  hasOutput: boolean
}>()

const slots        = useSlots()
const showEvidence = ref(false)
</script>

<template>
  <div class="lab-card bento-card" :style="{ '--card-accent': accent }">
    <div class="lab-card__header">
      <div class="lab-card__label">{{ label }}</div>
      <h2 class="lab-card__title">{{ title }}</h2>
    </div>
    <slot name="inputs" />
    <template v-if="hasOutput">
      <div class="lab-card__divider" />
      <slot name="output" />
      <button
        v-if="slots.evidence"
        class="lab-card__evidence-toggle"
        @click="showEvidence = !showEvidence"
      >
        {{ showEvidence ? '▾' : '▸' }} Research basis
      </button>
      <div
        v-if="slots.evidence"
        class="lab-card__evidence-wrap"
        :class="{ 'lab-card__evidence-wrap--open': showEvidence }"
      >
        <slot name="evidence" />
      </div>
    </template>
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

/* Evidence toggle */
.lab-card__evidence-toggle {
  align-self: flex-start;
  background: none;
  border: none;
  padding: 0;
  margin-top: 0.35rem;
  font-family: 'Geist Mono', monospace;
  font-size: var(--font-size-3xs);
  letter-spacing: var(--tracking-fine);
  color: rgba(255, 246, 233, 0.35);
  cursor: pointer;
  transition: color 0.15s;
}
.lab-card__evidence-toggle:hover {
  color: var(--card-accent);
}

/* Evidence body — hidden by default, shown via class */
.lab-card__evidence-wrap {
  display: none;
  margin-top: 0.25rem;
}
.lab-card__evidence-wrap--open {
  display: block;
}
</style>
