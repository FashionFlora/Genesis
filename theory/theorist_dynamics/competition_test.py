"""Compare bounded and cumulative local expert competition after regime changes."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from candidates.dynamics_predictive_competition import principle


def run(seed, weight_decay):
    principle.PARAMS["weight_decay"] = weight_decay
    system = principle.System()
    rng = random.Random(seed)
    prev_sources = [rng.randrange(2), rng.randrange(2)]
    obs = [*prev_sources, rng.randrange(2)]
    losses = []
    for t in range(2400):
        pred = system.step(obs)
        regime = (t // 300) % 2
        sources = [rng.randrange(2), rng.randrange(2)]
        target = prev_sources[regime] ^ (rng.random() < 0.12)
        next_obs = [*sources, int(target)]
        losses.append((pred[2] - target) ** 2)
        prev_sources, obs = sources, next_obs
    return sum(losses[t] for t in range(len(losses)) if t % 300 < 60) / (len(losses) // 300 * 60)


if __name__ == "__main__":
    seeds = (31, 47, 83, 101, 137)
    for decay in (1.0, 0.98, 0.95, 0.90, 0.80, 0.70):
        scores = [run(seed, decay) for seed in seeds]
        print(f"weight_decay={decay:.3f} early-switch Brier={sum(scores)/len(scores):.5f} seeds={scores}")
