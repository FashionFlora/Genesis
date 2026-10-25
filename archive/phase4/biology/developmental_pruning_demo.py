"""Logic check: separate competitive selection from physical pruning."""

import random


def trial(seed, mode, n=8, target=2, steps=100, active=20, target_overlap=16):
    rng = random.Random(seed)
    post = set(rng.sample(range(steps), active))
    trains = []
    for i in range(n):
        if i < target:
            shared = set(rng.sample(sorted(post), target_overlap))
            rest = set(rng.sample(sorted(set(range(steps)) - post), active - target_overlap))
            trains.append(shared | rest)
        else:
            trains.append(set(rng.sample(range(steps), active)))

    scores = [len(x & post) / active for x in trains]
    tie_order = list(range(n))
    rng.shuffle(tie_order)
    if mode == "staged":
        # Stage 1 stores relative evidence; Stage 2 removes weak connections.
        center = sum(scores) / n
        staged_scores = [score - center for score in scores]
        survivors = sorted(tie_order, key=lambda i: staged_scores[i], reverse=True)[: n // 2]
    elif mode == "absolute":
        survivors = sorted(tie_order, key=lambda i: len(trains[i]) / steps, reverse=True)[: n // 2]
    elif mode == "no_cleanup":
        survivors = list(range(n))
    else:
        raise ValueError(mode)
    return len(set(survivors) & set(range(target))), len(survivors)


def main():
    seeds = range(2000)
    print("seeds=2000 inputs=8 target_inputs=2 activity=20/100 retained=4")
    for overlap in (20, 16, 12, 8, 4, 0):
        print(f"target_overlap={overlap}/20")
        for mode in ("staged", "absolute", "no_cleanup"):
            rows = [trial(seed, mode, target_overlap=overlap) for seed in seeds]
            print(f"  {mode}: target_retained={sum(x[0] for x in rows) / len(rows):.4f}/2 "
                  f"edges_remaining={sum(x[1] for x in rows) / len(rows):.4f}/8")


if __name__ == "__main__":
    main()
