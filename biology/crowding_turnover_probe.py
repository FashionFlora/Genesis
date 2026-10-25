"""Toy test of density-coupled growth/extrusion for a changing input ensemble.

Cells occupy a ring of slots, sense only the current input, and keep a local
use trace.  Turnover is structural: a crowded local neighborhood removes its
weakest trace, while a sparse neighborhood lets an active cell copy into an
empty neighboring slot.  No labels, reward, or global selection signal is
used.
"""
import math
import random
import statistics


SLOTS = 96
INITIAL_ALIVE = 64
DIM = 8
PROTOTYPES = 24
EVENTS_PER_CONTEXT = 1800
SEEDS = 100
NEIGHBOR_RADIUS = 3
LOW_DENSITY = 3
HIGH_DENSITY = 6
MUTATION_SD = 0.035
LESION = tuple(range(40, 48))


def unit(v):
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def neighbors(i):
    return [((i + d) % SLOTS) for d in range(-NEIGHBOR_RADIUS, NEIGHBOR_RADIUS + 1)]


def score(cells, alive, targets):
    hits = []
    for target in targets:
        best = max((cosine(cells[i], target) for i in range(SLOTS) if alive[i]), default=0.0)
        hits.append(best)
    return statistics.mean(hits), statistics.pstdev(hits)


def run(seed, mode):
    rng = random.Random(seed)
    targets = [unit([rng.gauss(0.0, 1.0) for _ in range(DIM)]) for _ in range(PROTOTYPES)]
    # The second context rotates each target, so memorizing one coordinate set is insufficient.
    shifted = [unit([t[(j - 1) % DIM] for j in range(DIM)]) for t in targets]
    cells = [unit([rng.gauss(0.0, 1.0) for _ in range(DIM)]) for _ in range(SLOTS)]
    alive = [i < INITIAL_ALIVE for i in range(SLOTS)]
    use = [0.0] * SLOTS
    context_scores = []
    lesion_recovery = 0.0
    for context_targets in (targets, shifted):
        for event in range(EVENTS_PER_CONTEXT):
            if context_targets is shifted and event == EVENTS_PER_CONTEXT // 2:
                for i in LESION:
                    alive[i] = False
                    use[i] = 0.0
            target = rng.choice(context_targets)
            activities = [cosine(cells[i], target) if alive[i] else -2.0 for i in range(SLOTS)]
            winner = max(range(SLOTS), key=lambda i: activities[i])
            for i in range(SLOTS):
                if alive[i]:
                    use[i] *= 0.997
            use[winner] += max(0.0, activities[winner])
            # Density is sensed at a local tissue location, while use chooses
            # which neighbor is fit enough to persist or divide.
            anchor = rng.randrange(SLOTS) if mode == "density" else winner
            local = neighbors(anchor)
            local_alive = [i for i in local if alive[i]]
            density = len(local_alive)
            if mode == "density":
                if density > HIGH_DENSITY and len(local_alive) > 1:
                    loser = min(local_alive, key=lambda i: use[i])
                    alive[loser] = False
                elif density < LOW_DENSITY:
                    empty = [i for i in local if not alive[i]]
                    if empty:
                        source = max(local_alive, key=lambda i: use[i], default=winner)
                        child = empty[0]
                        cells[child] = unit([x + rng.gauss(0.0, MUTATION_SD) for x in cells[source]])
                        use[child] = use[source] * 0.5
                        alive[child] = True
            elif mode == "global":
                living = [i for i in range(SLOTS) if alive[i]]
                if living:
                    empty = [i for i in range(SLOTS) if not alive[i]]
                    if len(living) < INITIAL_ALIVE and empty:
                        child = rng.choice(empty)
                        cells[child] = unit([x + rng.gauss(0.0, MUTATION_SD) for x in cells[winner]])
                        use[child] = use[winner] * 0.5
                        alive[child] = True
                    else:
                        loser = min(living, key=lambda i: use[i])
                        cells[loser] = unit([x + rng.gauss(0.0, MUTATION_SD) for x in cells[winner]])
                        use[loser] = use[winner] * 0.5
            elif mode == "none":
                pass
            # local activity update is the only adaptation shared by all modes
            cells[winner] = unit([x + 0.012 * (t - x) for x, t in zip(cells[winner], target)])
        context_scores.append(score(cells, alive, context_targets))
    lesion_recovery = sum(alive[i] for i in LESION) / len(LESION)
    return context_scores, sum(alive), lesion_recovery


if __name__ == "__main__":
    modes = ("none", "global", "density")
    print(f"seeds={SEEDS} slots={SLOTS} initial_alive={INITIAL_ALIVE} events_per_context={EVENTS_PER_CONTEXT}")
    all_results = {mode: [run(seed, mode) for seed in range(SEEDS)] for mode in modes}
    for mode in modes:
        results = all_results[mode]
        for ctx, label in enumerate(("base", "shifted")):
            means = [row[0][ctx][k] for row in results for k in (0,)]
            spread = [row[0][ctx][1] for row in results]
            print(f"{mode} {label}: coverage={statistics.mean(means):.6f} "
                  f"coverage_sd={statistics.pstdev(means):.6f} "
                  f"target_spread={statistics.mean(spread):.6f}")
        counts = [row[1] for row in results]
        print(f"{mode} alive_end={statistics.mean(counts):.6f} alive_sd={statistics.pstdev(counts):.6f}")
        recovery = [row[2] for row in results]
        print(f"{mode} lesion_recovery={statistics.mean(recovery):.6f} "
              f"lesion_recovery_sd={statistics.pstdev(recovery):.6f}")
