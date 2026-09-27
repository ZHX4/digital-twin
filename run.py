from __future__ import annotations

import argparse
import json

from app.models import ChildConfig
from app.simulation import simulate


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Digital Twin simulation")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scenario", default="global_digital_twin")
    parser.add_argument("--name", default="Astra")
    parser.add_argument("--horizon", type=int, default=16)
    args = parser.parse_args()
    state = simulate(ChildConfig(seed=args.seed, scenario=args.scenario, name=args.name, horizon=args.horizon))
    print(json.dumps(state.to_dict(), indent=2))


if __name__ == "__main__":
    main()
