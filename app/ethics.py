from __future__ import annotations


def safety_assessment(age: int, confidence: float, posterior_entropy: float, exploration_priority: float,
                      genomic_weight: float, missingness: float = 0.0) -> dict:
    flags: list[str] = []
    if age < 9:
        flags += ["NO_IRREVERSIBLE_DECISION", "HUMAN_REVIEW_REQUIRED"]
    if confidence < 0.55:
        flags.append("HUMAN_REVIEW_REQUIRED")
    if posterior_entropy > 0.62:
        flags.append("KEEP_MULTIPLE_PATHWAYS_OPEN")
    if exploration_priority > 0.62:
        flags.append("EXPLORE_BEFORE_SPECIALIZATION")
    if genomic_weight > 0.10:
        flags.append("GENOMIC_WEIGHT_EXCEEDS_SAFE_SIMULATION_BOUND")
    if missingness > 0.30:
        flags.append("DATA_QUALITY_REVIEW")
    return {
        "decision_level": "advisory_only", "reversible": True, "flags": sorted(set(flags)),
        "requirements": [
            "human mentor oversight", "child agency increases with developmental capacity",
            "no exclusion on synthetic genomic prior alone", "periodic reassessment and appeal",
            "data minimization, purpose limitation and provenance", "counterfactual review before high-impact pathway changes",
        ],
    }
