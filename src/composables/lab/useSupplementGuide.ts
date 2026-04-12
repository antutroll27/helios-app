import { computed } from 'vue'
import { useBiometricsStore } from '@/stores/biometrics'

export interface RankedSupplement {
  key:       'magnesium' | 'ashwagandha' | 'glycine'
  name:      string
  dose:      string
  timing:    string
  effect:    string
  caveat:    string
  citation:  string
  grade:     'A+' | 'A' | 'B'
  score:     number     // 0–3
  note:      string     // personalised biometric note — never empty
  isTopPick: boolean
}

// ── Static supplement definitions ────────────────────────────────────────────
const SUPPLEMENTS: Omit<RankedSupplement, 'score' | 'note' | 'isTopPick'>[] = [
  {
    key:      'magnesium',
    name:     'Magnesium Glycinate',
    dose:     '300–400 mg elemental',
    timing:   '30–60 min before bed',
    effect:   '+16 min TST, +deep sleep quality',
    caveat:   'Effect strongest in adults with low dietary Mg or insomnia; smaller in healthy well-nourished adults.',
    citation: 'Abbasi 2012, Mah 2021 BMC',
    grade:    'A',
  },
  {
    key:      'ashwagandha',
    name:     'Ashwagandha KSM-66',
    dose:     '300 mg KSM-66 extract',
    timing:   'Morning with food',
    effect:   '−15% cortisol, +11% HRV in stressed adults',
    caveat:   'Benefits most pronounced under high perceived stress. Full effect takes 8–12 weeks.',
    citation: 'Chandrasekhar 2012, Pratte 2014',
    grade:    'A',
  },
  {
    key:      'glycine',
    name:     'Glycine',
    dose:     '3 g',
    timing:   '30 min before bed',
    effect:   '−10 min latency, −0.1–0.2°C core temp',
    caveat:   'Mechanism well-understood (peripheral vasodilation lowers core temp). Fewest side effects.',
    citation: 'Bannai 2012',
    grade:    'A',
  },
]

// ── Scoring helpers ──────────────────────────────────────────────────────────
function scoreMagnesium(
  sleepScore: number | null,
  sleepHours: number | null,
): { score: number; note: string } {
  const hoursLow = sleepHours != null && sleepHours < 7.0
  const scoreLow = sleepScore != null && sleepScore < 75
  const score    = (hoursLow ? 2 : 0) + (scoreLow ? 1 : 0)

  if (hoursLow && scoreLow) {
    return { score, note: `Your ${sleepHours!.toFixed(1)}h avg is below the 7h threshold — Mg supports slow-wave sleep depth · sleep score ${sleepScore} also flags low recovery` }
  }
  if (hoursLow) {
    return { score, note: `Your ${sleepHours!.toFixed(1)}h avg is below the 7h threshold — Mg supports slow-wave sleep depth` }
  }
  if (scoreLow) {
    return { score, note: `Sleep score ${sleepScore} suggests reduced recovery — Mg glycinate supports deep sleep quality` }
  }
  return { score: 0, note: 'Your sleep metrics look healthy — Mg becomes more relevant if total sleep drops below 7h or sleep score below 75' }
}

function scoreAshwagandha(
  hrv:        number | null,
  sleepScore: number | null,
): { score: number; note: string } {
  const hrvLow   = hrv != null && hrv < 40
  const scoreLow = sleepScore != null && sleepScore < 75
  const score    = (hrvLow ? 2 : 0) + (scoreLow ? 1 : 0)

  if (hrvLow && scoreLow) {
    return { score, note: `HRV ${hrv!.toFixed(1)}ms suggests elevated stress load — KSM-66 reduces cortisol ~15% (Chandrasekhar 2012) · sleep score also supports prioritising cortisol reduction` }
  }
  if (hrvLow) {
    return { score, note: `HRV ${hrv!.toFixed(1)}ms suggests elevated stress load — KSM-66 reduces cortisol ~15% (Chandrasekhar 2012)` }
  }
  if (scoreLow) {
    return { score, note: `Sleep score ${sleepScore} suggests stress-related sleep disruption — consider Ashwagandha` }
  }
  return { score: 0, note: 'Your HRV is in a good range — Ashwagandha becomes more relevant if HRV drops below 40ms' }
}

function scoreGlycine(
  sleepScore: number | null,
  sleepHours: number | null,
): { score: number; note: string } {
  const scoreLow = sleepScore != null && sleepScore < 72
  const hoursLow = sleepHours != null && sleepHours < 6.5
  const score    = (scoreLow ? 1 : 0) + (hoursLow ? 1 : 0)

  if (scoreLow && hoursLow) {
    return { score, note: `Sleep score ${sleepScore} suggests onset or fragmentation — glycine lowers core body temperature · combined with short sleep (${sleepHours!.toFixed(1)}h), sleep onset is the likely bottleneck` }
  }
  if (scoreLow) {
    return { score, note: `Sleep score ${sleepScore} suggests onset or fragmentation — glycine lowers core body temperature` }
  }
  if (hoursLow) {
    return { score, note: `Short sleep (${sleepHours!.toFixed(1)}h) may reflect slow sleep onset — glycine reduces latency ~10 min` }
  }
  return { score: 0, note: 'Sleep onset appears normal — consider Glycine if sleep score drops below 72 or nightly hours below 6.5h' }
}

// ── Pure function (injectable for tests) ─────────────────────────────────────
export function scoreSupplements(
  hrv:        number | null,
  sleepScore: number | null,
  sleepHours: number | null,
): RankedSupplement[] {
  const mg    = scoreMagnesium(sleepScore, sleepHours)
  const ashwa = scoreAshwagandha(hrv, sleepScore)
  const gly   = scoreGlycine(sleepScore, sleepHours)

  const scored: RankedSupplement[] = [
    { ...SUPPLEMENTS[0], ...mg,    isTopPick: false },
    { ...SUPPLEMENTS[1], ...ashwa, isTopPick: false },
    { ...SUPPLEMENTS[2], ...gly,   isTopPick: false },
  ]

  // Sort descending by score; stable (magnesium > ashwagandha > glycine on tie)
  scored.sort((a, b) => b.score - a.score)
  scored[0].isTopPick = true

  return scored
}

// ── Composable (store-aware) ──────────────────────────────────────────────────
export function useSupplementGuide() {
  const biometrics = useBiometricsStore()

  const hasPersonalization = computed(() =>
    biometrics.avgHRV != null && biometrics.avgSleepScore != null
  )

  const rankedSupplements = computed(() =>
    scoreSupplements(biometrics.avgHRV, biometrics.avgSleepScore, biometrics.avgTotalSleepH)
  )

  return { rankedSupplements, hasPersonalization }
}
