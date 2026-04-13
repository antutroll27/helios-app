export type EvidenceTier = 'A' | 'B' | 'C'

export interface EvidenceProfile {
  evidenceTier: EvidenceTier
  effectSummary: string
  populationSummary: string
  mainCaveat: string
  uncertaintyFactors: string[]
  claimBoundary: string
}

function cleanText(value: string, fieldName: string): string {
  const cleaned = value.trim()
  if (!cleaned) {
    throw new Error(`${fieldName} must not be blank`)
  }
  return cleaned
}

export function buildEvidenceProfile(profile: EvidenceProfile): EvidenceProfile {
  return {
    evidenceTier: profile.evidenceTier,
    effectSummary: cleanText(profile.effectSummary, 'effectSummary'),
    populationSummary: cleanText(profile.populationSummary, 'populationSummary'),
    mainCaveat: cleanText(profile.mainCaveat, 'mainCaveat'),
    uncertaintyFactors: [...profile.uncertaintyFactors],
    claimBoundary: cleanText(profile.claimBoundary, 'claimBoundary'),
  }
}
