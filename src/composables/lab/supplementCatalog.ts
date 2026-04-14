export type SupplementGoal =
  | 'sleep_onset'
  | 'recovery_support'
  | 'stress_resilience'
  | 'jet_lag_support'
  | 'circadian_realignment'

export type TravelState = 'none' | 'eastbound_shift' | 'westbound_shift'
export type Chronotype = 'early' | 'intermediate' | 'late'
export type EvidenceTier = 'A' | 'B' | 'C'

export interface SupplementGoalOption {
  key: SupplementGoal
  label: string
  description: string
}

export interface SupplementCatalogEntry {
  key: 'melatonin' | 'magnesium' | 'ashwagandha' | 'glycine'
  name: string
  dose: string
  timing: string
  effect: string
  population: string
  caveat: string
  contraindications: readonly string[]
  clinicianDisclaimer: string
  evidenceTier: EvidenceTier
  goals: SupplementGoal[]
}

export const SUPPLEMENT_GOALS: readonly SupplementGoalOption[] = [
  {
    key: 'sleep_onset',
    label: 'Sleep onset',
    description: 'For difficulty falling asleep or settling at night',
  },
  {
    key: 'recovery_support',
    label: 'Recovery support',
    description: 'For lower recovery markers, short sleep, or sleep debt',
  },
  {
    key: 'stress_resilience',
    label: 'Stress resilience',
    description: 'For elevated stress load or a higher-adaptation phase',
  },
  {
    key: 'jet_lag_support',
    label: 'Jet lag support',
    description: 'For travel-related sleep disruption and time-zone shifts',
  },
  {
    key: 'circadian_realignment',
    label: 'Circadian realignment',
    description: 'For phase advance / phase delay support after schedule shifts',
  },
] as const

export const SUPPLEMENT_CATALOG: readonly SupplementCatalogEntry[] = [
  {
    key: 'melatonin',
    name: 'Melatonin',
    dose: '0.3-1 mg',
    timing: '30-90 min before target bedtime',
    effect: 'Supports sleep onset and circadian phase shifting when timing is aligned to the goal.',
    population: 'Adults with jet lag, delayed sleep timing, or schedule-shifted sleep onset.',
    caveat: 'Timing matters more than dose; larger doses can increase next-day grogginess without improving phase shift.',
    contraindications: [
      'Use extra caution with pregnancy, epilepsy, autoimmune disease, or sedating medications unless a clinician has okayed it.',
    ],
    clinicianDisclaimer: 'Discuss with a clinician if you take prescription sleep medicines, anticoagulants, anticonvulsants, or immunosuppressants.',
    evidenceTier: 'B',
    goals: ['sleep_onset', 'jet_lag_support', 'circadian_realignment'],
  },
  {
    key: 'magnesium',
    name: 'Magnesium glycinate',
    dose: '200-400 mg elemental',
    timing: '30-60 min before bed',
    effect: 'May support sleep depth and recovery, especially when sleep debt or low intake is present.',
    population: 'Adults with short sleep, lower sleep quality, or low dietary magnesium intake.',
    caveat: 'Effects are usually smaller in well-nourished adults with already-healthy sleep metrics.',
    contraindications: [
      'Avoid unsupervised use with kidney disease or significant electrolyte problems.',
    ],
    clinicianDisclaimer: 'Check with a clinician if you have kidney disease or take medications that affect magnesium absorption or clearance.',
    evidenceTier: 'B',
    goals: ['sleep_onset', 'recovery_support'],
  },
  {
    key: 'ashwagandha',
    name: 'Ashwagandha',
    dose: '300 mg extract',
    timing: 'With food, often earlier in the day',
    effect: 'May help with stress adaptation and cortisol-related sleep disruption in stressed adults.',
    population: 'Adults with a higher stress load and lower recovery signaling.',
    caveat: 'Benefits are most plausible when the main issue is stress rather than sleep mechanics alone.',
    contraindications: [
      'Avoid if pregnant, breastfeeding, or if you have thyroid disease, autoimmune disease, or liver concerns unless a clinician has reviewed it.',
    ],
    clinicianDisclaimer: 'Discuss with a clinician if you use thyroid medication, sedatives, or have an autoimmune condition.',
    evidenceTier: 'B',
    goals: ['stress_resilience', 'recovery_support'],
  },
  {
    key: 'glycine',
    name: 'Glycine',
    dose: '3 g',
    timing: '30-60 min before bed',
    effect: 'May support sleep onset and perceived sleep quality by modestly lowering core temperature.',
    population: 'Adults whose main issue is falling asleep rather than recovery debt.',
    caveat: 'This is a narrower sleep-onset tool and should not be expected to correct broader recovery problems by itself.',
    contraindications: [
      'Use caution if you have complex medical issues or are using multiple sleep aids.',
    ],
    clinicianDisclaimer: 'Discuss with a clinician if you are pregnant, using sedatives, or have a chronic medical condition.',
    evidenceTier: 'B',
    goals: ['sleep_onset'],
  },
] as const
