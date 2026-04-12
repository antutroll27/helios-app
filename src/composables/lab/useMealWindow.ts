import { ref, computed } from 'vue'

export type MealWindowResult =
  | { valid: false; error: string }
  | {
      valid: true
      windowHours: number
      hoursBeforeSleep: number
      score: number
      earlyTRF: boolean
      glucoseBenefit: string | null
    }

export function calculateMealWindow(
  firstMealHour: number,   // decimal, e.g. 8.0
  lastMealHour: number,    // decimal, e.g. 20.5
  sleepHour: number        // decimal, e.g. 23.0
): MealWindowResult {
  const invalidWindow      = lastMealHour <= firstMealHour
  const invalidSleepOrder  = sleepHour <= lastMealHour
  if (invalidWindow || invalidSleepOrder) {
    return { valid: false, error: 'Use same-day times: first meal < last meal < sleep time' }
  }

  const windowHours      = lastMealHour - firstMealHour
  const hoursBeforeSleep = sleepHour - lastMealHour
  const earlyTRF         = firstMealHour <= 9 && lastMealHour <= 14

  const score =
    (windowHours <= 10 ? 40 : windowHours <= 12 ? 25 : windowHours <= 14 ? 10 : 0) +
    (firstMealHour >= 7 && firstMealHour <= 9 ? 30 : firstMealHour <= 11 ? 15 : 0) +
    (hoursBeforeSleep >= 3 ? 30 : hoursBeforeSleep >= 2 ? 15 : 0)

  const glucoseBenefit = windowHours <= 10 ? '+10–15% glucose tolerance (Manoogian 2022)' : null

  return { valid: true, windowHours, hoursBeforeSleep, score, earlyTRF, glucoseBenefit }
}

export function useMealWindow() {
  const firstMealHour = ref(8)
  const lastMealHour  = ref(18)
  const sleepHour     = ref(23)

  const result = computed(() =>
    calculateMealWindow(firstMealHour.value, lastMealHour.value, sleepHour.value)
  )

  return { firstMealHour, lastMealHour, sleepHour, result }
}
