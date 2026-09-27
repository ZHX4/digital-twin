from __future__ import annotations

import random
from collections.abc import Iterable, Sequence
from statistics import mean

from .world import POLICIES, simulate_world


def quantiles(values: Sequence[float]) -> dict[str, float]:
    if not values:
        return {"p05": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p95": 0.0}
    values = sorted(values)
    def q(p: float) -> float:
        idx = (len(values) - 1) * p
        lo, hi = int(idx), min(len(values) - 1, int(idx) + 1)
        frac = idx - lo
        return values[lo] * (1 - frac) + values[hi] * frac
    return {f"p{int(p*100):02d}": round(q(p), 5) for p in (0.05, 0.25, 0.50, 0.75, 0.95)}

def bootstrap_ci(values: Sequence[float], seed: int = 42, rounds: int = 400) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    rng = random.Random(seed)
    means = []
    n = len(values)
    for _ in range(rounds):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(mean(sample))
    means.sort()
    return round(means[int(0.025 * rounds)], 5), round(means[int(0.975 * rounds) - 1], 5)

def run_population(seed: int = 42, learners: int = 512, years: int = 12, policy: str = "digital_twin",
                   trajectories: bool = False, policy_override=None) -> dict:
    result = simulate_world(seed, learners=learners, years=years, policy_name=policy, return_trajectories=trajectories, policy_override=policy_override)
    competency = [row["competency"] for row in result["terminal"]]
    wellbeing = [row["wellbeing"] for row in result["terminal"]]
    return {
        "world": result,
        "distribution": {"competency": quantiles(competency), "wellbeing": quantiles(wellbeing)},
        "bootstrap": {
            "competency_mean_95ci": bootstrap_ci(competency, seed + 1),
            "wellbeing_mean_95ci": bootstrap_ci(wellbeing, seed + 2),
        },
    }

def compare_population_policies(seed: int = 42, learners: int = 256, years: int = 12, policies: Iterable[str] | None = None) -> dict:
    policies = list(policies or POLICIES.keys())
    rows = {}
    for idx, policy in enumerate(policies):
        rows[policy] = run_population(seed + idx * 1013, learners=learners, years=years, policy=policy, trajectories=False)
    return rows


def monte_carlo_policy(seed: int = 42, policy: str = "digital_twin", repetitions: int = 12,
                       learners: int = 96, years: int = 10) -> dict:
    runs = []
    for i in range(repetitions):
        result = run_population(seed + i * 10007, learners=learners, years=years, policy=policy, trajectories=False)
        runs.append(result["world"]["metrics"])
    def ci(metric: str):
        values = [row[metric] for row in runs]
        lo, hi = bootstrap_ci(values, seed + 999 + len(metric), rounds=300)
        return {"mean": round(mean(values), 5), "ci95": [lo, hi], "distribution": quantiles(values)}
    return {
        "schema_version": "4.0",
        "seed": seed,
        "policy": policy,
        "repetitions": repetitions,
        "learners_per_run": learners,
        "years": years,
        "metrics": {metric: ci(metric) for metric in ("competency_mean", "wellbeing_mean", "agency_mean", "mismatch_mean", "equity_index")},
        "interpretation": "Monte Carlo over synthetic worlds; confidence intervals quantify simulator variability, not sampling uncertainty in real populations.",
    }
