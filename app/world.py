from __future__ import annotations

import hashlib
import random
from dataclasses import asdict, dataclass
from statistics import mean, median
from typing import TypedDict

from .curriculum_agent import LinearUCBCurriculum
from .learner_model import (
    LatentLearnerState,
    competency_index,
    initial_state,
    learn,
    select_information_gap,
)
from .market import market_snapshot
from .tutor import TutorAgent

SKILL_TO_PATHWAY = {
    "machine_learning": "AI & Machine Learning",
    "programming": "AI & Machine Learning",
    "systems_engineering": "Robotics & Autonomous Systems",
    "scientific_reasoning": "Fundamental Science",
    "experimental_design": "Fundamental Science",
    "communication": "Language & Social Systems",
    "design": "Design & Creative Technology",
}

@dataclass(frozen=True)
class WorldPolicy:
    name: str
    specialization_age: int
    acceleration: float
    exploration: float
    mentorship: float
    teacher_ratio: float
    resource_equalization: float
    tutor_enabled: bool
    core_ratio: float
    objective_profile: str = "balanced"

POLICIES = {
    "traditional": WorldPolicy("traditional", 13, 0.35, 0.25, 0.45, 22, 0.10, False, 0.72, "stability"),
    "adaptive": WorldPolicy("adaptive", 11, 0.56, 0.65, 0.78, 16, 0.35, True, 0.60, "balanced"),
    "exploration_first": WorldPolicy("exploration_first", 13, 0.50, 0.95, 0.88, 14, 0.45, True, 0.58, "exploration"),
    "resource_balanced": WorldPolicy("resource_balanced", 12, 0.58, 0.72, 0.84, 14, 0.92, True, 0.62, "equity"),
    "digital_twin": WorldPolicy("digital_twin", 11, 0.76, 0.88, 0.94, 10, 0.82, True, 0.55, "balanced"),
}

@dataclass
class LearnerAgent:
    learner_id: str
    school_id: str
    family_id: str
    resource_access: float
    state: LatentLearnerState
    pathway: str | None = None
    interventions: int = 0

@dataclass(frozen=True)
class TeacherAgent:
    teacher_id: str
    school_id: str
    quality: float
    mentorship: float

@dataclass(frozen=True)
class FamilyAgent:
    family_id: str
    resource_access: float
    support: float
    stability: float

@dataclass(frozen=True)
class SchoolAgent:
    school_id: str
    resources: float
    teacher_capacity: float
    exploration_capacity: float
    culture: str


class TerminalLearner(TypedDict):
    learner_id: str
    resource_access: float
    resource_stratum: str
    competency: float
    wellbeing: float
    agency: float
    pathway: str
    mismatch_risk: float
    interventions: int

def _stable_seed(*parts: object) -> int:
    raw = "|".join(map(str, parts)).encode()
    return int(hashlib.sha256(raw).hexdigest()[:12], 16)

def _stratum(x: float) -> str:
    if x >= 0.80: return "high_resource"
    if x >= 0.60: return "mid_resource"
    return "low_resource"

def _school_culture(index: int) -> str:
    return ["research", "mastery", "community", "innovation"][index % 4]

def _choose_pathway(state: LatentLearnerState, age: int, policy: WorldPolicy) -> tuple[str | None, float]:
    if age < policy.specialization_age:
        return None, 0.0
    skill_scores = sorted(((v, SKILL_TO_PATHWAY.get(k)) for k, v in state.mastery.items() if k in SKILL_TO_PATHWAY), reverse=True)
    votes: dict[str, float] = {}
    for score, path in skill_scores:
        if path:
            votes[path] = votes.get(path, 0.0) + score
    if not votes:
        return None, 0.0
    total = sum(votes.values()) or 1.0
    path, score = max(votes.items(), key=lambda item: item[1])
    confidence = score / total
    return path, confidence

def _candidate_actions(gaps: list[str], explore: float) -> list:
    from .curriculum_agent import DEFAULT_ACTIONS
    actions = list(DEFAULT_ACTIONS)
    if explore < 0.45:
        actions = [a for a in actions if a.exploration <= 0.50]
    if gaps:
        actions.sort(key=lambda a: 0 if a.skill in gaps else 1)
    return actions

def simulate_world(seed: int = 42, learners: int = 128, years: int = 12, policy_name: str = "digital_twin",
                   schools: int | None = None, return_trajectories: bool = True, policy_override: WorldPolicy | None = None) -> dict:
    policy = policy_override or POLICIES[policy_name]
    school_count = schools or max(3, min(16, learners // 16))
    school_objs: list[SchoolAgent] = []
    teacher_objs: list[TeacherAgent] = []
    family_objs: list[FamilyAgent] = []
    learner_objs: list[LearnerAgent] = []
    rng = random.Random(seed)

    for s in range(school_count):
        resources = max(0.35, min(0.98, 0.48 + 0.42 * rng.random()))
        school_objs.append(SchoolAgent(f"school-{s:03d}", resources, 0.82 + 0.15 * rng.random(),
                                       0.40 + 0.55 * rng.random(), _school_culture(s)))
        teacher_count = max(2, round(25 / max(1.0, policy.teacher_ratio)))
        for t in range(teacher_count):
            teacher_objs.append(TeacherAgent(f"teacher-{s}-{t}", school_objs[-1].school_id,
                                             0.62 + 0.34 * rng.random(), policy.mentorship * (0.82 + 0.18 * rng.random())))

    for i in range(learners):
        local = random.Random(_stable_seed(seed, "learner", i))
        family_access = 0.36 + 0.60 * local.random()
        family = FamilyAgent(f"family-{i:04d}", family_access, 0.48 + 0.48 * local.random(), 0.50 + 0.48 * local.random())
        family_objs.append(family)
        school = school_objs[i % school_count]
        resource_access = max(0.20, min(1.0, 0.55 * family.resource_access + 0.45 * school.resources))
        state = initial_state(_stable_seed(seed, "latent", i), f"learner-{i:05d}", resource_access)
        learner_objs.append(LearnerAgent(f"learner-{i:05d}", school.school_id, family.family_id,
                                         round(resource_access, 4), state))

    teachers_by_school: dict[str, list[TeacherAgent]] = {}
    for teacher in teacher_objs:
        teachers_by_school.setdefault(teacher.school_id, []).append(teacher)
    schools_by_id = {s.school_id: s for s in school_objs}
    families_by_id = {f.family_id: f for f in family_objs}
    planners = {agent.learner_id: LinearUCBCurriculum(alpha=0.55) for agent in learner_objs}
    tutor = TutorAgent()
    trajectories: list[dict] = []

    for year in range(years):
        age = 5 + year
        snapshots: dict[str, list[float]] = {agent.school_id: [] for agent in learner_objs}
        for agent in learner_objs:
            snapshots[agent.school_id].append(competency_index(agent.state))
        school_peer = {sid: mean(values) if values else 0.5 for sid, values in snapshots.items()}
        for agent in learner_objs:
            local = random.Random(_stable_seed(seed, "year", year, agent.learner_id, policy_name))
            school = schools_by_id[agent.school_id]
            family = families_by_id[agent.family_id]
            teacher_pool = teachers_by_school[agent.school_id]
            teacher = teacher_pool[(year + int(agent.learner_id[-2:])) % len(teacher_pool)]
            peer_effect = max(-0.08, min(0.08, school_peer[agent.school_id] - competency_index(agent.state)))
            access = max(0.0, min(1.0, 0.72 * agent.resource_access + 0.20 * policy.resource_equalization
                               + 0.08 * school.exploration_capacity))
            gaps = select_information_gap(agent.state, top_k=5)
            focus_skill = gaps[0] if gaps else "programming"
            ctx = planners[agent.learner_id].context(
                age, 1.0 - competency_index(agent.state), max(agent.state.uncertainty.values()),
                agent.state.interests.get(focus_skill, 0.5), agent.state.wellbeing, agent.state.agency,
                access, policy.exploration,
            )
            actions = _candidate_actions(gaps, policy.exploration)
            action = planners[agent.learner_id].select(ctx, actions)
            if policy.core_ratio > 0.65 and action.exploration > 0.52 and local.random() > policy.exploration:
                action = actions[-1]
            intensity = min(1.0, action.intensity * (0.66 + 0.34 * policy.acceleration))
            quality = min(1.0, teacher.quality * (0.60 + 0.25 * teacher.mentorship + 0.15 * access))
            gain = learn(agent.state, action.skill, intensity, quality, peer_effect, transfer=True, rng=local)
            tutor_intervention = None
            tutor_gain = 0.0
            if policy.tutor_enabled and local.random() < 0.52:
                tutor_intervention = tutor.propose(agent.state, actions)
                tutor_gain = learn(agent.state, tutor_intervention.action.skill,
                                   0.23 + 0.23 * policy.mentorship, min(1.0, quality + 0.05),
                                   0.0, transfer=True, rng=local)
                gain += tutor_gain
                agent.interventions += 1
            reward = (
                0.45 * gain
                + 0.22 * agent.state.wellbeing
                + 0.14 * agent.state.agency
                + 0.10 * access
                + 0.09 * action.exploration
                - 0.07 * action.cost
            )
            planners[agent.learner_id].update(action, ctx, reward)
            agent.state.age = age
            if year > 0 and local.random() < 0.17:
                from .learner_model import forget
                forget(agent.state, 0.5)
            path, confidence = _choose_pathway(agent.state, age, policy)
            if path and confidence > 0.43:
                agent.pathway = path
            if return_trajectories:
                trajectories.append({
                    "year": year, "age": age, "learner_id": agent.learner_id, "school_id": agent.school_id,
                    "resource_stratum": _stratum(agent.resource_access), "competency": competency_index(agent.state),
                    "wellbeing": agent.state.wellbeing, "agency": agent.state.agency, "pathway": agent.pathway,
                    "action": action.action_id, "skill": action.skill, "gain": round(gain, 5),
                    "tutor_action": tutor_intervention.action.action_id if tutor_intervention else None,
                    "tutor_target": tutor_intervention.target_skill if tutor_intervention else None,
                    "tutor_gain": round(tutor_gain, 5),
                    "school_resources": school.resources, "peer_effect": round(peer_effect, 5),
                })

    terminal: list[TerminalLearner] = []
    for agent in learner_objs:
        competency = competency_index(agent.state)
        path = agent.pathway or "Undifferentiated"
        mismatch = 1.0 - max(agent.state.interests.get(skill, 0.5) for skill, p in SKILL_TO_PATHWAY.items() if p == path) if path != "Undifferentiated" else 0.35
        row: TerminalLearner = {
            "learner_id": agent.learner_id,
            "resource_access": agent.resource_access,
            "resource_stratum": _stratum(agent.resource_access),
            "competency": round(competency, 4),
            "wellbeing": round(agent.state.wellbeing, 4),
            "agency": round(agent.state.agency, 4),
            "pathway": path,
            "mismatch_risk": round(max(0.0, min(1.0, mismatch)), 4),
            "interventions": agent.interventions,
        }
        terminal.append(row)

    strata: dict[str, list[TerminalLearner]] = {}
    for row in terminal:
        strata.setdefault(row["resource_stratum"], []).append(row)
    distribution: dict[str, dict[str, float | int]] = {
        key: {
            "n": len(rows),
            "competency_mean": round(mean(r["competency"] for r in rows), 4),
            "wellbeing_mean": round(mean(r["wellbeing"] for r in rows), 4),
            "agency_mean": round(mean(r["agency"] for r in rows), 4),
            "mismatch_mean": round(mean(r["mismatch_risk"] for r in rows), 4),
        } for key, rows in strata.items()
    }
    inequality: dict[str, float] = {
        "competency_gap": round(max(x["competency_mean"] for x in distribution.values()) - min(x["competency_mean"] for x in distribution.values()), 4),
        "wellbeing_gap": round(max(x["wellbeing_mean"] for x in distribution.values()) - min(x["wellbeing_mean"] for x in distribution.values()), 4),
        "mismatch_gap": round(max(x["mismatch_mean"] for x in distribution.values()) - min(x["mismatch_mean"] for x in distribution.values()), 4),
    }
    market = market_snapshot(seed, 2040 + years)
    mean_competency = mean(x["competency"] for x in terminal)
    mean_wellbeing = mean(x["wellbeing"] for x in terminal)
    mean_agency = mean(x["agency"] for x in terminal)
    mean_mismatch = mean(x["mismatch_risk"] for x in terminal)
    return {
        "schema_version": "4.0",
        "seed": seed, "policy": asdict(policy), "learners": learners, "schools": school_count, "years": years,
        "metrics": {
            "competency_mean": round(mean_competency, 4), "competency_median": round(median(x["competency"] for x in terminal), 4),
            "wellbeing_mean": round(mean_wellbeing, 4), "agency_mean": round(mean_agency, 4),
            "mismatch_mean": round(mean_mismatch, 4),
            "equity_index": round(max(0.0, 1.0 - inequality["competency_gap"]), 4),
            "population_size": learners,
        },
        "distribution_by_resource": distribution,
        "inequality": inequality,
        "market_snapshot": market,
        "terminal": terminal,
        "trajectories": trajectories if return_trajectories else [],
        "planner_diagnostics": {a: p.diagnostics() for a, p in list(planners.items())[:8]},
    }
