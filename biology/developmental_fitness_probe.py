"""Toy probe of intrinsic fitness selection during developmental pruning.

Candidate units have a latent maturation/utility value and a noisy local
fitness code. A finite trophic budget keeps K units. Relative competition is
implemented by weighted sampling without replacement; ablations remove the
code or use a fixed absolute threshold. The task changes its global offset,
so a relative rule should keep the same high-fitness population.
"""
import numpy as np


SEEDS = 100
N = 256
K = 64
BASELINE_SHIFT = 0.0
SHIFTED_SHIFT = 0.30


def choose(rng, utility, mode, shift):
    observed = utility + shift + rng.normal(0.0, 0.07, N)
    if mode == "relative":
        # Shared capacity: only differences from the local population mean
        # affect access to the survival resource.
        logits = 5.0 * (observed - observed.mean())
        logits -= logits.max()
        weights = np.exp(logits)
        weights /= weights.sum()
        return rng.choice(N, size=K, replace=False, p=weights)
    if mode == "random":
        return rng.choice(N, size=K, replace=False)
    if mode == "scrambled":
        scrambled = observed.copy()
        rng.shuffle(scrambled)
        logits = 5.0 * (scrambled - scrambled.mean())
        logits -= logits.max()
        weights = np.exp(logits)
        weights /= weights.sum()
        return rng.choice(N, size=K, replace=False, p=weights)
    if mode == "absolute":
        # A fixed trophic threshold is intentionally not shift invariant.
        pool = np.flatnonzero(observed >= 0.50)
        if len(pool) >= K:
            return rng.choice(pool, size=K, replace=False)
        missing = rng.choice(np.setdiff1d(np.arange(N), pool), size=K - len(pool), replace=False)
        return np.concatenate([pool, missing])
    raise ValueError(mode)


def run(seed, mode):
    rng = np.random.default_rng(seed)
    # Two intrinsic subgroups model a maturation code: the high group is
    # more likely to integrate into either downstream context.
    utility = np.concatenate([
        rng.normal(0.28, 0.07, N // 2),
        rng.normal(0.78, 0.07, N // 2),
    ])
    rng.shuffle(utility)
    high = utility >= 0.53
    chosen_a = choose(rng, utility, mode, BASELINE_SHIFT)
    chosen_b = choose(rng, utility, mode, SHIFTED_SHIFT)
    score_a = float(np.mean(utility[chosen_a]))
    score_b = float(np.mean(utility[chosen_b]))
    precision_a = float(np.mean(high[chosen_a]))
    precision_b = float(np.mean(high[chosen_b]))
    overlap = float(len(set(chosen_a).intersection(set(chosen_b))) / K)
    return np.array([score_a, score_b, precision_a, precision_b, overlap])


def main():
    print("mode score_base score_shift high_precision_base high_precision_shift survivor_overlap; 100 seeds")
    for mode in ("random", "scrambled", "absolute", "relative"):
        rows = np.array([run(seed, mode) for seed in range(SEEDS)])
        print(
            "%s %.6f %.6f %.6f %.6f %.6f"
            % (mode, rows[:, 0].mean(), rows[:, 1].mean(), rows[:, 2].mean(),
               rows[:, 3].mean(), rows[:, 4].mean())
        )


if __name__ == "__main__":
    main()
