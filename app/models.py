from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List

DOMAINS = [
    "mathematics", "programming", "physics", "biology", "language",
    "spatial_reasoning", "design", "social_reasoning", "systems_thinking",
    "scientific_reasoning", "creativity", "self_regulation",
]

PATHWAYS = {
    "AI & Machine Learning": ["mathematics", "programming", "scientific_reasoning", "systems_thinking"],
    "Robotics & Autonomous Systems": ["programming", "physics", "spatial_reasoning", "systems_thinking"],
    "Computational Biology": ["biology", "mathematics", "programming", "scientific_reasoning"],
    "Fundamental Science": ["mathematics", "physics", "scientific_reasoning", "systems_thinking"],
    "Human-Centered Computing": ["programming", "design", "social_reasoning", "language"],
    "Design & Creative Technology": ["design", "creativity", "spatial_reasoning", "programming"],
    "Language & Social Systems": ["language", "social_reasoning", "creativity", "self_regulation"],
}

CORE_SKILLS = [
    "numeracy", "literacy", "scientific_method", "computational_thinking",
    "communication", "collaboration", "health_and_safety", "ethics",
    "physical_capability", "self_management",
]

SCENARIOS = {
    "traditional": "Age-synchronized schooling with low personalization, low exploration and fixed progression.",
    "adaptive": "Mastery-oriented education with longitudinal assessment, mentorship and adaptive curriculum.",
    "genomic_adaptive": "Adaptive education with an explicitly weak, synthetic genomic prior entering the uncertainty model.",
    "global_digital_twin": "Closed-loop Digital Twin system with active exploration, competency gates, reversible pathways and human governance.",
}

SCENARIO_PARAMS = {
    "traditional": dict(acceleration=0.35, exploration=0.28, mentorship=0.45, environment_quality=0.72, genomic_weight=0.0),
    "adaptive": dict(acceleration=0.60, exploration=0.68, mentorship=0.80, environment_quality=0.86, genomic_weight=0.0),
    "genomic_adaptive": dict(acceleration=0.64, exploration=0.72, mentorship=0.84, environment_quality=0.88, genomic_weight=0.08),
    "global_digital_twin": dict(acceleration=0.78, exploration=0.90, mentorship=0.94, environment_quality=0.94, genomic_weight=0.05),
}


@dataclass
class ChildConfig:
    seed: int = 42
    name: str = "Astra"
    scenario: str = "global_digital_twin"
    acceleration: float = 0.78
    exploration: float = 0.90
    mentorship: float = 0.94
    environment_quality: float = 0.94
    curiosity: float = 0.80
    persistence: float = 0.82
    uncertainty_tolerance: float = 0.65
    genomic_weight: float = 0.05
    cohort_size: int = 64
    horizon: int = 16
    life_horizon: int = 30
    population: str = "synthetic-global"
    resource_access: float = 0.85


@dataclass
class Genome:
    model: str
    sequence_preview: str
    markers: Dict[str, str]
    synthetic_latents: Dict[str, float]
    factor_latents: Dict[str, float]
    uncertainty: Dict[str, float]
    prior_strength: float
    disclaimer: str


@dataclass
class Evidence:
    age: int
    source: str
    domain: str
    observed_mastery: float
    confidence: float
    context: str
    instrument: str = "synthetic_observation"
    item_count: int = 1
    notes: str = ""


@dataclass
class AssessmentResult:
    age: int
    domain: str
    theta: float
    standard_error: float
    accuracy: float
    items: int
    information_gain: float
    instrument: str


@dataclass
class SkillState:
    skill_id: str
    domain: str
    mastery: float
    uncertainty: float
    velocity: float
    forgetting_rate: float
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class LearningUnit:
    id: str
    title: str
    domain: str
    level: int
    effort_hours: float
    prerequisites: List[str]
    competency_gain: float
    novelty: float
    social: float
    information_value: float = 0.0


@dataclass
class CampResult:
    age: int
    camp: str
    domain: str
    prior_score: float
    performance: float
    enjoyment: float
    persistence: float
    posterior_score: float
    evidence_confidence: float
    information_gain: float


@dataclass
class PathwayPosterior:
    age: int
    pathway: str
    probability: float
    uncertainty: float
    entropy: float
    evidence_strength: float
    recommended_action: str
    exploration_priority: float
    contributing_domains: Dict[str, float]
    rationale: List[str]
    safety_flags: List[str]


@dataclass
class Recommendation:
    age: int
    pathway: str
    score: float
    confidence: float
    exploration_priority: float
    contributing_domains: Dict[str, float]
    ranked_pathways: Dict[str, float]
    rationale: List[str]
    safety_flags: List[str]


@dataclass
class YearRecord:
    age: int
    phase: str
    capability_index: float
    mastery_index: float
    uncertainty_index: float
    wellbeing: float
    engagement: float
    recommended_path: str
    confidence: float
    hours_learned: float
    projects_completed: int
    camps_completed: int
    evidence_count: int
    skill_count: int
    notes: List[str] = field(default_factory=list)


@dataclass
class ImpactMetrics:
    competency_age: float
    education_years: float
    pathway_stability: float
    mismatch_risk: float
    exploration_coverage: float
    wellbeing: float
    agency: float
    equity_index: float
    opportunity_cost: float
    calibration_error: float
    uncertainty_at_gate: float


@dataclass
class TwinState:
    identity: Dict
    genome: Genome
    capabilities: Dict[int, Dict]
    skills: Dict[int, Dict]
    evidence: List[Evidence]
    assessments: List[AssessmentResult]
    camps: List[CampResult]
    recommendations: List[Recommendation]
    pathway_posteriors: List[PathwayPosterior]
    curriculum: Dict[int, List[LearningUnit]]
    years: List[YearRecord]
    impact: ImpactMetrics
    market: Dict[int, Dict]
    life_course: Dict[int, Dict]
    experiments: Dict
    audit_log: List[Dict]
    limitations: List[str]
    scenario_description: str

    def to_dict(self) -> Dict:
        return asdict(self)
