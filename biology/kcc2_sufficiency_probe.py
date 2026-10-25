"""Test whether a KCC2-like transporter state, rather than a sign schedule,
causes the developmental GABA transition.

This is a mechanistic toy probe.  Chloride is a local state and KCC2 is a
local transport capacity.  The calcium proxy is the depolarizing component of
the lateral GABA drive; no labels or reward are used by the update.
"""
from __future__ import annotations

import numpy as np

SEEDS = 120
UNITS = 20
DIM = 40
STEPS = 1600
SWITCH = STEPS // 2


def pattern(rng: np.random.Generator, kind: int) -> np.ndarray:
    x = rng.normal(0.0, 0.10, DIM)
    half = DIM // 2
    x[kind * half:(kind + 1) * half] += 1.0
    return np.maximum(x, 0.0)


def response(w: np.ndarray, x: np.ndarray, prev: np.ndarray,
             lateral: np.ndarray, chloride: np.ndarray) -> tuple[np.ndarray, float]:
    signs = 2.0 * chloride - 1.0
    gaba = 0.30 * signs * (lateral @ prev)
    y = np.maximum(w @ x + gaba, 0.0)
    y /= np.sqrt(np.mean(y * y)) + 1e-6
    calcium = float(np.mean(np.maximum(gaba, 0.0)))
    return y, calcium


def score(seed: int, mode: str, expression_gain: float = 0.80,
          transport: float = 0.020) -> tuple[float, float, float, float, float]:
    rng = np.random.default_rng(seed)
    w = np.maximum(rng.normal(0.15, 0.03, (UNITS, DIM)), 0.0)
    w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-6
    lateral = rng.normal(0.0, 0.06, (UNITS, UNITS))
    np.fill_diagonal(lateral, 0.0)
    chloride = np.full(UNITS, 0.85)
    kcc2 = np.zeros(UNITS)
    prev = np.zeros(UNITS)
    early_ca, late_ca, early_cov, late_cov = [], [], [], []

    for step in range(STEPS):
        mature = step >= SWITCH
        if mode == "endogenous":
            target = expression_gain / (1.0 + np.exp(-(step - SWITCH) / 140.0))
            kcc2 += (target - kcc2) / 35.0
        elif mode == "premature":
            kcc2 += (expression_gain - kcc2) / 35.0
        elif mode == "no_kcc2":
            kcc2.fill(0.0)
        elif mode == "fixed_schedule":
            kcc2.fill(0.0)
        else:
            raise ValueError(mode)

        # Passive chloride loading opposes KCC2 extrusion.  The fixed-sign
        # control bypasses this state while keeping all other updates equal.
        chloride += 0.010 * (0.85 - chloride) - transport * kcc2 * chloride
        chloride = np.clip(chloride, 0.0, 1.0)
        if mode == "fixed_schedule":
            chloride.fill(0.85 if not mature else 0.15)

        kind = int(mature) if rng.random() < 0.8 else 1 - int(mature)
        x = pattern(rng, kind)
        y, calcium = response(w, x, prev, lateral, chloride)
        w += 0.002 * (y[:, None] * x[None, :] - 0.001 * w)
        w = np.maximum(w, 0.0)
        w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-6
        lateral += 0.0005 * (np.outer(y, y) - lateral)
        np.fill_diagonal(lateral, 0.0)
        prev = y
        cov = float(np.mean(y > 0.2))
        if step >= SWITCH - 200:
            early_ca.append(calcium)
            early_cov.append(cov)
        if step >= STEPS - 200:
            late_ca.append(calcium)
            late_cov.append(cov)

    means = []
    for kind in (0, 1):
        vals = [response(w, pattern(rng, kind), np.zeros(UNITS), lateral,
                          chloride)[0] for _ in range(20)]
        means.append(np.mean(vals, axis=0))
    separation = float(np.mean(np.abs(means[0] - means[1])))
    return (separation, float(np.mean(early_ca)), float(np.mean(late_ca)),
            float(np.mean(early_cov)), float(np.mean(late_cov)))


def main() -> None:
    print("mode separation calcium_early calcium_late coverage_early coverage_late; %d seeds" % SEEDS)
    for mode in ("no_kcc2", "endogenous", "premature", "fixed_schedule"):
        rows = np.asarray([score(seed, mode) for seed in range(SEEDS)])
        print("%s %.6f %.6f %.6f %.6f %.6f" % (mode, *rows.mean(axis=0)))
    print("robustness endogenous gain transport")
    for gain, rate in ((0.40, 0.020), (0.80, 0.020), (1.20, 0.020),
                       (0.80, 0.010), (0.80, 0.040)):
        rows = np.asarray([score(seed, "endogenous", gain, rate)
                           for seed in range(SEEDS)])
        print("%.2f %.3f %.6f %.6f %.6f %.6f %.6f" %
              (gain, rate, *rows.mean(axis=0)))


if __name__ == "__main__":
    main()
