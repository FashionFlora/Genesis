"""Toy ablation: an action copy must cover every action coordinate.

The task is a two-step movement with no sensory feedback between steps.  The
second command is expressed in world coordinates, so the agent must subtract
the first action's predicted consequence.  This is a logic check, not an
organism model.
"""

import math
import random


def run(mode, seed, episodes=1000):
    rng = random.Random(seed)
    first_errors = []
    second_errors = []
    for _ in range(episodes):
        first = [rng.uniform(-1.0, 1.0) for _ in range(3)]
        target = [rng.uniform(-1.0, 1.0) for _ in range(3)]

        # A noisy efference copy models an imperfect relay.  All ablations get
        # the same noise stream and the same first command.
        copy = [value + rng.gauss(0.0, 0.02) for value in first]
        if mode == "vector":
            predicted = copy
        elif mode == "turn_only":
            predicted = [copy[0], 0.0, 0.0]
        elif mode == "none":
            predicted = [0.0, 0.0, 0.0]
        else:
            raise ValueError(mode)

        # The first move itself does not depend on the corollary discharge.
        first_errors.append(0.0)
        command = [target[i] - predicted[i] for i in range(3)]
        true_command = [target[i] - first[i] for i in range(3)]
        second_errors.append(
            math.sqrt(sum((command[i] - true_command[i]) ** 2 for i in range(3)) / 3)
        )
    return sum(first_errors) / episodes, sum(second_errors) / episodes


if __name__ == "__main__":
    print("mode first_rmse second_rmse")
    for mode in ("vector", "turn_only", "none"):
        rows = [run(mode, seed) for seed in range(100)]
        means = [sum(row[i] for row in rows) / len(rows) for i in range(2)]
        print(f"{mode} {means[0]:.6f} {means[1]:.6f}")
