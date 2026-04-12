import { ref, computed } from 'vue'

export type Chronotype = 'early' | 'mid' | 'late'

export function calculateExercisePhaseShift(
  hour: number,
  chronotype: Chronotype
): { shiftMin: number; morningMetabolicBonus: boolean; label: string } {
  // Youngstedt 2019 phase response curve for exercise
  const baseShift =
    hour <= 8  ?  60 :   // morning: advance
    hour <= 16 ?  45 :   // afternoon: moderate advance
    hour <= 22 ? -45 :   // evening: delay
    0

  // Thomas 2020: late chronotypes get ~1.5x shift from morning exercise;
  // early chronotypes get ~0.5x (already advanced, less to shift)
  const multiplier =
    chronotype === 'late'  && hour <= 10 ? 1.5 :
    chronotype === 'early' && hour <= 10 ? 0.5 : 1.0

  const shiftMin = Math.round(baseShift * multiplier)
  const morningMetabolicBonus = hour <= 10  // Sato 2019 clock gene expression
  const label = shiftMin > 0
    ? `+${shiftMin} min advance`
    : shiftMin < 0
      ? `${shiftMin} min delay`
      : 'Minimal phase effect'

  return { shiftMin, morningMetabolicBonus, label }
}

export function useExerciseTiming() {
  const hour       = ref(7)
  const chronotype = ref<Chronotype>('mid')

  const result = computed(() =>
    calculateExercisePhaseShift(hour.value, chronotype.value)
  )

  return { hour, chronotype, result }
}
