import { ref, computed, onUnmounted } from 'vue'

export type NapCalcInput = {
  hoursAwake: number
  sleepDebtMin: number
  currentHour: number   // injected — not read from clock inside pure fn
}

export type NapCalcResult = {
  duration: number
  durationLabel: string
  idealStart: string
  nightPenalty: number   // % night sleep efficiency lost (0 if before 3PM)
  boostMinutes: number   // alert boost in minutes
  inWindow: boolean      // true if 13:00–15:00
  coffeeNap: boolean
}

export function calculateNapRecommendation(input: NapCalcInput): NapCalcResult {
  const { hoursAwake, sleepDebtMin, currentHour } = input
  const inWindow = currentHour >= 13 && currentHour <= 15

  let duration = 26
  let durationLabel = '26 min (NASA sweet spot)'
  if (sleepDebtMin > 60)    { duration = 90; durationLabel = '90 min (full cycle — significant debt)' }
  else if (hoursAwake < 5)  { duration = 10; durationLabel = '10 min (too early for longer)' }

  const idealStart = currentHour < 13 ? '13:00' : currentHour > 15 ? 'now (expect some night impact)' : 'now'
  const nightPenalty = currentHour > 15 ? Math.round((currentHour - 15) * 4) : 0
  const boostMinutes = duration === 10 ? 120 : duration === 26 ? 180 : 480
  const coffeeNap = duration <= 26

  return { duration, durationLabel, idealStart, nightPenalty, boostMinutes, inWindow, coffeeNap }
}

export function useNapCalc() {
  const hoursAwake   = ref(6)
  const sleepDebtMin = ref(0)
  // Refreshed every minute so the 13:00–15:00 window and penalty calculations
  // stay accurate during extended page sessions (critical at the 15:00 boundary)
  const currentHour  = ref(new Date().getHours())
  const timer = setInterval(() => {
    currentHour.value = new Date().getHours()
  }, 60_000)
  onUnmounted(() => clearInterval(timer))

  const result = computed(() =>
    calculateNapRecommendation({
      hoursAwake: hoursAwake.value,
      sleepDebtMin: sleepDebtMin.value,
      currentHour: currentHour.value,
    })
  )

  return { hoursAwake, sleepDebtMin, result }
}
