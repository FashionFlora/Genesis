"""Toy test of target-specific versus global synaptic compensation."""
import numpy as np


def run(seed, mode, targets=8, odors=5, repeats=10):
    rng = np.random.default_rng(seed)
    # Each odor drives a distinct sparse target population.
    drive = rng.uniform(0.0, 0.15, (odors, targets))
    for odor in range(odors):
        drive[odor, odor % targets] += 1.0
    release = np.full(targets, 0.75)
    sites = rng.integers(10, 31, targets).astype(float)
    baseline = np.stack([
        np.stack([rng.binomial(int(sites[j]), release[j], repeats) for j in range(targets)], axis=1)
        for _ in range(odors)
    ])
    affected = np.arange(targets // 2)
    release[affected] *= 0.6
    if mode == "target":
        sites[affected] /= 0.6
    elif mode == "global":
        sites /= 0.6
    elif mode != "none":
        raise ValueError(mode)
    after = np.stack([
        np.stack([rng.binomial(int(sites[j]), release[j], repeats) for j in range(targets)], axis=1)
        for _ in range(odors)
    ])
    weights = drive[:, None, :]
    before_out = (baseline * weights).sum(2)
    after_out = (after * weights).sum(2)
    mean_shift = np.abs(after_out.mean(1) - before_out.mean(1)) / (before_out.mean(1) + 1e-8)
    reliability = np.mean(after_out.std(1, ddof=1) / (after_out.mean(1) + 1e-8))
    return mean_shift.mean(), reliability


def main():
    for mode in ("none", "target", "global"):
        values = np.array([run(seed, mode) for seed in range(100)])
        print(f"{mode}: relative_mean_shift={values[:, 0].mean():.6f} "+
              f"(sd={values[:, 0].std(ddof=1):.6f}), after_cv={values[:, 1].mean():.6f} "+
              f"(sd={values[:, 1].std(ddof=1):.6f})")


if __name__ == "__main__":
    main()
