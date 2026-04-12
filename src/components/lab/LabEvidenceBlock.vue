<script setup lang="ts">
defineProps<{
  effect: string      // e.g. "+180 min alertness after 26 min nap"
  population: string  // e.g. "NASA pilots / controlled nap studies"
  caveat: string      // e.g. "Late naps can impair night sleep efficiency"
}>()
</script>

<template>
  <div class="lab-evidence">
    <div class="lab-evidence__row">
      <span class="lab-evidence__key">Effect</span>
      <span class="lab-evidence__val">{{ effect }}</span>
    </div>
    <div class="lab-evidence__row">
      <span class="lab-evidence__key">Population</span>
      <span class="lab-evidence__val">{{ population }}</span>
    </div>
    <div class="lab-evidence__row lab-evidence__row--caveat">
      <span class="lab-evidence__key">Caveat</span>
      <span class="lab-evidence__val">{{ caveat }}</span>
    </div>
  </div>
</template>

<style scoped>
.lab-evidence {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  margin-top: 0.2rem;
}
.lab-evidence__row {
  display: flex;
  gap: 0.4rem;
  align-items: baseline;
  font-size: 0.42rem;
  line-height: 1.5;
}
.lab-evidence__key {
  font-family: 'Geist Mono', monospace;
  font-size: 0.38rem;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  text-transform: uppercase;
  flex-shrink: 0;
  width: 56px;
}
.lab-evidence__val {
  color: rgba(255,246,233,0.65);
}
.lab-evidence__row--caveat .lab-evidence__val {
  color: rgba(255,189,118,0.7);
  font-style: italic;
}
</style>
