from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health_endpoint():
    r=client.get("/health");assert r.status_code==200;assert r.json()["status"]=="ok";assert r.json()["version"]=="3.0.0"
def test_simulation_endpoint():
    r=client.get("/api/simulate?seed=42&scenario=global_digital_twin");assert r.status_code==200
    data=r.json();assert data["identity"]["age_horizon"]==16;assert len(data["recommendations"])==17;assert "ranked_pathways" in data["recommendations"][-1];assert len(data["assessments"])>=50
def test_research_endpoints():
    for path in ["/api/metadata","/api/experiments","/api/experiment/counterfactual","/api/experiment/fairness?per_group=8"]:
        assert client.get(path).status_code==200
def test_compare_endpoint():
    r=client.get("/api/compare?seed=42&size=8");assert r.status_code==200;assert set(r.json())=={"traditional","adaptive","genomic_adaptive","global_digital_twin"}
