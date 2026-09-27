from __future__ import annotations

import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
import argparse
import json
from pathlib import Path

from app.experiments import compare_scenarios

p=argparse.ArgumentParser();p.add_argument("--seed",type=int,default=42);p.add_argument("--size",type=int,default=100);a=p.parse_args()
Path("results").mkdir(exist_ok=True);r=compare_scenarios(a.seed,a.size);Path("results/policy_comparison.json").write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
