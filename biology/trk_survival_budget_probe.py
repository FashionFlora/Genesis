"""Compare trophic competition variants under an identical death budget."""
import numpy as np


N = 256
TARGET = 64
SEEDS = 100
ROUNDS = (N - TARGET) // 4
NEIGHBORS = 4


def run(seed, context, mode):
    rng = np.random.default_rng(seed * 2 + context)
    is_a = np.zeros(N, dtype=bool)
    is_a[: N // 2] = True
    rng.shuffle(is_a)
    utility_a = np.where(is_a, 0.60, 0.50) + rng.normal(0.0, 0.13, N)
    utility_b = np.where(is_a, 0.50, 0.60) + rng.normal(0.0, 0.13, N)
    utility = utility_a if context == 0 else utility_b
    alive = np.ones(N, dtype=bool)
    receptor = np.ones(N)
    for _ in range(ROUNDS):
        weights = np.where(alive, np.maximum(utility, 0.01) * receptor, 0.0)
        uptake = TARGET * weights / weights.sum()
        if mode not in ("no_sensitization", "all_off"):
            receptor[alive] = 0.85 * receptor[alive] + 0.15 * (1 + uptake[alive])
        exposure = sum(np.roll(uptake, shift) for shift in (-2, -1, 1, 2)) / NEIGHBORS
        vulnerability = np.ones(N)
        if mode not in ("no_protection", "all_off"):
            vulnerability = np.exp(-0.7 * uptake)
        hazard = 0.12 * np.maximum(0.0, 1.0 - uptake) ** 2
        if mode not in ("no_paracrine", "all_off"):
            hazard += 0.035 * exposure * vulnerability
        hazard[~alive] = 0.0
        p = hazard / hazard.sum() if hazard.sum() else alive / alive.sum()
        dead = rng.choice(N, size=4, replace=False, p=p)
        alive[dead] = False
    survivors = np.flatnonzero(alive)
    correct = is_a if context == 0 else ~is_a
    return float(utility[survivors].mean()), float(correct[survivors].mean())


def main():
    modes = ("full", "no_sensitization", "no_paracrine", "no_protection", "all_off")
    print("N=256; target=64; seeds=100; fixed 4 deaths/round; 48 rounds; paired seeds")
    print("mode quality_a quality_b precision_a precision_b")
    for mode in modes:
        values = np.array([[run(seed, context, mode) for context in (0, 1)]
                           for seed in range(SEEDS)])
        means = values.mean(axis=0)
        print("%s %.6f %.6f %.6f %.6f" % (
            mode, means[0, 0], means[1, 0], means[0, 1], means[1, 1]))


if __name__ == "__main__":
    main()
