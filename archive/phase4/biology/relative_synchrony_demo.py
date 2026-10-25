"""Toy test: can pairwise timing select inputs when marginal activity is equal?"""

import random


def trial(seed, mode, n_steps=100, n_inputs=8, n_corr=2, active=20):
    rng = random.Random(seed)
    target = set(rng.sample(range(n_steps), active))
    inputs = []
    for i in range(n_inputs):
        if i < n_corr:
            shared = set(rng.sample(sorted(target), 16))
            rest = set(rng.sample(sorted(set(range(n_steps)) - target), active - 16))
            inputs.append(shared | rest)
        else:
            inputs.append(set(rng.sample(range(n_steps), active)))

    if mode == "synchrony":
        scores = [len(x & target) / active for x in inputs]
    elif mode == "absolute":
        scores = [len(x) / n_steps for x in inputs]
    else:
        raise ValueError(mode)
    # Prune half the candidates; random tie-breaking represents no timing signal.
    ranked = list(range(n_inputs))
    rng.shuffle(ranked)
    ranked.sort(key=lambda i: scores[i], reverse=True)
    survivors = set(ranked[: n_inputs // 2])
    return len(survivors & set(range(n_corr)))


def main():
    seeds = range(2000)
    print("steps=100 inputs=8 correlated_inputs=2 impulses_per_input=20 target_impulses=20 correlated_overlap=16 survivors=4")
    for mode in ("synchrony", "absolute"):
        selected = sum(trial(seed, mode) for seed in seeds)
        print(f"{mode}: correlated_inputs_retained={selected / len(seeds):.4f}/2")


if __name__ == "__main__":
    main()
