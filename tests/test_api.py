from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "4.0.0"


def test_simulation_endpoint():
    response = client.get("/api/simulate?seed=42&scenario=global_digital_twin")
    assert response.status_code == 200
    data = response.json()
    assert data["identity"]["age_horizon"] == 16
    assert len(data["recommendations"]) == 17
    assert "ranked_pathways" in data["recommendations"][-1]
    assert len(data["assessments"]) >= 50


def test_research_endpoints():
    for path in [
        "/api/metadata",
        "/api/experiments",
        "/api/experiment/counterfactual",
        "/api/experiment/fairness?per_group=8",
    ]:
        assert client.get(path).status_code == 200


def test_compare_endpoint():
    response = client.get("/api/compare?seed=42&size=8")
    assert response.status_code == 200
    assert set(response.json()) == {
        "traditional",
        "adaptive",
        "genomic_adaptive",
        "global_digital_twin",
    }


def test_v4_world_and_research_endpoints():
    for path in [
        "/api/world/policies",
        "/api/world/simulate?seed=42&learners=12&years=4",
        "/api/population?seed=42&learners=16&years=4",
        "/api/population/compare?seed=42&learners=16&years=4",
        "/api/policy-search?seed=42&candidates=4&learners=16&years=4",
        "/api/benchmark?seed=42&learners=16&steps=8",
        "/api/model-registry",
        "/api/monte-carlo?seed=42&policy=digital_twin&repetitions=4&learners=16&years=4",
        "/api/shift-demo?seed=42&learners=16&years=4",
    ]:
        response = client.get(path)
        assert response.status_code == 200, path
    assert client.get("/api/world/simulate?learners=12&years=4").json()["schema_version"] == "4.0"


def test_unknown_policy_is_controlled_validation_error():
    for path in [
        "/api/world/simulate?policy=does_not_exist&learners=8&years=4",
        "/api/population?policy=does_not_exist&learners=16&years=4",
        "/api/monte-carlo?policy=does_not_exist&repetitions=4&learners=16&years=4",
    ]:
        response = client.get(path)
        assert response.status_code == 422
        assert "Unknown policy" in response.json()["detail"]


def test_unknown_scenario_is_controlled_validation_error():
    for path in [
        "/api/simulate?scenario=does_not_exist",
        "/api/cohort?scenario=does_not_exist&size=8",
    ]:
        response = client.get(path)
        assert response.status_code == 422
        assert "Unknown scenario" in response.json()["detail"]
