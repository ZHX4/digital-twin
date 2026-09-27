from __future__ import annotations

import random
from collections.abc import Iterable

from .models import DOMAINS, CampResult

CAMP_LIBRARY = {
    "robotics": "Robotics Systems Camp", "biology": "Life Science Lab", "mathematics": "Mathematical Discovery Lab",
    "programming": "AI Systems Studio", "physics": "Physics & Engineering Lab", "design": "Design & Prototyping Studio",
    "language": "Communication & Debate Lab", "social_reasoning": "Social Systems Lab",
    "scientific_reasoning": "Research Methods Studio", "spatial_reasoning": "Spatial Computing Studio",
}


def information_gain(prior: float, posterior: float, uncertainty: float) -> float:
    change = abs(posterior - prior)
    return max(0.0, min(1.0, 0.7 * change + 0.3 * uncertainty))


def run_camps(age: int, capabilities: dict[str, float], interests: dict[str, float], domains: Iterable[str], rng: random.Random) -> list[CampResult]:
    results: list[CampResult] = []
    for domain in domains:
        if domain not in DOMAINS:
            continue
        prior = capabilities.get(domain, 0.5)
        enjoyment = max(0.0, min(1.0, 0.30 + 0.60 * interests.get(domain, 0.5) + rng.gauss(0, 0.06)))
        persistence = max(0.0, min(1.0, 0.30 + 0.55 * capabilities.get("self_regulation", 0.5) + rng.gauss(0, 0.05)))
        performance = max(0.0, min(1.0, 0.50 * prior + 0.30 * enjoyment + 0.20 * persistence + rng.gauss(0, 0.055)))
        posterior = max(0.0, min(1.0, 0.42 * prior + 0.34 * performance + 0.14 * enjoyment + 0.10 * persistence))
        confidence = max(0.22, min(0.96, 0.30 + 0.48 * age / 16.0 + 0.16 * performance))
        results.append(CampResult(age, CAMP_LIBRARY.get(domain, f"{domain.title()} Lab"), domain,
                                  round(prior, 4), round(performance, 4), round(enjoyment, 4), round(persistence, 4),
                                  round(posterior, 4), round(confidence, 4), round(information_gain(prior, posterior, 1-confidence), 4)))
    return results


def choose_exploration_domains(capabilities: dict[str, float], interests: dict[str, float], uncertainties: dict[str, float], count: int = 4) -> list[str]:
    scored = []
    for domain in DOMAINS:
        if domain == "self_regulation":
            continue
        curiosity = 0.35 * interests.get(domain, 0.5)
        uncertainty = 0.45 * uncertainties.get(domain, 0.35)
        novelty = 0.20 * (1.0 - capabilities.get(domain, 0.5))
        scored.append((curiosity + uncertainty + novelty, domain))
    scored.sort(reverse=True)
    return [d for _, d in scored[:count]]
