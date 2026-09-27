from __future__ import annotations

from dataclasses import replace
from typing import Dict, Iterable


def policy_overrides(base_cfg, **changes):
    return replace(base_cfg, **changes)


def ate(results_treated: Iterable[float], results_control: Iterable[float]) -> float:
    t = list(results_treated); c = list(results_control)
    if not t or not c:
        return 0.0
    return sum(t) / len(t) - sum(c) / len(c)


def counterfactual_summary(base_result: Dict, treated_result: Dict, metrics: Iterable[str]) -> Dict:
    effects = {}
    for metric in metrics:
        b = base_result.get("impact", {}).get(metric)
        t = treated_result.get("impact", {}).get(metric)
        if isinstance(b, (int, float)) and isinstance(t, (int, float)):
            effects[metric] = round(float(t - b), 6)
    b_mastery = base_result.get("years", [{}])[-1].get("mastery_index")
    t_mastery = treated_result.get("years", [{}])[-1].get("mastery_index")
    if isinstance(b_mastery, (int, float)) and isinstance(t_mastery, (int, float)):
        effects["terminal_mastery_index"] = round(float(t_mastery - b_mastery), 6)
    b_conf = base_result.get("recommendations", [{}])[-1].get("score")
    t_conf = treated_result.get("recommendations", [{}])[-1].get("score")
    if isinstance(b_conf, (int, float)) and isinstance(t_conf, (int, float)):
        effects["terminal_pathway_posterior"] = round(float(t_conf - b_conf), 6)
    return {"estimand": "individual synthetic treatment effect", "effects": effects,
            "warning": "Counterfactuals are model-based interventions, not causal evidence from human populations."}
