"""Toy check: action-conditioned prediction can gate expected sensory input."""
import json
from pathlib import Path

import numpy as np


def run(seed=27, worlds=200, trials=120, noise_sd=0.15, pulse=0.5, threshold=0.35):
    rng = np.random.default_rng(seed)
    expected_by_action = np.array([-0.5, 0.5])
    stats = {"raw": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
             "gated": {"tp": 0, "fp": 0, "fn": 0, "tn": 0}}
    for _ in range(worlds):
        order = rng.integers(0, 2, size=trials)
        pulse_at = rng.integers(0, trials)
        estimate = np.zeros(2)
        count = np.zeros(2)
        for t, action in enumerate(order):
            external = pulse if t == pulse_at else 0.0
            sensory = expected_by_action[action] + external + rng.normal(0, noise_sd)
            # Treat the first half as calibration, then evaluate on held-out trials.
            if t < trials // 2:
                count[action] += 1
                estimate[action] += (sensory - estimate[action]) / count[action]
                continue
            is_pulse = t == pulse_at
            raw_detected = abs(sensory) > threshold
            predicted = estimate[action]
            gated_detected = abs(sensory - predicted) > threshold
            for name, detected in (("raw", raw_detected), ("gated", gated_detected)):
                stats[name]["tp"] += int(detected and is_pulse)
                stats[name]["fp"] += int(detected and not is_pulse)
                stats[name]["fn"] += int(not detected and is_pulse)
                stats[name]["tn"] += int(not detected and not is_pulse)
    result = {"config": {"seed": seed, "worlds": worlds, "trials": trials,
                         "noise_sd": noise_sd, "pulse": pulse, "threshold": threshold},
              "counts": stats}
    for name, s in stats.items():
        s["precision"] = s["tp"] / max(s["tp"] + s["fp"], 1)
        s["recall"] = s["tp"] / max(s["tp"] + s["fn"], 1)
        s["false_positive_rate"] = s["fp"] / max(s["fp"] + s["tn"], 1)
    path = Path(__file__).with_name("efference_gate_probe_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
