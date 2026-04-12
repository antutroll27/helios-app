<script setup lang="ts">
import { onMounted } from 'vue'
onMounted(() => { document.title = 'HELIOS · Lab' })
</script>

<template>
  <div class="lab-page">
    <div class="lab-header">
      <div class="lab-page__breadcrumb">HELIOS / LAB</div>
      <h1 class="lab-page__title">Science Tools</h1>
      <p class="lab-page__sub">Peer-reviewed calculators. Every output cites its source.</p>
    </div>
    <div class="lab-grid">
      <!-- cards added per task -->
    </div>
  </div>
</template>

<style scoped>
.lab-page { padding: 5rem 1.5rem 2rem; max-width: 1000px; margin: 0 auto; }
.lab-page__breadcrumb { font-family: 'Geist Mono', monospace; font-size: 0.45rem; letter-spacing: 0.15em; color: var(--text-muted); margin-bottom: 0.3rem; }
.lab-page__title { font-size: 1.8rem; font-weight: 800; letter-spacing: -0.04em; }
.lab-page__sub { font-size: 0.55rem; color: var(--text-muted); margin-top: 0.3rem; }
.lab-header { margin-bottom: 1.5rem; }
.lab-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
@media (max-width: 900px) { .lab-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 580px) { .lab-grid { grid-template-columns: 1fr; } }
</style>
