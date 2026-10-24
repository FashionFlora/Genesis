"""Toy test of intrinsic fitness selection under a shared survival limit.

This is a mechanism check, not a fitted model of proprioceptor development.
"""

import random


N_CELLS = 200
CAPACITY = 100


def run(mode: str, seed: int) -> tuple[int, float]:
    rng = random.Random(seed)
    if mode == "equal_fitness":
        fitness = [1.0] * N_CELLS
    else:
        fitness = [rng.uniform(0.5, 1.5) for _ in range(N_CELLS)]

    if mode == "no_competition":
        survivors = list(range(N_CELLS))
    else:
        remaining = list(range(N_CELLS))
        survivors = []
        for _ in range(CAPACITY):
            weights = [fitness[index] if mode == "selection" else 1.0 for index in remaining]
            chosen = rng.choices(remaining, weights=weights, k=1)[0]
            survivors.append(chosen)
            remaining.remove(chosen)

    mean_fitness = sum(fitness[index] for index in survivors) / len(survivors)
    return len(survivors), mean_fitness


if __name__ == "__main__":
    for mode in ("selection", "equal_fitness", "no_competition", "random_loss"):
        results = [run(mode, seed) for seed in range(100)]
        mean_count = sum(row[0] for row in results) / len(results)
        mean_fitness = sum(row[1] for row in results) / len(results)
        print(f"{mode}: survivors={mean_count:.1f}; mean_fitness={mean_fitness:.3f}")
