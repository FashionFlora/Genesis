import math
import random
import statistics


def wrap(angle):
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def run(seed, mode, routes=40, frequent=8, steps=1200, switch=600):
    rng = random.Random(seed)
    lengths = [rng.uniform(4.0, 10.0) for _ in range(routes)]
    offsets = [rng.uniform(-math.pi, math.pi) for _ in range(routes)]
    base = [length / 4.0 for length in lengths]
    delays = base[:]
    errors = []

    for step in range(steps):
        phase = 0 if step < switch else 1
        start = phase * frequent
        end = start + frequent
        route = rng.randrange(start, end) if rng.random() < 0.9 else rng.randrange(routes)
        error = wrap(offsets[route] - delays[route])

        if mode in ("phase_cost", "phase_only"):
            delays[route] += 0.08 * error
            if mode == "phase_cost":
                # Local phase correction competes with a metabolic pull to baseline.
                delays[route] -= 0.002 * (delays[route] - base[route])
        elif mode == "use_shortening":
            delays[route] = max(lengths[route] / 8.0, delays[route] * 0.99)

        delays[route] = min(lengths[route] / 2.0, max(lengths[route] / 8.0, delays[route]))
        if (step + 1) % 100 == 0:
            errors.append((phase, route, error))

    def phase_error(route_ids):
        return statistics.mean(abs(wrap(offsets[i] - delays[i])) for i in route_ids)

    return (
        phase_error(range(frequent)),
        phase_error(range(frequent, 2 * frequent)),
        phase_error(range(2 * frequent, routes)),
        statistics.mean(abs(delays[i] - base[i]) for i in range(routes)),
    )


def summarize(rows):
    columns = list(zip(*rows))
    return " ".join(f"{statistics.mean(col):.6f}" for col in columns)


if __name__ == "__main__":
    print("columns: phase1_active_error phase2_active_error unused_error mean_delay_shift")
    for mode in ("none", "use_shortening", "phase_only", "phase_cost"):
        print(f"{mode}: {summarize([run(seed, mode) for seed in range(100)])}")
