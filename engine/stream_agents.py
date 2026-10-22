"""Reference agents for the reward-free stream benchmark.

The common contract is ``predict(observation) -> prediction`` followed by
``observe(observation, next_observation)``. The target is the next sensory
observation, not a reward or task label. Regime metadata is never supplied.
"""

import numpy as np
import random


class MeanPredictor:
    """Online per-channel mean predictor with no learned connections."""

    def __init__(self, input_dim=8, output_dim=8, seed=0):
        del seed
        self.input_dim = int(input_dim)
        self.output_dim = int(output_dim)
        self.mean = np.full(self.output_dim, 0.5, dtype=np.float64)
        self.count = 0
        self.work_units = 0

    def predict(self, observation):
        self.work_units += self.output_dim
        return self.mean.copy()

    def observe(self, observation, next_observation):
        del observation
        target = np.asarray(next_observation, dtype=np.float64)
        if self.count == 0:
            self.mean[:] = target
        else:
            self.mean += (target - self.mean) / (self.count + 1)
        self.count += 1
        self.work_units += self.output_dim * 2

    def structure_metrics(self):
        return {
            "unit_count": self.output_dim,
            "connection_count": 0,
            "growth_events": 0,
            "pruning_events": 0,
            "work_units": self.work_units,
            "estimated_state_bytes": int(self.mean.nbytes + 8),
        }


class PersistencePredictor:
    """Fixed identity predictor, a minimal temporal baseline."""

    def __init__(self, input_dim=8, output_dim=8, seed=0):
        del seed
        if input_dim != output_dim:
            raise ValueError("persistence baseline requires equal input/output dimensions")
        self.input_dim = int(input_dim)
        self.output_dim = int(output_dim)
        self.work_units = 0

    def predict(self, observation):
        self.work_units += self.output_dim
        return np.asarray(observation, dtype=np.float64).copy()

    def observe(self, observation, next_observation):
        del observation, next_observation
        self.work_units += 1

    def structure_metrics(self):
        return {
            "unit_count": self.input_dim + self.output_dim,
            "connection_count": self.input_dim,
            "growth_events": 0,
            "pruning_events": 0,
            "work_units": self.work_units,
            "estimated_state_bytes": 0,
        }


class FixedHebbPredictor:
    """Fixed all-to-all predictor with centered local Hebbian association."""

    def __init__(self, input_dim=8, output_dim=8, seed=0, learning_rate=0.025):
        del seed
        self.input_dim = int(input_dim)
        self.output_dim = int(output_dim)
        self.learning_rate = float(learning_rate)
        self.input_mean = np.full(self.input_dim, 0.5, dtype=np.float64)
        self.output_mean = np.full(self.output_dim, 0.5, dtype=np.float64)
        self.weights = np.zeros((self.input_dim, self.output_dim), dtype=np.float64)
        self.work_units = 0

    def predict(self, observation):
        x = np.asarray(observation, dtype=np.float64)
        pred = self.output_mean + (x - self.input_mean) @ self.weights
        self.work_units += self.input_dim * self.output_dim * 2 + self.output_dim
        return np.clip(pred, 0.0, 1.0)

    def observe(self, observation, next_observation):
        x = np.asarray(observation, dtype=np.float64)
        y = np.asarray(next_observation, dtype=np.float64)
        dx = x - self.input_mean
        dy = y - self.output_mean
        # A centered Hebbian co-activity estimate, scaled by Bernoulli variance.
        target_weights = 4.0 * np.outer(dx, dy)
        rate = self.learning_rate
        self.weights += rate * (target_weights - self.weights)
        np.clip(self.weights, -1.0, 1.0, out=self.weights)
        self.input_mean += rate * dx
        self.output_mean += rate * dy
        self.work_units += self.input_dim * self.output_dim * 5 + self.input_dim + self.output_dim

    def structure_metrics(self):
        return {
            "unit_count": self.input_dim + self.output_dim,
            "connection_count": self.input_dim * self.output_dim,
            "growth_events": 0,
            "pruning_events": 0,
            "work_units": self.work_units,
            "estimated_state_bytes": int(self.input_mean.nbytes + self.output_mean.nbytes + self.weights.nbytes),
        }


class GrowingCorrelationPredictor:
    """Local correlation predictor whose edge units grow and are pruned online."""

    def __init__(self, input_dim=8, output_dim=8, seed=0, trace_rate=0.02,
                 grow_threshold=0.55, prune_threshold=0.25, prune_patience=30,
                 min_evidence=40, max_units=16):
        del seed
        self.input_dim = int(input_dim)
        self.output_dim = int(output_dim)
        self.trace_rate = float(trace_rate)
        self.grow_threshold = float(grow_threshold)
        self.prune_threshold = float(prune_threshold)
        self.prune_patience = int(prune_patience)
        self.min_evidence = int(min_evidence)
        self.max_units = int(max_units)
        self.input_mean = np.full(self.input_dim, 0.5, dtype=np.float64)
        self.output_mean = np.full(self.output_dim, 0.5, dtype=np.float64)
        self.input_var = np.full(self.input_dim, 0.25, dtype=np.float64)
        self.output_var = np.full(self.output_dim, 0.25, dtype=np.float64)
        self.cross_cov = np.zeros((self.input_dim, self.output_dim), dtype=np.float64)
        # Active edge units are keyed by (source, target); each connects one
        # sensory node to one predictive node through a local association.
        self.edges = {}
        self.samples = 0
        self.growth_events = 0
        self.pruning_events = 0
        self.work_units = 0

    def _correlations(self):
        denominator = np.sqrt(np.maximum(self.input_var[:, None] * self.output_var[None, :], 1e-8))
        return np.clip(self.cross_cov / denominator, -1.0, 1.0)

    def predict(self, observation):
        x = np.asarray(observation, dtype=np.float64)
        pred = self.output_mean.copy()
        for (source, target), edge in self.edges.items():
            coefficient = self.cross_cov[source, target] / max(self.input_var[source], 1e-8)
            pred[target] += coefficient * (x[source] - self.input_mean[source])
        self.work_units += self.output_dim + len(self.edges) * 6
        return np.clip(pred, 0.0, 1.0)

    def observe(self, observation, next_observation):
        x = np.asarray(observation, dtype=np.float64)
        y = np.asarray(next_observation, dtype=np.float64)
        dx = x - self.input_mean
        dy = y - self.output_mean
        rate = self.trace_rate
        self.cross_cov += rate * (np.outer(dx, dy) - self.cross_cov)
        self.input_var += rate * (dx * dx - self.input_var)
        self.output_var += rate * (dy * dy - self.output_var)
        self.input_mean += rate * dx
        self.output_mean += rate * dy
        self.samples += 1

        correlations = self._correlations()
        remove = []
        for key, edge in self.edges.items():
            if abs(correlations[key]) < self.prune_threshold:
                edge["low_steps"] += 1
                if edge["low_steps"] >= self.prune_patience:
                    remove.append(key)
            else:
                edge["low_steps"] = 0
        for key in remove:
            del self.edges[key]
            self.pruning_events += 1

        if self.samples >= self.min_evidence and len(self.edges) < self.max_units:
            candidates = np.argwhere(np.abs(correlations) >= self.grow_threshold)
            ranked = sorted(
                ((float(abs(correlations[source, target])), int(source), int(target))
                 for source, target in candidates if (int(source), int(target)) not in self.edges),
                reverse=True,
            )
            for _, source, target in ranked[:self.max_units - len(self.edges)]:
                self.edges[(source, target)] = {"low_steps": 0}
                self.growth_events += 1

        self.work_units += self.input_dim * self.output_dim * 10 + len(self.edges) * 5

    def structure_metrics(self):
        # Input/output sensory nodes are fixed. Each active edge unit introduces
        # one predictive unit and two connections.
        estimated_bytes = (self.input_mean.nbytes + self.output_mean.nbytes
                           + self.input_var.nbytes + self.output_var.nbytes
                           + self.cross_cov.nbytes + 160 * len(self.edges))
        return {
            "unit_count": self.input_dim + self.output_dim + len(self.edges),
            "connection_count": 2 * len(self.edges),
            "active_edge_units": len(self.edges),
            "growth_events": self.growth_events,
            "pruning_events": self.pruning_events,
            "work_units": self.work_units,
            "estimated_state_bytes": int(estimated_bytes),
        }


class _LocalContact:
    """The endpoint EMA state stored on one extant contact."""

    def __init__(self, target):
        self.target = int(target)
        self.source_mean = 0.5
        self.target_mean = 0.5
        self.product_mean = 0.25
        self.low_streak = 0

    def update(self, source, target_event, alpha, prune_threshold):
        self.source_mean += alpha * (source - self.source_mean)
        self.target_mean += alpha * (target_event - self.target_mean)
        self.product_mean += alpha * (source * target_event - self.product_mean)
        if self.score < prune_threshold:
            self.low_streak += 1
        else:
            self.low_streak = 0

    @property
    def score(self):
        return self.product_mean - self.source_mean * self.target_mean


class ProbationarySproutingPredictor:
    """H001: coactivity-gated local sprouting under a hard contact budget."""

    uses_backprop = False

    def __init__(self, input_dim=1, output_dim=8, seed=0, total_capacity=2,
                 probe_steps=50, alpha=0.02, accept_threshold=0.08,
                 prune_threshold=0.025, prune_steps=100, probe_mode="coactive"):
        if int(input_dim) != 1:
            raise ValueError("probationary sprouting requires one source event")
        if int(output_dim) < 2 or int(total_capacity) < 2:
            raise ValueError("sprouting requires at least two targets and two total slots")
        if probe_mode not in {"coactive", "uniform"}:
            raise ValueError("probe_mode must be coactive or uniform")
        self.input_dim = 1
        self.output_dim = int(output_dim)
        self.total_capacity = int(total_capacity)
        self.stable_capacity = self.total_capacity - 1
        self.probe_steps = int(probe_steps)
        self.alpha = float(alpha)
        self.accept_threshold = float(accept_threshold)
        self.prune_threshold = float(prune_threshold)
        self.prune_steps = int(prune_steps)
        self.probe_mode = probe_mode
        self.rng = random.Random(int(seed) ^ 0x5A17C9E3)
        self.stable = {}
        self.probe = None
        self.probe_age = 0
        self.samples = 0
        self.sprout_births = 0
        self.stabilizations = 0
        self.rejections = 0
        self.pruning_events = 0
        self.max_total_contacts = 0
        self.work_units = 0

    def predict(self, observation):
        source = float(np.asarray(observation, dtype=np.float64).reshape(-1)[0])
        prediction = np.full(self.output_dim, 0.5, dtype=np.float64)
        for target in self.stable:
            prediction[target] = source
        self.work_units += self.output_dim + 2 * len(self.stable)
        return prediction

    def _choose_probe(self, source, target_events):
        available = [i for i in range(self.output_dim) if i not in self.stable]
        if self.probe_mode == "coactive":
            if source == 0.0:
                return None
            available = [i for i in available if target_events[i] == 1.0]
        return self.rng.choice(available) if available else None

    def observe(self, observation, next_observation):
        source = float(np.asarray(observation, dtype=np.float64).reshape(-1)[0])
        target_events = np.asarray(next_observation, dtype=np.float64).reshape(-1)
        if target_events.shape != (self.output_dim,):
            raise ValueError(f"expected target shape {(self.output_dim,)}, got {target_events.shape}")

        for contact in self.stable.values():
            contact.update(source, target_events[contact.target], self.alpha, self.prune_threshold)
        if self.probe is not None:
            self.probe.update(source, target_events[self.probe.target], self.alpha, self.prune_threshold)
            self.probe_age += 1

        expired = [target for target, contact in self.stable.items()
                   if contact.low_streak >= self.prune_steps]
        for target in expired:
            del self.stable[target]
            self.pruning_events += 1

        if self.probe is not None and self.probe_age >= self.probe_steps:
            weakest = min(self.stable.values(), key=lambda contact: contact.score) if self.stable else None
            eligible = self.probe.score > self.accept_threshold
            wins = weakest is None or self.probe.score > weakest.score
            if eligible and (len(self.stable) < self.stable_capacity or wins):
                if len(self.stable) >= self.stable_capacity and weakest is not None:
                    del self.stable[weakest.target]
                    self.pruning_events += 1
                self.stable[self.probe.target] = self.probe
                self.stabilizations += 1
            else:
                self.rejections += 1
                self.pruning_events += 1
            self.probe = None
            self.probe_age = 0

        if self.probe is None:
            target = self._choose_probe(source, target_events)
            if target is not None:
                self.probe = _LocalContact(target)
                self.probe_age = 0
                self.sprout_births += 1

        self.samples += 1
        contacts = len(self.stable) + int(self.probe is not None)
        self.max_total_contacts = max(self.max_total_contacts, contacts)
        if contacts > self.total_capacity:
            raise RuntimeError("hard contact capacity exceeded")
        self.work_units += 8 * self.output_dim + 12 * contacts

    def structure_metrics(self):
        contacts = len(self.stable) + int(self.probe is not None)
        return {
            "unit_count": self.input_dim + self.output_dim,
            "connection_count": contacts,
            "active_contacts": contacts,
            "stable_contacts": len(self.stable),
            "probationary_contact": int(self.probe is not None),
            "growth_events": self.sprout_births,
            "stabilizations": self.stabilizations,
            "rejections": self.rejections,
            "pruning_events": self.pruning_events,
            "max_total_contacts": self.max_total_contacts,
            "work_units": self.work_units,
            "estimated_state_bytes": int(160 * contacts + 8 * (self.input_dim + self.output_dim)),
        }


AGENTS = {
    "mean": MeanPredictor,
    "persistence": PersistencePredictor,
    "fixed_hebb": FixedHebbPredictor,
    "growing": GrowingCorrelationPredictor,
    "probationary_sprouting": ProbationarySproutingPredictor,
}
