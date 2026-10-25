#!/usr/bin/env python3
"""Probe a developmental switch from correlation-potentiation to depression.

The rule has no labels or reward.  A winner receives the signed correlation
update; row norms are softly bounded so the comparison is about the sign,
not runaway weight growth.
"""
import numpy as np


def run(seed, mode, n_in=32, n_units=32, steps=2400, early=1200):
    rng = np.random.default_rng(seed)
    W = np.clip(0.15 + 0.04 * rng.standard_normal((n_units, n_in)), 0.01, 0.35)
    positions = np.arange(n_in)
    seq = rng.integers(0, n_in, size=steps)
    # A random walk gives local correlations during development, then a
    # shifted distribution tests whether the mature rule can refine it.
    seq[: early] = np.cumsum(rng.choice([-1, 0, 1], size=early)) % n_in
    seq[early:] = (seq[early:] + n_in // 4) % n_in
    for t, p in enumerate(seq):
        d = np.minimum((positions - p) % n_in, (p - positions) % n_in)
        x = np.exp(-(d * d) / (2 * 2.2 * 2.2))
        x += 0.03 * rng.random(n_in)
        a = W @ x + 0.01 * rng.standard_normal(n_units)
        k = int(np.argmax(a))
        # Positive correlation builds the initial scaffold; negative
        # correlation later removes the currently used contacts.
        if mode == "switch":
            sign = 1.0 if t < early else -1.0
        elif mode == "ltp":
            sign = 1.0
        elif mode == "ltd":
            sign = -1.0
        else:
            sign = 0.0
        if sign:
            eta = 0.018 if t < early else 0.010
            W[k] += sign * eta * (x - 0.25 * W[k])
            W[k] = np.clip(W[k], 0.001, 1.0)
        if (t + 1) % 32 == 0:
            # Local homeostasis prevents the sign comparison becoming a
            # comparison of total gain.
            norms = np.linalg.norm(W, axis=1, keepdims=True) + 1e-8
            W *= np.clip(2.0 / norms, 0.85, 1.15)

    # Evaluate without plasticity on the two regimes.
    def eval_positions(offset):
        hits = []
        responses = []
        for p in range(n_in):
            q = (p + offset) % n_in
            d = np.minimum((positions - q) % n_in, (q - positions) % n_in)
            x = np.exp(-(d * d) / (2 * 2.2 * 2.2))
            z = W @ x
            hits.append(int(np.argmax(z)))
            responses.append(z)
        R = np.asarray(responses)
        coverage = len(set(hits)) / n_units
        # Smoothness: nearby inputs should not jump between unrelated units.
        step = np.mean(np.minimum(np.abs(np.diff(hits)), n_units - np.abs(np.diff(hits))))
        # Selectivity: winner margin over the mean non-winner response.
        margins = []
        for z in R:
            order = np.sort(z)
            margins.append((order[-1] - order[-2]) / (abs(order[-1]) + 1e-8))
        return coverage, float(step), float(np.mean(margins)), R

    old = eval_positions(0)
    new = eval_positions(n_in // 4)
    # Cross-regime response overlap, lower means better refinement.
    corr = np.corrcoef(old[3].ravel(), new[3].ravel())[0, 1]
    return (*old[:3], *new[:3], float(corr), float(np.mean(W)))


def main():
    modes = ("switch", "ltp", "ltd", "none")
    for mode in modes:
        vals = np.asarray([run(s, mode) for s in range(100)], dtype=float)
        print(
            mode,
            "old_cov/old_step/old_margin/new_cov/new_step/new_margin/cross_corr/mean_w",
            *(f"{x:.6f}" for x in vals.mean(axis=0)),
        )
    # A switch should be a timing principle, not a hand-picked midpoint.
    for early in (600, 1200, 1800):
        vals = np.asarray([run(s, "switch", early=early) for s in range(100)], dtype=float)
        print(
            "switch_early", early,
            "old_cov/new_cov/cross_corr/mean_w",
            f"{vals[:, 0].mean():.6f}", f"{vals[:, 3].mean():.6f}",
            f"{vals[:, 6].mean():.6f}", f"{vals[:, 7].mean():.6f}",
        )


if __name__ == "__main__":
    main()
