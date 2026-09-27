from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.research import run_research_pack


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Digital Twin v4 research pack.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="results/v4_research_pack.json")
    args = parser.parse_args()

    result = run_research_pack(args.seed)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(path),
        "experiment": result["manifest"]["experiment"],
        "model_version": result["manifest"]["model_version"],
        "config_hash": result["manifest"]["config_hash"],
    }, indent=2))


if __name__ == "__main__":
    main()
