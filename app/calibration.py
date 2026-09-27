from __future__ import annotations

from collections.abc import Iterable, Sequence

from .psychometrics import expected_calibration_error, reliability_bins


def multiclass_brier(
    probability_rows: Sequence[dict[str, float]],
    outcomes: Sequence[str],
    classes: Sequence[str],
) -> float:
    if not probability_rows or not outcomes:
        return 0.0
    total = 0.0
    for probs, outcome in zip(probability_rows, outcomes):
        total += sum((probs.get(cls, 0.0) - float(cls == outcome)) ** 2 for cls in classes)
    return total / len(outcomes)


def evaluate(
    predictions: Iterable[float],
    outcomes: Iterable[float],
) -> dict[str, float | list[dict[str, float]]]:
    pred = list(predictions)
    outcome = list(outcomes)
    return {
        "brier": round(sum((p - y) ** 2 for p, y in zip(pred, outcome)) / len(outcome), 6) if outcome else 0.0,
        "ece": round(expected_calibration_error(pred, outcome), 6),
        "reliability": reliability_bins(pred, outcome),
    }


def evaluate_multiclass(
    probability_rows: Sequence[dict[str, float]],
    outcomes: Sequence[str],
    classes: Sequence[str],
) -> dict[str, float | list[dict[str, float]]]:
    if not probability_rows or not outcomes:
        return {"brier_multiclass": 0.0, "ece_top_class": 0.0, "reliability": []}
    top_probs: list[float] = []
    top_correct: list[float] = []
    for probs, outcome in zip(probability_rows, outcomes):
        top_class = max(probs, key=lambda name: probs[name])
        top_probs.append(probs[top_class])
        top_correct.append(float(top_class == outcome))
    return {
        "brier_multiclass": round(multiclass_brier(probability_rows, outcomes, classes), 6),
        "ece_top_class": round(expected_calibration_error(top_probs, top_correct), 6),
        "reliability": reliability_bins(top_probs, top_correct),
    }


def temperature_scale(probability_rows: Sequence[dict[str, float]], temperature: float) -> list[dict[str, float]]:
    import math

    t = max(0.05, float(temperature))
    scaled: list[dict[str, float]] = []
    for probs in probability_rows:
        logits = {name: math.log(max(1e-12, prob)) / t for name, prob in probs.items()}
        maximum = max(logits.values())
        exps = {name: math.exp(value - maximum) for name, value in logits.items()}
        normalizer = sum(exps.values()) or 1.0
        scaled.append({name: value / normalizer for name, value in exps.items()})
    return scaled


def fit_temperature(
    probability_rows: Sequence[dict[str, float]],
    outcomes: Sequence[str],
    classes: Sequence[str],
) -> float:
    if not probability_rows or not outcomes:
        return 1.0
    best_temperature = 1.0
    best_brier = float("inf")
    # Grid search is deterministic and auditable for this synthetic calibration stage.
    for step in range(8, 81):
        temperature = step / 20.0
        score = multiclass_brier(temperature_scale(probability_rows, temperature), outcomes, classes)
        if score < best_brier:
            best_brier = score
            best_temperature = temperature
    return best_temperature
