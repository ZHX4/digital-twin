from __future__ import annotations

import random
from typing import Dict

from .models import ChildConfig


def environment_profile(cfg: ChildConfig, age: int, rng: random.Random) -> Dict[str, float]:
    maturity = min(1.0, age / 12.0)
    safe = min(1.0, cfg.environment_quality * (0.94 + 0.06 * rng.random()))
    mentoring = min(1.0, cfg.mentorship * (0.92 + 0.08 * rng.random()))
    challenge = min(1.0, 0.28 + cfg.acceleration * 0.46 + maturity * 0.20)
    exploration = min(1.0, cfg.exploration * (0.90 + 0.10 * rng.random()))
    pressure = max(0.02, 0.10 + cfg.acceleration * 0.24 - cfg.mentorship * 0.13)
    autonomy = min(1.0, 0.18 + maturity * 0.52 + cfg.exploration * 0.25)
    resource_access = min(1.0, cfg.resource_access * (0.90 + 0.10 * rng.random()))
    return {"safety": round(safe, 3), "mentorship": round(mentoring, 3), "challenge": round(challenge, 3),
            "exploration": round(exploration, 3), "pressure": round(pressure, 3), "autonomy": round(autonomy, 3),
            "resource_access": round(resource_access, 3)}


def wellbeing_delta(environment: Dict[str, float], engagement: float, self_regulation: float, acceleration: float) -> float:
    challenge_penalty = max(0.0, environment["pressure"] + acceleration * 0.04 - self_regulation * 0.38)
    recovery = 0.007 * environment["safety"] + 0.010 * environment["mentorship"]
    strain = 0.018 * challenge_penalty
    return 0.004 * environment["safety"] + 0.006 * environment["mentorship"] + 0.006 * engagement - 0.016 * challenge_penalty - 0.004 * environment["pressure"]
