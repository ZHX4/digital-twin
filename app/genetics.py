from __future__ import annotations

import random

import numpy as np

from .models import DOMAINS, Genome

MARKERS = [f"DTG-{i:04d}" for i in range(1, 145)]
BASES = "ACGT"
FACTOR_NAMES = ["quantitative", "spatial", "verbal", "novelty", "persistence", "social"]


def _clip(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def generate_genome(rng: random.Random, prior_strength: float = 0.05) -> Genome:
    markers = {m: rng.choice(BASES) for m in MARKERS}
    vector = np.array([BASES.index(markers[m]) / 3.0 for m in MARKERS], dtype=float)
    factors: dict[str, float] = {}
    for i, factor in enumerate(FACTOR_NAMES):
        idx = np.arange(i % 6, len(vector), 6)
        factors[factor] = round(_clip(0.25 + 0.55 * float(np.mean(vector[idx])) + rng.gauss(0, 0.035)), 4)

    mappings = {
        "mathematics": ["quantitative"], "programming": ["quantitative", "novelty"],
        "physics": ["quantitative", "spatial"], "biology": ["verbal", "quantitative"],
        "language": ["verbal"], "spatial_reasoning": ["spatial"], "design": ["spatial", "novelty"],
        "social_reasoning": ["social", "verbal"], "systems_thinking": ["quantitative", "novelty"],
        "scientific_reasoning": ["quantitative", "novelty"], "creativity": ["novelty", "verbal"],
        "self_regulation": ["persistence"],
    }
    latents = {}
    uncertainty = {}
    for domain in DOMAINS:
        source = [factors[k] for k in mappings[domain]]
        latent = _clip(sum(source) / len(source) + rng.gauss(0, 0.055))
        latents[domain] = round(latent, 4)
        uncertainty[domain] = round(_clip(0.34 + 0.12 * abs(latent - 0.5)), 4)

    return Genome(
        model="synthetic-genome-prior-v3",
        sequence_preview="".join(markers[m] for m in MARKERS[:64]),
        markers=markers,
        synthetic_latents=latents,
        factor_latents=factors,
        uncertainty=uncertainty,
        prior_strength=round(max(0.0, min(0.15, prior_strength)), 4),
        disclaimer=(
            "Synthetic markers only. No real genes, GWAS, polygenic scores, medical risks, IQ, personality, "
            "brain state, or career suitability are inferred. Genomic effects are intentionally weak priors "
            "whose contribution can be ablated in experiments."
        ),
    )
