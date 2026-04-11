<script setup lang="ts">
interface Props {
  anchorLabel: string
  destinationLabel: string
  timingLabel: string
}

defineProps<Props>()
</script>

<template>
  <div class="globe-stat-strip">
    <dl class="globe-stat-strip__list" aria-label="Globe status strip">
      <div class="globe-stat-strip__item">
        <dt class="globe-stat-strip__label">Anchor</dt>
        <dd class="globe-stat-strip__value">{{ anchorLabel }}</dd>
      </div>

      <div class="globe-stat-strip__item">
        <dt class="globe-stat-strip__label">Target</dt>
        <dd class="globe-stat-strip__value">{{ destinationLabel }}</dd>
      </div>

      <div class="globe-stat-strip__item">
        <dt class="globe-stat-strip__label">Solar Shift</dt>
        <dd class="globe-stat-strip__value">{{ timingLabel }}</dd>
      </div>
    </dl>
  </div>
</template>

<style scoped>
.globe-stat-strip {
  width: 100%;
}

.globe-stat-strip__list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
  width: 100%;
  padding: 0.78rem 0.88rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 999px;
  background:
    linear-gradient(180deg, rgba(10, 18, 32, 0.72), rgba(7, 15, 28, 0.54)),
    radial-gradient(circle at top, rgba(0, 212, 170, 0.08), transparent 60%);
  box-shadow:
    0 18px 36px rgba(2, 8, 20, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.globe-stat-strip__list,
.globe-stat-strip__item,
.globe-stat-strip__label,
.globe-stat-strip__value {
  min-width: 0;
}

.globe-stat-strip__list {
  margin: 0;
}

.globe-stat-strip__item {
  display: grid;
  gap: 0.2rem;
  padding-inline: 0.15rem;
}

.globe-stat-strip__label {
  margin: 0;
  font-size: 0.64rem;
  line-height: 1.1;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(203, 213, 225, 0.82);
}

.globe-stat-strip__value {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.28;
  font-weight: 650;
  color: rgba(248, 250, 252, 0.98);
  overflow-wrap: anywhere;
  text-wrap: balance;
}

@media (max-width: 720px) {
  .globe-stat-strip__list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.38rem;
    border-radius: 1rem;
    padding: 0.65rem 0.72rem;
  }

  .globe-stat-strip__item {
    flex: 1 1 8.25rem;
    gap: 0.2rem;
    padding-inline: 0;
  }

  .globe-stat-strip__label {
    font-size: 0.64rem;
    letter-spacing: 0.18em;
  }

  .globe-stat-strip__value {
    font-size: 0.9rem;
    line-height: 1.2;
  }
}
</style>
