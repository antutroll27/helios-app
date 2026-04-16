import { ref, computed } from 'vue'

export const TECHNIQUES = {
  resonance: { bpm: 5.5, label: 'Resonance', baseBoost: 30, extendedExhale: true  },
  box:        { bpm: 4,   label: 'Box',       baseBoost: 20, extendedExhale: false },
  '4-7-8':    { bpm: 3.6, label: '4-7-8',    baseBoost: 25, extendedExhale: true  },
  coherent:   { bpm: 6,   label: 'Coherent', baseBoost: 28, extendedExhale: false },
} as const

export type Technique = keyof typeof TECHNIQUES

export function calculateBreathworkResponse(
  technique: Technique,
  durationMin: number
): { rmssdBoost: number; residualHours: number; bpm: number } {
  const tech = TECHNIQUES[technique]
  // Dose-response (Laborde 2022 meta-analysis)
  const durationMult = durationMin <= 5 ? 0.5 : durationMin <= 10 ? 0.75 : durationMin <= 20 ? 1.0 : 1.15
  // Van Diest 2014: extended exhale +15% vs equal ratio
  const ratioBonus = tech.extendedExhale ? 1.15 : 1.0
  const rmssdBoost = Math.round(tech.baseBoost * durationMult * ratioBonus)
  const residualHours = durationMin <= 10 ? 1 : durationMin <= 20 ? 2 : 4
  return { rmssdBoost, residualHours, bpm: tech.bpm }
}

export function useBreathwork() {
  const technique   = ref<Technique>('resonance')
  const durationMin = ref(10)

  const result = computed(() =>
    calculateBreathworkResponse(technique.value, durationMin.value)
  )

  return { technique, durationMin, result }
}
