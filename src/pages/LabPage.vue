<script setup lang="ts">
import { onMounted } from 'vue'
import NapCalcCard from '../components/lab/NapCalcCard.vue'
import AlcoholImpactCard from '../components/lab/AlcoholImpactCard.vue'
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
      <NapCalcCard />
      <AlcoholImpactCard />
    </div>
  </div>
</template>

<style scoped>
.lab-page { padding: 5rem 1.5rem 2rem; max-width: 1000px; margin: 0 auto; }
.lab-page__breadcrumb { font-family: 'Geist Mono', monospace; font-size: var(--font-size-3xs); letter-spacing: var(--tracking-label); color: var(--text-muted); margin-bottom: 0.3rem; }
.lab-page__title { font-size: 1.8rem; font-weight: 800; letter-spacing: -0.04em; }
.lab-page__sub { font-size: var(--font-size-xs3); color: var(--text-muted); margin-top: 0.3rem; }
.lab-header { margin-bottom: 1.5rem; }
.lab-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
@media (max-width: 900px) { .lab-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 580px) { .lab-grid { grid-template-columns: 1fr; } }
</style>
