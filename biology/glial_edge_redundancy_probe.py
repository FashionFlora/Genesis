"""Probe whether redundant glial-like paths preserve load redistribution."""
import numpy as np


def run(seed, edge_retention, edge_pattern="random", side=16, steps=600,
        perturb_at=300, coupling=0.8):
    rng = np.random.default_rng(seed)
    topo_rng = np.random.default_rng(seed + 100_003)
    n = side * side
    load = np.zeros((side, side), dtype=float)
    values = np.zeros((steps, n), dtype=float)
    lesion = rng.choice(n, size=n // 8, replace=False)
    base = rng.poisson(1.8, (steps, n)).astype(float)
    base[perturb_at:, lesion] *= 3.0

    # Each mask represents one undirected bond; reverse directions share it.
    if edge_pattern == "clustered":
        retained_columns = np.arange(side) >= side // 2
        right = np.broadcast_to(retained_columns, (side, side)).copy()
        down = right.copy()
    else:
        right = topo_rng.random((side, side)) < edge_retention
        down = topo_rng.random((side, side)) < edge_retention
    masks = (right, np.roll(right, 1, axis=1), down, np.roll(down, 1, axis=0))
    shifts = ((0, -1), (0, 1), (-1, 0), (1, 0))

    for t in range(steps):
        load += base[t].reshape(side, side)
        load *= 0.18
        flux = np.zeros_like(load)
        for mask, shift in zip(masks, shifts):
            neighbor = np.roll(load, shift, axis=(0, 1))
            flux += mask * (neighbor - load)
        load += (coupling / 4.0) * flux
        values[t] = load.ravel()

    pre = values[perturb_at - 80:perturb_at]
    post = values[-80:]
    return {
        "pre_p95": float(np.quantile(pre, 0.95)),
        "post_p95": float(np.quantile(post, 0.95)),
        "post_max": float(post.max()),
        "post_mean": float(post.mean()),
    }


def main():
    conditions = (("intact", 1.0, "random"),
                  ("random_50", 0.5, "random"),
                  ("clustered_50", 0.5, "clustered"))
    for name, retention, pattern in conditions:
        vals = [run(seed, retention, pattern) for seed in range(100)]
        print({
            "condition": name,
            "edge_retention": retention,
            "pre_p95_mean": round(float(np.mean([v["pre_p95"] for v in vals])), 6),
            "post_p95_mean": round(float(np.mean([v["post_p95"] for v in vals])), 6),
            "post_max_mean": round(float(np.mean([v["post_max"] for v in vals])), 6),
            "post_mean": round(float(np.mean([v["post_mean"] for v in vals])), 6),
        })


if __name__ == "__main__":
    main()
