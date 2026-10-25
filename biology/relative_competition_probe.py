"""Toy test: neighbor-relative selection versus a fixed loser threshold."""
import random
import statistics


N = 128
STEPS = 1200
SEEDS = 100
MUTATION = 0.04


def run(seed, mode):
    rng = random.Random(seed)
    cells = [[rng.random(), rng.random()] for _ in range(N)]
    epoch_means = []
    for epoch, context in enumerate(((1.0, 0.0), (0.0, 1.0))):
        for _ in range(STEPS):
            i = rng.randrange(N)
            j = (i + 1) % N
            fi = cells[i][0] * context[0] + cells[i][1] * context[1]
            fj = cells[j][0] * context[0] + cells[j][1] * context[1]
            loser, winner = (i, j) if fi < fj else (j, i)
            replace = mode == "relative"
            if mode == "absolute":
                replace = min(fi, fj) < 0.5
            if replace:
                child = [max(0.0, min(1.0, x + rng.gauss(0.0, MUTATION)))
                         for x in cells[winner]]
                cells[loser] = child
        epoch_means.append(statistics.mean(c[epoch] for c in cells))
    return epoch_means


if __name__ == "__main__":
    modes = ("none", "absolute", "relative")
    results = {mode: [run(seed, mode) for seed in range(SEEDS)] for mode in modes}
    print(f"seeds={SEEDS} cells={N} steps_per_context={STEPS} mutation_sd={MUTATION}")
    for mode in modes:
        means = [statistics.mean(row[e] for row in results[mode]) for e in range(2)]
        sds = [statistics.pstdev(row[e] for row in results[mode]) for e in range(2)]
        print(f"{mode}: context0={means[0]:.6f} (sd={sds[0]:.6f}) "
              f"context1_after_switch={means[1]:.6f} (sd={sds[1]:.6f})")
