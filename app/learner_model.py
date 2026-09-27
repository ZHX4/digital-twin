from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass, field
from typing import Dict, Iterable, List, Mapping, Tuple

SKILL_GRAPH: Dict[str, List[str]] = {
    "numeracy": [],
    "algebra": ["numeracy"],
    "functions": ["algebra"],
    "calculus": ["functions"],
    "probability": ["numeracy"],
    "optimization": ["calculus", "probability"],
    "programming": [],
    "data_structures": ["programming"],
    "algorithms": ["data_structures", "algebra"],
    "machine_learning": ["algorithms", "probability", "optimization"],
    "systems_engineering": ["algorithms", "functions"],
    "scientific_reasoning": ["numeracy"],
    "experimental_design": ["scientific_reasoning", "probability"],
    "research_methods": ["experimental_design"],
    "communication": [],
    "scientific_writing": ["communication", "research_methods"],
    "collaboration": [],
    "metacognition": [],
}

TRANSFER_EDGES: Dict[Tuple[str, str], float] = {
    ("algebra", "programming"): 0.08,
    ("functions", "systems_engineering"): 0.12,
    ("calculus", "optimization"): 0.16,
    ("probability", "machine_learning"): 0.17,
    ("algorithms", "machine_learning"): 0.15,
    ("scientific_reasoning", "experimental_design"): 0.16,
    ("research_methods", "scientific_writing"): 0.12,
    ("communication", "scientific_writing"): 0.10,
    ("metacognition", "algebra"): 0.05,
}

@dataclass
class LatentLearnerState:
    learner_id: str
    age: int
    mastery: Dict[str, float]
    uncertainty: Dict[str, float]
    interests: Dict[str, float]
    wellbeing: float
    agency: float
    retention: Dict[str, float]
    misconceptions: Dict[str, float] = field(default_factory=dict)
    evidence_count: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


def _clip(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def initial_state(seed: int, learner_id: str, resource_access: float = 0.8) -> LatentLearnerState:
    rng = random.Random(seed)
    mastery = {}
    uncertainty = {}
    interests = {}
    retention = {}
    for skill in SKILL_GRAPH:
        base = _clip(0.23 + 0.22 * resource_access + rng.gauss(0, 0.06))
        mastery[skill] = round(base, 4)
        uncertainty[skill] = round(_clip(0.36 + rng.random() * 0.22), 4)
        interests[skill] = round(_clip(0.35 + rng.random() * 0.50), 4)
        retention[skill] = round(0.82 + rng.random() * 0.13, 4)
    return LatentLearnerState(
        learner_id=learner_id, age=0, mastery=mastery, uncertainty=uncertainty, interests=interests,
        wellbeing=round(_clip(0.72 + rng.gauss(0, 0.04)), 4),
        agency=round(_clip(0.32 + 0.08 * resource_access + rng.gauss(0, 0.03)), 4),
        retention=retention,
    )


def prerequisite_ready(state: LatentLearnerState, skill: str, threshold: float = 0.58) -> bool:
    return all(state.mastery.get(p, 0.0) >= threshold for p in SKILL_GRAPH.get(skill, []))


def update_from_observation(state: LatentLearnerState, skill: str, correct: bool, information: float = 0.35) -> None:
    prior = state.mastery.get(skill, 0.3)
    error = 0.08 if correct else 0.18
    direction = 1.0 if correct else -1.0
    gain = information * (1.0 - prior if correct else prior)
    state.mastery[skill] = _clip(prior + direction * gain * (0.55 if correct else 0.28))
    state.uncertainty[skill] = _clip(state.uncertainty.get(skill, 0.4) * (1.0 - 0.14 * information) + error * 0.08)
    state.misconceptions[skill] = _clip(state.misconceptions.get(skill, 0.20) + (0.04 if not correct else -0.025))
    state.evidence_count += 1


def learn(
    state: LatentLearnerState,
    skill: str,
    intensity: float,
    teaching_quality: float,
    peer_effect: float = 0.0,
    transfer: bool = True,
    rng: random.Random | None = None,
) -> float:
    rng = rng or random.Random()
    if skill not in SKILL_GRAPH:
        return 0.0
    prerequisite_factor = 1.0 if prerequisite_ready(state, skill) else 0.62
    motivation = 0.55 + 0.45 * state.interests.get(skill, 0.5)
    stress_penalty = max(0.42, 1.0 - max(0.0, 0.66 - state.wellbeing))
    gain = 0.060 * intensity * teaching_quality * motivation * prerequisite_factor * stress_penalty
    gain *= 0.90 + 0.20 * rng.random()
    old = state.mastery.get(skill, 0.3)
    new = _clip(old + gain * (1.0 - old))
    state.mastery[skill] = round(new, 5)
    state.uncertainty[skill] = round(_clip(state.uncertainty.get(skill, 0.4) * 0.93 - 0.015 * gain), 5)
    state.retention[skill] = round(_clip(state.retention.get(skill, 0.88) + 0.02 * intensity - 0.008 * (1.0 - teaching_quality)), 5)
    state.wellbeing = round(_clip(state.wellbeing + 0.004 * teaching_quality + 0.002 * peer_effect - 0.006 * max(0.0, intensity - 0.85)), 5)
    state.agency = round(_clip(state.agency + 0.006 * intensity + 0.004 * state.interests.get(skill, 0.5) - 0.003 * max(0.0, 0.6 - teaching_quality)), 5)

    if transfer:
        for (src, dst), coefficient in TRANSFER_EDGES.items():
            if src == skill and dst in state.mastery:
                transfer_gain = coefficient * gain * state.mastery[skill]
                state.mastery[dst] = round(_clip(state.mastery[dst] + transfer_gain), 5)
                state.uncertainty[dst] = round(_clip(state.uncertainty[dst] * (1.0 - 0.06 * coefficient)), 5)
    return round(gain, 5)


def forget(state: LatentLearnerState, years: float = 1.0) -> None:
    for skill in list(state.mastery):
        retention = state.retention.get(skill, 0.88)
        rate = 0.014 + 0.042 * (1.0 - retention)
        state.mastery[skill] = round(_clip(state.mastery[skill] * math.exp(-rate * years)), 5)
        state.uncertainty[skill] = round(_clip(state.uncertainty[skill] * 1.035), 5)
    state.wellbeing = round(_clip(state.wellbeing - 0.003 * years), 5)


def select_information_gap(state: LatentLearnerState, top_k: int = 4) -> List[str]:
    scored = []
    for skill in SKILL_GRAPH:
        gap = 1.0 - state.mastery.get(skill, 0.0)
        uncertainty = state.uncertainty.get(skill, 0.4)
        interest = state.interests.get(skill, 0.5)
        score = 0.45 * uncertainty + 0.35 * gap + 0.20 * interest
        scored.append((score, skill))
    scored.sort(reverse=True)
    return [skill for _, skill in scored[:top_k]]


def competency_index(state: LatentLearnerState) -> float:
    values = list(state.mastery.values())
    return round(sum(values) / max(1, len(values)), 5)
