from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Sequence

from .curriculum_agent import DEFAULT_ACTIONS, LearningAction
from .learner_model import LatentLearnerState, select_information_gap


@dataclass(frozen=True)
class TutorIntervention:
    action: LearningAction
    target_skill: str
    rationale: str
    misconception_risk: float
    uncertainty: float
    reversible: bool = True

    def to_dict(self) -> Dict:
        return asdict(self)


class TutorAgent:
    """Deterministic pedagogical agent; an LLM can be plugged in above this interface later."""

    def propose(self, state: LatentLearnerState, actions: Sequence[LearningAction] = DEFAULT_ACTIONS) -> TutorIntervention:
        target = max(
            select_information_gap(state, top_k=5),
            key=lambda skill: state.misconceptions.get(skill, 0.0) + state.uncertainty.get(skill, 0.0)
        )
        candidates = [a for a in actions if a.skill == target]
        action = candidates[0] if candidates else min(actions, key=lambda a: abs(a.exploration - state.uncertainty.get(target, 0.4)))
        uncertainty = state.uncertainty.get(target, 0.4)
        misconception = state.misconceptions.get(target, 0.18)
        rationale = (
            f"Target {target}: mastery={state.mastery.get(target, 0.0):.2f}, "
            f"uncertainty={uncertainty:.2f}, misconception_risk={misconception:.2f}."
        )
        return TutorIntervention(action, target, rationale, round(misconception, 4), round(uncertainty, 4))
