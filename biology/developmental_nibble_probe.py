"""Test selective, partial presynaptic remodeling against blunt pruning.

This is a small mechanistic probe, not an organism-world candidate.  The
``nibble`` rule uses recent presynaptic activity to choose edges, then removes
only half of each selected edge.  It is compared with a matched random partial
lesion and with complete deletion.  A separate switch tests local homeostatic
scaling, so recovery of activity cannot hide structural loss.
"""
import numpy as np


def run(seed, mode, scaling, n=64, d=32, steps=600, remodel_at=180):
    rng = np.random.default_rng(seed)
    w = rng.uniform(0.25, 0.75, (n, d))
    x = rng.uniform(0.0, 1.0, (steps, d))
    rates = np.zeros((steps, n))
    edge_activity = np.zeros((n, d))

    for t in range(remodel_at):
        pre = x[t]
        rates[t] = 1.0 - np.exp(-(w @ pre) / np.sqrt(d))
        # A slow local trace of presynaptic use, available to a nearby glial cell.
        edge_activity = 0.98 * edge_activity + 0.02 * (rates[t, :, None] * pre[None, :])

    baseline = rates[remodel_at - 40:remodel_at].mean(axis=0)
    count = int(round(0.20 * n * d))
    if mode == "nibble":
        # Select the least-used contacts, but retain a weakened edge.
        flat = np.argsort(edge_activity, axis=None)[:count]
        damaged = np.zeros((n, d), dtype=bool)
        damaged.flat[flat] = True
        w[damaged] *= 0.5
    elif mode == "random_partial":
        flat = rng.choice(n * d, size=count, replace=False)
        damaged = np.zeros((n, d), dtype=bool)
        damaged.flat[flat] = True
        w[damaged] *= 0.5
    elif mode == "delete":
        flat = rng.choice(n * d, size=count, replace=False)
        damaged = np.zeros((n, d), dtype=bool)
        damaged.flat[flat] = True
        w[damaged] = 0.0
    else:
        raise ValueError(mode)

    for t in range(remodel_at, steps):
        rates[t] = 1.0 - np.exp(-(w @ x[t]) / np.sqrt(d))
        if scaling:
            recent = rates[max(remodel_at, t - 19):t + 1].mean(axis=0)
            gain = np.clip(1.0 + 0.04 * (baseline - recent), 0.94, 1.06)
            w *= gain[:, None]

    final = rates[-80:].mean(axis=0)
    error = np.linalg.norm(final - baseline) / np.linalg.norm(baseline)
    return float(error), float(np.count_nonzero(w) / (n * d)), float(final.mean())


def main():
    for scaling in (False, True):
        for mode in ("nibble", "random_partial", "delete"):
            vals = np.array([run(seed, mode, scaling) for seed in range(40)])
            print({
                "mode": mode,
                "local_scaling": scaling,
                "relative_rate_vector_error_mean": round(float(vals[:, 0].mean()), 6),
                "relative_rate_vector_error_sd": round(float(vals[:, 0].std(ddof=1)), 6),
                "retained_edge_fraction_mean": round(float(vals[:, 1].mean()), 6),
                "final_rate_mean": round(float(vals[:, 2].mean()), 6),
            })


if __name__ == "__main__":
    main()
