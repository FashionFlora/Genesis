"""Probe for local astrocyte-like ion buffering through gap-junction diffusion.

This is a mechanistic probe, not an organism candidate. Every condition uses
the same stochastic input and lesion for a seed; only neighbor coupling changes.
"""
import numpy as np


def run(seed, coupling, side=16, steps=600, perturb_at=300):
    rng = np.random.default_rng(seed)
    n = side * side
    load = np.zeros(n, dtype=float)
    values = np.zeros((steps, n), dtype=float)
    # A fixed local insult tests whether connected glia can redistribute load.
    lesion = rng.choice(n, size=n // 8, replace=False)
    base = rng.poisson(1.8, (steps, n)).astype(float)
    base[perturb_at:, lesion] *= 3.0
    for t in range(steps):
        load += base[t]
        load *= 0.18  # 82% local clearance each step
        if coupling:
            grid = load.reshape(side, side)
            neighbors = (
                np.roll(grid, 1, 0)
                + np.roll(grid, -1, 0)
                + np.roll(grid, 1, 1)
                + np.roll(grid, -1, 1)
            ) / 4.0
            load += coupling * (neighbors.reshape(-1) - load)
        values[t] = load
    pre = values[perturb_at - 80:perturb_at]
    post = values[-80:]
    threshold = 4.0
    return {
        "pre_p95": float(np.quantile(pre, 0.95)),
        "post_p95": float(np.quantile(post, 0.95)),
        "post_max": float(post.max()),
        "post_overload_fraction": float((post > threshold).mean()),
        "post_mean": float(post.mean()),
    }


def main():
    for coupling in (0.0, 0.5, 1.0):
        vals = [run(seed, coupling) for seed in range(100)]
        print({
            "coupling": coupling,
            "pre_p95_mean": round(float(np.mean([v["pre_p95"] for v in vals])), 6),
            "post_p95_mean": round(float(np.mean([v["post_p95"] for v in vals])), 6),
            "post_max_mean": round(float(np.mean([v["post_max"] for v in vals])), 6),
            "post_overload_fraction_mean": round(float(np.mean([v["post_overload_fraction"] for v in vals])), 6),
            "post_mean": round(float(np.mean([v["post_mean"] for v in vals])), 6),
        })


if __name__ == "__main__":
    main()
