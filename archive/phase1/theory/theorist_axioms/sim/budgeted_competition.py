"""Test a local covariance estimator with a hard cap on active edges.

CPU-only deterministic stream. Each edge uses only its endpoint events and
exponential traces. The target identity is used only for evaluation.
"""
from __future__ import annotations

import json
import random
import statistics
from pathlib import Path

N = 8
REGIME_LENGTH = 1500
T = N * REGIME_LENGTH
SEEDS = tuple(range(20261022, 20261042))
ALPHA = 0.02
THRESHOLDS = (0.05, 0.10, 0.15)
CAPACITIES = (None, 1, 2)  # None means no competition cap.
SUSTAINED_STEPS = 50


def choose_edges(scores: list[float], threshold: float, capacity: int | None) -> list[int]:
    eligible = [(score, i) for i, score in enumerate(scores) if score > threshold]
    eligible.sort(key=lambda pair: (-pair[0], pair[1]))
    if capacity is not None:
        eligible = eligible[:capacity]
    return [i for _, i in eligible]


def trial(seed: int, threshold: float, capacity: int | None, null_stream: bool) -> dict:
    rng = random.Random(seed)
    ema_x = 0.0
    ema_y = [0.0] * N
    ema_xy = [0.0] * N
    scores = [0.0] * N
    active_total = 0
    correct_total = 0
    steps_with_edge = 0
    recovery_delays: list[int | None] = []
    streak = 0
    found_recovery = False

    for t in range(T):
        regime = t // REGIME_LENGTH
        within_regime = t % REGIME_LENGTH
        if within_regime == 0:
            if t > 0 and not null_stream:
                recovery_delays.append(None if not found_recovery else recovery_delays.pop())
            streak = 0
            found_recovery = False

        target = None if null_stream else regime % N
        x = float(rng.random() < 0.5)
        y = [
            x if (target is not None and i == target)
            else float(rng.random() < 0.5)
            for i in range(N)
        ]

        # Select using only evidence available before this timestep.
        active = choose_edges(scores, threshold, capacity)
        active_total += len(active)
        if active:
            steps_with_edge += 1
        if target is not None:
            correct = target in active
            correct_total += int(correct)
            if not found_recovery:
                streak = streak + 1 if correct else 0
                if streak >= SUSTAINED_STEPS:
                    recovery_delays.append(within_regime - SUSTAINED_STEPS + 1)
                    found_recovery = True

        # Each candidate edge updates from its own pre/post event traces.
        ema_x += ALPHA * (x - ema_x)
        for i, event in enumerate(y):
            ema_y[i] += ALPHA * (event - ema_y[i])
            ema_xy[i] += ALPHA * (x * event - ema_xy[i])
            scores[i] = ema_xy[i] - ema_x * ema_y[i]

    if not null_stream:
        recovery_delays.append(None if not found_recovery else recovery_delays.pop())

    return {
        "active_edges_per_step": active_total / T,
        "edge_active_step_fraction": steps_with_edge / T,
        "true_edge_precision": correct_total / active_total if active_total else None,
        "target_coverage": correct_total / T if not null_stream else None,
        "null_false_edges_per_step": active_total / T if null_stream else None,
        "null_step_fraction_with_any_edge": steps_with_edge / T if null_stream else None,
        "recovery_delay_steps_to_50_sustained": recovery_delays if not null_stream else None,
    }


def mean(values: list[float | int | None]) -> float | None:
    numeric = [float(v) for v in values if v is not None]
    return statistics.mean(numeric) if numeric else None


def sd(values: list[float | int | None]) -> float | None:
    numeric = [float(v) for v in values if v is not None]
    return statistics.pstdev(numeric) if numeric else None


def main() -> dict:
    configurations = []
    for threshold in THRESHOLDS:
        for capacity in CAPACITIES:
            target_runs = [trial(seed, threshold, capacity, False) for seed in SEEDS]
            null_runs = [trial(seed, threshold, capacity, True) for seed in SEEDS]
            target_coverages = [r["target_coverage"] for r in target_runs]
            precisions = [r["true_edge_precision"] for r in target_runs]
            active_counts = [r["active_edges_per_step"] for r in target_runs]
            recoveries = [
                delay
                for r in target_runs
                for delay in r["recovery_delay_steps_to_50_sustained"]
            ]
            null_occupancies = [r["null_step_fraction_with_any_edge"] for r in null_runs]
            null_counts = [r["null_false_edges_per_step"] for r in null_runs]
            configurations.append({
                "threshold": threshold,
                "capacity": capacity if capacity is not None else "uncapped",
                "target_stream": {
                    "target_coverage_mean": mean(target_coverages),
                    "target_coverage_sd_across_seeds": sd(target_coverages),
                    "true_edge_precision_mean": mean(precisions),
                    "active_edges_per_step_mean": mean(active_counts),
                    "recovery_50_steps_mean": mean(recoveries),
                    "recovery_50_steps_sd": sd(recoveries),
                    "recovery_success_fraction": sum(v is not None for v in recoveries) / len(recoveries),
                    "recovery_windows": len(recoveries),
                },
                "null_stream": {
                    "steps_with_any_edge_fraction_mean": mean(null_occupancies),
                    "false_edges_per_step_mean": mean(null_counts),
                },
            })

    # Fixed-edge control, evaluated on the same balanced target schedule.
    fixed_coverage = sum((regime % N) == 0 for regime in range(N)) / N
    return {
        "experiment": "local covariance evidence with hard active-edge budget",
        "parameters": {
            "N": N,
            "regimes": N,
            "steps_per_regime": REGIME_LENGTH,
            "total_steps_per_seed": T,
            "seeds": list(SEEDS),
            "alpha": ALPHA,
            "thresholds": list(THRESHOLDS),
            "capacities": ["uncapped", 1, 2],
            "sustained_recovery_steps": SUSTAINED_STEPS,
        },
        "fixed_edge_control_target_coverage": fixed_coverage,
        "configurations": configurations,
        "definitions": {
            "score": "EMA(x*y) - EMA(x)*EMA(y), updated online after selecting edges",
            "active": "score > threshold; if capped, keep the largest scores up to capacity",
            "target_stream": "one target equals x in each regime; other targets are independent Bernoulli(0.5)",
            "null_stream": "all targets are independent Bernoulli(0.5)",
            "recovery": "first run of 50 consecutive pre-update selections containing current target, per regime",
        },
    }


if __name__ == "__main__":
    result = main()
    output = Path(__file__).with_name("budgeted_competition_result.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
