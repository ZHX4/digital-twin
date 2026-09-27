from __future__ import annotations

import math
import random
from collections.abc import Iterable
from statistics import mean

from .models import AssessmentResult


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def irt_probability(theta: float, difficulty: float, discrimination: float = 1.15) -> float:
    return sigmoid(discrimination * (theta - difficulty))


def bkt_update(prior: float, correct: bool, learn: float = 0.14, slip: float = 0.08, guess: float = 0.20) -> float:
    prior = max(1e-4, min(0.9999, prior))
    if correct:
        p_correct = prior * (1 - slip) + (1 - prior) * guess
        posterior = prior * (1 - slip) / max(p_correct, 1e-9)
    else:
        p_incorrect = prior * slip + (1 - prior) * (1 - guess)
        posterior = prior * slip / max(p_incorrect, 1e-9)
    return max(0.0, min(1.0, posterior + (1 - posterior) * learn))


def adaptive_assessment(age: int, domain: str, mastery: float, uncertainty: float, rng: random.Random,
                        max_items: int = 12) -> AssessmentResult:
    """Synthetic IRT/CAT-style measurement with deterministic seeds."""
    theta_true = -3.0 + 6.0 * mastery
    theta = 0.0
    responses: list[bool] = []
    information = 0.0
    for _ in range(max_items):
        difficulty = max(-2.4, min(2.4, theta + rng.gauss(0, 0.55 * (0.7 + uncertainty))))
        p = irt_probability(theta_true, difficulty)
        correct = rng.random() < p
        responses.append(correct)
        info = 1.15 ** 2 * p * (1 - p)
        information += info
        pred = irt_probability(theta, difficulty)
        grad = 1.15 * ((1.0 if correct else 0.0) - pred)
        hess = -1.15 ** 2 * pred * (1 - pred) - 0.10
        theta = theta - grad / hess
        if len(responses) >= 5 and abs(grad) < 0.06:
            break
    se = 1.0 / math.sqrt(max(information, 1e-6))
    theta_norm = max(0.0, min(1.0, (theta + 3.0) / 6.0))
    return AssessmentResult(age=age, domain=domain, theta=round(theta_norm, 4),
        standard_error=round(min(1.0, se / 3.0), 4), accuracy=round(mean(responses), 4),
        items=len(responses), information_gain=round(min(1.0, information / 4.5), 4),
        instrument="synthetic_irt_cat_v1")


def reliability_bins(predictions: Iterable[float], outcomes: Iterable[float], bins: int = 10) -> list[dict[str, float]]:
    groups: list[list[tuple[float, float]]] = [[] for _ in range(bins)]
    for p, y in zip(predictions, outcomes):
        idx = min(bins - 1, int(max(0, min(0.999999, p)) * bins))
        groups[idx].append((p, y))
    rows = []
    for i, group in enumerate(groups):
        if not group:
            continue
        rows.append({"bin_low": round(i / bins, 3), "bin_high": round((i + 1) / bins, 3),
                     "mean_prediction": round(mean(p for p, _ in group), 4),
                     "empirical_rate": round(mean(y for _, y in group), 4), "count": len(group)})
    return rows


def brier_score(predictions: Iterable[float], outcomes: Iterable[float]) -> float:
    pairs = list(zip(predictions, outcomes))
    return mean((p - y) ** 2 for p, y in pairs) if pairs else 0.0


def expected_calibration_error(predictions: Iterable[float], outcomes: Iterable[float], bins: int = 10) -> float:
    rows = reliability_bins(predictions, outcomes, bins)
    n = sum(r["count"] for r in rows) or 1
    return sum((r["count"] / n) * abs(r["mean_prediction"] - r["empirical_rate"]) for r in rows)
