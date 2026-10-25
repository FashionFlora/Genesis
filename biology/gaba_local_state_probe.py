"""Probe local chloride state versus a purely scheduled GABA switch.

This is a mechanistic toy, not an organism result.  The only difference in
the paired conditions is whether each unit's chloride state receives a local
activity-dependent load; all weight and lateral updates are shared.
"""
from __future__ import annotations

import numpy as np

SEEDS = 100
UNITS = 16
DIM = 32
STEPS = 1200


def pattern(rng: np.random.Generator, kind: int) -> np.ndarray:
    x = rng.normal(0.0, 0.10, DIM)
    x[kind * (DIM // 2):(kind + 1) * (DIM // 2)] += 1.0
    return np.maximum(x, 0.0)


def response(w: np.ndarray, x: np.ndarray, prev: np.ndarray,
             lateral: np.ndarray, signs: np.ndarray) -> np.ndarray:
    y = np.maximum(w @ x + 0.30 * signs * (lateral @ prev), 0.0)
    return y / (np.sqrt(np.mean(y * y)) + 1e-6)


def score(seed: int, mode: str, tau: float = 120.0,
          load_gain: float = 0.0015) -> tuple[float, float, float, float]:
    rng = np.random.default_rng(seed)
    w = np.maximum(rng.normal(0.15, 0.03, (UNITS, DIM)), 0.0)
    w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-6
    lateral = rng.normal(0.0, 0.06, (UNITS, UNITS))
    np.fill_diagonal(lateral, 0.0)
    prev = np.zeros(UNITS)
    chloride = np.ones(UNITS)
    early = []
    late = []
    for step in range(STEPS):
        mature = step >= STEPS // 2
        if mode in ("scheduled", "local_state", "local_ablated"):
            target = 0.0 if mature else 1.0
            chloride += (target - chloride) / tau
            if mode == "local_state":
                chloride += load_gain * prev
            elif mode == "local_ablated":
                chloride += load_gain * float(np.mean(prev))
            chloride = np.clip(chloride, 0.0, 1.0)
            signs = 2.0 * chloride - 1.0
        elif mode == "fixed_hyper":
            signs = np.full(UNITS, -1.0)
        elif mode == "fixed_depol":
            signs = np.ones(UNITS)
        else:
            raise ValueError(mode)
        kind = int(mature) if rng.random() < 0.8 else 1 - int(mature)
        x = pattern(rng, kind)
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
        vals = [response(w, pattern(rng, kind), np.zeros(UNITS),
                         lateral, np.full(UNITS, -1.0)) for _ in range(20)]
        means.append(np.mean(vals, axis=0))
    separation = float(np.mean(np.abs(means[0] - means[1])))
    coverage_early = float(np.mean(np.asarray(early) > 0.2))
    coverage_late = float(np.mean(np.asarray(late) > 0.2))
    chloride_late = float(np.mean(chloride))
    return separation, coverage_early, coverage_late, chloride_late


def main() -> None:
    print("mode tau load separation coverage_early coverage_late chloride_late; %d seeds" % SEEDS)
    conditions = [
        ("scheduled", 120.0, 0.0),
        ("local_state", 120.0, 0.0015),
        ("local_ablated", 120.0, 0.0015),
        ("local_state", 30.0, 0.0015),
        ("local_state", 480.0, 0.0015),
        ("fixed_hyper", 120.0, 0.0),
        ("fixed_depol", 120.0, 0.0),
    ]
    for mode, tau, load in conditions:
        rows = np.asarray([score(seed, mode, tau, load) for seed in range(SEEDS)])
        print("%s %.0f %.4f %.6f %.6f %.6f %.6f" %
              (mode, tau, load, *rows.mean(axis=0)))


if __name__ == "__main__":
    main()
