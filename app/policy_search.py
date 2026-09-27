from __future__ import annotations

import random
from dataclasses import asdict
from functools import lru_cache

from .population import run_population
from .world import POLICIES, WorldPolicy


def _score(row: dict) -> dict[str, float]:
    m = row["world"]["metrics"]
    inequality = row["world"]["inequality"]
    return {
        "learning": m["competency_mean"],
        "wellbeing": m["wellbeing_mean"],
        "agency": m["agency_mean"],
        "equity": m["equity_index"],
        "mismatch": m["mismatch_mean"],
        "inequality": inequality["competency_gap"],
        "cost_proxy": 1.0 - m["equity_index"],
    }

def _dominates(a: dict[str, float], b: dict[str, float]) -> bool:
    maximize = ["learning", "wellbeing", "agency", "equity"]
    minimize = ["mismatch", "inequality", "cost_proxy"]
    return (
        all(a[k] >= b[k] for k in maximize)
        and all(a[k] <= b[k] for k in minimize)
        and any(a[k] != b[k] for k in maximize + minimize)
    )

def pareto_frontier(rows: list[dict]) -> list[dict]:
    frontier = []
    for i, row in enumerate(rows):
        if not any(_dominates(other["objectives"], row["objectives"]) for j, other in enumerate(rows) if i != j):
            frontier.append(row)
    return frontier

def _candidate(name: str, rng: random.Random, baseline: WorldPolicy) -> WorldPolicy:
    return WorldPolicy(
        name=name,
        specialization_age=rng.randint(10, 15),
        acceleration=round(rng.uniform(0.30, 0.86), 3),
        exploration=round(rng.uniform(0.20, 0.98), 3),
        mentorship=round(rng.uniform(0.35, 1.00), 3),
        teacher_ratio=round(rng.uniform(9, 24), 2),
        resource_equalization=round(rng.uniform(0.0, 1.0), 3),
        tutor_enabled=rng.random() > 0.30,
        core_ratio=round(rng.uniform(0.48, 0.78), 3),
        objective_profile=baseline.objective_profile,
    )

@lru_cache(maxsize=32)
def search_policies(seed: int = 42, candidates: int = 24, learners: int = 96, years: int = 10) -> dict:
    rng = random.Random(seed)
    rows = []
    for i in range(candidates):
        candidate = _candidate(f"candidate-{i:03d}", rng, POLICIES["digital_twin"])
        if i == 0:
            candidate = POLICIES["digital_twin"]
        result = run_population(seed + 17 * i, learners=learners, years=years, policy="digital_twin", trajectories=False, policy_override=candidate)
        objectives = _score(result)
        rows.append({"candidate": asdict(candidate), "objectives": objectives})
    frontier = pareto_frontier(rows)
    return {"seed": seed, "candidates": candidates, "population_per_candidate": learners, "years": years,
            "results": rows, "pareto_frontier": frontier}
