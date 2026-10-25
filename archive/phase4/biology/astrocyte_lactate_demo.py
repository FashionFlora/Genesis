"""Toy ablation of activity-gated shared metabolic support for memory tags.

The numbers are deliberately dimensionless.  This checks the mechanism's
logic, not a biological estimate of lactate concentration or timing.
"""

from __future__ import annotations

import random


def run(seed: int, *, gated: bool = True, resource: bool = True,
        finite_tag: bool = True) -> tuple[int, int, float]:
    rng = random.Random(seed)
    tags: list[int] = []
    durable = 0
    spill = 0
    reservoir = 0.0

    for step in range(80):
        # Most episodes are weak; occasional arousal drives astrocyte release.
        aroused = rng.random() < 0.20
        if resource and (aroused or not gated):
            reservoir = min(1.0, reservoir + 0.85)
        reservoir *= 0.93

        if rng.random() < 0.55:
            tags.append(step)
        if finite_tag:
            tags = [start for start in tags if step - start <= 3]

        # A shared resource captures all currently tagged traces.  A trace
        # without a tag is counted as spillover when resource is present.
        if reservoir >= 0.35 and tags:
            durable += len(tags)
            tags.clear()
            reservoir *= 0.45
        elif reservoir >= 0.35 and not tags:
            spill += 1

    return durable, spill, reservoir


def main() -> None:
    variants = {
        "gated_finite": dict(gated=True, resource=True, finite_tag=True),
        "no_resource": dict(gated=True, resource=False, finite_tag=True),
        "always_resource": dict(gated=False, resource=True, finite_tag=True),
        "unlimited_tag": dict(gated=True, resource=True, finite_tag=False),
    }
    for name, options in variants.items():
        rows = [run(seed, **options) for seed in range(100)]
        mean_durable = sum(row[0] for row in rows) / len(rows)
        mean_spill = sum(row[1] for row in rows) / len(rows)
        mean_reservoir = sum(row[2] for row in rows) / len(rows)
        print(f"{name}: durable={mean_durable:.2f}; spill={mean_spill:.2f}; "
              f"terminal_resource={mean_reservoir:.3f}")


if __name__ == "__main__":
    main()
