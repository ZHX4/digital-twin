from __future__ import annotations

import random
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Tuple

from .world import POLICIES, simulate_world

def quantiles(values: Sequence[float]) -> Dict[str, float]:
    if not values:
        return {"p05": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p95": 0.0}
    values = sorted(values)
    def q(p: float) -> float:
        idx = (len(values) - 1) * p
        lo, hi = int(idx), min(len(values) - 1, int(idx) + 1)
        frac = idx - lo
        return values[lo] * (1 - frac) + values[hi] * frac
    return {f"p{int(p*100):02d}": round(q(p), 5) for p in (0.05, 0.25, 0.50, 0.75, 0.95)}

def bootstrap_ci(values: Sequence[float], seed: int = 42, rounds: int = 400) -> Tuple[float, float]:
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
                   trajectories: bool = False) -> Dict:
    result = simulate_world(seed, learners=learners, years=years, policy_name=policy, return_trajectories=trajectories)
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

def compare_population_policies(seed: int = 42, learners: int = 256, years: int = 12, policies: Iterable[str] | None = None) -> Dict:
    policies = list(policies or POLICIES.keys())
    rows = {}
    for idx, policy in enumerate(policies):
        rows[policy] = run_population(seed + idx * 1013, learners=learners, years=years, policy=policy, trajectories=False)
    return rows
