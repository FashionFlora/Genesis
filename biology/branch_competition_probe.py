"""Probe branch-local competition as an unsupervised binding mechanism.

The experiment is deliberately small: two noisy feature bindings are shown in
an interleaved stream.  A winner-take-all branch update is compared with a
matched global update whose total update mass is the same.  No labels or
external reward are used during learning.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


N_SEEDS = 100
D = 24
BRANCHES = 4
STEPS = 800
ETA = 0.08
NOISE = 0.08


def make_patterns(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    # Each pattern binds one feature from each half of the input.  The two
    # patterns share no exact feature, while recombinations test binding.
    a = np.zeros(D, dtype=np.float64)
    b = np.zeros(D, dtype=np.float64)
    a[[0, 2, 4, 12, 14, 16]] = 1.0
    b[[6, 8, 10, 18, 20, 22]] = 1.0
    # A fixed random permutation per seed prevents a hand-coded branch index.
    perm = rng.permutation(D)
    return a[perm], b[perm]


def sample(pattern: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    x = pattern + rng.normal(0.0, NOISE, size=pattern.shape)
    return np.clip(x, 0.0, 1.0)


def run(seed: int, mode: str) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    a, b = make_patterns(rng)
    w = rng.uniform(0.0025, 0.0225, size=(BRANCHES, D))
    w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-9

    for t in range(STEPS):
        x = sample(a if t % 2 == 0 else b, rng)
        scores = w @ x / (np.linalg.norm(w, axis=1) * np.linalg.norm(x) + 1e-9)
        winner = int(np.argmax(scores))
        if mode == "local":
            w[winner] += ETA * (x - w[winner])
        elif mode == "global":
            # Same total update mass as one local update, spread over all
            # branches; this controls for learning-rate budget.
            w += (ETA / BRANCHES) * (x[None, :] - w)
        elif mode == "single":
            w[0] += ETA * (x - w[0])
        else:
            raise ValueError(mode)
        w = np.clip(w, 0.0, None)
        w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-9

    def score(x: np.ndarray) -> np.ndarray:
        return w @ x / (np.linalg.norm(w, axis=1) * np.linalg.norm(x) + 1e-9)

    # Use noisy held-out samples.  The winning branch for each pure pattern
    # is the learned identity; a recombination should not score as either
    # pure pattern if branches have bound the two conjunctions separately.
    pure_a = np.mean([score(sample(a, rng)).max() for _ in range(80)])
    pure_b = np.mean([score(sample(b, rng)).max() for _ in range(80)])
    sa = score(a)
    sb = score(b)
    ia, ib = int(np.argmax(sa)), int(np.argmax(sb))
    separation = float(np.abs(sa[ia] - sa[ib]) + np.abs(sb[ib] - sb[ia])) / 2.0
    occupancy = float(len({ia, ib}) == 2)
    recomb = 0.5 * (a + b)
    recomb_score = float(score(recomb).max())
    pure_score = 0.5 * (pure_a + pure_b)
    # Lower recombination relative to pure patterns means sharper binding.
    binding_margin = pure_score - recomb_score
    return {
        "pure": pure_score,
        "recombination": recomb_score,
        "binding_margin": binding_margin,
        "branch_separation": separation,
        "two_branch_occupancy": occupancy,
    }


def main() -> None:
    rows = {}
    for mode in ("local", "global", "single"):
        vals = [run(seed, mode) for seed in range(N_SEEDS)]
        rows[mode] = {
            key: float(np.mean([v[key] for v in vals]))
            for key in vals[0]
        }
        rows[mode].update({
            key + "_sd": float(np.std([v[key] for v in vals]))
            for key in vals[0]
        })
    out = {"config": {"seeds": N_SEEDS, "dims": D, "branches": BRANCHES,
                       "steps": STEPS, "eta": ETA, "noise": NOISE},
           "results": rows}
    path = Path(__file__).with_suffix(".result.txt")
    path.write_text(json.dumps(out, indent=2) + "\n")
    for mode, result in rows.items():
        print(mode, " ".join(f"{k}={v:.6f}" for k, v in result.items()
                             if not k.endswith("_sd")))
        print(mode + "_sd", " ".join(f"{k}={v:.6f}" for k, v in result.items()
                                      if k.endswith("_sd")))


if __name__ == "__main__":
    main()
