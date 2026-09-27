# Digital Twin Evaluation Report — 2026-09-27

## Scope

Evaluation target: `ZHX4/digital-twin`

Evaluation branch: `evaluation/2026-09-27`

Baseline main commit: `2dbf341b6c6ecb48b1d3028780d42dffe1986be0`

Latest evaluation commit: `Phase 3/4 branch tip after validation synchronization`

The evaluation covered software correctness, API behavior, browser E2E, randomized invariants, maximum configured scale, HTTP performance, scientific diagnostics, static analysis, dependency security, and the repository's own research workflows.

## Phase 1 findings

### Functional bug found and fixed

Unknown policy names previously reached the simulation registry and caused uncaught `KeyError` exceptions.

Affected API surfaces:
- `/api/world/simulate`
- `/api/population`
- `/api/monte-carlo`

Unknown scenarios could also escape through:
- `/api/simulate`
- `/api/cohort`

They now return controlled HTTP 422 responses with explicit messages.

Regression tests cover both invalid policy and invalid scenario cases.

### Test-suite issue found and fixed

`tests/test_v4.py` contained duplicate definitions of:
- `test_tutor_agent_targets_uncertainty`
- `test_monte_carlo_and_shift`

These duplicates and an unused import were removed.

## Phase 2 engineering changes

### Static quality

The initial evaluation found 314 Ruff findings and 21 mypy errors.

The final branch now reports:

- **Ruff: 0 findings**
- **mypy: 0 errors**
- `compileall`: PASS
- **64 tests: PASS**

The type cleanup used explicit typed records for simulation outputs and benchmark interactions, explicit `ChildConfig` construction, and safer dictionary access patterns.

### Performance

Two deterministic expensive paths now use bounded in-process memoization:

- `search_policies`: `lru_cache(maxsize=32)`
- `run_research_pack`: `lru_cache(maxsize=8)`

Fresh-process measurement for `run_research_pack(42)`:

- cold call: **3.288 s**
- repeated call in the same process: **~0.000001 s**
- cached result was exactly equal to the cold result.

This cache is process-local and is intended to eliminate duplicate work during repeated dashboard/API requests; it is not a cross-worker or distributed cache.

### Calibration redesign

The previous calibration calculation treated next-year pathway persistence as if it were the directly predicted event and evaluated a scalar score against that outcome.

The calibration experiment was redesigned as a proper synthetic forecasting task:

1. At year `t`, use the complete `ranked_pathways` probability distribution.
2. At year `t+1`, use the actual next simulated recommended pathway as the outcome.
3. Compute a multiclass Brier score.
4. Compute top-class ECE and reliability bins.
5. Fit temperature scaling on a calibration half and evaluate on a separate holdout half.

For seed 42 and size 64:

- evaluation examples: **1024**
- fitted temperature: **0.4**
- raw multiclass Brier: **0.838118**
- calibrated multiclass Brier: **0.808019**
- raw top-class ECE: **0.741853**
- calibrated top-class ECE: **0.725685**

Temperature scaling improved both measured metrics, but calibration remains weak. This is a useful simulator diagnostic, not evidence of validated prediction quality.

## Final automated verification

### Static analysis

- Ruff: PASS, 0 findings
- mypy: PASS, 0 errors across 29 source files
- compileall: PASS

### Unit/integration tests

- pytest: **64 passed**
- `make test`: **PASS**
- `make research-v4`: **PASS**
- `make validation`: **PASS**

A FastAPI/Starlette deprecation warning remains in the test environment because the installed Starlette test client reports that direct httpx usage will change in a future version. This is a warning, not a test failure.

### Coverage

Final `pytest --cov=app`:

- total statements: **1566**
- missed: **62**
- total coverage: **96%**

Current lower-coverage areas include:

- `app/shift.py`: 68%
- `app/research.py`: 77%
- `app/learner_model.py`: 89%
- `app/world.py`: 93%
- `app/calibration.py`: 94%

These represent testing opportunities rather than observed functional failures.

### Dependency/security checks

`pip-audit -r requirements.txt`:
- **PASS**
- No known dependency vulnerabilities reported.

Bandit: **0 findings with B311 explicitly suppressed**. Before suppression, the only findings were low-severity B311 notices from deterministic `random.Random` used for reproducible simulation. No medium/high findings were present.

## Broader behavioral testing

Earlier in the evaluation, the system also passed:

### API surface

All exposed API endpoints were exercised with valid minimum workloads.

### Invalid-input testing

Out-of-range numeric inputs returned controlled HTTP 422 validation errors.

Unknown policies and scenarios no longer caused server exceptions.

### Reproducibility

Same seeds reproduced identical outputs.

Different seeds produced distinct hashes.

### Numerical invariants

No NaN/Inf values were found across the high-risk tested API outputs.

### Randomized property-style testing

120 randomized runs across multiple seeds, all five world policies, learner counts 8–64, and horizons 4–12 produced:

- 120/120 successful
- 0 bounded-metric failures
- 0 shape failures

### Maximum configured scale

Direct stress tests completed:

- 2,000 learners × 20 years world simulation: **8.39 s**
- 2,000 learners × 20 years population simulation: **9.56 s**

### HTTP load testing

Earlier real-Uvicorn measurements:

| Endpoint | Requests | Success | p50 | p95 |
|---|---:|---:|---:|---:|
| `/health` | 40 | 40/40 | 22.5 ms | 75.4 ms |
| `/api/world/simulate` (32×6) | 20 | 20/20 | 857.6 ms | 984.1 ms |
| `/api/policy-search` (8 candidates, 32×6) | 8 | 8/8 | 6.94 s | 6.95 s |
| `/api/research-pack` | 6 | 6/6 | 22.93 s | 23.01 s |

The caching introduced in Phase 2 changes repeated-call behavior substantially, while cold computation remains the relevant deployment cost.

## Browser E2E

A temporary public tunnel was used to expose a local Uvicorn instance to the browser automation layer. It was shut down after testing.

The browser smoke test verified:

- homepage load
- title and main heading
- Twin section
- World section
- Policy Lab
- Benchmark
- `/health`
- `/api/world/policies`
- `/api/model-registry`
- `/api/world/simulate`

Result: PASS.

A separate browser regression check confirmed that an invalid policy now returns HTTP 422 with:

`Unknown policy: does_not_exist`

## Research workflows

The repository's own workflows were executed after Phase 3/4:

- `make test`: PASS — 64 tests
- `make research-v4`: PASS
- research pack generation: PASS
- policy comparison: PASS
- sensitivity analysis: PASS
- fairness analysis: PASS
- calibration analysis: PASS

The latest research pack retains model version `4.0.0`.

## CI

GitHub Actions remains blocked by the runner/service layer rather than repository test failures.

The historical workflow run used for diagnosis had:

- conclusion: failure
- runner_id: 0
- empty runner name
- zero executed steps

Local execution of the equivalent checks succeeds.

## Scientific boundary

The simulator is internally reproducible and numerically stable under the tested configurations, but it remains a **synthetic systems simulator**.

Important limitations remain:

- The genome layer is synthetic and intentionally weak.
- The educational, causal, market, psychometric, and world models are simulation constructs rather than validated empirical instruments.
- The benchmark data are synthetic.
- Fairness groups are synthetic resource-access strata, not real demographic groups.
- Counterfactual outputs are model-based interventions, not causal evidence for real populations.
- Calibration results are simulator diagnostics, not external validation.
- The system must not be treated as a validated system for real children or real educational placement without external data, validated instruments, and independent ethical/causal evaluation.

## Phase 3 scientific validation

Phase 3 added boundary/invariant tests, paired genomic ablation, counterfactual separation tests, Monte Carlo convergence checks, deterministic confidence intervals, and calibration across four policies and multiple seeds.

Across 8 seeds with 32 learners and an 8-year horizon, the synthetic digital-twin competency mean was **0.380962** with bootstrap 95% interval **[0.372623, 0.388553]**; wellbeing mean was **0.754025** with interval **[0.751637, 0.756138]**.

The paired genomic-prior pathway-stability delta was **0.013664** with bootstrap 95% interval **[0.007264, 0.019034]**. This is an architectural ablation result only and is not evidence for real genetic utility.

Monte Carlo competency intervals narrowed in the tested configuration from **[0.36960, 0.38745]** at 4 repetitions to **[0.37437, 0.38275]** at 16 repetitions.

For `global_digital_twin`, mean multiclass Brier changed from **0.838612** raw to **0.809403** calibrated; top-class ECE changed from **0.747525** to **0.731768**. Calibration remains weak and simulator-internal.

## Phase 4 engineering validation

The API contract suite now covers valid endpoint requests, unknown policy/scenario values, numeric boundary inputs, response content types, and protection against HTTP 5xx responses. The CI workflow now runs Ruff, mypy, pytest, research smoke tests, the scientific validation runner, pip-audit, and Bandit.

`results/scientific_validation.json` records the 8-seed validation artifact. Reproduce it with:

`python scripts/run_validation.py --seed 42 --seeds 8 --learners 32 --years 8`
## Final state

Phases 2–4 completed the planned engineering and validation work:

- the original API exception bug is fixed
- Ruff is clean
- mypy is clean
- compilation is clean
- all 64 tests pass
- coverage remains 96% with 1,566 statements
- dependency audit is clean
- research workflows pass
- repeated expensive deterministic calls are cached
- calibration now uses an explicit multiclass next-year forecasting task with holdout temperature scaling
- scientific validation includes multi-seed confidence intervals, paired ablation, Monte Carlo convergence, and cross-policy calibration
- API contract and adversarial boundary tests are included
- CI now runs static analysis, dependency security checks, and the scientific validation smoke suite

The remaining engineering priorities are therefore concentrated in deeper empirical validation, additional coverage for low-tested modules, deployment architecture, and restoration of GitHub Actions runner availability.
