# Digital Twin Evaluation Report — 2026-09-27

## Scope

Evaluation target: `ZHX4/digital-twin`

Evaluation branch: `evaluation/2026-09-27`

Baseline main commit: `2dbf341b6c6ecb48b1d3028780d42dffe1986be0`

Evaluation head after fixes: `9ddb6b75ef0e62d52474a2e644be70010886512e`

The evaluation covered software correctness, API behavior, browser E2E, randomized invariants, maximum configured scale, performance, security/dependency posture, research experiment execution, reproducibility, and selected scientific diagnostics.

## Baseline findings

### Functional

- Python dependency installation: PASS
- Bytecode compilation: PASS
- Pytest baseline: PASS
- All 21 exposed API endpoints with valid minimum workloads: PASS
- Documented research CLI commands: PASS
- v4 research pack: PASS
- Same-seed reproducibility: PASS
- Different-seed variation: PASS
- No NaN/Inf observed in tested high-risk API outputs: PASS

### Bug found and fixed

Unknown policy names were not validated at the API boundary and caused an uncaught `KeyError`.

Affected paths:
- `/api/world/simulate`
- `/api/population`
- `/api/monte-carlo`

Unknown scenarios could also escape as unhandled errors through:
- `/api/simulate`
- `/api/cohort`

The API now returns HTTP 422 with an explicit validation message instead of an internal exception.

Regression tests were added for both policy and scenario validation.

### Test-suite quality issue found and fixed

`tests/test_v4.py` contained duplicate definitions of:
- `test_tutor_agent_targets_uncertainty`
- `test_monte_carlo_and_shift`

One unused import was also removed.

The final suite reports 27 passing tests.

## Coverage

Final `pytest --cov=app` result:

- 27 passed
- 96% total statement coverage
- 62 uncovered statements

Lowest-coverage modules include:
- `app/shift.py`
- `app/research.py`
- `app/benchmark.py`
- `app/causal.py`

These are coverage opportunities, not observed runtime failures.

## Randomized/property-style testing

120 randomized API runs across:
- multiple seeds
- all five world policies
- learner counts 8–64
- horizons 4–12

Result: 120/120 successful with no bounded-metric or shape invariant failures.

## Maximum configured scale

Direct stress tests completed successfully:

- 2,000 learners × 20 years world simulation: PASS, 8.39 s
- 2,000 learners × 20 years population simulation: PASS, 9.56 s

## HTTP load testing

A real Uvicorn server was exercised over HTTP.

Observed results:

| Endpoint | Requests | Success | p50 | p95 |
|---|---:|---:|---:|---:|
| /health | 40 | 40/40 | 22.5 ms | 75.4 ms |
| /api/world/simulate (32×6) | 20 | 20/20 | 857.6 ms | 984.1 ms |
| /api/policy-search (8 candidates, 32×6) | 8 | 8/8 | 6.94 s | 6.95 s |
| /api/research-pack | 6 | 6/6 | 22.93 s | 23.01 s |

The research pack and policy search are computationally expensive; this is an important deployment/performance characteristic.

## Browser E2E

Because no Vercel project/deployment exists for the repository, a temporary local-to-public tunnel was used only for testing and was shut down afterward.

Browser E2E verified:
- homepage loading
- title and main heading
- Twin section
- World section
- Policy Lab
- Benchmark
- /health
- /api/world/policies
- /api/model-registry
- /api/world/simulate

Result: PASS.

A browser regression test also confirmed the fixed invalid-policy behavior:
- HTTP 422
- `Unknown policy: does_not_exist`

## Security/dependency checks

### pip-audit

Result: PASS

No known dependency vulnerabilities were reported for the declared requirements.

### Bandit

Bandit reports 16 low-severity B311 findings caused by the use of Python's deterministic `random.Random` in simulation code.

These are not cryptographic/security randomness uses; they are simulation PRNGs. They should eventually be configured/suppressed explicitly rather than replaced with cryptographic randomness.

### Ruff

Current result: 314 findings.

Main categories:
- UP006 / UP035 modernization findings
- I001 import ordering
- F401 unused imports
- minor code-quality findings

These are predominantly maintainability/style issues rather than demonstrated runtime defects.

### mypy

Current result: 21 type errors in 6 modules.

Main concentration:
- `app/recommendation.py`
- `app/psychometrics.py`
- `app/benchmark.py`
- `app/simulation.py`
- `app/experiments.py`
- `app/world.py`

The code executes successfully despite these static typing defects.

## Scientific diagnostics

The simulator is internally reproducible and numerically stable under the tested conditions, but its outputs remain synthetic.

The calibration experiment produced:
- Brier score: 0.639282
- ECE: 0.7356

This is a material warning about calibration quality for the current synthetic pathway-persistence proxy. It should be treated as a diagnostic result, not as evidence that the model is well calibrated.

The genomic ablation experiment showed only small mean synthetic effects in the tested configuration. This does not establish real-world genetic predictive utility.

The fairness experiment explicitly uses synthetic resource-access strata rather than demographic data.

The repository's v4 architecture correctly documents the scientific boundary: the simulator is not empirical evidence until validated against external datasets and validated models.

## CI

GitHub Actions remains unavailable at the runner layer.

The latest workflow run completed with:
- conclusion: failure
- runner_id: 0
- runner_name: empty
- steps: none

This means the workflow failed before executing its test steps. Local execution of the same relevant checks succeeded.

## Project-defined workflow

The repository's own targets were executed after the fixes:

- `make test`: PASS — 27 tests
- `make research-v4`: PASS

## Changes made on evaluation branch

1. Added controlled policy validation to the API.
2. Added controlled scenario validation to the API.
3. Added regression tests for invalid policy/scenario inputs.
4. Removed duplicate v4 test definitions and unused import.
5. Re-ran the full functional and research suite after the fixes.

No changes were made to `main`.

## Remaining issues

The principal remaining engineering work is:

1. Reduce the 314 Ruff findings.
2. Resolve the 21 mypy findings.
3. Add targeted tests for low-coverage modules.
4. Improve calibration methodology and validate it against an explicit empirical prediction task.
5. Improve the performance of the research pack and policy-search endpoints for interactive deployment.
6. Restore a functioning GitHub Actions runner path.
7. Replace the synthetic benchmark with a documented, licensed educational dataset before making empirical claims.
