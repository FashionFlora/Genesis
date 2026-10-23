"""Toy test of whether action prediction should gate sensory input by timing."""
import json
from pathlib import Path

import numpy as np


def run(seed=410, worlds=300, trials=120, noise_sd=0.15, pulse=0.5,
        threshold=0.35, expected=(-0.5, 0.5)):
    rng = np.random.default_rng(seed)
    stats = {str(offset): {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
             for offset in (-150, -50, 0, 50, 150)}
    raw = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for _ in range(worlds):
        actions = rng.integers(0, 2, size=trials)
        pulse_at = rng.integers(trials // 2, trials)
        estimate = np.zeros(2)
        count = np.zeros(2)
        for t, action in enumerate(actions):
            is_pulse = t == pulse_at
            sensory = expected[action] + pulse * is_pulse + rng.normal(0, noise_sd)
            if t < trials // 2:
                count[action] += 1
                estimate[action] += (sensory - estimate[action]) / count[action]
                continue
            for detected in (abs(sensory) > threshold,):
                raw["tp"] += int(detected and is_pulse)
                raw["fp"] += int(detected and not is_pulse)
                raw["fn"] += int(not detected and is_pulse)
                raw["tn"] += int(not detected and not is_pulse)
            for offset in (-150, -50, 0, 50, 150):
                # The copy can explain reafference only after its action was issued.
                prediction = estimate[action] if offset < 0 else 0.0
                detected = abs(sensory - prediction) > threshold
                s = stats[str(offset)]
                s["tp"] += int(detected and is_pulse)
                s["fp"] += int(detected and not is_pulse)
                s["fn"] += int(not detected and is_pulse)
                s["tn"] += int(not detected and not is_pulse)
    result = {"config": {"seed": seed, "worlds": worlds, "trials": trials,
                          "noise_sd": noise_sd, "pulse": pulse,
                          "threshold": threshold, "offsets": "negative means action leads sensory input"},
              "raw": raw, "timing_gated": stats}
    for s in [raw, *stats.values()]:
        s["recall"] = s["tp"] / max(s["tp"] + s["fn"], 1)
        s["false_positive_rate"] = s["fp"] / max(s["fp"] + s["tn"], 1)
    path = Path(__file__).with_name("efference_timing_probe_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
