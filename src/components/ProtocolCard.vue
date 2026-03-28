<script setup lang="ts">
import { computed } from 'vue'
import { Sunrise, Sun, Brain, Coffee, Moon, BedDouble } from 'lucide-vue-next'

const props = defineProps<{
  title: string
  time: Date
  icon: string
  citation: string
  subtitle: string
  status: 'upcoming' | 'active' | 'passed'
}>()

const iconMap: Record<string, object> = {
  Sunrise, Sun, Brain, Coffee, Moon, BedDouble
}

const iconComponent = computed(() => iconMap[props.icon] ?? Sun)

const formattedTime = computed(() => {
  try {
    const d = props.time instanceof Date ? props.time : new Date(props.time)
    if (isNaN(d.getTime())) {
      // If it's already a time string like "05:48" or "19:30", show it directly
      return String(props.time)
    }
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return String(props.time)
  }
})

// Each card gets a distinct color — Swiss poster vibes with punch
const cardThemes: Record<string, { bg: string; text: string; accent: string }> = {
  Sunrise:   { bg: '#FFBD76', text: '#0A171D', accent: '#0A171D' },  // warm amber
  Sun:       { bg: '#FFD700', text: '#0A171D', accent: '#0A171D' },  // gold
  Brain:     { bg: '#A78BFA', text: '#FFFFFF', accent: '#FFFFFF' },  // violet
  Coffee:    { bg: '#F97316', text: '#FFFFFF', accent: '#FFFFFF' },  // orange
  Moon:      { bg: '#60A5FA', text: '#0A171D', accent: '#0A171D' },  // blue
  BedDouble: { bg: '#818CF8', text: '#FFFFFF', accent: '#FFFFFF' },  // indigo
}

const theme = computed(() => cardThemes[props.icon] || cardThemes.Sun)
const isPassed = computed(() => props.status === 'passed')
const isActive = computed(() => props.status === 'active')
</script>

<template>
  <div class="card" :class="{ 'card--passed': isPassed }">
    <!-- Colored circle with time — the hero -->
    <div class="card-circle" :style="{ background: theme.bg }">
      <component
        :is="iconComponent"
        :size="16"
        :color="theme.text"
        :stroke-width="2"
        style="position: absolute; top: 10px; right: 10px; opacity: 0.4;"
      />
      <span class="card-time font-mono" :style="{ color: theme.text }">{{ formattedTime }}</span>
    </div>

    <!-- Label with icon -->
    <div class="card-label font-mono">
      <component :is="iconComponent" :size="13" :color="theme.bg" :stroke-width="2" />
      <span :style="{ color: theme.bg }">{{ title }}</span>
    </div>

    <!-- Description -->
    <p class="card-desc">{{ subtitle }}</p>

    <!-- Citation -->
    <p class="card-cite font-mono">/ {{ citation }}</p>
  </div>
</template>

<style scoped>
.card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 1.5rem 1rem 1.25rem;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  transition: all 0.2s ease;
  gap: 0.5rem;
}

.card:hover {
  background: var(--bg-card-hover);
  transform: translateY(-2px);
}

.card--passed {
  opacity: 0.3;
}

/* Colored circle with time */
.card-circle {
  position: relative;
  width: 90px;
  height: 90px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.15rem;
  overflow: hidden;
}

.card-time {
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

/* Label with icon and colored text */
.card-label {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.55rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.card-desc {
  font-family: var(--font-body);
  font-size: 0.65rem;
  color: var(--text-secondary);
  line-height: 1.4;
  max-width: 190px;
}

.card-cite {
  font-size: 0.48rem;
  color: var(--text-muted);
  line-height: 1.3;
  opacity: 0.5;
  max-width: 190px;
}
</style>
