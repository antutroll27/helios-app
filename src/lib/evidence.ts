export type EvidenceTier = 'A' | 'B' | 'C'

export interface EvidenceProfile {
  evidenceTier: EvidenceTier
  effectSummary: string
  populationSummary: string
  mainCaveat: string
  uncertaintyFactors: string[]
  claimBoundary: string
}

export function buildEvidenceProfile(profile: EvidenceProfile): EvidenceProfile {
  return {
    ...profile,
    uncertaintyFactors: [...profile.uncertaintyFactors],
  }
}
