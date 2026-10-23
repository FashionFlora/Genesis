#!/usr/bin/env python3
"""Test how efference-copy gain errors affect residual-based event detection."""
import json
import random
from pathlib import Path

WORLDS = 200
TRIALS = 120
CALIBRATION_TRIALS = 60
NOISE_SD = 0.15
THRESHOLD = 0.35
GAINS = (0.0, 0.5, 0.8, 1.0, 1.2, 1.5)


def run(seed, gain):
    rng = random.Random(seed)
    contexts = [-0.5, 0.5]
    samples = []
    for t in range(TRIALS):
        action = rng.randrange(2)
        external = t >= CALIBRATION_TRIALS and rng.random() < 0.1
        observed = contexts[action] + rng.gauss(0, NOISE_SD) + (0.5 if external else 0.0)
        if t < CALIBRATION_TRIALS:
            samples.append((contexts[action], observed))
        else:
            samples.append((contexts[action], observed, external))
    # A single calibrated gain stands in for a learned action-conditioned forward model.
    context_energy = sum(x * x for x, _ in samples[:CALIBRATION_TRIALS])
    calibrated = sum(x * y for x, y in samples[:CALIBRATION_TRIALS]) / context_energy
    model_gain = calibrated * gain
    raw = [[], []]
    residual = [[], []]
    for expected, observed, external in samples[CALIBRATION_TRIALS:]:
        raw[external].append(abs(observed) > THRESHOLD)
        residual[external].append(abs(observed - model_gain * expected) > THRESHOLD)
    def metrics(pred):
        tp, fp = sum(pred[1]), sum(pred[0])
        return tp / len(pred[1]), tp / max(1, tp + fp), fp / len(pred[0])
    return metrics(raw), metrics(residual)


def main():
    rows = []
    for gain in GAINS:
        results = [run(seed, gain) for seed in range(WORLDS)]
        row = {"model_gain_fraction": gain}
        for mode, index in (("raw", 0), ("residual", 1)):
            row[mode] = {
                key: sum(result[index][i] for result in results) / WORLDS
                for i, key in enumerate(("recall", "precision", "false_positive_rate"))
            }
        rows.append(row)
    out = {"worlds": WORLDS, "trials_per_world": TRIALS,
           "calibration_trials": CALIBRATION_TRIALS, "noise_sd": NOISE_SD,
           "external_event_probability": 0.1, "external_event_amplitude": 0.5,
           "threshold": THRESHOLD, "conditions": rows,
           "note": "synthetic model-gain sweep; action contexts and event amplitude supplied"}
    path = Path(__file__).with_name("efference_calibration_probe_result.json")
    path.write_text(json.dumps(out, indent=2) + "\n")
    for row in rows:
        print(f"gain={row['model_gain_fraction']:.1f} raw P/R/FPR="
              f"{row['raw']['precision']:.3f}/{row['raw']['recall']:.3f}/"
              f"{row['raw']['false_positive_rate']:.3f} residual="
              f"{row['residual']['precision']:.3f}/{row['residual']['recall']:.3f}/"
              f"{row['residual']['false_positive_rate']:.3f}")
    print(f"result={path}")


if __name__ == "__main__":
    main()
