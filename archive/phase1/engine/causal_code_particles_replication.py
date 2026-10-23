"""Independent particle-filter replication of the bounded H002 reference."""

from __future__ import annotations

import argparse
import json
import math
import random
import resource
import statistics
import sys
import time
from pathlib import Path

from stream import SourceNeighborhoodStream


N = 4
REGIMES = 4
STEPS_PER_REGIME = 300
T = REGIMES * STEPS_PER_REGIME
PARTICLE_COUNT = 128
SUSTAINED_STEPS = 25
SEED_START = 20
REPLICATES = 20


class Particle:
    __slots__ = (
        "state", "age", "marginal_ones", "marginal_total",
        "conditional_ones", "conditional_total",
    )

    def __init__(self, state):
        self.state = int(state)
        self.age = 0
        self.marginal_ones = [0] * N
        self.marginal_total = [0] * N
        self.conditional_ones = [0, 0]
        self.conditional_total = [0, 0]

    def clone(self):
        result = Particle(self.state)
        result.age = self.age
        result.marginal_ones = self.marginal_ones.copy()
        result.marginal_total = self.marginal_total.copy()
        result.conditional_ones = self.conditional_ones.copy()
        result.conditional_total = self.conditional_total.copy()
        return result

    def probability(self, target, source_value):
        if self.state == target + 1:
            return (self.conditional_ones[source_value] + 0.5) / (
                self.conditional_total[source_value] + 1.0
            )
        return (self.marginal_ones[target] + 0.5) / (
            self.marginal_total[target] + 1.0
        )

    def log_likelihood(self, source_value, targets):
        score = 0.0
        for target, value in enumerate(targets):
            probability = self.probability(target, source_value)
            score += math.log2(probability if value else 1.0 - probability)
        return score

    def update(self, source_value, targets):
        for target, value in enumerate(targets):
            if self.state != target + 1:
                self.marginal_ones[target] += int(value)
                self.marginal_total[target] += 1
        if self.state != 0:
            target = self.state - 1
            self.conditional_ones[source_value] += int(targets[target])
            self.conditional_total[source_value] += 1


def _prior():
    empty_raw = 1.0 / 2.0
    edge_raw = 1.0 / 6.0
    normalizer = empty_raw + edge_raw
    return [empty_raw / normalizer] + [edge_raw / normalizer / N] * N


def _draw_state(rng, probabilities, excluded=None):
    choices = [state for state in range(len(probabilities)) if state != excluded]
    total = sum(probabilities[state] for state in choices)
    remaining = rng.random() * total
    for state in choices:
        remaining -= probabilities[state]
        if remaining <= 0.0:
            return state
    return choices[-1]


def _resample(particles, log_weights, rng):
    largest = max(log_weights)
    scaled = [2.0 ** (value - largest) for value in log_weights]
    denominator = sum(scaled)
    cumulative = []
    running = 0.0
    for weight in scaled:
        running += weight / denominator
        cumulative.append(running)
    offset = rng.random() / len(particles)
    selected = []
    index = 0
    for slot in range(len(particles)):
        position = offset + slot / len(particles)
        while position > cumulative[index] and index < len(particles) - 1:
            index += 1
        selected.append(particles[index].clone())
    return selected


def _stream(seed, null_stream):
    world = SourceNeighborhoodStream(
        seed=seed,
        steps_per_regime=STEPS_PER_REGIME,
        target_count=N,
        regime_count=REGIMES,
        event_rates=(0.5,),
        null_stream=null_stream,
        target_sequence=tuple(range(N)),
    )
    rows = []
    for _ in range(T):
        source, target_values, metadata = world.sample()
        rows.append((int(source[0]), [int(value) for value in target_values],
                     None if null_stream else int(metadata["regime"])))
    return rows


def _state_bytes(particles):
    size = sys.getsizeof(particles)
    for particle in particles:
        size += sys.getsizeof(particle)
        for values in (particle.marginal_ones, particle.marginal_total,
                       particle.conditional_ones, particle.conditional_total):
            size += sys.getsizeof(values)
            size += sum(sys.getsizeof(value) for value in values)
        size += sys.getsizeof(particle.age) + sys.getsizeof(particle.state)
    return size


def _run(seed, null_stream):
    rows = _stream(seed, null_stream)
    probabilities = _prior()
    rng = random.Random(seed ^ 0xC0DEC0DE)
    particles = [Particle(_draw_state(rng, probabilities)) for _ in range(PARTICLE_COUNT)]
    posterior_modes = []
    structural_modes = []
    edge_masses = []
    target_masses = []
    prequential_bits = []
    online_brier = []
    online_target_brier = []

    for source_value, targets, hidden_target in rows:
        log_weights = [particle.log_likelihood(source_value, targets)
                       for particle in particles]
        maximum = max(log_weights)
        log_normalizer = maximum + math.log2(
            sum(2.0 ** (value - maximum) for value in log_weights)
        )
        weights = [2.0 ** (value - log_normalizer) for value in log_weights]

        predictions = []
        for target in range(N):
            predictions.append(sum(
                weight * particle.probability(target, source_value)
                for weight, particle in zip(weights, particles)
            ))
        errors = [(prediction - value) ** 2 for prediction, value in zip(predictions, targets)]
        online_brier.append(sum(errors) / N)
        if hidden_target is not None:
            online_target_brier.append(errors[hidden_target])

        posterior_by_state = [sum(
            weight for weight, particle in zip(weights, particles)
            if particle.state == state
        ) for state in range(N + 1)]
        posterior_modes.append(max(range(N + 1), key=posterior_by_state.__getitem__))
        edge_masses.append(1.0 - posterior_by_state[0])
        target_masses.append(
            posterior_by_state[hidden_target + 1] if hidden_target is not None else None
        )
        prequential_bits.append(-log_normalizer + math.log2(PARTICLE_COUNT))

        particles = _resample(particles, log_weights, rng)
        for index, particle in enumerate(particles):
            particle.update(source_value, targets)
            particle.age += 1
            hazard = 1.0 / (particle.age + 1.0)
            if rng.random() < hazard:
                particles[index] = Particle(
                    _draw_state(rng, probabilities, excluded=particle.state)
                )

        sampled_counts = [0] * (N + 1)
        for particle in particles:
            sampled_counts[particle.state] += 1
        structural_modes.append(max(range(N + 1), key=sampled_counts.__getitem__))

    def _summarize_modes(modes):
        coverage = None
        recovery_delays = []
        successes = 0
        if not null_stream:
            coverage = sum(
                mode == target + 1 for mode, (_, _, target) in zip(modes, rows)
            ) / T
            for regime in range(REGIMES):
                target = regime % N
                start = regime * STEPS_PER_REGIME
                streak = 0
                delay = None
                for step in range(start, start + STEPS_PER_REGIME):
                    if modes[step] == target + 1:
                        streak += 1
                        if streak >= SUSTAINED_STEPS:
                            delay = step - start - SUSTAINED_STEPS + 1
                            break
                    else:
                        streak = 0
                if delay is not None:
                    successes += 1
                    recovery_delays.append(delay)
        return {
            "coverage": coverage,
            "edge_occupancy": sum(mode != 0 for mode in modes) / T,
            "recovery_success_fraction": successes / REGIMES if not null_stream else None,
            "recovery_delay_mean_steps": (
                statistics.mean(recovery_delays) if recovery_delays else None
            ),
            "structural_changes": sum(
                left != right for left, right in zip(modes, modes[1:])
            ),
        }

    posterior_metrics = _summarize_modes(posterior_modes)
    structural_metrics = _summarize_modes(structural_modes)
    target_edge_mass = [value for value in target_masses if value is not None]
    return {
        "seed": seed,
        "condition": "independent_null" if null_stream else "rotating_target",
        "posterior_map_target_coverage": posterior_metrics["coverage"],
        "posterior_map_edge_occupancy": posterior_metrics["edge_occupancy"],
        "posterior_map_recovery_success_fraction": posterior_metrics["recovery_success_fraction"],
        "posterior_map_recovery_delay_mean_steps": posterior_metrics["recovery_delay_mean_steps"],
        "posterior_map_structural_changes": posterior_metrics["structural_changes"],
        "sampled_structure_map_target_coverage": structural_metrics["coverage"],
        "sampled_structure_map_edge_occupancy": structural_metrics["edge_occupancy"],
        "sampled_structure_map_recovery_success_fraction": structural_metrics["recovery_success_fraction"],
        "sampled_structure_map_recovery_delay_mean_steps": structural_metrics["recovery_delay_mean_steps"],
        "sampled_structure_map_changes": structural_metrics["structural_changes"],
        "posterior_target_mass_mean": statistics.mean(target_edge_mass) if target_edge_mass else None,
        "posterior_edge_mass_mean": statistics.mean(edge_masses),
        "null_posterior_map_edge_occupancy": (
            posterior_metrics["edge_occupancy"] if null_stream else None
        ),
        "null_sampled_structure_map_edge_occupancy": (
            structural_metrics["edge_occupancy"] if null_stream else None
        ),
        "mean_predictive_code_bits_per_step": statistics.mean(prequential_bits),
        "mean_online_brier": statistics.mean(online_brier),
        "mean_target_brier": statistics.mean(online_target_brier) if online_target_brier else None,
        "max_edges_per_particle": 1,
        "particle_count": PARTICLE_COUNT,
        "particle_state_bytes_estimate": _state_bytes(particles),
        "numeric_state_bytes_estimate": PARTICLE_COUNT * (2 * N + 8) * 8,
    }


def _mean_sd(rows, field):
    values = [row[field] for row in rows if row[field] is not None]
    return {
        "mean": statistics.mean(values) if values else None,
        "sd": statistics.stdev(values) if len(values) > 1 else (0.0 if values else None),
    }


def run(seed_start=SEED_START, replicates=REPLICATES,
        output="experiments/h002-particles-replication"):
    start_time = time.perf_counter()
    seeds = list(range(seed_start, seed_start + replicates))
    target_runs = [_run(seed, False) for seed in seeds]
    null_runs = [_run(seed, True) for seed in seeds]
    fields = (
        "posterior_map_target_coverage", "posterior_map_edge_occupancy",
        "posterior_map_recovery_success_fraction", "posterior_map_recovery_delay_mean_steps",
        "posterior_map_structural_changes", "sampled_structure_map_target_coverage",
        "sampled_structure_map_edge_occupancy", "sampled_structure_map_recovery_success_fraction",
        "sampled_structure_map_recovery_delay_mean_steps", "sampled_structure_map_changes",
        "posterior_target_mass_mean", "posterior_edge_mass_mean",
        "mean_predictive_code_bits_per_step", "mean_online_brier", "mean_target_brier",
        "particle_state_bytes_estimate", "numeric_state_bytes_estimate",
    )
    rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = {
        "hypothesis_id": "H002",
        "experiment": "independent bounded SMC implementation on fresh registered seeds",
        "config": {
            "N": N,
            "regimes": REGIMES,
            "steps_per_regime": STEPS_PER_REGIME,
            "steps_per_seed": T,
            "seeds": seeds,
            "replicates": replicates,
            "particles": PARTICLE_COUNT,
            "resampling": "systematic each observation",
            "duration_hazard_after_update": "1/(age+1)",
            "graph_prior": "p(k)=1/((k+1)(k+2)) conditioned on k<=1; changes conditioned on a change",
            "predictor": "Jeffreys Beta(1/2,1/2) segment code, segment statistics reset on graph edit",
            "reward": False,
            "regime_label_available_to_filter": False,
            "backpropagation": False,
        },
        "target_stream_summary": {field: _mean_sd(target_runs, field) for field in fields},
        "null_stream_summary": {
            field: _mean_sd(null_runs, field) for field in (
                "null_posterior_map_edge_occupancy",
                "null_sampled_structure_map_edge_occupancy",
                "posterior_edge_mass_mean", "mean_predictive_code_bits_per_step",
                "mean_online_brier", "particle_state_bytes_estimate",
                "numeric_state_bytes_estimate",
            )
        },
        "target_runs": target_runs,
        "null_runs": null_runs,
        "resources": {
            "wall_seconds": time.perf_counter() - start_time,
            "peak_rss_kib": int(rss_kib),
            "parallel_processes": 1,
            "expected_cpu_affinity": "0-2",
        },
        "limitations": [
            "A fixed particle count bounds particle-state memory, but particle resampling can lose posterior modes.",
            "The one-edge cap is imposed by each particle's finite architecture state space.",
            "The model resets predictive counts after an edit and does not test memory restoration on returning regimes.",
            "No sampled graph controls an action, so behavioral exploration is untested.",
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
    parser.add_argument("--output", default="experiments/h002-particles-replication")
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
