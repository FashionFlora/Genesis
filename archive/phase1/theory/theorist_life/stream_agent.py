"""Resource-flow cell ecology for engine.stream_bench.SensorStream.

Every cell carries one directed sensory edge (input source -> output target),
a local Beta-Bernoulli predictor, and resource mass. The same mass-flow law as
the small ecology simulator drives fission and depletion. The stream interface
exposes only observations and next observations; no regime metadata or reward
is read.
"""
from __future__ import annotations

import random

import numpy as np


class _Cell:
    __slots__ = ("source", "target", "positive", "seen", "mass")

    def __init__(self, source, target, mass=1.0, positive=None, seen=None):
        self.source = int(source)
        self.target = int(target)
        self.positive = [0, 0] if positive is None else positive
        self.seen = [0, 0] if seen is None else seen
        self.mass = float(mass)

    def q(self, x):
        return (self.positive[x] + 1.0) / (self.seen[x] + 2.0)


class ResourceFlowPredictor:
    """Dynamic population predictor using only local error and resource flow."""

    def __init__(self, input_dim=8, output_dim=8, seed=0,
                 maintenance=0.10, error_cost=0.25, mutation_rate=0.05):
        self.input_dim = int(input_dim)
        self.output_dim = int(output_dim)
        if self.input_dim <= 0 or self.output_dim <= 0:
            raise ValueError("input_dim and output_dim must be positive")
        self.maintenance = float(maintenance)
        self.error_cost = float(error_cost)
        self.mutation_rate = float(mutation_rate)
        self.rng = random.Random(int(seed) ^ 0xC011)
        self.resource_rng = random.Random(int(seed) ^ 0xF10A)
        self.initial_population = self.input_dim * self.output_dim
        # Each target niche receives the same finite expected substrate flow;
        # source variants competing for that target share it locally.
        self.substrate_inflow_per_target = self.input_dim * (
            self.maintenance + self.error_cost * 0.25)
        self.substrate_inflow = self.output_dim * self.substrate_inflow_per_target
        self.cells = [
            _Cell(source, target)
            for source in range(self.input_dim)
            for target in range(self.output_dim)
        ]
        self.rng.shuffle(self.cells)
        self.growth_events = 0
        self.pruning_events = 0
        self.mutation_events = 0
        self.work_units = 0
        self._last_observation = None
        self._last_prediction = None

    @staticmethod
    def _poisson(rng, rate):
        if rate <= 0.0:
            return 0
        product = 1.0
        limit = np.exp(-rate)
        count = 0
        while product > limit:
            product *= rng.random()
            count += 1
        return count - 1

    def predict(self, observation):
        x = np.asarray(observation, dtype=np.float64)
        if x.shape != (self.input_dim,):
            raise ValueError(f"expected observation shape {(self.input_dim,)}, got {x.shape}")
        weighted = np.zeros(self.output_dim, dtype=np.float64)
        mass = np.zeros(self.output_dim, dtype=np.float64)
        for cell in self.cells:
            weighted[cell.target] += cell.mass * cell.q(int(x[cell.source]))
            mass[cell.target] += cell.mass
        prediction = np.full(self.output_dim, 0.5, dtype=np.float64)
        occupied = mass > 0.0
        prediction[occupied] = weighted[occupied] / mass[occupied]
        self._last_observation = x.copy()
        self._last_prediction = prediction.copy()
        self.work_units += len(self.cells) * 4 + self.output_dim
        return prediction

    def observe(self, observation, next_observation):
        x = np.asarray(observation, dtype=np.float64)
        y = np.asarray(next_observation, dtype=np.float64)
        if x.shape != (self.input_dim,) or y.shape != (self.output_dim,):
            raise ValueError("observation dimensions do not match configured interface")
        if self._last_prediction is None:
            raise RuntimeError("observe must follow predict")

        errors = []
        for cell in self.cells:
            context = int(x[cell.source])
            target = int(y[cell.target])
            prediction = cell.q(context)
            errors.append((prediction - target) ** 2)
            cell.seen[context] += 1
            cell.positive[context] += target
        # Finite stochastic substrate inflow is shared within each output
        # niche. Competing source edges for the same target draw from one local
        # pool; the same flow law applies independently at each target.
        intake = [0] * len(self.cells)
        total_packets = 0
        for target in range(self.output_dim):
            indices = [i for i, cell in enumerate(self.cells)
                       if cell.target == target]
            if not indices:
                continue
            packets = self._poisson(self.resource_rng,
                                    self.substrate_inflow_per_target)
            total_packets += packets
            for _ in range(packets):
                intake[self.resource_rng.choice(indices)] += 1

        survivors = []
        for i, cell in enumerate(self.cells):
            flux = intake[i] - self.maintenance - self.error_cost * errors[i]
            mass = cell.mass + flux
            if mass <= 0.0:
                self.pruning_events += 1
                continue
            cell.mass = mass
            lineage = [cell]
            index = 0
            while index < len(lineage):
                parent = lineage[index]
                if parent.mass >= 2.0:
                    daughter_mass = parent.mass / 2.0
                    parent.mass = daughter_mass
                    source, target = parent.source, parent.target
                    positive, seen = parent.positive.copy(), parent.seen.copy()
                    if self.rng.random() < self.mutation_rate:
                        edge = self.rng.randrange(self.input_dim * self.output_dim - 1)
                        old_edge = source * self.output_dim + target
                        if edge >= old_edge:
                            edge += 1
                        source, target = divmod(edge, self.output_dim)
                        positive, seen = [0, 0], [0, 0]
                        self.mutation_events += 1
                    lineage.append(_Cell(source, target, daughter_mass,
                                         positive, seen))
                    self.growth_events += 1
                index += 1
            survivors.extend(lineage)

        self.cells = survivors
        self.work_units += len(errors) * 8 + len(self.cells) * 5 + total_packets
        self._last_observation = None
        self._last_prediction = None

    def structure_metrics(self):
        unique_edges = {(cell.source, cell.target) for cell in self.cells}
        return {
            "unit_count": self.input_dim + self.output_dim + len(self.cells),
            "connection_count": len(self.cells),
            "active_edge_types": len(unique_edges),
            "growth_events": self.growth_events,
            "pruning_events": self.pruning_events,
            "mutation_events": self.mutation_events,
            "work_units": self.work_units,
            "estimated_state_bytes": 64 * len(self.cells) + 8 * (self.input_dim + self.output_dim),
        }
