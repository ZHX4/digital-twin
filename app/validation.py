from __future__ import annotations

import math
import random
from collections.abc import Sequence
from statistics import mean
from typing import Any


def mean_ci(values: Sequence[float], confidence: float = 0.95) -> dict[str, float]:
    """Deterministic normal-approximation CI for a sample mean."""
    if not values:
        return {"mean": 0.0, "lower": 0.0, "upper": 0.0, "n": 0.0}
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    n = len(values)
    mu = mean(values)
    if n == 1:
        return {"mean": round(mu, 6), "lower": round(mu, 6), "upper": round(mu, 6), "n": 1.0}
    variance = sum((x - mu) ** 2 for x in values) / (n - 1)
    standard_error = math.sqrt(variance / n)
    z = 1.959963984540054 if confidence == 0.95 else _normal_quantile((1.0 + confidence) / 2.0)
    margin = z * standard_error
    return {"mean": round(mu, 6), "lower": round(mu - margin, 6), "upper": round(mu + margin, 6), "n": float(n)}


def paired_mean_ci(
    treated: Sequence[float], control: Sequence[float], confidence: float = 0.95
) -> dict[str, float]:
    if len(treated) != len(control):
        raise ValueError("treated and control must have equal length")
    return mean_ci([t - c for t, c in zip(treated, control)], confidence)


def bootstrap_mean_ci(
    values: Sequence[float], resamples: int = 1000, seed: int = 42, confidence: float = 0.95
) -> dict[str, float]:
    """Percentile bootstrap CI with a deterministic PRNG for reproducible simulation studies."""
    if not values:
        return {"mean": 0.0, "lower": 0.0, "upper": 0.0, "n": 0.0}
    if resamples < 1:
        raise ValueError("resamples must be >= 1")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    rng = random.Random(seed)
    n = len(values)
    estimates = [mean(rng.choices(values, k=n)) for _ in range(resamples)]
    alpha = (1.0 - confidence) / 2.0
    estimates.sort()
    lower = _quantile(estimates, alpha)
    upper = _quantile(estimates, 1.0 - alpha)
    return {"mean": round(mean(values), 6), "lower": round(lower, 6), "upper": round(upper, 6), "n": float(n)}


def _quantile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must be in [0, 1]")
    if len(values) == 1:
        return float(values[0])
    position = q * (len(values) - 1)
    lo = math.floor(position)
    hi = math.ceil(position)
    if lo == hi:
        return float(values[lo])
    weight = position - lo
    return float(values[lo] * (1.0 - weight) + values[hi] * weight)


def _normal_quantile(p: float) -> float:
    from statistics import NormalDist

    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    return NormalDist().inv_cdf(p)


def assert_finite_bounded(value: Any, low: float = 0.0, high: float = 1.0) -> list[str]:
    """Recursively collect non-finite or out-of-range numeric values."""
    errors: list[str] = []

    def visit(node: Any, path: str) -> None:
        if isinstance(node, bool):
            return
        if isinstance(node, (int, float)):
            if not math.isfinite(float(node)):
                errors.append(f"{path}: non-finite value")
            elif not low <= float(node) <= high:
                errors.append(f"{path}: {node} outside [{low}, {high}]")
        elif isinstance(node, dict):
            for key, child in node.items():
                visit(child, f"{path}.{key}")
        elif isinstance(node, (list, tuple)):
            for index, child in enumerate(node):
                visit(child, f"{path}[{index}]")

    visit(value, "$")
    return errors
