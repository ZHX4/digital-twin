# Benchmark Suite

## Current benchmark

The v4 benchmark generates synthetic learner interactions and compares global-rate, learner-mastery and Digital-Twin proxy methods.

Metrics: Brier score, accuracy, expected calibration error and reliability bins.

## Real-data boundary

load_assistments_csv() defines a minimal ingestion contract:

```text
learner_id, skill_id, correct, timestamp
```

Before using real educational data, add dataset license, provenance, preprocessing version, checksum and ethical review metadata.

The benchmark exists to make model replacement measurable; synthetic performance is not empirical validation.
