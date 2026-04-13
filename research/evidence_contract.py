from dataclasses import dataclass
from typing import Literal

EvidenceTier = Literal["A", "B", "C"]


@dataclass(frozen=True)
class EvidenceProfile:
    evidence_tier: EvidenceTier
    effect_summary: str
    population_summary: str
    main_caveat: str
    uncertainty_factors: list[str]
    claim_boundary: str

    def __post_init__(self) -> None:
        if self.evidence_tier not in {"A", "B", "C"}:
            raise ValueError("evidence_tier must be one of: A, B, C")

    def as_dict(self) -> dict:
        return {
            "evidence_tier": self.evidence_tier,
            "effect_summary": self.effect_summary,
            "population_summary": self.population_summary,
            "main_caveat": self.main_caveat,
            "uncertainty_factors": list(self.uncertainty_factors),
            "claim_boundary": self.claim_boundary,
        }


def merge_evidence(payload: dict, profile: EvidenceProfile) -> dict:
    merged = dict(payload)
    merged["evidence_profile"] = profile.as_dict()
    return merged
