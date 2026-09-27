from __future__ import annotations

import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
import argparse
import json
from pathlib import Path

from app.experiments import (
    calibration_lab,
    compare_scenarios,
    counterfactual_lab,
    fairness_lab,
    genomic_ablation,
    sensitivity_analysis,
)

OUT = Path("results")
def main() -> None:
    p=argparse.ArgumentParser(description="Digital Twin reproducible research experiments")
    p.add_argument("experiment",choices=["policy-comparison","counterfactual","genomic-ablation","sensitivity","fairness","calibration"])
    p.add_argument("--seed",type=int,default=42);p.add_argument("--size",type=int,default=48);p.add_argument("--samples",type=int,default=96);p.add_argument("--per-group",type=int,default=24);args=p.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.experiment=="policy-comparison": result=compare_scenarios(args.seed,args.size)
    elif args.experiment=="counterfactual": result=counterfactual_lab(args.seed)
    elif args.experiment=="genomic-ablation": result=genomic_ablation(args.seed,args.size)
    elif args.experiment=="sensitivity": result=sensitivity_analysis(args.seed,args.samples)
    elif args.experiment=="fairness": result=fairness_lab(args.seed,args.per_group)
    else: result=calibration_lab(args.seed,args.size)
    path=OUT/f"{args.experiment.replace('-','_')}.json";path.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"output":str(path),"experiment":args.experiment},indent=2))
if __name__=="__main__": main()
