"""Toy ablation: inhibitory balance gates unsupervised synaptic change.

This is a mechanism check, not a fit to cortical data and not an organism
controller.  A low-drive, unstructured interval is used as a deprivation
perturbation; the useful output is retention of cue responses after it.
"""

import math
import random


def _activity(weights, inputs, inhibition):
    excitation = [sum(w * x for w, x in zip(row, inputs)) / 4.0 for row in weights]
    activity = [max(0.0, value) / (1.0 + inhibition) for value in excitation]
    return activity, excitation


def _gate(excitation, inhibition, enabled):
    if not enabled:
        return 1.0
    ratio = excitation / (0.5 + inhibition)
    return max(0.0, 1.0 - abs(ratio - 1.1) / 0.9)


def run(mode, seed):
    rng = random.Random(seed)
    patterns = []
    for _ in range(3):
        active = rng.sample(range(12), 4)
        patterns.append([1.0 if i in active else 0.0 for i in range(12)])
    weights = [[rng.uniform(0.5, 1.0) for _ in range(12)] for _ in range(3)]
    inhibition = 0.7
    target = 0.35

    def step(inputs, plastic=True):
        nonlocal inhibition
        activities, excitations = _activity(weights, inputs, inhibition)
        winner = max(range(3), key=lambda unit: activities[unit])
        activity, excitation = activities[winner], excitations[winner]
        if mode != "fixed_inhibition":
            inhibition = min(3.0, max(0.1, inhibition + 0.025 * (target - activity)))
        if plastic:
            gate = _gate(excitation, inhibition, mode == "adaptive_gate")
            for i, x in enumerate(inputs):
                # Hebbian change with weight normalization; no target or reward.
                spontaneous_drive = activity + 0.08
                weights[winner][i] = min(2.0, max(0.0, weights[winner][i] + 0.140 * gate * spontaneous_drive * (x - 0.18)))
            mean_weight = sum(weights[winner]) / len(weights[winner])
            weights[winner][:] = [w * (0.78 / mean_weight) for w in weights[winner]]
        return activity

    for t in range(240):
        step(patterns[t % len(patterns)])
    before = [max(range(3), key=lambda unit: _activity(weights, pattern, inhibition)[0][unit]) for pattern in patterns]
    weights_before = [row[:] for row in weights]

    # Low-drive, unstructured input models a deprivation interval.
    for _ in range(1200):
        noisy = [0.15 if rng.random() < 0.30 else 0.0 for _ in range(12)]
        step(noisy)
    after = [max(range(3), key=lambda unit: _activity(weights, pattern, inhibition)[0][unit]) for pattern in patterns]
    dot = sum(sum(a * b for a, b in zip(old, new)) for old, new in zip(weights_before, weights))
    norm_old = math.sqrt(sum(value * value for row in weights_before for value in row))
    norm_new = math.sqrt(sum(value * value for row in weights for value in row))
    retention = dot / (norm_old * norm_new)
    gap = len(set(after)) / len(patterns)
    return retention, gap, inhibition


if __name__ == "__main__":
    for mode in ("adaptive_gate", "no_gate", "fixed_inhibition"):
        values = [run(mode, seed) for seed in range(100)]
        means = [sum(row[i] for row in values) / len(values) for i in range(3)]
        print(
            f"{mode}: retention={means[0]:.3f}; cue_gap={means[1]:.3f}; "
            f"final_inhibition={means[2]:.3f}"
        )
