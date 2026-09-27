from __future__ import annotations

from .psychometrics import brier_score, expected_calibration_error, reliability_bins


def evaluate(predictions, outcomes):
    return {"brier": round(brier_score(predictions, outcomes), 6),
            "ece": round(expected_calibration_error(predictions, outcomes), 6),
            "reliability": reliability_bins(predictions, outcomes)}
