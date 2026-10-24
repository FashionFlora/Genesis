"""Regime-return test: compare gated conditional memory to fixed aging."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from candidates.dynamics_surprise_gated_memory import principle


def run(seed, gain):
    principle.PARAMS["surprise_gain"] = gain
    system = principle.System()
    rng = random.Random(seed)
    previous_sources = [rng.randrange(2), rng.randrange(2)]
    obs = [*previous_sources, rng.randrange(2)]
    losses = []
    for t in range(2400):
        prediction = system.step(obs)
        regime = (t // 300) % 2
        sources = [rng.randrange(2), rng.randrange(2)]
        target = previous_sources[regime] ^ (rng.random() < 0.12)
        losses.append((prediction[2] - target) ** 2)
        previous_sources, obs = sources, [*sources, int(target)]
    return sum(losses[t] for t in range(len(losses)) if t % 300 < 60) / (len(losses) // 300 * 60)


if __name__ == "__main__":
    for gain in (0.0, 4.0, 8.0, 16.0):
        scores = [run(seed, gain) for seed in (31, 47, 83, 101, 137)]
        print(f"surprise_gain={gain:.1f} early-switch Brier={sum(scores)/len(scores):.5f} seeds={scores}")
