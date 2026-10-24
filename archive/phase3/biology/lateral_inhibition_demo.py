"""Toy check of neighbor-mediated fate suppression; not organism-judge evidence."""

import math
import random


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def run(seed, inhibition=True, cells=64, rounds=80):
    rng = random.Random(seed)
    bias = [rng.uniform(-0.25, 0.25) for _ in range(cells)]
    fate = [0.5] * cells
    for _ in range(rounds):
        for i in range(cells):
            neighbor_signal = (fate[(i - 1) % cells] + fate[(i + 1) % cells]) / 2
            drive = 4 * bias[i] - (5 * neighbor_signal if inhibition else 0)
            fate[i] = 0.5 * fate[i] + 0.5 * sigmoid(drive)
    density = sum(fate) / cells
    neighbor_pairs = sum(fate[i] * fate[(i + 1) % cells] for i in range(cells)) / cells
    return density, neighbor_pairs


if __name__ == "__main__":
    for enabled in (True, False):
        values = [run(seed, enabled) for seed in range(100)]
        label = "inhibition" if enabled else "ablation"
        density = sum(x[0] for x in values) / len(values)
        pairs = sum(x[1] for x in values) / len(values)
        print(f"{label}: fate_density={density:.4f} neighbor_pair_activity={pairs:.4f}")
