"""One-state coactivity support for reward-free sensory streams.

Each source owns a finite integer support budget.  A positive support count is
the edge, its predictive strength, and its persistence state.  No separate
edge estimator or regime signal is maintained.
"""

import numpy as np


class SupportAllocationPredictor:
    """Locally reallocate integer support from coactivity differences."""

    def __init__(self, input_dim=8, output_dim=8, seed=0, budget=4,
                 eta=0.03, noise=0.0, resolution=32):
        self.input_dim = int(input_dim)
        self.output_dim = int(output_dim)
        self.budget = int(budget)
        self.eta = float(eta)
        self.noise = float(noise)
        self.resolution = int(resolution)
        if self.input_dim <= 0 or self.output_dim <= 0 or self.budget < 1 or self.resolution < 1:
            raise ValueError("dimensions and budget must be positive")
        if self.eta < 0.0 or self.noise < 0.0:
            raise ValueError("eta and noise must be non-negative")
        self.rng = np.random.default_rng(int(seed) ^ 0xC0A17)
        self.budget_units = self.budget * self.resolution
        self.support = np.zeros((self.input_dim, self.output_dim), dtype=np.int32)
        self.growth_events = 0
        self.pruning_events = 0
        self.samples = 0
        self.work_units = 0

    @staticmethod
    def _project(raw, budget):
        """Nearest non-negative integer vector under a sum budget."""
        q = np.maximum(0, np.rint(raw)).astype(np.int16)
        while int(q.sum()) > budget:
            candidates = np.flatnonzero(q > 0)
            costs = 2.0 * (q[candidates] - raw[candidates]) - 1.0
            q[candidates[int(np.argmax(costs))]] -= 1
        while int(q.sum()) < budget:
            candidates = np.flatnonzero(2.0 * q + 1.0 - 2.0 * raw < 0.0)
            if len(candidates) == 0:
                break
            costs = 2.0 * q[candidates] + 1.0 - 2.0 * raw[candidates]
            q[candidates[int(np.argmin(costs))]] += 1
        return q

    def predict(self, observation):
        x = np.asarray(observation, dtype=np.float64).reshape(-1)
        if x.shape != (self.input_dim,):
            raise ValueError(f"expected observation shape {(self.input_dim,)}, got {x.shape}")
        # One strongest support per output prevents weak competitors from
        # inventing a second predictor; the selected k is still the only edge
        # state and supplies both strength and persistence.
        prediction = np.full(self.output_dim, 0.5, dtype=np.float64)
        for target in range(self.output_dim):
            source = int(np.argmax(self.support[:, target]))
            strength = self.support[source, target] / float(self.budget_units)
            prediction[target] += strength * (x[source] - 0.5)
        self.work_units += self.input_dim * self.output_dim + self.output_dim
        return np.clip(prediction, 0.0, 1.0)

    def observe(self, observation, next_observation):
        x = np.asarray(observation, dtype=np.float64).reshape(-1)
        y = np.asarray(next_observation, dtype=np.float64).reshape(-1)
        if x.shape != (self.input_dim,) or y.shape != (self.output_dim,):
            raise ValueError("observation dimensions do not match predictor")
        coactivity = np.outer(x, y)
        signal = coactivity - coactivity.mean(axis=1, keepdims=True)
        raw = self.support.astype(np.float64) + self.eta * signal * self.budget_units
        if self.noise:
            raw += self.noise * self.budget_units * self.rng.standard_normal(raw.shape)
        old = self.support.copy()
        for source in range(self.input_dim):
            self.support[source] = self._project(raw[source], self.budget_units)
        self.growth_events += int(np.count_nonzero((old == 0) & (self.support > 0)))
        self.pruning_events += int(np.count_nonzero((old > 0) & (self.support == 0)))
        self.samples += 1
        self.work_units += self.input_dim * self.output_dim * 4

    def structure_metrics(self):
        source_mass = (self.support.sum(axis=1) / self.resolution).tolist()
        active = int(np.count_nonzero(self.support))
        state_bytes = int(self.support.nbytes + 8 * self.input_dim)
        return {
            "unit_count": self.input_dim + self.output_dim + active,
            "connection_count": active,
            "active_edge_units": active,
            "support_mass": float(self.support.sum() / self.resolution),
            "support_resolution": self.resolution,
            "source_support_mass": source_mass,
            "growth_events": self.growth_events,
            "pruning_events": self.pruning_events,
            "work_units": self.work_units,
            "estimated_state_bytes": state_bytes,
        }
