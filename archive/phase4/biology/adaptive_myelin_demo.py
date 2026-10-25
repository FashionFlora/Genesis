"""Toy ablation: activity-dependent, path-specific myelin protects a skill.

This is a logic check inspired by McKenzie et al. (Science 2014), not a
biological fit.  A slowly acquired local sheath raises learning rate and
reduces drift from inactive noise; the sheath has a finite shared budget.
"""

from __future__ import annotations

import math
import random


N_PATHS = 8
ETA = 0.10
DRIFT = 0.006
MYELIN_BUDGET = 3.2


def _allocate(m: list[float], active: int, mode: str) -> None:
    if mode == "none":
        for i in range(N_PATHS):
            m[i] = 0.0
        return
    if mode == "global":
        level = min(MYELIN_BUDGET / N_PATHS, m[active] + 0.09 * (MYELIN_BUDGET / N_PATHS - m[active]))
        for i in range(N_PATHS):
            m[i] = level
        return
    if mode == "instant":
        for i in range(N_PATHS):
            m[i] = 1.0
        return
    # Local precursor supply: the active route gains sheath while old routes
    # slowly relax, then the total is clipped to a finite developmental pool.
    for i in range(N_PATHS):
        m[i] *= 0.999
    m[active] += 0.11 * (1.0 - m[active])
    total = sum(m)
    if total > MYELIN_BUDGET:
        scale = MYELIN_BUDGET / total
        for i in range(N_PATHS):
            m[i] *= scale


def run(seed: int, mode: str) -> tuple[float, float, float, float]:
    rng = random.Random(seed)
    target = [(-1.0 + 2.0 * i / (N_PATHS - 1)) for i in range(N_PATHS)]
    learned = [rng.uniform(-0.35, 0.35) for _ in range(N_PATHS)]
    myelin = [0.0] * N_PATHS

    # Novel paths are encountered in a fixed stream, as a skill curriculum.
    for step in range(18 * N_PATHS):
        active = step % N_PATHS
        _allocate(myelin, active, mode)
        rate = ETA * (0.18 + 1.35 * myelin[active])
        learned[active] += rate * (target[active] - learned[active])
        for i in range(N_PATHS):
            if i != active:
                learned[i] += DRIFT * (1.0 - myelin[i]) * (rng.uniform(-1.0, 1.0) - learned[i])

    initial_error = sum(abs(learned[i] - target[i]) for i in range(N_PATHS)) / N_PATHS
    initial_accuracy = sum(abs(learned[i] - target[i]) < 0.22 for i in range(N_PATHS)) / N_PATHS

    # Change one path after consolidation.  A useful mechanism should adapt
    # that path while preserving the other seven.
    changed_target = -target[0]
    for _ in range(20):
        _allocate(myelin, 0, mode)
        rate = ETA * (0.18 + 1.35 * myelin[0])
        learned[0] += rate * (changed_target - learned[0])
        for i in range(1, N_PATHS):
            learned[i] += DRIFT * (1.0 - myelin[i]) * (rng.uniform(-1.0, 1.0) - learned[i])

    new_error = abs(learned[0] - changed_target)
    retained = sum(abs(learned[i] - target[i]) < 0.22 for i in range(1, N_PATHS)) / (N_PATHS - 1)
    return initial_error, initial_accuracy, new_error, retained


def main() -> None:
    for mode in ("local", "global", "none", "instant"):
        rows = [run(seed, mode) for seed in range(500)]
        means = [sum(row[j] for row in rows) / len(rows) for j in range(4)]
        print(
            f"{mode}: initial_mae={means[0]:.4f}; initial_accuracy={means[1]:.4f}; "
            f"new_path_mae={means[2]:.4f}; old_retention={means[3]:.4f}"
        )


if __name__ == "__main__":
    main()
