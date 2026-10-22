"""A one-principle structural learner: posterior over predictive code paths.

The only selection quantity is codelength. A path consists of a sequence of
local architectures (no edge, or one of N possible sensor-to-sensor edges).
Each architecture segment uses a Jeffreys/Krichevsky-Trott Bayesian predictor.
Graph size uses a universal prior conditioned on the physical capacity, and
segment durations use p(d)=1/[d(d+1)] with survival S(d)=1/d. Thus
growth, pruning, predictor adaptation, and uncertainty over alternatives are
all posterior consequences of a single generative code; there are no hand-set
growth/pruning thresholds, probe windows, or learning rates.

This exact finite-neighborhood filter is a research reference, not yet a
bounded-memory implementation: the dynamic program retains prefix evidence
for all possible segment starts. The physical topology itself is capped at one
edge. This limitation is measured and recorded rather than hidden.
"""
from __future__ import annotations

import json
import math
import random
import statistics
from functools import lru_cache
from pathlib import Path

N = 2
REGIME_LENGTH = 300
REGIMES = 3
T = REGIME_LENGTH * REGIMES
SEEDS = tuple(range(20, 40))
SUSTAINED_STEPS = 25
LOG2 = math.log(2.0)
LOG2E = 1.0 / LOG2


@lru_cache(maxsize=None)
def kt_code_bits(n1: int, n0: int) -> float:
    """Jeffreys Beta(1/2,1/2) marginal code length for binary outcomes."""
    a = 0.5
    log_marginal = (
        math.lgamma(a + n1) + math.lgamma(a + n0)
        - math.lgamma(2 * a + n1 + n0)
        - (2 * math.lgamma(a) - math.lgamma(2 * a))
    )
    return -log_marginal * LOG2E


def logsumexp2(values: list[float]) -> float:
    if not values:
        return -math.inf
    top = max(values)
    if top == -math.inf:
        return top
    return top + math.log2(sum(2.0 ** (v - top) for v in values))


def architecture_prior() -> list[float]:
    """Universal graph-size code p(k)=1/[(k+1)(k+2)], conditioned on k<=1."""
    raw_empty = 1.0 / 2.0
    raw_one_edge = 1.0 / 6.0
    normalizer = raw_empty + raw_one_edge
    return [raw_empty / normalizer] + [raw_one_edge / normalizer / N] * N


def make_stream(seed: int, null_stream: bool) -> tuple[list[float], list[list[float]], list[int | None]]:
    rng = random.Random(seed)
    xs: list[float] = []
    ys = [[] for _ in range(N)]
    target_by_t: list[int | None] = []
    for t in range(T):
        x = float(rng.random() < 0.5)
        target = None if null_stream else (t // REGIME_LENGTH) % N
        xs.append(x)
        target_by_t.append(target)
        for i in range(N):
            y = x if target == i else float(rng.random() < 0.5)
            ys[i].append(y)
    return xs, ys, target_by_t


def prefix_counts(xs: list[float], ys: list[list[float]]) -> dict[str, list[list[int]]]:
    length = len(xs)
    marginal_ones = [[0] * (length + 1) for _ in range(N)]
    x1y1 = [[0] * (length + 1) for _ in range(N)]
    x1total = [0] * (length + 1)
    for t, x in enumerate(xs, start=1):
        x1total[t] = x1total[t - 1] + int(x == 1.0)
        for i in range(N):
            y = ys[i][t - 1]
            marginal_ones[i][t] = marginal_ones[i][t - 1] + int(y == 1.0)
            x1y1[i][t] = x1y1[i][t - 1] + int(x == 1.0 and y == 1.0)
    return {"marginal_ones": marginal_ones, "x1y1": x1y1, "x1total": [x1total]}


def segment_costs(xs: list[float], ys: list[list[float]]) -> list[list[list[float]]]:
    """Return code[s][t][state], where intervals are Python [s,t)."""
    length = len(xs)
    states = N + 1  # state 0 is no edge; i+1 is an edge to channel i
    prefix = prefix_counts(xs, ys)
    marginal_ones = prefix["marginal_ones"]
    x1y1 = prefix["x1y1"]
    x1total = prefix["x1total"][0]
    costs = [[[0.0] * states for _ in range(length + 1)] for _ in range(length)]

    for s in range(length):
        for t in range(s + 1, length + 1):
            d = t - s
            base_cost = 0.0
            marginals = [0.0] * N
            y_ones = [marginal_ones[i][t] - marginal_ones[i][s] for i in range(N)]
            for i in range(N):
                marginals[i] = kt_code_bits(y_ones[i], d - y_ones[i])
                base_cost += marginals[i]
            costs[s][t][0] = base_cost
            n_x1 = x1total[t] - x1total[s]
            n_x0 = d - n_x1
            for i in range(N):
                n_x1y1 = x1y1[i][t] - x1y1[i][s]
                n_x1y0 = n_x1 - n_x1y1
                n_x0y1 = y_ones[i] - n_x1y1
                n_x0y0 = n_x0 - n_x0y1
                conditional = kt_code_bits(n_x1y1, n_x1y0) + kt_code_bits(n_x0y1, n_x0y0)
                costs[s][t][i + 1] = base_cost - marginals[i] + conditional
    return costs


def filter_stream(seed: int, null_stream: bool) -> dict:
    xs, ys, targets = make_stream(seed, null_stream)
    costs = segment_costs(xs, ys)
    states = N + 1
    prior = architecture_prior()
    alpha = [[-math.inf] * states for _ in range(T + 1)]
    posterior_map: list[int] = []
    posterior_edge_mass: list[float] = []
    posterior_target_mass: list[float | None] = []
    prequential_bits: list[float] = []
    log_evidence = 0.0

    for t in range(1, T + 1):
        current_log_mass = [-math.inf] * states
        ended_log_mass = [-math.inf] * states
        for state in range(states):
            ongoing_terms = []
            ended_terms = []
            for start in range(t):
                duration = t - start
                segment_bits = costs[start][t][state]
                if start == 0:
                    transition_log = math.log2(prior[state])
                else:
                    transition_log = logsumexp2([
                        alpha[start][p]
                        + math.log2(prior[state] / (1.0 - prior[p]))
                        for p in range(states) if p != state
                    ])
                ongoing_terms.append(transition_log - math.log2(duration) - segment_bits)
                ended_terms.append(
                    transition_log - math.log2(duration * (duration + 1)) - segment_bits
                )
            current_log_mass[state] = logsumexp2(ongoing_terms)
            ended_log_mass[state] = logsumexp2(ended_terms)
        alpha[t] = ended_log_mass

        normalizer = logsumexp2(current_log_mass)
        if not math.isfinite(normalizer):
            raise ArithmeticError(f"non-finite architecture evidence at t={t}")
        p_state = [2.0 ** (v - normalizer) for v in current_log_mass]
        mode = max(range(states), key=p_state.__getitem__)
        posterior_map.append(mode)
        posterior_edge_mass.append(1.0 - p_state[0])
        target = targets[t - 1]
        posterior_target_mass.append(p_state[target + 1] if target is not None else None)
        prequential_bits.append(-(normalizer - log_evidence))
        log_evidence = normalizer

    regimes_hit = 0
    delays = []
    regime_delays = []
    for regime in range(REGIMES):
        start = regime * REGIME_LENGTH
        target = None if null_stream else regime % N
        if target is None:
            regime_delays.append(None)
            continue
        streak = 0
        found = None
        for t in range(start, start + REGIME_LENGTH):
            if posterior_map[t] == target + 1:
                streak += 1
                if streak >= SUSTAINED_STEPS:
                    found = t - start - SUSTAINED_STEPS + 1
                    break
            else:
                streak = 0
        if found is not None:
            regimes_hit += 1
            delays.append(found)
        regime_delays.append(found)

    changes = sum(a != b for a, b in zip(posterior_map, posterior_map[1:]))
    map_coverage = None
    mean_target_mass = None
    if not null_stream:
        map_coverage = sum(
            state == target + 1 for state, target in zip(posterior_map, targets)
        ) / T
        mean_target_mass = statistics.mean(
            p for p in posterior_target_mass if p is not None
        )

    return {
        "map_target_coverage": map_coverage,
        "posterior_target_mass_mean": mean_target_mass,
        "posterior_edge_mass_mean": statistics.mean(posterior_edge_mass),
        "map_edge_occupancy": sum(state != 0 for state in posterior_map) / T,
        "map_structural_changes": changes,
        "mean_predictive_code_bits_per_step": statistics.mean(prequential_bits),
        "recovery_success_fraction": regimes_hit / REGIMES if not null_stream else None,
        "recovery_delay_mean_steps": statistics.mean(delays) if delays else None,
        "regime_recovery_delays": regime_delays,
        "null_posterior_edge_mass_mean": statistics.mean(posterior_edge_mass) if null_stream else None,
        "null_map_edge_occupancy": sum(state != 0 for state in posterior_map) / T if null_stream else None,
        "max_edges": 1,
    }


def summarize(rows: list[dict], key: str) -> dict:
    values = [r[key] for r in rows if r[key] is not None]
    return {
        "mean": statistics.mean(values) if values else None,
        "sd_across_seeds": statistics.pstdev(values) if len(values) > 1 else 0.0 if values else None,
    }


def main() -> dict:
    target_rows = [filter_stream(seed, False) for seed in SEEDS]
    null_rows = [filter_stream(seed, True) for seed in SEEDS]
    keys = (
        "map_target_coverage", "posterior_target_mass_mean", "posterior_edge_mass_mean",
        "map_edge_occupancy", "map_structural_changes", "mean_predictive_code_bits_per_step",
        "recovery_success_fraction", "recovery_delay_mean_steps",
    )
    return {
        "experiment": "return-memory diagnostic for exact causal-code path filter on A-B-A recurrence",
        "parameters": {
            "N": N,
            "regimes": REGIMES,
            "steps_per_regime": REGIME_LENGTH,
            "total_steps_per_seed": T,
            "seeds": list(SEEDS),
            "target_schedule": [0, 1, 0],
            "physical_edge_capacity": 1,
            "predictive_code": "Jeffreys Beta(1/2,1/2) integrated Bernoulli code; conditional edge uses separate source=0 and source=1 contexts",
            "initial_architecture_prior": "universal graph-size code p(k)=1/[(k+1)(k+2)], conditioned on physical capacity k<=1; edge identity uniform within k",
            "edit_prior": "same code prior conditioned on a topology change; no hand-set edit rate",
            "duration_prior": "p(d)=1/[d(d+1)], survival P(D>=d)=1/d; no scale parameter",
        },
        "fixed_random_edge_target_coverage": 1 / N,
        "target_stream_summary": {key: summarize(target_rows, key) for key in keys},
        "null_stream_summary": {
            "posterior_edge_mass_mean": summarize(null_rows, "null_posterior_edge_mass_mean"),
            "map_edge_occupancy": summarize(null_rows, "null_map_edge_occupancy"),
            "mean_predictive_code_bits_per_step": summarize(null_rows, "mean_predictive_code_bits_per_step"),
        },
        "target_runs": target_rows,
        "null_runs": null_rows,
        "limitations": [
            "The exact reference filter stores O(T*N) prefix counts and O(T^2*N) segment costs; bounded-memory approximation is not yet implemented.",
            "One local neighborhood is enumerated exactly; scaling to many coupled local neighborhoods is untested.",
            "A posterior distribution over architectures is measured; a physically sampled coherent architecture path is not yet implemented.",
        ],
    }


if __name__ == "__main__":
    result = main()
    output = Path(__file__).with_name("causal_code_return_test_result.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if not k.endswith("_runs")}, indent=2, sort_keys=True))
