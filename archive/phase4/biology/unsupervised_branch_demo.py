"""Toy ablation: can unlabeled context cues route task-local memories?"""

import random


TASKS = 4
INPUTS = 12
CONTEXT = 4
BRANCHES = 4
TRAIN_PER_TASK = 100
PROBES = 100
RATE = 0.03


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def kmeans(points, rng):
    centers = [list(point) for point in rng.sample(points, BRANCHES)]
    for _ in range(30):
        groups = [[] for _ in centers]
        for point in points:
            winner = min(range(BRANCHES), key=lambda j: dot(
                [a - b for a, b in zip(point, centers[j])],
                [a - b for a, b in zip(point, centers[j])]))
            groups[winner].append(point)
        for j, group in enumerate(groups):
            if group:
                centers[j] = [sum(row[i] for row in group) / len(group)
                              for i in range(CONTEXT)]
    return centers


def nearest(point, centers):
    return min(range(len(centers)), key=lambda j: sum(
        (a - b) ** 2 for a, b in zip(point, centers[j])))


def run(seed, mode):
    rng = random.Random(seed)
    contexts = [[rng.gauss(0, 2) for _ in range(CONTEXT)] for _ in range(TASKS)]
    targets = [[0.0] * CONTEXT + [rng.gauss(0, 1) for _ in range(INPUTS - CONTEXT)]
               for _ in range(TASKS)]
    samples = []
    for task in range(TASKS):
        for _ in range(TRAIN_PER_TASK + PROBES):
            x = [contexts[task][i] + rng.gauss(0, 0.15) for i in range(CONTEXT)]
            x += [rng.gauss(0, 1) for _ in range(INPUTS - CONTEXT)]
            y = dot(x, targets[task]) / (INPUTS - CONTEXT) ** 0.5
            samples.append((task, x, y))

    if mode == "unsupervised":
        # The router sees a held-out, unlabeled cue sample, not task identities.
        centers = kmeans([x[:CONTEXT] for _, x, _ in samples[::5]], rng)
    elif mode == "random":
        routes = [rng.randrange(BRANCHES) for _ in range(TASKS)]

    train = [samples[task * (TRAIN_PER_TASK + PROBES) + i]
             for task in range(TASKS) for i in range(TRAIN_PER_TASK)]
    rng.shuffle(train)
    weights = [[0.0] * INPUTS for _ in range(BRANCHES)]
    for task, x, y in train:
        if mode == "shared":
            branch = 0
        elif mode == "oracle":
            branch = task
        elif mode == "random":
            branch = routes[task]
        else:
            branch = nearest(x[:CONTEXT], centers)
        prediction = dot(x, weights[branch]) / (INPUTS - CONTEXT) ** 0.5
        error = y - prediction
        scale = RATE / (INPUTS - CONTEXT) ** 0.5
        weights[branch] = [w + scale * error * v for w, v in zip(weights[branch], x)]

    errors = []
    for task in range(TASKS):
        # Hold out the final examples of each task for evaluation.
        start = task * (TRAIN_PER_TASK + PROBES) + TRAIN_PER_TASK
        probes = samples[start:start + PROBES]
        for _, x, y in probes:
            if mode == "shared":
                branch = 0
            elif mode == "oracle":
                branch = task
            elif mode == "random":
                branch = routes[task]
            else:
                branch = nearest(x[:CONTEXT], centers)
            errors.append((y - dot(x, weights[branch]) /
                           (INPUTS - CONTEXT) ** 0.5) ** 2)
    return sum(errors) / len(errors)


def main():
    for mode in ("oracle", "unsupervised", "shared", "random"):
        values = [run(seed, mode) for seed in range(200)]
        print(f"{mode}: mean_probe_mse={sum(values) / len(values):.6f}")


if __name__ == "__main__":
    main()
