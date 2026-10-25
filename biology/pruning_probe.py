"""Compare partial synaptic weakening with complete edge deletion.

This controlled probe is not an organism-world candidate.
"""
import numpy as np


def run(seed, mode, scaling, n=64, d=32, steps=400, perturb_at=120):
    rng = np.random.default_rng(seed)
    w = rng.uniform(0.25, 0.75, (n, d))
    x = rng.uniform(0.0, 1.0, (steps, d))
    rates = np.zeros((steps, n))

    for t in range(perturb_at):
        rates[t] = 1.0 - np.exp(-(w @ x[t]) / np.sqrt(d))
    target = rates[perturb_at - 40:perturb_at].mean(axis=0)
    damaged = rng.random((n, d)) < 0.20
    if mode == "partial":
        w[damaged] *= 0.5
    elif mode == "delete":
        w[damaged] = 0.0
    else:
        raise ValueError(mode)
    edge_count_before = np.count_nonzero(w)

    for t in range(perturb_at, steps):
        rates[t] = 1.0 - np.exp(-(w @ x[t]) / np.sqrt(d))
        if scaling:
            recent = rates[max(perturb_at, t - 19):t + 1].mean(axis=0)
            gain = np.clip(1.0 + 0.04 * (target - recent), 0.94, 1.06)
            w *= gain[:, None]

    reference = target
    final = rates[-40:].mean(axis=0)
    error = np.linalg.norm(final - reference) / np.linalg.norm(reference)
    retained = np.count_nonzero(w) / (n * d)
    return float(error), float(retained), float(final.mean()), float(reference.mean())


def main():
    for scaling in (False, True):
        for mode in ("partial", "delete"):
            values = np.array([run(seed, mode, scaling) for seed in range(20)])
            print({
                "perturbation": mode,
                "local_scaling": scaling,
                "relative_rate_vector_error_mean": round(float(values[:, 0].mean()), 6),
                "retained_edge_fraction_mean": round(float(values[:, 1].mean()), 6),
                "final_rate_mean": round(float(values[:, 2].mean()), 6),
                "reference_rate_mean": round(float(values[:, 3].mean()), 6),
            })


if __name__ == "__main__":
    main()
