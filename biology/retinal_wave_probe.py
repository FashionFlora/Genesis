#!/usr/bin/env python3
"""Probe: can patterned spontaneous waves teach a topographic map?

This is a mechanistic toy, not an organism result.  Every condition has the
same total input activity.  Only the spatial correlation of the activity is
changed.  A winner and its local output neighbours update weights using only
their pre/post activity (competitive Hebbian/SOM update).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass

import numpy as np


N = 32
TRAIN = 3000
EVAL = 32
SEEDS = 100


def circ_dist(a: np.ndarray | int, b: np.ndarray | int, n: int = N) -> np.ndarray:
    d = np.abs(np.asarray(a) - np.asarray(b))
    return np.minimum(d, n - d)


def wave(center: int, sigma: float = 1.5) -> np.ndarray:
    d = circ_dist(np.arange(N), center)
    x = np.exp(-0.5 * (d / sigma) ** 2)
    return x / x.sum()


def shuffled_spikes(rng: np.random.Generator, k: int = 5) -> np.ndarray:
    x = np.zeros(N)
    x[rng.choice(N, size=k, replace=False)] = 1.0 / k
    return x


def train(seed: int, condition: str, radius: float = 2.0) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    w = rng.random((N, N))
    w /= w.sum(axis=1, keepdims=True)
    out_pos = np.arange(N)
    for step in range(TRAIN):
        center = int(rng.integers(N))
        if condition == "wave":
            x = wave(center)
        elif condition == "scrambled":
            x = shuffled_spikes(rng)
        elif condition == "global":
            x = np.full(N, 1.0 / N)
        else:
            raise ValueError(condition)
        winner = int(np.argmax(w @ x))
        d = circ_dist(out_pos, winner)
        h = np.exp(-0.5 * (d / radius) ** 2) if radius > 0 else (d == 0)
        eta = 0.32 * (1.0 - 0.7 * step / TRAIN)
        w += eta * h[:, None] * (x[None, :] - w)
        w = np.maximum(w, 1e-12)
        w /= w.sum(axis=1, keepdims=True)

    # Test with clean locations. Preferred input position is the local map.
    prefs = np.asarray([np.argmax(w @ wave(c)) for c in range(N)])
    neighbour_step = float(np.mean(circ_dist(prefs, np.roll(prefs, -1))))
    coverage = float(len(np.unique(prefs)) / N)
    smoothness = float(1.0 - neighbour_step / (N / 2.0))
    map_score = coverage * smoothness
    return map_score, coverage, neighbour_step


def main() -> None:
    result: dict[str, dict[str, float]] = {}
    for condition in ("wave", "scrambled", "global"):
        vals = np.asarray([train(seed, condition) for seed in range(SEEDS)])
        result[condition] = {
            "map_score": float(vals[:, 0].mean()),
            "coverage": float(vals[:, 1].mean()),
            "neighbor_step": float(vals[:, 2].mean()),
            "map_score_sd": float(vals[:, 0].std(ddof=1)),
            "coverage_sd": float(vals[:, 1].std(ddof=1)),
            "neighbor_step_sd": float(vals[:, 2].std(ddof=1)),
        }
    # Ablate the local output neighbourhood while retaining patterned waves.
    vals = np.asarray([train(seed, "wave", radius=0.0) for seed in range(SEEDS)])
    result["wave_no_neighborhood"] = {
        "map_score": float(vals[:, 0].mean()),
        "coverage": float(vals[:, 1].mean()),
        "neighbor_step": float(vals[:, 2].mean()),
        "map_score_sd": float(vals[:, 0].std(ddof=1)),
        "coverage_sd": float(vals[:, 1].std(ddof=1)),
        "neighbor_step_sd": float(vals[:, 2].std(ddof=1)),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
