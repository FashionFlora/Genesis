"""Measure whether crosstalk benefits survive an explicit energy tax."""
import numpy as np

from astro_lactate_shuttle_probe import run


def main():
    seeds = range(100)
    for cost in (0.0, 0.01, 0.05):
        variants = {
            f"leak_{leak}": np.asarray([
                run(seed, "local_shuttle", crosstalk=leak,
                    transfer_cost=cost)
                for seed in seeds
            ]) for leak in (0.0, 0.3, 1.0)
        }
        base = variants["leak_0.0"]
        for name, values in variants.items():
            print("mean", cost, name, "shift/recovery/delay/energy_sd",
                  *[f"{x:.6f}" for x in values[:, [1, 2, 4, 5]].mean(axis=0)])
            if name == "leak_0.0":
                continue
            delta = values[:, [1, 2, 4, 5]] - base[:, [1, 2, 4, 5]]
            mean = delta.mean(axis=0)
            se = delta.std(axis=0, ddof=1) / np.sqrt(len(delta))
            print("paired", cost, name,
                  *[f"{x:.6f}" for x in mean], "ci95",
                  *[f"{lo:.6f}:{hi:.6f}" for lo, hi in
                    zip(mean - 1.96 * se, mean + 1.96 * se)])


if __name__ == "__main__":
    main()
