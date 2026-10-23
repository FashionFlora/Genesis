"""Finite-memory particle approximation to the local predictive-code posterior.

Each particle is one local graph path with at most one edge. It carries the
Beta sufficient statistics for its current architecture segment. A source/edge
path is proposed from the same graph-size code and universal duration prior
as `causal_code_filter.py`; sensory likelihood reweights particles and
resampling removes poor codes. There is no external reward, gradient, probe
timer, or utility threshold. Particle count is the explicit memory budget.

This model intentionally resets a segment's predictive statistics after a
topology edit, matching the exact reference. It does not yet test retrieval of
old edge parameters when an earlier regime returns.
"""
from __future__ import annotations

import copy
import json
import math
import random
import statistics
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


def empty_particle(state: int) -> dict:
    return {
        "state": state,
        "age": 0,
        "marginal_ones": [0] * N,
        "marginal_total": [0] * N,
        "conditional_ones": [0, 0],
        "conditional_total": [0, 0],
    }


def predictive_log2(particle: dict, x: float, ys: list[float]) -> float:
    state = particle["state"]
    total = 0.0
    for i, y in enumerate(ys):
        if state == i + 1:
            context = int(x)
            p1 = (particle["conditional_ones"][context] + 0.5) / (
                particle["conditional_total"][context] + 1.0
            )
        else:
            p1 = (particle["marginal_ones"][i] + 0.5) / (
                particle["marginal_total"][i] + 1.0
            )
        total += math.log2(p1 if y == 1.0 else 1.0 - p1)
    return total


def update_particle(particle: dict, x: float, ys: list[float]) -> None:
    state = particle["state"]
    for i, y in enumerate(ys):
        if state != i + 1:
            particle["marginal_ones"][i] += int(y == 1.0)
            particle["marginal_total"][i] += 1
    if state != 0:
        context = int(x)
        target = state - 1
        particle["conditional_ones"][context] += int(ys[target] == 1.0)
        particle["conditional_total"][context] += 1


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

    for x, ys, target in rows:
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
        for index, particle in enumerate(particles):
            update_particle(particle, x, ys)
            particle["age"] += 1
            hazard = 1.0 / (particle["age"] + 1.0)
            if rng.random() < hazard:
                new_state = draw_state(rng, prior, excluded=particle["state"])
                particle = empty_particle(new_state)
            particles[index] = particle

        counts = [0] * (N + 1)
        for particle in particles:
            counts[particle["state"]] += 1
        structural_map.append(max(range(N + 1), key=counts.__getitem__))

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
        "memory_bytes_estimate": PARTICLES * (2 * N + 8) * 8,
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
        "experiment": "fixed-memory posterior particle approximation to causal-code topology filter",
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
        "memory_bytes_estimate": PARTICLES * (2 * N + 8) * 8,
    }


if __name__ == "__main__":
    result = main()
    output = Path(__file__).with_name("causal_code_particles_result.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if not k.endswith("_runs")}, indent=2, sort_keys=True))
