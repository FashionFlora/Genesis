"""Logic check for selective versus global suppression; not an organism test."""

import random


def run(seed=41, n=10000):
    rng = random.Random(seed)
    cases = {name: [0, 0.0] for name in ("none", "selective", "global")}
    for _ in range(n):
        target = rng.choice((-1, 1))
        relevant = target + rng.gauss(0, 0.6)
        distractor = rng.gauss(0, 2.0)
        for name in cases:
            r, d = relevant, distractor
            if name == "selective":
                d = 0.0
            elif name == "global":
                r, d = 0.5 * r, 0.5 * d
            decision = r + 0.15 * d
            correct = int((1 if decision >= 0 else -1) == target)
            cases[name][0] += correct
            cases[name][1] += abs(r) + abs(d)
    return {name: (hits / n, activity / n) for name, (hits, activity) in cases.items()}


if __name__ == "__main__":
    for mode, (accuracy, activity) in run().items():
        print(f"{mode}: accuracy={accuracy:.4f} activity={activity:.4f}")
