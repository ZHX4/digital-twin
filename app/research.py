from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from typing import Any

from .benchmark import evaluate_benchmark
from .policy_search import search_policies
from .population import compare_population_policies

MODEL_VERSION = "4.0.0"

def config_hash(payload: dict[str, Any]) -> str:
    encoded=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(encoded).hexdigest()

def manifest(experiment: str, seed: int, parameters: dict[str, Any], results: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment": experiment,
        "model_version": MODEL_VERSION,
        "seed": seed,
        "git_commit": os.getenv("GIT_COMMIT", "unknown"),
        "config_hash": config_hash({"experiment":experiment,"seed":seed,"parameters":parameters}),
        "parameters": parameters,
        "result_keys": sorted(results.keys()),
        "interpretation": "Synthetic systems research artifact; not empirical evidence about real children or populations.",
    }

@lru_cache(maxsize=8)
def run_research_pack(seed: int = 42) -> dict:
    comparison = compare_population_policies(seed, learners=96, years=10)
    search = search_policies(seed+1, candidates=12, learners=64, years=8)
    benchmark = evaluate_benchmark(seed+2, learners=64, steps=18)
    results = {"policy_comparison": comparison, "policy_search": search, "benchmark": benchmark}
    return {"manifest": manifest("v4_research_pack", seed, {"population":96, "policy_candidates":12, "benchmark_learners":64}, results), **results}
