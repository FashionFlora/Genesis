"""Toy assay: local vacancy-driven recruitment stabilizes a pruned population.

The rule uses no task reward: a vacant site can be filled only when a living
neighbor remains. This is a digital check of the proposed mechanism, not an
organism-judge result.
"""
from __future__ import annotations

import numpy as np


def run(seed: int, route_a: bool = True, route_b: bool = True,
        independent: bool = True, recruit: bool = True, n: int = 256,
        steps: int = 300) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    alive = np.ones(n, dtype=bool)
    deaths = births = 0
    for _ in range(steps):
        a = rng.random(n) < 0.4
        b = (rng.random(n) < 0.4) if independent else a.copy()
        support = (a & route_a) | (b & route_b)
        die = alive & ~support & (rng.random(n) < 0.025)
        deaths += int(die.sum())
        alive[die] = False
        if recruit:
            # A vacancy is locally repairable only if either ring neighbor lives.
            neighbor = np.roll(alive, 1) | np.roll(alive, -1)
            vacant = ~alive & neighbor & (rng.random(n) < 0.8)
            births += int(vacant.sum())
            alive[vacant] = True
    return {"occupancy": float(alive.mean()),
            "deaths_per_initial_cell": deaths / n,
            "births_per_initial_cell": births / n}


if __name__ == "__main__":
    conditions = (("independent_recruit", True, True, True, True),
                  ("correlated_recruit", True, True, False, True),
                  ("A_only_recruit", True, False, True, True),
                  ("both_off_recruit", False, False, True, True),
                  ("independent_no_recruit", True, True, True, False))
    for label, a, b, independent, recruit in conditions:
        vals = [run(seed, a, b, independent, recruit) for seed in range(100)]
        print(label + " " + " ".join(
            f"{key}={np.mean([v[key] for v in vals]):.4f}"
            for key in vals[0]))
