# Reproducibility

## Seed contract
A simulation is deterministic with respect to seed, simulator version, scenario parameters, requested horizon and Python/NumPy numerical behavior.

```bash
python run.py --seed 42 --scenario global_digital_twin > results/twin_42.json
```

## Experiment provenance
Outputs should record seed, model version, scenario and experiment.

## CI contract
GitHub Actions runs the test suite and research smoke experiments.

## Data policy
The repository ships no personal data or real genomic data. Future external datasets require licensing, provenance, preprocessing and checksum metadata.
