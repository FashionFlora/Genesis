#!/usr/bin/env python3
"""Toy test of selective offline downscaling (not an organism result)."""
import numpy as np


def run(seed, mode, n=100, engram_n=12):
    rng = np.random.default_rng(seed)
    baseline = rng.uniform(0.5, 1.0, n)
    wake = baseline * rng.uniform(1.0, 1.35, n)
    engram = rng.choice(n, engram_n, replace=False)
    before = wake[engram].copy()

    if mode == "selective":
        # Approximate the reported ~18% shrinkage in 80% of synapses.
        down = rng.choice(np.setdiff1d(np.arange(n), engram), int(0.8 * n), replace=False)
        wake[down] *= 0.82
        # Replay protects the tagged subset during the same offline period.
        wake[engram] *= 1.04
    elif mode == "global":
        wake *= 0.82
    elif mode == "random":
        down = rng.choice(n, int(0.8 * n), replace=False)
        wake[down] *= 0.82
    elif mode != "none":
        raise ValueError(mode)

    # Relative memory signal and synaptic mass are the two reported outcomes.
    rank_signal = (wake[engram].mean() / wake[np.setdiff1d(np.arange(n), engram)].mean())
    # Amplitude retention catches uniform shrinkage that cosine similarity misses.
    retention = float(wake[engram].mean() / before.mean())
    return retention, rank_signal, float(wake.sum())


def main():
    modes = ("selective", "global", "random", "none")
    for mode in modes:
        vals = np.array([run(seed, mode) for seed in range(100)])
        print(f"{mode:9s} retention={vals[:, 0].mean():.3f} "
              f"rank_signal={vals[:, 1].mean():.3f} mass={vals[:, 2].mean():.2f}")


if __name__ == "__main__":
    main()
