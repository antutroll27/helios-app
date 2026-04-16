<script setup lang="ts">
import { computed } from 'vue'
import { useBiometricsStore } from '@/stores/biometrics'

const biometrics = useBiometricsStore()
const insights = computed(() => biometrics.insights)
</script>

<template>
  <div class="insights-panel">
    <!-- Header -->
    <header class="insights-panel__header">
      <p class="insights-panel__eyebrow font-mono text-xs5 tracking-label">CIRCADIAN INSIGHTS</p>
      <span class="insights-panel__count font-mono text-xs5">
        {{ insights.length }} active
      </span>
    </header>
    <div class="insights-panel__rule" />

    <!-- Cards -->
    <div class="insights-panel__list">
      <article
        v-for="insight in insights"
        :key="insight.id"
        class="insight-card"
        :style="{ borderLeftColor: insight.accent }"
      >
        <!-- Type · Confidence row -->
        <div class="insight-card__meta">
          <span class="insight-card__type font-mono text-xs4 tracking-spread">
            {{ insight.type.toUpperCase() }}
          </span>
          <span
            class="insight-card__badge font-mono"
            :class="`insight-card__badge--${insight.confidence}`"
          >{{ insight.confidence.toUpperCase() }}</span>
        </div>

        <!-- Title -->
        <h3 class="insight-card__title font-display">{{ insight.title }}</h3>

        <!-- Body -->
        <p class="insight-card__body">{{ insight.body }}</p>
      </article>

      <p v-if="insights.length === 0" class="insights-panel__empty text-xs5">
        No patterns detected yet. Check back after 7+ nights of data.
      </p>
    </div>
  </div>
</template>

<style scoped>
/* ── Panel shell ─────────────────────────────────────────── */
.insights-panel {
  display: flex;
  flex-direction: column;
  gap: 0;
  height: 100%;
}

.insights-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  padding-bottom: 0.5rem;
}

.insights-panel__eyebrow {
  margin: 0;
  color: var(--text-primary);
}

/* count badge */
.insights-panel__count {
  color: var(--text-muted);
  background: var(--bg-surface);
  border: 1px solid var(--border-card);
  border-radius: 0.375rem;
  padding: 0.1rem 0.45rem;
  font-size: 0.55rem;
  letter-spacing: 0.06em;
}

/* hairline separator */
.insights-panel__rule {
  height: 1px;
  background: var(--border-card);
  flex-shrink: 0;
  margin-bottom: 0.625rem;
}

.insights-panel__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  overflow-y: auto;
}

/* ── Insight card ─────────────────────────────────────────── */
.insight-card {
  /* no full box border — just the left accent stripe */
  background: var(--bg-card);
  border-left: 2.5px solid transparent; /* color set inline */
  border-radius: 0 0.5rem 0.5rem 0;
  padding: 0.625rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  transition: background 0.15s ease;
}

.insight-card:hover {
  background: var(--bg-card-hover);
}

/* meta row */
.insight-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.insight-card__type {
  color: var(--text-muted);
  font-size: 0.55rem;
  letter-spacing: 0.1em;
}

/* confidence chip */
.insight-card__badge {
  font-size: 0.55rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  padding: 0.12rem 0.4rem;
  border-radius: 0.25rem;
  border: 1px solid transparent;
  flex-shrink: 0;
}

.insight-card__badge--high {
  background: rgba(0, 212, 170, 0.1);
  border-color: rgba(0, 212, 170, 0.3);
  color: #00D4AA;
}

.insight-card__badge--medium {
  background: rgba(255, 189, 118, 0.1);
  border-color: rgba(255, 189, 118, 0.3);
  color: #FFBD76;
}

.insight-card__badge--low {
  background: rgba(96, 112, 128, 0.1);
  border-color: rgba(96, 112, 128, 0.2);
  color: var(--text-muted);
}

/* title */
.insight-card__title {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.25;
  letter-spacing: -0.02em;
}

/* body */
.insight-card__body {
  margin: 0;
  font-family: var(--font-body);
  font-size: 0.68rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* empty state */
.insights-panel__empty {
  margin: 0;
  color: var(--text-muted);
  font-style: italic;
  font-family: var(--font-body);
}
</style>
