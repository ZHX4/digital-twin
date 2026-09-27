from __future__ import annotations

import random

from .models import CORE_SKILLS, PATHWAYS, LearningUnit
from .psychometrics import bkt_update

DOMAIN_TEMPLATES = {
    "mathematics": ["Number Sense", "Algebra", "Functions", "Calculus", "Probability", "Optimization"],
    "programming": ["Computational Thinking", "Python Foundations", "Data Structures", "Algorithms", "ML Systems", "Research Engineering"],
    "physics": ["Mechanics", "Waves", "Electricity", "Modeling", "Control", "Advanced Physics"],
    "biology": ["Life Systems", "Cell Biology", "Genetics Concepts", "Systems Biology", "Bioinformatics", "Research Methods"],
    "language": ["Reading", "Writing", "Argumentation", "Technical Communication", "Presentation", "Scientific Writing"],
    "spatial_reasoning": ["3D Reasoning", "Geometry", "CAD Thinking", "Spatial Computing", "Simulation", "Systems Visualization"],
    "design": ["Visual Composition", "Prototyping", "Interaction Design", "Product Thinking", "Creative Technology", "Design Research"],
    "social_reasoning": ["Collaboration", "Conflict Resolution", "Social Systems", "Leadership", "Negotiation", "Human Factors"],
    "systems_thinking": ["Causal Thinking", "Systems Mapping", "Complexity", "Architecture", "Simulation", "Systems Research"],
    "scientific_reasoning": ["Observation", "Experiment Design", "Inference", "Research Methods", "Evidence Synthesis", "Scientific Computing"],
    "creativity": ["Idea Generation", "Creative Constraints", "Synthesis", "Original Projects", "Creative Direction", "Research Creativity"],
    "self_regulation": ["Planning", "Attention", "Metacognition", "Project Management", "Independent Practice", "Research Discipline"],
}


def build_catalog() -> list[LearningUnit]:
    catalog: list[LearningUnit] = []
    for domain, titles in DOMAIN_TEMPLATES.items():
        for level, title in enumerate(titles, 1):
            prereq = [] if level == 1 else [f"{domain}:{level - 1}"]
            catalog.append(LearningUnit(id=f"{domain}:{level}", title=title, domain=domain, level=level,
                effort_hours=float(16 + level * 7), prerequisites=prereq, competency_gain=0.018 + level * 0.006,
                novelty=min(0.95, 0.12 + level * 0.13), social=min(0.9, 0.18 + level * 0.10),
                information_value=min(0.95, 0.20 + level * 0.08)))
    for i, title in enumerate(CORE_SKILLS, 1):
        catalog.append(LearningUnit(id=f"core:{i}", title=title.replace("_", " ").title(), domain="core", level=i,
            effort_hours=float(12 + i * 2), prerequisites=[], competency_gain=0.055 + 0.006 * i,
            novelty=0.10, social=0.25, information_value=0.12))
    return catalog

CATALOG = build_catalog()


def apply_forgetting(skills: dict[str, dict], months: float = 12.0) -> dict[str, dict]:
    out = {}
    for skill_id, state in skills.items():
        row = dict(state)
        decay = min(0.28, row.get("forgetting_rate", 0.055) * months / 12.0)
        old = row["mastery"]
        row["mastery"] = max(0.0, old * (1.0 - decay))
        row["uncertainty"] = min(0.99, row["uncertainty"] * 1.04 + decay * 0.08)
        row["velocity"] = row.get("velocity", 0.0) * 0.75 - (old - row["mastery"]) * 0.25
        out[skill_id] = row
    return out


def initialize_skill_state(capabilities: dict[str, float]) -> dict[str, dict]:
    return {f"{domain}:1": {"skill_id": f"{domain}:1", "domain": domain, "mastery": float(value),
        "uncertainty": 0.34, "velocity": 0.0, "forgetting_rate": 0.055, "prerequisites": []}
        for domain, value in capabilities.items()}


def select_curriculum(age: int, skills: dict[str, dict], capabilities: dict[str, float], pathway: str,
                      pace: float, max_units: int = 7) -> list[LearningUnit]:
    target_domains = set(PATHWAYS[pathway])
    candidates: list[tuple[float, LearningUnit]] = []
    level_ceiling = max(1, min(6, int(1 + age / 2.5)))
    for unit in CATALOG:
        if unit.domain != "core" and unit.domain not in target_domains:
            continue
        current = capabilities.get(unit.domain, 0.5) if unit.domain != "core" else sum(capabilities.values()) / len(capabilities)
        gap = max(0.0, 1.0 - current)
        prerequisite_ok = all(skills.get(p, {}).get("mastery", 0.0) >= 0.62 for p in unit.prerequisites)
        level_fit = 1.0 if unit.level <= level_ceiling else max(0.20, 1.0 - 0.18 * (unit.level - level_ceiling))
        exploration_value = unit.information_value * (0.6 + 0.4 * pace)
        score = 0.40 * gap + 0.22 * level_fit + 0.18 * unit.novelty + 0.12 * exploration_value + 0.08 * float(prerequisite_ok)
        candidates.append((score, unit))
    candidates.sort(key=lambda x: x[0], reverse=True)
    chosen: list[LearningUnit] = []
    used_domains = set()
    for score, unit in candidates:
        if unit.domain != "core" and unit.domain in used_domains and len(chosen) < max_units - 2:
            continue
        chosen.append(unit)
        if unit.domain != "core":
            used_domains.add(unit.domain)
        if len(chosen) >= max_units:
            break
    return chosen


def apply_learning(capabilities: dict[str, float], skills: dict[str, dict], units: list[LearningUnit],
                   rng: random.Random, teaching_quality: float, effort_factor: float) -> tuple[dict[str, float], dict[str, dict], float, int]:
    updated_caps = dict(capabilities)
    updated_skills = {k: dict(v) for k, v in skills.items()}
    hours = 0.0
    projects = 0
    for unit in units:
        noise = 0.86 + rng.random() * 0.24
        gain = unit.competency_gain * teaching_quality * effort_factor * noise
        mapped = ["self_regulation", "language", "scientific_reasoning"] if unit.domain == "core" else [unit.domain]
        for domain in mapped:
            updated_caps[domain] = min(0.995, updated_caps.get(domain, 0.5) + gain)
            primary = f"{domain}:{unit.level}" if f"{domain}:{unit.level}" in updated_skills else f"{domain}:1"
            prev = updated_skills.get(primary, {"mastery": updated_caps[domain], "uncertainty": 0.35, "velocity": 0.0,
                "forgetting_rate": 0.055, "skill_id": primary, "domain": domain, "prerequisites": []})
            prior = float(prev["mastery"])
            pseudo_correct = rng.random() < min(0.99, 0.62 + gain * 3.0)
            new_mastery = bkt_update(prior, pseudo_correct, learn=min(0.16, gain * 1.15 + 0.025))
            prev["velocity"] = new_mastery - prior
            prev["mastery"] = min(0.995, max(prior, new_mastery))
            prev["uncertainty"] = max(0.04, prev.get("uncertainty", 0.35) * 0.92)
            updated_skills[primary] = prev
        hours += unit.effort_hours * effort_factor
        projects += int(unit.level >= 4 and effort_factor > 0.75)
    return updated_caps, updated_skills, hours, projects
