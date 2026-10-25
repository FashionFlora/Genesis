"""Toy ablation of an adult-born, high-plasticity cohort.

The model is deliberately small: binary context prototypes are presented in
sequence, a unit predicts a +/-1 context label, and units can be born when an
old receptive field no longer explains the input.  Young units are broad and
plastic; age narrows their receptive field and slows their update.  This is a
mechanistic check, not an organism score or a biological simulation.
"""

import math
import random


DIM = 32
CONTEXTS = 8
TRAIN_PER_CONTEXT = 35
PROBES = 80
MATURATION = 8
YOUNG_SIGMA = 0.75
MATURE_SIGMA = 0.16
YOUNG_RATE = 0.55
MATURE_RATE = 0.025
ACTIVATION_BIRTH = 0.68


def mse(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)


def activation(x, proto, sigma):
    return math.exp(-mse(x, proto) / (2.0 * sigma * sigma))


class Unit:
    def __init__(self, x, target):
        self.proto = list(x)
        self.value = target
        self.age = 0

    def sigma(self, mode):
        if mode == "maturing":
            return MATURE_SIGMA if self.age >= MATURATION else YOUNG_SIGMA
        return YOUNG_SIGMA

    def rate(self, mode):
        if mode == "maturing":
            return MATURE_RATE if self.age >= MATURATION else YOUNG_RATE
        return YOUNG_RATE


def run(seed, mode):
    rng = random.Random(seed)
    prototypes = []
    labels = []
    # Adjacent contexts share 24/32 bits; labels alternate to expose interference.
    base = [rng.randrange(2) for _ in range(DIM)]
    for context in range(CONTEXTS):
        p = list(base)
        for j in range(context * 4, context * 4 + 8):
            p[j % DIM] = 1 - p[j % DIM]
        prototypes.append(p)
        labels.append(1.0 if context % 2 == 0 else -1.0)

    units = []
    order = list(range(CONTEXTS))
    rng.shuffle(order)
    # A shuffled first pass prevents a fixed context from receiving a privileged slot.
    for context in order:
        for _ in range(TRAIN_PER_CONTEXT):
            x = [float(v) + rng.gauss(0.0, 0.035) for v in prototypes[context]]
            target = labels[context]
            if units:
                scores = [activation(x, u.proto, u.sigma(mode)) for u in units]
                winner_i = max(range(len(units)), key=scores.__getitem__)
                winner = units[winner_i]
                if mode == "maturing" and scores[winner_i] < ACTIVATION_BIRTH:
                    winner = Unit(x, target)
                    units.append(winner)
                elif mode != "no_birth" and scores[winner_i] < ACTIVATION_BIRTH:
                    winner = Unit(x, target)
                    units.append(winner)
                else:
                    rate = winner.rate(mode)
                    winner.proto = [p + rate * (v - p) for p, v in zip(winner.proto, x)]
                    winner.value += rate * (target - winner.value)
            else:
                units.append(Unit(x, target))
            for unit in units:
                unit.age += 1

    def predict(x):
        scores = [activation(x, u.proto, u.sigma(mode)) for u in units]
        return units[max(range(len(units)), key=scores.__getitem__)].value

    # Probe after all contexts have competed, then probe each context separately.
    correct = [0] * CONTEXTS
    for context in range(CONTEXTS):
        for _ in range(PROBES):
            x = [float(v) + rng.gauss(0.0, 0.035) for v in prototypes[context]]
            if (predict(x) >= 0) == (labels[context] >= 0):
                correct[context] += 1
    first_retention = correct[0] / PROBES
    similar_accuracy = sum(correct) / (CONTEXTS * PROBES)
    return first_retention, similar_accuracy, len(units)


def main():
    seeds = range(500)
    for mode in ("maturing", "no_birth", "always_broad"):
        rows = [run(seed, mode) for seed in seeds]
        means = [sum(row[i] for row in rows) / len(rows) for i in range(3)]
        print(
            f"{mode}: first_context_retention={means[0]:.3f}; "
            f"all_context_accuracy={means[1]:.3f}; mean_units={means[2]:.2f}"
        )


if __name__ == "__main__":
    main()
