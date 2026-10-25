"""Test whether reservoir mixing survives changes in endogenous energy noise."""
import numpy as np

from astro_lactate_shuttle_probe import run


def main():
    for noise in (0.02, 0.08, 0.20):
        variants = {
            "local": np.asarray([run(s, "local_shuttle", noise=noise, crosstalk=0.0)
                                 for s in range(100)]),
            "leak_0.3": np.asarray([run(s, "local_shuttle", noise=noise, crosstalk=0.3)
                                    for s in range(100)]),
            "leak_1.0": np.asarray([run(s, "local_shuttle", noise=noise, crosstalk=1.0)
                                    for s in range(100)]),
            "global": np.asarray([run(s, "global_shuttle", noise=noise)
                                  for s in range(100)]),
        }
        for name, values in variants.items():
            print("mean", noise, name, "shift/recovery/delay",
                  *[f"{x:.6f}" for x in values[:, [1, 2, 4]].mean(axis=0)])
        base = variants["local"]
        for name in ("leak_0.3", "leak_1.0", "global"):
            delta = variants[name][:, [1, 2, 4]] - base[:, [1, 2, 4]]
            mean = delta.mean(axis=0)
            se = delta.std(axis=0, ddof=1) / np.sqrt(len(delta))
            print("paired", noise, name,
                  *[f"{x:.6f}" for x in mean],
                  "ci95", *[f"{lo:.6f}:{hi:.6f}" for lo, hi in
                            zip(mean - 1.96 * se, mean + 1.96 * se)])


if __name__ == "__main__":
    main()
