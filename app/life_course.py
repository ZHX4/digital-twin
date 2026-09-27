from __future__ import annotations

import random
from typing import Dict

from .market import market_snapshot


def simulate_life_course(seed: int, start_age: int, end_age: int, pathway: str, competency: float,
                         wellbeing: float, persistence: float) -> Dict[int, Dict]:
    rng = random.Random(seed + 9187)
    rows: Dict[int, Dict] = {}
    skill = max(0.25, min(1.0, competency))
    burnout = 0.0
    role = "learner"
    for age in range(start_age, end_age + 1):
        market = market_snapshot(seed, 2020 + age)
        m = market[pathway]
        transition = "education_to_work" if age == start_age else "stable_development"
        if age == start_age:
            role = "researcher / professional trainee"
        elif age >= 18 and skill > 0.74:
            role = "professional / researcher"
        skill = max(0.0, min(1.0, skill + 0.012 * persistence + 0.008 * m["research_intensity"] - 0.006 * burnout))
        burnout = max(0.0, min(1.0, burnout + 0.008 * max(0.0, 0.65 - wellbeing) - 0.004 * wellbeing + rng.gauss(0, 0.004)))
        income_index = max(0.0, min(1.0, 0.32 + 0.55 * skill * m["demand"] - 0.12 * m["automation_exposure"]))
        rows[age] = {"age": age, "role": role, "pathway": pathway, "skill_index": round(skill, 4),
            "wellbeing_proxy": round(max(0.0, wellbeing - 0.25 * burnout), 4), "burnout_proxy": round(burnout, 4),
            "income_index": round(income_index, 4), "market_demand": m["demand"], "transition": transition}
    return rows
