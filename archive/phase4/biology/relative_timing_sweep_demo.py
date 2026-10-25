"""Toy robustness check for timing-based competitive synapse selection."""

import random


def trial(seed, overlap, mode, steps=100, active=20, inputs=8, targets=2):
    rng = random.Random(seed)
    post = set(rng.sample(range(steps), active))
    trains = []
    for i in range(inputs):
        if i < targets:
            shared = set(rng.sample(sorted(post), overlap))
            outside = set(rng.sample(sorted(set(range(steps)) - post), active - overlap))
            trains.append(shared | outside)
        else:
            trains.append(set(rng.sample(range(steps), active)))

    if mode == "timing":
        scores = [len(x & post) / active for x in trains]
    elif mode == "rate":
        scores = [len(x) / steps for x in trains]
    else:
        raise ValueError(mode)

    order = list(range(inputs))
    rng.shuffle(order)
    order.sort(key=lambda i: scores[i], reverse=True)
    return len(set(order[: inputs // 2]) & set(range(targets)))


def main():
    seeds = range(2000)
    print("seeds=2000 steps=100 inputs=8 targets=2 active_per_input=20 keep=4")
    print("target_overlap | timing_retained/2 | rate_retained/2")
    for overlap in (20, 16, 12, 8, 4, 0):
        results = {
            mode: sum(trial(seed, overlap, mode) for seed in seeds) / len(seeds)
            for mode in ("timing", "rate")
        }
        print(f"{overlap:14d} | {results['timing']:.4f} | {results['rate']:.4f}")


if __name__ == "__main__":
    main()
