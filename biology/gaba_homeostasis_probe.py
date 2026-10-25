"""Probe local chloride loading and maturation-dependent extrusion.

This is a mechanistic toy, not an organism result.  GABA's sign is derived
from each unit's chloride state.  Activity loads chloride; a slow, local
KCC2-like extrusion term becomes available during maturation.  Ablations
separate local from global activity and remove either load or extrusion.
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
             lateral: np.ndarray, chloride: np.ndarray, gaba: bool) -> np.ndarray:
    signs = 2.0 * chloride - 1.0
    lateral_drive = 0.30 * signs * (lateral @ prev) if gaba else 0.0
    y = np.maximum(w @ x + lateral_drive, 0.0)
    return y / (np.sqrt(np.mean(y * y)) + 1e-6)


def score(seed: int, mode: str, tau: float = 120.0,
          load_gain: float = 0.0015, extrude_gain: float = 0.0025
          ) -> tuple[float, float, float, float]:
    rng = np.random.default_rng(seed)
    w = np.maximum(rng.normal(0.15, 0.03, (UNITS, DIM)), 0.0)
    w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-6
    lateral = rng.normal(0.0, 0.06, (UNITS, UNITS))
    np.fill_diagonal(lateral, 0.0)
    prev = np.zeros(UNITS)
    chloride = np.ones(UNITS)
    early, late = [], []
    for step in range(STEPS):
        mature = step >= STEPS // 2
        target = 0.0 if mature else 1.0
        chloride += (target - chloride) / tau
        if mode in ("local", "global"):
            activity = prev if mode == "local" else np.full(UNITS, float(np.mean(prev)))
            chloride += load_gain * activity
            chloride -= extrude_gain * float(mature) * activity * chloride
        elif mode == "load_only":
            chloride += load_gain * prev
        elif mode == "extrusion_only":
            chloride -= extrude_gain * float(mature) * prev * chloride
        chloride = np.clip(chloride, 0.0, 1.0)
        kind = int(mature) if rng.random() < 0.8 else 1 - int(mature)
        x = pattern(rng, kind)
        y = response(w, x, prev, lateral, chloride,
                     mode != "none")
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
        vals = [response(w, pattern(rng, kind), np.zeros(UNITS), lateral,
                         np.full(UNITS, -1.0), True) for _ in range(20)]
        means.append(np.mean(vals, axis=0))
    separation = float(np.mean(np.abs(means[0] - means[1])))
    cov_early = float(np.mean(np.asarray(early) > 0.2))
    cov_late = float(np.mean(np.asarray(late) > 0.2))
    return separation, cov_early, cov_late, float(np.mean(chloride))


def main() -> None:
    print("mode separation coverage_early coverage_late chloride_late; %d seeds" % SEEDS)
    for mode in ("none", "load_only", "extrusion_only", "global", "local"):
        rows = np.asarray([score(seed, mode) for seed in range(SEEDS)])
        print("%s %.6f %.6f %.6f %.6f" % (mode, *rows.mean(axis=0)))
    print("robustness local tau")
    for tau in (30.0, 120.0, 480.0):
        rows = np.asarray([score(seed, "local", tau=tau) for seed in range(SEEDS)])
        print("%.0f %.6f %.6f %.6f %.6f" % (tau, *rows.mean(axis=0)))


if __name__ == "__main__":
    main()
