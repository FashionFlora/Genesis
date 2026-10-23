"""Reward-free nonstationary sensory stream with explicit returns to old regimes."""

from dataclasses import dataclass
import random

import numpy as np


@dataclass(frozen=True)
class Regime:
    name: str
    source: int
    target: int
    flip_probability: float = 0.10


DEFAULT_REGIMES = {
    "A": Regime("A", source=0, target=7),
    "B": Regime("B", source=1, target=7),
    "C": Regime("C", source=2, target=7),
}
DEFAULT_SCHEDULE = ("A", "B", "A", "C", "B", "A")


class SensorStream:
    """Binary observations whose predictive relation changes and later returns.

    At each transition every output channel is an independent fair bit except
    the selected target, which copies its regime's source channel with the
    configured probability. The regime and phase are evaluator metadata; the
    agent interface receives sensory vectors only.
    """

    def __init__(self, seed=0, segment_length=1000, input_dim=8, output_dim=8,
                 regimes=None, schedule=None):
        self.seed = int(seed)
        self.segment_length = int(segment_length)
        self.input_dim = int(input_dim)
        self.output_dim = int(output_dim)
        self.regimes = dict(DEFAULT_REGIMES if regimes is None else regimes)
        self.schedule = tuple(DEFAULT_SCHEDULE if schedule is None else schedule)
        if self.segment_length <= 0 or self.input_dim <= 0 or self.output_dim <= 0:
            raise ValueError("segment_length and stream dimensions must be positive")
        if self.input_dim != self.output_dim:
            raise ValueError("next-observation prediction requires equal input and output dimensions")
        if not self.schedule or any(name not in self.regimes for name in self.schedule):
            raise ValueError("schedule must contain known regimes")
        for regime in self.regimes.values():
            if not 0 <= regime.source < self.input_dim:
                raise ValueError(f"source index out of range in regime {regime.name}")
            if not 0 <= regime.target < self.output_dim:
                raise ValueError(f"target index out of range in regime {regime.name}")
            if not 0.0 <= regime.flip_probability <= 0.5:
                raise ValueError("flip_probability must be in [0, 0.5]")
        self.reset()

    def reset(self):
        self.rng = np.random.default_rng(self.seed)
        self.observation = self.rng.integers(0, 2, size=self.input_dim).astype(np.float64)
        self.transitions = 0
        return self.observation.copy()

    def regime_at(self, step=None):
        step = self.transitions if step is None else int(step)
        phase_index = step // self.segment_length
        regime_name = self.schedule[phase_index % len(self.schedule)]
        return self.regimes[regime_name], phase_index

    def step(self):
        """Return ``(next_observation, regime_name, phase_index)`` for evaluation."""
        regime, phase_index = self.regime_at()
        next_observation = self.rng.integers(0, 2, size=self.output_dim).astype(np.float64)
        if self.rng.random() >= regime.flip_probability:
            next_observation[regime.target] = self.observation[regime.source]
        else:
            next_observation[regime.target] = 1.0 - self.observation[regime.source]
        self.observation = next_observation
        self.transitions += 1
        return next_observation.copy(), regime.name, phase_index

    def describe(self):
        return {
            "seed": self.seed,
            "input_dim": self.input_dim,
            "output_dim": self.output_dim,
            "segment_length": self.segment_length,
            "schedule": list(self.schedule),
            "regimes": {
                name: {"source": regime.source, "target": regime.target,
                       "flip_probability": regime.flip_probability}
                for name, regime in sorted(self.regimes.items())
            },
        }


class SourceNeighborhoodStream:
    """One source event and a neighborhood of simultaneous sensory events.

    A hidden regime selects one target channel. On the correlated stream that
    channel copies the source event; all other channels are independent bits.
    A null stream makes every target independent. An optional per-regime rate
    schedule shifts the Bernoulli event rate without exposing it to agents.
    """

    def __init__(self, seed=0, steps_per_regime=1500, target_count=8,
                 regime_count=8, event_rates=None, null_stream=False,
                 target_sequence=None, source_rates=None, target_rates=None):
        self.seed = int(seed)
        self.steps_per_regime = int(steps_per_regime)
        self.target_count = int(target_count)
        self.regime_count = int(regime_count)
        common_rates = tuple((0.5,) if event_rates is None else event_rates)
        self.source_rates = tuple(common_rates if source_rates is None else source_rates)
        self.target_rates = tuple(common_rates if target_rates is None else target_rates)
        self.null_stream = bool(null_stream)
        self.target_sequence = tuple((i % self.target_count for i in range(self.regime_count))
                                     if target_sequence is None else target_sequence)
        if min(self.steps_per_regime, self.target_count, self.regime_count) <= 0:
            raise ValueError("steps_per_regime, target_count, and regime_count must be positive")
        if (not self.source_rates or not self.target_rates
                or any(not 0.0 < rate < 1.0 for rate in self.source_rates + self.target_rates)):
            raise ValueError("event rates must be strictly between zero and one")
        if not self.target_sequence or any(not 0 <= target < self.target_count for target in self.target_sequence):
            raise ValueError("target_sequence must contain valid target indices")
        self.rng = random.Random(self.seed)
        self.transitions = 0

    def sample(self):
        """Return source, target vector, and evaluator-only regime metadata."""
        phase_index = self.transitions // self.steps_per_regime
        phase_step = self.transitions % self.steps_per_regime
        target_index = self.target_sequence[phase_index % len(self.target_sequence)]
        source_rate = self.source_rates[phase_index % len(self.source_rates)]
        target_rate = self.target_rates[phase_index % len(self.target_rates)]
        source = float(self.rng.random() < source_rate)
        target = []
        for index in range(self.target_count):
            if index == target_index and not self.null_stream:
                target.append(source)
            else:
                target.append(float(self.rng.random() < target_rate))
        self.transitions += 1
        metadata = {
            "phase_index": phase_index,
            "phase_step": phase_step,
            "regime": target_index,
            "event_rate": source_rate,
            "source_rate": source_rate,
            "target_rate": target_rate,
            "null_stream": self.null_stream,
        }
        return np.asarray([source], dtype=np.float64), np.asarray(target, dtype=np.float64), metadata

    def describe(self):
        return {
            "seed": self.seed,
            "source_dim": 1,
            "target_dim": self.target_count,
            "steps_per_regime": self.steps_per_regime,
            "regime_count": self.regime_count,
            "source_rates": list(self.source_rates),
            "target_rates": list(self.target_rates),
            "null_stream": self.null_stream,
            "target_sequence": list(self.target_sequence),
        }
