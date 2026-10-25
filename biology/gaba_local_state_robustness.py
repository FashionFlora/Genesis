"""Paired robustness probe for activity-loaded developmental GABA polarity.

This is a toy circuit.  Every row shares the same seed and Hebbian updates;
only chloride loading mode, recovery time, or input geometry changes.
"""
from __future__ import annotations

import numpy as np

SEEDS = 100
UNITS, DIM, STEPS = 16, 32, 1200


def pattern(rng: np.random.Generator, kind: int, geometry: str,
            proto: np.ndarray) -> np.ndarray:
    x = rng.normal(0.0, 0.10, DIM)
    if geometry == "block":
        x[kind * (DIM // 2):(kind + 1) * (DIM // 2)] += 1.0
    elif geometry == "diffuse":
        x += 0.65 * proto[kind]
    else:
        raise ValueError(geometry)
    return np.maximum(x, 0.0)


def response(w, x, prev, lateral, signs):
    y = np.maximum(w @ x + 0.30 * signs * (lateral @ prev), 0.0)
    return y / (np.sqrt(np.mean(y * y)) + 1e-6)


def score(seed: int, mode: str, tau: float, load_gain: float,
          geometry: str) -> np.ndarray:
    rng = np.random.default_rng(seed)
    proto = rng.uniform(0.0, 1.0, (2, DIM))
    if geometry == "diffuse":
        proto[1] = 1.0 - proto[0]
    w = np.maximum(rng.normal(0.15, 0.03, (UNITS, DIM)), 0.0)
    w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-6
    lateral = rng.normal(0.0, 0.06, (UNITS, UNITS))
    np.fill_diagonal(lateral, 0.0)
    prev = np.zeros(UNITS)
    chloride = np.ones(UNITS)
    early, late = [], []
    for step in range(STEPS):
        mature = step >= STEPS // 2
        if mode in ("scheduled", "local", "global"):
            target = 0.0 if mature else 1.0
            chloride += (target - chloride) / tau
            if mode == "local":
                chloride += load_gain * prev
            elif mode == "global":
                chloride += load_gain * float(np.mean(prev))
            chloride = np.clip(chloride, 0.0, 1.0)
            signs = 2.0 * chloride - 1.0
        elif mode == "none":
            signs = np.zeros(UNITS)
        elif mode == "fixed_hyper":
            signs = -np.ones(UNITS)
        else:
            raise ValueError(mode)
        kind = int(mature) if rng.random() < 0.8 else 1 - int(mature)
        x = pattern(rng, kind, geometry, proto)
        y = response(w, x, prev, lateral, signs)
        w += 0.002 * (y[:, None] * x[None, :] - 0.001 * w)
        w = np.maximum(w, 0.0)
        w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-6
        lateral += 0.0005 * (np.outer(y, y) - lateral)
        np.fill_diagonal(lateral, 0.0)
        prev = y
        if step >= STEPS // 2 - 200:
            early.append(y)
        if step >= STEPS - 200:
            late.append(y)
    means = []
    for kind in (0, 1):
        vals = [response(w, pattern(rng, kind, geometry, proto),
                         np.zeros(UNITS), lateral, -np.ones(UNITS))
                for _ in range(20)]
        means.append(np.mean(vals, axis=0))
    return np.array([
        np.mean(np.abs(means[0] - means[1])),
        np.mean(np.asarray(early) > 0.2),
        np.mean(np.asarray(late) > 0.2),
        np.mean(chloride),
    ])


def main() -> None:
    print("geometry mode tau load separation early late chloride; %d seeds" % SEEDS)
    conditions = [
        ("scheduled", 30.0, 0.0), ("scheduled", 120.0, 0.0),
        ("scheduled", 480.0, 0.0), ("local", 120.0, 0.0),
        ("local", 120.0, 0.0015), ("global", 120.0, 0.0015),
        ("none", 120.0, 0.0), ("fixed_hyper", 120.0, 0.0),
    ]
    for geometry in ("block", "diffuse"):
        for mode, tau, load in conditions:
            rows = np.asarray([score(seed, mode, tau, load, geometry)
                               for seed in range(SEEDS)])
            print("%s %s %.0f %.5f %.6f %.6f %.6f %.6f" %
                  (geometry, mode, tau, load, *rows.mean(axis=0)))


if __name__ == "__main__":
    main()
