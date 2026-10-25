"""Toy test of slow complement-like tagging before developmental pruning.

The probe keeps the pruning budget identical.  Edges have a persistent
quality (the activity they contribute) plus observation noise.  A slow
low-activity tag should identify persistently weak edges more reliably than
pruning the currently weakest sample.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def run(seed: int, noise: float, mode: str, n_edges: int = 160,
        steps: int = 120, prune_every: int = 24, prune_frac: float = 0.10):
    rng = np.random.default_rng(seed)
    # Two target territories.  Each has an eye that is persistently useful;
    # the other eye supplies weaker, noisy competitors.
    eye = np.tile(np.arange(2), n_edges // 2)
    target = rng.integers(0, 2, n_edges)
    preferred = (eye == target).astype(float)
    quality = np.where(preferred > 0, rng.normal(0.82, 0.08, n_edges),
                       rng.normal(0.34, 0.10, n_edges)).clip(0.03, 1.0)
    alive = np.ones(n_edges, dtype=bool)
    weight = np.ones(n_edges, dtype=float)
    low_tag = np.zeros(n_edges, dtype=float)
    updates = max(1, steps // prune_every)

    for step in range(steps):
        obs = (quality + rng.normal(0.0, noise, n_edges)).clip(0.0, 1.2)
        obs[~alive] = 0.0
        if mode == "complement":
            # Slow complement deposition, with a hysteretic phagocytic gate.
            low_tag[alive] += 0.055 * ((1.0 - obs[alive]) - low_tag[alive])
        elif mode == "instant":
            low_tag[alive] = 1.0 - obs[alive]
        elif mode == "no_tag_random":
            low_tag[alive] *= 0.95

        if (step + 1) % prune_every == 0 and alive.sum() > 16:
            k = min(int(round(prune_frac * alive.sum())), int(alive.sum() - 16))
            candidates = np.flatnonzero(alive)
            if mode in ("complement", "instant"):
                # Small random tie break makes the budget exactly comparable.
                order = np.lexsort((rng.random(candidates.size), -low_tag[candidates]))
                drop = candidates[order[:k]]
            elif mode == "no_tag_random":
                drop = rng.choice(candidates, size=k, replace=False)
            else:
                drop = np.empty(0, dtype=int)
            alive[drop] = False
            weight[drop] = 0.0
            # A local homeostat preserves total postsynaptic resource, so the
            # readout tests which edges survive rather than trivial mass loss.
            mass = weight.sum()
            if mass > 0:
                weight[alive] *= n_edges / mass

    # Eye overlap within each target, analogous to retinogeniculate overlap.
    masses = np.zeros((2, 2), dtype=float)
    for t in range(2):
        for e in range(2):
            masses[t, e] = weight[(target == t) & (eye == e)].sum()
    overlap = float(np.minimum(masses[:, 0], masses[:, 1]).sum() / max(masses.sum(), 1e-12))
    functional = float((weight * quality * preferred).sum() / max((weight * quality).sum(), 1e-12))
    quality_retention = float(quality[alive].mean() / quality.mean())
    return overlap, functional, quality_retention, int(alive.sum()), updates


def main():
    seeds = range(200)
    rows = []
    for noise in (0.06, 0.20, 0.35):
        for mode in ("complement", "instant", "no_tag_random", "none"):
            for seed in seeds:
                vals = run(seed, noise, mode)
                rows.append({"seed": seed, "noise": noise, "mode": mode,
                             "overlap": vals[0], "functional": vals[1],
                             "quality_retention": vals[2], "alive": vals[3]})

    out = Path(__file__).with_suffix(".result.txt")
    summary = {}
    arr = {(n, m): np.array([[r[k] for k in ("overlap", "functional", "quality_retention")]
                             for r in rows if r["noise"] == n and r["mode"] == m])
           for n in (0.06, 0.20, 0.35) for m in ("complement", "instant", "no_tag_random", "none")}
    for noise in (0.06, 0.20, 0.35):
        summary[str(noise)] = {}
        for mode in ("complement", "instant", "no_tag_random", "none"):
            x = arr[(noise, mode)]
            summary[str(noise)][mode] = {"mean": x.mean(axis=0).tolist(),
                                        "sd": x.std(axis=0, ddof=1).tolist()}
        # Paired complement-minus-control deltas.  Negative overlap and
        # positive function/retention are the desired directions.
        c = arr[(noise, "complement")]
        for control in ("instant", "no_tag_random", "none"):
            d = c - arr[(noise, control)]
            summary[str(noise)]["delta_complement_minus_" + control] = {
                "mean": d.mean(axis=0).tolist(),
                "ci95": (np.quantile(d, 0.025, axis=0).tolist(),
                         np.quantile(d, 0.975, axis=0).tolist())}
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
