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
</script>

<template>
  <div
    class="flex flex-col items-center text-center pt-6 pb-5 px-4 bg-(--bg-card) border border-(--border-subtle) rounded-lg transition-all duration-200 ease-in-out gap-2 hover:bg-(--bg-card-hover) hover:-translate-y-0.5"
    :class="{ 'opacity-30': isPassed }"
  >
    <!-- Colored circle with time — the hero -->
    <div class="relative w-[90px] h-[90px] rounded-full flex items-center justify-center mb-[0.15rem] overflow-hidden" :style="{ background: theme.bg }">
      <component
        :is="iconComponent"
        :size="16"
        :color="theme.text"
        :stroke-width="2"
        class="absolute top-2.5 right-2.5 opacity-40"
      />
      <span class="font-mono text-[1.35rem] font-extrabold tracking-[-0.02em]" :style="{ color: theme.text }">{{ formattedTime }}</span>
    </div>

    <!-- Label with icon -->
    <div class="font-mono flex items-center gap-[0.3rem] text-[0.55rem] font-bold tracking-[0.15em] uppercase">
      <component :is="iconComponent" :size="13" :color="theme.bg" :stroke-width="2" />
      <span :style="{ color: theme.bg }">{{ title }}</span>
    </div>

    <!-- Description -->
    <p class="font-body text-[0.65rem] text-(--text-secondary) leading-[1.4] max-w-47.5">{{ subtitle }}</p>

    <!-- Citation -->
    <p class="font-mono text-[0.48rem] text-(--text-muted) leading-[1.3] opacity-50 max-w-47.5">/ {{ citation }}</p>
  </div>
</template>
