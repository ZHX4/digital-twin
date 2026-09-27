from __future__ import annotations

from collections.abc import Sequence
from statistics import mean, pstdev


def standardized_shift(reference: Sequence[float], current: Sequence[float]) -> float:
    if not reference or not current:
        return 0.0
    mu = mean(reference)
    sigma = pstdev(reference) or 1e-6
    return round(abs(mean(current) - mu) / sigma, 5)


def distribution_shift_report(reference: dict[str, Sequence[float]], current: dict[str, Sequence[float]],
                              threshold: float = 0.75) -> dict:
    scores = {}
    for feature in sorted(set(reference) & set(current)):
        scores[feature] = standardized_shift(reference[feature], current[feature])
    aggregate = mean(scores.values()) if scores else 0.0
    return {
        "feature_scores": scores,
        "aggregate_score": round(aggregate, 5),
        "ood_flag": bool(aggregate > threshold),
        "threshold": threshold,
        "interpretation": "Synthetic covariate-shift diagnostic; not an empirical domain detector.",
    }


def conformal_interval(values: Sequence[float], alpha: float = 0.10) -> dict[str, float]:
    if not values:
        return {"lower": 0.0, "upper": 0.0, "coverage_target": 1.0 - alpha}
    values = sorted(values)
    lo = values[max(0, int((alpha / 2) * len(values)))]
    hi = values[min(len(values) - 1, int((1 - alpha / 2) * len(values)))]
    return {"lower": round(lo, 5), "upper": round(hi, 5), "coverage_target": round(1.0 - alpha, 5)}
