from app.experiments import (
    calibration_lab,
    compare_scenarios,
    counterfactual_lab,
    fairness_lab,
    genomic_ablation,
    sensitivity_analysis,
)
from app.models import ChildConfig
from app.simulation import simulate


def test_reproducible_lifecycle():
    a=simulate(ChildConfig(seed=42)).to_dict();b=simulate(ChildConfig(seed=42)).to_dict();assert a==b;assert len(a["years"])==17
def test_research_layers_exist():
    state=simulate(ChildConfig(seed=7));assert len(state.evidence)>=50;assert len(state.assessments)>=50;assert len(state.camps)>=10;assert len(state.recommendations)==17;assert len(state.pathway_posteriors)==119;assert len(state.skills)==17;assert len(state.audit_log)>=17;assert len(state.life_course)>=14;assert state.years[-1].phase=="competency_gate";assert state.limitations
def test_outputs_are_bounded():
    state=simulate(ChildConfig(seed=123,acceleration=1,exploration=1,mentorship=1,environment_quality=1))
    for row in state.capabilities.values(): assert all(0<=v<=1 for v in row["capabilities"].values()) and all(0<=v<=1 for v in row["uncertainty"].values())
    assert 0<=state.impact.mismatch_risk<=1 and 0<=state.impact.wellbeing<=1 and 0<=state.impact.calibration_error<=1
def test_scenarios_are_distinct():
    results=compare_scenarios(seed=5,size=8);assert set(results)=={"traditional","adaptive","genomic_adaptive","global_digital_twin"};assert all(r["size"]==8 for r in results.values())
def test_counterfactual_lab():
    r=counterfactual_lab(5);assert "interventions" in r and "genomics_off" in r["interventions"] and "effects" in r["interventions"]["genomics_off"]
def test_genomic_ablation():
    r=genomic_ablation(5,size=8);assert "mean_effect_of_genomic_prior" in r and "competency_age" in r["mean_effect_of_genomic_prior"]
def test_sensitivity_lab():
    r=sensitivity_analysis(5,samples=16);assert len(r["sensitivity"])==5;assert all("pearson_proxy" in x for x in r["sensitivity"].values())
def test_fairness_lab():
    r=fairness_lab(5,per_group=8);assert len(r["groups"])==3;assert "competency_age" in r["gaps"]
def test_calibration_lab():
    r=calibration_lab(5,size=12)
    assert r["n"]>0
    assert 0<=r["calibrated"]["brier_multiclass"]<=2
    assert 0<=r["calibrated"]["ece_top_class"]<=1
    assert 0<=r["raw"]["brier_multiclass"]<=2
    assert 0<=r["raw"]["ece_top_class"]<=1
