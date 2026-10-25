"""Toy ablation: persistent mismatch reopens only the affected plasticity gate.

This is a scalar two-trace logic check inspired by selective PNN/Otx2 gating,
not a neural or organism model.  A later probe perturbs the stable trace to
test whether a global reset exposes unrelated memory to plasticity.
"""

import random


def run(mode, seed, persistence_steps=3):
    rng = random.Random(seed)
    estimates = [0.0, 0.0]
    brakes = [0.0, 0.0]
    mismatch = [0, 0]
    rate = 0.08

    def step(targets):
        nonlocal estimates, brakes, mismatch
        errors = [targets[i] - estimates[i] for i in range(2)]
        high = [abs(error) > 0.45 for error in errors]
        if mode == "none":
            gates = [1.0, 1.0]
        else:
            gates = [1.0 / (1.0 + 100.0 * brakes[i]) for i in range(2)]

        for i in range(2):
            if mode == "global_persistent":
                mismatch[i] = mismatch[i] + 1 if high[i] else 0
            elif mode == "local_persistent":
                mismatch[i] = mismatch[i] + 1 if high[i] else 0
            elif mode == "global_instant" and any(high):
                mismatch = [0, 0]
                brakes = [0.0, 0.0]
                gates = [1.0, 1.0]
                break

        if mode == "global_persistent" and any(x >= persistence_steps for x in mismatch):
            brakes = [0.0, 0.0]
            gates = [1.0, 1.0]
        elif mode == "local_persistent":
            for i in range(2):
                if mismatch[i] >= persistence_steps:
                    brakes[i] = 0.0
                    gates[i] = 1.0

        for i in range(2):
            estimates[i] += rate * gates[i] * errors[i]
            if mode != "none" and abs(errors[i]) < 0.05:
                brakes[i] = min(1.0, brakes[i] + 0.010)

    for _ in range(300):
        step([0.8 + rng.uniform(-0.02, 0.02)] * 2)
    old_stable = estimates[1]

    for _ in range(300):
        step([0.2 + rng.uniform(-0.02, 0.02), 0.8 + rng.uniform(-0.02, 0.02)])
    changed_error = abs(estimates[0] - 0.2)

    # A single unexpected sample on the unchanged trace is the selectivity probe.
    step([0.8, -0.8])
    stable_probe_drift = abs(estimates[1] - old_stable)
    return changed_error, stable_probe_drift


if __name__ == "__main__":
    modes = ("none", "fixed", "global_instant", "global_persistent", "local_persistent")
    for mode in modes:
        rows = [run(mode, seed) for seed in range(1000)]
        means = [sum(row[i] for row in rows) / len(rows) for i in range(2)]
        print(
            f"{mode}: changed_error={means[0]:.4f}; "
            f"stable_probe_drift={means[1]:.4f}"
        )
