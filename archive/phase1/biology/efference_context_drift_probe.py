#!/usr/bin/env python3
"""Test action-tagged residuals when motor gain drifts and effects overlap."""
import json
import math
import random
from pathlib import Path

WORLDS = 200
STEPS = 240
CALIBRATION = 60
DRIFT = 120
NOISE = 0.12
PULSE = 0.50
PULSE_RATE = 0.10
LR = 0.10
UNCERTAINTY_LR = 0.08
THRESHOLD = 0.34


def effect(action, gain):
    # Both actions affect both channels; the action identity is still informative.
    base = ((1.0, 0.60), (0.60, 1.0))[action]
    return tuple(gain * x for x in base)


def run(seed, drift_gain, mode):
    rng = random.Random(seed)
    estimates = [[0.0, 0.0], [0.0, 0.0]]
    uncertainty = [0.0, 0.0]
    counts = {"tp": 0, "fp": 0, "positives": 0, "negatives": 0}
    residual_sum = []
    for t in range(STEPS):
        action = rng.randrange(2)
        gain = 1.0 if t < DRIFT else drift_gain
        expected = effect(action, gain)
        pulse = t >= CALIBRATION and rng.random() < PULSE_RATE
        observed = [x + rng.gauss(0.0, NOISE) for x in expected]
        if pulse:
            observed[0] += PULSE

        if mode == "raw":
            score = math.sqrt(sum(x * x for x in observed))
        else:
            residual = [observed[i] - estimates[action][i] for i in range(2)]
            score = math.sqrt(sum(x * x for x in residual))
        confident = mode != "confidence" or uncertainty[action] < 0.22
        novelty = score > THRESHOLD and confident
        if t >= CALIBRATION:
            counts["positives" if pulse else "negatives"] += 1
            counts["tp" if pulse and novelty else "fp" if (not pulse and novelty) else "tn" if not pulse else "fn"] = counts.get("tp" if pulse and novelty else "fp" if (not pulse and novelty) else "tn" if not pulse else "fn", 0) + 1
        if mode != "raw":
            residual = [observed[i] - estimates[action][i] for i in range(2)]
            norm = math.sqrt(sum(x * x for x in residual))
            uncertainty[action] += UNCERTAINTY_LR * (norm - uncertainty[action])
            # Prediction adapts continuously; confidence only gates structural novelty.
            for i in range(2):
                estimates[action][i] += LR * (observed[i] - estimates[action][i])
            if t >= DRIFT:
                residual_sum.append(norm)
    fp = counts.get("fp", 0)
    tn = counts.get("tn", 0)
    tp = counts.get("tp", 0)
    fn = counts.get("fn", 0)
    return {
        "precision": tp / max(1, tp + fp),
        "recall": tp / max(1, tp + fn),
        "fpr": fp / max(1, fp + tn),
        "post_drift_mean_residual": sum(residual_sum) / max(1, len(residual_sum)),
    }


def main():
    rows = []
    for gain in (0.6, 1.4):
        for mode in ("raw", "residual", "confidence"):
            runs = [run(seed, gain, mode) for seed in range(WORLDS)]
            rows.append({"drift_gain": gain, "mode": mode, "worlds": WORLDS, **{
                key: sum(r[key] for r in runs) / WORLDS
                for key in ("precision", "recall", "fpr", "post_drift_mean_residual")
            }})
    result = {
        "steps": STEPS, "calibration_steps": CALIBRATION, "drift_step": DRIFT,
        "noise_sd": NOISE, "pulse": PULSE, "pulse_rate": PULSE_RATE,
        "threshold": THRESHOLD, "learning_rate": LR,
        "rows": rows,
        "limitation": "Synthetic two-channel motor effects with supplied gain drift and external pulses; no neural circuit or synaptic growth.",
    }
    path = Path(__file__).with_name("efference_context_drift_probe_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
