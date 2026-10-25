"""Probe whether front-loaded partial remodeling differs from a fixed rate.

This is a mechanistic matrix simulation, not an organism-world result. The
conditions receive the same total number of edge attenuations.
"""
import numpy as np


def run(seed, schedule, n=64, d=32, phases=5, steps_per_phase=120):
    rng = np.random.default_rng(seed)
    w = rng.uniform(0.25, 0.75, (n, d))
    probe = rng.uniform(0.0, 1.0, (256, d))
    baseline = 1.0 - np.exp(-(w @ probe.T) / np.sqrt(d))
    trace = np.zeros_like(w)

    for phase in range(phases):
        x = rng.uniform(0.0, 1.0, (steps_per_phase, d))
        # Slowly changing input statistics mimic a changing developmental niche.
        x[:, (phase * 5) % d:((phase * 5) % d) + 8] *= 0.25
        for sample in x:
            y = 1.0 - np.exp(-(w @ sample) / np.sqrt(d))
            trace = 0.98 * trace + 0.02 * (y[:, None] * sample[None, :])
        count = int(round(schedule[phase] * n * d / 100.0))
        if count:
            flat = np.argsort(trace, axis=None)[:count]
            w.flat[flat] *= 0.9

    final = 1.0 - np.exp(-(w @ probe.T) / np.sqrt(d))
    err = np.linalg.norm(final - baseline) / np.linalg.norm(baseline)
    return float(err), float(w.mean()), float(w.sum(axis=1).std())


def main():
    schedules = {
        "none": (0, 0, 0, 0, 0),
        "constant": (2, 2, 2, 2, 2),
        "front_loaded_taper": (4, 3, 2, 1, 0),
    }
    for name, schedule in schedules.items():
        vals = np.array([run(seed, schedule) for seed in range(40)])
        print({
            "schedule": name,
            "attenuation_events_percent": sum(schedule),
            "relative_response_error_mean": round(float(vals[:, 0].mean()), 6),
            "relative_response_error_sd": round(float(vals[:, 0].std(ddof=1)), 6),
            "mean_weight_mean": round(float(vals[:, 1].mean()), 6),
            "row_sum_sd_mean": round(float(vals[:, 2].mean()), 6),
        })


if __name__ == "__main__":
    main()
