"""Toy test of deleting versus parking losing local specialists across a task switch."""
import random
import statistics


N = 128
STEPS = 1200
SEEDS = 100
MUTATION = 0.04


def run(seed, mode):
    rng = random.Random(seed)
    active = [[rng.random(), rng.random()] for _ in range(N)]
    reserve = []
    phase_scores = []
    for phase, task in enumerate((0, 1, 0)):
        for _ in range(STEPS):
            i = rng.randrange(N)
            j = (i + 1) % N
            loser, winner = (i, j) if active[i][task] < active[j][task] else (j, i)
            winner_trait = active[winner][:]
            if mode.startswith("reserve"):
                reserve.append(active[loser])
            active[loser] = [max(0.0, min(1.0, x + rng.gauss(0.0, MUTATION)))
                             for x in winner_trait]
            if mode == "reserve" and reserve and rng.random() < 0.02:
                weakest = min(range(N), key=lambda k: active[k][task])
                parked = max(range(len(reserve)), key=lambda k: reserve[k][task])
                if reserve[parked][task] > active[weakest][task]:
                    active[weakest] = reserve.pop(parked)
        phase_scores.append(statistics.mean(cell[task] for cell in active))
    return phase_scores


if __name__ == "__main__":
    outputs = {mode: [run(seed, mode) for seed in range(SEEDS)]
               for mode in ("delete", "reserve", "reserve_no_retrieve")}
    print(f"seeds={SEEDS} active_cells={N} steps_per_phase={STEPS} mutation_sd={MUTATION}")
    for mode, rows in outputs.items():
        means = [statistics.mean(row[p] for row in rows) for p in range(3)]
        sds = [statistics.pstdev(row[p] for row in rows) for p in range(3)]
        print(f"{mode}: task0={means[0]:.6f} (sd={sds[0]:.6f}) "
              f"task1={means[1]:.6f} (sd={sds[1]:.6f}) "
              f"task0_return={means[2]:.6f} (sd={sds[2]:.6f})")
