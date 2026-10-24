"""Toy ablation of a reversible, experience-built brake on plasticity.

This scalar tracking model is not a neural circuit or organism result. A
feature shifts between two stationary environments; report old-trace retention
and adaptation to the new feature separately.
"""

import random


def run(mode, seed):
    rng = random.Random(seed)
    estimate = 0.0
    brake = 0.0
    rate = 0.08

    def step(target):
        nonlocal estimate, brake
        error = target - estimate
        if mode == "none":
            gate = 1.0
        else:
            gate = 1.0 / (1.0 + 100.0 * brake)
        if mode == "reversible" and abs(error) > 0.45:
            brake = 0.0
            gate = 1.0
        estimate += rate * gate * error
        if mode != "none":
            if abs(error) < 0.05:
                brake = min(1.0, brake + 0.010)

    for _ in range(300):
        step(0.8 + rng.uniform(-0.02, 0.02))
    old_trace = estimate
    for _ in range(300):
        step(0.2 + rng.uniform(-0.02, 0.02))
    return old_trace, estimate


if __name__ == "__main__":
    for mode in ("none", "permanent", "reversible"):
        rows = [run(mode, seed) for seed in range(100)]
        old_trace = sum(row[0] for row in rows) / len(rows)
        final = sum(row[1] for row in rows) / len(rows)
        adaptation = 1.0 - sum(abs(row[1] - 0.2) for row in rows) / len(rows)
        print(f"{mode}: old_trace={old_trace:.3f}; final={final:.3f}; adaptation={adaptation:.3f}")
