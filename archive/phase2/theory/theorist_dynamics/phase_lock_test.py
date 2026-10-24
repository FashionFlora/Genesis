"""Regime-switch test for a local phase-locking edge memory."""
import math
import json
import random
from pathlib import Path


def stream(seed, steps=6000):
    rng = random.Random(seed)
    previous_sources = [rng.randrange(2), rng.randrange(2)]
    for t in range(steps):
        regime = (t // 300) % 2
        sources = [rng.randrange(2), rng.randrange(2)]
        noise = rng.random() < 0.12
        target = previous_sources[regime] ^ noise
        previous_sources = sources
        yield sources + [target]


class PhaseEdges:
    def __init__(self, gain=0.12, damping=0.04):
        self.theta = None
        self.previous = None
        self.gain = gain
        self.damping = damping

    def step(self, obs):
        if self.theta is None:
            self.theta = [[math.pi / 2 for _ in obs] for _ in obs]
        if self.previous is not None:
            for i, x in enumerate(self.previous):
                for j, y in enumerate(obs):
                    signed = (2 * x - 1) * (2 * y - 1)
                    theta = self.theta[i][j]
                    self.theta[i][j] += (-self.gain * signed + self.damping * math.cos(theta)) * math.sin(theta)
        out = [0.5] * len(obs)
        for j in range(len(obs)):
            sources = range(2) if j == 2 else range(len(obs))
            i = max(sources, key=lambda k: abs(math.cos(self.theta[k][j])))
            out[j] = 0.5 + 0.5 * math.cos(self.theta[i][j]) * (2 * obs[i] - 1)
        self.previous = list(obs)
        return out


class ExpCorrelation:
    def __init__(self, decay=0.96):
        self.sum = [[0.0] * 3 for _ in range(3)]
        self.count = [[0.0] * 3 for _ in range(3)]
        self.previous = None
        self.decay = decay

    def step(self, obs):
        for i in range(3):
            for j in range(3):
                self.sum[i][j] *= self.decay
                self.count[i][j] *= self.decay
        if self.previous is not None:
            for i, x in enumerate(self.previous):
                for j, y in enumerate(obs):
                    self.sum[i][j] += (2 * x - 1) * (2 * y - 1)
                    self.count[i][j] += 1.0
        out = [0.5] * 3
        for j in range(3):
            sources = range(2) if j == 2 else range(3)
            i = max(sources, key=lambda k: abs(self.sum[k][j]) / (self.count[k][j] + 2))
            q = self.sum[i][j] / (self.count[i][j] + 2)
            out[j] = 0.5 + 0.5 * q * (2 * obs[i] - 1)
        self.previous = list(obs)
        return out


def evaluate(agent_type, seed):
    agent = agent_type()
    rng = random.Random(seed)
    losses = []
    previous = [rng.randrange(2) for _ in range(3)]
    for t, obs in enumerate(stream(seed)):
        pred = agent.step(previous)
        # Score target 1 prediction for this transition; the stream is generated
        # from the source in obs, so use the observed target as next state.
        losses.append((pred[2] - obs[2]) ** 2)
        previous = obs
    post_switch = [losses[t] for t in range(300, len(losses)) if t % 300 < 100]
    return sum(post_switch) / len(post_switch)


if __name__ == "__main__":
    seeds = (31, 47, 83, 101, 137)
    variants = {
        "phase_no_damping": lambda: PhaseEdges(damping=0.0),
        "phase_damped": PhaseEdges,
        "exp_correlation": ExpCorrelation,
    }
    results = {name: [evaluate(factory, seed) for seed in seeds]
               for name, factory in variants.items()}
    for name, rows in results.items():
        print(name, "early-after-switch Brier", round(sum(rows) / len(rows), 5), rows)
    Path(__file__).with_name("phase_lock_result.json").write_text(
        json.dumps({"metric": "early-after-switch Brier", "seeds": seeds,
                    "results": results}, indent=2) + "\n")
