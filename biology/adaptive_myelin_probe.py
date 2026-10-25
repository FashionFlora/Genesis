import random
import statistics


def run(seed, mode, episodes=1200, routes=40, frequent=8):
    rng = random.Random(seed)
    delays = [1.0] * routes
    for _ in range(episodes):
        if rng.random() < 0.9:
            route = rng.randrange(frequent)
        else:
            route = rng.randrange(frequent, routes)

        if mode == "activity_gated":
            delays[route] = max(0.5, delays[route] * 0.99)
        elif mode == "global_budget":
            saving = delays[route] - max(0.5, delays[route] * 0.99)
            per_route = saving / routes
            delays = [max(0.5, delay - per_route) for delay in delays]

    active = statistics.mean(delays[:frequent])
    rare = statistics.mean(delays[frequent:])
    weighted = 0.9 * active + 0.1 * rare
    return weighted, active, rare


def summarize(rows):
    cols = list(zip(*rows))
    return " ".join(f"{statistics.mean(col):.6f} +/- {statistics.pstdev(col):.6f}" for col in cols)


if __name__ == "__main__":
    print("condition: weighted_latency, frequent_latency, rare_latency; n=100 seeds")
    for mode in ("none", "global_budget", "activity_gated"):
        results = [run(seed, mode) for seed in range(100)]
        print(f"{mode}: {summarize(results)}")
