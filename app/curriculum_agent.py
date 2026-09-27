from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class LearningAction:
    action_id: str
    skill: str
    mode: str
    intensity: float
    exploration: float
    cost: float

    def to_dict(self) -> dict:
        return asdict(self)


DEFAULT_ACTIONS = [
    LearningAction("guided_microlesson", "algebra", "lesson", 0.48, 0.10, 0.18),
    LearningAction("project_build", "programming", "project", 0.74, 0.45, 0.34),
    LearningAction("research_problem", "scientific_reasoning", "research", 0.68, 0.68, 0.42),
    LearningAction("spaced_practice", "probability", "practice", 0.42, 0.12, 0.15),
    LearningAction("systems_design", "systems_engineering", "project", 0.73, 0.57, 0.39),
    LearningAction("communication_workshop", "communication", "collaboration", 0.40, 0.50, 0.20),
    LearningAction("metacognition_session", "metacognition", "reflection", 0.28, 0.60, 0.12),
]


class LinearUCBCurriculum:
    """Small research-grade contextual bandit with per-action ridge regression."""

    def __init__(self, actions: Sequence[LearningAction] = DEFAULT_ACTIONS, alpha: float = 0.65, ridge: float = 1.0):
        self.actions = list(actions)
        self.alpha = alpha
        self.dimension = 8
        self.A = {a.action_id: np.eye(self.dimension) * ridge for a in self.actions}
        self.b = {a.action_id: np.zeros(self.dimension) for a in self.actions}
        self.pulls = {a.action_id: 0 for a in self.actions}

    @staticmethod
    def context(age: int, mastery_gap: float, uncertainty: float, interest: float,
                wellbeing: float, agency: float, resource_access: float, exploration_pressure: float) -> np.ndarray:
        return np.array([
            1.0, age / 18.0, mastery_gap, uncertainty, interest, wellbeing, agency,
            0.5 * resource_access + 0.5 * exploration_pressure,
        ], dtype=float)

    def _ucb(self, action: LearningAction, x: np.ndarray) -> float:
        A_inv = np.linalg.inv(self.A[action.action_id])
        theta = A_inv @ self.b[action.action_id]
        mean = float(theta @ x)
        uncertainty = math.sqrt(max(0.0, float(x.T @ A_inv @ x)))
        structural_prior = 0.10 * action.exploration - 0.06 * action.cost
        return mean + self.alpha * uncertainty + structural_prior

    def select(self, context: np.ndarray, allowed_actions: Sequence[LearningAction] | None = None) -> LearningAction:
        pool = list(allowed_actions or self.actions)
        return max(pool, key=lambda action: self._ucb(action, context))

    def update(self, action: LearningAction, context: np.ndarray, reward: float) -> None:
        aid = action.action_id
        self.A[aid] += np.outer(context, context)
        self.b[aid] += context * float(reward)
        self.pulls[aid] += 1

    def diagnostics(self) -> dict:
        return {"alpha": self.alpha, "actions": {k: {"pulls": v} for k, v in self.pulls.items()}}
