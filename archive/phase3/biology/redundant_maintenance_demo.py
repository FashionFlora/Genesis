"""Toy assay: independent local maintenance routes buffer pruning.

Not a model of apoptosis or evidence for transfer to the organism judge.
"""
from __future__ import annotations

import numpy as np


def run(seed: int, route_a: bool = True, route_b: bool = True,
        independent: bool = True, n: int = 256, steps: int = 300) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    alive = np.ones(n, dtype=bool)
    deaths = 0
    for _ in range(steps):
        a = rng.random(n) < 0.4
        b = (rng.random(n) < 0.4) if independent else a.copy()
        support = (a & route_a) | (b & route_b)
        # A cell is pruned only when neither local maintenance route is present.
        die = alive & ~support & (rng.random(n) < 0.025)
        deaths += int(die.sum())
        alive[die] = False
    return {"survival_fraction": float(alive.mean()),
            "deaths_per_initial_cell": deaths / n}


if __name__ == "__main__":
    conditions = (("both_independent", True, True, True),
                  ("A_only", True, False, True),
                  ("B_only", False, True, True),
                  ("both_off", False, False, True),
                  ("both_correlated", True, True, False))
    for label, a, b, independent in conditions:
        vals = [run(seed, a, b, independent) for seed in range(100)]
        print(label + " " + " ".join(
            f"{key}={np.mean([v[key] for v in vals]):.4f}"
            for key in vals[0]))
