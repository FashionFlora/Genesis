"""Ablation of a finite, activity-gated resource captured by local tags.

This is a dimensionless mechanism check.  It asks whether a shared resource
can remain permissive while tags select which traces are consolidated.
"""

from __future__ import annotations

import random


def run(seed: int, *, gated: bool = True, finite_tag: bool = True,
        selective: bool = True, consume: bool = True) -> tuple[int, int, int, float]:
    rng = random.Random(seed)
    tags: list[int] = []
    durable = 0
    off_target = 0
    spill = 0
    reservoir = 0.0
    total_release = 0.0

    for step in range(120):
        aroused = rng.random() < 0.18
        if not gated or aroused:
            reservoir = min(2.0, reservoir + 0.85)
            total_release += 0.85
        reservoir *= 0.93

        if rng.random() < 0.55:
            tags.append(step)
        distractor = rng.random() < 0.55
        if finite_tag:
            tags = [start for start in tags if step - start <= 3]

        if reservoir >= 0.35:
            if selective:
                captured = min(len(tags), int(reservoir / 0.35))
                durable += captured
                if consume:
                    reservoir -= 0.35 * captured
                tags = tags[captured:]
                if not captured:
                    spill += 1
            else:
                # A global write changes one unrelated trace whenever one is
                # available, illustrating nonspecific plasticity.
                durable += len(tags)
                off_target += int(distractor)
                if consume:
                    reservoir = max(0.0, reservoir - 0.35 * (len(tags) + int(distractor)))
                tags.clear()

    return durable, off_target, spill, total_release


def main() -> None:
    variants = {
        "gated_selective": dict(gated=True, finite_tag=True, selective=True, consume=True),
        "gated_global": dict(gated=True, finite_tag=True, selective=False, consume=True),
        "gated_no_consume": dict(gated=True, finite_tag=True, selective=True, consume=False),
        "always_selective": dict(gated=False, finite_tag=True, selective=True, consume=True),
        "gated_unlimited_tag": dict(gated=True, finite_tag=False, selective=True, consume=True),
    }
    for name, options in variants.items():
        rows = [run(seed, **options) for seed in range(1000)]
        means = [sum(row[index] for row in rows) / len(rows) for index in range(4)]
        print(f"{name}: durable={means[0]:.2f}; off_target={means[1]:.2f}; "
              f"spill={means[2]:.2f}; released={means[3]:.2f}")


if __name__ == "__main__":
    main()
