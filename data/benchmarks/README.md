# Educational Benchmark Boundary

This directory intentionally contains **no downloaded third-party dataset**.

## Accepted interaction schema

The current CSV adapter accepts:

```text
learner_id,skill_id,correct,timestamp
```

Optional fields may be added later without changing the required contract.

## Recommended calibration sources

When a licensed educational dataset is added, record:

- source and publication;
- dataset version;
- license;
- download date;
- preprocessing commit;
- SHA-256 checksum;
- anonymization/privacy procedure;
- skill taxonomy mapping;
- train/validation/test split rule.

The simulator should be calibrated with behavior data, not real genetic profiles.
