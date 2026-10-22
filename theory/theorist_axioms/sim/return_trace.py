import json
from pathlib import Path

import numpy as np


def first_sustained(values, target, start, stop, width=20):
    for t in range(start, stop - width + 1):
        if np.all(values[t:t + width] == target):
            return t - start
    return stop - start


def run(seed, phases=500, channels=4, noise=0.08):
    rng = np.random.default_rng(seed)
    x = rng.integers(0, 2, phases * 3)
    y = rng.integers(0, 2, (phases * 3, channels))
    # A, B, A: one channel carries a noisy copy of the source in each phase.
    for t in range(phases * 3):
        target = 0 if t < phases or t >= 2 * phases else 1
        flip = rng.random() < noise
        y[t, target] = x[t] ^ flip

    evidence = np.zeros(channels, dtype=np.int64)
    choice = np.empty(phases * 3, dtype=np.int64)
    for t in range(phases * 3):
        evidence += (2 * x[t] - 1) * (2 * y[t] - 1)
        choice[t] = np.argmax(evidence)

    # Fresh learner control has no evidence from the first A when A returns.
    reset_evidence = np.zeros(channels, dtype=np.int64)
    reset_choice = np.empty(phases * 3, dtype=np.int64)
    for t in range(phases * 3):
        if t in (phases, 2 * phases):
            reset_evidence[:] = 0
        reset_evidence += (2 * x[t] - 1) * (2 * y[t] - 1)
        reset_choice[t] = np.argmax(reset_evidence)

    return {
        "first": first_sustained(choice, 0, 0, phases),
        "return": first_sustained(choice, 0, 2 * phases, 3 * phases),
        "reset_first": first_sustained(reset_choice, 0, 0, phases),
        "reset_return": first_sustained(reset_choice, 0, 2 * phases, 3 * phases),
        "null": float(np.mean(choice[2 * phases:] == 0)),
        "scores": evidence.tolist(),
    }


def main():
    rows = [run(seed) for seed in range(40)]
    paired = [r["return"] - r["first"] for r in rows]
    reset_paired = [r["reset_return"] - r["reset_first"] for r in rows]
    result = {
        "seeds": 40,
        "phases": 500,
        "channels": 4,
        "persistent_first_mean": float(np.mean([r["first"] for r in rows])),
        "persistent_return_mean": float(np.mean([r["return"] for r in rows])),
        "persistent_return_minus_first_mean": float(np.mean(paired)),
        "persistent_return_faster_fraction": float(np.mean(np.array(paired) < 0)),
        "reset_first_mean": float(np.mean([r["reset_first"] for r in rows])),
        "reset_return_mean": float(np.mean([r["reset_return"] for r in rows])),
        "reset_return_minus_first_mean": float(np.mean(reset_paired)),
        "return_choice_occupancy": float(np.mean([r["null"] for r in rows])),
        "per_seed": rows,
    }
    path = Path(__file__).with_name("return_trace_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "per_seed"}, indent=2))


if __name__ == "__main__":
    main()
