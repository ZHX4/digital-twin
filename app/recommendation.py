from __future__ import annotations

import math
from statistics import mean

from .models import PATHWAYS, CampResult, Evidence, PathwayPosterior, Recommendation


def _softmax(scores: dict[str, float], temperature: float) -> dict[str, float]:
    t = max(0.08, temperature)
    m = max(scores.values())
    exps = {k: math.exp((v - m) / t) for k, v in scores.items()}
    z = sum(exps.values()) or 1.0
    return {k: v / z for k, v in exps.items()}


def entropy(probs: dict[str, float]) -> float:
    return -sum(p * math.log(max(p, 1e-12)) for p in probs.values())


def recommend(age: int, capabilities: dict[str, float], uncertainties: dict[str, float], interests: dict[str, float],
              evidence: list[Evidence], camps: list[CampResult], mentorship: float, exploration: float,
              market: dict[str, dict[str, float]] | None = None, genomic_weight: float = 0.0,
              genomic_latents: dict[str, float] | None = None) -> Recommendation:
    raw: dict[str, float] = {}
    for path, domains in PATHWAYS.items():
        cap = mean(capabilities[d] for d in domains)
        interest = mean(interests.get(d, 0.5) for d in domains)
        unc = mean(uncertainties.get(d, 0.3) for d in domains)
        ev = [e.observed_mastery * e.confidence for e in evidence if e.domain in domains]
        evidence_score = mean(ev) if ev else cap
        camp_scores = [c.posterior_score for c in camps if c.domain in domains]
        camp_score = mean(camp_scores) if camp_scores else cap
        market_score = mean(market.get(path, {}).get("demand", 0.5) for _ in [0]) if market else 0.5
        genomic = mean(genomic_latents[d] for d in domains) if genomic_latents else cap
        raw[path] = (0.34 * cap + 0.19 * interest + 0.18 * evidence_score + 0.12 * camp_score
            + 0.07 * mentorship + 0.05 * market_score + genomic_weight * (genomic - 0.5) - 0.11 * unc)
    temp = 1.25 if age < 7 else 0.92 if age < 10 else 0.62 if age < 13 else 0.38
    probs = _softmax(raw, temp)
    path = max(probs, key=lambda name: probs[name])
    h = entropy(probs)
    normalized_h = h / math.log(max(2, len(probs)))
    uncertainty = 0.50 * normalized_h + 0.50 * mean(uncertainties[d] for d in PATHWAYS[path])
    exploration_priority = min(1.0, 0.55 * exploration + 0.75 * normalized_h + (0.12 if age < 10 else 0.0))
    flags = []
    if age < 9: flags += ["NO_IRREVERSIBLE_DECISION", "DEVELOPMENTAL_STAGE_NOT_FINAL"]
    if probs[path] < 0.30: flags.append("HUMAN_REVIEW_REQUIRED")
    if exploration_priority > 0.62: flags.append("KEEP_MULTIPLE_PATHWAYS_OPEN")
    if normalized_h > 0.62: flags.append("HIGH_POSTERIOR_ENTROPY")
    rationale = [
        f"Current leading posterior is {probs[path]:.2f}; decision remains advisory and reversible.",
        f"Posterior entropy is {normalized_h:.2f}, indicating {'high' if normalized_h > 0.6 else 'moderate' if normalized_h > 0.35 else 'lower'} uncertainty.",
        "The genomic contribution is bounded and can be switched off in ablation experiments.",
    ]
    return Recommendation(age=age, pathway=path, score=round(probs[path], 4), confidence=round(1.0 - uncertainty, 4),
        exploration_priority=round(exploration_priority, 4), contributing_domains={d: round(capabilities[d], 4) for d in PATHWAYS[path]},
        ranked_pathways={k: round(v, 4) for k, v in sorted(probs.items(), key=lambda kv: kv[1], reverse=True)},
        rationale=rationale, safety_flags=flags)


def pathway_posteriors(age: int, rec: Recommendation, evidence_strength: float) -> list[PathwayPosterior]:
    rows = []
    max_h = math.log(7)
    for path, p in rec.ranked_pathways.items():
        u = max(0.0, min(1.0, 1.0 - rec.confidence + (p < 0.35) * 0.10))
        rows.append(PathwayPosterior(age=age, pathway=path, probability=p, uncertainty=round(u, 4),
            entropy=round(min(1.0, -p * math.log(max(p, 1e-12)) / max_h), 4),
            evidence_strength=round(evidence_strength, 4),
            recommended_action=("explore" if p < max(rec.ranked_pathways.values()) * 0.86 else "continue_observation"),
            exploration_priority=rec.exploration_priority, contributing_domains=rec.contributing_domains if path == rec.pathway else {},
            rationale=rec.rationale, safety_flags=rec.safety_flags))
    return rows
