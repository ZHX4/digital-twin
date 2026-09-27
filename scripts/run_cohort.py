from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
import argparse,json
from pathlib import Path
from app.experiments import run_cohort
p=argparse.ArgumentParser();p.add_argument("--seed",type=int,default=42);p.add_argument("--size",type=int,default=100);p.add_argument("--scenario",default="global_digital_twin");a=p.parse_args()
Path("results").mkdir(exist_ok=True);r=run_cohort(a.seed,a.size,a.scenario);Path("results/cohort.json").write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
