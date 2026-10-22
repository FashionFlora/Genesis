"""Test whether slow local edge plasticity trades adaptation for stability.

CPU-only, deterministic experiment. No external data or packages required.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

SEED = 20261022
N = 8
T = 12000
SWITCH = 6000
ETA = 0.008
DECAY = 0.0005
THRESHOLD = 0.50


def run(seed: int = SEED) -> dict:
    rng = random.Random(seed)
    # A source emits a binary event. The identity of the correlated target
    # changes halfway through; all event rates remain stationary.
    weights = [0.0] * N
    ema_x = 0.0
    ema_y = [0.0] * N
    alpha = 0.02
    absolute_error = [0.0, 0.0]
    detected = [0] * 2
    edge_count = [0, 0]
    correct_edges = [0, 0]
    pre_switch_weight = post_switch_weight = 0.0
    post_switch_samples = 0

    for t in range(T):
        epoch = 0 if t < SWITCH else 1
        target = epoch  # target 0 in first regime, target 1 in second
        x = 1.0 if rng.random() < 0.5 else 0.0
        ys = [1.0 if (x if i == target else rng.random() < 0.5) else 0.0 for i in range(N)]
        # Local coincidence deviation from chance, estimated only from local
        # pre/post traces. A signed Hebbian term alone would drift under noise.
        for i, y in enumerate(ys):
            ema_y[i] += alpha * (y - ema_y[i])
            coincidence = x * y - (ema_x * ema_y[i])
            weights[i] = max(0.0, weights[i] + ETA * coincidence - DECAY * weights[i])
        ema_x += alpha * (x - ema_x)
        active = [i for i, w in enumerate(weights) if w >= THRESHOLD]
        edge_count[epoch] += len(active)
        correct_edges[epoch] += sum(1 for i in active if i == target)
        # Track response on samples where source is active; a learned edge
        # predicts target's event above its 0.5 baseline.
        for i, y in enumerate(ys):
            pred = 1.0 if weights[i] >= THRESHOLD and x else 0.5
            absolute_error[epoch] += abs(pred - y)
        if t < SWITCH:
            pre_switch_weight += weights[0]
        else:
            post_switch_weight += weights[1]
            post_switch_samples += 1
            if t >= SWITCH + 100 and weights[1] >= THRESHOLD:
                detected[1] += 1

    return {
        "seed": seed,
        "parameters": {"N": N, "T": T, "switch": SWITCH, "eta": ETA,
                       "decay": DECAY, "edge_threshold": THRESHOLD},
        "mean_weight_target0_before_switch": pre_switch_weight / SWITCH,
        "mean_weight_target1_after_switch": post_switch_weight / post_switch_samples,
        "active_edge_fraction_regime0": edge_count[0] / (SWITCH * N),
        "active_edge_fraction_regime1": edge_count[1] / ((T - SWITCH) * N),
        "true_edge_precision_regime0": correct_edges[0] / edge_count[0] if edge_count[0] else None,
        "true_edge_precision_regime1": correct_edges[1] / edge_count[1] if edge_count[1] else None,
        "regime1_threshold_occupancy_after_100_steps": detected[1] / (T - SWITCH - 100),
        "mae_regime0": absolute_error[0] / (SWITCH * N),
        "mae_regime1": absolute_error[1] / ((T - SWITCH) * N),
    }


if __name__ == "__main__":
    result = run()
    out = Path(__file__).with_name("local_plasticity_result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
