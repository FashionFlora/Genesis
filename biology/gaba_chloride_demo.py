"""Toy ablation of a developmental GABA polarity switch.

The source anchors the direction of the mechanism, not these parameters:
NKCC1 keeps intracellular chloride high in immature neurons; KCC2 lowers it
as neurons mature.  A positive GABA sign is treated as a growth drive and a
negative sign as a stabilizing brake.  This is not a neural model or an
organism result.
"""

import random


def run(mode, seed, steps=200):
    rng = random.Random(seed)
    # 0.10 is the lower end of the reported neonatal KCC2 fraction (5-15%).
    kcc2 = 0.10
    state = 0.0
    mass = 0.5
    early_growth = 0.0
    late_variance = 0.0

    for t in range(steps):
        mature = t >= steps // 2
        if mode == "switch":
            # Slow developmental increase in chloride extrusion.
            kcc2 = 0.10 + 0.90 * (t / (steps - 1))
            gaba_sign = 1.0 - 2.0 * kcc2
        elif mode == "always_exc":
            gaba_sign = 1.0
        elif mode == "always_inh":
            gaba_sign = -1.0
        else:
            raise ValueError(mode)

        drive = 0.35 + rng.uniform(-0.04, 0.04)
        activity = max(0.0, drive + gaba_sign * 0.30 * state)
        # The same local signal first supports growth, then limits runaway drift.
        mass = max(0.0, mass + 0.04 * activity - 0.025 * max(0.0, -gaba_sign) * mass)
        state += 0.08 * gaba_sign * (activity - 0.30)
        if not mature:
            early_growth += mass
        else:
            late_variance += abs(state)

    return mass, early_growth / (steps // 2), late_variance / (steps // 2)


if __name__ == "__main__":
    for mode in ("switch", "always_exc", "always_inh"):
        rows = [run(mode, seed) for seed in range(100)]
        means = [sum(row[i] for row in rows) / len(rows) for i in range(3)]
        print(
            f"{mode}: final_mass={means[0]:.3f}; "
            f"early_growth={means[1]:.3f}; late_abs_state={means[2]:.3f}"
        )
