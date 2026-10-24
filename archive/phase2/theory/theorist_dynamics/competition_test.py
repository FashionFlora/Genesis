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
    phase_masses = []
    phase_loss = []
    for t in range(2400):
        pred = system.step(obs)
        regime = (t // 300) % 2
        sources = [rng.randrange(2), rng.randrange(2)]
        target = prev_sources[regime] ^ (rng.random() < 0.12)
        next_obs = [*sources, int(target)]
        losses.append((pred[2] - target) ** 2)
        if t % 300 == 299:
            phase_masses.append(system.structure()["connections"])
            phase_loss.append(sum(losses[-300:]) / 300)
        prev_sources, obs = sources, next_obs
    early = sum(losses[t] for t in range(len(losses)) if t % 300 < 60) / (len(losses) // 300 * 60)
    return early, phase_masses, phase_loss


if __name__ == "__main__":
    seeds = (31, 47, 83, 101, 137)
    for decay in (1.0, 0.98, 0.95, 0.90, 0.80, 0.70):
        results = [run(seed, decay) for seed in seeds]
        scores = [result[0] for result in results]
        masses = [sum(result[1]) / len(result[1]) for result in results]
        print(f"weight_decay={decay:.3f} early-switch Brier={sum(scores)/len(scores):.5f} mean-edges={sum(masses)/len(masses):.1f}")
