"""Test whether mixing local metabolic reservoirs changes reversal learning."""
import numpy as np

from astro_lactate_shuttle_probe import run


def main():
    variants = [("local", 0.0), ("leak_0.1", 0.1), ("leak_0.3", 0.3),
                ("leak_0.6", 0.6), ("leak_1.0", 1.0), ("global", None)]
    results = {}
    for name, leak in variants:
        if leak is None:
            values = np.asarray([run(seed, "global_shuttle") for seed in range(100)])
        else:
            values = np.asarray([run(seed, "local_shuttle", crosstalk=leak)
                                 for seed in range(100)])
        mean = values.mean(axis=0)
        sd = values.std(axis=0)
        results[name] = values
        print(name, "early/shift/recovery/late/delay",
              *[f"{x:.6f}" for x in mean[:5]],
              "sd", *[f"{x:.6f}" for x in sd[:5]])
    baseline = results["local"]
    for name, _ in variants[1:]:
        delta = results[name][:, [1, 2, 4]] - baseline[:, [1, 2, 4]]
        mean = delta.mean(axis=0)
        se = delta.std(axis=0, ddof=1) / np.sqrt(len(delta))
        print("paired_delta_vs_local", name, "shift/recovery/delay",
              *[f"{x:.6f}" for x in mean], "95pct_ci",
              *[f"{lo:.6f}:{hi:.6f}" for lo, hi in zip(mean - 1.96 * se,
                                                           mean + 1.96 * se)])


if __name__ == "__main__":
    main()
