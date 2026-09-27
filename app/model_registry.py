from __future__ import annotations

from typing import Dict

MODEL_REGISTRY: Dict[str, Dict] = {
    "learner.latent_state.v1": {
        "family": "probabilistic-state",
        "purpose": "Latent learner state, uncertainty, retention and misconceptions",
        "status": "active",
        "data_boundary": "synthetic",
    },
    "assessment.irt_cat.v1": {
        "family": "psychometrics",
        "purpose": "Adaptive synthetic assessment",
        "status": "active",
        "data_boundary": "synthetic",
    },
    "curriculum.linear_ucb.v1": {
        "family": "contextual-bandit",
        "purpose": "Adaptive curriculum action selection",
        "status": "active",
        "data_boundary": "synthetic",
    },
    "tutor.rule_agent.v1": {
        "family": "agent-policy",
        "purpose": "Uncertainty/misconception-targeted tutoring",
        "status": "active",
        "data_boundary": "synthetic",
    },
    "world.multi_agent.v1": {
        "family": "agent-based-simulation",
        "purpose": "Learner/family/school/teacher world",
        "status": "active",
        "data_boundary": "synthetic",
    },
    "policy.pareto.v1": {
        "family": "multi-objective-search",
        "purpose": "Education policy Pareto search",
        "status": "active",
        "data_boundary": "synthetic",
    },
    "benchmark.learner_models.v1": {
        "family": "benchmark-suite",
        "purpose": "Prediction and calibration comparison",
        "status": "active",
        "data_boundary": "synthetic",
    },
}


def registry() -> Dict[str, Dict]:
    return MODEL_REGISTRY
