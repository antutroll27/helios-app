import { computed, toValue } from 'vue'
import type { MaybeRefOrGetter } from 'vue'
import { useBiometricsStore } from '@/stores/biometrics'
import { useJetLagStore } from '@/stores/jetlag'
import { useUserStore } from '@/stores/user'
import {
  SUPPLEMENT_CATALOG,
  SUPPLEMENT_GOALS,
  type Chronotype,
  type EvidenceTier,
  type SupplementCatalogEntry,
  type SupplementGoal,
  type TravelState,
} from './supplementCatalog'

export type {
  Chronotype,
  EvidenceTier,
  SupplementGoal,
  TravelState,
} from './supplementCatalog'

export interface SupplementGuideContext {
  goal: SupplementGoal
  chronotype: Chronotype
  travelState: TravelState
  hrv: number | null
  sleepScore: number | null
  totalSleepHours: number | null
}

export interface RankedSupplement extends SupplementCatalogEntry {
  score: number
  note: string
  isTopPick: boolean
}

const GOAL_TIE_BREAK_ORDER: Record<SupplementGoal, ReadonlyArray<SupplementCatalogEntry['key']>> = {
  sleep_onset: ['glycine', 'melatonin', 'magnesium', 'ashwagandha'],
  recovery_support: ['magnesium', 'ashwagandha', 'glycine', 'melatonin'],
  stress_resilience: ['ashwagandha', 'magnesium', 'glycine', 'melatonin'],
  jet_lag_support: ['melatonin', 'magnesium', 'glycine', 'ashwagandha'],
  circadian_realignment: ['melatonin', 'magnesium', 'glycine', 'ashwagandha'],
}

function clampScore(score: number): number {
  return Math.max(0, Math.min(5, score))
}

function isLowHrv(context: SupplementGuideContext): boolean {
  return context.hrv != null && context.hrv < 40
}

function isLowSleepScore(context: SupplementGuideContext): boolean {
  return context.sleepScore != null && context.sleepScore < 75
}

function isShortSleep(context: SupplementGuideContext): boolean {
  return context.totalSleepHours != null && context.totalSleepHours < 6.5
}

function hasRecoverySignal(context: SupplementGuideContext): boolean {
  return isLowHrv(context) || isLowSleepScore(context) || isShortSleep(context)
}

function hasSleepOnsetSignal(context: SupplementGuideContext): boolean {
  return isLowSleepScore(context) || isShortSleep(context)
}

function hasCircadianShift(context: SupplementGuideContext): boolean {
  return context.travelState !== 'none' || context.goal === 'circadian_realignment' || context.goal === 'jet_lag_support'
}

function buildMelatoninNote(context: SupplementGuideContext, score: number): string {
  if (context.goal === 'circadian_realignment' && context.travelState === 'eastbound_shift' && context.chronotype === 'late') {
    return 'Eastbound phase advance plus a late chronotype makes melatonin the most relevant circadian tool here.'
  }
  if (context.goal === 'jet_lag_support' && context.travelState !== 'none') {
    return context.travelState === 'eastbound_shift'
      ? 'Travel-related phase advance makes melatonin more relevant for resetting timing after an eastbound shift.'
      : 'Travel-related timing disruption still makes melatonin relevant, but westbound shifts usually lean less heavily on it.'
  }
  if (context.goal === 'sleep_onset') {
    return 'Melatonin may help sleep onset, but it is most useful when bedtime timing itself needs support.'
  }
  if (score > 0 && hasCircadianShift(context)) {
    return 'Circadian timing inputs make melatonin more relevant than a generic sleep aid.'
  }
  return 'No strong circadian signal is present, so melatonin stays a lower-priority wellness option.'
}

function buildMagnesiumNote(context: SupplementGuideContext, score: number): string {
  if (isLowHrv(context) && (isLowSleepScore(context) || isShortSleep(context))) {
    return 'Lower HRV plus shorter or lower-quality sleep makes magnesium the clearest recovery-oriented option.'
  }
  if (isLowHrv(context)) {
    return 'Lower HRV makes magnesium more relevant as a recovery-support option.'
  }
  if (isLowSleepScore(context) || isShortSleep(context)) {
    return 'Short sleep or lower sleep quality keeps magnesium relevant when recovery debt is part of the picture.'
  }
  if (score > 0) {
    return 'Magnesium stays relevant when recovery markers start to drift down.'
  }
  return 'Recovery markers look reasonably steady, so magnesium remains a general wellness option rather than a priority.'
}

function buildAshwagandhaNote(context: SupplementGuideContext, score: number): string {
  if (context.goal === 'stress_resilience' && isLowHrv(context)) {
    return 'Stress resilience plus lower HRV makes ashwagandha more relevant than a pure sleep aid.'
  }
  if (isLowHrv(context)) {
    return 'Lower HRV suggests a stress-adaptation pattern where ashwagandha may be more relevant.'
  }
  if (context.goal === 'stress_resilience') {
    return 'Ashwagandha is the most stress-oriented option here, but it is still framed as general wellness support.'
  }
  if (score > 0) {
    return 'Stress-adaptation inputs give ashwagandha some relevance, but it remains secondary to stronger goal matches.'
  }
  return 'There is no strong stress signal in the current inputs, so ashwagandha stays lower priority.'
}

function buildGlycineNote(context: SupplementGuideContext, score: number): string {
  if (context.goal === 'sleep_onset' && (isLowSleepScore(context) || isShortSleep(context))) {
    return 'Sleep-onset framing fits glycine best when falling asleep is the main bottleneck.'
  }
  if (context.goal === 'sleep_onset') {
    return 'Glycine is the most onset-oriented option here, especially when falling asleep is the main issue.'
  }
  if (score > 0) {
    return 'Glycine can help with sleep onset, but it does not address recovery debt as strongly as magnesium.'
  }
  return 'Without a clear sleep-onset problem, glycine stays a lower-priority wellness option.'
}

function scoreMelatonin(context: SupplementGuideContext): { score: number; note: string } {
  let score = 0

  if (context.travelState === 'eastbound_shift') score += 3
  if (context.travelState === 'westbound_shift') score += 2
  if (context.goal === 'circadian_realignment' && context.travelState !== 'none') score += 2
  if (context.goal === 'jet_lag_support' && context.travelState !== 'none') score += 2
  if (context.goal === 'sleep_onset' && hasSleepOnsetSignal(context)) score += 1
  if (context.chronotype === 'late' && context.travelState === 'eastbound_shift') score += 1
  if ((isLowSleepScore(context) || isShortSleep(context)) && context.travelState !== 'none') score += 1

  return {
    score: clampScore(score),
    note: buildMelatoninNote(context, score),
  }
}

function scoreMagnesium(context: SupplementGuideContext): { score: number; note: string } {
  let score = 0

  if (isLowHrv(context)) score += 2
  if (isLowSleepScore(context)) score += 2
  if (isShortSleep(context)) score += 1
  if (context.goal === 'recovery_support' && hasRecoverySignal(context)) score += 2
  if (context.goal === 'sleep_onset' && hasSleepOnsetSignal(context)) score += 1

  return {
    score: clampScore(score),
    note: buildMagnesiumNote(context, score),
  }
}

function scoreAshwagandha(context: SupplementGuideContext): { score: number; note: string } {
  let score = 0

  if (isLowHrv(context)) score += 2
  if (isLowSleepScore(context) && isLowHrv(context)) score += 1
  if (context.goal === 'stress_resilience' && isLowHrv(context)) score += 2
  if (context.goal === 'recovery_support' && isLowHrv(context)) score += 1

  return {
    score: clampScore(score),
    note: buildAshwagandhaNote(context, score),
  }
}

function scoreGlycine(context: SupplementGuideContext): { score: number; note: string } {
  let score = 0

  if (isLowSleepScore(context)) score += 1
  if (isShortSleep(context)) score += 1
  if (context.goal === 'sleep_onset' && hasSleepOnsetSignal(context)) score += 2

  return {
    score: clampScore(score),
    note: buildGlycineNote(context, score),
  }
}

function createRankedSupplement(
  supplement: SupplementCatalogEntry,
  scoreData: { score: number; note: string },
): RankedSupplement {
  return {
    ...supplement,
    score: scoreData.score,
    note: scoreData.note,
    isTopPick: false,
  }
}

export function scoreSupplements(context: SupplementGuideContext): RankedSupplement[] {
  const tieBreakOrder = GOAL_TIE_BREAK_ORDER[context.goal]
  const scored = SUPPLEMENT_CATALOG.map((supplement) => {
    switch (supplement.key) {
      case 'melatonin':
        return createRankedSupplement(supplement, scoreMelatonin(context))
      case 'magnesium':
        return createRankedSupplement(supplement, scoreMagnesium(context))
      case 'ashwagandha':
        return createRankedSupplement(supplement, scoreAshwagandha(context))
      case 'glycine':
        return createRankedSupplement(supplement, scoreGlycine(context))
    }
  })

  const ranked = scored
    .map((supplement, index) => ({ supplement, index }))
    .sort((left, right) => {
      if (right.supplement.score !== left.supplement.score) {
        return right.supplement.score - left.supplement.score
      }
      const leftPriority = tieBreakOrder.indexOf(left.supplement.key)
      const rightPriority = tieBreakOrder.indexOf(right.supplement.key)

      if (leftPriority !== rightPriority) {
        return leftPriority - rightPriority
      }

      return left.index - right.index
    })
    .map(({ supplement }) => supplement)

  if (ranked.length > 0 && ranked[0].score > 0) {
    ranked[0].isTopPick = true
  }

  return ranked
}

export function useSupplementGuide(goalInput: MaybeRefOrGetter<SupplementGoal> = 'sleep_onset') {
  const biometrics = useBiometricsStore()
  const user = useUserStore()
  const jetlag = useJetLagStore()

  const goal = computed(() => toValue(goalInput))

  const travelState = computed<TravelState>(() => {
    if (!jetlag.tripInput || jetlag.totalShiftHours === 0) return 'none'
    return jetlag.shiftDirection === 'advance' ? 'eastbound_shift' : 'westbound_shift'
  })

  const context = computed<SupplementGuideContext>(() => ({
    goal: goal.value,
    chronotype: user.chronotype,
    travelState: travelState.value,
    hrv: biometrics.avgHRV,
    sleepScore: biometrics.avgSleepScore,
    totalSleepHours: biometrics.avgTotalSleepH,
  }))

  const rankedSupplements = computed(() => scoreSupplements(context.value))
  const usesBiometrics = computed(() =>
    context.value.hrv != null ||
    context.value.sleepScore != null ||
    context.value.totalSleepHours != null
  )
  const usesTravelContext = computed(() => context.value.travelState !== 'none')
  const hasPersonalization = computed(() =>
    usesBiometrics.value || usesTravelContext.value
  )

  return {
    SUPPLEMENT_GOALS,
    context,
    goal,
    hasPersonalization,
    usesBiometrics,
    usesTravelContext,
    rankedSupplements,
  }
}
