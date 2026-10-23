"""Fixed-population particle approximation to the local predictive-code posterior.

Each particle carries one graph path with at most one edge. After likelihood
resampling, a Gibbs move resamples the current segment's architecture from its
integrated sensory code and transition prior. The move uses sufficient counts
for every candidate local architecture during the current segment; this is a
posterior-preserving rejuvenation step, not an independent structural rule.
Segment statistics reset after a topology transition, matching the exact
reference. This test still does not model stored parameters for a dormant edge.
"""
from __future__ import annotations

import copy
import json
import math
import random
import statistics
import sys
from pathlib import Path

N = 4
REGIME_LENGTH = 300
REGIMES = 4
T = REGIME_LENGTH * REGIMES
SEEDS = tuple(range(20, 40))
PARTICLES = 128
SUSTAINED_STEPS = 25


def architecture_prior() -> list[float]:
    raw = [1 / 2, 1 / 6]
    normalizer = sum(raw)
    return [raw[0] / normalizer] + [raw[1] / normalizer / N] * N


def draw_state(rng: random.Random, probabilities: list[float], excluded: int | None = None) -> int:
    choices = [i for i in range(len(probabilities)) if i != excluded]
    total = sum(probabilities[i] for i in choices)
    draw = rng.random() * total
    for state in choices:
        draw -= probabilities[state]
        if draw <= 0.0:
            return state
    return choices[-1]


def empty_particle(state: int, previous_state: int | None = None) -> dict:
    return {
        "state": state,
        "previous_state": previous_state,
        "age": 0.0,
        "marginal_ones": [0.0] * N,
        "marginal_total": [0.0] * N,
        "conditional_ones": [[0.0, 0.0] for _ in range(N)],
        "conditional_total": [[0.0, 0.0] for _ in range(N)],
    }


def predictive_log2(particle: dict, x: float, ys: list[float]) -> float:
    state = particle["state"]
    total = 0.0
    for i, y in enumerate(ys):
        if state == i + 1:
            context = int(x)
            p1 = (particle["conditional_ones"][i][context] + 0.5) / (
                particle["conditional_total"][i][context] + 1.0
            )
        else:
            p1 = (particle["marginal_ones"][i] + 0.5) / (
                particle["marginal_total"][i] + 1.0
            )
        total += math.log2(p1 if y == 1.0 else 1.0 - p1)
    return total


def update_particle(particle: dict, x: float, ys: list[float]) -> None:
    for i, y in enumerate(ys):
        particle["marginal_ones"][i] += float(y == 1.0)
        particle["marginal_total"][i] += 1.0
        context = int(x)
        particle["conditional_ones"][i][context] += float(y == 1.0)
        particle["conditional_total"][i][context] += 1.0


def kt_code_bits(n1: float, n0: float) -> float:
    """Jeffreys Beta(1/2,1/2) integrated code length for binary data."""
    a = 0.5
    log_marginal = (
        math.lgamma(a + n1) + math.lgamma(a + n0)
        - math.lgamma(2 * a + n1 + n0)
        - (2 * math.lgamma(a) - math.lgamma(2 * a))
    )
    return -log_marginal / math.log(2.0)


def segment_code_bits(particle: dict, state: int) -> float:
    """Integrated code of the current segment under one architecture state."""
    total = 0.0
    for i in range(N):
        if state == i + 1:
            for context in range(2):
                ones = particle["conditional_ones"][i][context]
                count = particle["conditional_total"][i][context]
                total += kt_code_bits(ones, count - ones)
        else:
            ones = particle["marginal_ones"][i]
            count = particle["marginal_total"][i]
            total += kt_code_bits(ones, count - ones)
    return total


def resample_segment_state(particle: dict, prior: list[float], rng: random.Random) -> None:
    """Gibbs-sample this segment's architecture conditional on its coded data."""
    previous = particle["previous_state"]
    states = [state for state in range(N + 1) if state != previous]
    log_masses = [math.log2(prior[state]) - segment_code_bits(particle, state)
                  for state in states]
    maximum = max(log_masses)
    weights = [2.0 ** (value - maximum) for value in log_masses]
    total = sum(weights)
    draw = rng.random() * total
    for state, weight in zip(states, weights):
        draw -= weight
        if draw <= 0.0:
            particle["state"] = state
            return
    particle["state"] = states[-1]


def deep_size(value, seen: set[int] | None = None) -> int:
    """Approximate retained Python payload size for one particle population."""
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(deep_size(k, seen) + deep_size(v, seen) for k, v in value.items())
    elif isinstance(value, (list, tuple)):
        size += sum(deep_size(item, seen) for item in value)
    return size


def systematic_resample(particles: list[dict], log_weights: list[float], rng: random.Random) -> list[dict]:
    maximum = max(log_weights)
    weights = [2.0 ** (value - maximum) for value in log_weights]
    total = sum(weights)
    cumulative = []
    run = 0.0
    for weight in weights:
        run += weight / total
        cumulative.append(run)
    count = len(particles)
    offset = rng.random() / count
    result = []
    index = 0
    for slot in range(count):
        location = offset + slot / count
        while location > cumulative[index] and index < count - 1:
            index += 1
        result.append(copy.deepcopy(particles[index]))
    return result


def generate(seed: int, null_stream: bool) -> tuple[list[tuple[float, list[float], int | None]], random.Random]:
    env_rng = random.Random(seed)
    rows = []
    for t in range(T):
        x = float(env_rng.random() < 0.5)
        target = None if null_stream else (t // REGIME_LENGTH) % N
        ys = [
            x if target == i else float(env_rng.random() < 0.5)
            for i in range(N)
        ]
        rows.append((x, ys, target))
    return rows, random.Random(seed ^ 0xC0DEC0DE)


def run(seed: int, null_stream: bool) -> dict:
    rows, rng = generate(seed, null_stream)
    prior = architecture_prior()
    particles = [empty_particle(draw_state(rng, prior)) for _ in range(PARTICLES)]
    posterior_map: list[int] = []
    structural_map: list[int] = []
    edge_mass: list[float] = []
    target_mass: list[float | None] = []
    code_bits: list[float] = []

    for t, (x, ys, target) in enumerate(rows):
        log_weights = [predictive_log2(p, x, ys) for p in particles]
        normalizer = max(log_weights) + math.log2(sum(2.0 ** (v - max(log_weights)) for v in log_weights))
        code_bits.append(-normalizer + math.log2(PARTICLES))

        weights = [2.0 ** (v - normalizer) for v in log_weights]
        masses = [sum(w for w, p in zip(weights, particles) if p["state"] == state)
                  for state in range(N + 1)]
        posterior_map.append(max(range(N + 1), key=masses.__getitem__))
        edge_mass.append(1.0 - masses[0])
        target_mass.append(masses[target + 1] if target is not None else None)

        particles = systematic_resample(particles, log_weights, rng)
        for particle in particles:
            update_particle(particle, x, ys)
            particle["age"] += 1.0
            resample_segment_state(particle, prior, rng)

        counts = [0] * (N + 1)
        for particle in particles:
            counts[particle["state"]] += 1
        structural_map.append(max(range(N + 1), key=counts.__getitem__))

        # A topology transition generates the next segment, after recording
        # the posterior structure for the observation just consumed.
        if t + 1 < T:
            for index, particle in enumerate(particles):
                hazard = 1.0 / (particle["age"] + 1.0)
                if rng.random() < hazard:
                    previous_state = particle["state"]
                    new_state = draw_state(rng, prior, excluded=previous_state)
                    particles[index] = empty_particle(new_state, previous_state)

    delays = []
    regimes_hit = 0
    if not null_stream:
        for regime in range(REGIMES):
            start = regime * REGIME_LENGTH
            target = regime % N
            streak = 0
            found = None
            for t in range(start, start + REGIME_LENGTH):
                if structural_map[t] == target + 1:
                    streak += 1
                    if streak >= SUSTAINED_STEPS:
                        found = t - start - SUSTAINED_STEPS + 1
                        break
                else:
                    streak = 0
            if found is not None:
                regimes_hit += 1
                delays.append(found)

    changes = sum(a != b for a, b in zip(structural_map, structural_map[1:]))
    return {
        "seed": seed,
        "stream": "null" if null_stream else "rotating_target",
        "map_target_coverage": (
            sum(state == target + 1 for state, (_, _, target) in zip(structural_map, rows)) / T
            if not null_stream else None
        ),
        "posterior_target_mass_mean": (
            statistics.mean(p for p in target_mass if p is not None) if not null_stream else None
        ),
        "posterior_edge_mass_mean": statistics.mean(edge_mass),
        "map_edge_occupancy": sum(state != 0 for state in structural_map) / T,
        "posterior_map_coverage": (
            sum(state == target + 1 for state, target in zip(posterior_map, [r[2] for r in rows])) / T
            if not null_stream else None
        ),
        "map_structural_changes": changes,
        "mean_predictive_code_bits_per_step": statistics.mean(code_bits),
        "recovery_success_fraction": regimes_hit / REGIMES if not null_stream else None,
        "recovery_delay_mean_steps": statistics.mean(delays) if delays else None,
        "null_map_edge_occupancy": sum(state != 0 for state in structural_map) / T if null_stream else None,
        "max_edges_per_particle": 1,
        "particle_state_bytes": deep_size(particles),
    }


def mean_sd(rows: list[dict], key: str) -> dict:
    values = [row[key] for row in rows if row[key] is not None]
    return {
        "mean": statistics.mean(values) if values else None,
        "sd_across_seeds": statistics.pstdev(values) if len(values) > 1 else 0.0 if values else None,
    }


def main() -> dict:
    target_rows = [run(seed, False) for seed in SEEDS]
    null_rows = [run(seed, True) for seed in SEEDS]
    target_keys = (
        "map_target_coverage", "posterior_target_mass_mean", "posterior_edge_mass_mean",
        "map_edge_occupancy", "posterior_map_coverage", "map_structural_changes",
        "mean_predictive_code_bits_per_step", "recovery_success_fraction",
        "recovery_delay_mean_steps",
    )
    return {
        "experiment": "fixed-population particle filter with posterior-preserving segment Gibbs moves",
        "parameters": {
            "N": N,
            "regimes": REGIMES,
            "steps_per_regime": REGIME_LENGTH,
            "total_steps_per_seed": T,
            "seeds": list(SEEDS),
            "particle_budget": PARTICLES,
            "max_edges_per_particle": 1,
            "architecture_prior": "universal graph-size code p(k)=1/[(k+1)(k+2)] conditioned on k<=1",
            "edit_transition": "same graph prior conditioned on changing state",
            "duration_prior": "p(d)=1/[d(d+1)], hazard after age d is 1/(d+1)",
            "posterior_move": "Gibbs update of current segment architecture from transition prior times integrated data code",
            "predictor": "Jeffreys Beta(1/2,1/2) prequential code; segment statistics reset on graph edit",
            "resampling": "systematic each observation; no ESS threshold",
        },
        "fixed_random_edge_target_coverage": 1 / N,
        "target_stream_summary": {key: mean_sd(target_rows, key) for key in target_keys},
        "null_stream_summary": {
            "posterior_edge_mass_mean": mean_sd(null_rows, "posterior_edge_mass_mean"),
            "map_edge_occupancy": mean_sd(null_rows, "null_map_edge_occupancy"),
            "mean_predictive_code_bits_per_step": mean_sd(null_rows, "mean_predictive_code_bits_per_step"),
        },
        "target_runs": target_rows,
        "null_runs": null_rows,
        "particle_state_bytes_max": max(row["particle_state_bytes"] for row in target_rows + null_rows),
    }


if __name__ == "__main__":
    result = main()
    output = Path(__file__).with_name("causal_code_particles_move_result.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if not k.endswith("_runs")}, indent=2, sort_keys=True))
