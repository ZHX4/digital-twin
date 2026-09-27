from __future__ import annotations

import math
import random

PATHWAY_BASE = {
    "AI & Machine Learning": {"demand": 0.84, "mobility": 0.92, "automation": 0.77, "research": 0.90},
    "Robotics & Autonomous Systems": {"demand": 0.80, "mobility": 0.83, "automation": 0.65, "research": 0.87},
    "Computational Biology": {"demand": 0.74, "mobility": 0.76, "automation": 0.51, "research": 0.94},
    "Fundamental Science": {"demand": 0.58, "mobility": 0.60, "automation": 0.34, "research": 0.99},
    "Human-Centered Computing": {"demand": 0.77, "mobility": 0.82, "automation": 0.58, "research": 0.78},
    "Design & Creative Technology": {"demand": 0.70, "mobility": 0.78, "automation": 0.68, "research": 0.67},
    "Language & Social Systems": {"demand": 0.67, "mobility": 0.70, "automation": 0.57, "research": 0.72},
}


def market_snapshot(seed: int, year: int = 2040) -> dict[str, dict[str, float]]:
    rng = random.Random(seed + year * 17)
    shock = 0.06 * math.sin(year / 3.0 + rng.random())
    snapshot = {}
    for path, base in PATHWAY_BASE.items():
        snapshot[path] = {"demand": round(max(0.05, min(0.99, base["demand"] + shock + rng.gauss(0, 0.025))), 3),
            "mobility": round(max(0.05, min(0.99, base["mobility"] + rng.gauss(0, 0.03))), 3),
            "automation_exposure": round(max(0.05, min(0.99, base["automation"] + rng.gauss(0, 0.035))), 3),
            "research_intensity": round(max(0.05, min(0.99, base["research"] + rng.gauss(0, 0.025))), 3)}
    return snapshot


def market_series(seed: int, start: int = 2025, end: int = 2045) -> dict[int, dict[str, dict[str, float]]]:
    return {year: market_snapshot(seed + year, year) for year in range(start, end + 1)}
