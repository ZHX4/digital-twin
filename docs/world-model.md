# World Model

The world model is an agent-based layer around the longitudinal Digital Twin.

## Agents

- LearnerAgent
- TeacherAgent
- FamilyAgent
- SchoolAgent

## Environment variables

- resource access;
- family support;
- family stability;
- school resources;
- teacher quality;
- peer effect;
- exploration capacity;
- policy settings.

## Fixed-seed counterfactual design

Learner initialization uses stable hashes of (seed, learner_id) and yearly randomness uses (seed, year, learner_id, policy).

This makes the same nominal population reproducible across policy configurations while allowing policy-dependent trajectories to diverge.

## Long-horizon direction

The next stage can add university, employer, research and reskilling agents without changing the learner-state contract.
