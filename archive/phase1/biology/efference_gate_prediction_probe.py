#!/usr/bin/env python3
"""Separate a broad sensory gate from feature-specific efference prediction."""
import json
import random
from pathlib import Path


WORLDS = 300
TRIALS = 160
CALIBRATION = 40
NOISE_SD = 0.12
EVENT_RATE = 0.10
EVENT_SIZE = 0.50
THRESHOLD = 0.35
GATE_GAIN = 0.25


def run(seed, event_channel, mode):
    rng = random.Random(seed)
    stats = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    expected = (0.60, 0.0)
    for t in range(TRIALS):
        event = t >= CALIBRATION and rng.random() < EVENT_RATE
        observed = [expected[i] + rng.gauss(0.0, NOISE_SD) for i in range(2)]
        if event:
            observed[event_channel] += EVENT_SIZE

        if mode == "raw":
            processed = observed
        elif mode == "broad_gate":
            processed = [GATE_GAIN * x for x in observed]
        else:
            # The action copy predicts only the expected feature, not all input.
            processed = [observed[0] - expected[0], observed[1] - expected[1]]
            if mode == "gate_plus_prediction":
                processed = [GATE_GAIN * x for x in processed]
        detected = max(abs(x) for x in processed) > THRESHOLD
        if t < CALIBRATION:
            continue
        label = "tp" if event and detected else "fn" if event else "fp" if detected else "tn"
        stats[label] += 1
    positives = stats["tp"] + stats["fn"]
    negatives = stats["fp"] + stats["tn"]
    return {
        "recall": stats["tp"] / max(1, positives),
        "false_positive_rate": stats["fp"] / max(1, negatives),
    }


def main():
    rows = []
    for event_channel, name in ((0, "predicted_feature"), (1, "orthogonal_feature")):
        for mode in ("raw", "broad_gate", "feature_prediction", "gate_plus_prediction"):
            runs = [run(seed, event_channel, mode) for seed in range(WORLDS)]
            rows.append({
                "event_relation": name,
                "mode": mode,
                **{key: sum(r[key] for r in runs) / WORLDS
                   for key in ("recall", "false_positive_rate")},
            })
    result = {
        "worlds": WORLDS,
        "trials_per_world": TRIALS,
        "calibration_trials": CALIBRATION,
        "noise_sd": NOISE_SD,
        "event_probability": EVENT_RATE,
        "event_size": EVENT_SIZE,
        "broad_gate_gain": GATE_GAIN,
        "threshold": THRESHOLD,
        "rows": rows,
        "limitation": "Synthetic two-feature signal; gate, prediction and event are stipulated, with no neural circuit or learned synapses.",
    }
    path = Path(__file__).with_name("efference_gate_prediction_probe_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    for row in rows:
        print(f"{row['event_relation']:18s} {row['mode']:22s} "
              f"recall={row['recall']:.3f} FPR={row['false_positive_rate']:.3f}")
    print(f"result={path}")


if __name__ == "__main__":
    main()
