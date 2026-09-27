from __future__ import annotations

import csv
import io
import random
from statistics import mean
from typing import TypedDict

from .calibration import evaluate
from .learner_model import initial_state, learn


class InteractionRow(TypedDict):
    learner_id: str
    step: int
    skill: str
    correct: int
    mastery: float



def _brier(predictions: list[float], outcomes: list[float]) -> float:
    return mean((p-y)**2 for p,y in zip(predictions,outcomes)) if predictions else 0.0

def _accuracy(predictions: list[float], outcomes: list[float]) -> float:
    return mean((p >= 0.5) == (y >= 0.5) for p,y in zip(predictions,outcomes)) if predictions else 0.0

def generate_synthetic_interactions(seed: int = 42, learners: int = 128, steps: int = 24) -> list[InteractionRow]:
    rng = random.Random(seed)
    rows: list[InteractionRow]=[]
    skills=["algebra","programming","probability","scientific_reasoning","communication"]
    for i in range(learners):
        state=initial_state(seed+i*31,f"bench-{i}",0.45+0.5*rng.random())
        for t in range(steps):
            skill=skills[(i*7+t)%len(skills)]
            p=state.mastery.get(skill,0.35)
            correct=rng.random()<p
            row: InteractionRow = {
                "learner_id": state.learner_id,
                "step": t,
                "skill": skill,
                "correct": int(correct),
                "mastery": p,
            }
            rows.append(row)
            learn(state,skill,0.35+0.3*rng.random(),0.72)
    return rows

def evaluate_benchmark(seed: int = 42, learners: int = 128, steps: int = 24) -> dict:
    rows=generate_synthetic_interactions(seed,learners,steps)
    by_learner: dict[str, list[InteractionRow]]={}
    for row in rows: by_learner.setdefault(row["learner_id"],[]).append(row)
    methods: dict[str, list[float]]={"global_rate":[],"learner_mastery":[],"digital_twin":[]}
    outcomes: list[float]=[]
    for items in by_learner.values():
        running: list[InteractionRow]=[]
        for row in items:
            skill=row["skill"]; hist=[x for x in running if x["skill"]==skill]
            global_pred=0.5 if not running else mean(x["correct"] for x in running)
            mastery_pred=row["mastery"]
            twin_pred=min(0.99,max(0.01,0.60*row["mastery"]+0.20*min(1.0,0.30+len(hist)/8)+0.20*(1.0-0.05*min(len(hist),8))))
            if running:
                methods["global_rate"].append(global_pred);methods["learner_mastery"].append(mastery_pred);methods["digital_twin"].append(twin_pred);outcomes.append(row["correct"])
            running.append(row)
    out={}
    for method,preds in methods.items():
        out[method]={"brier":round(_brier(preds,outcomes),5),"accuracy":round(_accuracy(preds,outcomes),5),
                     "calibration":evaluate(preds,outcomes)}
    return {"schema_version":"4.0","seed":seed,"learners":learners,"steps":steps,"methods":out,
            "dataset":"synthetic_interactions_v1","note":"Synthetic benchmark only. Replace with licensed educational data for empirical evaluation."}

def load_assistments_csv(csv_text: str) -> list[dict]:
    reader=csv.DictReader(io.StringIO(csv_text))
    required={"learner_id","skill_id","correct"}
    missing=required-set(reader.fieldnames or [])
    if missing: raise ValueError(f"Missing required columns: {sorted(missing)}")
    rows=[]
    for row in reader:
        rows.append({"learner_id":row["learner_id"],"skill_id":row["skill_id"],"correct":int(float(row["correct"])),"timestamp":row.get("timestamp")})
    return rows
