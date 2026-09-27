# Architecture

Digital Twin is a simulation laboratory, not a production decision system.

```mermaid
flowchart LR
B[Synthetic prior] --> T[Longitudinal Twin]
T --> A[IRT/CAT]
T --> X[Active exploration]
T --> E[Environment]
A --> P[Posterior state]
X --> P
E --> P
P --> C[Adaptive curriculum]
C --> O[Learning + projects]
O --> T
P --> R[Pathway posterior]
R --> G[Competency gate]
G --> L[Life-course stress test]
P --> Q[Governance]
Q --> CF[Counterfactual lab]
CF --> Q
```

## Decision order

1. update environment
2. update capability state
3. conduct adaptive assessments
4. update uncertainty
5. choose information-rich exploration
6. update from exploration evidence
7. calculate pathway posterior
8. select curriculum
9. apply learning and forgetting
10. evaluate wellbeing
11. write audit record
12. check competency gate

The recommendation engine returns a posterior distribution and safety flags rather than deleting alternatives.
