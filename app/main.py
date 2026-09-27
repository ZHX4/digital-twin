from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse

from .experiments import calibration_lab, compare_scenarios, counterfactual_lab, fairness_lab, genomic_ablation, sensitivity_analysis
from .experiments_registry import EXPERIMENTS
from .models import ChildConfig, PATHWAYS, SCENARIOS, SCENARIO_PARAMS
from .simulation import simulate

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Digital Twin — Human Development Research Laboratory", version="3.0.0",
    description="Synthetic, reproducible research simulator for longitudinal personalized education and governance experiments.")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/simulate")
def api_simulate(seed: int = Query(42, ge=0, le=99999999), name: str = Query("Astra", min_length=1, max_length=48),
    scenario: str = Query("global_digital_twin"), acceleration: float | None = Query(None, ge=0, le=1),
    exploration: float | None = Query(None, ge=0, le=1), mentorship: float | None = Query(None, ge=0, le=1),
    environment: float | None = Query(None, ge=0, le=1), genomic_weight: float | None = Query(None, ge=0, le=0.15),
    horizon: int = Query(16, ge=6, le=20)) -> JSONResponse:
    defaults = SCENARIO_PARAMS.get(scenario, SCENARIO_PARAMS["global_digital_twin"])
    cfg = ChildConfig(seed=seed, name=name, scenario=scenario,
        acceleration=defaults["acceleration"] if acceleration is None else acceleration,
        exploration=defaults["exploration"] if exploration is None else exploration,
        mentorship=defaults["mentorship"] if mentorship is None else mentorship,
        environment_quality=defaults["environment_quality"] if environment is None else environment,
        genomic_weight=defaults["genomic_weight"] if genomic_weight is None else genomic_weight, horizon=horizon)
    return JSONResponse(simulate(cfg).to_dict())


@app.get("/api/cohort")
def api_cohort(seed: int = 42, size: int = Query(64, ge=8, le=500), scenario: str = "global_digital_twin") -> dict:
    from .experiments import run_cohort
    return run_cohort(seed, size, scenario)


@app.get("/api/compare")
def api_compare(seed: int = 42, size: int = Query(48, ge=8, le=250)) -> dict:
    return compare_scenarios(seed, size)


@app.get("/api/experiments")
def api_experiments() -> dict:
    return EXPERIMENTS


@app.get("/api/experiment/counterfactual")
def api_counterfactual(seed: int = 42) -> dict:
    return counterfactual_lab(seed)


@app.get("/api/experiment/genomic-ablation")
def api_genomic_ablation(seed: int = 42, size: int = Query(48, ge=8, le=200)) -> dict:
    return genomic_ablation(seed, size)


@app.get("/api/experiment/sensitivity")
def api_sensitivity(seed: int = 42, samples: int = Query(96, ge=16, le=500)) -> dict:
    return sensitivity_analysis(seed, samples)


@app.get("/api/experiment/fairness")
def api_fairness(seed: int = 42, per_group: int = Query(24, ge=8, le=120)) -> dict:
    return fairness_lab(seed, per_group)


@app.get("/api/experiment/calibration")
def api_calibration(seed: int = 42, size: int = Query(72, ge=12, le=200)) -> dict:
    return calibration_lab(seed, size)


@app.get("/api/metadata")
def metadata() -> dict[str, Any]:
    return {"version": "3.0.0", "scenarios": SCENARIOS, "scenario_parameters": SCENARIO_PARAMS, "pathways": PATHWAYS,
        "system_layers": ["synthetic_genome_prior", "longitudinal_digital_twin", "irt_cat_assessment", "bayesian_knowledge_tracing",
            "forgetting_model", "active_exploration", "adaptive_curriculum", "pathway_posteriors", "causal_counterfactuals",
            "fairness_lab", "calibration_lab", "dynamic_labor_market", "life_course_stress_test", "governance_audit"],
        "disclaimer": "Synthetic research simulator. No real genetic, medical, psychological, or career inference is performed."}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "digital-twin", "version": "3.0.0", "research_mode": True}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")
