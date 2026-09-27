from __future__ import annotations

import math
import random
from dataclasses import asdict
from statistics import mean, pstdev
from typing import Any

from .causal import counterfactual_summary, policy_overrides
from .equity import fairness_gap, group_metrics
from .models import SCENARIO_PARAMS, ChildConfig
from .simulation import simulate


def summarize(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    return {"mean": round(mean(values), 4), "std": round(pstdev(values), 4),
            "min": round(min(values), 4), "max": round(max(values), 4)}


def _cfg_for(seed: int, scenario: str, resource_access: float = 0.85) -> ChildConfig:
    p = SCENARIO_PARAMS[scenario]
    return ChildConfig(
        seed=seed,
        scenario=scenario,
        acceleration=p["acceleration"],
        exploration=p["exploration"],
        mentorship=p["mentorship"],
        environment_quality=p["environment_quality"],
        genomic_weight=p["genomic_weight"],
        resource_access=resource_access,
    )


def run_cohort(seed: int, size: int, scenario: str) -> dict:
    outcomes = []
    pathway_counts: dict[str, int] = {}
    rng = random.Random(seed)
    for _ in range(size):
        result = simulate(_cfg_for(rng.randint(0, 10_000_000), scenario), include_experiments=False)
        impact = asdict(result.impact)
        outcomes.append(impact)
        path = result.recommendations[-1].pathway
        pathway_counts[path] = pathway_counts.get(path, 0) + 1
    keys = outcomes[0].keys() if outcomes else []
    return {"seed": seed, "size": size, "scenario": scenario,
            "aggregates": {k: summarize([o[k] for o in outcomes]) for k in keys},
            "pathway_counts": pathway_counts}


def compare_scenarios(seed: int, size: int = 48) -> dict:
    scenarios = list(SCENARIO_PARAMS)
    return {s: run_cohort(seed + i * 1009, size, s) for i, s in enumerate(scenarios)}


def counterfactual_lab(seed: int = 42) -> dict:
    base = simulate(_cfg_for(seed, "global_digital_twin"), include_experiments=False).to_dict()
    interventions: dict[str, dict[str, Any]] = {
        "more_mentorship": {"mentorship": 1.0},
        "slower_acceleration": {"acceleration": 0.45},
        "more_exploration": {"exploration": 1.0},
        "genomics_off": {"genomic_weight": 0.0},
        "traditional_policy": {"scenario": "traditional"},
    }
    rows = {}
    base_cfg = _cfg_for(seed, "global_digital_twin")
    for name, changes in interventions.items():
        cfg = policy_overrides(base_cfg, **changes)
        treated = simulate(cfg, include_experiments=False).to_dict()
        rows[name] = counterfactual_summary(base, treated, [
            "competency_age", "mismatch_risk", "wellbeing", "exploration_coverage", "pathway_stability", "uncertainty_at_gate"
        ])
    return {"seed": seed, "baseline": base["impact"], "interventions": rows}


def genomic_ablation(seed: int = 42, size: int = 48) -> dict:
    with_genome = run_cohort(seed, size, "genomic_adaptive")
    rng = random.Random(seed)
    metrics_with, metrics_without = [], []
    confidence_with, confidence_without = [], []
    for _ in range(size):
        local = rng.randint(0, 10_000_000)
        a_cfg = _cfg_for(local, "genomic_adaptive")
        b_cfg = policy_overrides(a_cfg, genomic_weight=0.0)
        a = simulate(a_cfg, include_experiments=False)
        b = simulate(b_cfg, include_experiments=False)
        metrics_with.append(asdict(a.impact)); metrics_without.append(asdict(b.impact))
        confidence_with.append(a.recommendations[-1].score); confidence_without.append(b.recommendations[-1].score)
    keys = metrics_with[0].keys() if metrics_with else []
    deltas = {k: round(mean(x[k] for x in metrics_with) - mean(y[k] for y in metrics_without), 5) for k in keys}
    return {"with_genomic_prior": with_genome, "mean_effect_of_genomic_prior": deltas,
            "continuous_diagnostics": {
                "terminal_confidence_shift": round(mean(confidence_with) - mean(confidence_without), 6),
                "competency_age_shift": round(mean(x["competency_age"] for x in metrics_with) - mean(y["competency_age"] for y in metrics_without), 6),
            },
            "interpretation": "Synthetic architectural ablation only; not evidence for real genetic utility."}


def sensitivity_analysis(seed: int = 42, samples: int = 96) -> dict:
    rng = random.Random(seed)
    params = ["acceleration", "exploration", "mentorship", "environment_quality", "genomic_weight"]
    rows: dict[str, list[tuple[float, float]]] = {p: [] for p in params}
    baseline = []
    terminal_mastery = []
    for _ in range(samples):
        values: dict[str, float] = {
            "acceleration": rng.uniform(0.2, 0.95),
            "exploration": rng.uniform(0.2, 1.0),
            "mentorship": rng.uniform(0.35, 1.0),
            "environment_quality": rng.uniform(0.55, 1.0),
            "genomic_weight": rng.uniform(0.0, 0.10),
        }
        cfg = ChildConfig(
            seed=rng.randint(0, 10_000_000),
            scenario="global_digital_twin",
            acceleration=values["acceleration"],
            exploration=values["exploration"],
            mentorship=values["mentorship"],
            environment_quality=values["environment_quality"],
            genomic_weight=values["genomic_weight"],
        )
        out = simulate(cfg, include_experiments=False).impact
        y = out.competency_age
        baseline.append(y)
        terminal_mastery.append(0.72 * (1.0 - out.mismatch_risk) + 0.28 * out.wellbeing)
        for p, v in values.items():
            rows[p].append((v, terminal_mastery[-1]))
    result = {}
    y_mean = mean(terminal_mastery)
    y_var = mean((y - y_mean) ** 2 for y in terminal_mastery) or 1e-9
    for p, pairs in rows.items():
        x_mean = mean(x for x, _ in pairs)
        cov = mean((x - x_mean) * (y - y_mean) for x, y in pairs)
        x_var = mean((x - x_mean) ** 2 for x, _ in pairs) or 1e-9
        r = cov / math.sqrt(x_var * y_var)
        result[p] = {"pearson_proxy": round(r, 4), "abs_influence": round(abs(r), 4)}
    return {"seed": seed, "samples": samples, "metric": "terminal_human_development_index", "competency_age_distribution": summarize(baseline), "sensitivity": result}


def fairness_lab(seed: int = 42, per_group: int = 24) -> dict:
    rng = random.Random(seed)
    rows = []
    groups = {"A_high_resource": 0.94, "B_mid_resource": 0.76, "C_low_resource": 0.58}
    for group, access in groups.items():
        for _ in range(per_group):
            local = rng.randint(0, 10_000_000)
            cfg = _cfg_for(local, "global_digital_twin", resource_access=access)
            out = simulate(cfg, include_experiments=False)
            rows.append({"group": group, "competency_age": out.impact.competency_age,
                         "wellbeing": out.impact.wellbeing, "mismatch": out.impact.mismatch_risk,
                         "confidence": out.recommendations[-1].confidence})
    grouped = group_metrics(rows)
    return {"groups": grouped,
            "gaps": {"competency_age": fairness_gap(grouped, "competency_age_mean"),
                     "wellbeing": fairness_gap(grouped, "wellbeing_mean"),
                     "mismatch": fairness_gap(grouped, "mismatch_mean")},
            "warning": "Groups are synthetic resource-access strata, not demographic groups."}


def calibration_lab(seed: int = 42, size: int = 72, scenario: str = "global_digital_twin") -> dict:
    from .calibration import evaluate_multiclass, fit_temperature, temperature_scale
    from .models import PATHWAYS

    rng = random.Random(seed)
    probability_rows: list[dict[str, float]] = []
    outcomes: list[str] = []
    for _ in range(size * 2):
        out = simulate(_cfg_for(rng.randint(0, 10_000_000), scenario), include_experiments=False)
        recs = out.recommendations
        for i in range(len(recs) - 1):
            probability_rows.append(dict(recs[i].ranked_pathways))
            outcomes.append(recs[i + 1].pathway)

    split = max(1, len(probability_rows) // 2)
    calibration_probs = probability_rows[:split]
    calibration_outcomes = outcomes[:split]
    eval_probs = probability_rows[split:]
    eval_outcomes = outcomes[split:]
    classes = list(PATHWAYS)
    temperature = fit_temperature(calibration_probs, calibration_outcomes, classes)
    scaled_eval = temperature_scale(eval_probs, temperature)
    raw_metrics = evaluate_multiclass(eval_probs, eval_outcomes, classes)
    calibrated_metrics = evaluate_multiclass(scaled_eval, eval_outcomes, classes)
    return {
        "n": len(eval_outcomes),
        "scenario": scenario,
        "target_definition": "next-year recommended pathway",
        "calibration_method": "temperature_scaling_on_simulation_holdout",
        "temperature": temperature,
        "raw": raw_metrics,
        "calibrated": calibrated_metrics,
    }
