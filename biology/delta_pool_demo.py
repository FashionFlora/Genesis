"""Toy test of a local neighbour signal that maintains a progenitor pool.

This is a mechanism check, not a fit to chick development.  Empty sites make
growth measurable; the only difference between modes is how the neighbour
signal is supplied.
"""

import random


N = 128
STEPS = 200
INITIAL_CELLS = 40
MATURE_AFTER = 6


def run(mode: str, seed: int) -> tuple[int, int, float]:
    rng = random.Random(seed)
    stage = [-1] * N  # -1 empty, 0 progenitor, 1 transition, 2 mature
    age = [0] * N
    for position in range(32):
        stage[position] = 0
    for position in range(32, INITIAL_CELLS):
        stage[position] = 1
    shuffled = list(range(N))
    rng.shuffle(shuffled)

    for _ in range(STEPS):
        next_stage = stage[:]
        next_age = age[:]
        births = []
        for position, value in enumerate(stage):
            if value < 0:
                continue
            if mode == "none":
                signal = 0.0
            elif mode == "shuffled":
                signal = (
                    int(stage[shuffled[position - 1 if position else N - 1]] == 0)
                    + int(stage[shuffled[(position + 1) % N]] == 0)
                ) / 2.0
            else:
                left = stage[position - 1 if position else N - 1]
                right = stage[(position + 1) % N]
                signal = (left == 0) + (right == 0)
                signal /= 2.0

            if value == 0 and signal >= 0.5:
                if rng.random() < 0.18:
                    for target in (position - 1 if position else N - 1,
                                   (position + 1) % N):
                        if stage[target] < 0:
                            births.append(target)
                            break
            elif value == 0 and rng.random() < 0.20:
                next_stage[position] = 1
                next_age[position] = 0
            elif value == 1:
                next_age[position] += 1
                if next_age[position] >= MATURE_AFTER:
                    next_stage[position] = 2
            next_age[position] = max(next_age[position], age[position])

        for target in births:
            if next_stage[target] < 0:
                next_stage[target] = 0
                next_age[target] = 0
        stage, age = next_stage, next_age

    occupied = sum(value >= 0 for value in stage)
    mature = sum(value == 2 for value in stage)
    progenitor_fraction = sum(value == 0 for value in stage) / max(1, occupied)
    return occupied, mature, progenitor_fraction


if __name__ == "__main__":
    for mode in ("local", "none", "shuffled"):
        results = [run(mode, seed) for seed in range(20)]
        means = [sum(row[index] for row in results) / len(results) for index in range(3)]
        print(
            f"{mode}: occupied={means[0]:.2f}; mature={means[1]:.2f}; "
            f"progenitor_fraction={means[2]:.3f}"
        )
