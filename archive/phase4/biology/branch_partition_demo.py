"""Toy ablation of branch-local memory versus shared dendritic storage."""

import random


TASKS = 4
INPUTS = 12
TRAIN_PER_TASK = 250
PROBES = 200
BRANCHES = 4
RATE = 0.25


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def run(seed, mode):
    rng = random.Random(seed)
    targets = [[rng.gauss(0, 1) for _ in range(INPUTS)] for _ in range(TASKS)]
    targets = [[v / (dot(w, w) ** 0.5) for v in w] for w in targets]
    if mode == "partitioned":
        route = list(range(TASKS))
    elif mode == "shared":
        route = [0] * TASKS
    else:
        route = [rng.randrange(BRANCHES) for _ in range(TASKS)]
    weights = [[0.0] * INPUTS for _ in range(BRANCHES)]

    for task in range(TASKS):
        branch = route[task]
        for _ in range(TRAIN_PER_TASK):
            x = [rng.gauss(0, 1) for _ in range(INPUTS)]
            y = dot(x, targets[task]) / INPUTS**0.5
            prediction = dot(x, weights[branch]) / INPUTS**0.5
            error = y - prediction
            scale = RATE / INPUTS**0.5
            weights[branch] = [w + scale * error * v for w, v in zip(weights[branch], x)]

    errors = []
    for task in range(TASKS):
        branch = route[task]
        squared = 0.0
        for _ in range(PROBES):
            x = [rng.gauss(0, 1) for _ in range(INPUTS)]
            y = dot(x, targets[task]) / INPUTS**0.5
            prediction = dot(x, weights[branch]) / INPUTS**0.5
            squared += (y - prediction) ** 2
        errors.append(squared / PROBES)
    return sum(errors) / TASKS, sum(route[i] == route[j] for i in range(TASKS) for j in range(i))


def main():
    seeds = range(500)
    for mode in ("partitioned", "shared", "random_route"):
        results = [run(seed, mode) for seed in seeds]
        mse = sum(result[0] for result in results) / len(results)
        collisions = sum(result[1] for result in results) / len(results)
        print(f"{mode}: mean_probe_mse={mse:.6f} mean_task_collisions={collisions:.3f}")


if __name__ == "__main__":
    main()
