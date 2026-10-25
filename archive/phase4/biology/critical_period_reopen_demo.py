"""Toy ablation: persistent mismatch reopens an experience-built plasticity gate.

This scalar tracking model is a logic check, not a neural or organism model.
"""

import random


def run(mode, seed, persistence_steps=3):
    rng = random.Random(seed)
    estimate = 0.0
    brake = 0.0
    mismatch = 0
    rate = 0.08

    def step(target):
        nonlocal estimate, brake, mismatch
        error = target - estimate
        if mode == "none":
            gate = 1.0
        else:
            gate = 1.0 / (1.0 + 100.0 * brake)

        high_error = abs(error) > 0.45
        if mode == "instant_release" and high_error:
            brake = 0.0
            gate = 1.0
        elif mode == "persistent_mismatch":
            mismatch = mismatch + 1 if high_error else 0
            if mismatch >= persistence_steps:
                brake = 0.0
                gate = 1.0

        estimate += rate * gate * error
        if mode != "none" and abs(error) < 0.05:
            brake = min(1.0, brake + 0.010)

    for _ in range(300):
        step(0.8 + rng.uniform(-0.02, 0.02))
    old_trace = estimate

    # One transient perturbation tests whether a single mismatch unlocks learning.
    step(-0.8)
    transient_drift = abs(estimate - old_trace)

    for _ in range(300):
        step(0.2 + rng.uniform(-0.02, 0.02))
    final_error = abs(estimate - 0.2)
    return old_trace, transient_drift, final_error


if __name__ == "__main__":
    modes = ((mode, 3) for mode in ("none", "fixed", "instant_release"))
    modes = list(modes) + [("persistent_mismatch", steps) for steps in (1, 2, 3, 5)]
    for mode, persistence_steps in modes:
        rows = [run(mode, seed, persistence_steps) for seed in range(100)]
        means = [sum(row[i] for row in rows) / len(rows) for i in range(3)]
        print(
            f"{mode}(steps={persistence_steps}): old_trace={means[0]:.3f}; "
            f"transient_drift={means[1]:.3f}; final_error={means[2]:.3f}"
        )
