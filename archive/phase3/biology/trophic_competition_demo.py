"""Toy assay for local resource competition and its ablation.

This tests whether a shared, finite support pool makes active units sparse.
It does not model apoptosis biophysics or the organism world.
"""
from __future__ import annotations

import numpy as np


def run(seed: int, competition: bool, n: int = 64, steps: int = 400) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    active = rng.random(n) < 0.5
    support = np.zeros(n, dtype=float)
    deaths = births = 0
    neighbors = np.roll(np.arange(n), 1), np.roll(np.arange(n), -1)
    for _ in range(steps):
        local_activity = (active[neighbors[0]].astype(float) + active[neighbors[1]]) / 2
        # Local trophic support is released by active units and shared nearby.
        support = 0.9 * support + 0.1 * (1.0 - local_activity)
        if competition:
            hazard = np.clip(0.08 * (0.5 - support), 0.0, 0.08)
            die = active & (rng.random(n) < hazard)
            deaths += int(die.sum())
            active[die] = False
            # Stochastic local recruitment keeps the population from trivially dying out.
            grow = (~active) & (rng.random(n) < 0.025 * support)
            births += int(grow.sum())
            active[grow] = True
    return {
        "active_fraction": float(active.mean()),
        "adjacent_pair_fraction": float(np.mean(active & np.roll(active, 1))),
        "turnover_per_step": float((deaths + births) / steps),
    }


if __name__ == "__main__":
    for condition in (True, False):
        values = [run(seed, condition) for seed in range(100)]
        means = {key: np.mean([v[key] for v in values]) for key in values[0]}
        print(f"competition={condition} " + " ".join(f"{k}={v:.4f}" for k, v in means.items()))
