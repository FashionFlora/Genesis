#!/usr/bin/env python3
"""Robustness and diversity test for contact-weighted Notch competition.

This keeps the original local/global update rule but varies cluster size,
surface bias, and noisy contact interfaces.  Each geometry is replayed with
multiple molecular-noise seeds, so winner diversity is not confused with a
single random draw of cell areas.
"""
from __future__ import annotations

import math
import random
from collections import Counter
from statistics import mean, pstdev


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, x))))


def run(geometry_seed: int, noise_seed: int, mode: str, side: int,
        area_sd: float, surface_noise: float, rounds: int = 80):
    geo = random.Random(geometry_seed)
    rng = random.Random(noise_seed)
    n = side * side
    area = [1.0 + area_sd * geo.gauss(0.0, 1.0) for _ in range(n)]
    bias = [0.55 * (a - 1.0) if mode != "no_bias" else 0.0 for a in area]
    xy = [(i % side, i // side) for i in range(n)]
    contact = [[0.0] * n for _ in range(n)]
    for i, (x0, y0) in enumerate(xy):
        for j, (x1, y1) in enumerate(xy):
            if i == j:
                continue
            d = abs(x0 - x1) + abs(y0 - y1)
            if mode == "global":
                contact[i][j] = 1.0
            elif d == 1 and mode in ("local", "uniform"):
                base = 1.0 if mode == "uniform" else 1.0 + 0.5 * (area[i] + area[j] - 2.0)
                contact[i][j] = max(0.0, base * (1.0 + surface_noise * geo.gauss(0.0, 1.0)))
    score = [b + 0.02 * rng.gauss(0.0, 1.0) for b in bias]
    for _ in range(rounds):
        drive = [sigmoid(4.0 * score[i]) for i in range(n)]
        total = [sum(contact[i][j] * drive[j] for j in range(n)) for i in range(n)]
        for i in range(n):
            score[i] += 0.06 * (bias[i] + 1.2 * drive[i] - 0.9 * total[i])
        score = [s + 0.01 * rng.gauss(0.0, 1.0) for s in score]
    order = sorted(range(n), key=lambda i: score[i], reverse=True)
    margin = score[order[0]] - score[order[1]]
    winner = order[0]
    ranks = sorted(range(n), key=lambda i: area[i])
    return float(margin > 0.22), margin, ranks.index(winner) / max(1, n - 1), winner


def summarize(mode: str, side: int, area_sd: float, surface_noise: float):
    rows = [run(g, 1000 * g + r, mode, side, area_sd, surface_noise)
            for g in range(20) for r in range(20)]
    winners = Counter(r[3] for r in rows)
    probs = [count / len(rows) for count in winners.values()]
    entropy = -sum(p * math.log(p) for p in probs)
    effective_winners = math.exp(entropy)
    return (mean(r[0] for r in rows), mean(r[1] for r in rows),
            mean(r[2] for r in rows), effective_winners / (side * side),
            pstdev(r[1] for r in rows))


def main() -> None:
    print("mode side area_sd surface_noise uniqueness margin winner_area_rank effective_winner_fraction margin_sd")
    for side in (2, 3, 4):
        for area_sd, surface_noise in ((0.04, 0.0), (0.08, 0.15), (0.16, 0.30)):
            for mode in ("local", "uniform", "global", "no_bias"):
                values = summarize(mode, side, area_sd, surface_noise)
                print(mode, side, f"{area_sd:.2f} {surface_noise:.2f}",
                      *(f"{x:.6f}" for x in values))


if __name__ == "__main__":
    main()
