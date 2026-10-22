"""Independent, exact reimplementation of H002's N=4 code-path filter.

The stream comes from engine.stream.SourceNeighborhoodStream. This reference
replication intentionally keeps all prefix sufficient statistics and all
possible run starts; it is not a bounded-memory learner.
"""

from __future__ import annotations

import argparse
import json
import math
import resource
import statistics
import time
from functools import lru_cache
from pathlib import Path

from stream import SourceNeighborhoodStream


CHANNELS = 4
REGIMES = 4
STEPS_PER_REGIME = 300
TOTAL_STEPS = REGIMES * STEPS_PER_REGIME
SUSTAINED_STEPS = 25
SEED_START = 20
REPLICATES = 20


@lru_cache(maxsize=100000)
def _kt_bits(ones: int, zeros: int) -> float:
    """Jeffreys Beta-Bernoulli marginal code in bits."""
    a = 0.5
    log_marginal = (
        math.lgamma(a + ones) + math.lgamma(a + zeros)
        - math.lgamma(2 * a + ones + zeros)
        - (2 * math.lgamma(a) - math.lgamma(2 * a))
    )
    return -log_marginal / math.log(2.0)


def _logsumexp2(values: list[float]) -> float:
    if not values:
        return -math.inf
    peak = max(values)
    if peak == -math.inf:
        return peak
    return peak + math.log2(sum(2.0 ** (value - peak) for value in values))


def _architecture_prior() -> list[float]:
    # Universal graph-size code p(k)=1/((k+1)(k+2)), conditioned on k <= 1.
    p_empty_raw = 1.0 / 2.0
    p_single_raw = 1.0 / 6.0
    normalizer = p_empty_raw + p_single_raw
    return [p_empty_raw / normalizer] + [
        p_single_raw / normalizer / CHANNELS for _ in range(CHANNELS)
    ]


def _collect(seed: int, null_stream: bool):
    stream = SourceNeighborhoodStream(
        seed=seed,
        steps_per_regime=STEPS_PER_REGIME,
        target_count=CHANNELS,
        regime_count=REGIMES,
        event_rates=(0.5,),
        null_stream=null_stream,
        target_sequence=tuple(range(CHANNELS)),
    )
    xs = []
    ys = [[] for _ in range(CHANNELS)]
    targets = []
    for _ in range(TOTAL_STEPS):
        source, target_events, metadata = stream.sample()
        xs.append(int(source[0]))
        for i, value in enumerate(target_events):
            ys[i].append(int(value))
        targets.append(None if null_stream else metadata["regime"])
    return xs, ys, targets


def _prefix_counts(xs: list[int], ys: list[list[int]]):
    n = len(xs)
    x_ones = [0] * (n + 1)
    y_ones = [[0] * (n + 1) for _ in range(CHANNELS)]
    xy_ones = [[0] * (n + 1) for _ in range(CHANNELS)]
    for t, x in enumerate(xs, start=1):
        x_ones[t] = x_ones[t - 1] + x
        for i in range(CHANNELS):
            y = ys[i][t - 1]
            y_ones[i][t] = y_ones[i][t - 1] + y
            xy_ones[i][t] = xy_ones[i][t - 1] + x * y
    return x_ones, y_ones, xy_ones


def _segment_code(start: int, end: int, prefix):
    x_ones, y_ones, xy_ones = prefix
    duration = end - start
    x1 = x_ones[end] - x_ones[start]
    x0 = duration - x1
    marginal_bits = []
    y_counts = []
    for i in range(CHANNELS):
        y1 = y_ones[i][end] - y_ones[i][start]
        y_counts.append(y1)
        marginal_bits.append(_kt_bits(y1, duration - y1))
    base = sum(marginal_bits)
    costs = [base]
    for i in range(CHANNELS):
        x1y1 = xy_ones[i][end] - xy_ones[i][start]
        x1y0 = x1 - x1y1
        x0y1 = y_counts[i] - x1y1
        x0y0 = x0 - x0y1
        conditional = _kt_bits(x1y1, x1y0) + _kt_bits(x0y1, x0y0)
        costs.append(base - marginal_bits[i] + conditional)
    return costs


def _filter(seed: int, null_stream: bool) -> dict:
    xs, ys, targets = _collect(seed, null_stream)
    prefix = _prefix_counts(xs, ys)
    prior = _architecture_prior()
    state_count = CHANNELS + 1

    # ended[t][state] is the joint evidence of paths ending a segment at t.
    ended = [[-math.inf] * state_count for _ in range(TOTAL_STEPS + 1)]
    transition_logs = [[-math.inf] * state_count for _ in range(TOTAL_STEPS)]
    for state in range(state_count):
        transition_logs[0][state] = math.log2(prior[state])

    current_modes = []
    edge_mass = []
    target_mass = []
    code_bits = []
    log_evidence = 0.0

    for end in range(1, TOTAL_STEPS + 1):
        if end > 1:
            for state in range(state_count):
                alternatives = [
                    ended[end - 1][previous]
                    + math.log2(prior[state] / (1.0 - prior[previous]))
                    for previous in range(state_count) if previous != state
                ]
                transition_logs[end - 1][state] = _logsumexp2(alternatives)

        continuation_terms = [[] for _ in range(state_count)]
        completed_terms = [[] for _ in range(state_count)]
        for start in range(end):
            duration = end - start
            segment_costs = _segment_code(start, end, prefix)
            log_survival = -math.log2(duration)
            log_duration_mass = -math.log2(duration * (duration + 1))
            for state in range(state_count):
                base_log_mass = transition_logs[start][state] - segment_costs[state]
                continuation_terms[state].append(base_log_mass + log_survival)
                completed_terms[state].append(base_log_mass + log_duration_mass)

        current = [_logsumexp2(terms) for terms in continuation_terms]
        ended[end] = [_logsumexp2(terms) for terms in completed_terms]
        normalizer = _logsumexp2(current)
        posterior = [2.0 ** (value - normalizer) for value in current]
        mode = max(range(state_count), key=posterior.__getitem__)
        current_modes.append(mode)
        edge_mass.append(1.0 - posterior[0])
        active_target = targets[end - 1]
        target_mass.append(posterior[active_target + 1] if active_target is not None else None)
        code_bits.append(-(normalizer - log_evidence))
        log_evidence = normalizer

    recovery_delays = []
    regime_successes = 0
    for regime in range(REGIMES):
        target = None if null_stream else regime % CHANNELS
        if target is None:
            continue
        first = regime * STEPS_PER_REGIME
        last = first + STEPS_PER_REGIME
        streak = 0
        delay = None
        for t in range(first, last):
            if current_modes[t] == target + 1:
                streak += 1
                if streak >= SUSTAINED_STEPS:
                    delay = t - first - SUSTAINED_STEPS + 1
                    break
            else:
                streak = 0
        if delay is not None:
            regime_successes += 1
            recovery_delays.append(delay)

    result = {
        "seed": seed,
        "condition": "independent_null" if null_stream else "rotating_target",
        "map_target_coverage": (
            sum(mode == target + 1 for mode, target in zip(current_modes, targets)) / TOTAL_STEPS
            if not null_stream else None
        ),
        "posterior_target_mass_mean": statistics.mean(
            value for value in target_mass if value is not None
        ) if not null_stream else None,
        "posterior_edge_mass_mean": statistics.mean(edge_mass),
        "map_edge_occupancy": sum(mode != 0 for mode in current_modes) / TOTAL_STEPS,
        "map_structural_changes": sum(
            left != right for left, right in zip(current_modes, current_modes[1:])
        ),
        "mean_predictive_code_bits_per_step": statistics.mean(code_bits),
        "recovery_success_fraction": regime_successes / REGIMES if not null_stream else None,
        "recovery_delay_mean_steps": statistics.mean(recovery_delays) if recovery_delays else None,
        "null_posterior_edge_mass_mean": statistics.mean(edge_mass) if null_stream else None,
        "null_map_edge_occupancy": (
            sum(mode != 0 for mode in current_modes) / TOTAL_STEPS if null_stream else None
        ),
        # This cap is imposed by the enumerated architecture state space.
        "max_edges": 1,
        "algorithm_state_items": (
            len(xs) + sum(map(len, ys)) + len(targets)
            + sum(map(len, prefix))
            + sum(len(row) for group in prefix[1:] for row in group)
            + sum(len(row) for row in ended)
            + sum(len(row) for row in transition_logs)
            + len(current_modes) + len(edge_mass) + len(target_mass) + len(code_bits)
        ),
    }
    return result


def _mean_sd(rows: list[dict], key: str):
    values = [row[key] for row in rows if row[key] is not None]
    return {
        "mean": statistics.mean(values) if values else None,
        "sd": statistics.stdev(values) if len(values) > 1 else (0.0 if values else None),
    }


def run(seed_start=SEED_START, replicates=REPLICATES, output="experiments/h002-reference-replication"):
    start_time = time.perf_counter()
    target_rows = [_filter(seed, False) for seed in range(seed_start, seed_start + replicates)]
    null_rows = [_filter(seed, True) for seed in range(seed_start, seed_start + replicates)]
    metric_keys = (
        "map_target_coverage", "posterior_target_mass_mean", "posterior_edge_mass_mean",
        "map_edge_occupancy", "map_structural_changes", "mean_predictive_code_bits_per_step",
        "recovery_success_fraction", "recovery_delay_mean_steps", "algorithm_state_items",
    )
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = {
        "hypothesis_id": "H002",
        "experiment": "independent exact code-path filter replication using engine.stream",
        "implementation": "fresh implementation of Jeffreys integrated segment codes and the registered graph-size/edit/duration prior",
        "config": {
            "N": CHANNELS,
            "regimes": REGIMES,
            "steps_per_regime": STEPS_PER_REGIME,
            "steps_per_seed": TOTAL_STEPS,
            "seed_start": seed_start,
            "replicates": replicates,
            "seeds": list(range(seed_start, seed_start + replicates)),
            "null_seeds": list(range(seed_start, seed_start + replicates)),
            "edge_capacity": 1,
            "edge_capacity_semantics": "hard cap imposed by finite architecture state space",
            "reward": False,
            "labels_passed_to_filter": False,
            "backpropagation": False,
        },
        "target_stream_summary": {key: _mean_sd(target_rows, key) for key in metric_keys},
        "null_stream_summary": {
            "posterior_edge_mass_mean": _mean_sd(null_rows, "null_posterior_edge_mass_mean"),
            "map_edge_occupancy": _mean_sd(null_rows, "null_map_edge_occupancy"),
            "mean_predictive_code_bits_per_step": _mean_sd(
                null_rows, "mean_predictive_code_bits_per_step"
            ),
            "algorithm_state_items": _mean_sd(null_rows, "algorithm_state_items"),
        },
        "target_runs": target_rows,
        "null_runs": null_rows,
        "resources": {
            "wall_seconds": time.perf_counter() - start_time,
            "peak_rss_kib": int(rss),
            "parallel_processes": 1,
            "cpu_affinity_expected": "0-2",
        },
        "limitations": [
            "The exact filter retains O(T*N) local prefix counts and O(T*|A|) path evidence; state grows with stream length.",
            "The one-edge cap comes from the enumerated architecture space and is not emergent.",
            "Posterior-mode decoding is measured; no coherent sampled physical graph or action exploration is tested.",
        ],
    }
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=SEED_START)
    parser.add_argument("--replicates", type=int, default=REPLICATES)
    parser.add_argument("--output", default="experiments/h002-reference-replication")
    args = parser.parse_args()
    result = run(args.seed_start, args.replicates, args.output)
    print(json.dumps({
        "result": str(Path(args.output) / "result.json"),
        "target_stream_summary": result["target_stream_summary"],
        "null_stream_summary": result["null_stream_summary"],
        "resources": result["resources"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
