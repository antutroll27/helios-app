import { ref, computed } from 'vue'

export function calculateAlcoholImpact(
  drinks: number,
  weightKg: number,
  sex: 'male' | 'female',
  sleepHour: number,
  hoursSinceDrinking: number
) {
  const r = sex === 'male' ? 0.68 : 0.55
  const bac = Math.max(0, (drinks * 14) / (weightKg * r * 10) - 0.015 * hoursSinceDrinking)

  // Pietilä 2018 — dose-response brackets
  const hrvDropPct = drinks === 0 ? 0 : drinks <= 2 ? -9.3 : drinks <= 4 ? -24 : -39.2
  const remLossMin = Math.min(Math.round(drinks * 12), 45)

  // Hours until BAC < 0.01 (safe to sleep with minimal HRV impact)
  const hoursToClear = Math.max(0, (bac - 0.01) / 0.015)
  const cutoffHour = Math.max(0, sleepHour - hoursToClear)

  return { bac, hrvDropPct, remLossMin, hoursToClear, cutoffHour }
}

export function useAlcoholImpact() {
  const drinks             = ref(2)
  const weightKg           = ref(70)
  const sex                = ref<'male' | 'female'>('male')
  const sleepHour          = ref(23)
  const hoursSinceDrinking = ref(0)

  const result = computed(() =>
    calculateAlcoholImpact(
      drinks.value,
      weightKg.value,
      sex.value,
      sleepHour.value,
      hoursSinceDrinking.value,
    )
  )

  return { drinks, weightKg, sex, sleepHour, hoursSinceDrinking, result }
}
