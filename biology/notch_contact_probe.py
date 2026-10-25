#!/usr/bin/env python3
"""Toy probe of geometry-weighted lateral inhibition.

The probe asks whether a small pre-existing cell-size bias plus local contact
weights makes one developmental winner more reproducible than uniform or
global inhibition at the same update budget.  It is deliberately not an
organism judge.
"""
from __future__ import annotations

import math
import random
from statistics import mean, pstdev


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, x))))


def run(seed: int, mode: str, n: int = 9, rounds: int = 80) -> tuple[float, float, float]:
    rng = random.Random(seed)
    # A compact 3x3 proneural cluster; area variation is the pre-feedback bias.
    area = [1.0 + 0.08 * rng.gauss(0.0, 1.0) for _ in range(n)]
    bias = [0.55 * (a - 1.0) if mode != "no_bias" else 0.0 for a in area]
    xy = [(i % 3, i // 3) for i in range(n)]
    contact = [[0.0] * n for _ in range(n)]
    for i, (x0, y0) in enumerate(xy):
        for j, (x1, y1) in enumerate(xy):
            if i == j:
                continue
            d = abs(x0 - x1) + abs(y0 - y1)
            if mode == "global":
                contact[i][j] = 1.0
            elif d == 1 and mode == "local":
                # Larger shared interfaces transmit more inhibition.
                contact[i][j] = 1.0 + 0.5 * (area[i] + area[j] - 2.0)
            elif d == 1 and mode == "uniform":
                contact[i][j] = 1.0
    score = [b + 0.02 * rng.gauss(0.0, 1.0) for b in bias]
    for _ in range(rounds):
        drive = [sigmoid(4.0 * score[i]) for i in range(n)]
        total = [sum(contact[i][j] * drive[j] for j in range(n)) for i in range(n)]
        # Equal total update budget across modes; contact only redistributes it.
        for i in range(n):
            score[i] += 0.06 * (bias[i] + 1.2 * drive[i] - 0.9 * total[i])
        score = [s + 0.01 * rng.gauss(0.0, 1.0) for s in score]
    order = sorted(range(n), key=lambda i: score[i], reverse=True)
    margin = score[order[0]] - score[order[1]]
    winner = order[0]
    # A single precursor is useful only if the winner is clearly separated.
    unique = float(margin > 0.22)
    area_rank = sorted(range(n), key=lambda i: area[i])
    winner_rank = area_rank.index(winner) / (n - 1)
    return unique, margin, winner_rank


def main() -> None:
    seeds = range(100)
    modes = ("local", "uniform", "global", "no_bias")
    # Repeat each developmental cluster with fresh molecular noise to measure
    # whether the same pre-existing geometry selects the same cell.
    for mode in modes:
        rows = [run(s, mode) for s in seeds]
        print(
            f"{mode} uniqueness={mean(r[0] for r in rows):.6f} "
            f"margin={mean(r[1] for r in rows):.6f} "
            f"winner_area_rank={mean(r[2] for r in rows):.6f} "
            f"margin_sd={pstdev(r[1] for r in rows):.6f}"
        )


if __name__ == "__main__":
    main()
