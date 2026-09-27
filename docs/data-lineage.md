# Data Lineage

All learner, genomic and environmental observations in the current release are generated synthetically from a seeded simulator.

| Source | Current use | Role |
|---|---|---|
| synthetic RNG | yes | learner/environment generation |
| synthetic genome markers | yes | bounded prior |
| synthetic psychometric responses | yes | IRT/CAT diagnostics |
| synthetic skill states | yes | mastery/forgetting |
| synthetic market | yes | stress test |
| real child data | no | intentionally excluded |
| real genomic data | no | intentionally excluded |

Future calibration datasets must be versioned with license, provenance, preprocessing and checksum metadata.
