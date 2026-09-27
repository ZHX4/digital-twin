from app.benchmark import evaluate_benchmark
from app.curriculum_agent import LinearUCBCurriculum
from app.learner_model import competency_index, initial_state, learn
from app.policy_search import pareto_frontier, search_policies
from app.population import bootstrap_ci, quantiles
from app.world import POLICIES, simulate_world


def test_latent_learner_transfer_and_forgetting():
    state = initial_state(42, "L-1", 0.8)
    before = state.mastery["machine_learning"]
    learn(state, "probability", 0.9, 0.95)
    assert 0 <= state.mastery["machine_learning"] <= 1
    assert state.mastery["machine_learning"] >= before
    old = state.mastery["probability"]
    from app.learner_model import forget
    forget(state, 1.0)
    assert state.mastery["probability"] <= old


def test_contextual_bandit_updates():
    planner = LinearUCBCurriculum()
    context = planner.context(10, 0.6, 0.4, 0.7, 0.8, 0.5, 0.8, 0.9)
    action = planner.select(context)
    planner.update(action, context, 0.9)
    assert planner.pulls[action.action_id] == 1


def test_world_is_population_scale():
    result = simulate_world(seed=42, learners=24, years=5, policy_name="digital_twin", return_trajectories=False)
    assert result["schema_version"] == "4.0"
    assert result["learners"] == 24
    assert result["schools"] >= 3
    assert result["metrics"]["population_size"] == 24
    assert set(result["distribution_by_resource"]) == {"high_resource", "mid_resource", "low_resource"}
    assert result["trajectories"] == []


def test_all_world_policies_run():
    for policy in POLICIES:
        result = simulate_world(seed=7, learners=12, years=4, policy_name=policy, return_trajectories=False)
        assert 0 <= result["metrics"]["competency_mean"] <= 1


def test_population_statistics():
    values = [0.1, 0.2, 0.3, 0.4, 0.5]
    qs = quantiles(values)
    lo, hi = bootstrap_ci(values, seed=1, rounds=100)
    assert qs["p50"] == 0.3
    assert lo <= 0.3 <= hi


def test_policy_search_and_pareto():
    result = search_policies(seed=3, candidates=4, learners=12, years=4)
    assert len(result["results"]) == 4
    assert len(result["pareto_frontier"]) >= 1
    front = pareto_frontier(result["results"])
    assert len(front) == len(result["pareto_frontier"])


def test_synthetic_benchmark():
    result = evaluate_benchmark(seed=9, learners=16, steps=8)
    assert set(result["methods"]) == {"global_rate", "learner_mastery", "digital_twin"}
    assert all(0 <= row["brier"] <= 1 for row in result["methods"].values())


def test_policy_search_does_not_mutate_registry():
    from app.policy_search import search_policies
    from app.world import POLICIES
    before = tuple(sorted(POLICIES))
    result = search_policies(seed=2, candidates=3, learners=10, years=4)
    after = tuple(sorted(POLICIES))
    assert before == after
    assert len(result["pareto_frontier"]) >= 1


def test_research_manifest_contains_result_keys():
    from app.research import run_research_pack
    # Use a lightweight direct manifest construction to avoid running the full pack in unit tests.
    from app.research import manifest
    out = manifest("unit", 1, {"x": 1}, {"alpha": {}, "beta": {}})
    assert out["model_version"] == "4.0.0"
    assert out["result_keys"] == ["alpha", "beta"]


def test_tutor_agent_targets_uncertainty():
    from app.tutor import TutorAgent
    from app.learner_model import initial_state
    state = initial_state(42, "tutor-test", 0.7)
    state.uncertainty["probability"] = 0.9
    state.misconceptions["probability"] = 0.8
    intervention = TutorAgent().propose(state)
    assert intervention.target_skill == "probability"
    assert intervention.reversible


def test_monte_carlo_and_shift():
    from app.population import monte_carlo_policy
    from app.shift import distribution_shift_report
    mc = monte_carlo_policy(seed=4, policy="digital_twin", repetitions=4, learners=12, years=4)
    assert mc["repetitions"] == 4
    assert "competency_mean" in mc["metrics"]
    report = distribution_shift_report({"x": [0, 1, 2, 3]}, {"x": [2, 3, 4, 5]})
    assert report["aggregate_score"] > 0


def test_tutor_agent_targets_uncertainty():
    from app.tutor import TutorAgent
    from app.learner_model import initial_state
    state = initial_state(42, "tutor-test", 0.7)
    state.uncertainty["probability"] = 0.9
    state.misconceptions["probability"] = 0.8
    intervention = TutorAgent().propose(state)
    assert intervention.target_skill == "probability"
    assert intervention.reversible


def test_monte_carlo_and_shift():
    from app.population import monte_carlo_policy
    from app.shift import distribution_shift_report
    mc = monte_carlo_policy(seed=4, policy="digital_twin", repetitions=4, learners=12, years=4)
    assert mc["repetitions"] == 4
    assert "competency_mean" in mc["metrics"]
    report = distribution_shift_report({"x": [0, 1, 2, 3]}, {"x": [2, 3, 4, 5]})
    assert report["aggregate_score"] > 0
