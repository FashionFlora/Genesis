"""Deterministic toy check for relative-timing competition and pruning.

This is a mechanism demonstrator, not an organism controller or a biological
parameter fit.  A postsynaptic burst train is the only teaching-like signal.
"""

import random


def run(competitive: bool, seed: int = 17):
    rng = random.Random(seed)
    steps = 240
    post = [int((t % 12) in (2, 3)) for t in range(steps)]
    inputs = []
    for index in range(8):
        if index == 0:  # reliably synchronous input
            signal = post[:]
        elif index == 1:  # anti-phase input
            signal = [1 - value for value in post]
        else:  # weak, unstructured input
            signal = [int(rng.random() < 0.12) for _ in range(steps)]
        inputs.append(signal)

    weights = [1.0] * len(inputs)
    for window_start in range(0, steps, 24):
        window_end = window_start + 24
        scores = [
            sum(x * y for x, y in zip(signal[window_start:window_end], post[window_start:window_end]))
            / sum(post[window_start:window_end])
            for signal in inputs
        ]
        baseline = sum(scores) / len(scores) if competitive else 0.0
        weights = [max(0.0, w + 0.35 * (score - baseline)) for w, score in zip(weights, scores)]
        if window_start == 120:
            weights = [w if w >= 0.70 else 0.0 for w in weights]

    active = sum(weight > 0 for weight in weights)
    return active, round(sum(weights), 3), [round(weight, 3) for weight in weights]


for mode in (True, False):
    active, total, weights = run(mode)
    label = "competition" if mode else "no_competition"
    print(f"{label}: active={active}; total={total:.3f}; weights={weights}")
