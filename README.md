
## v4.0 — From Digital Twin to World Laboratory

The repository now has an executable multi-scale layer above the original longitudinal twin:

- Latent learner model: explicit mastery, uncertainty, retention, misconceptions and cross-skill transfer.
- Knowledge graph: prerequisite-linked skills instead of independent domain scores.
- Contextual-bandit curriculum: linear-UCB planner chooses learning interventions from learner/environment context.
- Multi-agent world: learners, families, teachers and schools interact over time.
- Population simulation: hundreds/thousands of synthetic learners with quantiles and bootstrap intervals.
- Education policy simulator: explicit policy objects rather than hard-coded scenarios.
- Pareto policy search: learning, wellbeing, agency, equity, mismatch and inequality are treated as competing objectives.
- Benchmark suite: reproducible learner-model comparison with Brier, accuracy and ECE diagnostics plus a real-data ingestion boundary.
- Research dashboard: Twin, World, Policy Lab and Benchmark views are exposed from the default UI.

### New research loop

```text
Learner state
   ↓
Curriculum action
   ↓
Teacher / school / family context
   ↓
Population trajectory
   ↓
Policy comparison
   ↓
Pareto frontier
   ↓
Counterfactual questions
```

The v4 world remains synthetic. Its purpose is to make the assumptions of a future education system executable and falsifiable before empirical calibration.

### New endpoints

- GET /api/world/simulate
- GET /api/world/policies
- GET /api/population
- GET /api/population/compare
- GET /api/policy-search
- GET /api/benchmark
- GET /api/research-pack

# Digital Twin

> **A synthetic research laboratory for a future education system that models each learner as a continuously updated Digital Twin.**

[![Research CI](https://github.com/ZHX4/Digital-Twin/actions/workflows/tests.yml/badge.svg)](https://github.com/ZHX4/Digital-Twin/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)
![Status](https://img.shields.io/badge/status-research%20prototype-7B61FF)
![Scope](https://img.shields.io/badge/data-synthetic%20only-5EE8F5)

![System map](docs/assets/system-map.svg)

Digital Twin is deliberately more than a dashboard. It is a **closed-loop systems simulator** for a hypothetical educational architecture:

```text
Synthetic Birth Data → Longitudinal Twin → Assessment / Exploration / Environment
→ Bayesian-style posterior → Adaptive curriculum → Projects / Camps / Mentorship
→ New evidence → Updated Twin

Governance / Causal Lab: counterfactuals · fairness · calibration · ablations
→ Competency gate → life-course stress test
```

## The research question

**What changes when we replace age-synchronized education with a longitudinal, competency-driven system that continuously models the learner and adapts the learning environment?**

This is a **future-systems laboratory**, not an implementation proposal for real children. Assumptions are explicit, mechanisms are inspectable, experiments are seeded, and outputs are framed as synthetic model behavior rather than human evidence.

## Why it is interesting

The prototype combines:

- longitudinal Digital Twin state;
- IRT/CAT-style adaptive assessment;
- Bayesian Knowledge Tracing-inspired mastery updates;
- forgetting and skill velocity;
- active exploration as information acquisition;
- probabilistic pathway posteriors rather than one-shot career labels;
- competency gates rather than fixed graduation ages;
- model-based counterfactual interventions;
- synthetic genomic-prior ablation;
- synthetic resource-equity stress tests;
- calibration diagnostics;
- dynamic labor-market stress tests;
- a life-course extension through age 30;
- explicit governance and reversibility gates.

The research object is the **feedback loop**, not one individual model.

## Simulator

For a seeded virtual learner, the simulator evolves a state from age 0 to 16:

[
S_t = {C_t, K_t, I_t, U_t, W_t, E_{0:t}, X_{0:t}}
]

where capability, skill mastery, interests, uncertainty, wellbeing, evidence and exploration history are updated longitudinally.

Each year follows:

[
S_t ightarrow assessment ightarrow exploration ightarrow curriculum
ightarrow learning ightarrow evidence ightarrow S_{t+1}
]

A competency gate can trigger before the default horizon when synthetic mastery, skill coverage, wellbeing and pathway stability satisfy configured conditions.

## Scientific layers

### Synthetic genomic prior

The genome module generates fictional markers and latent factors. It is **not a real genotype model**. Its contribution is bounded and can be switched off in the genomic-ablation experiment.

The architectural question is: what happens when a high-status, apparently objective prior enters a high-impact decision pipeline? The system therefore treats the genomic signal as a weak, uncertain prior rather than a destiny variable.

### Psychometrics

The assessment engine uses an IRT/CAT-style simulation:

[
P(X=1|	heta,b,a)=sigma(a(	heta-b))
]

It reports estimated ability, standard error, response accuracy, item count and information gain.

### Skill graph

Broad capabilities are decomposed into prerequisite-linked skills. Skill states track mastery, uncertainty, velocity and forgetting.

### Learning and forgetting

[
K_{t+1}=K_t+Learning_t-Forgetting_t+Transfer_t
]

The simulator explicitly models learning and forgetting; transfer is a documented extension point.

### Active exploration

The Digital Twin can select a camp because the system is uncertain, not merely because a pathway currently has the highest score:

[
a^*=argmax_a VOI(a)
]

where (VOI) is a synthetic value-of-information quantity.

### Pathway posterior

The system maintains a distribution over pathways rather than a hard class. High entropy triggers exploration and governance flags.

### Causal / counterfactual laboratory

The runner holds a seed fixed and intervenes on mentorship, acceleration, exploration, genomic prior or education regime. Outputs are explicitly **model-based synthetic treatment effects**.

### Equity laboratory

Synthetic resource-access strata stress-test gaps in competency age, wellbeing, mismatch risk and pathway confidence. No demographic or protected-class inference is performed.

### Life-course stress test

After the competency gate, the simulator can extend through age 30 and expose the final pathway to a synthetic labor market with changing demand, mobility, research intensity and automation exposure. This is a systems stress test, not an individual-life predictor.

## Research experiments

| Experiment | Core question |
|---|---|
| Policy comparison | How do synthetic education regimes differ under the same model family? |
| Counterfactual lab | What changes when one intervention changes while the seed is held fixed? |
| Genomic ablation | Does a weak synthetic genomic prior materially change simulated outputs? |
| Sensitivity sweep | Which assumptions most affect simulated competency time? |
| Fairness lab | Do unequal resource levels widen synthetic outcome gaps? |
| Calibration lab | Do posterior confidences behave like calibrated probabilities? |

Run the complete suite:

```bash
make research
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/` for the research laboratory UI and `/docs` for OpenAPI.

## CLI

```bash
python run.py --seed 42 --scenario global_digital_twin
python scripts/run_experiment.py policy-comparison --size 64
python scripts/run_experiment.py counterfactual
python scripts/run_experiment.py genomic-ablation --size 64
python scripts/run_experiment.py sensitivity --samples 128
python scripts/run_experiment.py fairness --per-group 24
python scripts/run_experiment.py calibration --size 64
```

## Repository map

```text
app/
├── models.py                 typed research state and schemas
├── genetics.py               synthetic genomic prior
├── psychometrics.py          IRT/CAT + calibration diagnostics
├── learning.py               skill graph, BKT-inspired updates, forgetting
├── camps.py                  exploration and value-of-information signals
├── recommendation.py         pathway posteriors and uncertainty
├── environment.py            synthetic developmental environment
├── market.py                 dynamic synthetic labor market
├── life_course.py            post-gate stress test to age 30
├── causal.py                 counterfactual intervention helpers
├── equity.py                 synthetic resource-access fairness lab
├── calibration.py            probability-quality metrics
├── ethics.py                 governance gates and audit requirements
├── experiments.py            cohort + ablation + sensitivity + fairness + calibration
├── experiments_registry.py   research catalogue
├── simulation.py             longitudinal closed-loop Digital Twin
├── main.py                   FastAPI research API
└── static/                   research laboratory frontend

docs/
├── architecture.md
├── benchmark-matrix.md
├── reproducibility.md
├── model-card.md
├── ethical-design.md
├── threat-model.md
├── evaluation-plan.md
├── data-lineage.md
├── research-protocol.md
├── research/paper.md
└── assets/system-map.svg

scripts/
├── run_experiment.py
├── run_cohort.py
├── compare_policies.py
└── run_simulation.py
```

## What this project does **not** claim

The simulator does **not** establish that:

- real DNA can identify a child's ideal profession;
- a neural implant can decode a child's future skills;
- early specialization is universally beneficial;
- accelerated education automatically creates psychological maturity;
- AI can safely determine a child's identity or life path;
- any simulated counterfactual is evidence of what would happen to a real population.

Those are research questions, not conclusions.

## Research positioning

The project sits at the intersection of learning analytics, adaptive learning, knowledge tracing, psychometrics, educational policy simulation and responsible AI. Existing literature already contains work on student Digital Twins and adaptive learning; the novelty claim here is therefore the **integrated systems laboratory** and explicit study of counterfactuals, uncertainty, genomic-prior ablations and governance.

## Reproducibility

Every simulation is seed-based. Experiment outputs record the seed, scenario and simulator version. CI runs unit tests and a small research smoke suite.

See `docs/reproducibility.md` and `docs/references.md`.

## License

MIT. See `LICENSE`.

## Citation

See `CITATION.cff`.
