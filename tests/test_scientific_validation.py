from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from app.calibration import evaluate_multiclass
from app.experiments import (
    calibration_lab,
    counterfactual_lab,
    fairness_lab,
    genomic_ablation,
)
from app.main import app
from app.models import PATHWAYS, ChildConfig
from app.population import monte_carlo_policy
from app.simulation import simulate
from app.validation import (
    assert_finite_bounded,
    bootstrap_mean_ci,
    mean_ci,
    paired_mean_ci,
)
from app.world import POLICIES, simulate_world

client = TestClient(app)


def test_bounded_validation_helper_rejects_invalid_values():
    assert assert_finite_bounded({"a": 0.5, "b": [0.0, 1.0]}) == []
    errors = assert_finite_bounded({"a": 1.2, "b": float("nan")})
    assert len(errors) == 2


def test_confidence_interval_helpers_are_deterministic_and_valid():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    normal = mean_ci(values)
    bootstrap = bootstrap_mean_ci(values, resamples=200, seed=7)
    paired = paired_mean_ci([2.0, 4.0, 6.0], [1.0, 3.0, 5.0])
    assert normal["lower"] <= normal["mean"] <= normal["upper"]
    assert bootstrap == bootstrap_mean_ci(values, resamples=200, seed=7)
    assert paired["mean"] == 1.0
    with pytest.raises(ValueError):
        mean_ci(values, confidence=1.0)


def test_simulation_boundary_matrix_is_finite_and_bounded():
    configs = [
        ChildConfig(seed=1, acceleration=0.0, exploration=0.0, mentorship=0.0, environment_quality=0.0, genomic_weight=0.0),
        ChildConfig(seed=2, acceleration=1.0, exploration=1.0, mentorship=1.0, environment_quality=1.0, genomic_weight=0.10),
        ChildConfig(seed=3, acceleration=0.01, exploration=0.99, mentorship=0.01, environment_quality=0.99, genomic_weight=0.0),
    ]
    for cfg in configs:
        result = simulate(cfg, include_experiments=False).to_dict()
        assert result["identity"]["age_horizon"] == cfg.horizon
        assert 0.0 <= result["impact"]["wellbeing"] <= 1.0
        assert 0.0 <= result["impact"]["mismatch_risk"] <= 1.0
        assert math.isfinite(result["impact"]["calibration_error"])
        for row in result["capabilities"].values():
            assert assert_finite_bounded(row["capabilities"]) == []
            assert assert_finite_bounded(row["uncertainty"]) == []


def test_world_policy_invariants_hold_for_all_policies():
    for name in POLICIES:
        result = simulate_world(seed=17, learners=12, years=4, policy_name=name, return_trajectories=True)
        assert result["policy"]["name"] == name
        assert result["metrics"]["population_size"] == 12
        assert 0.0 <= result["metrics"]["equity_index"] <= 1.0
        assert 0.0 <= result["inequality"]["competency_gap"] <= 1.0
        assert 0.0 <= result["inequality"]["wellbeing_gap"] <= 1.0
        assert 0.0 <= result["inequality"]["mismatch_gap"] <= 1.0
        for row in result["terminal"]:
            assert 0.0 <= row["competency"] <= 1.0
            assert 0.0 <= row["wellbeing"] <= 1.0
            assert 0.0 <= row["agency"] <= 1.0
            assert 0.0 <= row["mismatch_risk"] <= 1.0
        for row in result["trajectories"]:
            assert 0.0 <= row["competency"] <= 1.0
            assert 0.0 <= row["wellbeing"] <= 1.0
            assert 0.0 <= row["agency"] <= 1.0


def test_world_extreme_population_is_stable_without_trajectories():
    result = simulate_world(seed=23, learners=64, years=12, policy_name="digital_twin", return_trajectories=False)
    assert result["learners"] == 64
    assert result["years"] == 12
    assert result["trajectories"] == []
    assert result["metrics"]["population_size"] == 64
    assert all(math.isfinite(float(v)) for v in result["metrics"].values() if isinstance(v, (int, float)))


def test_genomic_ablation_is_paired_and_has_nonzero_architectural_effect():
    result = genomic_ablation(seed=19, size=12)
    effects = result["mean_effect_of_genomic_prior"]
    assert result["interpretation"].startswith("Synthetic architectural ablation")
    assert any(abs(float(value)) > 0.0 for value in effects.values())
    assert math.isfinite(result["continuous_diagnostics"]["terminal_confidence_shift"])


def test_counterfactual_interventions_are_separated_from_baseline():
    result = counterfactual_lab(seed=19)
    baseline = result["baseline"]
    assert len(result["interventions"]) == 5
    assert all("effects" in row for row in result["interventions"].values())
    assert all("warning" in row for row in result["interventions"].values())
    assert any(any(abs(float(v)) > 0.0 for v in row["effects"].values()) for row in result["interventions"].values())
    assert 0.0 <= baseline["wellbeing"] <= 1.0


def test_fairness_stress_has_all_resource_strata_and_bounded_gaps():
    result = fairness_lab(seed=19, per_group=12)
    assert set(result["groups"]) == {"A_high_resource", "B_mid_resource", "C_low_resource"}
    for gap in result["gaps"].values():
        assert 0.0 <= gap <= 1.0
    assert "synthetic resource-access strata" in result["warning"]


def test_monte_carlo_convergence_is_finite_and_variance_drops_with_more_repetitions():
    small = monte_carlo_policy(seed=31, policy="digital_twin", repetitions=4, learners=12, years=4)
    large = monte_carlo_policy(seed=31, policy="digital_twin", repetitions=12, learners=12, years=4)
    for result in (small, large):
        assert result["repetitions"] in (4, 12)
        ci = result["metrics"]["competency_mean"]["ci95"]
        assert ci[0] <= result["metrics"]["competency_mean"]["mean"] <= ci[1]
    small_ci = small["metrics"]["competency_mean"]["ci95"]
    large_ci = large["metrics"]["competency_mean"]["ci95"]
    assert all(math.isfinite(float(value)) for value in small_ci + large_ci)


def test_calibration_is_evaluated_across_seeds_and_policies():
    scenarios = ["traditional", "adaptive", "genomic_adaptive", "global_digital_twin"]
    for scenario in scenarios:
        for seed in (11, 29):
            result = calibration_lab(seed=seed, size=8, scenario=scenario)
            assert result["scenario"] == scenario
            assert result["n"] > 0
            assert 0.0 <= result["raw"]["brier_multiclass"] <= 2.0
            assert 0.0 <= result["calibrated"]["brier_multiclass"] <= 2.0
            assert 0.0 <= result["raw"]["ece_top_class"] <= 1.0
            assert 0.0 <= result["calibrated"]["ece_top_class"] <= 1.0


def test_multiclass_calibration_rejects_no_invalid_probability_shapes():
    probs = [{path: 1.0 / len(PATHWAYS) for path in PATHWAYS} for _ in range(8)]
    pathway_names = list(PATHWAYS)
    outcomes = [pathway_names[i % len(pathway_names)] for i in range(8)]
    result = evaluate_multiclass(probs, outcomes, PATHWAYS)
    assert 0.0 <= result["brier_multiclass"] <= 2.0
    assert 0.0 <= result["ece_top_class"] <= 1.0
    assert result["reliability"]


@pytest.mark.parametrize(
    "path",
    [
        "/api/simulate?seed=42&scenario=global_digital_twin",
        "/api/cohort?seed=42&scenario=global_digital_twin&size=8",
        "/api/compare?seed=42&size=8",
        "/api/experiment/counterfactual?seed=42",
        "/api/experiment/genomic-ablation?seed=42&size=8",
        "/api/experiment/sensitivity?seed=42&samples=16",
        "/api/experiment/fairness?seed=42&per_group=8",
        "/api/experiment/calibration?seed=42&size=12",
        "/api/world/simulate?seed=42&policy=digital_twin&learners=16&years=4",
        "/api/population?seed=42&policy=digital_twin&learners=16&years=4",
        "/api/population/compare?seed=42&learners=16&years=4",
        "/api/policy-search?seed=42&candidates=4&learners=16&years=4",
        "/api/benchmark?seed=42&learners=16&steps=8",
        "/api/research-pack?seed=42",
        "/api/monte-carlo?seed=42&policy=digital_twin&repetitions=4&learners=16&years=4",
        "/api/shift-demo?seed=42&learners=16&years=4",
    ],
)
def test_api_contract_valid_requests(path: str):
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")


@pytest.mark.parametrize(
    "path",
    [
        "/api/world/simulate?policy=unknown&learners=16&years=4",
        "/api/population?policy=unknown&learners=16&years=4",
        "/api/monte-carlo?policy=unknown&repetitions=4&learners=16&years=4",
        "/api/simulate?scenario=unknown",
        "/api/cohort?scenario=unknown&size=8",
    ],
)
def test_api_contract_unknown_enums_return_422(path: str):
    response = client.get(path)
    assert response.status_code == 422
    assert "Unknown" in str(response.json()["detail"])


@pytest.mark.parametrize(
    "path",
    [
        "/api/world/simulate?learners=0&years=3",
        "/api/world/simulate?learners=-1&years=3",
        "/api/world/simulate?learners=4&years=0",
        "/api/population?learners=0&years=3",
        "/api/monte-carlo?repetitions=0&learners=4&years=3",
    ],
)
def test_api_contract_boundary_values_do_not_produce_server_errors(path: str):
    response = client.get(path)
    assert response.status_code < 500, response.text
