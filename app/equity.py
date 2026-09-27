from __future__ import annotations

from collections.abc import Iterable
from statistics import mean


def group_metrics(rows: Iterable[dict]) -> dict[str, dict[str, float]]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row["group"], []).append(row)
    out = {}
    for group, items in groups.items():
        out[group] = {
            "n": len(items),
            "competency_age_mean": round(mean(x["competency_age"] for x in items), 4),
            "wellbeing_mean": round(mean(x["wellbeing"] for x in items), 4),
            "mismatch_mean": round(mean(x["mismatch"] for x in items), 4),
            "pathway_confidence_mean": round(mean(x["confidence"] for x in items), 4),
        }
    return out


def fairness_gap(groups: dict[str, dict[str, float]], metric: str) -> float:
    values = [g[metric] for g in groups.values()]
    return round(max(values) - min(values), 4) if values else 0.0
