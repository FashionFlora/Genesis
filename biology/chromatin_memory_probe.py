"""Test local mark propagation against turnover in a spatial memory trace.

This dimensionless toy model is inspired by chromatin-domain dynamics. It is
not a model of neurons or a biological rate fit. Propagation is ablated while
the same turnover remains, and propagation-heavy / turnover-heavy conditions
test the boundary-stability tradeoff.
"""
import numpy as np


def run(seed, propagation, turnover, n=128, steps=1200):
    rng = np.random.default_rng(seed)
    marked = np.zeros(n, dtype=bool)
    induced = slice(n // 2 - 4, n // 2 + 4)

    for t in range(steps):
        if t < 20:
            marked[induced] = True
        neighbors = np.zeros(n, dtype=np.int8)
        neighbors[1:] += marked[:-1]
        neighbors[:-1] += marked[1:]
        add = (~marked) & (rng.random(n) < propagation * neighbors / 2.0)
        remove = marked & (rng.random(n) < turnover)
        marked = (marked | add) & ~remove

    retained = float(marked[induced].mean())
    leak = float(marked[:n // 2 - 4].mean() + marked[n // 2 + 4:].mean()) / 2.0
    return retained, leak, float(marked.mean())


def main():
    conditions = {
        "propagation_ablated": (0.0, 0.01),
        "balanced": (0.01, 0.01),
        "propagation_2x": (0.02, 0.01),
        "propagation_heavy": (0.03, 0.01),
        "propagation_5x": (0.05, 0.01),
        "propagation_7x": (0.07, 0.01),
        "turnover_heavy": (0.01, 0.03),
    }
    for name, rates in conditions.items():
        vals = np.array([run(seed, *rates) for seed in range(80)])
        print({
            "condition": name,
            "propagation": rates[0],
            "turnover": rates[1],
            "induced_region_retention_mean": round(float(vals[:, 0].mean()), 6),
            "induced_region_retention_sd": round(float(vals[:, 0].std(ddof=1)), 6),
            "outside_leak_mean": round(float(vals[:, 1].mean()), 6),
            "total_marked_fraction_mean": round(float(vals[:, 2].mean()), 6),
        })


if __name__ == "__main__":
    main()
