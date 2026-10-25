"""Survival-hazard probe for trophic competition and local paracrine feedback."""
import numpy as np


N = 256
TARGET = 64
SEEDS = 100
MAX_ROUNDS = 200
NEIGHBORS = 4


def run(seed, mode):
    rng = np.random.default_rng(seed)
    is_a = np.zeros(N, dtype=bool)
    is_a[: N // 2] = True
    rng.shuffle(is_a)
    utility_a = np.where(is_a, 0.60, 0.50) + rng.normal(0.0, 0.13, N)
    utility_b = np.where(is_a, 0.50, 0.60) + rng.normal(0.0, 0.13, N)
    utility = np.stack((utility_a, utility_b))
    rounds_by_context = []
    metrics = []
    for context in range(2):
        context_rng = np.random.default_rng(seed * 2 + context)
        alive = np.ones(N, dtype=bool)
        receptor = np.ones(N)
        rounds = 0
        for rounds in range(1, MAX_ROUNDS + 1):
            live = alive
            weights = np.where(live, np.maximum(utility[context], 0.01) * receptor, 0.0)
            uptake = TARGET * weights / max(weights.sum(), 1e-12)
            if mode not in ("no_sensitization", "all_off"):
                receptor[live] = 0.85 * receptor[live] + 0.15 * (1 + uptake[live])

            exposure = np.zeros(N)
            for offset in range(1, NEIGHBORS // 2 + 1):
                exposure += np.roll(uptake, offset) + np.roll(uptake, -offset)
            exposure /= NEIGHBORS
            vulnerability = np.ones(N)
            if mode not in ("no_protection", "all_off"):
                vulnerability = np.exp(-0.7 * uptake)
            hazard = 0.12 * np.maximum(0.0, 1.0 - uptake) ** 2
            if mode not in ("no_paracrine", "all_off"):
                hazard += 0.035 * exposure * vulnerability
            hazard[~live] = 0
            proposed = np.flatnonzero(live & (context_rng.random(N) < np.clip(hazard, 0, 0.8)))
            deaths_left = int(live.sum() - TARGET)
            if len(proposed) > deaths_left:
                proposed = context_rng.choice(proposed, size=deaths_left, replace=False)
            alive[proposed] = False
            if alive.sum() == TARGET:
                break
        survivor = np.flatnonzero(alive)
        rounds_by_context.append(rounds)
        metrics.append((len(survivor), float(utility[context, survivor].mean()),
                        float(np.mean(is_a[survivor]) if context == 0 else np.mean(~is_a[survivor]))))
    return rounds_by_context, metrics


def main():
    modes = ("full", "no_sensitization", "no_paracrine", "no_protection", "all_off")
    rows = {mode: [run(seed, mode) for seed in range(SEEDS)] for mode in modes}
    print("Command: .venv/bin/python biology/trk_survival_probe.py")
    print("N=256; target=64; seeds=100; max_rounds=200; four ring neighbors; paired seeds; separate contexts; no undershoot")
    print("mode rounds_a rounds_b survivors_a survivors_b quality_a quality_b precision_a precision_b")
    for mode in modes:
        data = rows[mode]
        rounds = np.array([x[0] for x in data])
        a = np.array([x[1][0] for x in data])
        b = np.array([x[1][1] for x in data])
        print("%s %.3f %.3f %.3f %.3f %.6f %.6f %.6f %.6f" % (
            mode, rounds[:, 0].mean(), rounds[:, 1].mean(), a[:, 0].mean(), b[:, 0].mean(),
            a[:, 1].mean(), b[:, 1].mean(), a[:, 2].mean(), b[:, 2].mean()))
    full = np.array([x[0] for x in rows["full"]], dtype=float).mean(axis=1)
    print("paired_delta_mean_context_rounds_vs_full mode mean sd")
    for mode in modes[1:]:
        delta = np.array([x[0] for x in rows[mode]], dtype=float).mean(axis=1) - full
        print("%s %.3f %.3f" % (mode, delta.mean(), delta.std(ddof=1)))
    print("Interpretation: feedback altered elimination speed in this constructed model, but did")
    print("not necessarily maximize endpoint quality. Each context stops at exactly 64 survivors;")
    print("these results are a synthetic probe, not a judge result.")


if __name__ == "__main__":
    main()
