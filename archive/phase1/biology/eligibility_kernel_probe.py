#!/usr/bin/env python3
"""Test how a delayed, overlapping outcome affects action-edge identification."""
import json
from pathlib import Path

import numpy as np


def kernels():
    result = {"newest_only": np.array([1.0, 0.0, 0.0, 0.0]),
              "exp_tau_0.5": np.exp(-np.arange(4) / 0.5),
              "exp_tau_1": np.exp(-np.arange(4) / 1.0),
              "exp_tau_2": np.exp(-np.arange(4) / 2.0),
              "exp_tau_4": np.exp(-np.arange(4) / 4.0),
              "matched_box4": np.ones(4)}
    return {name: weights / weights.sum() for name, weights in result.items()}


def run(seed, weights, worlds=300, steps=240, switch=120, noise_sd=0.15,
        learning_rate=0.08):
    rng = np.random.default_rng(seed)
    estimates = np.zeros((worlds, 2))
    support1_wins = np.zeros(worlds, dtype=np.int64)
    scored = 0
    actions = rng.integers(0, 2, size=(worlds, steps))
    effects = np.empty((worlds, steps, 2))
    effects[:, :switch, :] = (0.6, -0.6)
    effects[:, switch:, :] = (-0.6, 0.6)
    # Each action contributes to four consecutive outcomes; only action order is observed.
    for t in range(steps):
        lo = max(0, t - len(weights) + 1)
        lags = np.arange(t - lo + 1)
        lag_weights = weights[:len(lags)]
        lag_weights = lag_weights / lag_weights.sum()
        history = actions[:, lo:t + 1][:, ::-1]
        features = np.stack([
            (history == action) @ lag_weights for action in range(2)
        ], axis=1)
        outcome = np.zeros(worlds)
        for lag, weight in zip(lags, lag_weights):
            issue_t = t - lag
            effect_by_world = np.take_along_axis(
                effects[:, issue_t, :], actions[:, issue_t, None], axis=1
            )[:, 0]
            outcome += weight * effect_by_world
        outcome += rng.normal(0, noise_sd, worlds)
        prediction = np.sum(features * estimates, axis=1)
        residual = outcome - prediction
        norm = np.sum(features ** 2, axis=1) + 1e-8
        estimates += learning_rate * features * (residual / norm)[:, None]
        if t >= switch + 8:
            support1_wins += estimates[:, 0] < estimates[:, 1]
            scored += 1
    return float(support1_wins.mean() / scored)


def main():
    all_kernels = kernels()
    rows = {name: run(9100, weights) for name, weights in all_kernels.items()}
    result = {
        "config": {"seed": 9100, "worlds": 300, "steps": 240, "switch": 120,
                   "true_consequence_kernel": "uniform over current and previous 3 issued actions",
                   "effect_pair": [0.6, -0.6], "effect_reversal": True,
                   "noise_sd": 0.15, "learning_rate": 0.08,
                   "action_policy": "independent random interventions"},
        "post_switch_correct_action_edge_fraction": rows,
        "limitation": "Synthetic four-step delayed mixture with abrupt effect reversal and independent actions; does not model neural eligibility, physiology, or pruning. Kernel match is supplied as a candidate, not learned."
    }
    path = Path(__file__).with_name("eligibility_kernel_probe_result.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
