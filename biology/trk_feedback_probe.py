"""Toy probe of target-initiated positive and paracrine survival feedback.

Cells compete for a fixed trophic pool. Target-derived signal changes receptor
sensitivity, high-uptake cells expose neighbors to a local death signal, and
their own uptake protects them from that signal. This abstracts Deppmann et al.
(Science, 2008); it is not a model of their molecular kinetics.
"""
import numpy as np


SEEDS = 100
N = 256
K = 64
ROUNDS = 12
NEIGHBORS = 4


def evaluate(utility, mode):
    receptor = np.ones(N)
    alive = np.ones(N, dtype=bool)
    uptake = np.zeros(N)

    for _ in range(ROUNDS):
        weights = np.where(alive, np.maximum(utility, 0.01) * receptor, 0.0)
        uptake = K * weights / max(weights.sum(), 1e-12)
        if mode not in ("no_sensitization", "all_off"):
            receptor = np.where(alive, 0.85 * receptor + 0.15 * (1.0 + uptake), receptor)

    # Ring adjacency supplies local paracrine exposure, not a global fitness cue.
    exposure = np.zeros(N)
    for offset in range(1, NEIGHBORS // 2 + 1):
        exposure += np.roll(uptake, offset) + np.roll(uptake, -offset)
    exposure /= NEIGHBORS
    vulnerability = np.ones(N)
    if mode not in ("no_protection", "all_off"):
        vulnerability = np.exp(-0.7 * uptake)
    death_pressure = 0.0 if mode in ("no_paracrine", "all_off") else 0.7 * exposure * vulnerability
    score = np.log(uptake + 1e-9) - death_pressure
    survivors = np.argpartition(score, -K)[-K:]
    return survivors


def run(seed, mode):
    rng = np.random.default_rng(seed)
    # Two equally sized phenotypes specialize in opposite target contexts.
    is_a = np.zeros(N, dtype=bool)
    is_a[: N // 2] = True
    rng.shuffle(is_a)
    utility_a = np.where(is_a, 0.60, 0.50) + rng.normal(0.0, 0.13, N)
    utility_b = np.where(is_a, 0.50, 0.60) + rng.normal(0.0, 0.13, N)
    survivors_a = evaluate(utility_a, mode)
    survivors_b = evaluate(utility_b, mode)
    quality_a = float(np.mean(utility_a[survivors_a]))
    quality_b = float(np.mean(utility_b[survivors_b]))
    precision_a = float(np.mean(is_a[survivors_a]))
    precision_b = float(np.mean(~is_a[survivors_b]))
    overlap = float(len(set(survivors_a).intersection(survivors_b)) / K)
    return np.array([quality_a, quality_b, precision_a, precision_b, overlap])


def main():
    modes = ("full", "no_sensitization", "no_paracrine", "no_protection", "all_off")
    results = {mode: np.array([run(seed, mode) for seed in range(SEEDS)]) for mode in modes}
    print("mode quality_a quality_b precision_a precision_b overlap; 100 seeds")
    for mode in modes:
        rows = results[mode]
        print(
            "%s %.6f %.6f %.6f %.6f %.6f"
            % (mode, rows[:, 0].mean(), rows[:, 1].mean(), rows[:, 2].mean(),
               rows[:, 3].mean(), rows[:, 4].mean())
        )
    full_quality = results["full"][:, :2].mean(axis=1)
    print("paired_delta_quality_vs_full mode mean sd")
    for mode in modes[1:]:
        delta = results[mode][:, :2].mean(axis=1) - full_quality
        print("%s %.6f %.6f" % (mode, delta.mean(), delta.std(ddof=1)))


if __name__ == "__main__":
    main()
