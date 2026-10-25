import random
import statistics


def run(seed, mode, turnover=0.0, routes=40, frequent=8, phase_steps=600):
    rng = random.Random(seed)
    delays = [1.0] * routes
    phase_rows = []

    for phase in range(2):
        start = 0 if phase == 0 else frequent
        end = frequent if phase == 0 else 2 * frequent
        weighted_delay = 0.0
        for _ in range(phase_steps):
            route = rng.randrange(start, end) if rng.random() < 0.9 else rng.randrange(routes)
            weighted_delay += delays[route]

            if mode.startswith("local_") and mode != "local_unused":
                delays[route] = max(0.5, delays[route] * 0.99)
            elif mode == "global_budget":
                saving = delays[route] - max(0.5, delays[route] * 0.99)
                per_route = saving / routes
                delays = [max(0.5, delay - per_route) for delay in delays]

            if turnover:
                delays = [delay + turnover * (1.0 - delay) for delay in delays]

        phase_rows.append(weighted_delay / phase_steps)

    return tuple(phase_rows)


def summarize(rows):
    cols = list(zip(*rows))
    return " ".join(f"{statistics.mean(col):.6f} +/- {statistics.pstdev(col):.6f}" for col in cols)


if __name__ == "__main__":
    print("phase1_latency phase2_latency; 100 seeds, switch after 600 events")
    for mode, turnover in (("none", 0.0), ("global_budget", 0.0),
                           ("local_permanent", 0.0), ("local_turnover_0005", 0.0005),
                           ("local_turnover_002", 0.002), ("local_turnover_005", 0.005)):
        rows = [run(seed, mode, turnover) for seed in range(100)]
        print(f"{mode}: {summarize(rows)}")
