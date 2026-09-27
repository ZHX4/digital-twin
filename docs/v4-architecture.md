# Digital Twin v4 — World Laboratory

## What changed

v3 modeled a longitudinal learner. v4 adds an executable world around the learner.

```text
Learner
  │
  ├── latent cognitive state
  ├── knowledge graph
  ├── interests / agency / wellbeing
  └── uncertainty
        │
        ▼
Contextual-bandit curriculum
        │
        ▼
Teacher ─ School ─ Family ─ Peers
        │
        ▼
Population trajectory
        │
        ├── resource-equity diagnostics
        ├── synthetic labor market
        ├── policy counterfactuals
        └── Pareto frontier
```

## v4 layers

### 1. Latent learner model

app/learner_model.py separates latent learner state from observed evidence. Skill states include mastery, uncertainty, retention and misconceptions.

### 2. Skill graph and transfer

Prerequisite edges form a directed knowledge graph. Transfer edges model limited cross-skill spillovers instead of assuming independent domains.

### 3. Curriculum as a contextual bandit

app/curriculum_agent.py implements a small linear-UCB planner. Each action is chosen from an eight-dimensional learner/environment context and updated from a multi-objective reward.

### 4. Multi-agent education world

app/world.py models learners, families, schools and teachers as interacting agents. School resources and family support become environmental causes of trajectory differences rather than hidden constants.

### 5. Population simulation

app/population.py provides quantiles and bootstrap intervals for population outcomes.

### 6. Policy search

app/policy_search.py samples policy configurations and returns a Pareto frontier across learning, wellbeing, agency, equity, mismatch and inequality.

### 7. Benchmark suite

app/benchmark.py provides reproducible synthetic learner interactions plus a documented CSV adapter boundary for licensed educational datasets.

## Scientific boundary

The world is still synthetic. A larger simulator does not become evidence merely because it contains more agents or more equations. External datasets and validated models are required before empirical claims can be made.
