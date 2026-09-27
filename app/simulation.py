from __future__ import annotations

import random
from statistics import mean

from .camps import choose_exploration_domains, run_camps
from .environment import environment_profile, wellbeing_delta
from .ethics import safety_assessment
from .genetics import generate_genome
from .learning import (
    apply_forgetting,
    apply_learning,
    initialize_skill_state,
    select_curriculum,
)
from .life_course import simulate_life_course
from .market import market_snapshot
from .models import (
    SCENARIO_PARAMS,
    SCENARIOS,
    AssessmentResult,
    ChildConfig,
    Evidence,
    ImpactMetrics,
    Recommendation,
    TwinState,
    YearRecord,
)
from .psychometrics import adaptive_assessment
from .recommendation import pathway_posteriors, recommend


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def _mean(values: dict[str, float]) -> float:
    return sum(values.values()) / max(1, len(values))


def _initial_interests(rng: random.Random, latents: dict[str, float], curiosity: float) -> dict[str, float]:
    return {d: _clip(0.30 + (0.42 + 0.18 * curiosity) * latents[d] + rng.gauss(0, 0.10)) for d in latents}


def _update_capabilities(current: dict[str, float], latent: dict[str, float], env: dict[str, float], cfg: ChildConfig,
                         interests: dict[str, float], rng: random.Random, age: int) -> dict[str, float]:
    out = {}
    maturity = min(1.0, age / 12.0)
    prior_pull_scale = 0.004 * (cfg.genomic_weight / 0.05)
    for domain, value in current.items():
        prior_pull = prior_pull_scale * (latent[domain] - value)
        learning = (0.0020 + 0.0048 * maturity) * env["mentorship"] * (0.62 + 0.38 * cfg.exploration)
        agency = 0.0032 * env["autonomy"] * interests[domain]
        challenge = 0.0028 * env["challenge"] * cfg.acceleration
        access = 0.0100 * env["resource_access"]
        noise = rng.gauss(0, 0.0045)
        out[domain] = _clip(value + prior_pull + learning + agency + challenge + access + noise)
    return out


def _evidence_domains(capabilities: dict[str, float], uncertainties: dict[str, float], interests: dict[str, float]) -> list[str]:
    scored = []
    for domain, capability in capabilities.items():
        score = 0.40 * uncertainties[domain] + 0.35 * interests[domain] + 0.25 * (1 - capability)
        scored.append((score, domain))
    scored.sort(reverse=True)
    return [d for _, d in scored[:5]]


def _phase(age: int) -> str:
    if age < 6:
        return "foundation"
    if age < 9:
        return "adaptive_core"
    if age < 13:
        return "exploration_and_specialization"
    if age < 16:
        return "advanced_practice"
    return "competency_gate"


def _scenario_config(cfg: ChildConfig) -> ChildConfig:
    params = SCENARIO_PARAMS.get(cfg.scenario, {})
    values = dict(cfg.__dict__)
    base = ChildConfig()
    for field in ("acceleration", "exploration", "mentorship", "environment_quality", "genomic_weight"):
        if field in params and getattr(cfg, field) == getattr(base, field):
            values[field] = params[field]
    return ChildConfig(**values)


def _run_one(cfg: ChildConfig, include_experiments: bool = True) -> TwinState:
    rng = random.Random(cfg.seed)
    cfg = _scenario_config(cfg)
    genome = generate_genome(rng, cfg.genomic_weight)
    interests = _initial_interests(rng, genome.synthetic_latents, cfg.curiosity)
    capabilities = {d: _clip(0.28 + 0.30 * genome.synthetic_latents[d] + rng.gauss(0, 0.025)) for d in genome.synthetic_latents}
    uncertainties = dict(genome.uncertainty)
    evidence: list[Evidence] = []
    assessments: list[AssessmentResult] = []
    camps = []
    recommendations: list[Recommendation] = []
    posterior_rows = []
    curriculum: dict[int, list] = {}
    years: list[YearRecord] = []
    audit_log: list[dict] = []
    capability_history: dict[int, dict] = {}
    skill_states = initialize_skill_state(capabilities)
    skill_history: dict[int, dict] = {}
    wellbeing = 0.71
    engagement = 0.68
    previous_path = None
    stability_samples: list[float] = []
    total_hours = 0.0
    projects = 0
    camp_count = 0
    competency_age = float(cfg.horizon)
    gate_reached = False
    market_history: dict[int, dict] = {}
    top_path_predictions: list[float] = []
    synthetic_outcomes: list[float] = []

    for age in range(cfg.horizon + 1):
        skill_states = apply_forgetting(skill_states, months=12.0 if age > 0 else 0.0)
        env = environment_profile(cfg, age, rng)
        capabilities = _update_capabilities(capabilities, genome.synthetic_latents, env, cfg, interests, rng, age)

        for d in interests:
            drift = rng.gauss(0, 0.025) + 0.022 * (capabilities[d] - interests[d]) + 0.018 * cfg.curiosity * env["exploration"]
            interests[d] = _clip(interests[d] + drift)

        if age >= 4:
            for domain in _evidence_domains(capabilities, uncertainties, interests):
                assessment = adaptive_assessment(age, domain, capabilities[domain], uncertainties[domain], rng,
                                                  max_items=8 if age < 8 else 12)
                assessments.append(assessment)
                observed = _clip(0.60 * assessment.theta + 0.40 * capabilities[domain])
                confidence = _clip(1.0 - assessment.standard_error)
                evidence.append(Evidence(
                    age=age, source="adaptive_assessment", domain=domain,
                    observed_mastery=round(observed, 4), confidence=round(confidence, 4),
                    context="synthetic longitudinal IRT/CAT observation", instrument=assessment.instrument,
                    item_count=assessment.items,
                ))
                uncertainties[domain] = _clip(0.72 * uncertainties[domain] + 0.28 * assessment.standard_error)

        if age in (6, 8, 10, 12, 14) and cfg.exploration > 0.25:
            domains = choose_exploration_domains(capabilities, interests, uncertainties, count=4)
            new_camps = run_camps(age, capabilities, interests, domains, rng)
            camps.extend(new_camps)
            camp_count += len(new_camps)
            for c in new_camps:
                capabilities[c.domain] = _clip(0.72 * capabilities[c.domain] + 0.28 * c.posterior_score)
                uncertainties[c.domain] = _clip(uncertainties[c.domain] * (1.0 - 0.20 * c.evidence_confidence))

        market_history[age] = market_snapshot(cfg.seed, 2030 + age)
        rec = recommend(
            age, capabilities, uncertainties, interests, evidence, camps, cfg.mentorship,
            cfg.exploration, market=market_history[age], genomic_weight=cfg.genomic_weight,
            genomic_latents=genome.synthetic_latents,
        )
        recommendations.append(rec)
        posterior_rows.extend(pathway_posteriors(age, rec, min(1.0, len(evidence) / 40.0)))
        top_path_predictions.append(rec.confidence)
        current_path = rec.pathway
        if previous_path is not None:
            stability_samples.append(1.0 if previous_path == current_path else 0.0)
            synthetic_outcomes.append(1.0 if previous_path == current_path else 0.0)
        previous_path = current_path

        if age >= 6:
            max_units = 3 if cfg.scenario == "traditional" else (7 if age >= 12 else 5)
            units = select_curriculum(age, skill_states, capabilities, rec.pathway, cfg.acceleration, max_units=max_units)
            curriculum[age] = units
            scenario_teaching = 0.60 if cfg.scenario == "traditional" else 0.68
            scenario_effort = 0.56 if cfg.scenario == "traditional" else 0.66
            teaching_quality = _clip(scenario_teaching + 0.20 * cfg.mentorship + 0.07 * env["safety"] + 0.05 * env["resource_access"])
            focus_interest = mean(interests[d] for d in rec.contributing_domains)
            effort_factor = _clip(scenario_effort + 0.22 * cfg.acceleration + 0.12 * focus_interest)
            capabilities, skill_states, hours, project_delta = apply_learning(
                capabilities, skill_states, units, rng, teaching_quality, effort_factor
            )
            total_hours += hours
            projects += project_delta + int(age >= 9)

        self_reg = capabilities["self_regulation"]
        wellbeing = _clip(wellbeing + wellbeing_delta(env, engagement, self_reg, cfg.acceleration))
        leading_interest = max(interests, key=lambda domain: interests[domain])
        engagement = _clip(0.60 * engagement + 0.26 * interests[leading_interest] + 0.14 * env["autonomy"] - 0.04 * env["pressure"])

        capability_history[age] = {
            "capabilities": {d: round(v, 4) for d, v in capabilities.items()},
            "uncertainty": {d: round(v, 4) for d, v in uncertainties.items()},
            "interests": {d: round(v, 4) for d, v in interests.items()},
            "executive_function": round(self_reg, 4),
            "wellbeing": round(wellbeing, 4), "engagement": round(engagement, 4),
            "environment": env,
        }
        skill_history[age] = {k: dict(v) for k, v in skill_states.items()}

        mastery_index = _mean(capabilities)
        uncertainty_index = _mean(uncertainties)
        year_notes = rec.rationale[:2] + rec.safety_flags
        years.append(YearRecord(
            age=age, phase=_phase(age), capability_index=round(mastery_index, 4),
            mastery_index=round(0.72 * mastery_index + 0.28 * min(1.0, age / 16.0), 4),
            uncertainty_index=round(uncertainty_index, 4), wellbeing=round(wellbeing, 4),
            engagement=round(engagement, 4), recommended_path=rec.pathway, confidence=rec.confidence,
            hours_learned=round(total_hours, 1), projects_completed=projects, camps_completed=camp_count,
            evidence_count=len(evidence), skill_count=len(skill_states), notes=year_notes,
        ))

        missingness = max(0.0, 1.0 - min(1.0, len(evidence) / max(1, (age - 3) * 5))) if age >= 4 else 1.0
        safety = safety_assessment(age, rec.confidence, 1.0 - rec.confidence, rec.exploration_priority, cfg.genomic_weight, missingness)
        audit_log.append({
            "age": age, "action": "pathway_update", "decision": rec.pathway, "confidence": rec.confidence,
            "safety": safety, "evidence_added": 5 if age >= 4 else 0,
            "genomic_prior_strength": cfg.genomic_weight, "model": "digital-twin-v3",
        })

        if age >= 12 and not gate_reached:
            stable = mean(stability_samples[-3:]) if len(stability_samples) >= 3 else 0.0
            skill_coverage = min(1.0, len([s for s in skill_states.values() if s["mastery"] >= 0.60]) / 8.0)
            gate_score = (0.43 * years[-1].mastery_index + 0.14 * skill_coverage +
                          0.18 * wellbeing + 0.10 * rec.confidence + 0.15 * stable)
            if gate_score >= 0.69:
                competency_age = float(age)
                gate_reached = True
                audit_log.append({"age": age, "action": "competency_gate", "status": "PASSED",
                                  "gate_score": round(gate_score, 4), "reversible": True, "human_review_required": True})


    final_rec = recommendations[-1]
    pathway_stability = mean(stability_samples) if stability_samples else 0.0
    mismatch = _clip(0.46 - 0.25 * pathway_stability - 0.12 * final_rec.confidence + 0.10 * final_rec.exploration_priority)
    exploration_coverage = min(1.0, len({c.domain for c in camps}) / 8.0)
    uncertainty_gate = years[int(competency_age)].uncertainty_index if int(competency_age) < len(years) else years[-1].uncertainty_index

    impact = ImpactMetrics(
        competency_age=round(competency_age, 2), education_years=round(max(1.0, competency_age - 5.0), 2),
        pathway_stability=round(pathway_stability, 3), mismatch_risk=round(mismatch, 3),
        exploration_coverage=round(exploration_coverage, 3), wellbeing=round(wellbeing, 3),
        agency=round(min(0.99, 0.30 + 0.032 * cfg.horizon + 0.25 * cfg.exploration + 0.06 * cfg.mentorship), 3),
        equity_index=round(min(0.99, 0.46 + 0.24 * cfg.environment_quality + 0.18 * cfg.mentorship + 0.10 * cfg.resource_access), 3),
        opportunity_cost=round(max(0.03, 0.31 - 0.12 * cfg.acceleration - 0.09 * cfg.exploration), 3),
        calibration_error=round(abs(mean(top_path_predictions) - mean(synthetic_outcomes)) if synthetic_outcomes else 0.0, 4),
        uncertainty_at_gate=round(uncertainty_gate, 4),
    )
    final_path = final_rec.pathway
    life_course = simulate_life_course(cfg.seed, max(16, int(competency_age)), cfg.life_horizon, final_path,
                                       final_rec.confidence + years[-1].mastery_index * 0.5, wellbeing, cfg.persistence)
    terminal_market = market_snapshot(cfg.seed, 2040)
    audit_log.append({"terminal": True, "final_pathway": final_path, "competency_gate": gate_reached,
                      "market_snapshot": terminal_market})

    limitations = [
        "The genome layer is synthetic and intentionally weak; it is not a proxy for real genetic prediction.",
        "IRT/CAT, BKT, forgetting, market dynamics and causal interventions are simulation models, not validated educational instruments.",
        "Counterfactual estimates are model-based synthetic treatment effects and must not be interpreted as causal evidence for human populations.",
        "Pathway posteriors are advisory and reversible; no automated exclusion or irreversible decision is permitted.",
        "The life-course extension is a systems stress test, not a predictor of an individual person's adult life.",
        "No brain implant, neural decoder, AGI or quantum computer is present. These are future-interface placeholders only.",
    ]
    identity = {"name": cfg.name, "seed": cfg.seed, "scenario": cfg.scenario, "age_horizon": cfg.horizon,
                "population": cfg.population, "model_version": "3.0.0"}
    return TwinState(
        identity=identity, genome=genome, capabilities=capability_history, skills=skill_history,
        evidence=evidence, assessments=assessments, camps=camps, recommendations=recommendations,
        pathway_posteriors=posterior_rows, curriculum=curriculum, years=years, impact=impact,
        market=market_history, life_course=life_course, experiments={}, audit_log=audit_log,
        limitations=limitations, scenario_description=SCENARIOS.get(cfg.scenario, "Synthetic future education scenario"),
    )


def simulate(cfg: ChildConfig, include_experiments: bool = True) -> TwinState:
    if cfg.scenario not in SCENARIO_PARAMS:
        raise ValueError(f"Unknown scenario: {cfg.scenario}")
    return _run_one(cfg, include_experiments=include_experiments)
