"""Noise sensitivity of sensory novelty gating versus gate ablations."""
import numpy as np

from pnn_temporal_probe import run


def main():
    for noise in (0.05, 0.15, 0.30):
        for mode in ("sensory", "ablated", "always"):
            results = {}
            for schedule in ("regular", "burst"):
                results[schedule] = np.array([
                    run(seed, schedule, mode, input_noise=noise)
                    for seed in range(100)
                ])
            for schedule, vals in results.items():
                print({"noise": noise, "gate": mode, "schedule": schedule,
                       "B_error": round(float(vals[:, 0].mean()), 6),
                       "A_recall_error": round(float(vals[:, 1].mean()), 6),
                       "plasticity_cost": round(float(vals[:, 3].mean()), 6)})
            delta = results["burst"] - results["regular"]
            ci = 1.96 * delta.std(axis=0, ddof=1) / np.sqrt(len(delta))
            print({"noise": noise, "gate": mode,
                   "burst_minus_regular": [round(float(v), 6) for v in delta.mean(axis=0)],
                   "ci95_half_width": [round(float(v), 6) for v in ci]})


if __name__ == "__main__":
    main()
